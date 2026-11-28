#!/usr/bin/env python3
"""Where a released Deletion Tuning mask deletes, per expert, whether the heavily deleted experts were ones the Wanda
calibration never reached, and which experts of a Team 5 run got no routed tokens (independent study; see
../results/dt_mask_anatomy.md).

    python dt/mask_anatomy.py masks <mask_dir> [--partners 1]                # per-matrix deleted counts, heavy experts
    python dt/mask_anatomy.py weights <mask_dir> <hf_repo> L:E [L:E ...]     # abs W of deleted vs kept (HTTP range reads)
    python dt/mask_anatomy.py calib <train.parquet> <tokenizer_dir> <out_dir> # the official calibration prompts, as text
    python dt/mask_anatomy.py routing <mask_dir> <imatrix.gguf> [...]        # calibration tokens per expert vs heavy experts
    python dt/mask_anatomy.py load <metrics.jsonl> [--last 5] [--gate 768x512] # idle experts in a Team 5 run record
    python dt/mask_anatomy.py revive [--grad-scale 1 0.1]                    # toy: an unscored gate under dt/mask.py

<mask_dir>: one folder of Jacklu0831/deletion-tuning-masks (config.json + model.safetensors, format packbits_zstd).
Decoding follows the official src/apply_mask.py: zstd -> np.unpackbits -> first numel bits -> reshape; 1 keeps.
calib: rebuilds the prompts the official verl_adapters._wanda_scores calibrates on (SimpleRL-Zoo simplelr_qwen_level3to5
train.parquet made into system + user messages as src/prepare_simplerl_zoo_train.py does, df.sample(n=2048,
random_state=42), chat template with the generation prompt, tokenizer(padding=True, truncation=True, max_length=512)),
and writes them as text files of --per-part prompts each, every prompt exactly max_length tokens, for
`llama-imatrix -f partNN.txt -c 512 --parse-special --no-ppl` (one chunk = one prompt). Needs pandas and transformers.
<imatrix.gguf>: llama-imatrix output on the calibration prompts; its blk.L.ffn_gate_exps.weight.counts are the routed
tokens per expert (llama.cpp tools/imatrix/imatrix.cpp adds 1 per token and routed slot). Several files are summed.
<metrics.jsonl>: a Team 5 run record (train_week2.py); rows with expert_load hold [layer][expert] routed token slots
counted over that whole training step (model.py start_expert_load / finish_expert_load).
Layer and expert numbers count from 0, as in the module names. Needs numpy; masks/weights/routing also need zstandard
and safetensors; routing needs gguf (llama.cpp's gguf-py); revive needs torch (it runs this folder's mask.py).
"""
from __future__ import annotations

import argparse
import http.client
import json
import math
import re
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

KEY = re.compile(r'model\.layers\.(\d+)\.mlp\.(?:experts\.(\d+)\.)?gate_proj\.weight$')
HEAVY = 0.01   # deleted share above which an expert matrix counts as heavy (the released MoE mask has a gap 0.17% .. 39%)


def deleted_masks(mask_dir: Path):
    """Yield (layer, expert or -1, bool[out, in] deleted) for every gate matrix, checking config.json's totals."""
    import zstandard
    from safetensors import safe_open
    cfg = json.loads((mask_dir / 'config.json').read_text())
    if cfg['format'] != 'packbits_zstd':
        sys.exit(f'{mask_dir}: format {cfg["format"]!r}, expected packbits_zstd')
    d, total, zero = zstandard.ZstdDecompressor(), 0, 0
    with safe_open(str(mask_dir / 'model.safetensors'), 'numpy') as f:
        names = {k[:-len('.shape')] for k in f.keys() if k.endswith('.shape')}
        bad = sorted(n for n in names if not KEY.match(n))
        if bad:
            sys.exit(f'{mask_dir}: not a gate_proj mask name: {bad[0]} (and {len(bad) - 1} more)')
        names = sorted(names, key=lambda n: tuple(int(x) if x else -1 for x in KEY.match(n).groups()))
        for n in names:
            shape = tuple(int(x) for x in f.get_tensor(n + '.shape').tolist())
            bits = np.unpackbits(np.frombuffer(d.decompress(f.get_tensor(n + '.packed').tobytes()), np.uint8))
            dele = ~bits[:int(np.prod(shape))].astype(bool).reshape(shape)
            total, zero = total + dele.size, zero + int(dele.sum())
            L, E = KEY.match(n).groups()
            yield int(L), int(E) if E is not None else -1, dele
    if (total, zero) != (cfg['total_params'], cfg['zero_params']):
        sys.exit(f'decode mismatch: {total:,} / {zero:,} against config.json {cfg["total_params"]:,} / {cfg["zero_params"]:,}')


