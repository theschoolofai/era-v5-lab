"""Quantized-rollout sampler, its place in the trainer, and the Team 8 feed. Tiny random models on CPU: mechanics only.

    python -m pytest rl-loop/test_quant_rollout.py -q
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
import yaml  # noqa: E402
from torch import nn  # noqa: E402

HERE = Path(__file__).resolve().parent
TEAMS = HERE.parents[1]
sys.path.insert(0, str(HERE))

import metrics_feed  # noqa: E402
import quant_rollout as qr  # noqa: E402
import train  # noqa: E402
from policy import Policy, completion_logprobs, hf_policy, module_policy  # noqa: E402

parametrize = pytest.mark.parametrize
PROMPTS = [[1, 2, 3], [4, 5, 6, 7, 8]]


def _llama(eos=None):
    torch.manual_seed(0)
    cfg = transformers.LlamaConfig(vocab_size=32, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                                   num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=64,
                                   eos_token_id=eos, bos_token_id=None, pad_token_id=None, tie_word_embeddings=False)
    return transformers.LlamaForCausalLM(cfg).eval()


class _Toy(nn.Module):
    """model(ids, valid) -> logits, the call shape of Team 5's LanguageModel."""

    def __init__(self):
        super().__init__()
        torch.manual_seed(0)
        self.emb = nn.Embedding(32, 16)
        self.a = nn.Linear(16, 16)
        self.head = nn.Linear(16, 32)

    def forward(self, ids, valid):
        return self.head(torch.tanh(self.a(self.emb(ids))))


def _learner_lp(policy, rolls, prompts):
    with torch.no_grad():
        return [completion_logprobs(policy, r.seq, len(p)) for p, r in zip(prompts, rolls)]


@parametrize("eos", [None, 5])
def test_exact_copy_reports_the_learners_own_logprobs(eos):
    policy = hf_policy(_llama(eos), eos, "cpu")
    sampler = qr.QuantRolloutSampler(policy, "copy")
    rolls = sampler.sample(PROMPTS, 4, 6, 1.0, torch.Generator().manual_seed(1))
    assert [tuple(r.seq.shape) for r in rolls] == [(4, 9), (4, 11)]
    for p, r, lp in zip(PROMPTS, rolls, _learner_lp(policy, rolls, PROMPTS)):
        assert r.seq[0, :len(p)].tolist() == p
        torch.testing.assert_close(r.rollout_lp[r.cmask], lp[r.cmask], rtol=1e-4, atol=1e-4)
        assert (r.rollout_lp[~r.cmask] == 0).all()
    assert sampler.last["entropy"] > 0 and sampler.refreshes == 1


@parametrize("scheme", ["bf16", "int8_dynamic", "w8a8_sim", "w4a16_sim"])
def test_a_quantized_copy_samples_with_its_own_logprobs_and_leaves_the_learner_alone(scheme):
    policy = hf_policy(_llama(), None, "cpu")
    before = {k: v.clone() for k, v in policy.model.state_dict().items()}
    sampler = qr.QuantRolloutSampler(policy, scheme)
    rolls = sampler.sample(PROMPTS, 4, 6, 1.0, torch.Generator().manual_seed(1))
    q = sampler.refresh()
    for p, r in zip(PROMPTS, rolls):  # rollout_lp is the COPY's log-probability of the tokens it sampled
        with torch.no_grad():
            own = completion_logprobs(q, r.seq, len(p))
        torch.testing.assert_close(r.rollout_lp, own, rtol=0.05, atol=0.05)
    assert all(torch.equal(before[k], v) for k, v in policy.model.state_dict().items())
    assert sampler.info["scheme"] == scheme and sampler.info["simulated"] == scheme.endswith("_sim")


def test_the_copy_follows_the_learners_weights():
    policy = hf_policy(_llama(), None, "cpu")
    sampler = qr.QuantRolloutSampler(policy, "w8a8_sim")
    ids = torch.tensor([PROMPTS[0]])
    mask = torch.ones_like(ids)
    a = sampler.refresh().logits(ids, mask)
    with torch.no_grad():
        policy.model.lm_head.weight.data.mul_(-1)  # a .data write bumps no version counter: still picked up
    assert not torch.allclose(a, sampler.refresh().logits(ids, mask))


def test_native_policy_path_and_a_greater_gap_with_fewer_bits():
    policy = module_policy(_Toy(), None, "cpu")
    gaps = {}
    for scheme in ("copy", "w8a8_sim", "w4a16_sim"):
        rolls = qr.QuantRolloutSampler(policy, scheme).sample(PROMPTS, 8, 16, 1.0, torch.Generator().manual_seed(2))
        lps = _learner_lp(policy, rolls, PROMPTS)
        gaps[scheme] = max(float((r.rollout_lp - lp)[r.cmask].abs().mean()) for r, lp in zip(rolls, lps))
    assert gaps["copy"] < 1e-6 < gaps["w8a8_sim"] < gaps["w4a16_sim"]


