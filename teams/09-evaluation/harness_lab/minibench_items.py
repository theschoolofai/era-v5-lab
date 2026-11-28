"""Build the mini-benchmark in memory from exact, locally staged snapshots."""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass
from itertools import islice
from pathlib import Path


@dataclass(frozen=True)
class Item:
    identity: str
    prompt: str
    choices: tuple[str, ...]
    answer: int


def json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def snapshot_paths(cache_roots, pin, pattern):
    relative = Path("datasets--" + pin["repo"].replace("/", "--")) / "snapshots" / pin["revision"]
    for root in cache_roots:
        paths = sorted((root / relative).glob(pattern))
        if paths:
            return paths
    raise FileNotFoundError(f"Stage {pin['repo']} at {pin['revision']} in the eval cache ({pattern})")


def parquet_rows(paths):
    from pyarrow.parquet import ParquetFile

    for path in paths:
        for batch in ParquetFile(path).iter_batches(batch_size=256):
            yield from batch.to_pylist()


def take_rows(paths, indices):
    by_index = {}
    remaining = set(indices)
    for index, row in enumerate(parquet_rows(paths)):
        if index in remaining:
            by_index[index] = row
            remaining.remove(index)
            if not remaining:
                break
    if remaining:
        raise ValueError(f"Missing {len(remaining)} pinned benchmark row(s)")
    return [by_index[index] for index in indices]


def arithmetic_items(kind, count, seed):
    # One independent stream per task. Every quick item has the same identity and
    # prompt in full, regardless of the counts or order of other tasks.
    rng = random.Random(f"{seed}/{kind}")
    seen = set()
    items = []
    digits = str.maketrans("0123456789", "०१२३४५६७८९")
    while len(items) < count:
        a, b = rng.randrange(10, 100), rng.randrange(10, 100)
        operator, answer = "+", a + b
        valid_low, valid_high = a + 10, a + 99
        stride = rng.randrange(1, 5)
        if kind == "sub2":
            a, b = max(a, b), min(a, b)
            operator, answer = "-", a - b
            valid_low, valid_high = 0, a - 10
        elif kind == "add3":
            a, b = rng.randrange(100, 1000), rng.randrange(100, 1000)
            answer = a + b
            valid_low, valid_high = a + 100, a + 999
        elif kind == "mul2x1":
            b = rng.randrange(2, 10)
            operator, answer = "×", a * b
            # Every candidate can be produced by multiplying a two-digit
            # number by b, so divisibility alone cannot identify the answer.
            valid_low, valid_high = 10 * b, 99 * b
            stride *= b
        # Accept an answer only if the same spacing can put it in any rank
        # without crossing a digit boundary.
        width = len(str(answer))
        low = max(valid_low, 0 if width == 1 else 10 ** (width - 1))
        high = min(valid_high, 10 ** width - 1)
        operands = (a, b) if kind == "sub2" else tuple(sorted((a, b)))
        if operands in seen or answer - 3 * stride < low or answer + 3 * stride > high:
            continue
        seen.add(operands)
        # Balance the gold's display position and numerical rank independently.
        # Both profiles use prefixes of the same stream.
        if len(items) % 4 == 0:
            positions = rng.sample(range(4), 4)
            ranks = rng.sample(range(4), 4)
        answer_index = positions[len(items) % 4]
        rank = ranks[len(items) % 4]
        distractors = [answer + (index - rank) * stride for index in range(4) if index != rank]
        rng.shuffle(distractors)
        distractors.insert(answer_index, answer)
        prompt = f"{a} {operator} {b} ="
        choices = tuple(f" {option}" for option in distractors)
        if kind == "add2_deva":
            prompt = prompt.translate(digits)
            choices = tuple(choice.translate(digits) for choice in choices)
        items.append(Item(str(len(items)), prompt, choices, answer_index))
    return items


def question(identity, text, options, answer):
    return Item(identity, f"Question: {text.strip()}\nAnswer:", tuple(" " + x.strip() for x in options), answer)


def clean_hellaswag(text):
    return re.sub(r"\[.*?\]", "", text.strip().replace(" [title]", ". ")).replace("  ", " ")


