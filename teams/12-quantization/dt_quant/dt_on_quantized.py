#!/usr/bin/env python3
"""Deletion Tuning on a quantized base model (G12 design task 9, with G10's dt/mask.py).

    python dt_on_quantized.py --model Qwen/Qwen3-0.6B-Base --out dt_quant.json \\
        [--arms base,base_q8_0,base_q4_0,dt,dt_q8_0,dt_q4_0,dt_then_q8_0,dt_then_q4_0] [--steps 400] [--device cuda]

TSAI's question: does Deletion Tuning work on a quantized base as well as on bf16, and what does the quantized base save
in memory? DT freezes W and trains one FP32 logit G per targeted weight; the model applies W * 1[G > 0]. Here W can be
stored quantized: Q8_0 or Q4_0, the llama.cpp block formats (blocks of 32 along the input dimension, one fp16 scale per
block; same values as gguf-py, tested), kept packed on the targeted layers and dequantized in the forward pass. Every
other decoder linear is quantized in place (round-trip through the format). Embeddings, head and norms stay as loaded.

Arms (names; "<q>" is q8_0 or q4_0):
  base, base_<q>      no DT: the dense model, and the dense model with every decoder linear quantized
  dt                  DT on the unquantized base
  dt_<q>              DT on the quantized base: W packed, the Wanda prior calibrated on the quantized weights
  dt_then_<q>         the `dt` result with its mask baked in (W * 1[G > 0]), then quantized: the other order, as a control
                      (computed inside the `dt` run, which bakes the mask once and scores a quantized copy per format)
Each arm reports held-out NLL per token (mean over windows, with per-window values for paired intervals), the share of
targeted weights deleted, training time and peak CUDA memory. Training uses G10's DT settings: AdamW on the logits (lr 5e-4, G10's default since its
17 Nov port check; its older ladder runs used 2e-3, set with --lr; betas 0.9/0.95), alpha 100 to 1000, Wanda prior (eta 1/2048, strength 3),
regulariser lambda 1e-5 decaying to 0, `gate_proj` targets. The loop is simpler than G10's trainer (sft/bench/train.py): constant
learning rate, no warmup, no cosine decay, no gradient clipping. That is the same for every arm, so arms compare fairly, but
the numbers are not G10's trainer's. The data is plain text (wikitext-2), next-token loss on every token:
not G10's SFT slice, so this answers "does the mask train on a quantized base", not G10's chat-format question.

Memory: `memory_accounting` gives bytes per decoder-linear weight (fp32 4, bf16 2, Q8_0 34/32, Q4_0 18/32) and the DT state per
targeted weight (FP32 logit 4 + gradient 4 + Adam moments 8 = 16 bytes; DT arms only), so the table shows how much of DT's cost
the quantized base can touch. These are STORAGE figures. Peak CUDA memory during training is measured separately and need not
fall with the format: `base_weight` dequantizes on every read and `W * mask` keeps that fp32 copy for backward in every layer
(Sourav measured 11.9 against 7.9 bytes per masked weight saved for backward at Q8_0), so a packed arm can peak as high as `dt`.
`dtmask.deletion_stats()` counts `named_parameters()`, and packing removes `weight`, so its `model_weights` is lower on packed
models; no number reported here uses it. Aggregate numbers only: no text is written.
"""
from __future__ import annotations

import argparse, importlib.util, json, math, sys, time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("g10_dt_mask", HERE.parents[1] / "10-post-training" / "dt" / "mask.py")
dtmask = importlib.util.module_from_spec(_spec); sys.modules["g10_dt_mask"] = dtmask; _spec.loader.exec_module(dtmask)

BLOCK = 32
BYTES_PER_WEIGHT = {"bf16": 2.0, "bfloat16": 2.0, "float32": 4.0, "q8_0": 34 / 32, "q4_0": 18 / 32}   # llama.cpp block sizes: 2 B scale + 32 / 16 B codes
DT_STATE_BYTES = 4 + 4 + 8                                          # FP32 logit, its gradient, Adam exp_avg and exp_avg_sq


