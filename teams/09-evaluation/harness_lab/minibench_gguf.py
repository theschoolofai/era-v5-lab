"""Run the fixed mini-benchmark on one local GGUF using Team 5's input token IDs."""

import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np

from lm_eval_lab import TEAM, split_pair
from minibench_items import json_bytes
from minibench_lab import MiniBenchmark, atomic_write, score_items, scorer_parser, software_versions, summarize


class FixedTokensLM:
    def __init__(self, backend, artifacts, block_size):
        self.backend = backend
        self.art = artifacts
        self.block_size = block_size
        if self.backend.llm.n_vocab() != len(self.art.lengths) or self.backend.llm.token_bos() != self.art.bos_id:
            raise ValueError("GGUF vocabulary size or BOS disagrees with the pinned tokenizer")

    def sequence_logp(self, tokens, targets):
        self.backend._eval_reuse_prefix(tokens)
        scores = self.backend.llm.scores
        offset = len(tokens) - len(targets)
        losses = []
        for i in range(0, len(targets), 64):
            part = targets[i : i + 64]
            row = np.asarray(scores[offset + i : offset + i + len(part)], dtype=np.float64)
            logp = row[np.arange(len(part)), part] - np.logaddexp.reduce(row, axis=1)
            losses.append(float(logp.sum()))
        value = math.fsum(losses)
        if not math.isfinite(value):
            raise ValueError("Nonfinite GGUF log likelihood")
        return value

    def loglikelihood(self, requests):
        pairs = [split_pair(*request.args) for request in requests]
        texts = list(dict.fromkeys(t for prompt, continuation in pairs for t in (prompt, prompt + continuation)))
        ids = {t: e.ids for t, e in zip(texts, self.art.tokenizer.encode_batch(texts, add_special_tokens=False))}
        return self.loglikelihood_tokens((ids[c], ids[c + x][len(ids[c]):]) for c, x in pairs)

    def loglikelihood_tokens(self, pairs, *, allow_truncation=True):
        out = []
        for base, targets in pairs:
            if not len(targets):
                raise ValueError("A continuation produced no tokens")
            if not allow_truncation and len(base) + len(targets) > self.block_size:
                raise ValueError("context and continuation exceed the model context window")
            tokens = ([self.art.bos_id] + base + targets)[-(self.block_size + 1):]
            targets = tokens[-min(len(targets), len(tokens) - 1):]
            out.append((self.sequence_logp(tokens[:-1], targets), False))
        return out


def heldout_scores(lm, dataset):
    from week2.scoring import group_metrics

    by_slice = {}
    for (inputs, targets, lengths), name in zip(dataset.windows, dataset.window_slices, strict=True):
        nats, tokens, sizes = by_slice.setdefault(name, ([], [], []))
        nats.append(-lm.sequence_logp(inputs, targets))
        tokens.append(len(targets))
        sizes.append(sum(lengths))
    output = {}
    bpbs = {}
    for name, (nats, tokens, sizes) in sorted(by_slice.items()):
        raw_size = dataset.slice_raw_bytes[name]
        if sum(sizes) != getattr(dataset, "slice_encoded_bytes", dataset.slice_raw_bytes)[name]:
            raise ValueError(f"GGUF slice byte conservation failed for {name}")
        total = math.fsum(nats)
        bpbs[name] = total / math.log(2) / raw_size
        prefix = f"val/slices/{name}"
        output.update({f"{prefix}/bpb": bpbs[name], f"{prefix}/nll_nats": total,
                       f"{prefix}/scored_tokens": sum(tokens), f"{prefix}/utf8_bytes": raw_size})
    total = math.fsum(output[f"val/slices/{name}/nll_nats"] for name in bpbs)
    output.update(group_metrics(bpbs))
    output.update({"val/bpb": total / math.log(2) / dataset.raw_bytes, "val/nll_nats": total,
                   "val/utf8_bytes": dataset.raw_bytes, "val/scored_tokens": dataset.tokens})
    return output


def main():
    parser = scorer_parser()
    parser.add_argument("--gguf", type=Path, required=True)
    parser.add_argument("--gguf-sha256")
    parser.add_argument("--format", required=True, choices=("bf16", "Q8_0", "Q6_K", "Q5_K_M", "Q4_K_M"))
    parser.add_argument("--n-gpu-layers", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(TEAM.parent / "12-quantization" / "eval_mini"))
    from llamacpp_lm import LlamaCppLM

    start = time.perf_counter()
    suite = MiniBenchmark(args)
    manifest = json.loads(args.model_config.read_text(encoding="utf-8"))
    suite.check(manifest)
    with args.gguf.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if args.gguf_sha256 and digest != args.gguf_sha256:
        raise ValueError("GGUF checksum mismatch")
    block = int(suite.m["block_size"])
    backend = LlamaCppLM(str(args.gguf), n_ctx=block, n_gpu_layers=args.n_gpu_layers)
    try:
        lm = FixedTokensLM(backend, suite.art, block)
        heldout = heldout_scores(lm, suite.heldout_dataset())
        end_heldout = time.perf_counter()
        per_item = score_items(lm, suite.tasks)
        evidence = {
            **suite.evidence_identity(), "gguf_sha256": digest, "format": args.format,
            "backend": "llama-cpp-python", "hardware": platform.processor() or platform.machine(),
            "n_gpu_layers": args.n_gpu_layers, "software": software_versions(),
            "heldout": heldout, "tasks": {name: summarize(rows) for name, rows in per_item.items()}, "items": per_item,
            "timing_seconds": {"load_and_heldout": end_heldout - start, "tasks": time.perf_counter() - end_heldout},
        }
        atomic_write(args.out, json_bytes(evidence))
    finally:
        backend.llm.close()


if __name__ == "__main__":
    main()
