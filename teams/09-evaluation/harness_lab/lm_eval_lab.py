"""lm-evaluation-harness model class for a Team 5 lab checkpoint, and the task-group runner of eval_lab_v1.yaml.

LabLM follows lm_eval's HF model (HFLM) for log-likelihood requests, as teams/12-quantization/eval_mini/llamacpp_lm.py
does for GGUF files: trailing spaces of the context move to the continuation, the continuation tokens are the tail of
the jointly tokenized string, the sequence is left-truncated to the model's context, and the score is the summed
log-probability of the continuation tokens. Like Team 5's training windows (week2/data.py), every sequence starts with
the BOS token <|begin_of_text|>.

Scoring is batched: requests are sorted by length, right-padded with the PAD token and passed with the `valid` mask
(attention is causal and the MoE skips invalid rows, so padding does not change a real token). The output head runs
only on the continuation positions, so a 131,072-way softmax is never built for the whole batch.
"""
from __future__ import annotations

from contextlib import nullcontext

import torch
from lm_eval.api.model import LM
from tqdm import tqdm


class LabLM(LM):
    def __init__(self, model, artifacts, block_size: int, device, bf16: bool, max_batch_tokens: int = 16384):
        super().__init__()
        self.model, self.art, self.block = model, artifacts, int(block_size)
        self._device = device              # lm_eval's LM exposes it as the read-only property `device`
        self.autocast = (lambda: torch.autocast(device_type="cuda", dtype=torch.bfloat16)) if bf16 else nullcontext
        self.bos, self.pad = artifacts.bos_id, artifacts.pad_id
        self.max_batch_tokens = int(max_batch_tokens)
        self.encode_fallbacks = 0      # texts that Artifacts.encode refused (no exact UTF-8 round trip); counted, not logged
        self.requests_scored = 0

    # ------------------------------------------------------------------ tokenization
    def _encode(self, text: str) -> list[int]:
        if not text:
            return []
        try:
            return self.art.encode(text)      # Team 5's strict encoder: ids must rebuild the exact UTF-8 bytes
        except ValueError:
            self.encode_fallbacks += 1
            return self.art.tokenizer.encode(text, add_special_tokens=False).ids

    def _pair(self, context: str, continuation: str) -> tuple[list[int], list[int]]:
        n_spaces = len(context) - len(context.rstrip())
        if n_spaces:
            continuation, context = context[-n_spaces:] + continuation, context[:-n_spaces]
        ctx = self._encode(context)
        whole = self._encode(context + continuation)
        cont = whole[len(ctx):]
        if not cont:
            raise ValueError("a continuation produced no tokens")
        return [self.bos] + ctx, cont

    # ------------------------------------------------------------------ scoring
    def _score_batch(self, batch, seqs, out):
        width = max(len(seqs[i][0]) for i in batch)
        ids = torch.full((len(batch), width), self.pad, dtype=torch.long)
        valid = torch.zeros((len(batch), width), dtype=torch.bool)
        for j, i in enumerate(batch):
            x = seqs[i][0]
            ids[j, : len(x)] = torch.tensor(x, dtype=torch.long)
            valid[j, : len(x)] = True
        ids, valid = ids.to(self._device), valid.to(self._device)
        with torch.no_grad(), self.autocast():
            hidden = self.model.hidden(ids, valid)
            for j, i in enumerate(batch):
                x, targets = seqs[i]
                end, n = len(x), len(targets)
                logits = self.model.head(hidden[j, end - n: end]).float()   # position p predicts token p + 1
                logp = torch.log_softmax(logits, dim=-1)
                t = torch.tensor(targets, dtype=torch.long, device=self._device)
                out[i] = (float(logp.gather(1, t[:, None]).sum().item()), bool((logp.argmax(-1) == t).all().item()))

    def loglikelihood(self, requests, disable_tqdm: bool = False):
        seqs = []
        for req in requests:
            ctx, cont = self._pair(*req.args)
            toks = (ctx + cont)[-(self.block + 1):]                          # left-truncate, as HFLM does
            n_cont = min(len(cont), len(toks) - 1)
            seqs.append((toks[:-1], toks[-n_cont:]))                          # inputs, continuation targets
        order = sorted(range(len(seqs)), key=lambda i: -len(seqs[i][0]))
        out, batch = [None] * len(seqs), []
        for i in tqdm(order, disable=disable_tqdm, desc="loglikelihood"):
            if batch and (len(batch) + 1) * len(seqs[batch[0]][0]) > self.max_batch_tokens:
                self._score_batch(batch, seqs, out)
                batch = []
            batch.append(i)
        if batch:
            self._score_batch(batch, seqs, out)
        self.requests_scored += len(seqs)
        return out

    def loglikelihood_rolling(self, requests, disable_tqdm: bool = False):
        raise NotImplementedError("eval_lab_v1 has no perplexity tasks")

    def generate_until(self, requests, disable_tqdm: bool = False):
        raise NotImplementedError("eval_lab_v1 scores log-likelihood tasks only (no generation)")


