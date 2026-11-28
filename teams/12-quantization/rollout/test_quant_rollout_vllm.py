"""Tests of quant_rollout_vllm.py and check_dense_w4a16.py with fake vLLM objects (no GPU, no vLLM).

    python -m pytest test_quant_rollout_vllm.py -q
"""
import json, struct, sys
from dataclasses import dataclass
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_dense_w4a16 as cd  # noqa: E402
import quant_rollout_vllm as qv  # noqa: E402

EOS = 99


@dataclass
class Lp:
    logprob: float
    rank: int = None


@dataclass
class Out:
    token_ids: list
    logprobs: list
    finish_reason: str = "length"


@dataclass
class Req:
    outputs: list


def _out(ids, finish="length", top=None):
    """logprobs entries: the sampled token, and the rank-1 token when it is a different one."""
    entries = []
    for i, t in enumerate(ids):
        e = {t: Lp(-0.5 - 0.1 * i, rank=1 if top is None else 2)}
        if top is not None:
            e[top] = Lp(-0.2, rank=1)
        entries.append(e)
    return Out(ids, entries, finish)


def test_rollout_from_output_reads_logprobs_and_top1():
    ids, lp, top1 = qv.rollout_from_output(_out([5, 6, 7], top=3), EOS)
    assert ids == [5, 6, 7] and lp == [-0.5, -0.6, -0.7] and top1 == [3, 3, 3]
    ids, lp, top1 = qv.rollout_from_output(_out([5, 6]), EOS)                       # the sampled token is the top-1
    assert top1 == [5, 6]


def test_the_eos_that_ended_a_completion_is_dropped_but_a_cut_completion_keeps_everything():
    ids, lp, top1 = qv.rollout_from_output(_out([5, 6, EOS], finish="stop"), EOS)
    assert ids == [5, 6] and len(lp) == len(top1) == 2
    ids, _, _ = qv.rollout_from_output(_out([5, 6, EOS], finish="length"), EOS)       # not an EOS stop: nothing dropped
    assert ids == [5, 6, EOS]
    ids, _, _ = qv.rollout_from_output(_out([EOS], finish="stop"), EOS)
    assert ids == []


def test_a_completion_without_logprobs_is_refused():
    with pytest.raises(ValueError):
        qv.rollout_from_output(Out([1, 2], None), EOS)
    with pytest.raises(ValueError):
        qv.rollout_from_output(Out([1, 2], [{1: Lp(-1.0, 1)}]), EOS)                  # length mismatch


class FakeLLM:
    def __init__(self):
        self.calls = []

    def generate(self, prompts, params):
        self.calls.append((prompts, params))
        reqs = []
        for pi, p in enumerate(prompts):
            outs = [_out([10 + pi, 20], finish="length") for _ in range(params["k"] - 1)] + [_out([30 + pi, EOS], finish="stop")]
            reqs.append(Req(outs))
        return reqs


def _params(k, max_new, seed):
    return {"k": k, "max_new": max_new, "seed": seed}


def test_sample_format_writes_the_dump_in_the_llama_stage_format(tmp_path):
    llm = FakeLLM()
    path = tmp_path / "d.jsonl"
    row = qv.sample_format(llm, "vllm_W4A16", [[1, 2, 3], [4, 5]], ["code", "indic"], k=3, max_new=16, seed=7, eos_id=EOS,
                           make_params=_params, dump_path=path)
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    assert len(rows) == 6 == row["rollouts"] and row["new_tokens"] == 2 + 2 + 1 + 2 + 2 + 1   # the EOS of each last sample is dropped
    r0 = rows[0]
    assert r0["format"] == "vllm_W4A16" and r0["prompt_idx"] == 0 and r0["prompt_len"] == 3 and r0["category"] == "code"
    assert r0["ids"] == [1, 2, 3, 10, 20] and len(r0["lp_q"]) == len(r0["top1_q"]) == 2
    assert {r["category"] for r in rows} == {"code", "indic"}
    assert row["finish_reasons"] == {"length": 4, "stop": 2} and "batched" in row["speed_is"]
    assert llm.calls[0][0][0] == {"prompt_token_ids": [1, 2, 3]} and llm.calls[0][1] == {"k": 3, "max_new": 16, "seed": 7}


def test_the_dump_is_what_the_pytorch_stage_reads(tmp_path):
    import score_with_torch as st                       # needs torch: skipped without it
    pytest.importorskip("torch")
    path = tmp_path / "d.jsonl"
    qv.sample_format(FakeLLM(), "vllm_fp16", [[1, 2, 3]], ["code"], k=2, max_new=8, seed=1, eos_id=EOS, make_params=_params, dump_path=path)
    recs = st.load_dump(path)
    assert recs and all({"format", "prompt_idx", "prompt_len", "ids", "lp_q", "top1_q", "category"} <= set(r) for r in recs)


# ---- the dense check -------------------------------------------------------------------------------------------
def _header(layers, packed=True, drop=None):
    ts = {"model.embed_tokens.weight": "BF16", "model.norm.weight": "BF16"}
    names = ["self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj"]
    for i in range(layers):
        for n in names:
            if (i, n) == drop:
                ts[f"model.layers.{i}.{n}.weight"] = "BF16"                         # silently skipped
            elif packed:
                ts[f"model.layers.{i}.{n}.weight_packed"] = "I32"; ts[f"model.layers.{i}.{n}.weight_scale"] = "BF16"
            else:
                ts[f"model.layers.{i}.{n}.weight"] = "BF16"
    return ts


def test_dense_check_passes_when_every_linear_is_packed():
    info = cd.check(_header(3), layers=3)
    assert info["packed"] == info["expected_linears"] == 21 and not cd.problems(info) and info["lm_head"].startswith("absent")


def test_dense_check_catches_a_skipped_layer_and_an_unquantized_model():
    bad = cd.problems(cd.check(_header(3, drop=(1, "mlp.up_proj")), layers=3))
    assert any("20 decoder linears are packed" in b for b in bad) and any("unpacked" in b for b in bad)
    assert cd.problems(cd.check(_header(3, packed=False), layers=3))


def test_dense_check_reads_a_safetensors_header(tmp_path):
    hdr = {k: {"dtype": v, "shape": [1], "data_offsets": [0, 0]} for k, v in _header(2).items()}
    blob = json.dumps(hdr).encode()
    (tmp_path / "model.safetensors").write_bytes(struct.pack("<Q", len(blob)) + blob)
    assert cd.check(cd.tensors(tmp_path), layers=2)["packed"] == 14
    with pytest.raises(SystemExit):
        cd.tensors(tmp_path / "nowhere")
