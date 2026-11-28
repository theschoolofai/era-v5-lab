"""models.gpt.document_mask (Lab 5 design 3): a packed row with the document mask computes each document exactly as
if it ran alone, in fp64 (logits, loss and every gradient); one document per row is the plain causal model."""
import pytest
import torch
import torch.nn.functional as F

from models.config import ModelConfig
from models.gpt import GPT, IGNORE_INDEX, document_mask, document_positions

V, T = 97, 24
DOCS = (7, 11, 6)                       # three documents filling one row of T = 24


def _model(**kw):
    torch.manual_seed(0)
    cfg = dict(vocab_size=V, block_size=T, n_layer=2, n_head=2, n_embd=32, attn_impl="eager", reversible=False)
    cfg.update(kw)
    return GPT(ModelConfig(**cfg)).double()


def _doc_ids(lengths):
    return torch.cat([torch.full((n,), i) for i, n in enumerate(lengths)])[None]


def _targets(idx, lengths):
    """Next token inside each document; a document's last position has no target (IGNORE)."""
    y = torch.full_like(idx, IGNORE_INDEX)
    s = 0
    for n in lengths:
        y[0, s:s + n - 1] = idx[0, s + 1:s + n]
        s += n
    return y


@pytest.mark.parametrize("kw", [{}, {"position": "rope", "rope_theta": 10000.0}, {"reversible": True}],
                         ids=["learned", "rope", "reversible"])
def test_packed_row_equals_documents_alone(kw):
    torch.manual_seed(1)
    idx = torch.randint(0, V, (1, T))
    model = _model(**kw)
    y = _targets(idx, DOCS)
    with document_mask(_doc_ids(DOCS)):
        logits, _ = model(idx)
        packed = F.cross_entropy(logits.reshape(T, V), y.reshape(T), ignore_index=IGNORE_INDEX, reduction="sum")
        packed.backward()
    g_packed = {n: p.grad.clone() for n, p in model.named_parameters() if p.grad is not None}
    model.zero_grad()

    alone, s, parts = 0.0, 0, []
    for n in DOCS:
        li, _ = model(idx[:, s:s + n])
        parts.append(li)
        yi = y[:, s:s + n]
        alone = alone + F.cross_entropy(li.reshape(n, V), yi.reshape(n), ignore_index=IGNORE_INDEX, reduction="sum")
        s += n
    alone.backward()
    torch.testing.assert_close(logits, torch.cat(parts, dim=1), rtol=1e-10, atol=1e-10)
    torch.testing.assert_close(packed, alone, rtol=1e-10, atol=1e-10)
    # RoPE tables are built in fp32, so the same relative offset at another absolute position differs in the last
    # bits: about 1e-9 on gradients of order 1 (rope only; learned and reversible agree to 1e-10).
    atol = 1e-8 if kw.get("position") == "rope" else 1e-10
    for n, p in model.named_parameters():
        if n in g_packed:
            torch.testing.assert_close(g_packed[n], p.grad, rtol=1e-8, atol=atol, msg=n)


def test_one_document_is_plain_causal():
    idx = torch.randint(0, V, (2, T))
    model = _model()
    plain, _ = model(idx)
    with document_mask(torch.zeros(2, T, dtype=torch.long)):
        masked, _ = model(idx)
    assert torch.equal(plain, masked)


def test_without_the_mask_documents_leak():
    """Control: packing without the mask is not the same as the documents alone (the study's third arm)."""
    torch.manual_seed(1)
    idx = torch.randint(0, V, (1, T))
    model = _model()
    nomask, _ = model(idx)
    with document_mask(_doc_ids(DOCS)):
        masked, _ = model(idx)
    n0 = DOCS[0]
    assert torch.equal(nomask[:, :n0], masked[:, :n0])           # the first document has nothing before it
    assert not torch.allclose(nomask[:, n0:], masked[:, n0:])


def test_document_positions():
    d = torch.tensor([[0, 0, 0, 1, 1, 2, 2, 2, 2]])
    assert document_positions(d).tolist() == [[0, 1, 2, 0, 1, 0, 1, 2, 3]]


@pytest.mark.parametrize("kw", [{}, {"n_kv_head": 1}, {"position": "rope", "rope_theta": 10000.0}],
                         ids=["mha", "gqa", "rope"])
