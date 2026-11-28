"""Design 3 (Lab 5): packing study. Same model, seed, data order and step count; three ways to fill rows of T positions.

  window         one window per row, the rest padded (padding is not scored): how the G5 trainer builds rows today
                 (teams/05 harness/week2/data.py DocumentWindows.batch).
  packed_mask    several windows per row, models.gpt.document_mask (a position sees only its own window; learned
                 positions restart at each window).
  packed_nomask  the same packed rows, no mask: a window also sees the windows before it in the row.

Two row formats (--rows):

  890     (default) the packed-row format of #890, which Team 6's loader follows. Each document is cut into windows of
          at most T targets; the first input is BOS (first window of a document) or the token before the window, so
          every document token is a target once and no end-of-text is trained on. Windows are shuffled (--data-seed);
          packed rows take the largest pooled window that still fits from a pool of the next --pack-pool windows
          (#890 BatchStream.next_packed, one pass), never cut a window, and carry doc_ids (1, 2, ... per window, 0 on
          padding) and pos_ids (0 at each window start).
  stream  the bring-up format of the first #940 results: documents (with their end-of-text) end to end, rows of T+1
          tokens cut every T, so documents are cut at row ends; window rows are windows of T+1 tokens of one
          document. Kept to reproduce those numbers.

In both formats every arm scores the same targets (each once), so fill = scored / positions compares like with like.

Per arm: fill, median step time, positions/s, scored tokens/s, bytes/s (UTF-8 bytes of the scored targets, #888), peak
memory, train loss over the last steps, and held-out bpb on held-out documents scored one window per row (the same
held-out bytes for every arm). bpb here is provisional (Raj, 28 Nov): not the G5 held-out set.

  python -B perfkit/packing.py --source fineweb --data-dir DIR --steps 200 --seeds 0 1 --attn sdpa --out packing.json
  python -B perfkit/packing.py --config configs/tiny_cpu.yaml --source synthetic --steps 5 --warmup 1   # smoke
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dataio.loader import open_shard  # noqa: E402
from models.config import load_config  # noqa: E402
from models.gpt import IGNORE_INDEX, document_mask  # noqa: E402
from perfkit import bench as B  # noqa: E402
from perfkit import metrics as M  # noqa: E402

ARMS = ("window", "packed_mask", "packed_nomask")
PACK_POOL = 16                                   # #890 run.pack_pool default


# ------------------------------------------------------------------------------ documents
def fineweb_documents(data_dir: str, split: str, max_docs: int, eos: int) -> list:
    """Documents from prepared FineWeb shards (documents are joined by end-of-text there); eos kept at each end."""
    docs = []
    for path in sorted(Path(data_dir).expanduser().glob(f"fineweb_{split}_*.bin")):
        toks = np.asarray(open_shard(path))
        ends = np.flatnonzero(toks == eos)
        start = 0
        for e in ends:
            if e + 1 - start >= 2:
                docs.append(toks[start:e + 1].astype(np.int64))
            start = e + 1
            if len(docs) >= max_docs:
                return docs
    if not docs:
        raise FileNotFoundError(f"no fineweb_{split}_*.bin documents in {data_dir}")
    return docs


def synthetic_documents(n: int, vocab: int, mean_len: float, seed: int) -> list:
    """Smoke data: log-normal lengths (median mean_len), uniform token ids."""
    rng = np.random.default_rng(seed)
    lens = np.maximum(2, rng.lognormal(math.log(mean_len), 1.0, n).astype(np.int64))
    return [rng.integers(0, vocab, size=int(k), dtype=np.int64) for k in lens]


# ------------------------------------------------------------------------------ rows: #890 format
def doc_windows(docs, T: int, bos: int) -> list:
    """(inputs, targets) per window, G5 DocumentWindows rule: at most T targets; the first input is bos for a
    document's first window, else the token before the window. Every document token is a target exactly once."""
    out = []
    for d in docs:
        for s in range(0, len(d), T):
            tgt = np.asarray(d[s:s + T], dtype=np.int64)
            prev = bos if s == 0 else int(d[s - 1])
            out.append((np.concatenate([[prev], tgt[:-1]]).astype(np.int64), tgt))
    return out


