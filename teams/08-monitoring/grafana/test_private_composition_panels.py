"""Private panels 35-37: native Indic share, lane shares, and data position next to the loss (Week 5)."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys
import urllib.parse
import urllib.request
import uuid

import pytest

HERE = Path(__file__).resolve().parent
PRIVATE_JSON = HERE / "private_v1.json"
INDIC, LANES, POSITION = 35, 36, 37


def _panels():
    return {p["id"]: p for p in json.loads(PRIVATE_JSON.read_text(encoding="utf-8"))["panels"]}


def _sql(pid):
    return _panels()[pid]["targets"][0]["rawSql"]


def test_panels_exist_with_unique_ids_and_read_metrics_raw():
    d = json.loads(PRIVATE_JSON.read_text(encoding="utf-8"))
    ids = [p["id"] for p in d["panels"]]
    assert len(ids) == len(set(ids))
    for pid in (INDIC, LANES, POSITION):
        p = _panels()[pid]
        assert p["type"] == "trend" and p["options"]["xField"] == "step"
        assert "FROM metrics_raw" in p["targets"][0]["rawSql"] and "run_id IN ($run)" in p["targets"][0]["rawSql"]
        assert p["options"]["legend"]["calcs"] == ["lastNotNull", "min", "max", "mean"]  # V4: current, min, max, mean


def test_indic_panel_band_matches_the_alarm():
    p = _panels()[INDIC]
    steps = p["fieldConfig"]["defaults"]["thresholds"]["steps"]
    assert [s["value"] for s in steps] == [None, 0.07, 0.09]  # 8% +/- 1 point, alarms.py rule 8 defaults
    assert "ROWS BETWEEN 49 PRECEDING AND CURRENT ROW" in p["targets"][0]["rawSql"]  # the alarm's 50-batch window
    assert p["fieldConfig"]["defaults"]["unit"] == "percentunit"


def test_position_panel_uses_the_bits_per_byte_formula():
    sql = _sql(POSITION)
    assert ("sumIf(value, name = 'train/ce_loss') * sumIf(value, name = 'train/scored_tokens') / "
            "(sumIf(value, name = 'train/utf8_bytes') * ln(2))") in sql
    assert "name = 'data_tokens_seen'" in sql


def _ch(sql: str, data: bytes | None = None) -> str:
    url = "http://127.0.0.1:8123/?" + urllib.parse.urlencode({"query": sql})
    with urllib.request.urlopen(urllib.request.Request(url, data=data or b"", method="POST"), timeout=10) as r:
        return r.read().decode("utf-8")


def _ch_up() -> bool:
    try:
        return _ch("SELECT 1").strip() == "1"
    except Exception:
        return False


@pytest.mark.skipif(not _ch_up(), reason="ClickHouse server is not reachable on 127.0.0.1:8123")
def test_panel_sql_on_clickhouse():
    sys.path.insert(0, str(HERE.parent / "clickhouse"))
    from load_jsonl import ensure_schema
    ensure_schema()
    run = f"test-comp-{uuid.uuid4().hex[:8]}"
    rows = []
    for step in range(1, 61):
        share = 0.08 if step <= 50 else 0.0
        for name, value in (("indic_share", share), ("lane_share_tokens.english", 1 - share),
                            ("lane_share_tokens.indic", share), ("data_tokens_seen", 100.0 * step),
                            ("train/ce_loss", 2.0), ("train/scored_tokens", 90.0), ("train/utf8_bytes", 400.0)):
            rows.append({"run_id": run, "step": step, "time": "2026-11-28 00:00:00.000", "name": name, "value": value})
    try:
        _ch("INSERT INTO metrics_raw FORMAT JSONEachRow", "\n".join(map(json.dumps, rows)).encode())

        def query(pid):
            out = _ch(_sql(pid).replace("$run", f"'{run}'") + " FORMAT JSONEachRow")
            return [(int(r["step"]), r["series"], float(r["value"])) for r in map(json.loads, out.strip().splitlines())]

        indic = query(INDIC)
        mean = {s: v for s, name, v in indic if name.endswith("50-batch mean (alarm)")}
        assert math.isclose(mean[50], 0.08) and math.isclose(mean[60], 40 * 0.08 / 50)  # 10 zero batches in the window
        assert {name for _, name, _ in query(LANES)} == {f"{run} english", f"{run} indic"}
        pos = query(POSITION)
        bpb = [v for _, name, v in pos if name.endswith("training bits per byte")]
        assert len(bpb) == 60 and all(math.isclose(v, 2.0 * 90 / (400 * math.log(2))) for v in bpb)
        seen = {s: v for s, name, v in pos if name.endswith("tokens seen")}
        assert seen[60] == 6000.0
    finally:
        _ch(f"ALTER TABLE metrics_raw DELETE WHERE run_id = '{run}' SETTINGS mutations_sync = 2")
