#!/usr/bin/env python3
"""Where does quantization error come from?  One offline command, numbers only.

    python quant_error.py all --hf-config <hf dir> --tokenizer <tokenizer.json> --ref <bf16.gguf>
        --quant Q8_0=<q8_0.gguf> [--quant Q4_K_M=<q4_k_m.gguf> ...] --heldout <heldout_v1.jsonl>
        --llama-bin <llama.cpp/build/bin> --out <dir> [--tokens-per-slice 1024] [--seq-len 512] [--kl-chunks 8]
        [--device cpu|mps|cuda] [--normalize] [--export-report export_report.json] [--work <dir>]

`all` first runs a preflight: every check that can fail (transformers 4.x, every input file present, the llama.cpp
checkout and binary, the tokenizer, every GGUF readable as the --hf-config model, every slice long enough for one
sequence, every quantized file a llama-quantize output of --ref: tensors.check_pair). A failure there exits non-zero
with a message before anything is computed or deleted, so --out keeps an earlier run's files. Then it deletes those
files and runs three steps over the same held-out slices (G5 heldout_v1, sha256-checked), writing to --out:
  tensors.csv   per tensor (per expert for expert tensors) of each quantized GGUF: error against the reference GGUF
  layers.csv    twin forward: hidden-state error and router agreement per layer and slice
  linears.csv   twin forward: activation-weighted error per nn.Linear (and per expert), and lm_head
  tokens.csv    twin forward: KL(ref || quant), same-top-1 per slice
  kl.csv        llama.cpp (llama-perplexity): KL, same-top-p, PPL and PPL ratio per slice and format
  summary.json  what is needed to reproduce the run: versions (python, torch, transformers, gguf, tokenizers, numpy,
                llama.cpp and its build and devices), the harness's git commit and dirty flag, the machine, torch's
                fp32 matmul settings, the model type, sha256 and byte size of every input, settings, wall time,
                export_gap
Each CSV is written when its step finishes and summary.json last (with `steps_completed` and `failed`), so a step
that fails late keeps the earlier results; the exit code is then non-zero. Nothing in --out is text or token ids. The slice texts and llama.cpp's scratch files go to --work (default: a temporary
folder, removed at the end), never to --out. The exit code is 1 when --out is larger than 5 MB.
See README.md.
"""
import argparse, csv, hashlib, importlib.metadata, json, os, platform, re, subprocess, sys, tempfile, time
from pathlib import Path
from types import SimpleNamespace

import torch
from tokenizers import Tokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from slices import SLICES, DOC_SEPARATOR, load_slices, write_slice_texts  # noqa: E402

MAX_OUT_BYTES = 5 * 1024 * 1024
OUTPUT_FILES = ('tensors.csv', 'layers.csv', 'linears.csv', 'tokens.csv', 'kl.csv', 'summary.json')
KL_CTX = 512
X_ROWS = 256   # sampled reference-track inputs per nn.Linear in the twin forward (act_rel_err)
TENSOR_FIELDS = ['format', 'tensor', 'layer', 'kind', 'expert', 'ggml_type', 'bits_per_weight', 'numel', 'rel_err',
                 'sqnr_db', 'max_abs_err']
LAYER_FIELDS = ['format', 'slice', 'layer', 'hidden_rel_err', 'router_agree']
LINEAR_FIELDS = ['format', 'layer', 'tensor', 'expert', 'rows', 'act_rel_err']
TOKEN_FIELDS = ['format', 'slice', 'n_tokens', 'kl_mean', 'kl_p99', 'same_top1']
KL_FIELDS = ['slice', 'format', 'chunks', 'tokens_scored', 'ppl_ratio', 'ppl_ratio_unc', 'kld_mean', 'kld_mean_unc',
             'kld_99', 'same_top_p', 'ppl', 'ppl_unc', 'kld_median', 'kld_max', 'same_top_p_unc', 'rms_dp', 'time_s']


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    """None is written as an empty field and inf as `inf`; a missing key is an empty field; an unknown key is a
    ValueError (so text can never slip into a file)."""
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, restval='', extrasaction='raise')
        w.writeheader()
        w.writerows(rows)


