#!/usr/bin/env python3
"""Quantized policy for GRPO rollouts: speed and mismatch per bit-width against bf16 (G12 design task 3, with G10).

    python quant_rollout_mismatch.py --ref model-bf16.gguf --quant Q8_0=model-Q8_0.gguf --quant Q6_K=model-Q6_K.gguf \\
        --prompts ../prompts/fixed_100.jsonl --out rollout_mismatch.json [--n 48] [--k 8] [--max-new 256] [--eps 0.2]

The question G10's trainer asks of a sampler (rl-loop/mismatch_probe.py): objective_v1 keeps a token only when
ratio = trainer / sampler lies in [1 - eps, 1 + eps]. With a quantized sampler the ratio differs from 1 by the
quantization error. Here the sampler is a quantized GGUF and the "trainer" is the bf16 GGUF of the same checkpoint:

  1. the quantized model draws k completions per prompt at temperature 1 (top-k, top-p and min-p off, so the sampled
     distribution is the model's own softmax); the decode speed is timed (rollout tokens/s);
  2. both models score the same token ids, teacher-forced, with their full logits;
  3. per sampled token: log_ratio = log p_bf16 - log p_quant; per position: KL(bf16 || quant) over the whole
     vocabulary and whether the two models' top-1 tokens agree.

Reported per format (same numbers as mismatch_probe.py, so the two reports can be read side by side): share of tokens
outside [1 - eps, 1 + eps] (below, above), mean and quantiles of |log_ratio|, k3 = mean(r - log r - 1), plus mean KL,
top-1 agreement, and the tokens/s of the rollout. Aggregate numbers only: no prompt or completion text is written.

Not the same as G10's number: bf16 here is llama.cpp's bf16, not the torch trainer's fp32-master / bf16 autocast, so the
engine-to-engine gap of G10's probe is not in these numbers, only the quantization gap (with llama.cpp's own bf16
arithmetic as the floor). `--quant bf16=<same file>` is a determinism check, not a noise floor: the teacher-forced
logits of one file are bit-identical on every run, so it must report exactly 0 (any other value means a bug).
"""
from __future__ import annotations

import argparse, json, math, sys, time
from pathlib import Path

import numpy as np

P_BUCKETS = ((0.0, 0.1), (0.1, 0.5), (0.5, 0.9), (0.9, 1.0001))   # by the sampler's probability, as mismatch_probe.py
POS_BUCKETS = ((0, 64), (64, 256), (256, 10**9))
EPS = 0.2                                                           # grpo.TR_EPSILON; override with --eps


def log_softmax(x: np.ndarray) -> np.ndarray:
    x = x.astype(np.float64)
    m = x.max(axis=-1, keepdims=True)
    return x - m - np.log(np.exp(x - m).sum(axis=-1, keepdims=True))


def position_stats(ref_logits: np.ndarray, q_logits: np.ndarray, tokens: np.ndarray, chunk: int = 64) -> dict:
    """ref_logits, q_logits: [T, V], row t predicts tokens[t]. Returns arrays of length T (float64 inside, in chunks)."""
    lp_ref, lp_q, kl, agree, top_ref, top_q = [], [], [], [], [], []
    for i in range(0, len(tokens), chunk):
        a, b = log_softmax(ref_logits[i:i + chunk]), log_softmax(q_logits[i:i + chunk])
        t = tokens[i:i + chunk]
        rows = np.arange(len(t))
        lp_ref.append(a[rows, t]); lp_q.append(b[rows, t])
        kl.append((np.exp(a) * (a - b)).sum(axis=-1))
        top_ref.append(a.argmax(-1)); top_q.append(b.argmax(-1))
        agree.append(top_ref[-1] == top_q[-1])
    return {"lp_ref": np.concatenate(lp_ref), "lp_q": np.concatenate(lp_q),
            "kl": np.concatenate(kl), "agree": np.concatenate(agree),
            "top1_ref": np.concatenate(top_ref), "top1_q": np.concatenate(top_q)}