def one_window_rows(windows, order, T: int, pad: int):
    """One window per row (today's G5 rows): the rest of the row is padding with IGNORE targets."""
    for i in order:
        xin, tgt = windows[i]
        x = np.full(T, pad, dtype=np.int64)
        y = np.full(T, IGNORE_INDEX, dtype=np.int64)
        x[:len(tgt)], y[:len(tgt)] = xin, tgt
        yield x, y, None, None


def pool_rows(windows, order, T: int, pad: int, pool: int = PACK_POOL):
    """#890 packed rows over one pass of order: each row repeatedly takes the largest pooled window that still fits
    (the earliest on a tie) and refills the pool from the next windows in order, until nothing fits; the rest is
    padding. Yields x, y, doc_ids (int32: 1, 2, ... per window, 0 on padding), pos_ids (int32: 0 at each window)."""
    order, off, held = list(order), 0, []
    size = lambda w: len(windows[w][1])                                         # noqa: E731
    while True:
        row, left = [], T
        while True:
            while len(held) < pool and off < len(order):
                held.append(order[off])
                off += 1
            fits = [j for j, w in enumerate(held) if size(w) <= left]
            if not fits:
                break
            j = max(fits, key=lambda j: (size(held[j]), -j))
            w = held.pop(j)
            row.append(w)
            left -= size(w)
        if not row:
            return
        x = np.full(T, pad, dtype=np.int64)
        y = np.full(T, IGNORE_INDEX, dtype=np.int64)
        doc = np.zeros(T, dtype=np.int32)
        pos = np.zeros(T, dtype=np.int32)
        at = 0
        for k, w in enumerate(row, start=1):
            xin, tgt = windows[w]
            n = len(tgt)
            x[at:at + n], y[at:at + n], doc[at:at + n], pos[at:at + n] = xin, tgt, k, np.arange(n)
            at += n
        yield x, y, doc, pos


# ------------------------------------------------------------------------------ rows: bring-up (stream) format
def window_rows(docs, T: int, pad: int):
    """One window of one document per row: (x, y) of T tokens; padding targets are IGNORE."""
    for d in docs:
        for s in range(0, len(d) - 1, T):
            chunk = d[s:s + T + 1]
            x = np.full(T, pad, dtype=np.int64)
            y = np.full(T, IGNORE_INDEX, dtype=np.int64)
            x[:len(chunk) - 1] = chunk[:-1]
            y[:len(chunk) - 1] = chunk[1:]
            yield x, y, None, None


def packed_rows(docs, T: int):
    """Documents end to end, rows of T+1 tokens that overlap by one (row r+1 starts at token T of row r).
    y is IGNORE where the next token belongs to the next document; doc ids are numbered from 0 in each row."""
    toks = np.concatenate(docs)
    owner = np.concatenate([np.full(len(d), i, dtype=np.int64) for i, d in enumerate(docs)])
    for s in range(0, len(toks) - T, T):
        tok, own = toks[s:s + T + 1], owner[s:s + T + 1]
        x, y = tok[:-1].copy(), tok[1:].copy()
        y[own[1:] != own[:-1]] = IGNORE_INDEX
        yield x, y, own[:-1] - own[0], None


# ------------------------------------------------------------------------------ batches
def arm_rows(arm: str, fmt: dict, docs, T: int, pad: int = 0) -> list:
    """The rows one arm trains on, in order. fmt: {"rows": "890" | "stream", "bos", "data_seed", "pool"}."""
    if fmt["rows"] == "stream":
        return list(window_rows(docs, T, pad) if arm == "window" else packed_rows(docs, T))
    windows = doc_windows(docs, T, fmt["bos"])
    # the window order #890's BatchStream draws for this seed, so its pass and this one place the same rows
    order = torch.randperm(len(windows), generator=torch.Generator().manual_seed(fmt["data_seed"])).tolist()
    if arm == "window":
        return list(one_window_rows(windows, order, T, pad))
    return list(pool_rows(windows, order, T, pad, fmt["pool"]))