def cut_batches(ids: list[int], tokens_per_slice: int, seq_len: int, bos: int | None = None) -> list[torch.Tensor]:
    """The first `tokens_per_slice` ids cut into sequences of n = min(seq_len, tokens_per_slice); the last partial one
    is dropped. With `bos`, each sequence is [bos] + (n - 1) ids, as llama-perplexity starts a chunk when the GGUF asks
    for a BOS. ValueError if no whole sequence is left."""
    n = min(seq_len, tokens_per_slice)
    body = n - 1 if bos is not None else n
    if body < 1:
        raise ValueError(f'a sequence of {n} tokens has no room for text after the BOS')
    ids = ids[:tokens_per_slice]
    pre = [] if bos is None else [bos]
    out = [torch.tensor(pre + ids[i:i + body], dtype=torch.long) for i in range(0, len(ids) - body + 1, body)]
    if not out:
        raise ValueError(f'{len(ids)} tokens are fewer than one sequence of {n}')
    return out


def bos_id(gguf_path: Path) -> int | None:
    """The BOS id llama.cpp prepends to every text with this GGUF: `tokenizer.ggml.bos_token_id` when
    `tokenizer.ggml.add_bos_token` is true, else None (false or absent). ValueError if it is true and there is no id."""
    import gguf
    reader = gguf.GGUFReader(str(gguf_path))
    add = reader.get_field('tokenizer.ggml.add_bos_token')
    if add is None or not bool(add.contents()):
        return None
    bos = reader.get_field('tokenizer.ggml.bos_token_id')
    if bos is None:
        raise ValueError(f'{gguf_path}: add_bos_token is true but there is no tokenizer.ggml.bos_token_id')
    return int(bos.contents())


def slice_batches(tok: Tokenizer, slices: dict[str, list[str]], tokens_per_slice: int, seq_len: int,
                  bos: int | None) -> dict[str, list[torch.Tensor]]:
    """The twin forward's batches: per slice, its documents joined as for llama.cpp, tokenized without special tokens.
    ValueError naming the slice if it is shorter than one sequence."""
    out = {}
    for s, docs in slices.items():
        try:
            out[s] = cut_batches(tok.encode(DOC_SEPARATOR.join(docs), add_special_tokens=False).ids,
                                 tokens_per_slice, seq_len, bos)
        except ValueError as e:
            raise ValueError(f'slice {s}: {e}') from None
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


def llama_cpp_build(llama_bin: Path) -> dict:
    """`version`: the lines `llama-perplexity --version` prints (compiler and target; its build number is not the
    version, see llama_cpp_version); `devices`: the devices `llama-perplexity --list-devices` names (the backend:
    Metal, CUDA, BLAS, ...), their free memory left out."""
    exe = str(Path(llama_bin) / 'llama-perplexity')
    run = lambda flag: subprocess.run([exe, flag], capture_output=True, text=True, check=True)
    v = run('--version')
    version = '; '.join(l.strip() for l in (v.stdout + v.stderr).splitlines() if l.startswith(('version:', 'built with')))
    if not version:
        raise RuntimeError(f'{exe} --version printed no "version:" line')
    listing = run('--list-devices').stdout.splitlines()
    start = next((i for i, l in enumerate(listing) if l.startswith('Available devices')), None)
    if start is None:
        raise RuntimeError(f'{exe} --list-devices printed no "Available devices" line')
    devices = [re.sub(r'\s*\([^()]*MiB[^()]*\)\s*$', '', l.strip()) for l in listing[start + 1:] if l.startswith((' ', '\t'))]
    return {'version': version, 'devices': devices}


