#!/usr/bin/env python3
"""Write Team 10's results note for Deletion Tuning on a quantized base from the run's results.json (no number typed by hand).

    python make_g10_note.py --results <run dir>/results.json --pr <link> --notebook-version 0d78c992a33b --out dt_quantized_base.md

Layout follows results/lab5_dt_muon_recompute.md of the week 5 branch: a scope and limits line, the exact reproduction
command with a link to the G12 PR, then one table across the arms: held-out NLL with the paired interval against the
same-format base, share of weights deleted, memory (storage, DT state, measured peak), and an optimizer-and-mask overhead note.
"""
from __future__ import annotations

import argparse, json
from pathlib import Path

ORDER = ["base", "base_q8_0", "base_q4_0", "dt", "dt_q8_0", "dt_q4_0", "dt_then_q8_0", "dt_then_q4_0"]
LABEL = {"base": "no DT, unquantized", "base_q8_0": "no DT, Q8_0", "base_q4_0": "no DT, Q4_0", "dt": "DT, unquantized base",
         "dt_q8_0": "DT on Q8_0 base", "dt_q4_0": "DT on Q4_0 base", "dt_then_q8_0": "DT then quantize to Q8_0", "dt_then_q4_0": "DT then quantize to Q4_0"}
VS = {"dt": "base", "dt_q8_0": "base_q8_0", "dt_q4_0": "base_q4_0", "dt_then_q8_0": "base_q8_0", "dt_then_q4_0": "base_q4_0"}


def gb(x) -> str:
    return "-" if x is None else f"{x / 1e9:.2f}"


def render(res: dict, a) -> str:
    args, arms = res["args"], res["arms"]
    paired = res.get("paired", {})
    first = next(iter(arms.values()))
    masked = next((v["memory"]["masked_weights"] for v in arms.values() if v["memory"]["masked_weights"]), 0)
    lines = [f"# Deletion Tuning on a quantized base (Team 12 with Team 10, Lab 5)", "",
             f"**Scope and limits:** {args['model']} (revision `{args.get('revision', 'None')}`), `{args['targets']}` targets, wikitext-2 (raw) with next-token loss "
             f"on every token, {args['steps']} steps, batch {args['batch']} x {args['length']} tokens, lr {args['lr']}, seed {args['seed']}, one seed. A small-scale "
             "mechanics check on a small base model: not an SFT slice, not a main-run claim, and not G10's chat-format question. Held-out NLL is on "
             f"{first['test_windows']} wikitext-2 test windows; intervals are paired bootstrap over windows, not over seeds. "
             "The loop is simpler than `sft/bench/train.py` (constant lr, no warmup, no cosine, no clipping), the same for every arm. "
             "Q8_0 and Q4_0 are llama.cpp's block formats (checked against gguf-py), kept packed on the targeted layers.", "",
             "**Exact reproduction:**", "```bash",
             f"python teams/12-quantization/dt_quant/dt_on_quantized.py --model {args['model']}"
             + (f" --revision {args['revision']}" if args.get('revision') not in (None, 'None') else "")
             + f" --out results.json --arms {args['arms']} --steps {args['steps']} --batch {args['batch']} --micro {args['micro']} --length {args['length']} "
             f"--train-windows {args['train_windows']} --test-windows {args['test_windows']} --lr {args['lr']} --seed {args['seed']} --device cuda",
             "```", f"On Kaggle: G12 notebook `dt_on_quantized.ipynb` version `{a.notebook_version}`. G12 PR: {a.pr}. Raw output: `results.json`.", "",
             "| Arm | Held-out NLL | Paired change vs same-format base (95% interval) | Deleted (% of targeted) | Prior-deleted at init | Weights stored (GB) | DT state (GB) | Peak CUDA (GB) | Train (s) |",
             "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
    for name in [n for n in ORDER if n in arms]:
        r = arms[name]
        base = VS.get(name)
        p = paired.get(f"{name}-{base}") if base else None
        change = "-" if not p else f"{p['mean_diff']:+.4f} [{p['ci95'][0]:+.4f}, {p['ci95'][1]:+.4f}]"
        dele = "-" if "deletion_final" not in r else f"{100 * r['deletion_final']:.3f}"
        prior = "-" if "wanda_prior" not in r else f"{r['wanda_prior']['prior_deleted']:,}"
        m = r["memory"]
        lines.append(f"| `{name}` ({LABEL[name]}) | {r['test_nll_mean']:.4f} | {change} | {dele} | {prior} | {gb(m['weights_bytes'])} | "
                     f"{gb(m['dt_state_bytes'])} | {r.get('peak_cuda_gb', '-')} | {r.get('train_seconds', '-')} |")
    if "dt_q8_0-dt" in paired or "dt_q4_0-dt" in paired:
        lines += ["", "Direct comparison with DT on the unquantized base (paired, 95% interval): "
                  + "; ".join(f"`{k}` {v['mean_diff']:+.4f} [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]" for k, v in paired.items() if k in ("dt_q8_0-dt", "dt_q4_0-dt"))
                  + "."]
    stored = ", ".join(f"{LABEL[n]}: {gb(arms[n]['memory']['weights_bytes'])} GB" for n in ("dt", "dt_q8_0", "dt_q4_0") if n in arms)
    lines += ["", "## Optimizer and mask overhead", "",
              f"DT keeps one FP32 logit per targeted weight, its gradient, and two Adam moments: 4 + 4 + 8 = **16 bytes per masked weight**, whatever the base format. "
              f"Here {masked:,} weights are targeted, so the DT state is **{gb(masked * 16)} GB** (the `DT state` column). All decoder linear weights are stored as: {stored}. "
              "A quantized base can therefore save at most the weight part of the memory. The `Weights stored` column is storage, not training memory: the `Peak CUDA` column is "
              "what the run measured, and it need not fall with the format, because the packed layer dequantizes on every read and `W * mask` keeps that float32 copy for backward. "
              "Read the `Peak CUDA` column before claiming any training-memory saving.",
              "", "Weights that Q8_0 or Q4_0 rounded to exactly zero are kept out of the Wanda prior's threshold (otherwise the share of a layer at zero sets the threshold to 0 and no weight "
              "is marked); `Prior-deleted at init` should be of the same order on every DT arm."]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True, type=Path); ap.add_argument("--pr", required=True)
    ap.add_argument("--notebook-version", required=True); ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    a.out.write_text(render(json.loads(a.results.read_text()), a))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
