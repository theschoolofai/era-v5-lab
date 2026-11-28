"""KAS V2 output head (Team 4's public #765 contract), Team 6's single copy for model.head_mode = "kas_v2".

Provenance: copied without maths changes from Team 5's harness at class main 61f0a3ae (#717, "G5: integrate untied
KAS V2 codec and output head"):
  teams/05-architecture/harness/week2/kas_v2.py    sha256 a98725c96576298517489dbcd0ff970aebc5ba18659d32d2ce6e6fd3630eca4b
      checked_rows, KASCodec, KASHead, initialize_prior
  teams/05-architecture/harness/week2/kas_terms.py sha256 03baf69cc14fe6bd16929a12d0b9ae5f86e2685503d8b976406baee8308894ac
      initialize_unigram_, correction_row_dropout
  teams/05-architecture/harness/week2/unigram.py   sha256 27e2d3680a7cc344843704868b1b9dafae2d20ee767819a8d57c492825f05da4
      UnigramCounts, load_counts, additive_log_prior
Differences from the source, all outside the maths:
  * one file; TEAMS is parents[2] (teams/06-performance/models/kas_v2.py) instead of parents[3];
  * KASInput (the KAS input embedding) and checkpoint_probe are not copied: Lab 5 task 1(a) swaps the head only;
  * load_kas_table() is new: the frozen p1536 raw byte table from Team 4 (teams/04-ke2/results/tables/p1536-s0),
    hash-checked by Team 4's ByteTable, as the (rows, lengths) the head needs. Team 5 builds the same rows from the
    tokenizer JSON (harness/week2/artifacts.py).
The head returns [N, V] logits as a transposed view (embedding_bag(...).t()); GPT makes them contiguous before the loss.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

TEAMS = Path(__file__).resolve().parents[2]
FIXTURE = TEAMS / "04-ke2/fixtures/kas_v2/kas_v2_fixture.npz"
FIXTURE_SHA = "1d77a48ed3fc1e2609dcb9eb91a2036f9ca773613f7a4b4be45d4c198b7cd50f"
COUNTS_SHA = "0768b5982825645a796abc76ec23c737837cfacc8f6b089335e5ce5446def3a6"
TOKENIZER_SHA = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"   # frozen p1536-s0
TABLE = TEAMS / "04-ke2/results/tables/p1536-s0/raw_table_P32.npz"


def load_kas_table(vocab_size: int):
    """Team 4's frozen p1536 raw byte table as (rows [V, 32] uint8, lengths [V] int64), content- and tokenizer-checked."""
    src = TEAMS / "04-ke2" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from ke2.tables import ByteTable

    table = ByteTable.load(TABLE, tokenizer_sha256=TOKENIZER_SHA)
    if table.vocab_size != vocab_size:
        raise ValueError(f"KAS byte table has {table.vocab_size} rows, model.vocab_size is {vocab_size}")
    return torch.from_numpy(table.bytes.copy()), torch.from_numpy(table.lengths.astype("int64"))


# ---- teams/05-architecture/harness/week2/kas_v2.py ----

def checked_rows(rows, lengths):
    rows = torch.as_tensor(rows).clone()
    lengths = torch.as_tensor(lengths).clone()
    if rows.dtype != torch.uint8 or lengths.is_floating_point() or lengths.dtype == torch.bool:
        raise ValueError("KAS needs raw uint8 bytes and integer lengths")
    lengths = lengths.long()
    if rows.ndim != 2 or rows.shape[1] > 32 or lengths.shape != (len(rows),):
        raise ValueError("KAS requires a byte table with at most 32 positions and one length per ID")
    if bool(((lengths <= 0) | (lengths > rows.shape[1])).any()):
        raise ValueError("KAS token lengths must be in [1, 32] without truncation")
    return rows, lengths


