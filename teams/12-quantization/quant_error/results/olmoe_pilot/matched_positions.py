#!/usr/bin/env python3
"""Pilot script, not core code: do the twin forward (tokens.csv) and llama.cpp (kl.csv) agree when they look at
the same positions?

For each held-out slice it builds llama-perplexity's own sequences (BOS first when the reference GGUF has
tokenizer.ggml.add_bos_token true, up to --chunks chunks of --ctx tokens, only positions ctx/2 .. ctx-2 scored), runs
the twin forward on exactly those sequences, and computes mean KL(ref||quant) and same-top-1 over exactly those
positions. They go next to llama.cpp's own numbers for the same slice (kl.csv of the tool run, same chunks).

It also runs llama-perplexity's base pass (reference GGUF) per slice and decodes the saved log-probabilities
(uint16 values with a per-token scale and minimum, see tools/perplexity/perplexity.cpp: `log_softmax`) to check
  1. that the tokens llama.cpp scored are the tokens built here, and
  2. how the twin's reference logits (fp32 forward over the bf16 weights) compare with llama.cpp's base logits.

Numbers only: no text, no token ids in the outputs.

    python matched_positions.py --hf-config <hf dir> --tokenizer <tokenizer.json> --ref <bf16.gguf>
        --quant Q8_0=<q8_0.gguf> --quant Q4_K_M=<q4_k_m.gguf> --heldout <heldout_v1.jsonl> --llama-bin <build/bin>
        --kl-csv <tool run>/kl.csv --tokens-csv <tool run>/tokens.csv --out <dir> --work <scratch> --device mps
"""
import argparse, csv, math, sys, time
from argparse import Namespace
from pathlib import Path

import numpy as np
import torch
from tokenizers import Tokenizer

QE = Path(__file__).resolve().parents[2]          # teams/12-quantization/quant_error
sys.path.insert(0, str(QE))
from quant_error import bos_id, parse_quant       # noqa: E402
from slices import load_slices, write_slice_texts  # noqa: E402
import kl_slices                                   # noqa: E402
from forward import twin_forward                   # noqa: E402
from weights import GGUFWeights                    # noqa: E402


def own_chunks(ids: list[int], bos: int | None, ctx: int, max_chunks: int) -> list[list[int]]:
    """The chunks llama-perplexity scores: the token stream ([BOS] + text tokens when the GGUF adds a BOS) cut into
    whole chunks of ctx tokens, at most max_chunks; the first token of every chunk is BOS (it overwrites the stream's
    own token there, as in perplexity.cpp)."""
    stream = ([] if bos is None else [bos]) + ids
    n = len(stream) // ctx
    out = []
    for c in range(min(n, max_chunks)):
        chunk = stream[c * ctx:(c + 1) * ctx]
        if bos is not None:
            chunk[0] = bos
        out.append(chunk)
    return out


