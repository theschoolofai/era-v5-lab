#!/usr/bin/env python3
"""Stage 1 with vLLM as the sampler: sample from a vLLM model (fp16/bf16 baseline or W4A16 GPTQ) and dump what Stage 2 needs.

    python quant_rollout_vllm.py --model-dir <bf16 or W4A16 folder> --name vllm_W4A16 --dtype half \\
        --prompts fixed_100.jsonl --balanced --n 50 --k 8 --max-new 256 --out vllm_W4A16.json --dump-dir dump

Same job as quant_rollout_mismatch.py (llama.cpp), same dump format, so `score_with_torch.py` scores either: per rollout
the token ids, the sampler's own log-probability of every sampled token (vLLM's raw log-probabilities, before any
sampling transform; at temperature 1 with top-k, top-p and min-p off they are the model's own softmax) and its top-1
token, plus the prompt index and category. The PyTorch bf16 model of Stage 2 is the reference.

What differs from the llama.cpp stage, and is written into the output:
  speed   vLLM decodes all prompts and all k samples at once (continuous batching), so tokens/s is a batched
          throughput, NOT the single-stream decode speed of the llama.cpp rows. Compare it only with the vLLM baseline.
  dtype   a T4 has no bf16 compute, so vLLM runs fp16 there (weights stay as stored); on an L4 or A100 use bfloat16.
          The PyTorch reference is bf16, so on a T4 the baseline row includes the fp16-against-bf16 difference.
Aggregate numbers and token ids only: no prompt or completion text is written.
"""
from __future__ import annotations

import argparse, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import quant_rollout_mismatch as qrm  # noqa: E402  (numpy only)


def rollout_from_output(out, eos_id: int | None) -> tuple[list[int], list[float], list[int]]:
    """One vLLM CompletionOutput -> (completion token ids, sampler log-probabilities, sampler top-1 ids).
    The EOS token that ended a completion is dropped, as the llama.cpp stage does; a completion cut at max_tokens keeps all."""
    ids = [int(t) for t in out.token_ids]
    if out.logprobs is None or len(out.logprobs) != len(ids):
        raise ValueError("vLLM returned no log-probabilities for the completion: SamplingParams needs logprobs=1")
    lp_q, top1 = [], []
    for tok, entries in zip(ids, out.logprobs):
        lp_q.append(float(entries[tok].logprob))
        ranked = [(t, e) for t, e in entries.items() if getattr(e, "rank", None) is not None]
        top1.append(int(min(ranked, key=lambda kv: kv[1].rank)[0]) if ranked else int(max(entries, key=lambda t: entries[t].logprob)))
    if ids and eos_id is not None and out.finish_reason == "stop" and ids[-1] == eos_id:
        ids, lp_q, top1 = ids[:-1], lp_q[:-1], top1[:-1]
    return ids, lp_q, top1


def sample_format(llm, name: str, prompts: list[list[int]], categories: list[str], k: int, max_new: int, seed: int,
                  eos_id: int | None, make_params, dump_path: Path | None = None) -> dict:
    """Sample k completions for every prompt in one batched call, time it, and write the dump. Returns the result row."""
    params = make_params(k=k, max_new=max_new, seed=seed)
    t0 = time.perf_counter()
    requests = llm.generate([{"prompt_token_ids": p} for p in prompts], params)
    seconds = time.perf_counter() - t0
    dump = open(dump_path, "w") if dump_path else None
    new_tokens, rollouts, empty, reasons = 0, 0, 0, {}
    for pi, (p, req) in enumerate(zip(prompts, requests)):
        for out in req.outputs:
            reasons[out.finish_reason] = reasons.get(out.finish_reason, 0) + 1
            comp, lp_q, top1 = rollout_from_output(out, eos_id)
            if not comp:
                empty += 1
                continue
            rollouts += 1
            new_tokens += len(comp)
            if dump:
                dump.write(json.dumps({"format": name, "prompt_idx": pi, "prompt_len": len(p), "category": categories[pi],
                                       "ids": p + comp, "lp_q": [round(x, 6) for x in lp_q], "top1_q": top1}) + "\n")
    if dump:
        dump.close()
    return {"format": name, "rollouts": rollouts, "empty_rollouts": empty, "new_tokens": new_tokens, "decode_seconds": round(seconds, 2),
            "rollout_tokens_per_s": round(new_tokens / seconds, 2) if seconds else None, "finish_reasons": reasons,
            "speed_is": "vLLM batched throughput (all prompts and samples at once), not single-stream decode"}


def vllm_params(k: int, max_new: int, seed: int):
    from vllm import SamplingParams
    return SamplingParams(n=k, temperature=1.0, top_p=1.0, top_k=-1, min_p=0.0, max_tokens=max_new, logprobs=1, seed=seed)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model-dir", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--dtype", default="half", help="half on a T4 (no bf16 compute), bfloat16 on an L4 or A100")
    ap.add_argument("--prompts", required=True, type=Path); ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--n", type=int, default=50); ap.add_argument("--k", type=int, default=8); ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--balanced", action="store_true"); ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--eps", type=float, default=qrm.EPS)
    ap.add_argument("--max-model-len", type=int, default=2048); ap.add_argument("--gpu-memory-utilization", type=float, default=0.80)
    ap.add_argument("--tp", type=int, default=1); ap.add_argument("--dump-dir", type=Path, default=None)
    a = ap.parse_args()
    import vllm
    from vllm import LLM
    llm = LLM(model=a.model_dir, dtype=a.dtype, max_model_len=a.max_model_len, seed=a.seed, tensor_parallel_size=a.tp,
              gpu_memory_utilization=a.gpu_memory_utilization)
    tok = llm.get_tokenizer()
    chosen = qrm.select_prompts(qrm.load_prompt_rows(a.prompts), a.n, a.balanced)
    tokenized = [(tok(text)["input_ids"], cat) for text, cat in chosen]
    tokenized = [(p, c) for p, c in tokenized if len(p) < a.max_model_len - a.max_new - 1]
    prompts, cats = [p for p, _ in tokenized], [c for _, c in tokenized]
    categories: dict[str, int] = {}
    for c in cats:
        categories[c or "-"] = categories.get(c or "-", 0) + 1
    if a.dump_dir:
        a.dump_dir.mkdir(parents=True, exist_ok=True)
    row = sample_format(llm, a.name, prompts, cats, a.k, a.max_new, a.seed, tok.eos_token_id, vllm_params,
                        a.dump_dir / f"{a.name}_rollouts.jsonl" if a.dump_dir else None)
    row.update(engine="vllm", vllm=vllm.__version__, dtype=a.dtype)
    a.out.write_text(json.dumps({"reference": Path(a.model_dir).name, "prompts": len(prompts), "prompt_selection": "balanced" if a.balanced else "first",
                                 "prompt_categories": categories, "k": a.k, "max_new": a.max_new, "eps": a.eps, "temperature": 1.0,
                                 "seed": a.seed, "formats": [row]}, indent=1))
    print(f"{a.name}: {row['rollout_tokens_per_s']} tok/s (batched), {row['rollouts']} rollouts, {row['new_tokens']} tokens, finish {row['finish_reasons']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
