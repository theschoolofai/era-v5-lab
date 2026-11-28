#!/usr/bin/env python3
"""Write Team 10's results note for the quantized rollout mismatch from the run's JSON files (no number is typed by hand).

    python make_g10_note.py --llama <run dir with <format>.json files> --torch <run dir>/torch_reference.json \\
        --model sarvam-1 --pr-this <link> --pr-baseline <link> --notebook-version 3d49ae3f859e --out quant_rollout_mismatch_pytorch.md

Columns follow rl/fast_rollouts_v1.md section 2 of the week 5 branch, with the prompt-clustered 95% intervals:
Format | tokens outside [1 - eps, 1 + eps] (below / above) | |log-ratio| quantiles | k3 | top-1 agreement | rollout tok/s |
speed against the llama.cpp bf16 sampler of the same run (same harness, same session). That last column is NOT a speed
against PyTorch bf16: no PyTorch decode speed is measured, and the note says so.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path


def load_llama(run_dir: Path) -> dict:
    """{format: result row} from the per-format JSON files of stage 1, plus the settings of the first file."""
    rows, meta = {}, None
    for p in sorted(run_dir.glob("*.json")):
        if p.name in ("torch_reference.json", "environment.json"):
            continue
        d = json.loads(p.read_text())
        # runs made before the prompt selection existed do not record it: None, and the note says so
        meta = meta or {k: d.get(k) for k in ("reference", "prompts", "prompt_selection", "prompt_categories", "k", "max_new", "eps", "temperature")}
        for f in d["formats"]:
            rows[f["format"]] = f
    return {"rows": rows, "meta": meta}


def pct(x: float) -> str:
    return f"{100 * x:.2f}%"


def ci(a: list, fmt) -> str:
    return f"[{fmt(a[0])}, {fmt(a[1])}]"


def render(llama: dict, torch_ref: dict, a) -> str:
    meta, speeds = llama["meta"], llama["rows"]
    order = [f["format"] for f in torch_ref["formats"]]
    base_speed = speeds["bf16"]["rollout_tokens_per_s"] if "bf16" in speeds else None
    eps = torch_ref["eps"]
    cats = (", ".join(f"{v} {k}" for k, v in meta["prompt_categories"].items()) if meta["prompt_categories"]
            else "composition not recorded by the script version of this run" + (f"; {a.prompt_note}" if a.prompt_note else ""))
    selection = meta["prompt_selection"] or "first (not recorded)"
    lines = [f"# Quantized-rollout mismatch against a PyTorch bf16 reference: {a.model} (Team 12 follow-up to #894)", "",
             f"**Scope and limits:** {a.model}, {a.hardware}, {meta['k']} rollouts per prompt, at most {meta['max_new']} new tokens, "
             f"eps = {eps}, temperature = {meta['temperature']} (Team 10's defaults). Prompts: {meta['prompts']} from the fixed prompt file, "
             f"selection `{selection}` ({cats}). The sampler is a quantized llama.cpp GGUF; the reference scores the same token ids in "
             f"PyTorch ({torch_ref['dtype']} weights, fp32 logits, {torch_ref['device']}, torch {torch_ref['torch']}), the setup of `rl-loop/policy.py`. "
             "Intervals are 95% percentile intervals that resample prompts (the rollouts of a prompt are not independent). "
             "One seed, one model. Mean KL is not available in PyTorch mode (it needs the sampler's full distribution). "
             "Rollout tok/s is llama-cpp-python decode on that GPU, one stream at a time, not a rollout engine's throughput.", "",
             f"Reference model: `{torch_ref['reference']}`. Notebook version `{a.notebook_version}` (G12 `rollout_mismatch.ipynb`). "
             f"Source PRs: this work {a.pr_this}; the llama.cpp-reference baseline {a.pr_baseline}.", "",
             "| Format | Tokens outside [0.8, 1.2] (below / above) | 95% interval | abs log-ratio p50 / p90 / p99 | k3 | k3 95% interval | Top-1 agreement | Rollout tok/s | Speed vs llama.cpp bf16 (same harness) |",
             "|---|---:|---|---|---:|---|---:|---:|---:|"]
    for f in torch_ref["formats"]:
        c = f["ci95_by_prompt"]
        q = f["abs_logratio_p50_p90_p99_p999"]
        tps = speeds[f["format"]]["rollout_tokens_per_s"] if f["format"] in speeds else None
        ratio = "-" if not (tps and base_speed) else f"{tps / base_speed:.2f}x"
        lines.append(f"| `{f['format']}` | **{pct(f['outside'])}** ({pct(f['below'])} / {pct(f['above'])}) | {ci(c['outside'], pct)} | "
                     f"{q[0]:.3g} / {q[1]:.3g} / {q[2]:.3g} | **{f['k3']:.4f}** | {ci(c['k3'], lambda v: f'{v:.4f}')} | "
                     f"{pct(f['top1_agreement'])} {ci(c['top1_agreement'], pct)} | {'-' if tps is None else f'{tps:.1f}'} | {ratio} |")
    lines += ["", "**Reading the table**"]
    if "bf16" in order:
        b = next(f for f in torch_ref["formats"] if f["format"] == "bf16")
        lines.append(f"- The `bf16` row has no quantization in it: llama.cpp's bf16 sampler against the PyTorch reference. It is the engine-to-engine "
                     f"floor ({pct(b['outside'])} of tokens outside, k3 {b['k3']:.4f}); a quantized row's excess over it is the quantization part.")
    lines.append("- The speed column divides a format's rollout tok/s by the `bf16` sampler's tok/s from the same run and session. It is not a speedup "
                 "against PyTorch bf16 decoding, which was not measured." if base_speed else
                 "- No `bf16` sampler row was run, so no speed ratio is given.")
    lines.append(f"- Team 10's stop rule (`k3 <= 0.05`) holds on the formats whose k3 and interval upper bound are at or below 0.05: "
                 + (", ".join(f"`{f['format']}`" for f in torch_ref["formats"] if f["ci95_by_prompt"]["k3"][1] <= 0.05) or "none") + ".")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--llama", required=True, type=Path, help="run folder with the per-format JSON files of stage 1")
    ap.add_argument("--torch", required=True, type=Path, help="torch_reference.json of stage 2")
    ap.add_argument("--model", required=True); ap.add_argument("--notebook-version", required=True)
    ap.add_argument("--pr-this", required=True); ap.add_argument("--pr-baseline", required=True)
    ap.add_argument("--hardware", default="Kaggle T4 x2", help="where the sampler ran, as written in the note")
    ap.add_argument("--prompt-note", default="", help="free text on the prompts, for runs that did not record their composition")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.write_text(render(load_llama(a.llama), json.loads(a.torch.read_text()), a))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