def read_kld(path: Path):
    """The base file of llama-perplexity: '_logits_', u32 n_ctx, i32 n_vocab, i32 n_chunk, i32 tokens[n_chunk*n_ctx],
    then per chunk n_ctx-1-n_ctx/2 rows of nv = 2*((n_vocab+1)//2)+4 uint16 (a float scale and a float min_log_prob,
    then n_vocab values: log_prob = scale * v + min_log_prob)."""
    with open(path, 'rb') as f:
        if f.read(8) != b'_logits_':
            raise ValueError(f'{path} is not a llama-perplexity base file')
        n_ctx, n_vocab, n_chunk = (int(np.frombuffer(f.read(4), dtype=dt)[0]) for dt in (np.uint32, np.int32, np.int32))
        tokens = np.frombuffer(f.read(n_chunk * n_ctx * 4), dtype=np.int32).reshape(n_chunk, n_ctx)
        offset = f.tell()
    nv = 2 * ((n_vocab + 1) // 2) + 4
    rows = n_ctx - 1 - n_ctx // 2
    lp = np.memmap(path, dtype=np.uint16, mode='r', offset=offset, shape=(n_chunk, rows, nv))
    return n_ctx, n_vocab, tokens, lp


def decode_logprobs(block: np.ndarray, n_vocab: int) -> np.ndarray:
    """[rows, nv] uint16 -> [rows, n_vocab] float32 log-probabilities."""
    block = np.asarray(block)
    d = np.ascontiguousarray(block[:, :4]).view(np.float32)            # [rows, 2]: scale, min_log_prob
    return block[:, 4:4 + n_vocab].astype(np.float32) * d[:, :1] + d[:, 1:2]


def _unc(p: float, n: int) -> float:
    return 100 * math.sqrt(p * (1 - p) / (n - 1)) if n > 1 else float('nan')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--hf-config', type=Path, required=True)
    ap.add_argument('--tokenizer', type=Path, required=True)
    ap.add_argument('--ref', type=Path, required=True)
    ap.add_argument('--quant', type=parse_quant, action='append', required=True, metavar='NAME=FILE')
    ap.add_argument('--heldout', type=Path, required=True)
    ap.add_argument('--llama-bin', type=Path, required=True)
    ap.add_argument('--kl-csv', type=Path, required=True, help='kl.csv of the tool run (llama.cpp values to compare with)')
    ap.add_argument('--tokens-csv', type=Path, required=True, help='tokens.csv of the tool run (twin values at its own positions)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--device', default='mps')
    ap.add_argument('--chunks', type=int, default=8)
    ap.add_argument('--ctx', type=int, default=512)
    args = ap.parse_args(argv)
    t0 = time.time()
    args.out.mkdir(parents=True, exist_ok=True)
    args.work.mkdir(parents=True, exist_ok=True)
    ctx, first = args.ctx, args.ctx // 2          # scored positions first .. ctx-2 (predicting tokens first+1 .. ctx-1)
    rows_per_chunk = ctx - 1 - first

    bos = bos_id(args.ref)
    tok = Tokenizer.from_file(str(args.tokenizer))
    slices = load_slices(args.heldout, args.heldout.parent / 'SHA256SUMS')
    files = write_slice_texts(slices, args.work / 'slices')

    # 1. llama.cpp's sequences, and its base file per slice (decoded below, deleted after the twin forward)
    seqs, base_files, tokens_match = {}, {}, {}
    for name, path in files.items():
        ids = tok.encode(Path(path).read_text(encoding='utf-8'), add_special_tokens=False).ids
        own = own_chunks(ids, bos, ctx, args.chunks)
        if not own or len(ids) + (bos is not None) < 2 * ctx:
            print(f'{name}: under {2 * ctx} tokens, llama-perplexity refuses it; skipped', file=sys.stderr)
            continue
        a = Namespace(llama_bin=str(args.llama_bin), ctx=ctx, chunks=len(own))
        base = args.work / f'{name}.kld'
        log, _ = kl_slices.kl_eval.perplexity(a, args.ref, kl_slices.NGL, ['-f', str(path), '--kl-divergence-base', str(base)],
                                              args.work / f'{name}-base.log')
        actual = kl_slices._chunks_run(log, name)
        _, n_vocab, kld_tokens, _ = read_kld(base)
        mine = np.array(own, dtype=np.int32)
        kld_tokens = kld_tokens.copy()
        if bos is not None:
            kld_tokens[:, 0] = bos   # the file keeps the stream's token; llama-perplexity overwrites it with BOS when scoring
        tokens_match[name] = dict(own_chunks=len(own), llama_chunks=actual,
                                  same=bool(actual == len(own) and np.array_equal(mine, kld_tokens)))
        use = kld_tokens if not tokens_match[name]['same'] else mine
        seqs[name] = [torch.tensor(r, dtype=torch.long) for r in use.astype(np.int64)]
        base_files[name] = base
        print(f'{name}: {len(own)} chunks (llama.cpp ran {actual}); tokens identical: {tokens_match[name]["same"]}',
              file=sys.stderr, flush=True)

    # 2. the twin forward on exactly those sequences; statistics over exactly the scored positions
    stats = {}   # (format, slice) -> [positions, sum kl, same top-1]
    basecmp = {}  # slice -> [positions, same top-1 (twin ref vs llama base), sum KL(base||twin ref), sum nll twin, sum nll llama, abs diff of nll]
    first_format = next(iter(dict(args.quant)))
    kld_cache = {n: read_kld(p) for n, p in base_files.items()}

    def make_hook(fmt):
        def hook(name, j, ref_logits, q_logits):
            lr = torch.log_softmax(ref_logits[0, first:ctx - 1].float(), -1)
            lq = torch.log_softmax(q_logits[0, first:ctx - 1].float(), -1)
            kl = (lr.exp() * (lr - lq)).sum(-1)
            same = lr.argmax(-1) == lq.argmax(-1)
            s = stats.setdefault((fmt, name), [0, 0.0, 0])
            s[0] += len(kl); s[1] += kl.sum().item(); s[2] += int(same.sum())
            if fmt == first_format:   # the reference track is the same for every format: compare it once
                _, nv_, toks, lp = kld_cache[name]
                lb = torch.from_numpy(decode_logprobs(lp[j], nv_)).to(lr.device)
                target = torch.from_numpy(toks[j, first + 1:ctx].astype(np.int64)).to(lr.device)
                b = basecmp.setdefault(name, [0, 0, 0.0, 0.0, 0.0, 0.0])
                b[0] += len(kl); b[1] += int((lr.argmax(-1) == lb.argmax(-1)).sum())
                b[2] += (lb.exp() * (lb - lr)).sum(-1).sum().item()
                nt, nl = -lr.gather(1, target[:, None])[:, 0], -lb.gather(1, target[:, None])[:, 0]
                b[3] += nt.sum().item(); b[4] += nl.sum().item(); b[5] += (nt - nl).abs().sum().item()
        return hook

    ref_w = GGUFWeights(args.ref, args.hf_config)
    for fmt, q in args.quant:
        t = time.time()
        twin_forward(args.hf_config, ref_w, GGUFWeights(q, args.hf_config), seqs, device=args.device, x_rows=1,
                     on_logits=make_hook(fmt))
        print(f'twin forward {fmt}: {time.time() - t:.0f} s', file=sys.stderr, flush=True)
    for p in base_files.values():
        p.unlink(missing_ok=True)

    # 3. next to llama.cpp's values for the same slices and formats (and the tool run's own twin values)
    kl = {(r['slice'], r['format']): r for r in csv.DictReader(open(args.kl_csv))}
    tk = {(r['slice'], r['format']): r for r in csv.DictReader(open(args.tokens_csv))}
    out_rows = []
    for fmt, _ in args.quant:
        tot = [0, 0.0, 0, 0.0, 0.0, 0.0]   # positions, twin kl sum, twin top1, llama kld*n, llama top1*n, tokens.csv kl*n
        for name in seqs:
            n, ksum, same = stats[(fmt, name)]
            l = kl[(name, fmt)]
            assert int(l['chunks']) * rows_per_chunk == n, (name, fmt, l['chunks'], n)
            lk, lt = float(l['kld_mean']), float(l['same_top_p'])
            out_rows.append(dict(format=fmt, slice=name, chunks=int(l['chunks']), positions=n,
                                 twin_kl_mean=ksum / n, llama_kld_mean=lk, llama_kld_mean_unc=float(l['kld_mean_unc']),
                                 twin_same_top1_pct=100 * same / n, llama_same_top_p_pct=lt,
                                 llama_same_top_p_unc_pct=_unc(lt / 100, n),
                                 tokens_csv_kl_mean=float(tk[(name, fmt)]['kl_mean']),
                                 tokens_csv_same_top1_pct=100 * float(tk[(name, fmt)]['same_top1'])))
            tot[0] += n; tot[1] += ksum; tot[2] += same; tot[3] += lk * n; tot[4] += lt * n
            tot[5] += float(tk[(name, fmt)]['kl_mean']) * int(tk[(name, fmt)]['n_tokens'])
        n = tot[0]
        out_rows.append(dict(format=fmt, slice='ALL (position-weighted)', chunks=sum(int(kl[(s, fmt)]['chunks']) for s in seqs),
                             positions=n, twin_kl_mean=tot[1] / n, llama_kld_mean=tot[3] / n,
                             twin_same_top1_pct=100 * tot[2] / n, llama_same_top_p_pct=tot[4] / n,
                             llama_same_top_p_unc_pct=_unc(tot[4] / n / 100, n)))
    fields = ['format', 'slice', 'chunks', 'positions', 'twin_kl_mean', 'llama_kld_mean', 'llama_kld_mean_unc',
              'twin_same_top1_pct', 'llama_same_top_p_pct', 'llama_same_top_p_unc_pct', 'tokens_csv_kl_mean',
              'tokens_csv_same_top1_pct']
    with open(args.out / 'matched_positions.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fields, restval='', extrasaction='raise')
        w.writeheader(); w.writerows(out_rows)

    base_rows, tb = [], [0, 0, 0.0, 0.0, 0.0, 0.0]
    for name, b in basecmp.items():
        n = b[0]
        base_rows.append(dict(slice=name, chunks=tokens_match[name]['llama_chunks'], tokens_identical=tokens_match[name]['same'],
                              positions=n, ref_top1_agree_pct=100 * b[1] / n, kl_llama_base_to_twin_ref=b[2] / n,
                              nll_twin_ref=b[3] / n, nll_llama_base=b[4] / n, mean_abs_nll_diff=b[5] / n))
        tb = [x + y for x, y in zip(tb, b)]
    n = tb[0]
    base_rows.append(dict(slice='ALL (position-weighted)', chunks=sum(r['chunks'] for r in base_rows), tokens_identical=all(
        r['tokens_identical'] for r in base_rows), positions=n, ref_top1_agree_pct=100 * tb[1] / n,
        kl_llama_base_to_twin_ref=tb[2] / n, nll_twin_ref=tb[3] / n, nll_llama_base=tb[4] / n, mean_abs_nll_diff=tb[5] / n))
    with open(args.out / 'matched_base_check.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, list(base_rows[0]), restval='', extrasaction='raise')
        w.writeheader(); w.writerows(base_rows)

    print(f'\nbos={bos is not None}  ctx={ctx}  scored positions per chunk={rows_per_chunk}  wall {time.time() - t0:.0f} s')
    for r in out_rows:
        if r['slice'].startswith('ALL'):
            print(f"{r['format']:8s} ALL  positions {r['positions']}  twin KL {r['twin_kl_mean']:.5f} vs llama {r['llama_kld_mean']:.5f}"
                  f"  top1 {r['twin_same_top1_pct']:.2f}% vs {r['llama_same_top_p_pct']:.2f}% (+/- {r['llama_same_top_p_unc_pct']:.2f})")
    r = base_rows[-1]
    print(f"base check ALL: tokens identical {r['tokens_identical']}, twin-ref vs llama-base top-1 {r['ref_top1_agree_pct']:.2f}%,"
          f" KL {r['kl_llama_base_to_twin_ref']:.5f}, nll {r['nll_twin_ref']:.4f} vs {r['nll_llama_base']:.4f}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