def quantiles(a: np.ndarray) -> list[float]:
    return [float(f"{x:.4g}") for x in np.quantile(a, [0.5, 0.9, 0.99, 0.999])]


def ratio_stats(log_ratio: np.ndarray, eps: float) -> dict:
    """Same fields as mismatch_probe.ratio_stats; log_ratio = log(trainer) - log(sampler) over real tokens."""
    n = log_ratio.size
    if n == 0:
        return {"tokens": 0}
    r, a = np.exp(log_ratio), np.abs(log_ratio)
    below, above = r < 1 - eps, r > 1 + eps
    return {"tokens": int(n), "outside": float((below | above).mean()), "below": float(below.mean()),
            "above": float(above.mean()), "mean_abs_logratio": float(a.mean()),
            "abs_logratio_p50_p90_p99_p999": quantiles(a), "max_abs_logratio": float(a.max()),
            "k3": float((r - log_ratio - 1).mean())}


def cluster_bootstrap(per_pos: dict, clusters: np.ndarray, eps: float = EPS, n_boot: int = 2000, seed: int = 0) -> dict:
    """95% percentile intervals of the share outside [1 - eps, 1 + eps], mean |log-ratio|, k3, top-1 agreement (and KL when
    present), resampling whole clusters (prompts) with replacement: the 8 rollouts of a prompt are not independent."""
    lr = per_pos["lp_ref"] - per_pos["lp_q"]
    r = np.exp(lr)
    cols = {"outside": ((r < 1 - eps) | (r > 1 + eps)).astype(float), "mean_abs_logratio": np.abs(lr),
            "k3": r - lr - 1, "top1_agreement": per_pos["agree"].astype(float)}
    if "kl" in per_pos:
        cols["mean_kl_ref_to_quant"] = per_pos["kl"].astype(float)
    ids, inv = np.unique(clusters, return_inverse=True)
    n = np.bincount(inv, minlength=len(ids)).astype(float)
    sums = {k: np.bincount(inv, weights=v, minlength=len(ids)) for k, v in cols.items()}
    pick = np.random.default_rng(seed).integers(0, len(ids), (n_boot, len(ids)))
    tot = n[pick].sum(1)
    out = {}
    for k, s in sums.items():
        est = s[pick].sum(1) / tot
        lo, hi = np.percentile(est, [2.5, 97.5])
        out[k] = [float(f"{lo:.4g}"), float(f"{hi:.4g}")]
    out["clusters"] = int(len(ids))
    return out


def aggregate(per_pos: dict, positions: np.ndarray, eps: float = EPS, clusters: np.ndarray | None = None) -> dict:
    """per_pos: concatenated position_stats arrays over all rollouts; positions: index of each token in its completion."""
    log_ratio = per_pos["lp_ref"] - per_pos["lp_q"]
    out = ratio_stats(log_ratio, eps)
    if not out["tokens"]:
        return out
    out["top1_agreement"] = float(per_pos["agree"].mean())
    if "kl" in per_pos:
        out["mean_kl_ref_to_quant"] = float(per_pos["kl"].mean())
    p = np.exp(per_pos["lp_q"])
    out["by_sampler_prob"] = {f"{lo}-{min(hi, 1.0)}": ratio_stats(log_ratio[(p >= lo) & (p < hi)], eps)
                              for lo, hi in P_BUCKETS if ((p >= lo) & (p < hi)).any()}
    out["by_position"] = {f"{lo}-{hi if hi < 10**9 else 'end'}": ratio_stats(log_ratio[(positions >= lo) & (positions < hi)], eps)
                          for lo, hi in POS_BUCKETS if ((positions >= lo) & (positions < hi)).any()}
    if clusters is not None:
        out["ci95_by_prompt"] = cluster_bootstrap(per_pos, clusters, eps)
    return out


