"""Tests for reconcile_shards.py: the synthetic chain runs through the ledger (fake F2), then a shards folder is written
in shard_writer.py's format (docs.parquet, manifest, quality report, shards_summary.json) from the real final parts, and
broken in each way the reconciliation must catch.

Kept documents of the chain: train code-go/part-00000 g1-g4 (rows 0-3), code-go/part-00001 g5, g6, en-dclm e0, e1;
heldout code-go h0.

  python -m pytest teams/01-data-a/pipeline/tests -q
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from conftest import PIPELINE
import reconcile_shards as rs
import run_pipeline as rp
from test_run_pipeline import config, tsai_outputs  # noqa: F401  (fixtures)


@pytest.fixture
def run(tmp_path, config):
    rp.run(config)
    return tmp_path / "runs" / "test-run"


def write_shards(run, out, drop=(), extra=(), left_out=None, rows_read=None, doc_count=None, packs=None):
    """A shards folder as run_shards.py writes it, from run/final. drop: (input_part, row) to leave out of docs.parquet;
    extra: (shard input_part, doc_id, input_row) rows to add; left_out: {input_part: {reason: [doc_id]}};
    rows_read / doc_count: {input_part: n}; packs: only these packs."""
    out.mkdir(parents=True, exist_ok=True)
    parts = {}
    for f in sorted((run / "final").glob("*/*/*.parquet")):
        split, pack = f.parent.parent.name, f.parent.name
        name = f"{split}/{pack}/{f.name}"
        if packs and pack not in packs:
            continue
        if split == "heldout":
            parts[name] = {"pack_id": pack, "status": "not_sharded", "reason": "held-out"}
            continue
        sid = f"{pack}-{split}-{int(f.stem.split('-')[1]):06d}"
        ids = pq.read_table(f, columns=["doc_id"])["doc_id"].to_pylist()
        gone = {d["doc_id"] if isinstance(d, dict) else d for ids in (left_out or {}).get(name, {}).values() for d in ids}
        rr = (rows_read or {}).get(name, len(ids))
        rows = [{"doc_id": d, "input_part": name, "input_row": i} for i, d in enumerate(ids)
                if i < rr and d not in gone and (name, i) not in drop]
        rows += [{"doc_id": d, "input_part": p, "input_row": r} for p, d, r in extra if p == name]
        pq.write_table(pa.Table.from_pylist(rows, schema=pa.schema([("doc_id", pa.string()), ("input_part", pa.string()),
                                                                     ("input_row", pa.int64())])), out / f"{sid}.docs.parquet")
        (out / f"{sid}.json").write_text(json.dumps({"shard_id": sid, "doc_count": (doc_count or {}).get(name, len(rows))}),
                                         encoding="utf-8")
        (out / f"{sid}.quality_report.json").write_text(json.dumps({
            "shard_id": sid, "rows_read": rr, "left_out_docs": (left_out or {}).get(name, {}),
            "upstream": {"input_part": name}}), encoding="utf-8")
        parts[name] = {"pack_id": pack, "status": "written", "shard_id": sid, "rows_read": rr, "rows_in_part": len(ids),
                       "truncated": rr < len(ids)}
    (out / "shards_summary.json").write_text(json.dumps({"run_id": "test-run", "parts": parts}), encoding="utf-8")
    return out


def statuses(out):
    t = pq.read_table(out / "reconcile_docs.parquet")
    return {(r["input_part"], r["doc_id"]): r["shard_status"] for r in t.to_pylist()}


def test_every_kept_document_is_accounted_for(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", left_out={"train/en-dclm/part-00000.parquet": {"empty": ["e1"]}})
    r = rs.reconcile(run / "ledger", shards, tmp_path / "rec")
    assert r["ok"] and r["kept"] == 9 and r["in_shards"] == 7
    assert r["totals"] == {"in_shard": 7, "left_out:empty": 1, "not_sharded": 1}
    s = statuses(tmp_path / "rec")
    assert s[("train/en-dclm/part-00000.parquet", "e1")] == "left_out:empty"
    assert s[("heldout/code-go/part-00000.parquet", "h0")] == "not_sharded"
    assert s[("train/code-go/part-00001.parquet", "g6")] == "in_shard"
    assert r["by_pack"]["code-go"]["train"] == {"in_shard": 6}
    text = (tmp_path / "rec" / "reconcile_summary.json").read_text(encoding="utf-8")
    assert "synthetic text" not in text


def test_a_dropped_document_in_a_shard_fails(run, tmp_path):
    # g0 was dropped by F2 from code-go/part-00000; a shard claiming it at row 0 names another doc than the ledger's (g1)
    shards = write_shards(run, tmp_path / "shards", drop={("train/code-go/part-00000.parquet", 0)},
                          extra=[("train/code-go/part-00000.parquet", "g0", 0)])
    with pytest.raises(rs.Stop, match="kept document at its ledger position"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")
    assert (tmp_path / "rec" / "reconcile_summary.json").is_file()  # written, to show what failed


def test_a_row_past_the_part_fails(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", extra=[("train/en-dclm/part-00000.parquet", "zz", 9)])
    with pytest.raises(rs.Stop, match="1 shard row\\(s\\) at no kept ledger position"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")


def test_a_document_in_two_shards_fails(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", extra=[("train/en-dclm/part-00000.parquet", "e0", 0)])
    with pytest.raises(rs.Stop, match="two shards"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")


def test_a_truncated_part_fails_as_not_reached(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", rows_read={"train/code-go/part-00000.parquet": 2})
    with pytest.raises(rs.Stop, match="not_reached"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")
    s = statuses(tmp_path / "rec")
    assert s[("train/code-go/part-00000.parquet", "g3")] == "not_reached" and s[("train/code-go/part-00000.parquet", "g2")] == "in_shard"


def test_a_silently_missing_document_fails(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", drop={("train/code-go/part-00001.parquet", 1)})
    with pytest.raises(rs.Stop, match="'missing': 1"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")
    assert statuses(tmp_path / "rec")[("train/code-go/part-00001.parquet", "g6")] == "missing"


def test_a_left_out_document_that_is_not_kept_fails(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", left_out={"train/code-go/part-00000.parquet": {"roundtrip": ["g0"]}})
    with pytest.raises(rs.Stop, match="left out is a kept document"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")


def test_a_manifest_count_mismatch_fails(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", doc_count={"train/en-dclm/part-00000.parquet": 5})
    with pytest.raises(rs.Stop, match="doc_count"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")


def test_packs_outside_the_shard_stage_are_not_selected(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", packs={"code-go"})
    r = rs.reconcile(run / "ledger", shards, tmp_path / "rec", packs=["code-go"])
    assert r["ok"] and r["totals"] == {"in_shard": 6, "not_selected": 2, "not_sharded": 1}


def test_a_written_part_without_its_files_stops(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards")
    next(shards.glob("*.quality_report.json")).unlink()
    with pytest.raises(rs.Stop, match="is not in --shards"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")


def test_cli(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards")
    p = subprocess.run([sys.executable, "-I", str(PIPELINE / "reconcile_shards.py"), "--ledger", str(run / "ledger"),
                        "--shards", str(shards), "--out", str(tmp_path / "rec")], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout.strip().splitlines()[-1]) == {"kept": 9, "in_shards": 8, "in_shard": 8, "not_sharded": 1}


def test_secret_and_every_writer_reason_are_accounted_for(run, tmp_path):
    left = {"train/en-dclm/part-00000.parquet": {"secret": ["e0"], "empty": [], "special": [{"doc_id": "e1", "ids": [3]}],
                                                 "roundtrip": []}}
    shards = write_shards(run, tmp_path / "shards", left_out=left)
    r = rs.reconcile(run / "ledger", shards, tmp_path / "rec")
    assert r["ok"] and r["totals"] == {"in_shard": 6, "left_out:secret": 1, "left_out:special": 1, "not_sharded": 1}


def test_a_document_both_left_out_and_in_a_shard_fails(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards", left_out={"train/en-dclm/part-00000.parquet": {"roundtrip": ["e0"]}},
                          extra=[("train/en-dclm/part-00000.parquet", "e0", 0)])
    with pytest.raises(rs.Stop, match="both left out and in a shard"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")


def test_a_shard_no_ledger_file_claims_fails(run, tmp_path):
    shards = write_shards(run, tmp_path / "shards")
    s = json.loads((shards / "shards_summary.json").read_text(encoding="utf-8"))
    s["parts"]["train/ghost/part-00000.parquet"] = {"pack_id": "ghost", "status": "written", "shard_id": "ghost-train-000000",
                                                    "rows_read": 1, "rows_in_part": 1, "truncated": False}
    (shards / "shards_summary.json").write_text(json.dumps(s), encoding="utf-8")
    pq.write_table(pa.table({"doc_id": ["z"], "input_part": ["train/ghost/part-00000.parquet"], "input_row": [0]}),
                   shards / "ghost-train-000000.docs.parquet")
    (shards / "ghost-train-000000.json").write_text(json.dumps({"doc_count": 1}), encoding="utf-8")
    (shards / "ghost-train-000000.quality_report.json").write_text(json.dumps({"left_out_docs": {}}), encoding="utf-8")
    with pytest.raises(rs.Stop, match=r"1 shard row\(s\) at no kept ledger position, 0 with another doc_id, e.g. ghost"):
        rs.reconcile(run / "ledger", shards, tmp_path / "rec")


def test_two_reconciliations_into_one_folder_are_refused(run, tmp_path):
    import runlock
    shards = write_shards(run, tmp_path / "shards")
    with runlock.exclusive(tmp_path / "rec"):
        with pytest.raises(rs.Stop, match="another process is writing"):
            rs.reconcile(run / "ledger", shards, tmp_path / "rec")


# --- the review of the scale pass (14 Nov) ---------------------------------------------------------------------------
def shard_files(sh, sid, name, docs, rows):
    pq.write_table(pa.table({"doc_id": docs, "input_part": [name] * len(docs), "input_row": rows}), sh / f"{sid}.docs.parquet")
    (sh / f"{sid}.json").write_text(json.dumps({"doc_count": len(docs)}), encoding="utf-8")
    (sh / f"{sid}.quality_report.json").write_text(json.dumps({"left_out_docs": {}, "upstream": {"input_part": name}}),
                                                   encoding="utf-8")


def ledger_file(root, pack, docs, part, rows):
    f = root / "ledger" / "train" / f"{pack}.parquet"
    f.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"pack_id": [pack] * len(docs), "split": ["train"] * len(docs), "doc_id": docs,
                             "final": ["kept"] * len(docs), "final_part": [part] * len(docs), "final_row": rows}), f)


def test_a_part_holding_two_packs_is_checked_against_its_shard_once(tmp_path):
    """The ledger writes one file per pack, so a part with documents of two packs is in two ledger files; its shard holds
    all of them. Both files are checked against the shard together."""
    part, name = "packA/part-00000.parquet", "train/packA/part-00000.parquet"
    docs = [f"d{i}" for i in range(6)]
    for k, pack in enumerate(("packA", "packB")):
        ledger_file(tmp_path, pack, docs[k::2], part, list(range(6))[k::2])
    sh = tmp_path / "shards"
    sh.mkdir()
    shard_files(sh, "packA-train-000000", name, docs, list(range(6)))
    (sh / "shards_summary.json").write_text(json.dumps({"parts": {name: {
        "pack_id": "packA", "status": "written", "shard_id": "packA-train-000000", "rows_read": 6}}}), encoding="utf-8")
    r = rs.reconcile(tmp_path / "ledger", sh, tmp_path / "rec", ["packA", "packB"])
    assert r["ok"] and r["kept"] == 6 and r["in_shards"] == 6 and r["totals"] == {"in_shard": 6}
    assert r["by_pack"] == {"packA": {"train": {"in_shard": 3}}, "packB": {"train": {"in_shard": 3}}}
    assert pq.read_table(tmp_path / "rec" / "reconcile_docs.parquet")["input_row"].to_pylist() == list(range(6))


def test_statuses_come_in_input_part_order_whatever_the_case_of_the_pack_names(tmp_path):
    """Ledger files are taken by their exact names (Windows sorts paths ignoring case), so the statuses are in
    (input_part, input_row) order, as one sort of the whole table gives."""
    sh = tmp_path / "shards"
    sh.mkdir()
    parts = {}
    for k, pack in enumerate(("alpha", "Zeta", "beta-2", "Beta")):
        part = f"{pack}/part-00000.parquet"
        docs = [f"{pack}-{i}" for i in range(3)]
        ledger_file(tmp_path, pack, docs, part, [0, 1, 2])
        shard_files(sh, f"s{k}", f"train/{part}", docs, [0, 1, 2])
        parts[f"train/{part}"] = {"pack_id": pack, "status": "written", "shard_id": f"s{k}", "rows_read": 3}
    (sh / "shards_summary.json").write_text(json.dumps({"parts": parts}), encoding="utf-8")
    assert rs.reconcile(tmp_path / "ledger", sh, tmp_path / "rec")["ok"]
    t = pq.read_table(tmp_path / "rec" / "reconcile_docs.parquet")
    assert t.equals(t.sort_by([("input_part", "ascending"), ("input_row", "ascending")]))
    assert t["pack_id"].to_pylist()[::3] == ["Beta", "Zeta", "alpha", "beta-2"]
