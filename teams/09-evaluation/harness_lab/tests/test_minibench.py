import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from minibench_compare import compare
from minibench_gguf import FixedTokensLM
from minibench_items import Item, arithmetic_items, sha256
from minibench_lab import HELDOUT, SUITE, heldout_inputs, score_items, summarize, task_notes


@pytest.mark.parametrize("kind", ("add2", "sub2", "add3", "mul2x1", "add2_deva"))
def test_arithmetic_profiles_balance_answer_position_and_numerical_rank(kind):
    items = arithmetic_items(kind, 50, 42)
    assert items[:20] == arithmetic_items(kind, 20, 42)
    assert [sum(item.answer == i for item in items[:20]) for i in range(4)] == [5] * 4
    assert len({item.prompt for item in items}) == 50
    ranks = []
    for item in items:
        choices = [choice.strip() for choice in item.choices]
        assert len(set(choices)) == 4
        assert len({len(choice) for choice in choices}) == 1
        values = list(map(int, choices))
        left, op, right, _ = item.prompt.split()
        a, b = int(left), int(right)
        assert values[item.answer] == {"+": a + b, "-": a - b, "×": a * b}[op]
        ordered = sorted(values)
        assert len({b - a for a, b in zip(ordered, ordered[1:])}) == 1
        if kind == "mul2x1":
            multiplier = int(item.prompt.split()[-2])
            assert all(value % multiplier == 0 and 10 <= value // multiplier <= 99 for value in values)
        ranks.append(sum(option < values[item.answer] for option in values))
    assert [ranks[:20].count(i) for i in range(4)] == [5] * 4
    assert sorted(ranks.count(i) for i in range(4)) == [12, 12, 13, 13]


def test_full_heldout_keeps_reference_bytes_and_quick_keeps_every_slice():
    cfg = yaml.safe_load(SUITE.read_text(encoding="utf-8"))["heldout"]
    text, sources, full_counts = heldout_inputs(cfg, "full", HELDOUT)
    quick, quick_sources, quick_counts = heldout_inputs(cfg, "quick", HELDOUT)
    assert text == (HELDOUT / "heldout_v1.jsonl").read_bytes()
    assert len(full_counts) == len(quick_counts) == 15
    assert sum(full_counts.values()) == 1059
    assert set(quick_counts.values()) == {cfg["quick_documents_per_slice"]}
    assert len(quick) < len(text) and len(quick_sources) < len(sources)
    originals = {doc["id"]: doc["text"] for doc in map(json.loads, text.splitlines())}
    for doc_line, source_line in zip(quick.splitlines(), quick_sources.splitlines(), strict=True):
        doc, source = json.loads(doc_line), json.loads(source_line)
        prefix = doc["text"].encode("utf-8")
        original = originals[doc["id"]].encode("utf-8")
        assert 0 < len(prefix) <= cfg["quick_max_bytes_per_document"]
        assert original.startswith(prefix)
        assert source["id"] == doc["id"] and source["text_sha256"] == sha256(prefix)
        assert source["original_text_sha256"] == sha256(original)


def test_task_scores_use_bytes_and_outputs_exclude_item_text():
    class Model:
        def loglikelihood(self, requests):
            assert len(requests) == 2
            return [(-4.0, False), (-3.0, False)]

    rows = score_items(Model(), {"task": [Item("1", "prompt\n", (" abc", " d"), 0)]})["task"]
    assert rows == [{"id": "1", "correct": True, "gold_nll_nats": 4.0, "utf8_bytes": 5}]
    assert summarize(rows)["accuracy_points"] == 100
    assert summarize(rows)["stderr_points"] is None


def test_reference_code_scores_exact_continuation_and_leaves_prompt_whitespace_in_context():
    class Model:
        art = SimpleNamespace(encode=lambda text: {"def f():\n": [1, 2], "    return 'é'": [3, 4]}[text])

        def loglikelihood_tokens(self, pairs, *, allow_truncation):
            assert list(pairs) == [([1, 2], [3, 4])]
            assert allow_truncation is False
            return [(-4.0, False)]

    choice = "    return 'é'"
    rows = score_items(Model(), {"code": [Item("1", "def f():\n", (choice,), 0)]})["code"]
    assert rows == [{"id": "1", "gold_nll_nats": 4.0, "utf8_bytes": len(choice.encode("utf-8"))}]


def test_records_carry_the_diagnostic_approval_and_internal_only_labels():
    diagnostic = "diagnostic, not cleared for contamination"
    assert diagnostic not in task_notes("mmlu_cloze", "full")
    assert diagnostic not in task_notes("arith_v1_add2", "quick")
    assert diagnostic in task_notes("arc_challenge_cloze", "full")
    assert "awaiting TSAI approval for lab checkpoints" in task_notes("arc_easy_cloze", "quick")
    assert "awaiting TSAI approval for lab checkpoints" not in task_notes("arc_challenge_cloze", "quick")
    assert task_notes("hellaswag_cloze", "full")[-1] == "internal only, TSAI decides public tables"
    assert task_notes("mmlu_cloze", "smoke")[-1] == "Smoke profile: execution evidence only"


def test_pair_comparison_requires_matching_inputs():
    identity = dict.fromkeys(("suite_sha256", "items_sha256", "heldout_sha256", "heldout_sources_sha256",
                             "tokenizer_sha256"), "sha")
    left = {**identity, "schema_version": "minibench_cont_v1", "profile": "quick", "suite": "minibench_v1",
            "items": {"task": [{"id": "1", "correct": True, "gold_nll_nats": 4.0, "utf8_bytes": 5}]},
            "heldout": {"val/bpb": 2.5}}
    assert compare(left, left)["tasks"]["task"]["accuracy_ci95_points"] == [0, 0]
    assert compare(left, left)["heldout_bpb_delta"] == {"val/bpb": 0.0}
    with pytest.raises(ValueError, match="items_sha256"):
        compare(left, {**left, "items_sha256": "other"})


def test_gguf_window_scores_each_target_from_its_preceding_logit_row():
    logits = np.array([[1.0, -2.0, 4.0], [2.0, 3.0, -1.0], [0.0, 8.0, 0.0]])
    llm = SimpleNamespace(n_vocab=lambda: 3, token_bos=lambda: 0, scores=logits)
    seen = []
    backend = SimpleNamespace(llm=llm, _eval_reuse_prefix=lambda tokens: seen.append(tokens))
    artifacts = SimpleNamespace(lengths=[0, 1, 1], bos_id=0)
    lm = FixedTokensLM(backend, artifacts, 3)
    score = lm.sequence_logp([0, 2, 1], [1, 1])
    expected = sum(row[1] - np.logaddexp.reduce(row) for row in logits[1:])
    assert score == pytest.approx(expected)
    assert seen == [[0, 2, 1]]
    assert lm.loglikelihood_tokens([([2], [1, 1])], allow_truncation=False)[0][0] == pytest.approx(
        sum(row[1] - np.logaddexp.reduce(row) for row in logits[1:])
    )
    with pytest.raises(ValueError, match="context window"):
        lm.loglikelihood_tokens([([2, 1], [1, 1])], allow_truncation=False)
