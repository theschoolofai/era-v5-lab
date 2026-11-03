#!/usr/bin/env python3
"""G12: how far each quantized model drifts from bf16, measured token by token.

    python teams/12-quantization/quality/kl_eval.py                 # all formats, defaults below
    python teams/12-quantization/quality/kl_eval.py --chunks 4      # smoke test

Accuracy on a 200-item eval has a 95% margin of about +/-6.5 points, so it cannot separate Q8_0 from
Q4_K_M. This script compares the full next-token distribution of each format with the bf16 model on
every scored token of a fixed text (WikiText-2 test, pinned), with llama.cpp's llama-perplexity:

  1. bf16 pass: perplexity, and the bf16 log-probabilities saved to a base file (~100 KB per scored token)
  2. one pass per format: perplexity, KL divergence to bf16, how often the top-1 token is the same

One row per format goes to kl.csv next to this script. GGUF files are shared with
scripts/quantize_eval.py (same --work directory and file names); a missing quantized file is made
with the same rule as that script (output layer Q8_0; llama.cpp never quantizes the router).
bf16 OLMoE needs ~14 GB: on a 16 GB Mac use --base-ngl 0 (CPU) or run the bf16 pass on a GPU box.
"""
import argparse, csv, datetime, importlib.util, re, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
# reuse the machine description of the team script, so both CSVs describe machines the same way
_spec = importlib.util.spec_from_file_location('quantize_eval', HERE.parent / 'scripts' / 'quantize_eval.py')
quantize_eval = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(quantize_eval)

TEXTS = {  # pinned parquet; rows are lines that already end in '\n'
    'wikitext2': 'https://huggingface.co/datasets/Salesforce/wikitext/resolve/b08601e04326c79dfdd32d625aee71d232d685c3/'
                 'wikitext-2-raw-v1/test-00000-of-00001.parquet',
}
FIELDS = ['date', 'model', 'revision', 'format', 'size_gb', 'base', 'text', 'chunks', 'ctx', 'tokens_scored',
          'ppl', 'ppl_unc', 'ppl_ratio', 'ppl_ratio_unc', 'kld_mean', 'kld_mean_unc', 'kld_median', 'kld_99',
          'kld_max', 'same_top_p', 'same_top_p_unc', 'rms_dp', 'time_s', 'machine', 'runtime', 'notes']
# llama-perplexity's summary lines (tools/perplexity/perplexity.cpp); '+/-' (printed as U+00B1) separates value and uncertainty
NUM = r'(-?[\d.]+(?:e-?\d+)?)'
PATTERNS = {
    'ppl': rf'Mean PPL\(Q\)\s*:\s*{NUM}\s*\u00b1\s*{NUM}',
    'ppl_ratio': rf'Mean PPL\(Q\)/PPL\(base\)\s*:\s*{NUM}\s*\u00b1\s*{NUM}',
    'kld_mean': rf'Mean\s+KLD:\s*{NUM}\s*\u00b1\s*{NUM}',
    'kld_median': rf'Median\s+KLD:\s*{NUM}',
    'kld_99': rf'99\.0%\s+KLD:\s*{NUM}',
    'kld_max': rf'Maximum KLD:\s*{NUM}',
    'same_top_p': rf'Same top p:\s*{NUM}\s*\u00b1\s*{NUM}',
    'rms_dp': rf'RMS \u0394p\s*:\s*{NUM}',
}


def llama_version(bindir):
    """'version: 0.7.0 (build 11669, commit 620d2225c)' (Homebrew 0.7+) or 'version: 10050 (b15ca938a)' (older)."""
    out = subprocess.run([bin_path('llama-perplexity', bindir), '--version'], capture_output=True, text=True)
    text = out.stdout + out.stderr
    m = re.search(r'build (\d+), commit (\w+)', text) or re.search(r'version: (\d+) \((\w+)\)', text)
    if not m: sys.exit(f'cannot read the llama.cpp version from: {text[:200]!r}')
    return f'llama.cpp {quantize_eval.llama_tag(int(m.group(1)), m.group(2))} ({m.group(2)})'


def bin_path(name, bindir):
    return str(Path(bindir) / name) if bindir else name


def text_file(work, name):
    out = work / f'{name}.test.txt'
    if not out.exists():
        pq_file = work / f'{name}.test.parquet'
        if not pq_file.exists():
            urllib.request.urlretrieve(TEXTS[name], pq_file)
        import pyarrow.parquet as pq  # only needed once, to build the text file
        out.write_text(''.join(pq.read_table(pq_file, columns=['text']).column('text').to_pylist()), encoding='utf-8')
    return out