def test_sdpa_mask_equals_eager_mask(kw):
    """sdpa with the explicit boolean mask computes what eager computes: logits and every gradient, fp64."""
    torch.manual_seed(1)
    idx = torch.randint(0, V, (2, T))
    docs = torch.stack([_doc_ids(DOCS)[0], _doc_ids((T,))[0]])     # row 0 packed, row 1 a single document
    y = torch.cat([_targets(idx[:1], DOCS), _targets(idx[1:], (T,))])
    out = {}
    for impl in ("eager", "sdpa"):
        model = _model(attn_impl=impl, **kw)
        with document_mask(docs):
            logits, loss = model(idx, y)
            loss.backward()
        out[impl] = logits, {n: p.grad for n, p in model.named_parameters() if p.grad is not None}
    torch.testing.assert_close(out["sdpa"][0], out["eager"][0], rtol=1e-10, atol=1e-10)
    assert out["sdpa"][1].keys() == out["eager"][1].keys()
    for n in out["eager"][1]:
        torch.testing.assert_close(out["sdpa"][1][n], out["eager"][1][n], rtol=1e-8, atol=1e-10, msg=n)


@pytest.mark.parametrize("impl", ["eager", "sdpa"])
def test_890_format_with_padding_and_pos_ids(impl):
    """#890 rows: doc_ids 1, 2, ... per window and 0 on the padding at the end, explicit pos_ids. Every real position
    equals its document alone, and no output is NaN (padding attends to padding)."""
    torch.manual_seed(1)
    lengths, pad = (7, 11), T - 18
    idx = torch.randint(0, V, (1, T))
    doc_ids = torch.cat([torch.full((7,), 1), torch.full((11,), 2), torch.zeros(pad, dtype=torch.long)])[None]
    pos_ids = torch.cat([torch.arange(7), torch.arange(11), torch.zeros(pad, dtype=torch.long)])[None]
    model = _model(attn_impl=impl)
    with document_mask(doc_ids.int(), pos_ids.int()):             # #890 stores both as int32
        logits, _ = model(idx)
    assert not logits.isnan().any()
    s = 0
    for n in lengths:
        alone, _ = model(idx[:, s:s + n])
        torch.testing.assert_close(logits[:, s:s + n], alone, rtol=1e-10, atol=1e-10)
        s += n


def test_mtp_target_does_not_cross_documents():
    """mtp: the t+2 target of a document's last positions would come from the next document; it is ignored, so the
    packed mtp loss equals the documents alone (count-weighted means)."""
    torch.manual_seed(1)
    idx = torch.randint(0, V, (1, T))
    y = _targets(idx, DOCS)
    model = _model(mtp=True)
    with document_mask(_doc_ids(DOCS)):
        model(idx, y)
    packed = model.loss_parts["mtp"]
    d = _doc_ids(DOCS)
    ym = y[:, 1:].masked_fill(d[:, 1:] != d[:, :-1], IGNORE_INDEX)
    total, count, s = 0.0, 0, 0
    for n in DOCS:
        model(idx[:, s:s + n], y[:, s:s + n])
        k = int((y[:, s + 1:s + n] != IGNORE_INDEX).sum())
        total, count, s = total + model.loss_parts["mtp"] * k, count + k, s + n
    assert count == int((ym != IGNORE_INDEX).sum())
    # the loss reads fp32 logits (_ce_input), so the means agree to fp32 rounding, not fp64
    torch.testing.assert_close(packed.double(), (total / count).double(), rtol=1e-6, atol=0)


def test_needs_eager_or_sdpa_and_matching_shape():
    idx = torch.randint(0, V, (1, T))
    with document_mask(_doc_ids(DOCS)), pytest.raises(ValueError, match="eager or sdpa"):
        _model(attn_impl="triton")(idx)
    with document_mask(torch.zeros(1, T - 1, dtype=torch.long)), pytest.raises(ValueError, match="doc_ids"):
        _model()(idx)
    with document_mask(_doc_ids(DOCS), torch.zeros(1, T - 1, dtype=torch.long)), pytest.raises(ValueError,
                                                                                                 match="pos_ids"):
        _model()(idx)