def per_matrix(mask_dir: Path):
    """(layer, expert, deleted count) arrays over all gate matrices, plus the weights per matrix."""
    rows = [(L, E, int(m.sum()), m.size) for L, E, m in deleted_masks(mask_dir)]
    if len({r[3] for r in rows}) != 1:
        sys.exit('gate matrices differ in size; per-matrix shares would not be comparable')
    return (np.array([r[0] for r in rows]), np.array([r[1] for r in rows]), np.array([r[2] for r in rows]), rows[0][3])


def cmd_masks(a):
    layer, expert, dele, cells = per_matrix(Path(a.mask_dir))
    frac = dele / cells
    print(f'{len(frac)} gate matrices of {cells:,} weights; deleted {dele.sum():,} = {dele.sum() / (len(frac) * cells):.4%}')
    if (expert >= 0).any():
        heavy = frac > HEAVY
        if not heavy.any():
            print(f'heavy experts (> {HEAVY:.0%} deleted): 0; max {frac.max():.4%}')
            return
        print(f'heavy experts (> {HEAVY:.0%} deleted): {heavy.sum()}, {frac[heavy].min():.3%} to {frac[heavy].max():.3%}, '
              f'holding {dele[heavy].sum() / dele.sum():.1%} of all deletions')
        print(f'other experts: mean {frac[~heavy].mean():.4%}, median {np.median(frac[~heavy]):.4%}, '
              f'max {frac[~heavy].max():.4%}')
        print('heavy (layer:expert):', ' '.join(f'{l}:{e}' for l, e in zip(layer[heavy], expert[heavy])))
        share = np.array([dele[layer == l].sum() / ((layer == l).sum() * cells) for l in range(layer.max() + 1)])
        with_heavy = np.array([heavy[layer == l].any() for l in range(layer.max() + 1)])
        print(f'per-layer deleted share: median {np.median(share[~with_heavy]):.3%} ({share[~with_heavy].min():.3%} to '
              f'{share[~with_heavy].max():.3%}) in the {(~with_heavy).sum()} layers without a heavy expert; '
              f'{share[with_heavy].min():.2%} to {share[with_heavy].max():.2%} in the {with_heavy.sum()} with one')
        if a.partners is not None:
            # one partner per heavy expert, from the same layer: one default_rng(seed) stream, heavy experts in
            # layer:expert order, rng.choice over that layer's experts that are not heavy and not yet picked
            rng, picked, out = np.random.default_rng(a.partners), set(), []
            for l, e in zip(layer[heavy], expert[heavy]):
                cand = [int(x) for x in expert[(layer == l) & ~heavy] if (int(l), int(x)) not in picked]
                x = int(rng.choice(cand))
                picked.add((int(l), x))
                out += [f'{l}:{e}', f'{l}:{x}']
            print(f'heavy experts and partners (seed {a.partners}):', ' '.join(out))


