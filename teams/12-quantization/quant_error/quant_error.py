#!/usr/bin/env python3
"""Where does quantization error come from?  One offline command, numbers only.

    python quant_error.py all --hf-config <hf dir> --tokenizer <tokenizer.json> --ref <bf16.gguf>
        --quant Q8_0=<q8_0.gguf> [--quant Q4_K_M=<q4_k_m.gguf> ...] --heldout <heldout_v1.jsonl>
        --llama-bin <llama.cpp/build/bin> --out <dir> [--tokens-per-slice 1024] [--seq-len 512] [--kl-chunks 8]
        [--device cpu|mps|cuda] [--normalize] [--export-report export_report.json] [--work <dir>]

`all` runs four steps over the same held-out slices (G5 heldout_v1, sha256-checked) and writes, to --out:
  tensors.csv   per tensor (per expert for expert tensors) of each quantized GGUF: error against the reference GGUF
  layers.csv    twin forward: hidden-state error and router agreement per layer and slice
  linears.csv   twin forward: activation-weighted error per nn.Linear (and per expert), and lm_head
  tokens.csv    twin forward: KL(ref || quant), same-top-1 per slice
  kl.csv        llama.cpp (llama-perplexity): KL, same-top-p and PPL ratio per slice and format
  summary.json  versions, llama.cpp build, sha256 of every GGUF and of the held-out file, settings, wall time, export_gap
Nothing in --out is text or token ids. The slice texts and llama.cpp's scratch files go to --work (default: a temporary
folder, removed at the end), never to --out. The exit code is 1 when --out is larger than 5 MB.
See README.md.
"""
import argparse, csv, hashlib, importlib.metadata, json, os, platform, subprocess, sys, tempfile, time
from pathlib import Path

import torch
from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from slices import SLICES, DOC_SEPARATOR, load_slices, write_slice_texts  # noqa: E402

MAX_OUT_BYTES = 5 * 1024 * 1024
KL_CTX = 512
TENSOR_FIELDS = ['format', 'tensor', 'layer', 'kind', 'expert', 'ggml_type', 'bits_per_weight', 'numel', 'rel_err',
                 'sqnr_db', 'max_abs_err']
LAYER_FIELDS = ['format', 'slice', 'layer', 'hidden_rel_err', 'router_agree']
LINEAR_FIELDS = ['format', 'layer', 'tensor', 'expert', 'rows', 'act_rel_err']
TOKEN_FIELDS = ['format', 'slice', 'n_tokens', 'kl_mean', 'kl_p99', 'same_top1']
KL_FIELDS = ['slice', 'format', 'chunks', 'tokens_scored', 'ppl_ratio', 'ppl_ratio_unc', 'kld_mean', 'kld_mean_unc',
             'kld_99', 'same_top_p', 'time_s']


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    """None is written as an empty field and inf as `inf`; a missing key is an empty field; an unknown key is a
    ValueError (so text can never slip into a file)."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, restval='', extrasaction='raise')
        w.writeheader()
        w.writerows(rows)


def cut_batches(ids: list[int], tokens_per_slice: int, seq_len: int) -> list[torch.Tensor]:
    """The first `tokens_per_slice` ids cut into sequences of min(seq_len, tokens_per_slice); the last partial one is
    dropped. ValueError if no whole sequence is left."""
    n = min(seq_len, tokens_per_slice)
    ids = ids[:tokens_per_slice]
    out = [torch.tensor(ids[i:i + n], dtype=torch.long) for i in range(0, len(ids) - n + 1, n)]
    if not out:
        raise ValueError(f'{len(ids)} tokens are fewer than one sequence of {n}')
    return out


def folder_bytes(folder: Path) -> int:
    return sum(p.stat().st_size for p in Path(folder).rglob('*') if p.is_file())


def within_limit(folder: Path, limit: int = MAX_OUT_BYTES) -> bool:
    return folder_bytes(folder) <= limit


def parse_quant(text: str) -> tuple[str, Path]:
    name, sep, path = text.partition('=')
    if not sep or not name or not path:
        raise argparse.ArgumentTypeError(f'--quant wants NAME=<file.gguf>, got {text!r}')
    return name, Path(path)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 22), b''):
            h.update(block)
    return h.hexdigest()


def llama_cpp_version(llama_bin: Path) -> str:
    """`b12359 (b1b770d)`: git describe --tags --match 'b[0-9]*' (the checkout also carries a v1.0.0 tag) and the short commit of the llama.cpp checkout (the parent of
    <root>/build/bin, else $LLAMA_CPP_DIR). Never the binary's own build number: a shallow clone reports "build 1"."""
    roots = [Path(llama_bin).resolve().parents[1]] if len(Path(llama_bin).resolve().parents) > 1 else []
    if os.environ.get('LLAMA_CPP_DIR'):
        roots.append(Path(os.environ['LLAMA_CPP_DIR']))
    for root in roots:
        try:
            git = lambda *a: subprocess.run(['git', '-C', str(root), *a], capture_output=True, text=True, check=True).stdout.strip()
            return f"{git('describe', '--tags', '--match', 'b[0-9]*')} ({git('rev-parse', '--short', 'HEAD')})"
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    raise SystemExit(f'cannot read the llama.cpp version: {llama_bin} is not in <llama.cpp>/build/bin of a git checkout '
                     'and LLAMA_CPP_DIR does not name one')


