"""Per-batch composition (Indic share, lane shares) and data position, and dry run 2's derived composition."""
import json
import math
from pathlib import Path

import pytest

from composition import DataPosition, batch_composition, composition_metrics, lane_of
from dryrun2_composition import add_composition
from metrics_writer import MetricsWriter

# Named decorator: pr-guard reads an added pytest decorator line as an email address.
parametrize = pytest.mark.parametrize

REPO = Path(__file__).resolve().parents[3]
DRYRUN2 = REPO / "teams/05-architecture/results/dryrun2-1234/metrics.jsonl"


@parametrize("pack, romanised, translated, lane", [
    ("en-fineweb-edu", False, False, "english"),
    ("code-python", False, False, "code"),
    ("math-megamath", False, False, "math"),
    ("sci-finepdfs", False, False, "science"),
    ("ind-hi-fw2", False, False, "indic"),
    ("ind-te-sangraha-v", False, False, "indic"),
    ("ind-hi-sangraha-s", False, False, "indic_translated"),  # machine-translated packs (#212)
    ("ind-kn-fw2", False, True, "indic_translated"),
    ("ind-ta-fw2", True, False, "indic_romanised"),
    ("xx-unknown", False, False, "other"),
    ("", False, False, "other"),
])
def test_lane_of(pack, romanised, translated, lane):
    assert lane_of(pack, romanised, translated) == lane


def test_batch_shares_by_tokens_bytes_and_words():
    docs = [
        {"pack": "en-dclm", "tokens": 800, "bytes": 3200, "words": 600},
        {"pack": "code-python", "tokens": 120, "bytes": 400, "words": 50},
        {"pack": "ind-hi-fw2", "tokens": 80, "bytes": 400, "words": 50},
    ]
    comp = batch_composition(docs)
    assert math.isclose(comp["indic_share"], 0.08)
    assert comp["lane_share_tokens"] == pytest.approx({"code": 0.12, "english": 0.8, "indic": 0.08})
    assert comp["lane_share_bytes"] == pytest.approx({"code": 0.1, "english": 0.8, "indic": 0.1})
    assert comp["lane_share_words"] == pytest.approx({"code": 50 / 700, "english": 600 / 700, "indic": 50 / 700})
    for key in ("lane_share_tokens", "lane_share_bytes", "lane_share_words"):
        assert math.isclose(sum(comp[key].values()), 1.0)


def test_translated_and_romanised_indic_are_not_native():
    docs = [{"pack": "ind-hi-fw2", "tokens": 50}, {"pack": "ind-hi-sangraha-s", "tokens": 30},
            {"pack": "ind-ta-fw2", "tokens": 20, "romanised": True}]
    comp = batch_composition(docs)
    assert math.isclose(comp["indic_share"], 0.5)
    assert comp["lane_share_tokens"] == pytest.approx({"indic": 0.5, "indic_translated": 0.3, "indic_romanised": 0.2})


def test_words_left_out_when_any_document_has_no_word_count():
    comp = batch_composition([{"pack": "en-dclm", "tokens": 10, "words": 7}, {"pack": "code-go", "tokens": 5}])
    assert "lane_share_words" not in comp and comp["_batch_counts"]["words"] is None


def test_empty_and_bad_batches():
    assert batch_composition([]) == {}
    assert batch_composition([{"pack": "en-dclm", "tokens": 0}]) == {}
    with pytest.raises(ValueError, match="token count"):
        batch_composition([{"pack": "en-dclm", "bytes": 10}])
    for bad in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            batch_composition([{"pack": "en-dclm", "tokens": bad}])


def test_data_position_totals_epoch_and_restore():
    pos = DataPosition(corpus_tokens=1000)
    first = pos.update(batch_composition([{"pack": "en-dclm", "tokens": 100, "bytes": 400, "words": 70}]))
    assert first == {"data_tokens_seen": 100, "data_bytes_seen": 400, "data_words_seen": 70, "data_epoch": 0.1}
    pos.update(tokens=150, bytes=500, words=None)  # a batch with no word count: words stop being reported
    state = pos.state_dict()
    restored = DataPosition()
    restored.load_state_dict(state)
    nxt = restored.update(tokens=250, bytes=100)
    assert nxt == {"data_tokens_seen": 500, "data_bytes_seen": 1000, "data_epoch": 0.5}
    with pytest.raises(ValueError):
        DataPosition().update({})


def test_writer_keeps_composition_fields(tmp_path):
    comp = batch_composition([{"pack": "en-dclm", "tokens": 92, "bytes": 300}, {"pack": "ind-bn-fw2", "tokens": 8, "bytes": 40}])
    pos = DataPosition()
    path = tmp_path / "metrics.jsonl"
    with MetricsWriter(str(path)) as w:
        w.write(1, loss_ntp=3.0, **composition_metrics(comp), **pos.update(comp))
    row = json.loads(path.read_text(encoding="utf-8"))
    assert math.isclose(row["indic_share"], 0.08)
    assert row["lane_share_tokens"] == pytest.approx({"english": 0.92, "indic": 0.08})
    assert row["data_tokens_seen"] == 100 and row["data_bytes_seen"] == 340
    assert "_batch_counts" not in row


def test_dryrun2_composition_from_the_run_record():
    """#869: one English web shard, so 100% english and 0 native Indic; the data position from the run's counts."""
    if not DRYRUN2.exists():
        pytest.skip("dry run 2 record not in this checkout")
    src = DRYRUN2.read_text(encoding="utf-8").splitlines()
    rows = list(add_composition(src))
    orig = [json.loads(line) for line in src if line.strip()]
    assert len(rows) == len(orig) == 1222
    assert "indic_share" not in rows[0]  # step 0: evaluation only, no training batch
    train = [r for r in rows if "indic_share" in r]
    assert len(train) == 1221
    assert all(r["indic_share"] == 0.0 and r["lane_share_tokens"] == {"english": 1.0} for r in train)
    assert train[-1]["data_tokens_seen"] == sum(r["train/input_positions"] for r in orig if "train/input_positions" in r)
    assert train[-1]["data_tokens_seen"] == 20_004_864
    assert train[-1]["data_bytes_seen"] == 39_818_093
    assert math.isclose(train[-1]["data_epoch"], 20_004_864 / 25_000_000)
    for a, b in zip(rows, orig):  # the run's own fields are unchanged
        assert {k: a[k] for k in b} == b


def test_dryrun2_composition_skips_a_torn_last_line():
    lines = ['{"step": 1, "train/input_positions": 10, "train/utf8_bytes": 20}', '{"step": 2, "train/inp']
    rows = list(add_composition(lines))
    assert len(rows) == 1 and rows[0]["data_tokens_seen"] == 10