def load_items(cfg, profile, cache_roots, milu_spec_path):
    counts = cfg["profiles"][profile]
    pins = cfg["datasets"]

    def paths(source, pattern):
        return snapshot_paths(cache_roots, pins[source], pattern)

    def first(source, pattern, count):
        return take_rows(paths(source, pattern), list(range(count)))

    tasks = {}
    for level in ("Easy", "Challenge"):
        rows = enumerate(parquet_rows(paths("arc", f"ARC-{level}/test-*.parquet")))
        four_option_rows = ((i, row) for i, row in rows if len(row["choices"]["text"]) == 4)
        items = [
            question(str(i), row["question"], row["choices"]["text"], row["choices"]["label"].index(row["answerKey"]))
            for i, row in islice(four_option_rows, counts["arc"])
        ]
        if len(items) != counts["arc"]:
            raise ValueError(f"Too few four-choice ARC-{level} rows")
        tasks[f"arc_{level.lower()}_cloze"] = items

    rows = first("hellaswag", "data/validation-*.parquet", counts["hellaswag"])
    tasks["hellaswag_cloze"] = [
        Item(str(i), clean_hellaswag(f"{row['activity_label']}: {row['ctx_a']} {row['ctx_b'].capitalize()}"),
             tuple(" " + clean_hellaswag(x) for x in row["endings"]), int(row["label"]))
        for i, row in enumerate(rows)
    ]

    subjects = {}
    for path in paths("mmlu", "*/test-*.parquet"):
        subject = path.parent.name
        if subject not in {"all", "auxiliary_train"}:
            subjects.setdefault(subject, []).append(path)
    if len(subjects) != 57:
        raise ValueError(f"Expected all 57 MMLU subject test files, found {len(subjects)}")
    tasks["mmlu_cloze"] = [
        question(f"{subject}/{i}", row["question"], row["choices"], row["answer"])
        for subject, subject_paths in sorted(subjects.items())
        for i, row in enumerate(take_rows(subject_paths, list(range(counts["mmlu_per_subject"]))))
    ]

    raw = milu_spec_path.read_bytes().replace(b"\r\n", b"\n")
    if sha256(raw) != cfg["milu_item_spec_sha256"]:
        raise ValueError("MILU item spec checksum mismatch")
    milu = json.loads(raw)["tasks"]
    for lang in ("Hindi", "Telugu", "Tamil", "Bengali"):
        pin = milu[f"milu_{lang}"]
        if pin["dataset_revision"] != pins["milu"]["revision"]:
            raise ValueError("MILU revision disagrees with the pinned Team 9 spec")
        ids = pin["doc_ids"][:counts["milu_per_language"]]
        rows = take_rows(paths("milu", f"{lang}/test-*.parquet"), ids)
        tasks[f"milu_{lang}_cloze"] = [
            question(str(i), row["question"], [row[f"option{k}"] for k in range(1, 5)],
                     int(row["target"].removeprefix("option")) - 1)
            for i, row in zip(ids, rows)
        ]

    rows = first("humaneval", "openai_humaneval/test-*.parquet", counts["code_per_set"])
    tasks["humaneval_gold"] = [
        Item(row["task_id"], row["prompt"], (row["canonical_solution"],), 0) for row in rows
    ]
    rows = first("mbpp", "full/test-*.parquet", counts["code_per_set"])
    tasks["mbpp_gold"] = [
        Item(str(row["task_id"]), f"{row['text']}\n{row['test_list'][0]}\n", (row["code"],), 0) for row in rows
    ]
    for kind in cfg["arithmetic"]["kinds"]:
        tasks[f"arith_v1_{kind}"] = arithmetic_items(kind, counts["arithmetic_per_kind"], cfg["arithmetic"]["seed"])
    return tasks


def item_identity(tasks):
    # Include rendered bytes, not just row IDs. The hash binds the exact prompt
    # and continuation while keeping all item text out of results.
    return sha256(json_bytes({name: [vars(item) for item in items] for name, items in tasks.items()}))
