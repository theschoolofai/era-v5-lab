"""Tests of quant_rollout_mismatch.py with stub engines (numpy only, no model).

    python -m pytest test_quant_rollout_mismatch.py -q
"""
import argparse, json, math, sys
from pathlib import Path

import numpy as np
import pytest

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


# ---- cluster intervals, the token dump and the PyTorch reference stage ----------------------------------------
def _per_pos(n=60, seed=0, shift=0.0):
    rng = np.random.default_rng(seed)
    lp_q = np.log(rng.uniform(0.05, 0.95, n))
    return {"lp_ref": lp_q + shift + rng.normal(0, 0.05, n), "lp_q": lp_q, "kl": rng.uniform(0, 0.02, n),
            "agree": rng.random(n) < 0.9}


def test_cluster_bootstrap_brackets_the_estimate_and_is_deterministic():
    per = _per_pos(); clusters = np.repeat(np.arange(6), 10)
    a = m.cluster_bootstrap(per, clusters); b = m.cluster_bootstrap(per, clusters)
    assert a == b and a["clusters"] == 6
    est = {"outside": float(m.ratio_stats(per["lp_ref"] - per["lp_q"], m.EPS)["outside"]),
           "top1_agreement": float(per["agree"].mean())}
    for k, v in est.items():
        assert a[k][0] <= v <= a[k][1]


def test_cluster_bootstrap_has_no_width_for_identical_clusters():
    per = {"lp_ref": np.zeros(40), "lp_q": np.zeros(40), "agree": np.ones(40, dtype=bool)}
    ci = m.cluster_bootstrap(per, np.repeat(np.arange(4), 10))
    assert ci["outside"] == [0.0, 0.0] and ci["top1_agreement"] == [1.0, 1.0] and "mean_kl_ref_to_quant" not in ci


def test_aggregate_without_kl_and_with_clusters():
    per = _per_pos(); per.pop("kl")
    agg = m.aggregate(per, np.arange(60), clusters=np.repeat(np.arange(6), 10))
    assert "mean_kl_ref_to_quant" not in agg and "ci95_by_prompt" in agg and agg["tokens"] == 60


def test_run_format_dumps_ids_and_the_samplers_numbers(tmp_path):
    path = tmp_path / "d.jsonl"
    res = m.run_format("stub", Stub(1.0), Stub(1.0), [[5, 6, 4], [1, 2]], k=2, max_new=3, eps=0.2, dump_path=path)
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    assert len(rows) == 4 == res["rollouts"] and res["ci95_by_prompt"]["clusters"] == 2
    r0 = rows[0]
    assert r0["ids"] == [5, 6, 4, 1, 2, 3] and r0["prompt_len"] == 3 and len(r0["lp_q"]) == len(r0["top1_q"]) == 3


@pytest.fixture()
def toy_hf(tmp_path):
    tr = pytest.importorskip("transformers")
    torch = pytest.importorskip("torch")
    torch.manual_seed(0)
    cfg = tr.Qwen3Config(vocab_size=64, hidden_size=64, intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                         num_key_value_heads=2, head_dim=16, tie_word_embeddings=True)
    model = tr.Qwen3ForCausalLM(cfg).eval()
    model.save_pretrained(tmp_path / "toy")
    return model, tmp_path / "toy"


def _records_from(model, n=3, plen=4, new=6, seed=0):
    import torch
    rng = np.random.default_rng(seed)
    recs = []
    for i in range(n):
        ids = rng.integers(0, 64, plen + new).tolist()
        with torch.no_grad():
            logp = torch.log_softmax(model(input_ids=torch.tensor([ids])).logits[0, plen - 1:-1].float(), -1)
        comp = torch.tensor(ids[plen:])
        recs.append({"format": "toy", "prompt_idx": i % 2, "prompt_len": plen, "ids": ids,
                     "lp_q": logp.gather(-1, comp[:, None]).squeeze(-1).tolist(), "top1_q": logp.argmax(-1).tolist()})
    return recs


def test_torch_stage_gives_ratio_one_when_the_sampler_is_the_same_model(toy_hf):
    torch = pytest.importorskip("torch")
    import score_with_torch as st
    model, _ = toy_hf
    per, pos, cl = st.score_records(model, _records_from(model), torch.device("cpu"), "float32")
    agg = m.aggregate(per, pos, clusters=cl)
    assert agg["max_abs_logratio"] < 1e-5 and agg["outside"] == 0 and agg["top1_agreement"] == 1.0 and agg["tokens"] == 18


def test_torch_stage_sees_a_perturbed_sampler(toy_hf):
    torch = pytest.importorskip("torch")
    import score_with_torch as st
    model, _ = toy_hf
    recs = _records_from(model)
    for r in recs:
        r["lp_q"] = [x - 0.5 for x in r["lp_q"]]                # the sampler assigned less probability everywhere
    per, pos, cl = st.score_records(model, recs, torch.device("cpu"), "float32")
    agg = m.aggregate(per, pos, clusters=cl)
    assert abs(agg["mean_abs_logratio"] - 0.5) < 1e-4 and agg["outside"] == 1.0


def test_torch_stage_rejects_an_id_outside_the_vocabulary(toy_hf):
    torch = pytest.importorskip("torch")
    import score_with_torch as st
    model, _ = toy_hf
    recs = _records_from(model); recs[0]["ids"][-1] = 999
    with pytest.raises(ValueError):
        st.score_records(model, recs, torch.device("cpu"), "float32")


