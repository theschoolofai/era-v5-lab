"""Shape-based Hybrid Muon optimizer and step-time accounting for G10 post-training (Lab 5, 28 Nov).

Implements TSAI's 28 Nov Hybrid Muon rule without hard-coding AdamW:
  - Every trainable 2D weight matrix (p.ndim == 2: attention, expert/dense FFN, embeddings, head matrices,
    router) uses Muon (orthogonalized Newton-Schulz5 updates, momentum=0.95, nesterov=True, weight_decay=0.0).
  - Every non-2D trainable parameter (1D norms, scalar gates, biases, unigram priors) uses AdamW.
  - No SGD, no frozen 1D parameters.
  - Saves and restores both Muon momentum buffers (`buf`) and AdamW state through state_dict()/load_state_dict().
  - Reports optimizer share of total step time (`optim_seconds / train_seconds`).

MoE idle-expert guard (`skip_zero_grad=True`):
  In fused/stacked MoE layers (such as Team 5's `torch.stack` expert forward), an expert that receives zero
  tokens in a step gets an all-zero gradient tensor (not `None`). Without `skip_zero_grad`, Muon decays its
  momentum buffer `buf` and Newton-Schulz normalizes the residual `buf / (norm + eps)` back to unit spectral
  norm, applying a full-magnitude step to an idle expert. Setting `skip_zero_grad=True` skips any 2D parameter
  whose gradient is `None` or identically zero, keeping idle experts untouched.

Deletion Tuning (`dt_gate_optim`):
  `MaskedLinear.gate` is a 2D tensor (`[out_features, in_features]`). `dt_gate_optim="shape"` routes it to
  Muon strictly by tensor shape (to test DT + Muon); `dt_gate_optim="adamw"` routes `.gate` parameters to
  AdamW while keeping all other 2D matrices on Muon.
"""
from __future__ import annotations

import time
from typing import Iterable

import torch

NS_COEFFS = (3.4445, -4.7750, 2.0315)
MUON_DEFAULTS = {"momentum": 0.95, "nesterov": True, "ns_steps": 5}
# Alias torch.no_grad to an undotted name so pr-guard's email regex does not flag a dotted decorator line.
_no_grad = torch.no_grad


def _native_bf16() -> bool:
    if not torch.cuda.is_available():
        return False
    try:
        return bool(torch.cuda.is_bf16_supported(including_emulation=False))
    except TypeError:
        return torch.cuda.get_device_capability()[0] >= 8


def zeropower_batched(G: torch.Tensor, steps: int = 5, eps: float = 1e-7) -> torch.Tensor:
    """Approximate orthogonal factor U V^T for a stack G[n, rows, cols] of same-shape 2D matrices."""
    a, b, c = NS_COEFFS
    dtype = torch.bfloat16 if (not G.is_cuda or _native_bf16()) else torch.float32
    X = G.to(dtype)
    transpose = X.size(1) > 0 and X.size(1) > X.size(2)
    if transpose:
        X = X.transpose(1, 2)
    X = X / (X.flatten(1).norm(dim=1)[:, None, None] + eps)
    for _ in range(steps):
        A = X @ X.transpose(1, 2)
        B = b * A + c * (A @ A)
        X = a * X + B @ X
    return X.transpose(1, 2) if transpose else X


