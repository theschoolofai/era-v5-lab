"""Per-batch data composition and data position, logged next to the loss (Week 5, Team 08 task 1).

What each batch is made of, as shares of the batch, and how far the run is into its data:

- `indic_share`: the **native-script Indic** share of the batch's tokens. Team 02's rule
  (`teams/02-data-b/mix/indic_share_v1.md`): native Indic is a fixed 8% of every batch. Translated packs
  (`ind-<lang>-sangraha-s`, #212) and romanised Indic documents do not count as native.
- `lane_share_tokens`, `lane_share_bytes`, `lane_share_words`: {lane: share} of the batch, by tokens, UTF-8 bytes and
  words. The shares of one batch add up to 1. Words are counted only when every document gives a word count.
- `data_tokens_seen`, `data_bytes_seen`, `data_words_seen`, `data_docs_seen`: running totals of what the run has trained
  on so far: the data position. `data_epoch` is `data_tokens_seen` / the corpus size, when the caller gives it.

A lane is read from the pack id (Team 01's naming, e.g. `en-fineweb-edu`, `code-python`, `math-megamath`,
`sci-finepdfs`, `ind-hi-fw2`):

    en-*                -> english        code-*  -> code       math-* -> math       sci-* -> science
    ind-<lang>-*        -> indic          (native script)
    ind-<lang>-sangraha-s, or a document marked translated  -> indic_translated
    a document marked romanised (script Latin)               -> indic_romanised
    anything else                                            -> other

Usage in the training loop, one call per optimizer step with the documents (or document pieces) of the batch:

    position = DataPosition(corpus_tokens=...)
    comp = batch_composition(docs)   # docs: [{"pack": "ind-hi-fw2", "tokens": 812, "bytes": 2203, "words": 390}, ...]
    writer.write(step, loss_ntp=..., **composition_metrics(comp), **position.update(comp))
"""
from __future__ import annotations

import math

LANES = ("english", "code", "math", "science", "indic", "indic_romanised", "indic_translated", "other")
_PREFIX_LANE = {"en": "english", "code": "code", "math": "math", "sci": "science"}
TRANSLATED_PACK_SUFFIX = "-sangraha-s"


def lane_of(pack: str, romanised: bool = False, translated: bool = False) -> str:
    """The lane of one document, from its pack id and its romanised / translated marks."""
    pack = (pack or "").strip().lower()
    prefix = pack.split("-", 1)[0]
    if prefix == "ind":
        if translated or pack.endswith(TRANSLATED_PACK_SUFFIX):
            return "indic_translated"
        if romanised:
            return "indic_romanised"
        return "indic"
    return _PREFIX_LANE.get(prefix, "other")


def _count(doc: dict, key: str):
    v = doc.get(key)
    if v is None or isinstance(v, bool):
        return None
    if hasattr(v, "item"):  # numpy / torch scalar
        v = v.item()
    v = float(v)
    if not math.isfinite(v) or v < 0:
        raise ValueError(f"{key} must be a finite count >= 0, got {doc.get(key)!r}")
    return v


def batch_composition(docs) -> dict:
    """Composition metrics of one batch; {} when the batch has no tokens.

    Each doc is a dict with `pack` and `tokens` (required), `bytes` and `words` (optional), `romanised` and
    `translated` (optional booleans). A packed sequence that holds pieces of several documents is passed as one entry
    per piece, with the piece's own counts.
    """
    totals = {"tokens": {}, "bytes": {}, "words": {}}
    words_complete = True
    for doc in docs:
        lane = lane_of(doc.get("pack", ""), bool(doc.get("romanised")), bool(doc.get("translated")))
        for key in ("tokens", "bytes", "words"):
            n = _count(doc, key)
            if n is None:
                if key == "tokens":
                    raise ValueError("every document needs a token count")
                if key == "words":
                    words_complete = False
                continue
            totals[key][lane] = totals[key].get(lane, 0.0) + n
    all_tokens = sum(totals["tokens"].values())
    if all_tokens <= 0:
        return {}
    out = {
        "indic_share": totals["tokens"].get("indic", 0.0) / all_tokens,
        "lane_share_tokens": {lane: n / all_tokens for lane, n in sorted(totals["tokens"].items())},
    }
    all_bytes = sum(totals["bytes"].values())
    if all_bytes > 0:
        out["lane_share_bytes"] = {lane: n / all_bytes for lane, n in sorted(totals["bytes"].items())}
    all_words = sum(totals["words"].values())
    if words_complete and all_words > 0:
        out["lane_share_words"] = {lane: n / all_words for lane, n in sorted(totals["words"].items())}
    # Batch totals, used by DataPosition; not written as metrics themselves.
    out["_batch_counts"] = {"tokens": all_tokens, "bytes": all_bytes, "docs": None,
                            "words": all_words if words_complete else None}
    return out


class DataPosition:
    """Running totals of the data the run has trained on (the data position), to log next to the loss.

    `update()` takes the counts of one batch and returns the new totals. A run restored from a checkpoint passes the
    totals saved with it (`state_dict()` / `load_state_dict()`), so the position does not restart from zero.
    """

    def __init__(self, corpus_tokens=None):
        self.corpus_tokens = float(corpus_tokens) if corpus_tokens else None
        self.tokens = 0.0
        self.bytes = 0.0
        self.words = 0.0
        self.docs = 0
        self._words_complete = True

    def update(self, comp_or_counts=None, *, tokens=None, bytes=None, words=None, docs=None) -> dict:
        counts = dict((comp_or_counts or {}).get("_batch_counts") or {})
        for key, val in (("tokens", tokens), ("bytes", bytes), ("words", words), ("docs", docs)):
            if val is not None:
                counts[key] = val
        if counts.get("tokens") is None:
            raise ValueError("a batch token count is needed to move the data position")
        self.tokens += float(counts["tokens"])
        self.bytes += float(counts.get("bytes") or 0.0)
        if counts.get("words") is None:
            self._words_complete = False
        else:
            self.words += float(counts["words"])
        if counts.get("docs") is not None:
            self.docs += int(counts["docs"])
        out = {"data_tokens_seen": self.tokens, "data_bytes_seen": self.bytes}
        if self._words_complete:
            out["data_words_seen"] = self.words
        if self.docs:
            out["data_docs_seen"] = self.docs
        if self.corpus_tokens:
            out["data_epoch"] = self.tokens / self.corpus_tokens
        return out

    def state_dict(self) -> dict:
        return {"tokens": self.tokens, "bytes": self.bytes, "words": self.words, "docs": self.docs,
                "words_complete": self._words_complete, "corpus_tokens": self.corpus_tokens}

    def load_state_dict(self, state: dict) -> None:
        self.tokens = float(state.get("tokens", 0.0))
        self.bytes = float(state.get("bytes", 0.0))
        self.words = float(state.get("words", 0.0))
        self.docs = int(state.get("docs", 0))
        self._words_complete = bool(state.get("words_complete", True))
        if state.get("corpus_tokens"):
            self.corpus_tokens = float(state["corpus_tokens"])


def composition_metrics(comp: dict) -> dict:
    """The writable part of batch_composition()'s result (drops the internal batch counts)."""
    return {k: v for k, v in comp.items() if not k.startswith("_")}