def load_prompt_rows(path: Path) -> list[tuple[str, str]]:
    """(text, category) per prompt: jsonl with a "prompt", "statement" or "question" field (and an optional "category"),
    or one prompt per line (category "")."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            out.append((next(row[k] for k in ("prompt", "statement", "question") if k in row), str(row.get("category", ""))))
        except (json.JSONDecodeError, StopIteration, TypeError, AttributeError):
            out.append((line, ""))
    return out


def select_prompts(rows: list[tuple[str, str]], n: int, balanced: bool = False) -> list[tuple[str, str]]:
    """The first n prompts, or with `balanced` n prompts taken round-robin across the categories (in file order within a
    category), so a file that lists its categories one after another (fixed_100.jsonl: 40 English first) is not read as one."""
    if not balanced:
        return rows[:n]
    by_cat: dict[str, list] = {}
    for r in rows:
        by_cat.setdefault(r[1], []).append(r)
    out, i = [], 0
    while len(out) < n and any(i < len(v) for v in by_cat.values()):
        out += [v[i] for v in by_cat.values() if i < len(v)][:n - len(out)]
        i += 1
    return out


def load_prompts(path: Path, n: int, balanced: bool = False) -> list[str]:
    return [text for text, _ in select_prompts(load_prompt_rows(path), n, balanced)]


class LlamaEngine:
    """One GGUF through llama-cpp-python (the build eval_wide uses): sampling with timing, and teacher-forced logits."""

    def __init__(self, path: str, n_ctx: int = 2048, n_gpu_layers: int = -1, seed: int = 1234):
        from llama_cpp import Llama
        self.llm = Llama(model_path=path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, logits_all=True, seed=seed, verbose=False)
        self.n_ctx, self.eos = n_ctx, self.llm.token_eos()

    def tokenize(self, text: str) -> list[int]:
        return self.llm.tokenize(text.encode("utf-8"), add_bos=True, special=True)

    def sample(self, prompt_ids: list[int], max_new: int) -> tuple[list[int], float]:
        """Temperature 1 from the model's own softmax. Returns (new token ids, seconds spent decoding)."""
        self.llm.reset()
        out, t0 = [], time.perf_counter()
        for tok in self.llm.generate(prompt_ids, temp=1.0, top_k=0, top_p=1.0, min_p=0.0, repeat_penalty=1.0, reset=True):
            if tok == self.eos or len(out) >= max_new or len(prompt_ids) + len(out) >= self.n_ctx - 1:
                break
            out.append(tok)
        return out, time.perf_counter() - t0

    def logits(self, ids: list[int]) -> np.ndarray:
        """[len(ids), V] float32; row j predicts ids[j + 1]."""
        self.llm.reset()
        self.llm.eval(ids)
        return np.array(self.llm.scores[:len(ids)], dtype=np.float32)