def _n_items(res, task):
    ns = res.get("n-samples", {})
    if task in ns:
        return {"effective": ns[task]["effective"], "original": ns[task]["original"]}
    # A group (mmlu): this call evaluated only that group, so its leaf tasks are all the n-samples entries.
    return {"effective": sum(v["effective"] for v in ns.values()), "original": sum(v["original"] for v in ns.values())}


_TASK_MANAGERS = {}


def task_manager(tasks_dir):
    """One lm-eval TaskManager per process: building its index opens every task YAML (about 14,000 files in lm-eval
    0.4.13), so it is built once and shared by every group and every run."""
    key = str(tasks_dir)
    if key not in _TASK_MANAGERS:
        from lm_eval.tasks import TaskManager

        print("  indexing lm-eval tasks (once per process)", flush=True)
        _TASK_MANAGERS[key] = TaskManager(include_path=key)
    return _TASK_MANAGERS[key]


def evaluate_group(lm, group, spec, tasks_dir, limit=None):
    """Yield (task entry, {"results", "n"}) for every task of one config group. Never logs samples or prompts."""
    import lm_eval

    tm = task_manager(tasks_dir)
    s = group["seed"]
    common = dict(model=lm, task_manager=tm, log_samples=False, write_out=False, apply_chat_template=False,
                  fewshot_as_multiturn=False, random_seed=s["random"], numpy_random_seed=s["numpy"],
                  torch_random_seed=s["torch"], fewshot_random_seed=s["fewshot"])
    if group["items"] == "limit":
        # Same as harness/run_eval_mini.py: one call per task, lm-eval's first-N items, the task's own 0-shot config.
        for e in group["tasks"]:
            n = min(limit, e["limit"]) if limit else e["limit"]
            print(f"  scoring {e['task']} (limit {n})", flush=True)
            res = lm_eval.simple_evaluate(tasks=[e["task"]], num_fewshot=e["num_fewshot"] or None, limit=n, **common)
            yield e, {"results": res["results"], "n": {e["task"]: _n_items(res, e["task"])}}
    else:
        # Same as harness_code_indic/run_lm_eval.py with the eval-mini spec: the spec's doc ids, grouped by shot count.
        by_shot = {}
        for e in group["tasks"]:
            by_shot.setdefault(e["num_fewshot"], []).append(e)
        for shot, entries in by_shot.items():
            names = [e["task"] for e in entries]
            print(f"  scoring {', '.join(names)} ({shot}-shot, spec items)", flush=True)
            samples = {t: spec["tasks"][t]["doc_ids"][:limit] if limit else spec["tasks"][t]["doc_ids"] for t in names}
            res = lm_eval.simple_evaluate(tasks=names, num_fewshot=shot, samples=samples, **common)
            for e in entries:
                yield e, {"results": res["results"], "n": {e["task"]: _n_items(res, e["task"])}}
