"""Design 3 (Lab 5): packing study. Same model, seed, data order and step count; three ways to fill rows of T positions.

  window         one window per row: each document cut into windows of T+1 tokens, the last one padded (padding is
                 not scored). This is how the G5 trainer builds rows (teams/05 harness/week2/data.py DocumentWindows).
  packed_mask    documents end to end, eager attention with models.gpt.document_mask (a position sees only its own
                 document; learned positions restart at each document).
  packed_nomask  the same packed rows, no mask: a document also sees the end of the one before it.

In every arm the scored targets are "the next token inside the same document": the packed arms ignore the target that
crosses a document boundary, so each document token after the first is scored once in all three arms.

Per arm: fill (scored / positions), median step time, positions/s, scored tokens/s, bytes/s (UTF-8 bytes of the scored
targets), peak memory, train loss over the last steps, and held-out bpb on held-out documents scored one window per
row (the same held-out bytes for every arm). bpb here is provisional (Raj, 28 Nov): not the G5 held-out set.

  python -B perfkit/packing.py --source fineweb --data-dir DIR --steps 200 --seeds 0 1 --out packing.json
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


# ------------------------------------------------------------------------------ rows
def window_rows(docs, T: int, pad: int):
    """One window of one document per row: (x, y) of T tokens; padding targets are IGNORE."""
    for d in docs:
        for s in range(0, len(d) - 1, T):
            chunk = d[s:s + T + 1]
            x = np.full(T, pad, dtype=np.int64)
            y = np.full(T, IGNORE_INDEX, dtype=np.int64)
            x[:len(chunk) - 1] = chunk[:-1]
            y[:len(chunk) - 1] = chunk[1:]
            yield x, y, None


def packed_rows(docs, T: int):
    """Documents end to end, rows of T+1 tokens that overlap by one (row r+1 starts at token T of row r).
    y is IGNORE where the next token belongs to the next document; doc ids are numbered from 0 in each row."""
    toks = np.concatenate(docs)
    owner = np.concatenate([np.full(len(d), i, dtype=np.int64) for i, d in enumerate(docs)])
    for s in range(0, len(toks) - T, T):
        tok, own = toks[s:s + T + 1], owner[s:s + T + 1]
        x, y = tok[:-1].copy(), tok[1:].copy()
        y[own[1:] != own[:-1]] = IGNORE_INDEX
        yield x, y, own[:-1] - own[0]


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
        out.append((x, y, d))
    return out


# ------------------------------------------------------------------------------ one arm
def steps_for_budget(batch_list, budget: int, cap: int) -> int:
    """Smallest number of measured batches whose scored targets reach budget (at most cap)."""
    total = 0
    for i, (_, y, _) in enumerate(batch_list[:cap]):
        total += int((y != IGNORE_INDEX).sum())
        if total >= budget:
            return i + 1
    return cap


def window_fill(docs, T: int) -> float:
    """Fill of one-window-per-row at row length T, from the document lengths alone: scored / (rows x T)."""
    n = np.array([len(d) for d in docs], dtype=np.int64)
    rows = np.ceil((n - 1) / T)
    return float((n - 1).sum() / (rows.sum() * T))


def run_arm(cfg_path, overrides, arm, docs, heldout, seed, steps, warmup, byte_len, budget=None):
    cfg = load_config(cfg_path, list(overrides) + [f"run.seed={seed}", "data.source=synthetic",
                                                   "model.attn_impl=eager"])
    device = B.pick_device(cfg["run"]["device"])
    s = B.build(cfg, device)
    T, Bsz = s.loader.T, s.loader.B
    pad = 0
    rows = window_rows(docs, T, pad) if arm == "window" else packed_rows(docs, T)
    cap = steps if budget is None else 50 * steps
    data = batches(rows, Bsz, warmup + cap)
    if budget is not None:                       # equal scored-token budget: as many steps as this arm needs
        steps = steps_for_budget(data[warmup:], budget, cap)
        data = data[:warmup + steps]
    cuda = device.type == "cuda"

    def step(x, y, d):
        x = torch.from_numpy(x).to(device, non_blocking=True)
        y = torch.from_numpy(y).to(device, non_blocking=True)
        ctx = document_mask(torch.from_numpy(d).to(device)) if (arm == "packed_mask") else _null()
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

    for x, y, d in data[:warmup]:
        step(x, y, d)
    if cuda:
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
    times, losses, scored, nbytes = [], [], 0, 0
    for x, y, d in data[warmup:]:
        mask = y != IGNORE_INDEX
        scored += int(mask.sum())
        nbytes += int(byte_len[y[mask]].sum())
        if cuda:
            a, b = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
            a.record()
            losses.append(step(x, y, d))
            b.record()
            times.append((a, b))
        else:
            t0 = time.perf_counter()
            losses.append(step(x, y, d))
            times.append((time.perf_counter() - t0) * 1e3)
    if cuda:
        torch.cuda.synchronize(device)
        times = [a.elapsed_time(b) for a, b in times]
    med = float(np.median(times))
    positions = steps * Bsz * T
    rates = B.throughput_rates(med, positions_per_step=Bsz * T, scored_tokens_per_step=scored / steps,
                               scored_bytes_per_step=nbytes / steps)
    tail = max(1, steps // 10)
    return {
        "arm": arm, "seed": seed, "steps": steps, "warmup": warmup, "B": Bsz, "T": T,
        "fill": round(scored / positions, 4), "scored_tokens": scored, "scored_bytes": nbytes,
        "step_ms_median": round(med, 3), "step_ms_p90": round(float(np.percentile(times, 90)), 3),
        **{k: round(v, 2) for k, v in rates.items()},
        "train_loss_last": round(float(torch.stack(losses[-tail:]).float().mean()), 4),
        "heldout_bpb": heldout_bpb(s, heldout, byte_len, pad),
        "peak_memory": M.memory(device), "dtype": s.dtype, "gpu": M.device_name(device),
    }


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@torch.no_grad()
def heldout_bpb(s, docs, byte_len, pad) -> float:
    """Sum of next-token CE (nats) / ln 2 / UTF-8 bytes of the scored targets, one window per row."""
    s.core.eval()
    nats, nbytes = 0.0, 0
    rows = list(window_rows(docs, s.loader.T, pad))
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
    ap.add_argument("--equal-budget", action="store_true",
                    help="every arm trains on the scored tokens the window arm gets in --steps steps (fair bpb)")
    ap.add_argument("--out", default=None)
    ap.add_argument("overrides", nargs="*")
    a = ap.parse_args(argv)

    cfg = load_config(a.config, list(a.overrides) + ["data.source=synthetic"])
    from dataio.tokenizer import BrahmicTokenizer
    tok = BrahmicTokenizer(cfg["data"]["tokenizer_path"])
    byte_len = np.array([len(b) for b in tok.raw_token_bytes()], dtype=np.int64)
    if a.source == "fineweb":
        eos = tok.spec["model"]["vocab"]["<|end_of_text|>"]
        docs = fineweb_documents(a.data_dir, "train", a.max_docs, eos)
        heldout = fineweb_documents(a.data_dir, "val", a.heldout_docs, eos)
    else:
        V = cfg["model"]["vocab_size"]
        docs = synthetic_documents(a.max_docs, V, 0.4 * cfg["model"]["block_size"], seed=123)
        heldout = synthetic_documents(a.heldout_docs, V, 0.4 * cfg["model"]["block_size"], seed=456)

    budget = None
    if a.equal_budget:
        T = load_config(a.config, list(a.overrides))["model"]["block_size"]
        Bsz = B.resolve_batch(load_config(a.config, list(a.overrides))["run"]["batch_size"])
        w = batches(window_rows(docs, T, 0), Bsz, a.warmup + a.steps)[a.warmup:]
        budget = int(sum(int((y != IGNORE_INDEX).sum()) for _, y, _ in w))
    rows = [run_arm(a.config, a.overrides, arm, docs, heldout, seed, a.steps, a.warmup, byte_len, budget)
            for seed in a.seeds for arm in a.arms]
    commit, dirty = M.git_state()
    res = {"measure": "design3_packing", "command": "python -B perfkit/packing.py " + " ".join(argv or sys.argv[1:]),
           "commit": commit, "dirty": dirty, "torch": torch.__version__, "source": a.source,
           "documents": len(docs), "document_tokens": int(sum(len(d) for d in docs)),
           "document_len_median": float(np.median([len(d) for d in docs])),
           "heldout_documents": len(heldout), "equal_budget_scored_tokens": budget,
           "window_fill_by_T": {T_: round(window_fill(docs, T_), 4) for T_ in (256, 512, 1024, 2048, 4096)},
           "runs": rows,
           "notes": ["bpb provisional: held-out documents from the same source, not the G5 held-out set",
                     "packed arms ignore the target that crosses a document boundary; window pads are not scored",
                     "packed_mask restarts learned positions per document; packed_nomask does not"]}
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(text)
    print("window fill by T:", res["window_fill_by_T"], "| budget:", budget)
    keys = ("arm", "seed", "steps", "fill", "step_ms_median", "positions_per_s", "scored_tokens_per_s", "bytes_per_s",
            "train_loss_last", "heldout_bpb")
    print(" | ".join(keys))
    for r in rows:
        print(" | ".join(str(r[k]) for k in keys))


if __name__ == "__main__":
    main()
