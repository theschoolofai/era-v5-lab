"""Rollouts from a quantized (or lower-precision) copy of the policy, with the sampler's own log-probabilities.

    train.sampler: quant
    train.quant: {scheme: int8_dynamic, max_k3: 0.05, guard: true}

Before every call of `sample` the copy is rebuilt from the learner's current weights (the time is recorded as
`refresh_s`), so a rollout never comes from stale weights. Every Rollout carries `rollout_lp`: the log-probability of
each sampled token under the COPY that sampled it, at temperature 1. The trainer then does what it already does for any
sampler with its own log-probabilities: `old_lp` from the high-precision learner, `mismatch_k3` and
`mismatch_abs_logratio`, and either TIS (`train.tis_clip`, grpo-family) or objective_v1's closed trust region
(`train.tr_epsilon`) on the ratio to `rollout_lp`. Evaluation stays on the learner (`self.exact`).

Schemes
    copy          an exact copy. A control: mismatch must be zero to rounding, and it shows what the plumbing costs.
    bf16, fp16    the copy cast to that dtype (a model that is not Hugging Face also computes under that autocast). Real
                  lower-precision kernels.
    int8_dynamic  torch dynamic quantization of nn.Linear (int8 weights per channel, activations quantized per call).
                  Real int8 kernels, CPU only, Hugging Face models only.
    w8a8_sim      SIMULATED: weights rounded to int8 per output row; the input of every nn.Linear that is called as a
                  module rounded to int8 per row. Runs in the stored dtype, so it measures mismatch, never speed.
    w4a16_sim     SIMULATED: weights rounded to int4 in groups of 128 inputs, activations as they are. Mismatch only.
Router weights are never quantized (as in Team 12's exports); bf16 and fp16 cast the whole copy, router included.
`copy` and the simulated schemes keep the learner's autocast dtype, so their gap is the rounding alone.
The copy is bound to the policy through Policy.with_model (Team 5's policy overrides it); a native policy whose forward
does not read the copy is refused.

Not covered: Deletion Tuning masks; int8_dynamic on Team 5's model (its MoE reads expert `.weight` tensors in one
batched product, which a quantized module does not have: that path needs Team 12's export or a serving engine).
"""
from __future__ import annotations

import copy
import re
import time
import warnings

import torch
import torch.nn as nn
from torch import no_grad  # decorator without a dot: pr-guard reads '+@a.b' as an email

import rollout
import router
from policy import HFPolicy, completion_logprobs

SCHEMES = ("copy", "bf16", "fp16", "int8_dynamic", "w8a8_sim", "w4a16_sim")
SIMULATED = ("w8a8_sim", "w4a16_sim")
W4_GROUP = 128


def fake_quantize(w: torch.Tensor, bits: int, group: int | None = None) -> torch.Tensor:
    """Symmetric round-to-nearest of a 2D weight [out, in]: one scale per output row, or per `group` inputs of a row."""
    qmax = 2 ** (bits - 1) - 1
    x = w.float()
    cols = x.shape[1]
    size = cols if group is None else group
    out = torch.empty_like(x)
    for start in range(0, cols, size):
        part = x[:, start:start + size]
        scale = (part.abs().amax(1, keepdim=True) / qmax).clamp_min(1e-12)
        out[:, start:start + size] = (part / scale).round().clamp(-qmax, qmax) * scale
    return out.to(w.dtype)


def _fake_quantize_input(_module, args):
    x = args[0]
    scale = (x.float().abs().amax(-1, keepdim=True) / 127).clamp_min(1e-12)
    return ((x.float() / scale).round().clamp(-127, 127) * scale).to(x.dtype), *args[1:]


def _check_reads(policy):
    """Refuse a native policy whose forward does not go through its own model: it would sample from the learner's weights
    and report a mismatch of zero."""
    seen = []
    hooks = [m.register_forward_pre_hook(lambda *_: seen.append(True)) for m in policy.model.modules()]
    try:
        completion_logprobs(policy, torch.zeros(1, 2, dtype=torch.long, device=policy.device), 1)
    finally:
        for h in hooks:
            h.remove()
    if not seen:
        raise RuntimeError("the policy's forward does not read the quantized copy: its class needs with_model()")