# ------------------------------------------------------------------------------------------------ block quantization
def _blocks(w: torch.Tensor) -> torch.Tensor:
    if w.shape[-1] % BLOCK:
        raise ValueError(f"input dimension {w.shape[-1]} is not a multiple of {BLOCK}")
    return w.float().reshape(*w.shape[:-1], w.shape[-1] // BLOCK, BLOCK)


def _round_away(x: torch.Tensor) -> torch.Tensor:
    return torch.sign(x) * torch.floor(x.abs() + 0.5)           # C roundf: halves away from zero


def quantize(w: torch.Tensor, fmt: str) -> tuple[torch.Tensor, torch.Tensor]:
    """llama.cpp's reference quantizers. Returns (codes, scales): Q8_0 int8 [.., nb, 32]; Q4_0 uint8 packed [.., nb, 16]
    (element j in the low nibble, j + 16 in the high one); scales fp16 [.., nb]."""
    b = _blocks(w)
    if fmt == "q8_0":
        d = b.abs().amax(-1) / 127.0
        inv = torch.where(d > 0, 1.0 / d, torch.zeros_like(d))
        return _round_away(b * inv[..., None]).to(torch.int8), d.to(torch.float16)
    if fmt == "q4_0":
        idx = b.abs().argmax(-1, keepdim=True)
        mx = b.gather(-1, idx).squeeze(-1)                       # the signed value with the largest magnitude
        d = mx / -8.0
        inv = torch.where(d != 0, 1.0 / d, torch.zeros_like(d))
        q = torch.clamp(torch.floor(b * inv[..., None] + 8.5), max=15).to(torch.uint8)
        return (q[..., :16] | (q[..., 16:] << 4)).contiguous(), d.to(torch.float16)
    raise ValueError(fmt)


def dequantize(codes: torch.Tensor, scales: torch.Tensor, fmt: str, shape, dtype) -> torch.Tensor:
    d = scales.float()[..., None]
    if fmt == "q8_0":
        x = codes.float() * d
    else:
        lo, hi = (codes & 0x0F).float(), (codes >> 4).float()
        x = (torch.cat([lo, hi], dim=-1) - 8.0) * d
    return x.reshape(shape).to(dtype)


def fake_quantize_(linear: nn.Linear, fmt: str) -> None:
    """Round-trip the weight through the format, stored back in its own dtype."""
    c, s = quantize(linear.weight.data, fmt)
    linear.weight.data.copy_(dequantize(c, s, fmt, linear.weight.shape, linear.weight.dtype))


class QuantMaskedLinear(dtmask.MaskedLinear):
    """A MaskedLinear whose frozen W is stored packed (Q8_0 or Q4_0) and dequantized on every read of `base_weight`.
    Built by `to_packed` from a MaskedLinear; `weight`, `forward`, the Wanda hooks, the regulariser and `bake` of
    mask.py all read `base_weight`, so they work unchanged."""
    fmt: str

    @property
    def base_weight(self) -> torch.Tensor:
        return dequantize(self.codes, self.scales, self.fmt, (self.out_features, self.in_features), self._wdtype)

    def packed_bytes(self) -> int:
        return self.codes.numel() * self.codes.element_size() + self.scales.numel() * self.scales.element_size()


def to_packed(m: "dtmask.MaskedLinear", fmt: str) -> "QuantMaskedLinear":
    w = m._parameters.pop("weight")
    codes, scales = quantize(w.data, fmt)
    m.__class__ = QuantMaskedLinear
    m.fmt, m._wdtype = fmt, w.dtype
    m.register_buffer("codes", codes.to(w.device)); m.register_buffer("scales", scales.to(w.device))
    return m


# ------------------------------------------------------------------------------------------------ model helpers
def decoder_linears(model: nn.Module) -> list[tuple[str, nn.Linear]]:
    return [(n, m) for n, m in model.named_modules() if isinstance(m, nn.Linear) and ".layers." in f".{n}"]


def quantize_decoder_(model: nn.Module, fmt: str, skip=()) -> int:
    n = 0
    for name, lin in decoder_linears(model):
        if not (skip and dtmask.target_match(name, skip)):
            fake_quantize_(lin, fmt); n += 1
    return n


def memory_accounting(model: nn.Module, targets, fmt: str) -> dict:
    """Bytes of the decoder linears under `fmt` plus DT's per-weight state, for the model as loaded (no CUDA needed)."""
    lins = decoder_linears(model)
    total = sum(m.weight.numel() for _, m in lins)
    masked = sum(m.weight.numel() for n, m in lins if targets and dtmask.target_match(n, targets))
    per_w = BYTES_PER_WEIGHT[fmt]
    return {"decoder_linear_weights": total, "masked_weights": masked, "format": fmt,
            "weights_bytes": round(total * per_w), "dt_state_bytes": masked * DT_STATE_BYTES,
            "total_bytes": round(total * per_w) + masked * DT_STATE_BYTES,
            "bf16_weights_bytes": total * 2, "saved_by_format_bytes": round(total * (2 - per_w))}


# ------------------------------------------------------------------------------------------------ data and scoring
def make_windows(token_ids: list[int], length: int, n: int, offset: int = 0) -> list[list[int]]:
    out = []
    for i in range(n):
        s = offset + i * length
        if s + length > len(token_ids):
            break
        out.append(token_ids[s:s + length])
    return out


@torch.no_grad()
def window_nll(model: nn.Module, windows: list[list[int]], device, batch: int = 4) -> list[float]:
    """Mean NLL per predicted token of every window, in eval mode (DT layers apply the hard mask)."""
    model.eval()
    out = []
    for i in range(0, len(windows), batch):
        ids = torch.tensor(windows[i:i + batch], device=device)
        logits = model(input_ids=ids).logits[:, :-1].float()
        nll = nn.functional.cross_entropy(logits.reshape(-1, logits.shape[-1]), ids[:, 1:].reshape(-1), reduction="none")
        out += nll.reshape(ids.shape[0], -1).mean(1).tolist()
    return out


def paired_bootstrap(a: list[float], b: list[float], n_boot: int = 2000, seed: int = 0) -> dict:
    """Mean of (a - b) over the same windows with a 95% percentile interval (resampling windows)."""
    d = np.asarray(a) - np.asarray(b)
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, len(d), (n_boot, len(d)))].mean(1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"mean_diff": float(d.mean()), "ci95": [float(lo), float(hi)], "windows": int(len(d))}


