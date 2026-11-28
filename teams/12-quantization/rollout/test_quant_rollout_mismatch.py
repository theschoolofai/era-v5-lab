"""Tests of quant_rollout_mismatch.py with stub engines (numpy only, no model).

    python -m pytest test_quant_rollout_mismatch.py -q
"""
import json, math, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import quant_rollout_mismatch as m  # noqa: E402

V = 7


def logits(seed, T=10, scale=1.0):
    return np.random.default_rng(seed).standard_normal((T, V)).astype(np.float32) * scale


def test_identical_models_have_ratio_one_and_no_kl():
    L = logits(0); toks = np.arange(10) % V
    per = m.position_stats(L, L, toks)
    agg = m.aggregate(per, np.arange(10))
    assert agg["outside"] == 0 and agg["max_abs_logratio"] == 0 and agg["k3"] == 0
    assert agg["mean_kl_ref_to_quant"] == 0 and agg["top1_agreement"] == 1.0


def test_kl_matches_the_definition():
    a, b = logits(1, 3), logits(2, 3)
    per = m.position_stats(a, b, np.array([0, 1, 2]))
    pa, pb = np.exp(m.log_softmax(a)), np.exp(m.log_softmax(b))
    assert np.allclose(per["kl"], (pa * np.log(pa / pb)).sum(-1))
    assert (per["kl"] >= 0).all()


def test_lp_is_the_log_softmax_of_the_sampled_token_and_chunking_does_not_change_it():
    a, b = logits(3, 150), logits(4, 150); toks = np.arange(150) % V
    whole = m.position_stats(a, b, toks, chunk=150)
    chunked = m.position_stats(a, b, toks, chunk=64)
    for k in whole:
        assert np.allclose(whole[k], chunked[k])
    assert np.allclose(whole["lp_ref"], m.log_softmax(a)[np.arange(150), toks])


def test_ratio_stats_counts_tokens_outside_the_trust_region():
    lr = np.log(np.array([1.0, 1.1, 0.7, 1.5]))                  # eps 0.2: 0.7 below, 1.5 above
    s = m.ratio_stats(lr, 0.2)
    assert (s["tokens"], s["below"], s["above"], s["outside"]) == (4, 0.25, 0.25, 0.5)
    assert math.isclose(s["k3"], float(np.mean(np.exp(lr) - lr - 1)))


def test_buckets_cover_every_token_once():
    per = m.position_stats(logits(5, 40), logits(6, 40), np.arange(40) % V)
    agg = m.aggregate(per, np.arange(40))
    assert sum(b["tokens"] for b in agg["by_sampler_prob"].values()) == 40
    assert sum(b["tokens"] for b in agg["by_position"].values()) == 40


def test_empty_input_is_reported_not_crashed():
    assert m.ratio_stats(np.array([]), 0.2) == {"tokens": 0}


class Stub:
    """Engine stub: fixed logits per sequence; sample() returns 3 tokens in 0.5 s of fake time."""
    def __init__(self, scale):
        self.scale = scale

    def sample(self, prompt_ids, max_new):
        return [1, 2, 3][:max_new], 0.5

    def logits(self, ids):
        return logits(len(ids), len(ids), self.scale)


def test_run_format_scores_the_same_ids_and_reports_speed():
    res = m.run_format("stub", Stub(1.0), Stub(1.0), [[5, 6, 4], [1, 2]], k=2, max_new=3, eps=0.2)
    assert res["rollouts"] == 4 and res["new_tokens"] == 12 and res["rollout_tokens_per_s"] == 6.0
    assert res["outside"] == 0 and res["top1_agreement"] == 1.0           # same stub logits for the same ids
    noisy = m.run_format("noisy", Stub(0.5), Stub(1.0), [[5, 6, 4]], k=2, max_new=3, eps=0.2)
    assert noisy["mean_kl_ref_to_quant"] > 0


def test_load_prompts_reads_prompt_statement_and_plain_lines(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text(json.dumps({"prompt": "a"}) + "\n" + json.dumps({"statement": "b"}) + "\nplain c\n\n")
    assert m.load_prompts(p, 10) == ["a", "b", "plain c"] and m.load_prompts(p, 2) == ["a", "b"]