def test_fake_quantize_rounds_to_the_expected_levels():
    w = torch.tensor([[1.27, -0.004, 0.5], [0.0, 0.0, 0.0]])
    out = qr.fake_quantize(w, 8)
    torch.testing.assert_close(out, torch.tensor([[1.27, 0.0, 0.5], [0.0, 0.0, 0.0]]))
    four = qr.fake_quantize(torch.tensor([[7.0, 0.4, 0.7, 0.2]]), 4, group=2)
    torch.testing.assert_close(four, torch.tensor([[7.0, 0.0, 0.7, 0.2]]))


def test_router_weights_are_never_quantized():
    class Moe(nn.Module):
        def __init__(self):
            super().__init__()
            self.moe = nn.Module()
            self.moe.router = nn.Linear(8, 4, bias=False)
            self.moe.expert = nn.Linear(8, 8, bias=False)

    m = Moe()
    q, info = qr.quantized_copy(m, "w4a16_sim")
    assert torch.equal(q.moe.router.weight, m.moe.router.weight) and not torch.equal(q.moe.expert.weight, m.moe.expert.weight)
    assert info["linear_layers"] == 1


def test_what_the_sampler_refuses():
    policy = hf_policy(_llama(), None, "cpu")
    with pytest.raises(ValueError, match="temperature must be 1.0"):
        qr.QuantRolloutSampler(policy, "copy").sample(PROMPTS, 2, 2, 0.7)
    with pytest.raises(ValueError, match="unknown quantization scheme"):
        qr.QuantRolloutSampler(policy, "q8")
    with pytest.raises(ValueError, match="int8_dynamic is for Hugging Face"):
        qr.QuantRolloutSampler(module_policy(_Toy(), None, "cpu"), "int8_dynamic")


def _config(tmp_path, steps=6, **overrides):
    cfg = yaml.safe_load((HERE / "config" / "smoke_tiny_olmoe.yaml").read_text())
    cfg["out_dir"] = str(tmp_path / "out")
    cfg["task"].update(n_train=32, n_heldout=8)
    cfg["train"].update(steps=steps, eval_every=3, eval_k=4, prompts_per_step=4, k=4, ppo_epochs=1, **overrides)
    cfg["verbose"] = False
    return cfg


def _rows(tmp_path):
    return [json.loads(x) for x in (tmp_path / "out" / "metrics.jsonl").read_text().splitlines()]


@parametrize("algo", ["grpo", "objective_v1"])
def test_training_on_quantized_rollouts_logs_mismatch_rates_and_the_guard(tmp_path, algo):
    extra = {"tis_clip": 2.0} if algo == "grpo" else {}
    s = train.train(_config(tmp_path, algo=algo, sampler="quant", quant={"scheme": "w8a8_sim"}, **extra))
    rows = _rows(tmp_path)
    assert len(rows) == 6 and not s.get("failures")
    measured = [r for r in rows if "mismatch_k3" in r]
    assert measured and all(r["mismatch_k3"] >= 0 and r["mismatch_abs_logratio"] > 0 for r in measured)
    assert any(r["mismatch_k3"] > 0 for r in measured)  # rows round to 6 decimals; a 16-token toy can sit below that
    assert all(r["quant_scheme"] == "w8a8_sim" and r["quant_refresh_s"] > 0 and r["optim_step_s"] >= 0 for r in rows)
    assert s["quant"]["refreshes"] >= 6 and s["quant"]["stopped"] is None and s["mean_mismatch_k3"] > 0
    if algo == "objective_v1":
        assert all(r["ratio_source"] == "rollout_lp" for r in rows if r["optimizer_stepped"])
    evals = [json.loads(x) for x in (tmp_path / "out" / "evals.jsonl").read_text().splitlines()]
    assert {e["name"] for e in evals} == {"heldout", "heldout_quant"}

    feed = metrics_feed.convert(tmp_path / "out" / "metrics.jsonl", tmp_path / "feed.jsonl", tmp_path / "out" / "summary.json")
    for key in ("train_reward", "mixed_group_frac", "rollout_tok_s", "idle_s", "optim_step_share", "gradient_norm", "entropy"):
        assert any(key in r for r in feed), key
    assert feed[-1]["router_checksum_ok"] is True


def test_the_stop_rule_ends_the_run_and_reports_a_failure(tmp_path):
    s = train.train(_config(tmp_path, sampler="quant", quant={"scheme": "w4a16_sim", "max_k3": 0.0, "guard": False}))
    assert len(_rows(tmp_path)) == 1 and s["steps"] == 1 and s["steps_planned"] == 6
    assert s["quant"]["stopped"]["after_step"] == 1 and "max_k3" in s["failures"][0]


