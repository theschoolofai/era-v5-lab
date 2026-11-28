"""Deletion Tuning against full FT and LoRA on a small model of Team 5's real classes (16 routed + 1 shared expert,
top 2): calibration policy and size, hybrid Muon learning rate, and activation recompute. CPU stand-in.

    python dt/run_lab5_dt_study.py --seeds 1 2 --out results/lab5_dt_study.json
    python dt/run_lab5_dt_study.py --seeds 1 2 --coverage --out results/lab5_dt_study_coverage.json

Per seed: a byte-level model is pre-trained on this repository's Markdown (the last tenth is held out), then every arm
starts from that same state and takes the same number of steps on one task (answer six random letters with the first of
them, six times). Reported per arm:
task loss and exact answers on unseen strings, bits per byte on the held-out text before and after (forgetting),
trainable parameters, optimizer state bytes, the size of what has to be shipped (bf16 changed tensors, or the packed
keep mask), step time and the optimizer's share of it, and for DT the deletions of calibrated and uncalibrated experts.

`saved_activation_bytes` counts the tensors autograd holds after one forward pass (parameters excluded). It is a
device-independent size of the activation memory recompute removes, not a peak-memory measurement.

The model is tiny. The study shows how the code behaves and which settings change it; it says nothing about which method
is better at 7B+, where the Deletion Tuning paper makes its claims.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.nn.functional as F
from torch import no_grad  # decorator without a dot: pr-guard reads '+@a.b' as an email

HERE = Path(__file__).resolve().parent
TEAM10 = HERE.parent
REPO = TEAM10.parents[1]
sys.path[:0] = [str(HERE), str(TEAM10 / "capstone"), str(TEAM10 / "rl-loop"), str(TEAM10.parent / "05-architecture" / "harness")]

import check_grad_coverage as check  # noqa: E402
import hybrid_optim as ho  # noqa: E402
import sft_g5  # noqa: E402
from week2 import config as C  # noqa: E402
from week2.model import LanguageModel  # noqa: E402

dtmask = sft_g5.dtmask
LETTERS = b"abcdefghijklmnop"
WIDTH = 64


def make_model(seed: int) -> LanguageModel:
    m = copy.deepcopy(C.load_runtime(str(TEAM10.parent / "05-architecture" / "configs" / "arms" / "t2.yaml"))["model"])
    m.update(vocab_size=256, block_size=128, n_layer=4, n_head=4, n_kv_head=2, n_embd=WIDTH)
    m["moe"] = dict(m["moe"], num_experts=16, top_k=2, num_shared=1, ffn_hidden=32, bias_gamma=0.001)
    rows = torch.randint(0, 255, (256, 32), generator=torch.Generator().manual_seed(1)).to(torch.uint8)
    lengths = torch.randint(1, 5, (256,), generator=torch.Generator().manual_seed(2))
    torch.manual_seed(seed)
    return LanguageModel(m, rows, lengths)


def corpus(limit: int) -> tuple[torch.Tensor, torch.Tensor, dict]:
    files = sorted((REPO / "teams").rglob("*.md"))
    data = b""
    for f in files:
        data += f.read_bytes()
        if len(data) >= limit:
            break
    data = data[:limit]
    cut = len(data) * 9 // 10
    t = torch.frombuffer(bytearray(data), dtype=torch.uint8).long()
    return t[:cut], t[cut:], {"markdown_files": len(files), "bytes": len(data), "heldout_bytes": len(data) - cut,
                              "sha256": hashlib.sha256(data).hexdigest()}


def task_rows(n: int, seed: int) -> torch.Tensor:
    """[n, 16]: "R:" + 6 letters + "=" + the first of those letters six times + "\n"."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        s = bytes(rng.choice(LETTERS) for _ in range(6))
        out.append(list(b"R:" + s + b"=" + s[:1] * 6 + b"\n"))
    return torch.tensor(out, dtype=torch.long)


ANSWER = slice(9, 16)  # the six answer letters and the newline