def harness_version() -> dict:
    """`commit`: the git commit of this folder's checkout; `dirty`: whether a tracked file in this folder, or one of the
    two team scripts it loads (quality/kl_eval.py, scripts/quantize_eval.py), differs from it (untracked files, such as
    __pycache__, are not counted). Both None outside a git checkout."""
    git = lambda *a: subprocess.run(['git', '-C', str(HERE), *a], capture_output=True, text=True, check=True).stdout.strip()
    try:
        commit = git('rev-parse', 'HEAD')
        changed = git('status', '--porcelain', '--untracked-files=no', '--', '.', '../quality/kl_eval.py',
                      '../scripts/quantize_eval.py')
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {'commit': None, 'dirty': None}
    return {'commit': commit, 'dirty': bool(changed)}


def export_gap(report: Path | None):
    if report is None:
        return None
    return json.loads(Path(report).read_text(encoding='utf-8'))['verify']['head_bias_effect']


def preflight(args) -> SimpleNamespace:
    """Every check that can fail before the long work, run before anything is computed or the previous run's outputs
    are deleted. A failure exits (SystemExit, non-zero) with a message and leaves --out as it was. Returns what the run
    uses: the GGUFWeights, the batches, the slices and the provenance read from the inputs."""
    try:
        return _preflight(args)
    except SystemExit as e:
        raise SystemExit(f'quant_error preflight: {e}; nothing was deleted or computed') from None
    except Exception as e:
        raise SystemExit(f'quant_error preflight: {type(e).__name__}: {e}; nothing was deleted or computed') from e


def _preflight(args) -> SimpleNamespace:
    import transformers
    from kl_slices import kl_eval
    from tensors import check_pair
    from weights import GGUFWeights

    if transformers.__version__.split('.')[0] != '4':
        raise SystemExit(f'transformers {transformers.__version__}: the twin forward needs transformers 4.x (5.x fuses '
                         "each layer's experts into one module, which the GGUF mapping and the per-expert rows need apart)")
    quants = dict(args.quant)
    if len(quants) != len(args.quant):
        raise SystemExit('--quant names must be distinct')
    inputs = {'--ref': args.ref, **{f'--quant {n}': q for n, q in quants.items()},
              '--hf-config': args.hf_config / 'config.json', '--tokenizer': args.tokenizer, '--heldout': args.heldout,
              '--llama-bin': args.llama_bin / 'llama-perplexity'}
    if args.export_report is not None:
        inputs['--export-report'] = args.export_report
    if missing := [f'{opt} {path}' for opt, path in inputs.items() if not Path(path).is_file()]:
        raise SystemExit(f'no such file: {", ".join(missing)}')
    out = args.out
    if args.work and (out.resolve() == args.work.resolve() or out.resolve() in args.work.resolve().parents):
        raise SystemExit('--work must not be --out or inside it: --out holds numbers only')

    run = SimpleNamespace(quants=quants, llama_cpp=llama_cpp_version(args.llama_bin),
                          llama_cpp_build=llama_cpp_build(args.llama_bin), harness=harness_version(),
                          machine=kl_eval.quantize_eval.machine_string(), export_gap=export_gap(args.export_report))
    tok = Tokenizer.from_file(str(args.tokenizer))
    run.normalizer = None
    if args.normalize:
        if tok.normalizer is None:
            raise SystemExit(f'--normalize: {args.tokenizer} has no normalizer')
        run.normalizer = tok.normalizer.normalize_str
    run.bos = bos_id(args.ref)
    run.ref_w = GGUFWeights(args.ref, args.hf_config)
    run.quant_w = {n: GGUFWeights(q, args.hf_config) for n, q in quants.items()}
    run.slices = load_slices(args.heldout, args.heldout.parent / 'SHA256SUMS')
    if unknown := sorted(set(run.slices) - set(SLICES)):
        raise SystemExit(f'held-out slices not in slices.SLICES: {unknown}')
    run.batches = slice_batches(tok, run.slices, args.tokens_per_slice, args.seq_len, run.bos)
    for q in quants.values():
        check_pair(q, args.ref)
    return run