def export_gap(report: Path | None):
    if report is None:
        return None
    return json.loads(Path(report).read_text(encoding='utf-8'))['verify']['head_bias_effect']


def run_all(args) -> int:
    from forward import twin_forward
    from kl_slices import run_kl_slices
    from tensors import tensor_errors
    from weights import GGUFWeights

    t0 = time.time()
    timings = {}
    quants = dict(args.quant)
    if len(quants) != len(args.quant):
        raise SystemExit('--quant names must be distinct')
    llama_version = llama_cpp_version(args.llama_bin)   # before the long work: a wrong --llama-bin fails at once
    gap = export_gap(args.export_report)
    out = args.out
    if args.work and (out.resolve() == args.work.resolve() or out.resolve() in args.work.resolve().parents):
        raise SystemExit('--work must not be --out or inside it: --out holds numbers only')
    out.mkdir(parents=True, exist_ok=True)

    def step(name, fn):
        t = time.time()
        result = fn()
        timings[name] = round(time.time() - t, 1)
        print(f'[{timings[name]:8.1f} s] {name}', file=sys.stderr, flush=True)
        return result

    tok = Tokenizer.from_file(str(args.tokenizer))
    normalizer = None
    if args.normalize:
        if tok.normalizer is None:
            raise SystemExit(f'--normalize: {args.tokenizer} has no normalizer')
        normalizer = tok.normalizer.normalize_str

    sums = args.heldout.parent / 'SHA256SUMS'
    slices = step('slices', lambda: load_slices(args.heldout, sums))
    unknown = sorted(set(slices) - set(SLICES))
    if unknown:
        raise SystemExit(f'held-out slices not in slices.SLICES: {unknown}')

    with tempfile.TemporaryDirectory(prefix='quant_error_') as tmp:
        work = args.work or Path(tmp)
        work.mkdir(parents=True, exist_ok=True)
        slice_files = write_slice_texts(slices, work / 'slices', normalizer)

        tensor_rows = step('tensors', lambda: [dict(r, format=name) for name, q in quants.items()
                                               for r in tensor_errors(q, args.ref)])

        def twin():
            batches = {s: cut_batches(tok.encode(DOC_SEPARATOR.join(docs), add_special_tokens=False).ids,
                                      args.tokens_per_slice, args.seq_len) for s, docs in slices.items()}
            layers, linears, tokens = [], [], []
            ref = GGUFWeights(args.ref, args.hf_config)
            for name, q in quants.items():
                res = twin_forward(args.hf_config, ref, GGUFWeights(q, args.hf_config), batches, device=args.device)
                layers += [dict(r, format=name) for r in res.layers]
                linears += [dict(r, format=name) for r in res.linears]
                tokens += [dict(r, format=name) for r in res.tokens]
                print(f'  twin forward {name} done', file=sys.stderr, flush=True)
            return layers, linears, tokens
        layers, linears, tokens = step('twin_forward', twin)

        kl_rows = step('kl', lambda: run_kl_slices(args.ref, quants, slice_files, args.tokenizer, args.llama_bin, work,
                                                   ctx=KL_CTX, max_chunks=args.kl_chunks))

    write_csv(out / 'tensors.csv', TENSOR_FIELDS, tensor_rows)
    write_csv(out / 'layers.csv', LAYER_FIELDS, layers)
    write_csv(out / 'linears.csv', LINEAR_FIELDS, linears)
    write_csv(out / 'tokens.csv', TOKEN_FIELDS, tokens)
    write_csv(out / 'kl.csv', KL_FIELDS, kl_rows)
    summary = {
        'python': platform.python_version(), 'torch': torch.__version__,
        'transformers': importlib.metadata.version('transformers'), 'gguf': importlib.metadata.version('gguf'),
        'llama_cpp': llama_version,
        'sha256': {'ref': sha256_file(args.ref), 'quants': {n: sha256_file(q) for n, q in quants.items()},
                   'heldout': sha256_file(args.heldout)},
        'settings': {'formats': list(quants), 'tokens_per_slice': args.tokens_per_slice, 'seq_len': args.seq_len,
                     'kl_chunks': args.kl_chunks, 'kl_ctx': KL_CTX, 'device': args.device, 'normalize': args.normalize,
                     'slices': list(slices), 'ref_file': args.ref.name, 'quant_files': {n: q.name for n, q in quants.items()},
                     'tokenizer_sha256': sha256_file(args.tokenizer)},
        'timings_s': timings, 'wall_time_s': round(time.time() - t0, 1),
        'export_gap': gap,
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    size = folder_bytes(out)
    print(f'wrote {out} ({size / 1024:.0f} KB, {summary["wall_time_s"]} s)', file=sys.stderr)
    if size > MAX_OUT_BYTES:
        print(f'ERROR: {out} is {size} bytes, over the {MAX_OUT_BYTES} byte limit', file=sys.stderr)
        return 1
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('all', help='slices, tensors, twin forward and llama.cpp KL in one run')
    p.add_argument('--hf-config', type=Path, required=True, help='Hugging Face folder with config.json (weights not read)')
    p.add_argument('--tokenizer', type=Path, required=True, help='tokenizer.json of the model')
    p.add_argument('--ref', type=Path, required=True, help='the reference GGUF (bf16 of the same export and llama.cpp build)')
    p.add_argument('--quant', type=parse_quant, action='append', required=True, metavar='NAME=FILE',
                   help='a quantized GGUF, e.g. Q4_K_M=model-q4_k_m.gguf (repeat for more formats)')
    p.add_argument('--heldout', type=Path, required=True, help='heldout_v1.jsonl (SHA256SUMS must sit beside it)')
    p.add_argument('--llama-bin', type=Path, required=True, help='<llama.cpp>/build/bin (llama-perplexity)')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--tokens-per-slice', type=int, default=1024, help='tokens of each slice in the twin forward')
    p.add_argument('--seq-len', type=int, default=512, help='sequence length of the twin forward (at most --tokens-per-slice)')
    p.add_argument('--kl-chunks', type=int, default=8, help='llama-perplexity chunks (of 512 tokens) per slice')
    p.add_argument('--device', choices=('cpu', 'mps', 'cuda'), default='cpu', help='device of the twin forward')
    p.add_argument('--normalize', action='store_true',
                   help="pass the slice text through the tokenizer's normalizer before llama.cpp (which cannot apply it)")
    p.add_argument('--export-report', type=Path, help='export_report.json: copies verify.head_bias_effect to summary.json')
    p.add_argument('--work', type=Path, help='scratch folder (slice texts, llama.cpp logs); default: temporary, removed')
    args = ap.parse_args(argv)
    return run_all(args)


if __name__ == '__main__':
    sys.exit(main())