def task_loss(lm, ids: torch.Tensor) -> torch.Tensor:
    logits = lm(ids, torch.ones_like(ids, dtype=torch.bool))
    return F.cross_entropy(logits[:, ANSWER.start - 1:ANSWER.stop - 1].reshape(-1, 256), ids[:, ANSWER].reshape(-1))


@no_grad()
def task_scores(lm, ids: torch.Tensor) -> dict:
    lm.eval()
    logits = lm(ids, torch.ones_like(ids, dtype=torch.bool))[:, ANSWER.start - 1:ANSWER.stop - 1]
    nll = float(F.cross_entropy(logits.reshape(-1, 256), ids[:, ANSWER].reshape(-1)))
    exact = float((logits.argmax(-1) == ids[:, ANSWER]).all(1).float().mean())  # teacher-forced: every position right
    return {"nll": nll, "exact": exact}


@no_grad()
def bits_per_byte(lm, text: torch.Tensor) -> float:
    lm.eval()
    n = (len(text) - 1) // 128
    x = torch.stack([text[i * 128:i * 128 + 128] for i in range(n)])
    y = torch.stack([text[i * 128 + 1:i * 128 + 129] for i in range(n)])
    total = 0.0
    for a, b in zip(x.split(32), y.split(32)):
        total += float(F.cross_entropy(lm(a, torch.ones_like(a, dtype=torch.bool)).reshape(-1, 256), b.reshape(-1),
                                       reduction="sum"))
    return total / (n * 128) / math.log(2)


def pretrain(lm, train_text: torch.Tensor, steps: int, seed: int) -> float:
    g = torch.Generator().manual_seed(seed)
    opt = torch.optim.AdamW(lm.parameters(), lr=3e-3, betas=(0.9, 0.95), weight_decay=0.01)
    lm.train()
    for step in range(steps):
        for group in opt.param_groups:
            group["lr"] = 3e-3 * min(1.0, (step + 1) / 50) * (0.1 + 0.45 * (1 + math.cos(math.pi * step / steps)))
        at = torch.randint(0, len(train_text) - 129, (16,), generator=g)
        x = torch.stack([train_text[i:i + 128] for i in at])
        y = torch.stack([train_text[i + 1:i + 129] for i in at])
        loss = F.cross_entropy(lm(x, torch.ones_like(x, dtype=torch.bool)).reshape(-1, 256), y.reshape(-1))
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(lm.parameters(), 1.0)
        opt.step()
    lm.zero_grad(set_to_none=True)
    return float(loss)


def saved_activation_bytes(lm, ids: torch.Tensor, recompute: bool) -> int:
    held: dict[tuple, int] = {}
    skip = {p.data_ptr() for p in lm.parameters()} | {b.data_ptr() for b in lm.buffers()}

    def pack(t):
        if t.data_ptr() not in skip:
            held[(t.data_ptr(), t.numel(), t.dtype)] = t.numel() * t.element_size()
        return t

    lm.train()
    with sft_g5.block_recompute(lm, recompute), torch.autograd.graph.saved_tensors_hooks(pack, lambda t: t):
        loss = task_loss(lm, ids)
    loss.backward()
    lm.zero_grad(set_to_none=True)
    return sum(held.values())