class KASCodec(nn.Module):
    """Fixed public G/Phi constants; canonical construction uses float64."""

    def __init__(self):
        super().__init__()
        if hashlib.sha256(FIXTURE.read_bytes()).hexdigest() != FIXTURE_SHA:
            raise ValueError("KAS V2 public fixture hash mismatch")
        with np.load(FIXTURE, allow_pickle=False) as source:
            self.register_buffer("G", torch.from_numpy(source["G"].copy()))
            self.register_buffer("Phi", torch.from_numpy(source["Phi"].copy()))

    def _apply(self, fn, recurse=True):
        # Model precision conversion must preserve the exact fixed codebook.
        original = {name: value for name, value in self._buffers.items()}
        super()._apply(fn, recurse=recurse)
        for name, value in original.items():
            self._buffers[name] = value.to(device=self._buffers[name].device, dtype=torch.float64)
        return self

    def positions(self, rows, lengths):
        p = rows.shape[-1]
        valid = torch.arange(p, device=rows.device) < lengths[..., None]
        values = self.G[rows.long()] * valid[..., None]
        values = values / lengths.double().sqrt()[..., None, None]
        return F.pad(values.transpose(-1, -2), (0, 32 - p))

    def codes(self, rows, lengths):
        # Canonical diagnostic/export representation matches the public NumPy
        # fingerprint. Training projects byte occupancy directly on device below.
        shape = rows.shape[:-1]
        raw = rows.detach().cpu().numpy().reshape(-1, rows.shape[-1])
        lens = lengths.detach().cpu().numpy().reshape(-1)
        values = self.G.detach().cpu().numpy()[raw] / np.sqrt(lens)[:, None, None]
        valid = np.arange(raw.shape[1])[None, :] < lens[:, None]
        values = np.where(valid[:, :, None], values, 0.0)
        positions = np.zeros((len(raw), 64, 32), dtype=np.float64)
        positions[:, :, :raw.shape[1]] = values.transpose(0, 2, 1)
        codes = (positions @ self.Phi.detach().cpu().numpy()).reshape(*shape, 2048)
        return torch.from_numpy(codes).to(rows.device)


class KASHead(nn.Module):
    def __init__(self, rows, lengths, width, codec):
        super().__init__()
        rows, lengths = checked_rows(rows, lengths)
        object.__setattr__(self, "codec", codec)
        self.out_features = len(rows)
        self.in_features = width
        self.tok_dropout = 0.05
        self.W_out = nn.Parameter(torch.randn(width, 2048) * 2048 ** -0.5)
        self.beta = nn.Parameter(torch.ones(33))
        self.unigram = nn.Parameter(torch.zeros(len(rows)))
        self.tok_u = nn.Parameter(torch.randn(len(rows), 64) * (0.02 * 64 ** -0.5))
        self.tok_c = nn.Parameter(torch.randn(64, width) * width ** -0.5)
        valid = torch.arange(rows.shape[1])[None, :] < lengths[:, None]
        indices = torch.arange(rows.shape[1])[None, :] * 256 + rows.long()
        self.register_buffer("indices", indices[valid], persistent=False)
        self.register_buffer("offsets", F.pad(lengths.cumsum(0), (1, 0)), persistent=False)
        self.register_buffer("lengths", lengths, persistent=False)
        # Keep canonical double weights for float64 parity and cast at use.
        self.register_buffer("scales", lengths.double().rsqrt().repeat_interleave(lengths), persistent=False)

    def forward(self, hidden):
        shape = hidden.shape[:-1]
        with torch.autocast(device_type=hidden.device.type, enabled=False):
            h = hidden.reshape(-1, self.in_features).to(self.W_out.dtype)
            position_scores = (h @ self.W_out).reshape(-1, 64, 32)
            byte_scores = torch.einsum("ncp,bc->npb", position_scores, self.codec.G.to(h.dtype))
            scores = F.embedding_bag(
                self.indices, byte_scores.flatten(1).t().contiguous(), self.offsets,
                mode="sum", per_sample_weights=self.scales.to(h.dtype), include_last_offset=True,
            ).t()
            correction = correction_row_dropout(self.tok_u, probability=self.tok_dropout, training=self.training)
            logits = scores * self.beta[self.lengths] + self.unigram + (h @ self.tok_c.t()) @ correction.t()
        return logits.reshape(*shape, self.out_features)


def initialize_prior(head, settings):
    """Use the public raw counts unless the config explicitly adapts EOS."""
    defaults = {
        "path": "03-tokenizer/counts/p1536_counts.json",
        "sha256": COUNTS_SHA,
        "tokenizer_sha256": TOKENIZER_SHA,
        "add_eos_per_document": False,
    }
    settings = {**defaults, **settings}
    extra = set(settings) - set(defaults)
    if extra:
        raise ValueError("Unsupported KAS prior settings: " + str(sorted(extra)))
    path = Path(settings["path"])
    if not path.is_absolute():
        path = TEAMS / path
    counts = load_counts(path, expected_sha256=settings["sha256"],
                         expected_tokenizer_sha256=settings["tokenizer_sha256"],
                         expected_vocab_size=head.out_features, checksum_mode="lf")
    return initialize_unigram_(head.unigram, counts, add_eos_per_document=settings["add_eos_per_document"])


