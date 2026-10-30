"""Run JSON -> Markdown, two-run comparison, baseline and slowest-parts files.

Build it against perfkit.schema.example_run(); no need to wait for bench.

    python -m perfkit.report results/runs/<tag>.json
    python -m perfkit.report run1.json --compare run2.json --baseline results/baseline_v0.md --slowest results/slowest5_v0.md

MVP
  * render(run) -> Markdown: header (GPU, dtype, B x T, torch, commit), step stats, MFU, per-region table
    (ms, p90, % of step, level), "time by part type" (sum over layers), five slowest leaf parts.
  * compare(a, b, tol_pct=5, gate_level=2) -> (rows, ok, problems): the whole step plus every region with
    level <= gate_level must be within tol_pct. NO exemption for small parts. Refuse runs on different
    GPUs or with different configs. Level-3 rows are listed as information only.
  * baseline_md(...): GPU name, commit, config, PASS/FAIL, the comparison table.
  * slowest_md(run): five slowest parts, each: ms and % of step, why (bound + evidence), trace reference,
    one week-2 idea.
Extra: roofline predictions (perfkit/roofline.py), per-part trace files cut from the full trace.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

# Config that changes the work a step does (aligned with bench.COMPARE_CONFIG).
COMPARE_CONFIG = [
    ("model", None),
    ("optim", None),
    ("run", "compile"),
    ("run", "grad_clip"),
    ("data", "source"),
]


def _f(x, digits=3):
    if x is None:
        return "-"
    try:
        return f"{float(x):.{digits}f}"
    except (TypeError, ValueError):
        return str(x)


def _pct_delta(x, y) -> float | None:
    """Relative percent gap: (slower/faster - 1) * 100. Same rule as bench.quick_compare."""
    if x is None or y is None:
        return None
    if x == y:
        return 0.0
    if min(x, y) > 0:
        return (max(x, y) / min(x, y) - 1) * 100
    return math.inf


def _cfg_get(run: dict, section: str, key: str | None):
    sec = run.get("config", {}).get(section, {})
    if key is None:
        return sec
    return sec.get(key) if isinstance(sec, dict) else None


def _batch_size(run: dict):
    meta = run.get("meta") or {}
    if "batch_size" in meta and meta["batch_size"] is not None:
        return meta["batch_size"]
    return (run.get("config") or {}).get("run", {}).get("batch_size")


def _dtype(run: dict):
    meta = run.get("meta") or {}
    if meta.get("dtype") is not None:
        return meta["dtype"]
    return (run.get("config") or {}).get("run", {}).get("dtype")


def _seq_len(run: dict):
    meta = run.get("meta") or {}
    if meta.get("seq_len") is not None:
        return meta["seq_len"]
    return (run.get("config") or {}).get("model", {}).get("block_size")


def _refuse(a: dict, b: dict) -> list[str]:
    """Why two runs cannot be a baseline pair. Besides the work and the GPU, both runs must time the SAME
    committed code: one commit, and a clean tree (dirty is False; None means it could not be checked)."""
    problems = []
    for k in ("gpu", "vocab_size", "commit"):
        if a.get("meta", {}).get(k) != b.get("meta", {}).get(k):
            problems.append(f"different {k}: {a.get('meta', {}).get(k)} vs {b.get('meta', {}).get(k)}")
    for run in (a, b):
        meta = run.get("meta", {})
        if meta.get("dirty") is not False:
            problems.append(f"run {meta.get('tag')}: dirty={meta.get('dirty')}: not a clean git checkout of the commit")
    if _dtype(a) != _dtype(b):
        problems.append(f"different dtype: {_dtype(a)} vs {_dtype(b)}")
    if _batch_size(a) != _batch_size(b):
        problems.append(f"different batch_size: {_batch_size(a)} vs {_batch_size(b)}")
    if _seq_len(a) != _seq_len(b):
        problems.append(f"different seq_len: {_seq_len(a)} vs {_seq_len(b)}")
    for section, key in COMPARE_CONFIG:
        va = _cfg_get(a, section, key)
        vb = _cfg_get(b, section, key)
        if va != vb:
            if key is None:
                problems.append(f"different {section} config")
            else:
                problems.append(f"different {section}.{key}: {va} vs {vb}")
    return problems


def _step_ms(run: dict):
    return run["clean"]["step_ms"]["median"]


def _regions(run: dict) -> dict:
    return (run.get("layer") or {}).get("regions") or {}


def _part_type_key(name: str) -> str:
    return re.sub(r"block\d+", "block*", name)


def _part_type_sums(regions: dict) -> dict[str, float]:
    sums: dict[str, float] = {}
    for name, r in regions.items():
        key = _part_type_key(name)
        sums[key] = sums.get(key, 0.0) + float(r["median"])
    return sums


def _is_leaf(name: str, regions: dict) -> bool:
    """A leaf is not a parent prefix of another region name (e.g. fwd:block0 vs fwd:block0.attn.qkv)."""
    prefix = name + "."
    phase_prefix = name + ":"
    for other in regions:
        if other == name:
            continue
        if other.startswith(prefix) or other.startswith(phase_prefix):
            return False
    return True


def _leaf_regions(run: dict) -> list[tuple[str, dict]]:
    regions = _regions(run)
    level3 = [(n, r) for n, r in regions.items() if r.get("level") == 3 and _is_leaf(n, regions)]
    if level3:
        return level3
    deepest = [(n, r) for n, r in regions.items() if _is_leaf(n, regions)]
    return deepest


def _five_slowest(run: dict) -> list[tuple[str, dict, float]]:
    step = _step_ms(run) or 1.0
    leaves = _leaf_regions(run)
    ranked = sorted(leaves, key=lambda nr: float(nr[1]["median"]), reverse=True)[:5]
    out = []
    for name, r in ranked:
        pct = 100.0 * float(r["median"]) / step
        out.append((name, r, pct))
    return out


def render(run: dict) -> str:
    meta = run.get("meta") or {}
    cfg_run = (run.get("config") or {}).get("run") or {}
    cfg_model = (run.get("config") or {}).get("model") or {}
    metrics = run.get("metrics") or {}
    clean = run.get("clean") or {}
    st = clean.get("step_ms") or {}

    gpu = meta.get("gpu") or "-"
    dtype = _dtype(run) or "-"
    b = _batch_size(run)
    t = _seq_len(run) or cfg_model.get("block_size")
    torch_v = meta.get("torch") or "-"
    commit = meta.get("commit") or "-"
    dirty = " (DIRTY)" if meta.get("dirty") else ""
    tag = meta.get("tag") or "-"

    mfu = metrics.get("mfu")
    mfu_s = f"{100 * mfu:.1f}%" if mfu is not None else "-"
    hfu = metrics.get("hfu")
    hfu_s = f"{100 * hfu:.1f}%" if hfu is not None else "-"
    tps = metrics.get("tokens_per_s")
    tps_s = f"{tps:,.0f}" if tps is not None else "-"

    step_base = st.get("median") or 1.0
    lines = [
        f"# Bench report — {tag}",
        "",
        f"**GPU:** {gpu}  |  **dtype:** {dtype}  |  **B x T:** {b} x {t}  |  **torch:** {torch_v}",
        f"**commit:** `{commit}`{dirty}  |  **tag:** {tag}",
        "",
        "## Step (clean)",
        "",
        f"- median: {_f(st.get('median'))} ms",
        f"- p10..p90: {_f(st.get('p10'))} .. {_f(st.get('p90'))} ms",
        f"- tokens/s: {tps_s}",
        f"- MFU: {mfu_s}  |  HFU: {hfu_s}",
        "",
    ]

    regions = _regions(run)
    if regions:
        lines += [
            "## Regions",
            "",
            f"| part | median ms | p90 | % of step | level |",
            f"| :--- | ---: | ---: | ---: | ---: |",
        ]
        for name, r in regions.items():
            pct = 100.0 * float(r["median"]) / float(step_base)
            lines.append(
                f"| {name} | {_f(r['median'])} | {_f(r.get('p90'))} | {_f(pct, 1)} | {r.get('level')} |"
            )
        lines.append("")

        sums = _part_type_sums(regions)
        lines += [
            "## Time by part type (sum over layers)",
            "",
            f"| part type | median ms sum | % of step |",
            f"| :--- | ---: | ---: |",
        ]
        for key in sorted(sums, key=sums.get, reverse=True):
            pct = 100.0 * sums[key] / float(step_base)
            lines.append(f"| {key} | {_f(sums[key])} | {_f(pct, 1)} |")
        lines.append("")

    lines += ["## Five slowest leaf parts", ""]
    for i, (name, r, pct) in enumerate(_five_slowest(run), 1):
        lines.append(f"{i}. `{name}` — {_f(r['median'])} ms ({_f(pct, 1)}% of step)")
    lines.append("")
    return "\n".join(lines)


def compare(a: dict, b: dict, tol_pct: float = 5.0, gate_level: int = 2):
    problems = _refuse(a, b)
    rows = []
    ok = not problems

    pairs = [("step (clean)", _step_ms(a), _step_ms(b))]
    ra, rb = _regions(a), _regions(b)
    gated_names = [n for n, r in ra.items() if r["level"] <= gate_level]
    gated_names += [n for n, r in rb.items() if r["level"] <= gate_level and n not in ra]
    for name in gated_names:
        pairs.append((name, ra[name]["median"] if name in ra else None, rb[name]["median"] if name in rb else None))

    if a.get("checkpoint") and b.get("checkpoint"):
        pairs.append(
            (
                "checkpoint save",
                a["checkpoint"]["save_ms"]["median"],
                b["checkpoint"]["save_ms"]["median"],
            )
        )
    ca = (a.get("comm") or {}).get("moe_a2a") or {}
    cb = (b.get("comm") or {}).get("moe_a2a") or {}
    if ca.get("measured") and cb.get("measured"):
        pairs.append(("moe all-to-all", ca["per_step_ms"], cb["per_step_ms"]))

    for name, x, y in pairs:
        if x is None or y is None:
            rows.append((name, x, y, None, "MISSING"))
            ok = False
            continue
        diff = _pct_delta(x, y)
        good = diff is not None and diff <= tol_pct
        ok = ok and good
        rows.append((name, x, y, diff, "ok" if good else "FAIL"))

    # Level > gate_level: information only (listed, not gated).
    info_names = sorted(
        {n for n, r in ra.items() if r["level"] > gate_level}
        | {n for n, r in rb.items() if r["level"] > gate_level}
    )
    for name in info_names:
        x = ra[name]["median"] if name in ra else None
        y = rb[name]["median"] if name in rb else None
        diff = _pct_delta(x, y) if x is not None and y is not None else None
        rows.append((name, x, y, diff, "info"))

    return rows, ok, problems


def baseline_md(a: dict, b: dict, rows, ok, problems) -> str:
    meta_a = a.get("meta") or {}
    meta_b = b.get("meta") or {}
    verdict = "PASS" if ok else "FAIL"
    lines = [
        f"# Baseline comparison — {verdict}",
        "",
        f"**GPU:** {meta_a.get('gpu')} (vs {meta_b.get('gpu')})",
        f"**commit a:** `{meta_a.get('commit')}`",
        f"**commit b:** `{meta_b.get('commit')}`",
        f"**config a:** tag={meta_a.get('tag')} batch={_batch_size(a)} dtype={_dtype(a)} T={_seq_len(a)}",
        f"**config b:** tag={meta_b.get('tag')} batch={_batch_size(b)} dtype={_dtype(b)} T={_seq_len(b)}",
        f"**result:** {verdict}",
        "",
    ]
    if problems:
        lines.append("## Refuse / problems")
        lines.append("")
        for p in problems:
            lines.append(f"- {p}")
        lines.append("")

    lines += [
        "## Comparison table",
        "",
        "| part | a ms | b ms | diff % | verdict |",
        "| :--- | ---: | ---: | ---: | :--- |",
    ]
    for name, x, y, diff, verdict_row in rows:
        lines.append(
            f"| {name} | {_f(x)} | {_f(y)} | {_f(diff, 2) if diff is not None else '-'} | {verdict_row} |"
        )
    lines.append("")
    return "\n".join(lines)


def slowest_md(run: dict) -> str:
    meta = run.get("meta") or {}
    trace = (run.get("trace") or {}).get("trace_file")
    lines = [
        "# Five slowest leaf parts",
        "",
        f"**GPU:** {meta.get('gpu')}  |  **tag:** {meta.get('tag')}  |  **commit:** `{meta.get('commit')}`",
        "",
    ]
    for i, (name, r, pct) in enumerate(_five_slowest(run), 1):
        level = r.get("level")
        lines += [
            f"## {i}. `{name}` (level {level})",
            "",
            f"- **ms:** {_f(r['median'])}",
            f"- **% of step:** {_f(pct, 1)}%",
            f"- **why (placeholder):** bound unknown until a real GPU trace; evidence = region median from run JSON.",
            f"- **trace reference:** {trace or '(no trace on this run)'}",
            f"- **week-2 idea:** profile this part; check PARTS.md switch for a faster registry entry.",
            "",
        ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render / compare perfkit run JSON to Markdown.")
    ap.add_argument("run", help="Primary run JSON path")
    ap.add_argument("--compare", help="Earlier / other run JSON to compare against")
    ap.add_argument("--baseline", help="Write baseline comparison Markdown here")
    ap.add_argument("--slowest", help="Write five-slowest Markdown here")
    ap.add_argument("--tol-pct", type=float, default=5.0)
    ap.add_argument("--gate-level", type=int, default=2)
    args = ap.parse_args(argv)

    run_path = Path(args.run)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    md_path = run_path.with_suffix(".md")
    md_path.write_text(render(run), encoding="utf-8")
    print(f"[report] render -> {md_path}")

    if args.slowest:
        Path(args.slowest).write_text(slowest_md(run), encoding="utf-8")
        print(f"[report] slowest -> {args.slowest}")

    if args.compare:
        other = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        rows, ok, problems = compare(run, other, tol_pct=args.tol_pct, gate_level=args.gate_level)
        for p in problems:
            print(f"[refuse] {p}")
        print(f"[report] compare: {'PASS' if ok else 'FAIL'}")
        if args.baseline:
            Path(args.baseline).write_text(baseline_md(run, other, rows, ok, problems), encoding="utf-8")
            print(f"[report] baseline -> {args.baseline}")
        return 0 if ok else 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
