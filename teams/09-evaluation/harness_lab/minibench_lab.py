"""Score minibench_v1 through run_lab_ckpt.py or time a seeded, untrained model."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

import torch
import yaml

from lm_eval_lab import HERE, TEAM, LabLM, build_model, load_model_config, probe_loss, split_pair, text_bytes, week2
from minibench_items import item_identity, json_bytes, load_items, sha256

HELDOUT = TEAM.parent / "05-architecture" / "heldout_v1" / "data"
SUITE = HERE / "minibench_v1.yaml"
MILU_SPEC = TEAM / "harness_code_indic" / "eval_mini_v0_spec.json"
UNCLEARED = {"arc_easy_cloze", "arc_challenge_cloze", "hellaswag_cloze", "humaneval_gold", "mbpp_gold"}
# benchmarks_v1.md Decision 7 (TSAI on #357, 12 Nov) lets only ARC-Challenge, MMLU-Pro, Belebele and HellaSwag run as
# diagnostics on lab checkpoints. These three wait for TSAI's approval for that use.
AWAITING_APPROVAL = {"arc_easy_cloze", "humaneval_gold", "mbpp_gold"}
# TSAI on #909 (28 Nov): HellaSwag is "skip" for fingerprints, internal scoring is allowed, TSAI decides public tables.
INTERNAL_ONLY = {"hellaswag_cloze"}
ITEM_PINS = {
    "full": "01fe24d16955131b71f7511e6daba040a2087be677fe52663e8deb0c5766556e",
    "quick": "ec2a00275f444e5064cf640c633a3b30415c3069644dedaa06080bdaa37520a0",
}


def heldout_inputs(cfg, profile, root):
    """Check both Team 5 source files and select the pinned profile input."""
    text = text_bytes(root / "heldout_v1.jsonl")
    sources = text_bytes(root / "heldout_v1_sources.jsonl")
    if sha256(text) != cfg["text_sha256"] or sha256(sources) != cfg["sources_sha256"]:
        raise ValueError("Team 5 held-out file or source index checksum mismatch")
    counts = {}
    bytes_by_slice = {}
    text_lines, source_lines = [], []
    threshold = cfg.get(f"{profile}_bytes_per_slice", math.inf)
    quick_docs = {}
    for left, right in zip(text.splitlines(), sources.splitlines(), strict=True):
        doc, source = json.loads(left), json.loads(right)
        name = source["slice"]
        if doc["id"] != source["id"]:
            raise ValueError("Held-out file and source index disagree")
        if profile == "quick":
            quick_docs.setdefault(name, []).append((doc, source))
            continue
        if bytes_by_slice.get(name, 0) < threshold:
            text_lines.append(left)
            source_lines.append(right)
            counts[name] = counts.get(name, 0) + 1
            bytes_by_slice[name] = bytes_by_slice.get(name, 0) + len(doc["text"].encode("utf-8"))
    if profile == "quick":
        return quick_heldout_inputs(quick_docs, cfg)
    return b"\n".join(text_lines) + b"\n", b"\n".join(source_lines) + b"\n", counts


def quick_heldout_inputs(by_slice, cfg):
    """Pick distinct documents by hash order, then cap each at a UTF-8 boundary."""
    documents, sources, counts = [], [], {}
    per_slice = cfg["quick_documents_per_slice"]
    byte_cap = cfg["quick_max_bytes_per_document"]
    for name, pairs in sorted(by_slice.items()):
        selected = sorted(pairs, key=lambda pair: sha256(pair[0]["id"].encode("utf-8")))[:per_slice]
        if len(selected) != per_slice:
            raise ValueError(f"Too few held-out documents in {name}")
        counts[name] = len(selected)
        for doc, source in selected:
            # The original text is valid UTF-8. A sliced byte sequence can only
            # be incomplete at its end. Trim trailing whitespace from the prefix.
            prefix = doc["text"].encode("utf-8")[:byte_cap].decode("utf-8", errors="ignore").rstrip()
            if not prefix:
                raise ValueError(f"Empty held-out document prefix in {name}")
            documents.append(json_bytes(dict(doc, text=prefix)))
            sources.append(json_bytes(dict(source, original_text_sha256=source["text_sha256"],
                                          text_sha256=sha256(prefix.encode("utf-8")))))
    return b"".join(documents), b"".join(sources), counts


def score_items(lm, tasks):
    """Shared task semantics for any backend with lm-eval-style loglikelihood."""
    by_task = {}
    for name, items in tasks.items():
        # Reference code is a fixed continuation. Encode each part with the
        # verified byte table and concatenate IDs at the exact task boundary.
        # Joint BPE can merge across that boundary and lose completion bytes.
        is_code = len(items[0].choices) == 1
        pairs = [(item.prompt, choice) for item in items for choice in item.choices]
        if is_code:
            tokens = ((lm.art.encode(prompt), lm.art.encode(choice)) for prompt, choice in pairs)
            scores = iter(lm.loglikelihood_tokens(tokens, allow_truncation=False))
        else:
            scores = iter(lm.loglikelihood([SimpleNamespace(args=pair) for pair in pairs]))
        rows = []
        for item in items:
            choices = [next(scores) for _ in item.choices]
            sizes = [len((choice if is_code else split_pair(item.prompt, choice)[1]).encode("utf-8"))
                     for choice in item.choices]
            if not all(math.isfinite(score[0]) and size > 0 for score, size in zip(choices, sizes)):
                raise ValueError(f"Unscorable continuation in {name}")
            gold = choices[item.answer][0]
            row = {"id": item.identity, "gold_nll_nats": -gold, "utf8_bytes": sizes[item.answer]}
            if len(choices) > 1:
                prediction = max(range(len(choices)), key=lambda i: choices[i][0] / sizes[i])
                row["correct"] = prediction == item.answer
            rows.append(row)
        by_task[name] = rows
    return by_task


def task_notes(name, profile):
    """The labels every record of this task carries (the 12 Nov conditions for diagnostic runs)."""
    notes = ["Byte-normalized likelihood of choice text, zero shot"]
    if name in UNCLEARED:
        notes.append("diagnostic, not cleared for contamination")
    if name in AWAITING_APPROVAL:
        notes.append("awaiting TSAI approval for lab checkpoints")
    if name in INTERNAL_ONLY:
        notes.append("internal only, TSAI decides public tables")
    if profile == "smoke":
        notes.append("Smoke profile: execution evidence only")
    return notes


def software_versions():
    versions = {"python": platform.python_version(), "torch": torch.__version__, "cuda": torch.version.cuda}
    try:
        import llama_cpp

        versions["llama_cpp_python"] = llama_cpp.__version__
    except ImportError:
        pass
    return versions


def summarize(rows):
    n = len(rows)
    nats = math.fsum(r["gold_nll_nats"] for r in rows)
    size = sum(r["utf8_bytes"] for r in rows)
    bpb = nats / math.log(2) / size
    residuals = [r["gold_nll_nats"] / math.log(2) - bpb * r["utf8_bytes"] for r in rows]
    result = {"items": n, "gold_bpb": bpb, "utf8_bytes": size,
              "gold_bpb_stderr": statistics.stdev(residuals) * math.sqrt(n) / size if n > 1 else None}
    if "correct" in rows[0]:
        accuracy = sum(r["correct"] for r in rows) / n
        result["accuracy_points"] = 100 * accuracy
        result["stderr_points"] = 100 * math.sqrt(accuracy * (1 - accuracy) / (n - 1)) if n > 1 else None
    return result


def atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        tmp = Path(stream.name)
        stream.write(raw)
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


class MiniBenchmark:
    name = "minibench_v1"

    def __init__(self, args):
        start = time.perf_counter()
        self.a = args
        suite_bytes = text_bytes(SUITE)
        cfg = yaml.safe_load(suite_bytes)
        self.revision = cfg["revision"]
        self.suite_sha = sha256(suite_bytes)
        self.script_sha = sha256(text_bytes(Path(__file__)))
        self.seed = cfg["arithmetic"]["seed"]
        self.m = load_model_config(args.model_config, args.runtime, args.resolution)
        Artifacts, _ = week2()
        self.art = Artifacts(args.tokenizer, args.byte_table, expected_tokenizer_sha=args.tokenizer_sha256,
                             expected_vocab=self.m["vocab_size"])
        if self.art.pos_dim != self.m["ke_max_pos"]:
            raise ValueError("Tokenizer byte table dimensions disagree with the checkpoint model")
        self.tasks = load_items(cfg, args.profile, args.cache, MILU_SPEC)
        self.items_sha = item_identity(self.tasks)
        if args.profile in ITEM_PINS and self.items_sha != ITEM_PINS[args.profile]:
            raise ValueError(f"Rendered item checksum mismatch for {args.profile}")
        self.source_root = args.heldout_root
        self.heldout_text, self.heldout_sources, self.doc_counts = heldout_inputs(
            cfg["heldout"], args.profile, self.source_root
        )
        self.setup_seconds = time.perf_counter() - start

    def check(self, manifest):
        pins = manifest.get("artifacts") or {}
        recorded_tokenizer = pins.get("tokenizer_sha256") or (manifest.get("env") or {}).get("tokenizer_sha")
        if recorded_tokenizer not in (None, "unknown", self.a.tokenizer_sha256):
            raise ValueError("Checkpoint manifest tokenizer checksum mismatch")
        table_hash = pins.get("table_file_sha256")
        if table_hash and sha256(self.a.byte_table.read_bytes()) != table_hash:
            raise ValueError("Checkpoint manifest byte table checksum mismatch")
        manifest_model = (manifest.get("config") or {}).get("model")
        if manifest_model is not None and self.m != manifest_model:
            raise ValueError("Checkpoint manifest and scorer model config disagree")

    def factory(self):
        return build_model(self.m, self.art)

    def probe(self, model):
        return probe_loss(model)

    def heldout_dataset(self):
        from week2.data import DocumentWindows

        if self.a.profile == "full":
            return DocumentWindows(self.source_root / "heldout_v1.jsonl", self.art, self.m["block_size"],
                                   require_ids=True, sources_path=self.source_root / "heldout_v1_sources.jsonl")
        (HERE / "out").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="minibench-", dir=HERE / "out") as temp:
            text, sources = Path(temp) / "text.jsonl", Path(temp) / "sources.jsonl"
            text.write_bytes(self.heldout_text)
            sources.write_bytes(self.heldout_sources)
            return DocumentWindows(text, self.art, self.m["block_size"], require_ids=True, sources_path=sources)

    def score(self, model, device):
        from week2.evaluation import evaluate

        start = time.perf_counter()
        dev = torch.device(device)
        gpu = dev.type == "cuda"
        if gpu:
            torch.cuda.reset_peak_memory_stats(dev)
        bf16 = gpu and torch.cuda.is_bf16_supported(including_emulation=False)
        model.to(dev).eval()
        hardware = torch.cuda.get_device_name(dev) if gpu else platform.processor() or platform.machine()
        torch.manual_seed(self.seed)
        lm = LabLM(model, self.art, self.m["block_size"], dev, bf16, self.a.max_batch_tokens)
        heldout = evaluate(model, self.heldout_dataset(), 1, dev, lm.autocast, max_batch_tokens=self.a.max_batch_tokens)
        t_heldout = time.perf_counter()
        per_item = score_items(lm, self.tasks)
        summaries = {name: summarize(rows) for name, rows in per_item.items()}
        dtype, fmt = ("bfloat16", "bf16") if bf16 else ("float32", "fp32")
        self.evidence = {
            **self.evidence_identity(), "heldout": heldout, "tasks": summaries, "items": per_item,
            "format": fmt, "dtype": dtype, "hardware": hardware, "device": dev.type,
            "timing_seconds": {"setup": self.setup_seconds, "heldout": t_heldout - start,
                               "tasks": time.perf_counter() - t_heldout},
            "cpu_threads": torch.get_num_threads(), "peak_gpu_bytes": torch.cuda.max_memory_allocated(dev) if gpu else None,
            "software": software_versions(),
            # Texts whose tokenizer ids do not rebuild the raw UTF-8. In this suite they are MILU Bengali (and one
            # Hindi) texts that p1536's normalizer rewrites (NFC, then nukta recomposition). Same ids as the watcher.
            "encode_fallbacks": lm.encode_fallbacks,
        }
        item_set = sha256(json_bytes([self.suite_sha, self.items_sha]))
        records = []
        for name, result in summaries.items():
            if "accuracy_points" not in result:
                continue
            notes = task_notes(name, self.a.profile)
            records.append({
                "task": name, "metric": "acc_norm", "filter": "none", "primary": True,
                "value": round(result["accuracy_points"], 2),
                "stderr": None if result["stderr_points"] is None else round(result["stderr_points"], 2),
                "n_items": result["items"], "item_set": f"spec:{item_set}", "profile": f"{self.name}/{self.a.profile}",
                "num_fewshot": 0, "decoding": "loglikelihood", "format": fmt, "dtype": dtype,
                "hardware": hardware, "harness": {"name": self.name, "version": str(self.revision), "script_sha256": self.script_sha},
                "notes": notes,
            })
        return records

    def evidence_identity(self):
        return {
            "schema_version": "minibench_cont_v1", "suite": self.name, "suite_revision": self.revision,
            "suite_sha256": self.suite_sha,
            "profile": self.a.profile, "items_sha256": self.items_sha, "tokenizer_sha256": self.a.tokenizer_sha256,
            "heldout_sha256": sha256(self.heldout_text), "heldout_sources_sha256": sha256(self.heldout_sources),
            "heldout_documents": self.doc_counts,
            # Labels travel with the evidence, so every copy of a score (dashboard rows, gap reports) can keep them.
            "diagnostic_tasks": sorted(UNCLEARED), "awaiting_approval_tasks": sorted(AWAITING_APPROVAL),
            "internal_only_tasks": sorted(INTERNAL_ONLY),
        }

    def write_result(self, path, raw, facts):
        self.evidence.update(model_revision=facts["model_revision"], checkpoint=facts["checkpoint"])
        self.evidence["result_sha256"] = sha256(raw)
        atomic_write(path.with_suffix(".continuous.json"), json_bytes(self.evidence))
        atomic_write(path, raw)


def scorer_parser():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--model-config", type=Path, required=True)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--resolution", type=Path)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--tokenizer-sha256", required=True)
    parser.add_argument("--byte-table", type=Path, required=True)
    parser.add_argument("--profile", choices=("full", "quick", "smoke"), required=True)
    parser.add_argument("--cache", type=Path, action="append", required=True,
                        help="staged Hugging Face hub cache, repeatable")
    parser.add_argument("--heldout-root", type=Path, default=HELDOUT)
    parser.add_argument("--max-batch-tokens", type=int, default=4096)
    return parser


def team5(argv):
    return MiniBenchmark(scorer_parser().parse_args(argv[1:] if argv[:1] == ["--"] else argv))


def main():
    parser = scorer_parser()
    model_source = parser.add_mutually_exclusive_group(required=True)
    model_source.add_argument("--init-only", action="store_true",
                              help="build an untrained seed replay for timing, never a checkpoint score")
    model_source.add_argument("--weights-safetensors", type=Path,
                              help="score a standalone weights export with the run manifest")
    parser.add_argument("--weights-sha256", help="expected SHA-256 of a standalone weights export")
    parser.add_argument("--step", type=int, help="committed step of the standalone export")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA is unavailable in this Torch environment")
    if args.weights_safetensors and (not args.weights_sha256 or args.step is None or args.step < 0):
        parser.error("--weights-safetensors requires --weights-sha256 and a nonnegative --step")
    start = time.perf_counter()
    manifest = json.loads(args.model_config.read_text(encoding="utf-8"))
    scorer = MiniBenchmark(args)
    scorer.check(manifest)
    if args.weights_safetensors:
        from safetensors.torch import load_file

        with args.weights_safetensors.open("rb") as stream:
            revision = hashlib.file_digest(stream, "sha256").hexdigest()
        if revision != args.weights_sha256:
            raise ValueError("Standalone weights checksum mismatch")
        model = scorer.factory()
        model.load_state_dict(load_file(str(args.weights_safetensors)), strict=True)
        source = {"mode": "standalone_export", "model_revision": revision, "step": args.step,
                  "manifest_sha256": sha256(args.model_config.read_bytes())}
    else:
        seed = manifest["config"]["run"]["seed"]
        _, LanguageModel = week2()
        torch.manual_seed(seed)
        model = LanguageModel(scorer.m, scorer.art.bytes, scorer.art.lengths)
        source = {"mode": "seeded_untrained_model", "initialization_seed": seed}
    scorer.score(model, args.device)
    evidence = scorer.evidence
    evidence.update(source, total_seconds=time.perf_counter() - start)
    atomic_write(args.out, json_bytes(evidence))
    print(f"{args.profile} {args.device}: {evidence['total_seconds']:.1f} s, "
          f"{evidence['heldout']['val/scored_tokens']} held-out tokens, {sum(len(x) for x in scorer.tasks.values())} items")


if __name__ == "__main__":
    main()
