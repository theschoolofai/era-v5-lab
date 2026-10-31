"""lm-evaluation-harness model class that runs a GGUF file in-process with llama-cpp-python.

Why this exists: lm_eval scores multiple-choice tasks by the log-probability of each answer. Neither server
route gives correct numbers for GGUF files (checked 28 Oct, llama.cpp b11669, llama-cpp-python 0.3.36):
  - llama-server ignores `echo=True` and returns logprobs only for generated tokens, so lm_eval's
    local-completions / gguf backends cannot score multiple choice at all;
  - llama-cpp-python's server returns prompt logprobs SHIFTED BY ONE position (log p(" Paris" | "The capital
    of France is") comes back as -8.58 instead of -0.49), which lm_eval would sum without any error.
Here the model runs in-process with every position's logits kept, and the log-probability of token i is read
from the distribution at position i-1. Checked: log p(" Paris" | ...) = -0.49, as greedy generation reports.

Use: `from llamacpp_lm import LlamaCppLM; lm = LlamaCppLM("model.gguf")`, then pass `model=lm` to
`lm_eval.simple_evaluate`. Requests are scored one at a time; a cache of the previous sequence's tokens means
the shared question of a multiple-choice item is evaluated once, not once per answer option.
"""
from __future__ import annotations

import numpy as np
from llama_cpp import Llama
from lm_eval.api.model import LM
from tqdm import tqdm


class LlamaCppLM(LM):
    def __init__(self, model_path: str, n_ctx: int = 2048, n_gpu_layers: int = -1, max_gen_toks: int = 256,
                 seed: int = 42, n_batch: int = 512):
        super().__init__()
        self.llm = Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, logits_all=True,
                         seed=seed, n_batch=n_batch, verbose=False)
        self.n_ctx, self.max_gen_toks = n_ctx, max_gen_toks
        meta = self.llm.metadata
        self.add_bos = meta.get("tokenizer.ggml.add_bos_token", "false") == "true"
        bos, eos = self.llm.token_bos(), self.llm.token_eos()
        # lm_eval's HF model uses this token as the context of an empty-context request
        self.prefix_token = bos if self.add_bos and bos >= 0 else eos

    # ------------------------------------------------------------------ helpers
    def _tok(self, text: str, bos: bool) -> list[int]:
        return self.llm.tokenize(text.encode("utf-8"), add_bos=bos, special=False)

    def _encode_pair(self, context: str, continuation: str) -> tuple[list[int], list[int]]:
        """Same split as lm_eval's HFLM: trailing spaces of the context move to the continuation, then the
        continuation tokens are the tail of the jointly tokenized string (so merges across the boundary hold)."""
        n_spaces = len(context) - len(context.rstrip())
        if n_spaces:
            continuation, context = context[-n_spaces:] + continuation, context[:-n_spaces]
        if not context:
            return [self.prefix_token], self._tok(continuation, bos=False)
        whole = self._tok(context + continuation, bos=self.add_bos)
        ctx = self._tok(context, bos=self.add_bos)
        return ctx, whole[len(ctx):]

    def _eval_reuse_prefix(self, tokens: list[int]) -> None:
        """Evaluate `tokens`, keeping the KV cache and logit rows of the longest prefix shared with the previous
        sequence. Row j of llm.scores depends only on tokens[:j+1], so kept rows stay valid."""
        llm, keep = self.llm, 0
        for a, b in zip(llm.input_ids[: llm.n_tokens], tokens):
            if a != b:
                break
            keep += 1
        keep = min(keep, len(tokens) - 1)  # always evaluate at least the last token
        llm.n_tokens = keep                # eval() drops the KV cache from n_tokens onward
        llm.eval(tokens[keep:])

    def _score(self, context_tokens: list[int], continuation_tokens: list[int]) -> tuple[float, bool]:
        tokens = (context_tokens + continuation_tokens)[-self.n_ctx:]   # left-truncate, as HFLM does
        n_cont = len(continuation_tokens)
        self._eval_reuse_prefix(tokens)
        start = len(tokens) - n_cont
        rows = np.asarray(self.llm.scores[start - 1: len(tokens) - 1], dtype=np.float64)  # row i-1 predicts token i
        logsm = rows - np.logaddexp.reduce(rows, axis=1, keepdims=True)
        targets = np.asarray(tokens[start:])
        logprob = float(logsm[np.arange(n_cont), targets].sum())
        greedy = bool((logsm.argmax(axis=1) == targets).all())
        return logprob, greedy

    # ------------------------------------------------------------------ lm_eval interface
    def loglikelihood(self, requests, disable_tqdm: bool = False):
        pairs = [self._encode_pair(*req.args) for req in requests]
        # score requests that share a question back to back, so the prefix cache is used; return in input order
        order = sorted(range(len(pairs)), key=lambda i: pairs[i][0])
        out = [None] * len(pairs)
        for i in tqdm(order, disable=disable_tqdm, desc="loglikelihood"):
            out[i] = self._score(*pairs[i])
        return out

    def loglikelihood_rolling(self, requests, disable_tqdm: bool = False):
        raise NotImplementedError("not needed by the eval_mini profiles (perplexity is measured in perplexity/)")

    def generate_until(self, requests, disable_tqdm: bool = False):
        out = []
        for req in tqdm(requests, disable=disable_tqdm, desc="generate_until"):
            context, gen_kwargs = req.args
            gen_kwargs = dict(gen_kwargs)
            until = gen_kwargs.pop("until", None) or []
            until = [until] if isinstance(until, str) else list(until)
            max_new = int(gen_kwargs.pop("max_gen_toks", self.max_gen_toks))
            if gen_kwargs.get("do_sample") or float(gen_kwargs.get("temperature", 0.0) or 0.0) > 0:
                raise ValueError(f"only greedy generation is supported, got {gen_kwargs}")
            prompt = self._tok(context, bos=self.add_bos)[-(self.n_ctx - max_new):]
            self.llm.reset()  # generation manages its own cache; do not mix it with the scoring cache
            res = self.llm.create_completion(prompt=prompt, max_tokens=max_new, temperature=0.0, top_k=1,
                                             stop=until or None)
            out.append(res["choices"][0]["text"])
        self.llm.reset()
        return out
