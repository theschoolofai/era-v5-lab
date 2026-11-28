#!/usr/bin/env python3
"""Build the Lab 5 per bit-width table (size, memory, speed, quality loss) from everyone's rows.

  python build_table.py --rows rows/*.csv --scores ./out/dryrun2-g12/scores.json \
      --prompts ./out/dryrun2-g12/prompts/summary.json --out table.md

--rows: CSVs written by measure_mac.py, one per Mac (16, 32 and 64 GB). --scores and --prompts: the dry run 2 job's
scores.json (quantize_eval.py) and prompts/summary.json (flow_fixed_prompts.py); both are optional, so the speed and
memory part can be built before the job has run. Quality is always against bf16 of the same export.
The script checks the rows before it writes anything: every row has the measure_mac.py columns, and the same model and
format has one sha256 everywhere (rows from different Macs, and the job's files). A mismatch is listed, not hidden.
"""
import argparse, csv, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from measure_mac import FIELDS  # noqa: E402

BITS = {'bf16': 16, 'F16': 16, 'Q8_0': 8, 'Q6_K': 6, 'Q5_K_M': 5, 'Q5_K_S': 5, 'Q4_K_M': 4, 'Q4_K_S': 4, 'Q4_0': 4,
        'Q3_K_M': 3, 'Q3_K_S': 3, 'Q2_K': 2}


def order(fmt: str) -> tuple:
    return (-BITS.get(fmt, 0), fmt)


def read_rows(paths: list[Path]) -> list[dict]:
    rows = []
    for p in paths:
        with open(p, newline='') as f:
            r = csv.DictReader(f)
            missing = [c for c in FIELDS if c not in (r.fieldnames or [])]
            if missing:
                sys.exit(f'{p}: missing columns {missing} (write rows with measure_mac.py)')
            rows += [dict(x, _file=p.name) for x in r]
    # the same file measured twice on the same Mac: keep the last row
    keep = {}
    for x in rows:
        keep[(x['gguf_sha256'], x['machine'], x['ram_gb'], x['contributor'])] = x
    return list(keep.values())


def load(p: Path | None) -> dict | None:
    return json.loads(p.read_text(encoding='utf-8')) if p else None


def sha_mismatches(rows: list[dict], scores: dict | None) -> list[str]:
    seen: dict[tuple, dict[str, list[str]]] = {}
    for x in rows:
        seen.setdefault((x['model'], x['format']), {}).setdefault(x['gguf_sha256'], []).append(f'{x["contributor"]} {x["ram_gb"]} GB')
    for f in (scores or {}).get('formats', []):
        if f.get('sha256'):
            seen.setdefault((f['model'], f['format']), {}).setdefault(f['sha256'], []).append('dry run 2 job')
    return [f'{m} {fmt}: ' + '; '.join(f'{s[:12]} ({", ".join(w)})' for s, w in shas.items())
            for (m, fmt), shas in sorted(seen.items()) if len(shas) > 1]


def agreement_cells(prompts: dict | None, fmt: str) -> tuple[str, str]:
    if not prompts:
        return '', ''
    ag = prompts.get('formats', {}).get(fmt, {}).get('agreement_with_bf16')
    if fmt == 'bf16':
        return 'reference', 'reference'
    if not ag:
        return '', ''
    parts = ag.values() if 'identical_outputs' not in ag else [ag]
    names = list(ag) if 'identical_outputs' not in ag else ['all']
    ident = ' / '.join(f'{a["identical_outputs"]}/{a["of"]}' for a in parts)
    pref = ' / '.join(f'{a["mean_shared_prefix_fraction"]:.3f}' for a in parts)
    label = '' if names == ['all'] else f' ({" / ".join(names)})'
    return ident + label, pref