def test_an_exact_copy_run_has_no_mismatch(tmp_path):
    s = train.train(_config(tmp_path, steps=3, sampler="quant", quant={"scheme": "copy", "max_k3": 1e-6}))
    assert s["quant"]["stopped"] is None and s["mean_mismatch_k3"] <= 1e-6


def test_a_resumed_quant_run_equals_an_uninterrupted_one(tmp_path):
    def run(sub, calls):
        cfg = _config(tmp_path / sub, sampler="quant", quant={"scheme": "w8a8_sim"},
                      state_dir=str(tmp_path / sub / "state"), state_every=1)
        if calls:
            cfg["train"]["max_steps_this_call"] = calls
            assert train.train(cfg)["status"] == "PAUSED_AT_DEADLINE"
            del cfg["train"]["max_steps_this_call"]
        train.train(cfg)
        evals = [json.loads(x) for x in (tmp_path / sub / "out" / "evals.jsonl").read_text().splitlines()]
        keep = ("step", "train_reward", "mismatch_k3", "loss")
        return [{k: r.get(k) for k in keep} for r in _rows(tmp_path / sub)], [(e["name"], e["step"], e["pass"]) for e in evals]

    assert run("whole", None) == run("parts", 2)


def test_a_quant_stop_stays_stopped_after_a_restart(tmp_path):
    cfg = _config(tmp_path, steps=4, sampler="quant", quant={"scheme": "w4a16_sim", "max_k3": 0.0, "guard": False},
                  state_dir=str(tmp_path / "state"), state_every=5)
    first = train.train(copy.deepcopy(cfg))
    again = train.train(copy.deepcopy(cfg))
    assert first["steps"] == again["steps"] == 1
    assert again["quant"]["stopped"] == first["quant"]["stopped"] and "max_k3" in again["failures"][0]
    assert [r["step"] for r in _rows(tmp_path)] == [1]


def test_the_feed_reads_held_out_rewards_of_a_resumable_run(tmp_path):
    cfg = _config(tmp_path, steps=2, sampler="quant", quant={"scheme": "w8a8_sim"}, state_dir=str(tmp_path / "state"),
                  state_every=1)
    cfg["train"]["eval_every"] = 1
    train.train(cfg)
    out = tmp_path / "out"
    assert all("heldout_reward" not in r for r in _rows(tmp_path))  # the row is written before the evaluation
    rows = metrics_feed.convert(out / "metrics.jsonl", tmp_path / "feed.jsonl")
    assert all("heldout_reward" in r and "heldout_reward_quant" in r for r in rows)


def test_the_feed_leaves_out_optimizer_time_that_was_not_synchronised():
    rec = {"step": 1, "step_s": 2.0, "optim_step_s": 0.5, "peak_torch_gb": 3.1}
    assert not {"optim_step_s", "optim_step_share"} & set(metrics_feed.feed_row(rec))
    assert metrics_feed.feed_row({**rec, "times_synced": True})["optim_step_share"] == 0.25
    assert metrics_feed.feed_row({k: v for k, v in rec.items() if k != "peak_torch_gb"})["optim_step_share"] == 0.25


@parametrize("train_cfg, match", [
    ({"sampler": "quant"}, "come together"),
    ({"quant": {"scheme": "copy"}}, "come together"),
    ({"sampler": "quant", "quant": {"scheme": "q8"}}, "train.quant needs scheme"),
    ({"sampler": "quant", "quant": {"scheme": "copy", "every": 3}}, "train.quant needs scheme"),
    ({"sampler": "quant", "quant": {"scheme": "copy"}, "temperature": 0.8}, "temperature 1.0"),
    ({"sampler": "quant", "quant": {"scheme": "copy"}, "logprob_gate": True}, "differs by design"),
])
def test_bad_quant_configs_are_refused(tmp_path, train_cfg, match):
    with pytest.raises(ValueError, match=match):
        train.train(_config(tmp_path, **train_cfg))


def _team5_bundle(kv_cache: bool):
    """A team5_adapter.Bundle around a tiny model of Team 5's classes: no tokenizer or checkpoint, so only the model paths."""
    harness = str(TEAMS / "05-architecture" / "harness")
    if harness not in sys.path:
        sys.path.append(harness)  # after rl-loop: harness/train.py must not shadow rl-loop/train.py
    import team5_adapter as ta  # noqa: PLC0415
    from week2 import config as C  # noqa: PLC0415
    from week2.model import LanguageModel  # noqa: PLC0415
    spec = copy.deepcopy(C.load_runtime(str(TEAMS / "05-architecture" / "configs" / "arms" / "t2.yaml"))["model"])
    spec.update(vocab_size=64, block_size=32, n_layer=2, n_head=4, n_kv_head=2, n_embd=32)
    spec["moe"] = dict(spec["moe"], num_experts=4, top_k=2, num_shared=1, ffn_hidden=32, bias_gamma=0.001)
    rows = torch.randint(0, 255, (64, 32), generator=torch.Generator().manual_seed(1)).to(torch.uint8)
    lengths = torch.randint(1, 5, (64,), generator=torch.Generator().manual_seed(2))
    torch.manual_seed(0)
    model = LanguageModel(spec, rows, lengths).eval()
    special = {"tokens": {"end_of_turn": {"id": 63}}, "stop_ids": [63], "pad_id": 0}
    return ta.Bundle("fixture", model, spec, None, special, {}, {}, Path("unused"), None, kv_cache=kv_cache)