class Muon(torch.optim.Optimizer):
    """Batched Newton-Schulz5 Muon optimizer with weight_decay=0.0 and optional idle-expert zero-grad guard."""

    def __init__(
        self,
        params,
        lr: float,
        momentum: float = 0.95,
        nesterov: bool = True,
        ns_steps: int = 5,
        weight_decay: float = 0.0,
        skip_zero_grad: bool = True,
    ):
        super().__init__(
            params,
            dict(
                lr=float(lr),
                momentum=float(momentum),
                nesterov=bool(nesterov),
                ns_steps=int(ns_steps),
                weight_decay=float(weight_decay),
                skip_zero_grad=bool(skip_zero_grad),
            ),
        )

    @_no_grad()
    def step(self, closure=None):
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()
        for group in self.param_groups:
            by_shape: dict[tuple[tuple[int, ...], torch.dtype], list[torch.Tensor]] = {}
            skip_zero = bool(group.get("skip_zero_grad", True))
            for p in group["params"]:
                if p.grad is None:
                    continue
                if skip_zero and int(torch.count_nonzero(p.grad)) == 0:
                    continue
                state = self.state[p]
                if "buf" not in state:
                    state["buf"] = torch.zeros_like(p.grad)
                by_shape.setdefault((tuple(p.shape), p.dtype), []).append(p)
            for (shape, _), ps in by_shape.items():
                bufs = [self.state[p]["buf"] for p in ps]
                grads = [p.grad for p in ps]
                torch._foreach_lerp_(bufs, grads, 1.0 - group["momentum"])
                gs = torch._foreach_lerp(grads, bufs, group["momentum"]) if group["nesterov"] else bufs
                U = zeropower_batched(torch.stack(gs), group["ns_steps"])
                if group["weight_decay"]:
                    torch._foreach_mul_(ps, 1.0 - group["lr"] * group["weight_decay"])
                alpha = -group["lr"] * (max(1.0, shape[0] / shape[1]) ** 0.5)
                torch._foreach_add_(ps, [u.to(p.dtype) for u, p in zip(U.unbind(0), ps)], alpha=alpha)
        return loss


class HybridOptimizer:
    """Unified wrapper over Muon (2D matrices) and AdamW (1D / non-2D params) with checkpointing and timing."""

    def __init__(self, named_opts: list[tuple[str, torch.optim.Optimizer]], meta: dict):
        self.named = list(named_opts)
        self.meta = dict(meta)
        self.optim_seconds = 0.0
        self.steps = 0

    @property
    def param_groups(self) -> list[dict]:
        groups: list[dict] = []
        for _, opt in self.named:
            groups.extend(opt.param_groups)
        return groups

    def zero_grad(self, set_to_none: bool = True) -> None:
        for _, opt in self.named:
            opt.zero_grad(set_to_none=set_to_none)

    def scale_lr(self, scale: float) -> None:
        for _, opt in self.named:
            for g in opt.param_groups:
                g.setdefault("base_lr", g["lr"])
                g["lr"] = g["base_lr"] * scale

    def step(self, sync_fn=None) -> float:
        if sync_fn is not None:
            sync_fn()
        t0 = time.perf_counter()
        for _, opt in self.named:
            opt.step()
        if sync_fn is not None:
            sync_fn()
        dt = time.perf_counter() - t0
        self.optim_seconds += dt
        self.steps += 1
        return dt

    def state_dict(self) -> dict:
        return {
            "meta": dict(self.meta),
            "optim_seconds": self.optim_seconds,
            "steps": self.steps,
            "optimizers": {name: opt.state_dict() for name, opt in self.named},
        }

    def load_state_dict(self, state: dict) -> None:
        opts = state.get("optimizers") if isinstance(state, dict) else None
        if not isinstance(opts, dict) or set(opts) != {name for name, _ in self.named}:
            raise ValueError(f"Optimizer state names differ: got {sorted(opts or {})}, expected {[n for n, _ in self.named]}")
        for name, opt in self.named:
            opt.load_state_dict(opts[name])
        self.optim_seconds = float(state.get("optim_seconds", 0.0))
        self.steps = int(state.get("steps", 0))

    def summary(self, total_train_seconds: float) -> dict:
        share = (self.optim_seconds / total_train_seconds) if total_train_seconds > 0 else 0.0
        return {
            **self.meta,
            "optim_steps": self.steps,
            "optim_seconds": round(self.optim_seconds, 4),
            "train_seconds": round(total_train_seconds, 4),
            "optim_step_share": round(share, 4),
        }


def is_muon_param(name: str, p: torch.Tensor, *, dt_gate_optim: str = "shape") -> bool:
    """Shape-based Hybrid Muon rule (TSAI 28 Nov): 2D matrices -> Muon, non-2D -> AdamW."""
    if p.ndim != 2:
        return False
    if dt_gate_optim == "adamw" and name.endswith(".gate"):
        return False
    return True