# ---- teams/05-architecture/harness/week2/kas_terms.py ----

@torch.no_grad()
def initialize_unigram_(parameter, counts, *, add_eos_per_document):
    """Initialize the trainable float32 head.unigram from verified raw counts.

    Add one to every ID, normalize, log, subtract the vocabulary mean, then store
    float32. Arithmetic before storage uses Python double precision; bitwise
    parity with the pinned implementation's intermediate dtype is not claimed.
    EOS addition is an explicit p1536 adaptation, not a reference default.
    """
    if not isinstance(parameter, torch.nn.Parameter) or not parameter.requires_grad:
        raise ValueError("head.unigram must be a trainable Parameter")
    if parameter.dtype != torch.float32 or tuple(parameter.shape) != (len(counts.counts),):
        raise ValueError("head.unigram must be float32 with one scalar per vocabulary ID")
    values, identity = additive_log_prior(counts, smoothing=1.0,
                                         add_eos_per_document=add_eos_per_document)
    mean = math.fsum(values) / len(values)
    centered = [value - mean for value in values]
    parameter.copy_(torch.tensor(centered, dtype=torch.float32, device=parameter.device))
    return {
        **identity,
        "centering": "subtract_vocabulary_mean",
        "initialization_math_dtype": "float64",
        "storage_dtype": "float32",
        "trainable": True,
    }


def correction_row_dropout(tok_u, *, probability, training, generator=None):
    """Apply inverted row dropout only to the supplied V x rank correction.

    The chosen arm must explicitly pass probability=0.05. One independent mask
    of shape [V, 1] is sampled per invocation; the caller owns invocation timing.
    No per-step caching or microbatch-sharing semantics are asserted here. The
    input parameter is never modified, and eval consumes no RNG. Apply this to
    tok_u only, never to the codec, unigram, output projection or final logits.
    """
    if tok_u.ndim != 2 or not tok_u.is_floating_point():
        raise ValueError("Token correction must be a floating V x rank tensor")
    if type(training) is not bool:
        raise ValueError("Training mode must be boolean")
    if type(probability) not in (int, float) or not math.isfinite(probability) or not 0 <= probability < 1:
        raise ValueError("Dropout probability must be finite in [0, 1)")
    if not training or probability == 0:
        return tok_u
    keep = 1.0 - probability
    mask = torch.rand((tok_u.shape[0], 1), device=tok_u.device, generator=generator) < keep
    return tok_u * mask.to(tok_u.dtype) / keep


# ---- teams/05-architecture/harness/week2/unigram.py ----

def _integer(value, label):
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _digest(value, label):
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{label} must be a lowercase sha256")
    return value


@dataclass(frozen=True)
class UnigramCounts:
    counts: tuple
    documents: int
    eos_id: int
    special_ids: tuple
    file_sha256: str
    tokenizer_sha256: str
    # Immutable source receipts: name, sha256, bytes, documents, tokens.
    sources: tuple
    verified_sha256: str
    checksum_mode: str

    def identity(self):
        return {
            "counts_file_sha256": self.file_sha256,
            "counts_verified_sha256": self.verified_sha256,
            "checksum_mode": self.checksum_mode,
            "tokenizer_sha256": self.tokenizer_sha256,
            "vocab_size": len(self.counts),
            "tokens": sum(self.counts),
            "documents": self.documents,
            "eos_id": self.eos_id,
            "special_ids": list(self.special_ids),
            "sources": {
                name: dict(sha256=sha, bytes=size, docs=docs, tokens=tokens)
                for name, sha, size, docs, tokens in self.sources
            },
        }