def run_arm(base, spec: dict, rows: torch.Tensor, heldout_rows: torch.Tensor, heldout_text, base_bpb: float, a) -> dict:
    lm = copy.deepcopy(base)
    method, seed = spec["method"], spec["seed"]
    opts = SimpleNamespace(seed=seed, steps=a.steps, lora_r=8, lora_alpha=16.0, dt_targets="g5_gate", dt_alpha_start=100.0,
                           dt_alpha_end=1000.0, dt_lambda=1e-5, dt_eta=1 / 2048)
    info = sft_g5.apply_method(lm, method, opts)
    out = {**spec, "trainable_params": info["trainable"]}
    if method == "dt":
        wrapper = sft_g5.G5ForBench(lm)
        rng = random.Random(10_000 + seed)
        calib = rows[rng.sample(range(len(rows)), spec["calib_rows"])]
        batches = ({"input_ids": b, "attention_mask": torch.ones_like(b)} for b in calib.split(16))
        scores = dtmask.wanda_scores(wrapper, batches, "cpu")
        prior = dtmask.apply_wanda_prior(wrapper, scores, opts.dt_eta, 3.0, unseen=spec["unseen"])
        out.update(layers_without_scores=prior["layers_without_scores"], masked_layers=info["masked_layers"],
                   deletion_at_init=dtmask.deletion_stats(lm)["deleted_frac_of_targeted"],
                   unseen_at_init=dtmask.unseen_report(lm, prior["unseen_layer_names"]))
    before = copy.deepcopy({n: p.detach() for n, p in lm.named_parameters() if p.requires_grad})
    opt = ho.build_optimizer(lm.named_parameters(), kind=spec["optimizer"], lr=spec["lr"],
                             muon_lr=spec.get("muon_lr") or spec["lr"], betas=(0.9, 0.95),
                             dt_gate_optim=spec.get("dt_gate_optim", "adamw"))
    order = random.Random(seed)
    lm.train()
    losses = []
    t0 = time.perf_counter()
    with sft_g5.block_recompute(lm, spec.get("recompute", False)):
        for step in range(a.steps):
            batch = rows[order.sample(range(len(rows)), a.batch)]
            opt.scale_lr(min(1.0, (step + 1) / 10) * (0.1 + 0.45 * (1 + math.cos(math.pi * step / a.steps))))
            opt.zero_grad(set_to_none=True)
            loss = task_loss(lm, batch)
            loss.backward()
            if method == "dt":
                dtmask.regulariser_backward_(lm, dtmask.lambda_at(step, a.steps, opts.dt_lambda))
            torch.nn.utils.clip_grad_norm_([p for p in lm.parameters() if p.requires_grad], 1.0)
            opt.step()
            if method == "dt":
                dtmask.step_all(lm)
            losses.append(float(loss))
    seconds = time.perf_counter() - t0
    lm.zero_grad(set_to_none=True)
    state = [v for _, o in opt.named for s in o.state.values() for v in s.values() if torch.is_tensor(v)]
    out.update(loss_first=losses[0], loss_last=losses[-1], step_ms=1000 * seconds / a.steps,
               optim_share=opt.optim_seconds / seconds, optim_state_bytes=sum(v.numel() * v.element_size() for v in state),
               saved_activation_bytes=saved_activation_bytes(lm, rows[:a.batch], spec.get("recompute", False)))
    if method == "dt":
        final = dtmask.deletion_stats(lm)
        out.update(deletion_final=final["deleted_frac_of_targeted"], max_layer_deletion=final["per_layer_max"],
                   unseen_final=dtmask.unseen_report(lm, prior["unseen_layer_names"]), band_final=dtmask.band_stats(lm))
        blob, meta = dtmask.pack_masks(dtmask.bake(lm))  # bake: the hard mask goes into plain Linear layers
        out.update(ship_bytes=len(blob), ship="packed keep mask (packbits + zlib)", mask_bits=meta["bits"])
    else:
        changed = [p for n, p in lm.named_parameters() if p.requires_grad and not torch.equal(p.detach(), before[n])]
        out.update(ship_bytes=2 * sum(p.numel() for p in changed),
                   ship="every changed tensor in bf16" if method == "full" else "LoRA A and B in bf16")
    out.update(task=task_scores(lm, heldout_rows), bpb=bits_per_byte(lm, heldout_text))
    out["bpb_change"] = out["bpb"] - base_bpb
    return out


def arms(seed: int) -> list[dict]:
    dt = {"method": "dt", "seed": seed, "optimizer": "adamw", "lr": 5e-4, "unseen": "keep", "calib_rows": 64}
    out = [
        {"arm": "full", "method": "full", "seed": seed, "optimizer": "adamw", "lr": 1e-4},
        {"arm": "full_muon", "method": "full", "seed": seed, "optimizer": "hybrid_muon", "lr": 1e-4, "muon_lr": 1e-3},
        {"arm": "lora", "method": "lora", "seed": seed, "optimizer": "adamw", "lr": 1e-3},
    ]
    for unseen in ("official", "keep"):
        for n in (64, 256):
            out.append({**dt, "arm": f"dt_{unseen}_{n}", "unseen": unseen, "calib_rows": n})
    for mlr in (1e-3, 3e-3, 6e-3):
        out.append({**dt, "arm": f"dt_muon_gates_{mlr:g}", "optimizer": "hybrid_muon", "muon_lr": mlr,
                    "dt_gate_optim": "shape"})
    for name in ("full", "lora", "dt_keep_64"):
        base = next(x for x in out if x["arm"] == name)
        out.append({**base, "arm": f"{name}_recompute", "recompute": True})
    return out