def test_select_prompts_first_and_balanced():
    rows = [(f"e{i}", "english") for i in range(6)] + [(f"c{i}", "code") for i in range(3)] + [(f"i{i}", "indic") for i in range(2)]
    assert [t for t, _ in m.select_prompts(rows, 4)] == ["e0", "e1", "e2", "e3"]
    bal = m.select_prompts(rows, 7, balanced=True)
    assert [t for t, _ in bal] == ["e0", "c0", "i0", "e1", "c1", "i1", "e2"]
    assert [c for _, c in m.select_prompts(rows, 100, balanced=True)].count("english") == 6        # asking for more returns all


def test_load_prompt_rows_reads_categories(tmp_path):
    p = tmp_path / "p.jsonl"
    p.write_text(json.dumps({"prompt": "a", "category": "code"}) + "\n" + json.dumps({"statement": "b"}) + "\nplain c\n")
    assert m.load_prompt_rows(p) == [("a", "code"), ("b", ""), ("plain c", "")]


def test_fixed_100_first_48_has_no_code_prompts_but_balanced_has_every_category():
    fixed = Path(__file__).resolve().parents[1] / "prompts" / "fixed_100.jsonl"
    if not fixed.exists():
        pytest.skip("fixed_100.jsonl not next to this folder")
    rows = m.load_prompt_rows(fixed)
    first = {c for _, c in m.select_prompts(rows, 48)}
    bal = {c for _, c in m.select_prompts(rows, 48, balanced=True)}
    assert "code" not in first and {"english", "indic", "code", "tool_call", "reasoning"} <= bal


# ---- Team 10 note generator -----------------------------------------------------------------------------------
def _llama_dir(tmp_path):
    d = tmp_path / "run"; d.mkdir()
    meta = {"reference": "m-bf16.gguf", "prompts": 50, "prompt_selection": "balanced",
            "prompt_categories": {"english": 10, "indic": 10, "code": 10, "tool_call": 10, "reasoning": 10}, "k": 8, "max_new": 256, "eps": 0.2, "temperature": 1.0}
    for fmt, tps in (("bf16", 100.0), ("Q8_0", 150.0)):
        (d / f"{fmt}.json").write_text(json.dumps({**meta, "formats": [{"format": fmt, "rollout_tokens_per_s": tps}]}))
    (d / "environment.json").write_text("{}")
    return d


def _torch_ref():
    ci = lambda o, k, t: {"outside": o, "k3": k, "top1_agreement": t, "mean_abs_logratio": [0, 0], "clusters": 50}
    row = lambda f, out, k3, top1: {"format": f, "outside": out, "below": out / 2, "above": out / 2, "k3": k3, "top1_agreement": top1,
                                    "abs_logratio_p50_p90_p99_p999": [0.01, 0.1, 0.5, 1.0], "ci95_by_prompt": ci([out * 0.8, out * 1.2], [k3 * 0.8, k3 * 1.2], [top1 - 0.02, top1 + 0.02])}
    return {"reference": "toy/model@rev", "dtype": "bfloat16", "device": "cuda", "torch": "2.11.0", "eps": 0.2,
            "formats": [row("bf16", 0.02, 0.003, 0.97), row("Q8_0", 0.09, 0.0065, 0.94), row("Q4_K_M", 0.41, 0.0739, 0.85)]}


def test_g10_rollout_note_columns_ratio_and_floor(tmp_path):
    import make_g10_note as g
    d = _llama_dir(tmp_path)
    ns = argparse.Namespace(model="toy", notebook_version="v9", pr_this="https://x/this", pr_baseline="https://x/894", hardware="Kaggle T4 x2", prompt_note="")
    md = g.render(g.load_llama(d), _torch_ref(), ns)
    q8 = [l for l in md.splitlines() if l.startswith("| `Q8_0`")][0]
    assert "9.00%" in q8 and "0.0065" in q8 and "1.50x" in q8                      # 150 / 100 tok/s against the bf16 sampler
    q4 = [l for l in md.splitlines() if l.startswith("| `Q4_K_M`")][0]
    assert q4.rstrip().endswith("| - | - |")                                       # no speed measured for that format here
    assert "engine-to-engine floor" in md and "not a speedup against PyTorch bf16" in md
    assert "`bf16`, `Q8_0`" in md and "Q4_K_M`." not in md.split("holds on the formats")[1]   # the stop-rule line lists only formats under 0.05
    assert "balanced" in md and "10 english" in md and "https://x/894" in md


def test_g10_rollout_note_without_a_bf16_sampler_gives_no_speed_ratio(tmp_path):
    import make_g10_note as g
    d = _llama_dir(tmp_path); (d / "bf16.json").unlink()
    ns = argparse.Namespace(model="toy", notebook_version="v9", pr_this="a", pr_baseline="b", hardware="Kaggle T4 x2", prompt_note="")
    md = g.render(g.load_llama(d), {**_torch_ref(), "formats": _torch_ref()["formats"][1:]}, ns)
    assert "No `bf16` sampler row was run" in md and "1.50x" not in md


def test_g10_rollout_note_for_a_run_that_did_not_record_its_prompt_selection(tmp_path):
    import make_g10_note as g
    d = tmp_path / "old"; d.mkdir()
    (d / "Q8_0.json").write_text(json.dumps({"reference": "m", "prompts": 48, "k": 8, "max_new": 256, "eps": 0.2, "temperature": 1.0,
                                             "formats": [{"format": "Q8_0", "rollout_tokens_per_s": 77.0}]}))
    ns = argparse.Namespace(model="toy", notebook_version="v1", pr_this="a", pr_baseline="b", hardware="Kaggle T4 x2", prompt_note="first 48 of the fixed prompts")
    md = g.render(g.load_llama(d), {**_torch_ref(), "formats": _torch_ref()["formats"][1:2]}, ns)
    assert "first (not recorded)" in md and "composition not recorded" in md and "first 48 of the fixed prompts" in md