def run_all(args) -> int:
    from forward import SEED, fp32_settings, twin_forward
    from kl_slices import NGL, run_kl_slices
    from tensors import tensor_errors

    t0 = time.time()
    timings = {}

    def step(name, fn):
        t = time.time()
        result = fn()
        timings[name] = round(time.time() - t, 1)
        print(f'[{timings[name]:8.1f} s] {name}', file=sys.stderr, flush=True)
        return result

    run = step('preflight', lambda: preflight(args))   # exits before --out is touched if anything is wrong
    quants, out = run.quants, args.out
    out.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:   # a failed run must not leave an earlier run's file looking like its own
        (out / name).unlink(missing_ok=True)

    failure = None
    try:
        with tempfile.TemporaryDirectory(prefix='quant_error_') as tmp:
            work = args.work or Path(tmp)
            work.mkdir(parents=True, exist_ok=True)
            slice_files = write_slice_texts(run.slices, work / 'slices', run.normalizer)

            tensor_rows = step('tensors', lambda: [dict(r, format=name) for name, q in quants.items()
                                                   for r in tensor_errors(q, args.ref)])
            write_csv(out / 'tensors.csv', TENSOR_FIELDS, tensor_rows)

            def twin():
                layers, linears, tokens = [], [], []
                for name, quant_w in run.quant_w.items():
                    res = twin_forward(args.hf_config, run.ref_w, quant_w, run.batches, device=args.device,
                                       x_rows=X_ROWS)
                    layers += [dict(r, format=name) for r in res.layers]
                    linears += [dict(r, format=name) for r in res.linears]
                    tokens += [dict(r, format=name) for r in res.tokens]
                    print(f'  twin forward {name} done', file=sys.stderr, flush=True)
                return layers, linears, tokens
            layers, linears, tokens = step('twin_forward', twin)
            write_csv(out / 'layers.csv', LAYER_FIELDS, layers)
            write_csv(out / 'linears.csv', LINEAR_FIELDS, linears)
            write_csv(out / 'tokens.csv', TOKEN_FIELDS, tokens)

            kl_rows = step('kl', lambda: run_kl_slices(args.ref, quants, slice_files, args.tokenizer, args.llama_bin, work,
                                                       ctx=KL_CTX, max_chunks=args.kl_chunks,
                                                       add_bos=run.bos is not None))
            write_csv(out / 'kl.csv', KL_FIELDS, kl_rows)
    except Exception as e:   # the CSVs of the finished steps stay; summary.json says what completed
        failure = e

    version = importlib.metadata.version
    summary = {
        'python': platform.python_version(), 'torch': torch.__version__, 'transformers': version('transformers'),
        'gguf': version('gguf'), 'tokenizers': version('tokenizers'), 'numpy': version('numpy'),
        'llama_cpp': run.llama_cpp, 'llama_cpp_build': run.llama_cpp_build,
        'harness': run.harness, 'machine': run.machine, 'torch_fp32': fp32_settings(),
        'model_type': run.ref_w.config.model_type,
        'sha256': {'ref': sha256_file(args.ref), 'quants': {n: sha256_file(q) for n, q in quants.items()},
                   'heldout': sha256_file(args.heldout), 'tokenizer': sha256_file(args.tokenizer),
                   'config': sha256_file(args.hf_config / 'config.json')},
        'bytes': {'ref': args.ref.stat().st_size, 'quants': {n: q.stat().st_size for n, q in quants.items()}},
        'settings': {'formats': list(quants), 'tokens_per_slice': args.tokens_per_slice, 'seq_len': args.seq_len,
                     'kl_chunks': args.kl_chunks, 'kl_ctx': KL_CTX, 'device': args.device, 'normalize': args.normalize,
                     'bos': run.bos is not None, 'bos_id': run.bos, 'x_rows': X_ROWS, 'seed': SEED, 'ngl': NGL,
                     'slices': list(run.slices), 'ref_file': args.ref.name,
                     'quant_files': {n: q.name for n, q in quants.items()}},
        'timings_s': timings, 'wall_time_s': round(time.time() - t0, 1),
        'export_gap': run.export_gap,
        'steps_completed': list(timings),
        'failed': None if failure is None else f'{type(failure).__name__}: {failure}',
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    if failure is not None:
        raise failure
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