def table(results: list[dict]) -> str:
    by: dict[str, list[dict]] = {}
    for r in results:
        by.setdefault(r["arm"], []).append(r)

    def mean(rs, f):
        return statistics.mean(f(r) for r in rs)

    lines = ["| Arm | Trainable | Task NLL | Exact | Held-out bpb change | Deleted at init / end | Uncalibrated layers (deleted "
             "at end) | Optim state KB | Ship KB | Activations KB | Step ms | Optim share |",
             "|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|"]
    for arm, rs in by.items():
        dele, unseen = "-", "-"
        if rs[0]["method"] == "dt":
            dele = f"{mean(rs, lambda r: r['deletion_at_init']):.3%} / {mean(rs, lambda r: r['deletion_final']):.3%}"
            n = mean(rs, lambda r: r["layers_without_scores"])
            fr = [r["unseen_final"]["unseen"]["deleted_frac"] for r in rs]
            fr = [x for x in fr if x is not None]  # None: calibration reached every layer
            unseen = f"{n:g} of {rs[0]['masked_layers']}" + (f" ({statistics.mean(fr):.2%})" if fr else "")
        lines.append(
            f"| `{arm}` | {rs[0]['trainable_params']:,} | {mean(rs, lambda r: r['task']['nll']):.3f} | "
            f"{mean(rs, lambda r: r['task']['exact']):.3f} | {mean(rs, lambda r: r['bpb_change']):+.4f} | {dele} | {unseen} | "
            f"{mean(rs, lambda r: r['optim_state_bytes']) / 1024:.0f} | {mean(rs, lambda r: r['ship_bytes']) / 1024:.1f} | "
            f"{mean(rs, lambda r: r['saved_activation_bytes']) / 1024:.0f} | {mean(rs, lambda r: r['step_ms']):.1f} | "
            f"{mean(rs, lambda r: r['optim_share']):.1%} |")
    return "\n".join(lines)


@no_grad()
def idle_experts(lm, ids: torch.Tensor) -> set[str]:
    """Name prefixes of the routed experts that get no token the task loss depends on (the model's own expert choice).
    The loss reads the logits of positions ANSWER.start - 1 to ANSWER.stop - 2. In the last block an expert's output
    reaches only its own position; in earlier blocks causal attention carries it to every later one."""
    lm = copy.deepcopy(lm).train()  # a training forward moves the router bias
    idle: set[str] = set()
    moes = [(n, m) for n, m in lm.named_modules() if hasattr(m, "router") and hasattr(m, "topk") and hasattr(m, "experts")]
    for i, (name, m) in enumerate(moes):
        def pre(mod, args, name=name, last=i == len(moes) - 1):
            x, valid = args[0], args[1].clone().bool()
            valid[:, ANSWER.stop - 1:] = False
            if last:
                valid[:, :ANSWER.start - 1] = False
            valid = valid.reshape(-1)
            scores = F.linear(x.reshape(-1, x.shape[-1]).float(), mod.router.weight.float()).softmax(-1)
            used = set(dtmask.g5_expert_choice(mod, scores)[valid].flatten().tolist())
            idle.update(f"{name}.experts.{e}." for e in range(len(mod.experts)) if e not in used)
        m.register_forward_pre_hook(pre)
    task_loss(lm, ids)
    return idle