def batches(rows, batch_size: int, steps: int):
    """steps batches of batch_size rows, cycling over the rows (same order every pass)."""
    rows = list(rows)
    if len(rows) < batch_size:
        raise ValueError(f"only {len(rows)} rows for batch_size {batch_size}: give more documents")
    out, i = [], 0
    for _ in range(steps):
        pick = [rows[(i + k) % len(rows)] for k in range(batch_size)]
        i += batch_size
        x = np.stack([r[0] for r in pick])
        y = np.stack([r[1] for r in pick])
        d = None if pick[0][2] is None else np.stack([r[2] for r in pick])
        p = None if pick[0][3] is None else np.stack([r[3] for r in pick])
        out.append((x, y, d, p))
    return out


# ------------------------------------------------------------------------------ one arm
def steps_for_budget(batch_list, budget: int, cap: int) -> int:
    """Smallest number of measured batches whose scored targets reach budget (at most cap)."""
    total = 0
    for i, b in enumerate(batch_list[:cap]):
        total += int((b[1] != IGNORE_INDEX).sum())
        if total >= budget:
            return i + 1
    return cap


def window_fill(docs, T: int, bos: bool = True) -> float:
    """Fill of one-window-per-row at row length T, from the document lengths alone: scored / (rows x T).
    bos=True: #890 windows (every token a target); False: stream windows (the first token has no target)."""
    n = np.array([len(d) for d in docs], dtype=np.int64) - (0 if bos else 1)
    rows = np.ceil(n / T)
    return float(n.sum() / (rows.sum() * T))


