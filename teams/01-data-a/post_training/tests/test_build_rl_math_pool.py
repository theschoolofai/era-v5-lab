"""Tests for build_rl_math_pool.py (no network, no fingerprint set: F2 and tokens are injected)."""
import hashlib, importlib.util, json, sys
from pathlib import Path

import pyarrow.parquet as pq
import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("build_rl_math_pool", HERE.parent / "build_rl_math_pool.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)
MV = B.load_module("math_verifier", B.VERIFIER)


def run(rows, f2=lambda t: False, drop=(), tok=lambda qs: [len(q.split()) for q in qs]):
    return B.build(iter(rows), f2, set(drop), MV, tok)


def test_clean_strips_zero_width_and_ghost_markers_only():
    assert B.clean("﻿Find​ x. [INST]<think></think>### Assistant:") == "Find x."


def test_clean_keeps_zwj_zwnj_and_does_not_apply_nfkc():
    s = "क्‍ष न‌ ﬁ １２"  # ZWJ, ZWNJ, the fi ligature, full-width digits
    assert B.clean(s) == s


def test_clean_applies_nfc():
    assert B.clean("caf\u0065\u0301") == "caf\u00e9"


def test_duplicates_are_dropped_after_case_and_space_folding_first_line_kept():
    kept, c = run([(0, "Find  X.", "1"), (1, "find x.", "2"), (2, "Find y.", "3")])
    assert [r["doc_id"] for r in kept] == ["omr_rl:0", "omr_rl:2"]
    assert c["duplicate"] == 1


def test_f2_hit_is_dropped_and_counted_and_sees_question_and_answer():
    seen = []
    kept, c = run([(0, "Q one", "7"), (1, "Q two", "8")], f2=lambda t: seen.append(t) or "two" in t)
    assert [r["doc_id"] for r in kept] == ["omr_rl:0"] and c["f2"] == 1
    assert seen[0] == "Q one\n\n7"


def test_drop_list_ids_are_removed():
    kept, c = run([(0, "Q a", "1"), (1, "Q b", "2")], drop={"omr_rl:1"})
    assert [r["doc_id"] for r in kept] == ["omr_rl:0"] and c["drop_list"] == 1


def test_a_duplicate_of_an_f2_row_counts_as_duplicate_not_f2():
    kept, c = run([(0, "Bench q", "1"), (1, "bench  q", "1")], f2=lambda t: True)
    assert kept == [] and c["f2"] == 1 and c["duplicate"] == 1


@pytest.mark.parametrize("answer,kind", [("32", "number"), (r"\frac{1}{2}", "number"), (r"\(\dfrac{3}{4}\)", "number"),
                                         ("-0.5", "number"), (r"\sqrt{2}", "symbolic"), ("x^2+1", "symbolic"),
                                         ("B", "guessable"), ("(c)", "guessable"), ("Yes", "guessable"),
                                         ("9" * 201, "too_long")])
def test_answer_type_uses_team10_parser(answer, kind):
    assert B.answer_type(answer, MV) == kind


def test_guessable_and_too_long_rows_are_not_written():
    kept, c = run([(0, "q0", "B"), (1, "q1", "9" * 300), (2, "q2", r"\pi"), (3, "q3", "12")])
    assert [(r["doc_id"], r["answer_type"]) for r in kept] == [("omr_rl:2", "symbolic"), ("omr_rl:3", "number")]
    assert (c["guessable"], c["too_long"], c["kept_symbolic"], c["kept_number"]) == (1, 1, 1, 1)


def test_rows_empty_after_cleaning_are_dropped():
    kept, c = run([(0, "​", "1"), (1, "q", "﻿")])
    assert kept == [] and c["empty_after_clean"] == 2


def test_every_read_row_is_counted_exactly_once():
    rows = [(0, "a", "1"), (1, "A", "1"), (2, "b", "B"), (3, "c", "2"), (4, "​", "1"), (5, "d", "x")]
    kept, c = run(rows, f2=lambda t: t.startswith("c"))
    dropped = c["empty_after_clean"] + c["duplicate"] + c["f2"] + c["drop_list"] + c["guessable"] + c["too_long"]
    assert c["read"] == 6 == dropped + c["kept_number"] + c["kept_symbolic"] == dropped + len(kept)


def test_two_writes_are_byte_identical_and_the_row_names_the_sha(tmp_path):
    kept, c = run([(0, "q0", "1"), (1, "q1", r"\sqrt{3}")])
    src = {**B.SOURCE, "input_sha256": "x"}
    s1 = B.write(kept, c, tmp_path / "a", src, {"f2_set_sha256": "s"})
    s2 = B.write(kept, c, tmp_path / "b", src, {"f2_set_sha256": "s"})
    a, b = (tmp_path / d / "rl_math_pool_v1.parquet" for d in "ab")
    assert a.read_bytes() == b.read_bytes()
    assert s1["parquet_sha256"] == s2["parquet_sha256"] == hashlib.sha256(a.read_bytes()).hexdigest()
    row = json.loads((tmp_path / "a" / "pack_table_row.json").read_text())
    assert all(row[k] not in (None, "") for k in ("hf_repo", "hf_revision", "license", "license_source", "generator",
                                                   "generator_license", "sha256", "language", "script", "lane"))
    assert row["rows"] == 2 and row["rows_number_answers"] == 1 and row["sha256"] == s1["parquet_sha256"]
    t = pq.read_table(a)
    assert t.column_names == ["doc_id", "pack_id", "question", "answer", "answer_type", "q_tokens", "source_line"]
    assert t.column("q_tokens").to_pylist() == [1, 1]


def test_main_refuses_an_input_whose_sha256_is_not_the_pin(tmp_path):
    f = tmp_path / "train.jsonl"
    f.write_text(json.dumps({"question": "q", "expected_answer": "1"}) + "\n")
    with pytest.raises(SystemExit, match="is not the pinned"):
        B.main(["--out", str(tmp_path / "o"), "--jsonl", str(f)])


def test_the_pinned_source_is_the_train_file_only():
    assert B.SOURCE["file"] == "train.jsonl" and "validation" not in json.dumps(B.SOURCE)