def run_format(name: str, sampler, ref, prompts: list[list[int]], k: int, max_new: int, eps: float, dump_path=None,
               categories: list[str] | None = None) -> dict:
    parts, positions, clusters, new_tokens, seconds, empty = [], [], [], 0, 0.0, 0
    dump = open(dump_path, "w") if dump_path else None
    for pi, p in enumerate(prompts):
        for _ in range(k):
            comp, secs = sampler.sample(p, max_new)
            new_tokens, seconds = new_tokens + len(comp), seconds + secs
            if not comp:
                empty += 1
                continue
            ids = p + comp
            rows = slice(len(p) - 1, len(ids) - 1)                       # rows that predict the completion tokens
            ps = position_stats(ref.logits(ids)[rows], sampler.logits(ids)[rows], np.array(comp))
            parts.append(ps)
            positions.append(np.arange(len(comp)))
            clusters.append(np.full(len(comp), pi))
            if dump:   # token ids and the quantized model's numbers, for a second reference (score_with_torch.py)
                dump.write(json.dumps({"format": name, "prompt_idx": pi, "prompt_len": len(p), "category": (categories[pi] if categories else None), "ids": ids,
                                       "lp_q": [round(float(x), 6) for x in ps["lp_q"]],
                                       "top1_q": [int(x) for x in ps["top1_q"]]}) + "\n")
    if dump:
        dump.close()
    keys = ("lp_ref", "lp_q", "kl", "agree", "top1_ref", "top1_q")
    per_pos = {k_: np.concatenate([x[k_] for x in parts]) for k_ in keys} if parts else None
    res = {"format": name, "rollouts": len(parts), "empty_rollouts": empty, "new_tokens": new_tokens,
           "decode_seconds": round(seconds, 2), "rollout_tokens_per_s": round(new_tokens / seconds, 2) if seconds else None}
    if per_pos:
        res.update(aggregate(per_pos, np.concatenate(positions), eps, np.concatenate(clusters)))
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", required=True, help="bf16 GGUF (the reference, scores every sampled token)")
    ap.add_argument("--quant", action="append", required=True, metavar="NAME=PATH", help="a sampler GGUF; repeat per bit-width")
    ap.add_argument("--prompts", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--n", type=int, default=48, help="prompts")
    ap.add_argument("--balanced", action="store_true", help="take the prompts round-robin across the file's categories, not the first n")
    ap.add_argument("--k", type=int, default=8, help="completions per prompt")
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--n-ctx", type=int, default=2048)
    ap.add_argument("--n-gpu-layers", type=int, default=-1)
    ap.add_argument("--ref-n-gpu-layers", type=int, default=None, help="for the bf16 reference only (default: --n-gpu-layers)")
    ap.add_argument("--eps", type=float, default=EPS)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--dump-dir", type=Path, default=None,
                    help="write <format>_rollouts.jsonl (token ids, the sampler's log-probabilities and top-1) for score_with_torch.py")
    a = ap.parse_args()
    formats = dict(q.split("=", 1) for q in a.quant)
    ref = LlamaEngine(a.ref, a.n_ctx, a.n_gpu_layers if a.ref_n_gpu_layers is None else a.ref_n_gpu_layers, a.seed)
    chosen = select_prompts(load_prompt_rows(a.prompts), a.n, a.balanced)
    tokenized = [(ref.tokenize(text), cat) for text, cat in chosen]
    tokenized = [(p, cat) for p, cat in tokenized if len(p) < a.n_ctx - a.max_new - 1]
    prompts = [p for p, _ in tokenized]
    categories: dict[str, int] = {}
    for _, cat in tokenized:
        categories[cat or "-"] = categories.get(cat or "-", 0) + 1
    results = []
    for i, (name, path) in enumerate(formats.items()):
        sampler = LlamaEngine(path, a.n_ctx, a.n_gpu_layers, a.seed + 1 + i)
        t0 = time.time()
        if a.dump_dir:
            a.dump_dir.mkdir(parents=True, exist_ok=True)
        results.append(run_format(name, sampler, ref, prompts, a.k, a.max_new, a.eps,
                                  a.dump_dir / f"{name}_rollouts.jsonl" if a.dump_dir else None, [c for _, c in tokenized]))
        print(f"{name}: {results[-1].get('rollout_tokens_per_s')} tok/s, outside [{1 - a.eps:.2f}, {1 + a.eps:.2f}] "
              f"{results[-1].get('outside')}, top-1 {results[-1].get('top1_agreement')}, {time.time() - t0:.0f}s", flush=True)
        del sampler
    a.out.write_text(json.dumps({"reference": Path(a.ref).name, "prompts": len(prompts), "prompt_selection": "balanced" if a.balanced else "first",
                                 "prompt_categories": categories, "k": a.k, "max_new": a.max_new,
                                 "eps": a.eps, "temperature": 1.0, "seed": a.seed, "formats": results}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