def perplexity(args, gguf, ngl, extra, log):
    cmd = [bin_path('llama-perplexity', args.llama_bin), '-m', str(gguf), '-c', str(args.ctx),
           '--chunks', str(args.chunks), '-ngl', str(ngl), *extra]
    print('$', ' '.join(cmd), flush=True)
    t0 = time.time()
    with open(log, 'w') as fh:
        subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, check=True)
    return log.read_text(errors='replace'), time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--model', default='allenai/OLMoE-1B-7B-0924')
    ap.add_argument('--revision', default='6d84c48581ece794365f2b8e9cfb043c68ade9c5')
    ap.add_argument('--formats', default='Q8_0,Q6_K,Q5_K_M,Q4_K_M,Q3_K_M,Q2_K')
    ap.add_argument('--base', default='bf16', help='reference format; bf16 is the unquantized model')
    ap.add_argument('--text', default='wikitext2', choices=sorted(TEXTS))
    ap.add_argument('--chunks', type=int, default=64, help='64 x 512 tokens = 16k scored tokens, ~1.6 GB base file')
    ap.add_argument('--ctx', type=int, default=512)
    ap.add_argument('--ngl', type=int, default=99, help='layers on GPU for the quantized formats')
    ap.add_argument('--base-ngl', type=int, default=99, help='layers on GPU for the base pass (0 = CPU)')
    ap.add_argument('--work', default=str(Path.home() / '.cache/era-v5-quant'))
    ap.add_argument('--llama-bin', help='directory with the llama.cpp binaries (default: PATH)')
    ap.add_argument('--out', default=str(HERE / 'kl.csv'))
    ap.add_argument('--notes', default='')
    ap.add_argument('--cleanup', action='store_true', help='delete each quantized GGUF after its pass (small disks, e.g. Kaggle)')
    args = ap.parse_args()

    work = Path(args.work).expanduser()
    name = args.model.split('/')[-1]
    gguf = lambda fmt: work / f'{name}-{fmt}.gguf'  # same names as scripts/quantize_eval.py
    base = gguf(args.base)
    if not base.exists():
        sys.exit(f'{base} not found: run scripts/quantize_eval.py first, or convert the model to {args.base} GGUF')
    runtime, machine = llama_version(args.llama_bin), quantize_eval.machine_string()
    logs = work / 'kl-logs'; logs.mkdir(exist_ok=True)
    tag = f'{name}-{args.base}-{args.text}-c{args.ctx}-n{args.chunks}'
    kld_base = work / f'{tag}.kld'

    # 1. base pass: saves the reference log-probabilities once; reused by every later run with the same tag
    base_ppl = None
    if not kld_base.exists():
        log, base_secs = perplexity(args, base, args.base_ngl,
                            ['-f', str(text_file(work, args.text)), '--kl-divergence-base', str(kld_base)],
                            logs / f'{tag}.log')
        m = re.search(r'Final estimate: PPL = ([\d.]+) \+/- ([\d.]+)', log)
        if not m: sys.exit(f'no perplexity in {logs / (tag + ".log")}')
        base_ppl = (float(m.group(1)), float(m.group(2)))
        print(f'{args.base}: PPL {base_ppl[0]:.4f} +/- {base_ppl[1]:.4f}', flush=True)

    out = Path(args.out); new = not out.exists()
    with open(out, 'a', newline='') as fh:
        w = csv.DictWriter(fh, FIELDS)
        if new: w.writeheader()
        common = dict(date=datetime.date.today().isoformat(), model=args.model, revision=args.revision[:12],
                      base=args.base, text=args.text, chunks=args.chunks, ctx=args.ctx,
                      tokens_scored=args.chunks * (args.ctx - args.ctx // 2),  # llama.cpp scores the 2nd half of each chunk
                      machine=machine, runtime=runtime, notes=args.notes)
        if base_ppl:
            w.writerow(dict(common, format=args.base, size_gb=round(base.stat().st_size / 1e9, 2), time_s=round(base_secs, 1),
                            ppl=base_ppl[0], ppl_unc=base_ppl[1], ppl_ratio=1.0, kld_mean=0.0, same_top_p=100.0))
        # 2. one pass per quantized format against the saved base
        for fmt in [f.strip() for f in args.formats.split(',') if f.strip()]:
            q = gguf(fmt)
            if not q.exists():  # same rule as scripts/quantize_eval.py: output layer at Q8_0 below 8 bits
                extra = [] if fmt.upper() == 'Q8_0' else ['--output-tensor-type', 'q8_0']
                subprocess.run([bin_path('llama-quantize', args.llama_bin), *extra, str(base), str(q), fmt], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            log, secs = perplexity(args, q, args.ngl, ['--kl-divergence-base', str(kld_base), '--kl-divergence'],
                                   logs / f'{name}-{fmt}-vs-{tag}.log')
            row = dict(common, format=fmt, size_gb=round(q.stat().st_size / 1e9, 2), time_s=round(secs, 1))
            for key, pat in PATTERNS.items():
                m = re.search(pat, log)
                if not m: sys.exit(f'{fmt}: no "{key}" in the llama-perplexity output; see {logs}')
                row[key] = float(m.group(1))
                if m.lastindex > 1: row[f'{key}_unc'] = float(m.group(2))
            w.writerow({k: row.get(k, '') for k in FIELDS}); fh.flush()
            print(f'{fmt}: KLD {row["kld_mean"]:.5f}  same top-1 {row["same_top_p"]:.2f}%  '
                  f'PPL ratio {row["ppl_ratio"]:.4f}  ({secs:.0f}s)', flush=True)
            if args.cleanup:
                q.unlink()


if __name__ == '__main__':
    main()