@parametrize("kv_cache", [False, True])
@parametrize("scheme", [s for s in qr.SCHEMES if s != "int8_dynamic"])
def test_team5s_policy_samples_from_the_copy_not_from_the_learner(scheme, kv_cache):
    bundle = _team5_bundle(kv_cache)
    policy = bundle.policy()
    prompts = [[1, 2, 3], [4, 5, 6]]
    before = {n: p.detach().clone() for n, p in policy.model.named_parameters()}
    sampler = qr.QuantRolloutSampler(policy, scheme, pad_id=bundle.special["pad_id"])
    q = sampler.refresh()
    ids = torch.tensor([prompts[0]])
    with torch.no_grad():
        learner, copy_ = policy.logits(ids).float(), q.logits(ids).float()
    assert q.model is not policy.model and bundle.model is policy.model
    if scheme == "copy":
        assert torch.equal(learner, copy_)
    elif scheme in qr.SIMULATED:
        assert not torch.allclose(learner, copy_, atol=1e-4, rtol=0)
    rolls = sampler.sample(prompts, 2, 4, 1.0, torch.Generator().manual_seed(0))
    for p, r in zip(prompts, rolls):
        with torch.no_grad():
            torch.testing.assert_close(r.rollout_lp[r.cmask], completion_logprobs(q, r.seq, len(p))[r.cmask],
                                       atol=1e-2 if scheme in ("bf16", "fp16") else 1e-5, rtol=0)
    assert all(torch.equal(before[n], p) for n, p in policy.model.named_parameters())


def test_a_policy_that_ignores_the_copy_is_refused():
    torch.manual_seed(0)
    learner = torch.nn.Embedding(8, 8)
    stuck = Policy(learner, lambda m, ids, mask: learner(ids))  # holds its own reference, no with_model()
    with pytest.raises(RuntimeError, match="needs with_model"):
        qr.QuantRolloutSampler(stuck, "w8a8_sim", router_patterns=()).refresh()


@parametrize("scheme", ["copy", "w8a8_sim", "w4a16_sim"])
def test_a_mixed_precision_hf_learner_keeps_its_compute_dtype_in_the_copy(scheme):
    policy = hf_policy(_llama(), None, "cpu")
    policy.model.to(torch.bfloat16)
    first = next(p for n, p in policy.model.named_parameters() if "q_proj" in n)
    first.data = first.data.float()  # an fp32 master inside a bf16 model, as use_fp32_master leaves it
    policy.amp_dtype = torch.bfloat16
    sampler = qr.QuantRolloutSampler(policy, scheme, pad_id=0)
    assert sampler.refresh().amp_dtype == torch.bfloat16
    assert len(sampler.sample([[1, 2, 3]], 2, 3, 1.0, torch.Generator().manual_seed(0))) == 1


def test_team8_loader_reads_the_feed(tmp_path):
    loader = TEAMS / "08-monitoring" / "clickhouse"
    if not (loader / "load_jsonl.py").is_file():
        pytest.skip("Team 8's loader is not in this checkout")
    sys.path.insert(0, str(loader))
    from load_jsonl import parse_source  # noqa: PLC0415

    rec = {"step": 1, "train_reward": 0.5, "groups_used": 1, "groups_dropped": 3, "mismatch_k3": 0.01,
           "times_s": {"reward": 0.2}, "rollout_tokens_per_s": 12.0, "optim_step_s": 0.1, "step_s": 1.0,
           "subgroups": {"code": {"passes": 3, "rollouts": 4}}}
    src = tmp_path / "metrics.jsonl"
    src.write_text(json.dumps(rec) + "\n")
    metrics_feed.convert(src, tmp_path / "feed.jsonl")
    got = {r["name"]: r["value"] for r in parse_source(str(tmp_path / "feed.jsonl"), run_id_override="g10")["rows"]}
    assert got["train_reward"] == 0.5 and got["mismatch_k3"] == 0.01 and got["reward_per_env.code"] == 0.75
    assert got["mixed_group_frac"] == 0.25 and got["idle_s"] == 0.2 and got["optim_step_share"] == 0.1
    assert "mismatch_abs_logratio" not in got  # not measured in this row: absent, not zero