def load_counts(path, *, expected_sha256, expected_tokenizer_sha256, expected_vocab_size, checksum_mode="exact"):
    """Load hash-pinned raw counts and verify their summaries/source receipts.

    Exact bytes are checked by default. Explicit checksum_mode="lf" supports
    Git's CRLF checkout conversion for this text JSON artifact. Both the actual
    file digest and verified digest/mode are retained in provenance.
    """
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if checksum_mode not in ("exact", "lf"):
        raise ValueError("Unknown counts checksum mode")
    checked = raw.replace(b"\r\n", b"\n") if checksum_mode == "lf" else raw
    verified = hashlib.sha256(checked).hexdigest()
    if verified != _digest(expected_sha256, "expected counts hash"):
        raise ValueError("Unigram counts file hash mismatch")
    spec = json.loads(raw)
    if spec["tokenizer_sha256"] != _digest(expected_tokenizer_sha256, "expected tokenizer hash"):
        raise ValueError("Unigram counts tokenizer mismatch")
    if type(expected_vocab_size) is not int or expected_vocab_size <= 0:
        raise ValueError("Expected vocabulary size must be a positive integer")
    if type(spec["vocab_size"]) is not int or spec["vocab_size"] != expected_vocab_size:
        raise ValueError("Unigram counts vocabulary mismatch")
    counts = spec["total"]
    if not isinstance(counts, list) or len(counts) != expected_vocab_size:
        raise ValueError("Unigram counts must have one entry per token ID")
    counts = tuple(_integer(n, "Token count") for n in counts)
    specials = spec["special_ids"]
    if not isinstance(specials, list) or any(type(i) is not int or not 0 <= i < len(counts) for i in specials):
        raise ValueError("Invalid special token IDs")
    if len(set(specials)) != len(specials):
        raise ValueError("Duplicate special token IDs")
    eos = spec["eos_id"]
    if type(eos) is not int or eos not in specials:
        raise ValueError("EOS must name a special token ID")
    summary = spec["summary"]
    calculated = {
        "tokens": sum(counts),
        "ids_seen": sum(n > 0 for n in counts),
        "ids_zero": sum(n == 0 for n in counts),
        "special_ids_seen": sum(counts[i] > 0 for i in specials),
    }
    for key, expected in calculated.items():
        if _integer(summary[key], "Summary " + key) != expected:
            raise ValueError("Unigram summary mismatch: " + key)
    docs = _integer(summary["docs"], "Document count")
    sources = []
    for name, source in sorted(spec["sources"].items()):
        sources.append((name, _digest(source["sha256"], "Source hash"),
                        _integer(source["bytes"], "Source bytes"),
                        _integer(source["docs"], "Source documents"),
                        _integer(source["tokens"], "Source tokens")))
    if sum(s[3] for s in sources) != docs or sum(s[4] for s in sources) != sum(counts):
        raise ValueError("Unigram source totals disagree with summary")
    return UnigramCounts(counts, docs, eos, tuple(specials), digest, spec["tokenizer_sha256"],
                         tuple(sources), verified, checksum_mode)


def additive_log_prior(counts, *, smoothing, add_eos_per_document):
    """Return (normalized log probabilities, provenance) for an explicit policy.

    All IDs, including specials, receive the same additive smoothing. There is
    no source reweighting or target masking. EOS correction is applied to a copy
    and refused if the artifact already has EOS counts, to avoid double counting.
    This utility is not a claim about the private reference's implementation.
    """
    if type(smoothing) not in (int, float) or not math.isfinite(smoothing) or smoothing < 0:
        raise ValueError("Smoothing must be finite and nonnegative")
    if type(add_eos_per_document) is not bool:
        raise ValueError("EOS policy must be explicitly true or false")
    adjusted = list(counts.counts)
    if add_eos_per_document:
        if adjusted[counts.eos_id] != 0:
            raise ValueError("Artifact already contains EOS counts; refusing document correction")
        adjusted[counts.eos_id] += counts.documents
    weights = [n + smoothing for n in adjusted]
    if any(n <= 0 or not math.isfinite(n) for n in weights):
        raise ValueError("Every token needs positive finite mass; choose smoothing for zero counts")
    total = math.fsum(weights)
    if not math.isfinite(total):
        raise ValueError("Unigram normalization is nonfinite")
    values = tuple(math.log(n) - math.log(total) for n in weights)
    identity = {
        **counts.identity(),
        "policy": "additive_all_ids",
        "smoothing": smoothing,
        "add_eos_per_document": add_eos_per_document,
        "source_weighting": "raw_total",
    }
    return values, identity