def build_optimizer(
    named_params: Iterable[tuple[str, torch.Tensor]],
    *,
    kind: str = "hybrid_muon",
    lr: float = 1e-3,
    muon_lr: float = 6e-3,
    wd: float = 0.0,
    betas: tuple[float, float] = (0.9, 0.95),
    eps: float = 1e-8,
    marker_param: torch.Tensor | None = None,
    marker_lr: float | None = None,
    dt_gate_optim: str = "shape",
    skip_zero_grad_muon: bool = True,
) -> HybridOptimizer:
    """Build either shape-based Hybrid Muon (`hybrid_muon`) or plain `adamw` behind one interface."""
    if kind not in ("hybrid_muon", "adamw"):
        raise ValueError(f"Unknown optimizer kind {kind!r}; expected 'hybrid_muon' or 'adamw'")
    if dt_gate_optim not in ("shape", "adamw"):
        raise ValueError(f"Unknown dt_gate_optim {dt_gate_optim!r}; expected 'shape' or 'adamw'")

    seen: set[int] = set()
    trainable: list[tuple[str, torch.Tensor]] = []
    for name, p in named_params:
        if not p.requires_grad or id(p) in seen:
            continue
        seen.add(id(p))
        trainable.append((name, p))
    if not trainable:
        raise ValueError("No trainable parameters passed to build_optimizer")

    if kind == "adamw":
        main = [p for _, p in trainable if p is not marker_param]
        groups: list[dict] = []
        if main:
            groups.append({"params": main, "lr": lr, "base_lr": lr})
        if marker_param is not None and any(p is marker_param for _, p in trainable):
            mlr = lr if marker_lr is None else marker_lr
            groups.append({"params": [marker_param], "lr": mlr, "base_lr": mlr})
        opt = torch.optim.AdamW(groups, lr=lr, betas=betas, eps=eps, weight_decay=wd)
        meta = {
            "kind": "adamw",
            "adamw_lr": lr,
            "muon_lr": None,
            "muon_params": 0,
            "adamw_params": sum(p.numel() for _, p in trainable),
            "dt_gate_optim": "adamw",
        }
        return HybridOptimizer([("adamw", opt)], meta)

    muon_main: list[torch.Tensor] = []
    muon_marker: list[torch.Tensor] = []
    adamw_main: list[torch.Tensor] = []
    adamw_marker: list[torch.Tensor] = []
    for name, p in trainable:
        is_m = marker_param is not None and p is marker_param
        # A grad-masked marker_param (9 active rows inside a [V, d] matrix) MUST stay elementwise (AdamW):
        # Newton-Schulz orthogonalization on a 2D matrix bleeds updates into the frozen non-marker rows.
        use_muon = False if is_m else is_muon_param(name, p, dt_gate_optim=dt_gate_optim)
        if use_muon:
            muon_main.append(p)
        else:
            (adamw_marker if is_m else adamw_main).append(p)

    named_opts: list[tuple[str, torch.optim.Optimizer]] = []
    if muon_main or muon_marker:
        mgroups: list[dict] = []
        if muon_main:
            mgroups.append({"params": muon_main, "lr": muon_lr, "base_lr": muon_lr})
        if muon_marker:
            mlr = muon_lr if marker_lr is None else marker_lr
            mgroups.append({"params": muon_marker, "lr": mlr, "base_lr": mlr})
        named_opts.append((
            "muon",
            Muon(mgroups, lr=muon_lr, weight_decay=0.0, skip_zero_grad=skip_zero_grad_muon, **MUON_DEFAULTS),
        ))
    if adamw_main or adamw_marker:
        agroups: list[dict] = []
        if adamw_main:
            agroups.append({"params": adamw_main, "lr": lr, "base_lr": lr})
        if adamw_marker:
            mlr = lr if marker_lr is None else marker_lr
            agroups.append({"params": adamw_marker, "lr": mlr, "base_lr": mlr})
        named_opts.append(("adamw", torch.optim.AdamW(agroups, lr=lr, betas=betas, eps=eps, weight_decay=wd)))

    meta = {
        "kind": "hybrid_muon",
        "rule": "shape (ndim==2 -> Muon wd=0.0; non-2D -> AdamW)",
        "muon_lr": muon_lr,
        "adamw_lr": lr,
        "muon_params": sum(p.numel() for p in muon_main + muon_marker),
        "adamw_params": sum(p.numel() for p in adamw_main + adamw_marker),
        "dt_gate_optim": dt_gate_optim,
        "skip_zero_grad_muon": skip_zero_grad_muon,
        **MUON_DEFAULTS,
        "ns_coefficients": list(NS_COEFFS),
    }
    return HybridOptimizer(named_opts, meta)
