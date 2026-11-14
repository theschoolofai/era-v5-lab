"""LabLM checks with a stub model (no checkpoint, tokenizer or dataset needed): run with
    pytest teams/09-evaluation/harness_lab/tests -q

The stub's hidden state at position t is the mean of the embeddings of tokens 0..t, so it is causal like Team 5's model,
and right padding cannot change a real position.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lm_eval_lab import LabLM  # noqa: E402

V = 64


class StubArtifacts:
    bos_id, pad_id = 1, 0

    def encode(self, text):
        return [2 + b % (V - 2) for b in text.encode("utf-8")]

    tokenizer = SimpleNamespace(encode=lambda text, add_special_tokens=False: SimpleNamespace(ids=[]))


class StubModel(nn.Module):
    def __init__(self):
        super().__init__()
        torch.manual_seed(0)
        self.emb = nn.Embedding(V, 16)
        self.head = nn.Linear(16, V, bias=False)

    def hidden(self, ids, valid):
        e = self.emb(ids) * valid[..., None]
        steps = torch.arange(1, ids.shape[1] + 1, dtype=e.dtype)[None, :, None]
        return e.cumsum(1) / steps


@torch.no_grad()
def manual(model, art, context, continuation, block):
    n = len(context) - len(context.rstrip())
    if n:
        continuation, context = context[-n:] + continuation, context[:-n]
    ctx = art.encode(context) if context else []
    cont = art.encode(context + continuation)[len(ctx):]
    toks = ([art.bos_id] + ctx + cont)[-(block + 1):]
    x = torch.tensor([toks[:-1]])
    logp = torch.log_softmax(model.head(model.hidden(x, torch.ones_like(x, dtype=torch.bool)))[0], -1)
    m = len(cont)
    targets = torch.tensor(toks[-m:])
    return float(logp[-m:].gather(1, targets[:, None]).sum())


PAIRS = [("Question: 2+2=", " 4"), ("Short", " answer that is longer"), ("Trailing space ", "moves"), ("", "empty context")]


@pytest.mark.parametrize("budget", [8, 100000])
def test_matches_manual_sum_and_batching(budget):
    model, art = StubModel().eval(), StubArtifacts()
    lm = LabLM(model, art, block_size=512, device=torch.device("cpu"), bf16=False, max_batch_tokens=budget)
    got = lm.loglikelihood([SimpleNamespace(args=p) for p in PAIRS], disable_tqdm=True)
    for (ctx, cont), (lp, _) in zip(PAIRS, got):
        assert lp == pytest.approx(manual(model, art, ctx, cont, 512), abs=1e-4)


def test_left_truncation_keeps_the_continuation():
    model, art = StubModel().eval(), StubArtifacts()
    lm = LabLM(model, art, block_size=8, device=torch.device("cpu"), bf16=False)
    (lp, _), = lm.loglikelihood([SimpleNamespace(args=("a long context of many bytes", " end"))], disable_tqdm=True)
    assert lp == pytest.approx(manual(model, art, "a long context of many bytes", " end", 8), abs=1e-4)


def test_same_numbers_twice():
    model, art = StubModel().eval(), StubArtifacts()
    lm = LabLM(model, art, block_size=512, device=torch.device("cpu"), bf16=False)
    reqs = [SimpleNamespace(args=p) for p in PAIRS]
    assert lm.loglikelihood(reqs, disable_tqdm=True) == lm.loglikelihood(reqs, disable_tqdm=True)


def test_generation_is_refused():
    lm = LabLM(StubModel(), StubArtifacts(), block_size=16, device=torch.device("cpu"), bf16=False)
    with pytest.raises(NotImplementedError):
        lm.generate_until([])