def grad_coverage(seed: int, a) -> list[dict]:
    """TSAI's rule for speed claims: after one forward and backward of the task loss, the trainable parameters whose
    gradient is None or all zero, with recompute off and on. DT is checked without its regulariser, which would give
    every logit a gradient and hide an idle expert."""
    base, rows = make_model(seed), task_rows(2048, 100 + seed)
    batch = rows[:a.batch]
    results = []
    for method in ("full", "lora", "dt"):
        def factory(method=method):
            lm = copy.deepcopy(base)
            opts = SimpleNamespace(seed=seed, steps=a.steps, lora_r=8, lora_alpha=16.0, dt_targets="g5_gate",
                                   dt_alpha_start=100.0, dt_alpha_end=1000.0, dt_lambda=1e-5, dt_eta=1 / 2048)
            sft_g5.apply_method(lm, method, opts)
            if method == "dt":
                wrapper = sft_g5.G5ForBench(lm)
                batches = ({"input_ids": b, "attention_mask": torch.ones_like(b)} for b in rows[:64].split(16))
                scores = dtmask.wanda_scores(wrapper, batches, "cpu")
                dtmask.apply_wanda_prior(wrapper, scores, opts.dt_eta, 3.0, unseen="keep")
            return lm.train()

        probe = factory()
        idle = idle_experts(probe, batch)
        params = dict(probe.named_parameters())
        reasons = {}
        for name in params:
            if any(name.startswith(prefix) for prefix in idle):
                reasons[name] = "its expert gets no token of this batch that the loss depends on"
            elif name.endswith(".lora_A") and not params[name[:-1] + "B"].any():
                reasons[name] = "lora_B starts at zero, so the first backward gives lora_A no gradient"

        def run(lm, fast_on):
            with sft_g5.block_recompute(lm, fast_on):
                task_loss(lm, batch).backward()

        r = check.compare_fast_vs_ref(f"{method}_recompute", factory, run, allowed_reasons=reasons)
        r.update(seed=seed, idle_experts=len(idle))
        results.append(r)
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--pretrain-steps", type=int, default=800)
    ap.add_argument("--corpus-bytes", type=int, default=500_000)
    ap.add_argument("--only", nargs="+", help="run only these arm names")
    ap.add_argument("--coverage", action="store_true", help="only the gradient-coverage check, recompute off and on")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.coverage:
        checks = [r for seed in a.seeds for r in grad_coverage(seed, a)]
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps({"schema": "g10-lab5-dt-study-coverage/1", "torch": torch.__version__,
                                     "checks": checks}, indent=1), encoding="utf-8")
        for r in checks:
            ref = r["ref_coverage"]
            print(json.dumps({"check": r["check"], "seed": r["seed"], "trainable": ref["trainable_tensors"],
                              "none": ref["none_grad_count"], "zero": ref["zero_grad_count"], "idle_experts": r["idle_experts"],
                              "lists_identical": r["lists_identical"], "max_grad_abs_diff": r["max_grad_abs_diff"],
                              "pass": r["pass"]}), flush=True)
        return 0 if all(r["pass"] for r in checks) else 1
    train_text, heldout_text, corpus_info = corpus(a.corpus_bytes)
    report = {"schema": "g10-lab5-dt-study/1", "args": {k: str(v) for k, v in vars(a).items()}, "torch": torch.__version__,
              "threads": torch.get_num_threads(), "corpus": corpus_info, "base": [], "arms": []}
    for seed in a.seeds:
        base = make_model(seed)
        t0 = time.perf_counter()
        last = pretrain(base, train_text, a.pretrain_steps, seed)
        rows, held = task_rows(2048, 100 + seed), task_rows(512, 900 + seed)
        bpb = bits_per_byte(base, heldout_text)
        report["base"].append({"seed": seed, "pretrain_loss": last, "seconds": time.perf_counter() - t0, "bpb": bpb,
                               "task": task_scores(base, held),
                               "parameters": sum(p.numel() for p in base.parameters())})
        print(json.dumps(report["base"][-1]), flush=True)
        for spec in arms(seed):
            if a.only and spec["arm"] not in a.only:
                continue
            r = run_arm(base, spec, rows, held, heldout_text, bpb, a)
            report["arms"].append(r)
            print(json.dumps({k: r[k] for k in ("arm", "seed", "loss_last", "task", "bpb_change", "step_ms")}), flush=True)
    report["table"] = table(report["arms"])
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(report["table"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