def range_get(url, start, end, tries=5):
    """Bytes start..end of url (HTTP range read), retried on a dropped connection."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}'}),
                                        timeout=120) as r:
                data = r.read()
            if len(data) == end - start + 1:
                return data
        except (OSError, http.client.HTTPException):
            if i == tries - 1:
                raise
    sys.exit(f'{url}: got a short read {tries} times')


def cmd_weights(a):
    """abs W statistics of deleted vs kept weights for some experts, reading only those tensors from the Hub."""
    base = f'https://huggingface.co/{a.hf_repo}/resolve/{a.revision}/'
    index = json.loads(urllib.request.urlopen(base + 'model.safetensors.index.json', timeout=120).read())['weight_map']
    want = {tuple(int(x) for x in s.split(':')) for s in a.experts}
    masks = {(L, E): m for L, E, m in deleted_masks(Path(a.mask_dir)) if (L, E) in want}
    if set(masks) != want:
        sys.exit(f'not in the mask: {sorted(want - set(masks))}')
    headers = {}
    pool = {g: np.zeros(10) for g in ('heavy', 'other')}   # summed over the experts of each group, for the pooled rows
    print(' L    E  deleted  absW del/kept  mean rank of deleted  del in bottom 10% absW  del in top 10% absW  del with W<0')
    for (L, E), dele in sorted(masks.items()):
        name = f'model.layers.{L}.mlp.experts.{E}.gate_proj.weight'
        shard = index[name]
        if shard not in headers:
            n = struct.unpack('<Q', range_get(base + shard, 0, 7))[0]
            headers[shard] = (8 + n, json.loads(range_get(base + shard, 8, 8 + n - 1)))
        off, h = headers[shard]
        t = h[name]
        s, e = t['data_offsets']
        if t['dtype'] != 'BF16' or tuple(t['shape']) != dele.shape:
            sys.exit(f'{name}: {t["dtype"]} {t["shape"]}, expected BF16 {dele.shape}')
        w = (np.frombuffer(range_get(base + shard, off + s, off + e - 1), np.uint16).astype(np.uint32) << 16).view(np.float32)
        w = w.reshape(dele.shape)
        aw = np.abs(w)
        rank = aw.ravel().argsort().argsort()[dele.ravel()] / (aw.size - 1)   # 0 = smallest abs W, 1 = largest
        q = np.quantile(aw, [0.1, 0.9])
        print(f'{L:2d} {E:4d}  {dele.mean():7.3%}  {aw[dele].mean() / aw[~dele].mean():12.3f}  {rank.mean():20.3f}  '
              f'{dele[aw <= q[0]].mean():22.3%}  {dele[aw >= q[1]].mean():19.3%}  {(w[dele] < 0).mean():12.3f}')
        pool['heavy' if dele.mean() > HEAVY else 'other'] += [
            dele.sum(), dele.size, aw[dele].sum(), aw[~dele].sum(), rank.sum(), dele[aw <= q[0]].sum(), (aw <= q[0]).sum(),
            dele[aw >= q[1]].sum(), (aw >= q[1]).sum(), (w[dele] < 0).sum()]
    for g, (nd, n, sd, sk, sr, db, nb, dt, nt, neg) in pool.items():
        if n:
            print(f'pooled {g} ({int(n // dele.size)} experts): deleted {nd / n:.3%}, absW del/kept '
                  f'{(sd / nd) / (sk / (n - nd)):.3f}, mean rank {sr / nd:.3f}, del in bottom 10% {db / nb:.2%}, '
                  f'in top 10% {dt / nt:.2%}, del with W<0 {neg / nd:.3f}')


QWEN_PROMPT = re.compile(r'<\|im_start\|>system\nYou are a helpful assistant\.<\|im_end\|>\n<\|im_start\|>user\n'
                         r'(?P<body>.*?)<\|im_end\|>\n<\|im_start\|>assistant\n?$', flags=re.DOTALL)


def cmd_calib(a):
    import hashlib
    import pandas as pd
    from transformers import AutoTokenizer
    df = pd.read_parquet(a.parquet)

    def messages(p):   # src/prepare_simplerl_zoo_train.py qwen_messages
        p = list(p)
        m = QWEN_PROMPT.match(p[0]['content']) if len(p) == 1 and p[0]['role'] == 'user' else None
        if m is None:
            sys.exit(f'prompt is not a qwen-boxed single user message: {p!r:.200}')
        return [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': m.group('body')}]
    df['prompt'] = [messages(p) for p in df['prompt']]
    rows = len(df)
    if len(df) > a.n:
        df = df.sample(n=a.n, random_state=42).reset_index(drop=True)
    tok = AutoTokenizer.from_pretrained(a.tokenizer)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    texts = [tok.apply_chat_template(list(m), tokenize=False, add_generation_prompt=True) for m in df['prompt']]
    ids = tok(texts, padding=True, truncation=True, max_length=a.max_length)['input_ids']
    width = len(ids[0])
    if {len(x) for x in ids} != {width} or tok.padding_side != 'right':
        sys.exit(f'expected right padding to one length, got {tok.padding_side} and {sorted({len(x) for x in ids})}')
    pad = sum(x.count(tok.pad_token_id) for x in ids)
    print(f'{len(df):,} prompts of {rows:,} rows in {a.parquet}; each {width} tokens after padding ({tok.pad_token!r}); '
          f'{len(ids) * width - pad:,} real + {pad:,} pad tokens; truncated: {sum(len(t) > width for t in tok(texts)["input_ids"])}')
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    for p in range(0, len(ids), a.per_part):
        part = ids[p:p + a.per_part]
        text = ''.join(tok.decode(x) for x in part)
        if tok(text, add_special_tokens=False)['input_ids'] != [t for x in part for t in x]:
            sys.exit(f'part {p // a.per_part}: the text does not tokenize back to the same {len(part) * width} tokens')
        (out / f'part{p // a.per_part:02d}.txt').write_text(text, encoding='utf-8')
        h.update(text.encode())
    print(f'wrote {-(-len(ids) // a.per_part)} parts of {a.per_part} prompts to {out}; sha256 of all parts in order '
          f'{h.hexdigest()}')


def imatrix_counts(paths) -> np.ndarray:
    """[layer, expert] routed calibration tokens, summed over llama-imatrix files."""
    from gguf import GGUFReader
    counts = {}
    for path in paths:
        for t in GGUFReader(path).tensors:
            m = re.fullmatch(r'blk\.(\d+)\.ffn_gate_exps\.weight\.counts', t.name)
            if m:
                c = np.asarray(t.data, np.float64).reshape(-1)
                counts[int(m.group(1))] = counts.get(int(m.group(1)), 0) + c
    if sorted(counts) != list(range(len(counts))) or not counts:
        sys.exit(f'expert counts missing for some layers: found {sorted(counts)}')
    return np.stack([counts[l] for l in range(len(counts))])


def cmd_routing(a):
    cnt = imatrix_counts(a.imatrix)
    layer, expert, dele, cells = per_matrix(Path(a.mask_dir))
    frac = {(int(l), int(e)): d / cells for l, e, d in zip(layer, expert, dele)}
    if cnt.shape != (layer.max() + 1, expert.max() + 1):
        sys.exit(f'imatrix has {cnt.shape} layers x experts, the mask {(layer.max() + 1, expert.max() + 1)}')
    heavy = {k for k, f in frac.items() if f > HEAVY}
    zero = {(l, e) for l in range(cnt.shape[0]) for e in range(cnt.shape[1]) if cnt[l, e] == 0}
    print(f'{cnt.shape[0]} layers x {cnt.shape[1]} experts; routed slots per layer {int(cnt.sum(1).min()):,} to '
          f'{int(cnt.sum(1).max()):,}; layer medians {np.median(cnt, 1).min():,.0f} to {np.median(cnt, 1).max():,.0f}')
    print(f'experts with zero calibration tokens: {len(zero)}; heavy experts: {len(heavy)}; heavy with zero tokens: '
          f'{len(heavy & zero)}; zero-token experts that are not heavy: {len(zero - heavy)}')
    for l, e in sorted(heavy):
        print(f'  heavy {l}:{e}: {int(cnt[l, e]):,} tokens (layer median {np.median(cnt[l]):,.0f}), {frac[l, e]:.3%} deleted')
    for l, e in sorted(zero - heavy):
        print(f'  not heavy, 0 tokens {l}:{e}: {frac[l, e]:.3%} deleted')
    few = [k for k in frac if k not in heavy and cnt[k] <= a.few]
    print(f'experts that are not heavy with <= {a.few} tokens: {len(few)} of {len(frac) - len(heavy)}')


def cmd_load(a):
    """Experts of a Team 5 run that got no (or almost no) routed tokens in the last logged snapshots."""
    if a.last < 1:
        sys.exit('--last must be at least 1')
    snaps = [r for r in (json.loads(x) for x in Path(a.metrics).read_text().splitlines() if x.strip())
             if 'expert_load' in r][-a.last:]
    if not snaps:
        sys.exit(f'{a.metrics}: no rows with expert_load')
    steps = [r['step'] for r in snaps]
    load = np.array([r['expert_load'] for r in snaps], np.int64)   # [snapshot, layer, expert]
    n_snap, L, E = load.shape
    even = load[-1].sum(1) / E
    print(f'{n_snap} snapshots, steps {steps[0]:,} to {steps[-1]:,}; {L} layers x {E} experts')
    print(f'step {steps[-1]:,}: routed slots per layer {int(load[-1].sum(1).min()):,} to {int(load[-1].sum(1).max()):,}, '
          f'even share per expert {even.min():,.0f} to {even.max():,.0f}')
    zero = [(l, e) for l in range(L) for e in range(E) if (load[:, l, e] == 0).all()]
    print(f'experts at 0 tokens in all {n_snap} snapshots: ' + (' '.join(f'{l}:{e}' for l, e in zero) or 'none'))
    print(f'experts below {a.below:.0%} of the even share at step {steps[-1]:,} (counts per snapshot):')
    low = [(l, e) for l in range(L) for e in range(E) if load[-1, l, e] < a.below * even[l]]
    for l, e in low:
        print(f'  {l}:{e}: ' + ', '.join(f'{int(c):,}' for c in load[:, l, e]) + f' (even share {even[l]:,.0f})')
    if a.gate:
        # Expected share of the targeted gate weights deleted at step 0 under dt/mask.py apply_wanda_prior, if these
        # experts get no calibration token. Logits start N(0, s^2); a calibrated matrix shifts its marked weights (scores
        # strictly below the k-th smallest, k = int(n * eta)) down by prior*s and the rest up, so they are deleted
        # (logit <= 0) with chance Phi(prior) and Phi(-prior); an unseen matrix keeps N(0, s^2) under official (1/2)
        # and is shifted up under keep (Phi(-prior)). The shared experts see every token, so they are calibrated.
        rows, cols = (int(x) for x in a.gate.lower().split('x'))
        n, mats = rows * cols, L * (E + a.shared)
        phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))   # noqa: E731
        marked = max(1, int(n * a.eta)) - 1
        seen = (marked * phi(a.prior) + (n - marked) * phi(-a.prior)) / n
        print(f'expected deleted share at step 0 (arithmetic, not run; --dt-targets g5_gate: one masked {rows}x{cols} '
              f'gate per routed expert and {a.shared} shared, {mats} in all; a calibrated one {seen:.4%}):')
        for what, k in ((f'the experts at 0 in every snapshot ({len(zero)})', len(zero)),
                        (f'all experts listed above ({len(low)})', len(low))):
            off = ((mats - k) * seen + k * 0.5) / mats
            keep = ((mats - k) * seen + k * phi(-a.prior)) / mats
            print(f'  if {what} get no calibration token: official {off:.3%}, keep {keep:.3%}')


def cmd_revive(a):
    """Toy: one unscored expert gate under G10's own dt/mask.py, with only the regulariser (no task gradient, as for an
    expert that no token reaches). dt/mask.py::regulariser_backward_ adds its keep-gradient to every masked layer,
    routed or not, so the logits of an idle expert still move. Prints the hard-mask deleted share over the steps."""
    import importlib.util
    import torch
    from torch import nn
    spec = importlib.util.spec_from_file_location('g10_dt_mask_revive', Path(__file__).resolve().parent / 'mask.py')
    dtmask = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dtmask)
    rows, cols = (int(x) for x in a.gate.lower().split('x'))
    marks = sorted({0, *a.at, a.steps})

    def lr_at(step):   # sft/bench/train.py lr_at: linear warmup, then cosine to min_lr_ratio * lr
        if step < a.warmup:
            return a.lr * (step + 1) / a.warmup
        t = (step - a.warmup) / max(1, a.steps - a.warmup)
        return a.lr * (a.min_lr_ratio + (1 - a.min_lr_ratio) * 0.5 * (1 + math.cos(math.pi * t)))

    print(f'one {rows}x{cols} gate, no calibration scores, regulariser only; AdamW lr {a.lr} (warmup {a.warmup}, cosine '
          f'to {a.min_lr_ratio}), betas (0.9, 0.95), eps 1e-8, wd 0; lambda {a.lam} -> 0; alpha {a.alpha[0]:g} -> '
          f'{a.alpha[1]:g} over {a.steps} steps; W from nn.Linear init, seed {a.seed}')
    print('grad scale  policy    ' + '  '.join(f'step {s:>4}' for s in marks))
    for scale in a.grad_scale:
        for policy in ('official', 'keep'):
            torch.manual_seed(a.seed)
            net = nn.Module()
            net.gate_proj = nn.Linear(cols, rows, bias=False)
            dtmask.convert(net, ('gate_proj',), a.alpha[0], a.alpha[1], a.steps, seed=a.seed)
            dtmask.apply_wanda_prior(net, {}, a.eta, a.prior, unseen=policy)   # no scores: the unseen rule only
            gate = net.gate_proj.gate
            opt = torch.optim.AdamW([gate], lr=a.lr, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.0)
            share = {0: float((gate <= 0).float().mean())}
            for step in range(a.steps):
                for g in opt.param_groups:
                    g['lr'] = lr_at(step)
                opt.zero_grad(set_to_none=True)
                dtmask.regulariser_backward_(net, dtmask.lambda_at(step, a.steps, a.lam))
                gate.grad.mul_(scale)   # stands in for a global grad-norm clip that scales every gradient
                opt.step()
                dtmask.step_all(net)
                if step + 1 in marks:
                    share[step + 1] = float((gate <= 0).float().mean())
            print(f'{scale:10g}  {policy:8s}  ' + '  '.join(f'{share[s]:9.3%}' for s in marks))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('masks')
    p.add_argument('mask_dir')
    p.add_argument('--partners', type=int, metavar='SEED', help='also pick one other expert per heavy one (same layer)')
    p.set_defaults(f=cmd_masks)
    p = sub.add_parser('weights')
    p.add_argument('mask_dir')
    p.add_argument('hf_repo')
    p.add_argument('experts', nargs='+')
    p.add_argument('--revision', default='1b75feb79f60b8dc6c5bc769a898c206a1c6a4f9',
                   help='Hub revision of hf_repo (default: the Qwen/Qwen3-30B-A3B-Base revision used in the note)')
    p.set_defaults(f=cmd_weights)
    p = sub.add_parser('calib')
    p.add_argument('parquet')
    p.add_argument('tokenizer')
    p.add_argument('out_dir')
    p.add_argument('--n', type=int, default=2048, help='mask_calib_num_samples')
    p.add_argument('--max-length', type=int, default=512, help='mask_calib_max_prompt_length')
    p.add_argument('--per-part', type=int, default=64, help='prompts per output file')
    p.set_defaults(f=cmd_calib)
    p = sub.add_parser('routing')
    p.add_argument('mask_dir')
    p.add_argument('imatrix', nargs='+')
    p.add_argument('--few', type=int, default=4, help='also count ordinary experts with at most this many tokens')
    p.set_defaults(f=cmd_routing)
    p = sub.add_parser('load')
    p.add_argument('metrics')
    p.add_argument('--last', type=int, default=5, help='use the last N expert_load snapshots')
    p.add_argument('--below', type=float, default=0.01, help='list experts under this share of the even share')
    p.add_argument('--gate', help='ROWSxCOLS of one expert gate matrix (e.g. 768x512): also print the expected '
                                  'step-0 deletion under --dt-unseen official and keep, assuming --dt-targets g5_gate '
                                  '(one masked matrix per expert; g5_mlp masks three)')
    p.add_argument('--shared', type=int, default=1, help='shared experts per layer (masked, always calibrated)')
    p.add_argument('--eta', type=float, default=0.00048828125, help='--dt-eta')
    p.add_argument('--prior', type=float, default=3.0, help='--dt-prior-strength')
    p.set_defaults(f=cmd_load)
    p = sub.add_parser('revive', help='toy: does the regulariser alone revive an unscored expert in dt/mask.py?')
    p.add_argument('--gate', default='768x512', help='ROWSxCOLS of the gate matrix')
    p.add_argument('--steps', type=int, default=243, help='DT optimizer steps (dryrun2_dt_compare.py --steps)')
    p.add_argument('--lr', type=float, default=5e-4, help='--dt-lr')
    p.add_argument('--warmup', type=int, default=10)
    p.add_argument('--min-lr-ratio', type=float, default=0.1)
    p.add_argument('--lam', type=float, default=1e-5, help='--dt-lambda')
    p.add_argument('--alpha', type=float, nargs=2, default=(100.0, 1000.0), help='--dt-alpha-start, --dt-alpha-end')
    p.add_argument('--eta', type=float, default=0.00048828125)
    p.add_argument('--prior', type=float, default=3.0)
    p.add_argument('--grad-scale', type=float, nargs='+', default=(1.0,), help='multiply the gradient (clip stand-in)')
    p.add_argument('--at', type=int, nargs='*', default=(10, 25, 50, 100), help='also report these steps')
    p.add_argument('--seed', type=int, default=0)
    p.set_defaults(f=cmd_revive)
    a = ap.parse_args(argv)
    a.f(a)


if __name__ == '__main__':
    main()