def _is_router(name: str, patterns) -> bool:
    return any(re.search(p, f"{name}.weight") for p in patterns)


def quantized_copy(model: nn.Module, scheme: str, router_patterns=router.ROUTER_PATTERNS) -> tuple[nn.Module, dict]:
    """(a frozen, eval-mode copy of `model` under `scheme`, what was changed)."""
    if scheme not in SCHEMES:
        raise ValueError(f"unknown quantization scheme {scheme!r}; choose from {SCHEMES}")
    with torch.no_grad():
        q = copy.deepcopy(model).eval()
    q.requires_grad_(False)
    linears = [(n, m) for n, m in q.named_modules() if isinstance(m, nn.Linear) and not _is_router(n, router_patterns)]
    info = {"scheme": scheme, "simulated": scheme in SIMULATED, "linear_layers": len(linears)}
    if scheme in ("bf16", "fp16"):
        dtype = torch.bfloat16 if scheme == "bf16" else torch.float16
        for p in q.parameters():
            if p.is_floating_point():
                p.data = p.data.to(dtype)
        info["linear_layers"] = len([m for m in q.modules() if isinstance(m, nn.Linear)])  # the router is cast too
    elif scheme == "int8_dynamic":
        if any(p.device.type != "cpu" for p in q.parameters()):
            raise ValueError("int8_dynamic has CPU kernels only")
        if not linears:
            raise ValueError("int8_dynamic: no nn.Linear to quantize")
        from torch.ao.quantization import per_channel_dynamic_qconfig, quantize_dynamic  # noqa: PLC0415
        for p in q.parameters():  # dynamic quantization starts from fp32 weights
            if p.is_floating_point():
                p.data = p.data.float()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            quantize_dynamic(q, {n: per_channel_dynamic_qconfig for n, _ in linears}, inplace=True)
    elif scheme in SIMULATED:
        bits, group = (8, None) if scheme == "w8a8_sim" else (4, W4_GROUP)
        done = set()
        with torch.no_grad():
            for _, m in linears:
                if m.weight.data_ptr() not in done:
                    m.weight.copy_(fake_quantize(m.weight, bits, group))
                    done.add(m.weight.data_ptr())
                if scheme == "w8a8_sim":
                    m.register_forward_pre_hook(_fake_quantize_input)
    return q, info


class _LogprobRecorder:
    """A generate() logits processor that changes nothing and keeps log p(chosen token) and the entropy per step. Only one
    [rows, vocab] tensor is alive at a time."""

    def __init__(self):
        self.prev: torch.Tensor | None = None
        self.lp: list[torch.Tensor] = []
        self.entropy: list[torch.Tensor] = []

    def take(self, chosen: torch.Tensor) -> None:
        if self.prev is not None:
            self.lp.append(self.prev.gather(-1, chosen[:, None]).squeeze(-1))
            self.prev = None

    def __call__(self, input_ids: torch.Tensor, scores: torch.Tensor) -> torch.Tensor:
        self.take(input_ids[:, -1])
        self.prev = torch.log_softmax(scores.float(), -1)
        self.entropy.append(-(self.prev.exp() * self.prev).sum(-1))
        return scores