# ------------------------------------------------------------------------------------------------ DT training
def run_arm(arm: str, args, tok_windows: dict, device) -> dict:
    """One arm end to end. arm is base | base_<q> | dt | dt_<q> | dt_then_<q>."""
    from transformers import AutoModelForCausalLM
    kind = "base" if arm.startswith("base") else "dt"
    fmt = arm.split("_", 1)[1] if "_" in arm else None
    assert not arm.startswith("dt_then"), "dt_then_<q> comes from the dt arm (it bakes and quantizes the same run)"
    assert fmt in (None, "q8_0", "q4_0"), arm
    if fmt and args.dtype != "float32":
        raise ValueError(f"{arm}: with --dtype {args.dtype} the dequantized values are rounded again and are no longer {fmt}; use float32")
    torch.manual_seed(args.seed)
    model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=getattr(torch, args.dtype), revision=args.revision).to(device)
    targets = dtmask.TARGET_SETS[args.targets]
    # the format's own bytes (the loaded dtype for an unquantized arm); DT state only where DT runs
    res = {"arm": arm, "format": fmt or args.dtype, "memory": memory_accounting(model, targets if kind == "dt" else (), fmt or args.dtype)}
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    if kind == "base":
        if fmt:
            quantize_decoder_(model, fmt)
    else:
        train_fmt = fmt
        if train_fmt:                                           # every non-targeted decoder linear is quantized in place
            quantize_decoder_(model, train_fmt, skip=targets)
        names = dtmask.convert(model, targets, args.alpha_start, args.alpha_end, args.steps, args.seed)
        if train_fmt:
            for _, m in dtmask.masked_layers(model):
                to_packed(m, train_fmt)
            res["packed_bytes_targeted"] = sum(m.packed_bytes() for _, m in dtmask.masked_layers(model))
            res["bf16_bytes_targeted"] = sum(m.in_features * m.out_features * 2 for _, m in dtmask.masked_layers(model))
        res["masked_layers"] = len(names)
        res.update(fit_mask(model, tok_windows["train"], tok_windows["calib"], device, args))
    res["train_seconds"] = round(time.time() - t0, 1)
    if device.type == "cuda":
        res["peak_cuda_gb"] = round(torch.cuda.max_memory_allocated() / 1e9, 3)
    nll = window_nll(model, tok_windows["test"], device)
    res.update(test_nll_mean=float(np.mean(nll)), test_windows=len(nll), per_window_nll=[round(x, 5) for x in nll])
    if kind == "dt" and fmt is None and args.then:             # the other order: bake the hard mask, then quantize the baked weights
        import copy
        dtmask.bake(model)
        res["then"] = {}
        for q in args.then:
            clone = copy.deepcopy(model)
            quantize_decoder_(clone, q)
            nq = window_nll(clone, tok_windows["test"], device)
            res["then"][q] = {"arm": f"dt_then_{q}", "format": q, "memory": memory_accounting(clone, (), q),   # served model: no DT state
                              "deletion_final": res["deletion_final"], "test_nll_mean": float(np.mean(nq)), "test_windows": len(nq),
                              "per_window_nll": [round(x, 5) for x in nq]}
            del clone
    del model
    return res