def run_arm(cfg_path, overrides, arm, docs, heldout_rows, seed, steps, warmup, byte_len, fmt, attn, budget=None):
    cfg = load_config(cfg_path, list(overrides) + [f"run.seed={seed}", "data.source=synthetic",
                                                   f"model.attn_impl={attn}"])
    device = B.pick_device(cfg["run"]["device"])
    s = B.build(cfg, device)
    T, Bsz = s.loader.T, s.loader.B
    rows = arm_rows(arm, fmt, docs, T)
    cap = steps if budget is None else 50 * steps
    data = batches(rows, Bsz, warmup + cap)
    if budget is not None:                       # equal scored-token budget: as many steps as this arm needs
        steps = steps_for_budget(data[warmup:], budget, cap)
        data = data[:warmup + steps]
    cuda = device.type == "cuda"

    def to(a):
        return None if a is None else torch.from_numpy(a).to(device, non_blocking=True)

    def step(x, y, d, p):
        x, y = to(x), to(y)
        ctx = document_mask(to(d), to(p)) if arm == "packed_mask" else _null()
        with ctx:
            with s.autocast():
                loss = s.model(x, y)[1]
            (s.scaler.scale(loss) if s.scaler is not None else loss).backward()
        if s.scaler is not None:
            s.opt.unscale(s.scaler)
        if s.grad_clip:
            torch.nn.utils.clip_grad_norm_(s.core.parameters(), s.grad_clip)
        s.opt.step(s.scaler)
        if s.scaler is not None:
            s.scaler.update()
        for m in s.core.moe_layers():
            m.update_bias()
        s.opt.zero_grad()
        return loss.detach()

    for b in data[:warmup]:
        step(*b)
    if cuda:
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
    times, losses, scored, nbytes = [], [], 0, 0
    for b in data[warmup:]:
        y = b[1]
        mask = y != IGNORE_INDEX
        scored += int(mask.sum())
        nbytes += int(byte_len[y[mask]].sum())
        if cuda:
            e0, e1 = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            e0.record()
            losses.append(step(*b))
            e1.record()
            times.append((e0, e1))
        else:
            t0 = time.perf_counter()
            losses.append(step(*b))
            times.append((time.perf_counter() - t0) * 1e3)
    if cuda:
        torch.cuda.synchronize(device)
        times = [e0.elapsed_time(e1) for e0, e1 in times]
    med = float(np.median(times))
    positions = steps * Bsz * T
    rates = B.throughput_rates(med, positions_per_step=Bsz * T, scored_tokens_per_step=scored / steps,
                               scored_bytes_per_step=nbytes / steps)
    tail = max(1, steps // 10)
    return {
        "arm": arm, "seed": seed, "steps": steps, "warmup": warmup, "B": Bsz, "T": T, "attn_impl": attn,
        "rows_per_pass": len(rows),
        "fill": round(scored / positions, 4), "scored_tokens": scored, "scored_bytes": nbytes,
        "step_ms_median": round(med, 3), "step_ms_p90": round(float(np.percentile(times, 90)), 3),
        **{k: round(v, 2) for k, v in rates.items()},
        "train_loss_last": round(float(torch.stack(losses[-tail:]).float().mean()), 4),
        "heldout_bpb": heldout_bpb(s, heldout_rows, byte_len),
        "peak_memory": M.memory(device), "dtype": s.dtype, "gpu": M.device_name(device),
    }


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@torch.no_grad()
def heldout_bpb(s, rows, byte_len) -> float:
    """Sum of next-token CE (nats) / ln 2 / UTF-8 bytes of the scored targets; rows: one window per row."""
    s.core.eval()
    nats, nbytes = 0.0, 0
    for i in range(0, len(rows), s.loader.B):
        x = torch.from_numpy(np.stack([r[0] for r in rows[i:i + s.loader.B]])).to(s.device)
        yn = np.stack([r[1] for r in rows[i:i + s.loader.B]])
        n = int((yn != IGNORE_INDEX).sum())
        if n == 0:
            continue
        with s.autocast():                       # mean CE over the scored targets (any ce_impl) x their count
            loss = s.core(x, torch.from_numpy(yn).to(s.device))[1]
        nats += float(loss.float()) * n
        nbytes += int(byte_len[yn[yn != IGNORE_INDEX]].sum())
    s.core.train()
    return round(nats / math.log(2) / nbytes, 5) if nbytes else None


# ------------------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=str(ROOT / "configs" / "base.yaml"))
    ap.add_argument("--source", choices=("fineweb", "synthetic"), default="fineweb")
    ap.add_argument("--data-dir", default=None, help="prepared FineWeb shards (dataio.prepare_fineweb)")
    ap.add_argument("--max-docs", type=int, default=20000)
    ap.add_argument("--heldout-docs", type=int, default=200)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--arms", nargs="+", default=list(ARMS), choices=ARMS)
    ap.add_argument("--rows", choices=("890", "stream"), default="890",
                    help="890: #890 packed-row format (default); stream: the first bring-up format")
    ap.add_argument("--attn", choices=("eager", "sdpa"), default="eager",
                    help="attention for every arm (#890: sdpa with the mask is faster than eager)")
    ap.add_argument("--pack-pool", type=int, default=PACK_POOL, help="#890 run.pack_pool (rows 890)")
    ap.add_argument("--data-seed", type=int, default=1234, help="window order (rows 890), same for every arm")
    ap.add_argument("--equal-budget", action="store_true",
                    help="every arm trains on the scored tokens the window arm gets in --steps steps (fair bpb)")
    ap.add_argument("--out", default=None)
    ap.add_argument("overrides", nargs="*")
    a = ap.parse_args(argv)
    if a.pack_pool < 1:
        ap.error("--pack-pool must be at least 1")

    cfg = load_config(a.config, list(a.overrides) + ["data.source=synthetic"])
    from dataio.tokenizer import BrahmicTokenizer
    tok = BrahmicTokenizer(cfg["data"]["tokenizer_path"])
    byte_len = np.array([len(b) for b in tok.raw_token_bytes()], dtype=np.int64)
    vocab = tok.spec["model"]["vocab"]
    if a.source == "fineweb":
        eos = vocab["<|end_of_text|>"]
        docs = fineweb_documents(a.data_dir, "train", a.max_docs, eos)
        heldout = fineweb_documents(a.data_dir, "val", a.heldout_docs, eos)
        if a.rows == "890":                      # G5 encodes documents without end-of-text and never trains on it
            docs = [d[:-1] for d in docs]
            heldout = [d[:-1] for d in heldout]
    else:
        V = cfg["model"]["vocab_size"]
        docs = synthetic_documents(a.max_docs, V, 0.4 * cfg["model"]["block_size"], seed=123)
        heldout = synthetic_documents(a.heldout_docs, V, 0.4 * cfg["model"]["block_size"], seed=456)
    fmt = {"rows": a.rows, "bos": vocab["<|begin_of_text|>"], "data_seed": a.data_seed, "pool": a.pack_pool}

    full = load_config(a.config, list(a.overrides))
    T = full["model"]["block_size"]
    if a.rows == "890":                          # held-out: one window per row, document order (no shuffle)
        hw = doc_windows(heldout, T, fmt["bos"])
        heldout_rows = list(one_window_rows(hw, range(len(hw)), T, 0))
    else:
        heldout_rows = list(window_rows(heldout, T, 0))
    budget = None
    if a.equal_budget:
        Bsz = B.resolve_batch(full["run"]["batch_size"])
        w = batches(arm_rows("window", fmt, docs, T), Bsz, a.warmup + a.steps)[a.warmup:]
        budget = int(sum(int((b[1] != IGNORE_INDEX).sum()) for b in w))
    rows = [run_arm(a.config, a.overrides, arm, docs, heldout_rows, seed, a.steps, a.warmup, byte_len, fmt, a.attn,
                    budget)
            for seed in a.seeds for arm in a.arms]
    commit, dirty = M.git_state()
    bos_rule = a.rows == "890"
    res = {"measure": "design3_packing", "command": "python -B perfkit/packing.py " + " ".join(argv or sys.argv[1:]),
           "commit": commit, "dirty": dirty, "torch": torch.__version__, "source": a.source,
           "rows": a.rows, "attn_impl": a.attn, "pack_pool": a.pack_pool if bos_rule else None,
           "data_seed": a.data_seed if bos_rule else None,
           "documents": len(docs), "document_tokens": int(sum(len(d) for d in docs)),
           "document_len_median": float(np.median([len(d) for d in docs])),
           "heldout_documents": len(heldout), "equal_budget_scored_tokens": budget,
           "window_fill_by_T": {T_: round(window_fill(docs, T_, bos_rule), 4) for T_ in (256, 512, 1024, 2048, 4096)},
           "runs": rows,
           "notes": ["bpb provisional: held-out documents from the same source, not the G5 held-out set",
                     ("rows 890: #890 windows (BOS first input, no end-of-text target), best-fit pool, doc_ids 0 on "
                      "padding" if bos_rule else
                      "rows stream: packed arms ignore the target that crosses a document boundary"),
                     "window pads are not scored; packed_mask restarts learned positions per window, packed_nomask "
                     "does not"]}
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(text)
    print("rows:", a.rows, "| attn:", a.attn, "| window fill by T:", res["window_fill_by_T"], "| budget:", budget)
    keys = ("arm", "seed", "steps", "fill", "step_ms_median", "positions_per_s", "scored_tokens_per_s", "bytes_per_s",
            "train_loss_last", "heldout_bpb")
    print(" | ".join(keys))
    for r in rows:
        print(" | ".join(str(r[k]) for k in keys))


if __name__ == "__main__":
    main()