def quality_table(scores: dict, prompts: dict | None) -> list[str]:
    fm = {f['format']: f for f in scores.get('formats', [])}
    base = fm.get('bf16', {}).get('score')
    out = ['| Bits | Format | bpw | Size (MB) | Score | Change vs bf16 | Same output as bf16 | Shared prefix with bf16 |',
           '|---:|---|---:|---:|---:|---:|---|---|']
    for fmt in sorted(fm, key=order):
        f = fm[fmt]
        delta = '' if base is None or fmt == 'bf16' else f'{f["score"] - base:+.4f}'
        ident, pref = agreement_cells(prompts, fmt)
        out.append(f'| {BITS.get(fmt, "")} | {fmt} | {f["bpw"]} | {f["size_bytes"] / 1e6:.1f} | {f["score"]:.4f} | '
                   f'{delta} | {ident} | {pref} |')
    model = scores.get('model') or next(iter(fm.values()), {}).get('model', '')
    n = next(iter(fm.values()), {}).get('n_items', '')
    return [f'Model: {model}. Score on {n} items ({next(iter(fm.values()), {}).get("eval_set", "")}).', ''] + out


def speed_table(rows: list[dict]) -> list[str]:
    depth = sorted({x['depth'] for x in rows})
    d = depth[0] if len(depth) == 1 else '/'.join(depth)
    out = [f'| Model | Bits | Format | bpw | Size (MB) | Mac | Prompt tok/s (512) | Gen tok/s (128) | Gen tok/s at {d} '
           f'| Memory at {d}: weights + KV + compute = total (MB) | KV per 1k tokens (MB) | GPU limit (MB) | Fits | Who |',
           '|---|---:|---|---:|---:|---|---:|---:|---:|---|---:|---:|---|---|']
    for x in sorted(rows, key=lambda x: (x['model'], order(x['format']), int(x['ram_gb'] or 0))):
        out.append(f'| {x["model"]} | {BITS.get(x["format"], "")} | {x["format"]} | {x["bpw"]} | '
                   f'{int(x["size_bytes"]) / 1e6:.1f} | {x["chip"]} {x["ram_gb"]} GB | {x["pp512_tok_s"]} | '
                   f'{x["tg128_tok_s"]} | {x["tg16_at_depth_tok_s"]} | '
                   f'{x["weights_mb"]} + {x["kv_mb"]} + {x["compute_mb"]} = {x["total_mb"]} | {x["kv_mb_per_1k"]} | '
                   f'{x["gpu_working_set_mb"]} | {x["fits_gpu"]} | {x["contributor"]} |')
    return out


def build(rows: list[dict], scores: dict | None, prompts: dict | None) -> str:
    lines = ['# Size, memory, speed and quality per bit-width', '']
    if scores:
        lines += ['## Quality loss against bf16 (dry run 2 job)', ''] + quality_table(scores, prompts) + ['']
        if prompts:
            lines += ['Same output: greedy outputs identical to bf16 on the 100 fixed prompts, Team 10\'s slots and our '
                      'fill slots apart. Shared prefix: mean fraction of output tokens before the first difference.', '']
    else:
        lines += ['## Quality loss against bf16', '', 'Not yet: the dry run 2 job has not run.', '']
    if rows:
        runtimes = sorted({x['runtime'] for x in rows})
        d = '/'.join(sorted({x['depth'] for x in rows}))
        lines += ['## Speed and memory per Mac', ''] + speed_table(rows) + [
            '', f'Runtime: {"; ".join(runtimes)}. Memory is what llama.cpp allocates with {d} tokens in the cache, from '
            'its own log: the weights, the KV cache and the compute buffers. Fits: the total is at or under the GPU '
            'working-set limit Metal reports for that Mac. MB = 10^6 bytes.', '']
    else:
        lines += ['## Speed and memory per Mac', '', 'No rows yet.', '']
    bad = sha_mismatches(rows, scores)
    lines += ['## Checks', '']
    lines += [f'- Different files for the same model and format: {b}' for b in bad] or \
             ['- Every model and format has one sha256 across all rows' + (' and the job.' if scores else '.')]
    return '\n'.join(lines) + '\n'


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--rows', nargs='*', type=Path, default=[])
    ap.add_argument('--scores', type=Path)
    ap.add_argument('--prompts', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--strict', action='store_true', help='exit 1 when the same model and format has two sha256 values')
    a = ap.parse_args()
    rows, scores, prompts = read_rows(a.rows), load(a.scores), load(a.prompts)
    text = build(rows, scores, prompts)
    a.out.write_text(text, encoding='utf-8')
    print(text)
    if a.strict and sha_mismatches(rows, scores):
        sys.exit(1)


if __name__ == '__main__':
    main()