def fit_mask(model, train_windows, calib_windows, device, args) -> dict:
    """Wanda prior on the calibration windows, then `steps` optimizer steps on the logits (the official recipe's loop)."""
    batches = [{"input_ids": torch.tensor([w], device=device), "attention_mask": torch.ones(1, len(w), dtype=torch.long, device=device)}
               for w in calib_windows]
    scores = dtmask.wanda_scores(model, batches, device)
    # A weight that Q8_0 or Q4_0 rounded to exactly 0 has Wanda score 0. The prior marks the scores below the k-th smallest
    # (k = eta x weights); with 0.8% (Q8_0) or 12% (Q4_0) of a layer at 0, that threshold is 0 and nothing is below it, so the
    # quantized arms would train without the prior that `dt` has. Such weights get +inf: they are no candidates and never set
    # the threshold. mask.py is untouched. (Found by Sourav's review of #889.)
    zeroed = 0
    for name, layer in dtmask.masked_layers(model):
        if name in scores:
            z = layer.base_weight == 0
            zeroed += int(z.sum())
            scores[name] = torch.where(z, torch.full_like(scores[name], float("inf")), scores[name])
    info = {"wanda_prior": dtmask.apply_wanda_prior(model, scores, args.eta, args.prior_strength), "weights_zero_before_prior": zeroed}
    info["deletion_at_init"] = dtmask.deletion_stats(model)["deleted_frac_of_targeted"]
    gates = [m.gate for _, m in dtmask.masked_layers(model)]
    opt = torch.optim.AdamW(gates, lr=args.lr, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.0)
    rng = np.random.default_rng(args.seed)
    model.train()
    losses = []
    for step in range(args.steps):
        idx = rng.choice(len(train_windows), args.batch, replace=len(train_windows) < args.batch)
        total = 0.0
        for j in range(0, args.batch, args.micro):
            ids = torch.tensor([train_windows[i] for i in idx[j:j + args.micro]], device=device)
            logits = model(input_ids=ids).logits[:, :-1].float()
            loss = nn.functional.cross_entropy(logits.reshape(-1, logits.shape[-1]), ids[:, 1:].reshape(-1))
            (loss * ids.shape[0] / args.batch).backward()
            total += float(loss.detach()) * ids.shape[0] / args.batch
        if args.lam > 0:
            dtmask.regulariser_backward_(model, dtmask.lambda_at(step, args.steps, args.lam))
        opt.step(); opt.zero_grad(set_to_none=True); dtmask.step_all(model)
        losses.append(total)
        if step % max(1, args.steps // 10) == 0:
            print(f"  step {step}/{args.steps} loss {total:.4f}", flush=True)
    stats = dtmask.deletion_stats(model)
    info.update(train_loss_first=losses[0], train_loss_last=float(np.mean(losses[-10:])), deletion_final=stats["deleted_frac_of_targeted"],
                deleted=stats["deleted"], targeted=stats["targeted"], per_layer_min=stats["per_layer_min"], per_layer_max=stats["per_layer_max"])
    return info


def load_text_windows(model_name: str, revision, length: int, n_train: int, n_test: int, n_calib: int) -> dict:
    """wikitext-2 (raw) from its parquet files (no `datasets` package: its huggingface-hub pin clashes with transformers 4.57)."""
    import hashlib
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name, revision=revision)
    ids, sha = {}, {}
    for split in ("train", "test"):
        path = hf_hub_download("Salesforce/wikitext", f"wikitext-2-raw-v1/{split}-00000-of-00001.parquet", repo_type="dataset")
        sha[split] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        ids[split] = tok("\n\n".join(pq.read_table(path).column("text").to_pylist()), add_special_tokens=False)["input_ids"]
    return {"train": make_windows(ids["train"], length, n_train), "calib": make_windows(ids["train"], length, n_calib, offset=n_train * length),
            "test": make_windows(ids["test"], length, n_test), "sha256": sha}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True); ap.add_argument("--revision", default=None)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--arms", default="base,base_q8_0,base_q4_0,dt,dt_q8_0,dt_q4_0,dt_then_q8_0,dt_then_q4_0")
    ap.add_argument("--targets", default="gate", choices=sorted(dtmask.TARGET_SETS))
    ap.add_argument("--steps", type=int, default=400); ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--micro", type=int, default=2); ap.add_argument("--length", type=int, default=512)
    ap.add_argument("--train-windows", type=int, default=2000); ap.add_argument("--calib-windows", type=int, default=32)
    ap.add_argument("--test-windows", type=int, default=200)
    ap.add_argument("--lr", type=float, default=5e-4); ap.add_argument("--eta", type=float, default=1 / 2048)
    ap.add_argument("--prior-strength", type=float, default=3.0); ap.add_argument("--lam", type=float, default=1e-5)
    ap.add_argument("--alpha-start", type=float, default=100.0); ap.add_argument("--alpha-end", type=float, default=1000.0)
    ap.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu"); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    device = torch.device(a.device)
    windows = load_text_windows(a.model, a.revision, a.length, a.train_windows, a.test_windows, a.calib_windows)
    done = json.loads(a.out.read_text()) if a.out.exists() else {"args": {k: str(v) for k, v in vars(a).items()}, "arms": {}}
    done["data_sha256"] = windows["sha256"]
    wanted = a.arms.split(",")
    a.then = [x[len("dt_then_"):] for x in wanted if x.startswith("dt_then_")]
    for arm in [x for x in wanted if not x.startswith("dt_then_")]:
        if arm in done["arms"]:
            print(arm, "already done"); continue
        print("==", arm, flush=True)
        r = done["arms"][arm] = run_arm(arm, a, windows, device)
        for q, sub in r.pop("then", {}).items():
            done["arms"][f"dt_then_{q}"] = sub
        print(f"{arm}: NLL {r['test_nll_mean']:.4f}, deleted {r.get('deletion_final')}, {r['train_seconds']}s, peak {r.get('peak_cuda_gb')} GB", flush=True)
        a.out.write_text(json.dumps(done, indent=1))
    arms = done["arms"]
    done["paired"] = {f"{x}-{y}": paired_bootstrap(arms[x]["per_window_nll"], arms[y]["per_window_nll"])
                      for x, y in (("dt", "base"), ("dt_q8_0", "base_q8_0"), ("dt_q4_0", "base_q4_0"), ("dt_q8_0", "dt"),
                                   ("dt_q4_0", "dt"), ("dt_then_q8_0", "dt_q8_0"), ("dt_then_q4_0", "dt_q4_0")) if x in arms and y in arms}
    a.out.write_text(json.dumps(done, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