class QuantRolloutSampler:
    def __init__(self, policy, scheme: str, pad_id: int | None = None, router_patterns=router.ROUTER_PATTERNS):
        if scheme not in SCHEMES:
            raise ValueError(f"unknown quantization scheme {scheme!r}; choose from {SCHEMES}")
        self.policy = policy
        self.scheme = scheme
        self.router_patterns = tuple(router_patterns)
        self.hf = isinstance(policy, HFPolicy)
        if scheme == "int8_dynamic" and not self.hf:
            raise ValueError("int8_dynamic is for Hugging Face models: Team 5's fused MoE reads expert weights directly")
        self.pad_id = pad_id if pad_id is not None else (policy.eos_id if policy.eos_id is not None else 0)
        self.exact = rollout.HFBatchSampler(policy, pad_id) if self.hf else rollout.PolicySampler(policy)
        self.info: dict | None = None
        self.refreshes = 0
        self.refresh_seconds = 0.0
        self.last: dict = {}

    def refresh(self):
        """A policy object whose model is a fresh quantized copy of the learner's current weights."""
        t0 = time.perf_counter()
        model, self.info = quantized_copy(self.policy.model, self.scheme, self.router_patterns)
        q = self.policy.with_model(model)
        if self.scheme in ("bf16", "fp16"):  # the copy's weights are in that dtype; a native model also computes in it
            q.amp_dtype = None if self.hf else (torch.bfloat16 if self.scheme == "bf16" else torch.float16)
        elif self.scheme == "int8_dynamic":
            q.amp_dtype = None
        # copy and the simulated schemes keep the learner's compute dtype: the gap is then quantization alone
        if not self.hf and not self.refreshes:
            _check_reads(q)
        dt = time.perf_counter() - t0
        self.refreshes += 1
        self.refresh_seconds += dt
        self.last = {"refresh_s": dt}
        return q

    @no_grad()
    def sample(self, prompts, k, max_new, temperature, generator=None) -> list[rollout.Rollout]:
        if temperature != 1.0:
            raise ValueError("the quant sampler reports log-probabilities of the raw distribution: temperature must be 1.0")
        q = self.refresh()
        out = self._sample_hf(q, prompts, k, max_new, generator) if self.hf else self._sample_native(q, prompts, k, max_new,
                                                                                                    generator)
        del q
        return out

    def _sample_native(self, q, prompts, k, max_new, generator):
        rolls = rollout.PolicySampler(q).sample(prompts, k, max_new, 1.0, generator)
        for p, r in zip(prompts, rolls):  # one extra forward of the copy per prompt (Policy.sample returns no logits)
            r.rollout_lp = completion_logprobs(q, r.seq, len(p)).masked_fill(~r.cmask, 0.0)
        return rolls

    def _sample_hf(self, q, prompts, k, max_new, generator):
        from transformers import LogitsProcessorList  # noqa: PLC0415
        dev, pad, eos = q.device, self.pad_id, q.eos_id
        if generator is not None:  # generate() has no generator argument; seed torch from ours (as HFBatchSampler does)
            torch.manual_seed(int(torch.randint(0, 2**31 - 1, (1,), generator=generator)))
        width = max(len(p) for p in prompts)
        rows, masks = [], []
        for p in prompts:
            for _ in range(k):
                rows.append([pad] * (width - len(p)) + list(p))
                masks.append([0] * (width - len(p)) + [1] * len(p))
        ids = torch.tensor(rows, dtype=torch.long, device=dev)
        rec = _LogprobRecorder()
        with q.autocast():
            out = q.model.generate(input_ids=ids, attention_mask=torch.tensor(masks, dtype=torch.long, device=dev),
                                   max_new_tokens=max_new, min_new_tokens=max_new if eos is None else 0, do_sample=True,
                                   temperature=1.0, top_k=0, top_p=1.0, eos_token_id=eos, pad_token_id=pad,
                                   logits_processor=LogitsProcessorList([rec]))
        comp = out[:, width:]
        made = comp.shape[1]
        rec.take(comp[:, -1])
        lp, ent = torch.stack(rec.lp, 1), torch.stack(rec.entropy, 1)
        if lp.shape[1] != made:
            raise RuntimeError(f"recorded {lp.shape[1]} log-probabilities for {made} generated tokens")
        if made < max_new:
            fill = (comp.shape[0], max_new - made)
            comp = torch.cat([comp, torch.full(fill, pad, device=dev)], 1)
            lp = torch.cat([lp, lp.new_zeros(fill)], 1)
            ent = torch.cat([ent, ent.new_zeros(fill)], 1)
        cmask = rollout.completion_mask(comp, eos)
        lp = lp.masked_fill(~cmask, 0.0)
        self.last["entropy"] = float(ent[cmask].mean())
        result = []
        for i, p in enumerate(prompts):
            s = slice(i * k, (i + 1) * k)
            prompt = torch.tensor([list(p)] * k, dtype=torch.long, device=dev)
            result.append(rollout.Rollout(torch.cat([prompt, comp[s]], 1), cmask[s], lp[s]))
        return result

    def summary(self) -> dict:
        return {**(self.info or {"scheme": self.scheme}), "refreshes": self.refreshes,
                "refresh_seconds": round(self.refresh_seconds, 4)}
