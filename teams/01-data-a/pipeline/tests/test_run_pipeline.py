"""Tests for run_pipeline.py: the whole chain on synthetic data, with clean, overlap and dedup adopted (as when TSAI ran
them) and apply, F2 (a stand-in, fake_run_f2.py), survivor_loss and the ledger run by the runner.

  python -m pytest teams/01-data-a/pipeline/tests -q
"""
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import pyarrow.parquet as pq

from conftest import HEADER, PARTS, PIPELINE
import run_pipeline as rp

FAKE_F2 = Path(__file__).resolve().parent / "fake_run_f2.py"
FAKE_SHARDS = Path(__file__).resolve().parent / "fake_run_shards.py"
FAKE_STAGE = Path(__file__).resolve().parent / "fake_stage.py"
GROUP_HEADER = ["group_id", "group_size", "priority_rule", "role", "pack_id", "split", "part", "row_in_part", "doc_id"]


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def overlap_folder(folder, cleaned_parts=PARTS, docs_all=13):
    """What overlap.py returns, shaped like its real summary (status, documents_all, inputs.parts, outputs)."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "overlap_matches.csv").write_text("row_a,row_b\n0,1\n", encoding="utf-8")
    (folder / "overlap_docs.parquet").write_bytes(b"stand-in for overlap_docs.parquet")
    summary = {"status": "complete", "documents_all": docs_all, "config": {"k": 5, "floor": 0.5, "inputs": "made up"},
               "inputs": {"parts": [{"part": f"{s}/{p}", "documents": len(rows)} for (s, p), rows in cleaned_parts.items()]},
               "outputs": {n: {"sha256": sha(folder / n)} for n in ("overlap_matches.csv", "overlap_docs.parquet")}}
    (folder / "overlap_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return folder


def dedup_folder(folder, overlap, removed=2, heldout_removed=0):
    """What dedup.py returns: G-numbered groups, integer rules, and the overlap files it checked."""
    write_csv(folder / "remove_list.csv", HEADER, [["code-go", "train", "code-go/part-00001.parquet", 0, "g0"],
                                                   ["en-dclm", "train", "en-dclm/part-00000.parquet", 2, "e2"]])
    write_csv(folder / "dedup_groups.csv", GROUP_HEADER, [
        ["G000001", 2, 4, "survivor", "code-go", "train", "code-go/part-00000.parquet", 0, "g0"],
        ["G000001", 2, 4, "removed", "code-go", "train", "code-go/part-00001.parquet", 0, "g0"],
        ["G000002", 3, 0, "survivor", "code-go", "heldout", "code-go/part-00000.parquet", 0, "h0"],
        ["G000002", 3, 0, "survivor", "code-go", "heldout", "code-go/part-00000.parquet", 1, "h1"],
        ["G000002", 3, 0, "removed", "en-dclm", "train", "en-dclm/part-00000.parquet", 2, "e2"]])
    log = [{"removed_pack_id": "code-go", "removed_split": "train", "removed_part": "code-go/part-00001.parquet",
            "removed_row_in_part": 0, "removed_id": "g0", "kept_pack_id": "code-go", "kept_split": "train",
            "kept_part": "code-go/part-00000.parquet", "kept_row_in_part": 0, "kept_id": "g0", "rule": "H1",
            "similarity": 1.0, "priority_rule": 4, "stage": "within_pack", "direct": True},
           {"removed_pack_id": "en-dclm", "removed_split": "train", "removed_part": "en-dclm/part-00000.parquet",
            "removed_row_in_part": 2, "removed_id": "e2", "kept_pack_id": "code-go", "kept_split": "heldout",
            "kept_part": "code-go/part-00000.parquet", "kept_row_in_part": 0, "kept_id": "h0", "rule": "H2",
            "similarity": 0.91, "priority_rule": 0, "stage": "cross_pack", "direct": True}]
    (folder / "dedup_log.jsonl").write_text("".join(json.dumps(e) + "\n" for e in log), encoding="utf-8")
    checked = {n: sha(overlap / n) for n in ("overlap_matches.csv", "overlap_docs.parquet")}
    (folder / "dedup_summary.json").write_text(json.dumps({
        "status": "complete", "overlap_run": {"documents_all": 13, "checked_sha256": checked}, "documents_all": 13,
        "removed": removed, "heldout_removed": heldout_removed,
        "config": {"cross_pack": True, "pack_order": ["code-go", "en-dclm"], "licence_usable": {}, "default_licence_usable": True,
                   "gold_dirs": []}}), encoding="utf-8")
    return folder


@pytest.fixture
def tsai_outputs(tmp_path, cleaned):
    overlap = overlap_folder(tmp_path / "overlap")
    return {"cleaned": cleaned, "overlap": overlap, "dedup": dedup_folder(tmp_path / "dedup", overlap)}


def write_config(path, outs, run_id="test-run", **extra):
    cfg = {"run_id": run_id, "out": str(path.parent / "runs"),
           "stages": {"clean": {"mode": "adopt", "output": str(outs["cleaned"])},
                      "overlap": {"mode": "adopt", "output": str(outs["overlap"])},
                      "dedup": {"mode": "adopt", "output": str(outs["dedup"])},
                      "f2": {"script": str(FAKE_F2)}}}
    cfg["stages"].update(extra)
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


@pytest.fixture
def config(tmp_path, tsai_outputs, monkeypatch):
    for k in ("FAKE_F2_ERROR", "FAKE_F2_BAD_SHA", "FAKE_F2_CRASH"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("FAKE_F2_DROP", "g0,h1")
    return write_config(tmp_path / "pipeline.json", tsai_outputs)


def final_ids(run):
    return sorted(d for f in (run / "final").rglob("*.parquet") for d in pq.read_table(f).column("doc_id").to_pylist())


def test_full_chain(tmp_path, config):
    m = rp.run(config)
    run = tmp_path / "runs" / "test-run"
    assert [s["stage"] for s in m["stages"]] == [s for s in rp.STAGES if s not in rp.OPTIONAL]
    c = {s["stage"]: s["counts"] for s in m["stages"]}
    assert c["clean"]["rows"] == 13 and c["overlap"]["documents_all"] == 13 and c["dedup"]["remove_list_rows"] == 2
    assert (c["apply"]["rows"], c["apply"]["removed"], c["apply"]["kept"]) == (13, 2, 11)
    assert (c["f2"]["rows"], c["f2"]["dropped_by_f2"], c["f2"]["kept"]) == (11, 2, 9)
    assert c["f2"]["by_split"]["heldout"] == {"rows": 2, "kept": 1, "dropped_by_f2": 1, "errors": 0}
    assert c["survivor_loss"]["lost"] == 1 and c["survivor_loss"]["partly_hit"] == 1
    assert m["totals"] == {"cleaned": 13, "removed_by_dedup": 2, "dropped_by_f2": 2, "final": 9}
    assert c["ledger"] == {"rows": 13, "rows_cleaned": 13, "kept": 9, "dropped_by_clean": 0, "removed_by_dedup": 2,
                           "dropped_by_f2": 2, "f2_error": 0}
    assert m["by_pack"] == {
        "code-go": {"train": {"cleaned": 8, "removed_by_dedup": 1, "dropped_by_f2": 1, "final": 6},
                    "heldout": {"cleaned": 2, "removed_by_dedup": 0, "dropped_by_f2": 1, "final": 1}},
        "en-dclm": {"train": {"cleaned": 3, "removed_by_dedup": 1, "dropped_by_f2": 0, "final": 2}}}
    assert {"ledger per pack = apply per pack", "every per-pack row adds up",
            "per-pack table adds up to the stages' counts"} <= {ch["check"] for ch in m["checks"]}
    assert rp.pack_table({}) == "" and rp.pack_table({"p": {}}) == ""
    assert sorted(p.relative_to(run / "ledger").as_posix() for p in (run / "ledger").rglob("*.parquet")) == [
        "heldout/code-go.parquet", "train/code-go.parquet", "train/en-dclm.parquet"]
    names = {ch["check"] for ch in m["checks"]}
    assert {"overlap read these cleaned parts", "dedup used this overlap run", "F2 read what apply wrote in train",
            "survivor loss saw every dedup group", "ledger kept = F2's kept"} <= names and all(ch["ok"] for ch in m["checks"])
    assert final_ids(run) == sorted(["g1", "g2", "g3", "g4", "g5", "g6", "e0", "e1", "h0"])
    assert (run / "logs" / "f2_train.log").is_file()
    on_disk = json.loads((run / "pipeline_manifest.json").read_text(encoding="utf-8"))
    assert on_disk["totals"] == m["totals"] and "synthetic text" not in json.dumps(on_disk)


def test_digests_repeat_across_identical_runs(tmp_path, config, tsai_outputs):
    a = rp.run(config)
    b = rp.run(write_config(tmp_path / "again.json", tsai_outputs, run_id="test-run-2"))
    assert [s["digest"] for s in a["stages"]] == [s["digest"] for s in b["stages"]]


def test_from_keeps_earlier_checks(config):
    full = len(rp.run(config, to="apply")["checks"])
    m = rp.run(config, start="f2")
    assert [s["stage"] for s in m["stages"]] == [s for s in rp.STAGES if s not in rp.OPTIONAL] and m["totals"]["final"] == 9
    assert len(m["checks"]) > full and {ch["stage"] for ch in m["checks"]} >= {"overlap", "dedup", "apply", "f2"}


def test_adopted_output_changed_after_recording_stops(config, tsai_outputs):
    rp.run(config, to="apply")
    with (tsai_outputs["dedup"] / "remove_list.csv").open("a", encoding="utf-8") as f:
        f.write("en-dclm,train,en-dclm/part-00000.parquet,1,e1\n")
    with pytest.raises(rp.Stop, match="changed"):
        rp.run(config, start="f2")


def test_from_a_stage_whose_input_was_never_run_stops(config):
    with pytest.raises(rp.Stop, match="no record .* run it first"):
        rp.run(config, start="f2")


def test_dedup_from_another_overlap_run_stops(tmp_path, config, tsai_outputs):
    other = overlap_folder(tmp_path / "other_overlap")
    (other / "overlap_matches.csv").write_text("row_a,row_b\n0,2\n", encoding="utf-8")
    dedup_folder(tsai_outputs["dedup"], other)
    with pytest.raises(rp.Stop, match="dedup used this overlap run"):
        rp.run(config)


def test_overlap_of_other_parts_stops(tmp_path, config, tsai_outputs):
    parts = dict(PARTS)
    parts[("train", "en-dclm/part-00009.parquet")] = parts.pop(("train", "en-dclm/part-00000.parquet"))
    overlap_folder(tsai_outputs["overlap"], parts)
    dedup_folder(tsai_outputs["dedup"], tsai_outputs["overlap"])
    with pytest.raises(rp.Stop, match="overlap read these cleaned parts"):
        rp.run(config)


def test_count_mismatch_stops(tmp_path, config, tsai_outputs):
    overlap_folder(tsai_outputs["overlap"], docs_all=12)
    with pytest.raises(rp.Stop, match="overlap read every cleaned row"):
        rp.run(config)


def test_dedup_removing_heldout_stops(config, tsai_outputs):
    dedup_folder(tsai_outputs["dedup"], tsai_outputs["overlap"], heldout_removed=1)
    with pytest.raises(rp.Stop, match="held-out"):
        rp.run(config)


def test_f2_errors_stop(config, monkeypatch):
    monkeypatch.setenv("FAKE_F2_ERROR", "g3")
    with pytest.raises(rp.Stop, match="F2 reported no errors on train"):
        rp.run(config)


def test_f2_that_read_something_else_stops(config, monkeypatch):
    monkeypatch.setenv("FAKE_F2_BAD_SHA", "1")
    with pytest.raises(rp.Stop, match="F2 read what apply wrote"):
        rp.run(config)


def test_stale_final_output_stops(tmp_path, config):
    stale = tmp_path / "runs" / "test-run" / "final" / "train" / "old-pack" / "part-00000.parquet"
    stale.parent.mkdir(parents=True)
    shutil.copyfile(next((tmp_path / "cleaned" / "train").rglob("*.parquet")), stale)
    with pytest.raises(rp.Stop, match="stale F2 output"):
        rp.run(config)


def test_train_only_run(tmp_path, cleaned, monkeypatch):
    shutil.rmtree(cleaned / "heldout")
    train = {k: v for k, v in PARTS.items() if k[0] == "train"}
    overlap = overlap_folder(tmp_path / "overlap1", train, docs_all=11)
    dedup = dedup_folder(tmp_path / "dedup1", overlap)
    rows = list(csv.reader((dedup / "dedup_groups.csv").open(encoding="utf-8")))
    write_csv(dedup / "dedup_groups.csv", rows[0], [r for r in rows[1:] if r[5] == "train"])
    s = json.loads((dedup / "dedup_summary.json").read_text(encoding="utf-8"))
    s.update(documents_all=11)
    (dedup / "dedup_summary.json").write_text(json.dumps(s), encoding="utf-8")
    monkeypatch.setenv("FAKE_F2_DROP", "g0")
    cfg = write_config(tmp_path / "p1.json", {"cleaned": cleaned, "overlap": overlap, "dedup": dedup}, run_id="train-only")
    m = rp.run(cfg)
    assert m["totals"] == {"cleaned": 11, "removed_by_dedup": 2, "dropped_by_f2": 1, "final": 8}


def test_run_mode_calls_the_script(tmp_path, config, tsai_outputs):
    maker = tmp_path / "make_overlap.py"
    src = tsai_outputs["overlap"]
    maker.write_text(f"import shutil, sys\nshutil.copytree({str(src)!r}, sys.argv[1], dirs_exist_ok=True)\n", encoding="utf-8")
    out = tmp_path / "overlap_run"
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["overlap"] = {"mode": "run", "output": str(out), "command": [str(maker), str(out)]}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    m = rp.run(config)
    rec = next(s for s in m["stages"] if s["stage"] == "overlap")
    assert rec["mode"] == "run" and rec["code_sha256"] == sha(maker)
    assert (tmp_path / "runs" / "test-run" / "logs" / "overlap.log").is_file()


def test_run_mode_failure_stops(tmp_path, config):
    bad = tmp_path / "bad_overlap.py"
    bad.write_text("import sys; print('boom'); sys.exit(3)\n", encoding="utf-8")
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["overlap"] = {"mode": "run", "output": cfg["stages"]["overlap"]["output"], "command": [str(bad)]}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="exit code 3.*boom"):
        rp.run(config)


def test_bad_config_stops_before_anything_runs(tmp_path, config):
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["f2"] = {"script": str(tmp_path / "missing_run_f2.py")}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="f2 script .* not found"):
        rp.run(config)
    assert not (tmp_path / "runs").exists()


def set_f2(config, **kw):
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["f2"].update(kw)
    config.write_text(json.dumps(cfg), encoding="utf-8")


def test_parallel_f2_matches_one_process(tmp_path, config, tsai_outputs):
    one = rp.run(config)
    par_cfg = write_config(tmp_path / "par.json", tsai_outputs, run_id="parallel")
    set_f2(par_cfg, workers=3)
    par = rp.run(par_cfg)
    run = tmp_path / "runs" / "parallel"
    f2 = next(s for s in par["stages"] if s["stage"] == "f2")
    assert (f2["workers"], f2["units"]) == (3, 3)  # train/code-go, train/en-dclm, heldout/code-go
    assert par["totals"] == one["totals"] and final_ids(run) == final_ids(tmp_path / "runs" / "test-run")
    assert {p.name for p in (run / "logs").glob("f2_*.log")} == {"f2_train_code-go.log", "f2_train_en-dclm.log",
                                                                  "f2_heldout_code-go.log"}
    c = {s["stage"]: s["counts"] for s in par["stages"]}
    assert (c["survivor_loss"]["lost"], c["survivor_loss"]["partly_hit"]) == (1, 1)
    assert c["ledger"] == {s["stage"]: s["counts"] for s in one["stages"]}["ledger"]


def test_parallel_f2_crash_names_the_pack_and_rerun_recovers(config, monkeypatch):
    set_f2(config, workers=2)
    monkeypatch.setenv("FAKE_F2_CRASH", "en-dclm")
    with pytest.raises(rp.Stop, match=r"1 of 3 unit\(s\) failed.*train/en-dclm"):
        rp.run(config)
    monkeypatch.delenv("FAKE_F2_CRASH")
    assert rp.run(config, start="f2")["totals"]["final"] == 9


@pytest.mark.parametrize("workers", [0, "4", 1.5, True])
def test_bad_workers_stop(config, workers):
    set_f2(config, workers=workers)
    with pytest.raises(rp.Stop, match="workers"):
        rp.run(config)


def test_cli(tmp_path, config):
    env = {**os.environ, "FAKE_F2_DROP": "g0,h1"}
    p = subprocess.run([sys.executable, "-I", str(PIPELINE / "run_pipeline.py"), "--config", str(config)],
                       capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout.strip().splitlines()[-1])["final"] == 9
    table = p.stderr.strip().splitlines()[-5:]
    assert table[0].split() == ["pack", "split", "cleaned", "-dedup", "-f2", "final"]
    assert table[-1].split() == ["total", "13", "2", "2", "9"]
    assert table[1].split() == ["code-go", "train", "8", "1", "1", "6"]


# --- the shard stage (stand-in run_shards.py; the real one is tested in shards/tests) -----------------------------------
@pytest.fixture
def shard_config(tmp_path, tsai_outputs, config, monkeypatch):
    """A config with stages.shards, and the clean job's job_summary.json the shard stage needs. Returns the config path."""
    for k in ("FAKE_SHARDS_FAIL", "FAKE_SHARDS_NONE", "FAKE_SHARDS_BAD_RUN"):
        monkeypatch.delenv(k, raising=False)
    (tsai_outputs["cleaned"] / "job_summary.json").write_text(json.dumps({"clean_sha256": "c" * 64, "parts": []}), encoding="utf-8")
    tokenizer = tmp_path / "tokenizer.json"
    tokenizer.write_text("{}", encoding="utf-8")
    return write_config(tmp_path / "pipeline.json", tsai_outputs,
                        shards={"script": str(FAKE_SHARDS), "tokenizer": str(tokenizer), "packs": ["code-go"], "tokens": 100})


def test_shards_run_after_f2_and_are_recorded(tmp_path, shard_config):
    m = rp.run(shard_config)
    run = tmp_path / "runs" / "test-run"
    assert [s["stage"] for s in m["stages"]] == list(rp.STAGES[: rp.STAGES.index("shards") + 1])
    s = m["stages"][-1]
    assert s["counts"] == {"written": 2, "failed": 0, "skipped": 0, "not_sharded": 1, "truncated": 0, "parts": 3}
    assert m["totals"]["shards_written"] == 2 and all(ch["ok"] for ch in m["checks"])
    record = json.loads((run / "cleaning_pipeline.json").read_text(encoding="utf-8"))
    assert sorted(record) == ["clean_py_sha256", "dedup", "f2_set_sha256"] and record["clean_py_sha256"] == "c" * 64
    assert s["cleaning_pipeline_sha256"] == rp.sha256(run / "cleaning_pipeline.json")
    assert json.loads((run / "pipeline_manifest.json").read_text(encoding="utf-8"))["stages"][-1]["stage"] == "shards"
    assert json.loads((run / "shards" / "args.json").read_text(encoding="utf-8"))["packs"] == ["code-go"]
    assert json.loads((run / "shards" / "args.json").read_text(encoding="utf-8"))["tokens"] == 100
    assert (run / "logs" / "shards.log").is_file() and s["digest"] and s["code_sha256"]


def test_without_stages_shards_the_run_stops_after_the_ledger(tmp_path, config):
    m = rp.run(config)
    assert [s["stage"] for s in m["stages"]][-1] == "ledger" and "shards_written" not in m["totals"]
    assert not (tmp_path / "runs" / "test-run" / "cleaning_pipeline.json").exists()
    with pytest.raises(rp.Stop, match="stages.shards is not configured"):
        rp.run(config, to="shards")


def test_from_shards_adds_the_stage_to_a_finished_run(tmp_path, shard_config):
    rp.run(shard_config, to="ledger")
    m = rp.run(shard_config, start="shards")
    assert [s["stage"] for s in m["stages"]] == list(rp.STAGES[: rp.STAGES.index("shards") + 1]) and m["totals"]["final"] == 9 and m["totals"]["shards_written"] == 2


def test_a_second_shard_run_into_the_same_out_stops(shard_config):
    rp.run(shard_config)
    with pytest.raises(rp.Stop, match="run_shards.py exited 0"):  # the stand-in refuses, as the real one does
        rp.run(shard_config, start="shards")


def test_a_failed_part_stops_the_run_before_the_stage_is_recorded(tmp_path, shard_config, monkeypatch):
    monkeypatch.setenv("FAKE_SHARDS_FAIL", "1")
    with pytest.raises(rp.Stop, match="no part failed or was skipped"):
        rp.run(shard_config)
    stages = [s["stage"] for s in json.loads((tmp_path / "runs" / "test-run" / "pipeline_manifest.json").read_text(encoding="utf-8"))["stages"]]
    assert stages[-1] == "ledger"


def test_a_shard_process_that_wrote_no_summary_stops_the_run(shard_config, monkeypatch):
    monkeypatch.setenv("FAKE_SHARDS_NONE", "1")
    with pytest.raises(rp.Stop, match="wrote no shards_summary.json"):
        rp.run(shard_config)


def test_a_summary_of_another_run_stops_the_run(shard_config, monkeypatch):
    monkeypatch.setenv("FAKE_SHARDS_BAD_RUN", "1")
    with pytest.raises(rp.Stop, match="the summary is this run's"):
        rp.run(shard_config)


def test_no_clean_job_summary_means_no_shard_stage(tmp_path, shard_config, tsai_outputs):
    (tsai_outputs["cleaned"] / "job_summary.json").unlink()
    with pytest.raises(rp.Stop, match="shards: .*no job_summary.json"):
        rp.run(shard_config)


@pytest.mark.parametrize("change, message", [({"tokenizer": "/no/such/tokenizer.json"}, "stages.shards.tokenizer"),
                                             ({"tokens": 0}, "stages.shards.tokens"), ({"packs": "code-go"}, "stages.shards.packs"),
                                             ({"script": "/no/such/run_shards.py"}, "shards script")])
def test_the_shards_config_is_checked_before_anything_runs(tmp_path, shard_config, change, message):
    cfg = json.loads(shard_config.read_text(encoding="utf-8"))
    cfg["stages"]["shards"].update(change)
    shard_config.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match=message):
        rp.run(shard_config)
    assert not (tmp_path / "runs").exists()


# --- stages run from settings files: default folders in the run folder, generated configs, --plan -----------------------
@pytest.fixture
def staged(tmp_path, tsai_outputs, monkeypatch):
    """A run config whose clean, overlap and dedup stages run the stand-in fake_stage.py from settings files, in a made-up
    repository (rp.REPO), with every folder left to the default. Returns (config path, repo)."""
    repo = tmp_path / "repo"
    (repo / "out").mkdir(parents=True)
    monkeypatch.setattr(rp, "REPO", repo)
    for k in ("FAKE_F2_ERROR", "FAKE_F2_BAD_SHA", "FAKE_F2_CRASH"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("FAKE_F2_DROP", "g0,h1")

    manifest = tmp_path / "sample_manifest.json"
    manifest.write_text('{"shards": []}', encoding="utf-8")

    def settings(name, fixture, **extra):
        p = tmp_path / f"{name}_settings.json"
        p.write_text(json.dumps({"fixture": str(fixture), **extra}), encoding="utf-8")
        return str(p)

    cfg = {"run_id": "test-run", "out": str(repo / "out" / "runs"), "stages": {
        "clean": {"mode": "run", "script": str(FAKE_STAGE), "settings": settings("clean", tsai_outputs["cleaned"]), "input": "raw/sample",
                  "manifest": str(manifest), "manifest_sha256": sha(manifest), "expected_parts": {"train": 9, "heldout": 2}, "sample": "made up"},
        "overlap": {"mode": "run", "script": str(FAKE_STAGE), "settings": settings("overlap", tsai_outputs["overlap"], k=5, floor=0.5, inputs="x", out="y")},
        "dedup": {"mode": "run", "script": str(FAKE_STAGE), "settings": settings("dedup", tsai_outputs["dedup"], cross_pack=True, results="x", inputs="x", out="y")},
        "f2": {"script": str(FAKE_F2)}}}
    path = tmp_path / "run_config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path, repo


def edit_stage(path, stage, **changes):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["stages"][stage].update(changes)
    path.write_text(json.dumps(cfg), encoding="utf-8")


def test_stages_run_from_settings_into_the_run_folder(tmp_path, staged):
    path, repo = staged
    m = rp.run(path)
    run = repo / "out" / "runs" / "test-run"
    recs = {s["stage"]: s for s in m["stages"]}
    assert m["totals"] == {"cleaned": 13, "removed_by_dedup": 2, "dropped_by_f2": 2, "final": 9} and all(c["ok"] for c in m["checks"])
    assert [recs[s]["output"] for s in ("clean", "overlap", "dedup")] == [f"out/runs/test-run/{s}" for s in ("clean", "overlap", "dedup")]
    assert (run / "clean" / "train").is_dir() and (run / "overlap" / "overlap_summary.json").is_file() and (run / "dedup" / "remove_list.csv").is_file()
    # every stage gets the settings with the path keys filled in, repo-relative; every other setting is kept
    cl = json.loads((run / "cfg" / "clean.json").read_text(encoding="utf-8"))
    assert (cl["input_root"], cl["output_root"]) == ("raw/sample", "out/runs/test-run/clean") and recs["clean"]["command"][-2:] == ["--config", (run / "cfg" / "clean.json").as_posix()]
    assert (cl["manifest_sha256"], cl["expected_parts"], cl["sample"]) == (sha(cl["manifest"]), {"train": 9, "heldout": 2}, "made up")
    ov = json.loads((run / "cfg" / "overlap.json").read_text(encoding="utf-8"))
    dd = json.loads((run / "cfg" / "dedup.json").read_text(encoding="utf-8"))
    assert (ov["inputs"], ov["out"], ov["k"], ov["floor"]) == ("out/runs/test-run/clean", "out/runs/test-run/overlap", 5, 0.5)
    assert (dd["results"], dd["inputs"], dd["out"], dd["cross_pack"]) == ("out/runs/test-run/overlap", "out/runs/test-run/clean", "out/runs/test-run/dedup", True)
    for stage in ("clean", "overlap", "dedup"):
        assert recs[stage]["config"] == f"cfg/{stage}.json" and recs[stage]["config_sha256"] == sha(run / "cfg" / f"{stage}.json")
    assert recs["overlap"]["settings_sha256"] == sha(json.loads(path.read_text(encoding="utf-8"))["stages"]["overlap"]["settings"])
    assert json.loads((run / "logs" / "clean.log").read_text(encoding="utf-8").splitlines()[-1])["input_root"] == "raw/sample"
    assert json.loads((run / "logs" / "dedup.log").read_text(encoding="utf-8").splitlines()[-1])["keys"]["results"] == "out/runs/test-run/overlap"


def test_a_settings_pin_that_does_not_match_stops_before_anything_runs(staged):
    path, repo = staged
    edit_stage(path, "overlap", settings_sha256="0" * 64)
    with pytest.raises(rp.Stop, match="overlap: .*pins"):
        rp.run(path)
    assert not (repo / "out" / "runs").exists()


def test_a_run_stage_needs_settings_or_a_command(staged):
    path, _ = staged
    cfg = json.loads(path.read_text(encoding="utf-8"))
    del cfg["stages"]["dedup"]["settings"]
    path.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="dedup: .*settings .* is missing"):
        rp.run(path)


def test_a_command_must_say_where_it_writes_and_an_adopted_stage_needs_its_folder(staged):
    path, _ = staged
    edit_stage(path, "overlap", command=[str(FAKE_STAGE)])
    with pytest.raises(rp.Stop, match="overlap.output is missing: with a command, say where it writes"):
        rp.run(path)
    edit_stage(path, "overlap", mode="adopt")
    with pytest.raises(rp.Stop, match="overlap.output is missing \\(an adopted stage needs"):
        rp.run(path)


def test_an_output_may_not_take_a_folder_name_of_the_run_or_overlap_another_stage(staged):
    path, repo = staged
    run = repo / "out" / "runs" / "test-run"
    edit_stage(path, "overlap", output=str(run / "final"))
    with pytest.raises(rp.Stop, match="folder of the run itself"):
        rp.run(path)
    edit_stage(path, "overlap", output=str(run / "clean" / "inner"))
    with pytest.raises(rp.Stop, match="stages.clean.output and stages.overlap.output overlap"):
        rp.run(path)


def test_a_settings_stage_cannot_write_outside_out(staged, tmp_path):
    path, repo = staged
    edit_stage(path, "overlap", output=str(tmp_path / "elsewhere"))
    with pytest.raises(rp.Stop, match="named subfolder"):
        rp.run(path)


def test_the_plan_shows_every_folder_and_command_and_runs_nothing(staged, capsys, monkeypatch):
    path, repo = staged
    text = rp.plan(path)
    for line in ("run folder: out/runs/test-run", "01 clean", "02 overlap", "03 dedup", "04 apply", "05 f2", "06 survivor_loss",
                 "inputs = out/runs/test-run/clean, out = out/runs/test-run/overlap", "generated config out/runs/test-run/cfg/overlap.json",
                 "input_root = raw/sample, manifest = ", "output_root = out/runs/test-run/clean", "settings "):
        assert line in text
    assert "shards" not in text.split("\n", 1)[1] and "07 shards" not in text
    assert not (repo / "out" / "runs").exists()  # nothing written, not even cfg/
    assert "05 f2" not in rp.plan(path, to="apply")
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--config", str(path), "--plan"])
    rp.main()
    assert "01 clean" in capsys.readouterr().out and not (repo / "out" / "runs").exists()


def test_the_plan_of_an_adopted_run_says_adopt(config):
    text = rp.plan(config)
    assert sum(" adopt  " in line for line in text.splitlines()) == 3 and "$ python" not in text


def test_the_plan_checks_the_config_like_a_run(staged):
    path, _ = staged
    edit_stage(path, "dedup", settings_sha256="0" * 64)
    with pytest.raises(rp.Stop, match="pins"):
        rp.plan(path)
    with pytest.raises(rp.Stop, match="unknown stage"):
        rp.Run(path).plan("nope")


# --- run parameters live in the config file: run_id, adopted stages, stages.clean.only, to, from ----------------------------
def edit_config(path, **top):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg.update(top)
    path.write_text(json.dumps(cfg), encoding="utf-8")


def set_stage(path, stage, spec):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["stages"][stage] = spec
    path.write_text(json.dumps(cfg), encoding="utf-8")


def test_run_id_in_the_config_names_the_run(staged):
    path, repo = staged
    edit_config(path, run_id="job-1")
    m = rp.run(path)
    assert m["run_id"] == "job-1" and "overrides" not in m
    assert (repo / "out" / "runs" / "job-1" / "pipeline_manifest.json").is_file() and not (repo / "out" / "runs" / "test-run").exists()
    assert m["config"]["run_id"] == "job-1"  # the manifest embeds the config that ran


def test_a_run_needs_a_run_id(staged):
    path, _ = staged
    cfg = json.loads(path.read_text(encoding="utf-8"))
    del cfg["run_id"]
    path.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="run_id is missing"):
        rp.run(path)


def test_an_adopted_stage_in_the_config_uses_the_folder_instead_of_running(tmp_path, staged, tsai_outputs):
    path, repo = staged
    prev = repo / "out" / "earlier" / "clean"
    shutil.copytree(tsai_outputs["cleaned"], prev)
    set_stage(path, "clean", {"mode": "adopt", "output": str(prev)})
    m = rp.run(path)
    run = repo / "out" / "runs" / "test-run"
    clean = next(s for s in m["stages"] if s["stage"] == "clean")
    assert (clean["mode"], clean["command"], clean["output"]) == ("adopt", None, "out/earlier/clean")
    assert not (run / "clean").exists() and not (run / "logs" / "clean.log").exists() and not (run / "cfg" / "clean.json").exists()
    assert json.loads((run / "cfg" / "overlap.json").read_text(encoding="utf-8"))["inputs"] == "out/earlier/clean"
    assert m["totals"]["final"] == 9


def test_clean_only_in_the_config_limits_the_clean_job_and_lets_overlap_expect_fewer_packs(staged):
    path, repo = staged
    part = "train/code-go/part-00000.parquet"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["stages"]["clean"]["only"] = [part]
    cfg["to"] = "overlap"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    m = rp.run(path)
    run = repo / "out" / "runs" / "test-run"
    clean = next(s for s in m["stages"] if s["stage"] == "clean")
    assert [s["stage"] for s in m["stages"]] == ["clean", "overlap"]
    assert clean["only"] == [part] and clean["command"][-2:] == ["--only", part]
    assert json.loads((run / "logs" / "clean.log").read_text(encoding="utf-8").splitlines()[-1])["only"] == [part]
    assert json.loads((run / "cfg" / "overlap.json").read_text(encoding="utf-8"))["expected_packs"] == []


def test_without_only_overlaps_settings_are_not_changed(staged):
    path, repo = staged
    edit_config(path, to="overlap")
    rp.run(path)
    assert "expected_packs" not in json.loads((repo / "out/runs/test-run/cfg/overlap.json").read_text(encoding="utf-8"))


def test_only_needs_a_clean_stage_that_runs_from_settings(staged, tsai_outputs):
    path, repo = staged
    prev = repo / "out" / "earlier" / "clean"
    shutil.copytree(tsai_outputs["cleaned"], prev)
    set_stage(path, "clean", {"mode": "adopt", "output": str(prev), "only": ["train/code-go/part-00000.parquet"]})
    with pytest.raises(rp.Stop, match="stages.clean.only limits the clean job"):
        rp.run(path)


def test_only_must_be_a_list_of_parts(staged):
    path, _ = staged
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["stages"]["clean"]["only"] = "train/code-go/part-00000.parquet"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="stages.clean.only must be a list"):
        rp.run(path)


def test_to_in_the_config_stops_after_that_stage_and_checks_only_the_stages_up_to_it(staged):
    path, repo = staged
    cfg = json.loads(path.read_text(encoding="utf-8"))
    del cfg["stages"]["overlap"], cfg["stages"]["dedup"]
    cfg["to"] = "clean"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    assert "02 overlap" not in rp.plan(path)
    m = rp.run(path)
    assert [s["stage"] for s in m["stages"]] == ["clean"] and m["totals"] == {"cleaned": 13}
    edit_config(path, to="dedup", run_id="second")
    with pytest.raises(rp.Stop, match="stages.overlap is missing"):
        rp.run(path)


def test_from_in_the_config_resumes_a_recorded_run(staged):
    path, repo = staged
    edit_config(path, to="apply")
    first = rp.run(path)
    assert [s["stage"] for s in first["stages"]][-1] == "apply"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    del cfg["to"]
    cfg["from"] = "f2"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    m = rp.run(path)
    assert [s["stage"] for s in m["stages"]] == ["clean", "overlap", "dedup", "apply", "f2", "survivor_loss", "ledger"] and m["totals"]["final"] == 9


def test_from_must_not_come_after_to(staged):
    path, _ = staged
    edit_config(path, to="clean")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cfg["from"] = "dedup"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match='"from": dedup comes after "to": clean'):
        rp.run(path)


def test_the_plan_follows_the_config(staged, tsai_outputs):
    path, repo = staged
    prev = repo / "out" / "earlier" / "clean"
    shutil.copytree(tsai_outputs["cleaned"], prev)
    set_stage(path, "clean", {"mode": "adopt", "output": str(prev)})
    edit_config(path, run_id="job-2", to="overlap")
    text = rp.plan(path)
    assert "run folder: out/runs/job-2" in text and "01 clean         adopt  out/earlier/clean" in text
    assert "02 overlap" in text and "03 dedup" not in text


def test_the_command_line_takes_only_config_and_plan(staged, capsys, monkeypatch):
    path, repo = staged
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--config", str(path), "--plan"])
    rp.main()
    assert "01 clean" in capsys.readouterr().out and not (repo / "out" / "runs").exists()
    for flag in (["--run-id", "x"], ["--adopt", "clean=y"], ["--only", "z"], ["--to", "dedup"], ["--from", "f2"]):
        monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--config", str(path), *flag])
        with pytest.raises(SystemExit) as e:
            rp.main()
        assert e.value.code == 2  # argparse: unrecognized arguments


def test_ledger_mode_b_adds_the_cleaners_drops(tmp_path, config, cleaned):
    raw = tmp_path / "raw"
    for f in cleaned.rglob("*.parquet"):
        t = pq.read_table(f)
        dst = raw / f.relative_to(cleaned)
        dst.parent.mkdir(parents=True, exist_ok=True)
        extra = t.slice(0, 1).to_pylist()
        extra[0]["doc_id"] = "x-" + extra[0]["doc_id"]
        pq.write_table(pa_concat(t, extra), dst)
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["ledger"] = {"raw": str(raw)}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    m = rp.run(config)
    assert m["totals"] == {"raw": 17, "dropped_by_clean": 4, "cleaned": 13, "removed_by_dedup": 2, "dropped_by_f2": 2,
                           "final": 9}
    rec = next(s for s in m["stages"] if s["stage"] == "ledger")
    assert rec["clean_mode"] == "B" and rec["counts"]["clean_fix_by_text"] == 0
    assert m["by_pack"]["en-dclm"]["train"] == {"raw": 4, "dropped_by_clean": 1, "cleaned": 3, "removed_by_dedup": 1,
                                                "dropped_by_f2": 0, "final": 2}


def test_ledger_mode_b_with_a_pack_the_cleaner_emptied(tmp_path, config, cleaned):
    """A raw pack whose every document the cleaner dropped: in the ledger with 0 cleaned rows, absent from apply."""
    import pyarrow as pa
    raw = tmp_path / "raw"
    for f in cleaned.rglob("*.parquet"):
        dst = raw / f.relative_to(cleaned)
        dst.parent.mkdir(parents=True, exist_ok=True)
        t = pq.read_table(f)
        if f.relative_to(cleaned).as_posix() == "train/en-dclm/part-00000.parquet":
            ghost = dict(t.slice(0, 1).to_pylist()[0], doc_id="ghost-1", pack_id="ghost-pack")
            t = pa.concat_tables([t, pa.Table.from_pylist([ghost], schema=t.schema)])
        pq.write_table(t, dst)
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["ledger"] = {"raw": str(raw)}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    m = rp.run(config)
    assert m["by_pack"]["ghost-pack"] == {"train": {"raw": 1, "dropped_by_clean": 1, "cleaned": 0, "removed_by_dedup": 0,
                                                    "dropped_by_f2": 0, "final": 0}}
    assert m["totals"]["dropped_by_clean"] == 1 and all(ch["ok"] for ch in m["checks"])


def pa_concat(t, rows):
    import pyarrow as pa
    return pa.concat_tables([t, pa.Table.from_pylist(rows, schema=t.schema)])


def test_ledger_raw_must_be_a_folder(tmp_path, config):
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["ledger"] = {"raw": str(tmp_path / "no-such-raw")}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="stages.ledger.raw"):
        rp.run(config)
    assert not (tmp_path / "runs").exists()


def test_from_ledger_reuses_earlier_stages(config):
    first = rp.run(config)
    again = rp.run(config, start="ledger")
    assert again["totals"] == first["totals"]
    assert [s["digest"] for s in again["stages"]] == [s["digest"] for s in first["stages"]]


def test_ledger_disagreeing_with_apply_per_pack_stops(config, monkeypatch):
    import ledger
    real = ledger.build

    def shifted(*a, **kw):
        s = real(*a, **kw)
        bp = s["by_pack"]
        bp["code-go"]["train"]["removed_by_dedup"] += 1
        bp["en-dclm"]["train"]["removed_by_dedup"] -= 1  # same totals, wrong packs
        return s
    monkeypatch.setattr(ledger, "build", shifted)
    with pytest.raises(rp.Stop, match="ledger per pack = apply per pack.*code-go/train"):
        rp.run(config)


def test_from_ledger_keeps_the_per_pack_table(config):
    first = rp.run(config)
    assert rp.run(config, start="ledger")["by_pack"] == first["by_pack"]
    assert rp.run(config, to="f2").get("by_pack") is None


# --- f2_pool.py as the F2 stage, and the reconcile stage ------------------------------------------------------------
FAKE_F2_MODULE = Path(__file__).resolve().parent / "fake_f2_module.py"


def test_f2_pool_gives_the_same_run_as_run_f2(tmp_path, config, tsai_outputs):
    one = rp.run(config)
    cfg = write_config(tmp_path / "pool.json", tsai_outputs, run_id="pooled")
    set_f2(cfg, script=str(FAKE_F2_MODULE), pool=True, workers=2)
    m = rp.run(cfg)
    f2 = next(s for s in m["stages"] if s["stage"] == "f2")
    assert f2["pool"] is True and f2["units"] == 2 and f2["pool_code_sha256"] == rp.sha256(rp.path(rp.POOL))
    assert m["totals"] == one["totals"] and m["by_pack"] == one["by_pack"] and all(ch["ok"] for ch in m["checks"])
    assert final_ids(tmp_path / "runs" / "pooled") == final_ids(tmp_path / "runs" / "test-run")
    assert "f2_pool.py" in rp.Run(cfg).plan()


def test_f2_pool_must_be_true_or_false(config):
    set_f2(config, pool="yes")
    with pytest.raises(rp.Stop, match="pool must be true or false"):
        rp.run(config)


def test_reconcile_needs_shards(config):
    cfg = json.loads(config.read_text(encoding="utf-8"))
    cfg["stages"]["reconcile"] = {}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="reconcile needs stages.shards"):
        rp.run(config)  # whatever "to" says


def test_to_reconcile_needs_it_configured(shard_config):
    with pytest.raises(rp.Stop, match="needs stages.reconcile"):
        rp.run(shard_config, to="reconcile")


def test_reconcile_runs_after_the_shards(tmp_path, shard_config, monkeypatch):
    from test_reconcile_shards import write_shards

    def fake_shards(self):  # shard files in the writer's format, made from this run's final parts
        write_shards(self.dir, self.output("shards"), packs={"code-go"})
        return {"mode": "run", "command": ["fake"], "code_sha256": None, "output": "shards",
                "counts": {"written": 2, "failed": 0, "skipped": 0, "not_sharded": 1, "truncated": 0, "parts": 3}}
    monkeypatch.setattr(rp.Run, "stage_shards", fake_shards)
    cfg = json.loads(shard_config.read_text(encoding="utf-8"))
    cfg["stages"]["reconcile"] = {}
    shard_config.write_text(json.dumps(cfg), encoding="utf-8")
    m = rp.run(shard_config)
    rec = m["stages"][-1]
    assert rec["stage"] == "reconcile" and [s["stage"] for s in m["stages"]] == list(rp.STAGES)
    assert rec["counts"] == {"kept": 9, "in_shards": 6, "in_shard": 6, "not_selected": 2, "not_sharded": 1}
    assert "reconcile: no document is in two shards" in {c["check"] for c in m["checks"]}


def test_a_failed_reconciliation_stops_the_run(tmp_path, shard_config, monkeypatch):
    from test_reconcile_shards import write_shards

    def fake_shards(self):
        write_shards(self.dir, self.output("shards"), packs={"code-go"}, rows_read={"train/code-go/part-00000.parquet": 2})
        return {"mode": "run", "command": ["fake"], "code_sha256": None, "output": "shards",
                "counts": {"written": 2, "failed": 0, "skipped": 0, "not_sharded": 1, "truncated": 1, "parts": 3}}
    monkeypatch.setattr(rp.Run, "stage_shards", fake_shards)
    cfg = json.loads(shard_config.read_text(encoding="utf-8"))
    cfg["stages"]["reconcile"] = {}
    shard_config.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match="reconcile: .*not_reached"):
        rp.run(shard_config)


# --- scale and robustness (the scale audit, 14 Nov) -----------------------------------------------------------------
def test_records_are_counted_not_lines(tmp_path):
    f = tmp_path / "list.csv"
    write_csv(f, HEADER, [["p", "train", "p/part-00000.parquet", 0, "two\nlines"], ["p", "train", "p/part-00000.parquet", 1, "b"]])
    assert rp.csv_rows(f) == 2 and len(f.read_text(encoding="utf-8").splitlines()) == 4


@pytest.mark.parametrize("key, value, message", [("hash_cache", "yes", "hash_cache"), ("apply_workers", 0, "stages.apply.workers")])
def test_new_config_keys_are_checked(tmp_path, config, key, value, message):
    cfg = json.loads(config.read_text(encoding="utf-8"))
    if key == "hash_cache":
        cfg["hash_cache"] = value
    else:
        cfg["stages"]["apply"] = {"workers": value}
    config.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(rp.Stop, match=message):
        rp.run(config)


def test_a_resumed_run_reuses_the_hash_cache(tmp_path, config):
    first = rp.run(config)
    store = tmp_path / "runs" / "test-run" / "cache" / "sha256.json"
    assert store.is_file() and json.loads(store.read_text(encoding="utf-8"))["sha256"]
    run = rp.Run(config)
    m = run.execute(start="ledger")
    assert [s["digest"] for s in m["stages"]] == [s["digest"] for s in first["stages"]]
    new_files = [f for f in (tmp_path / "runs" / "test-run" / "ledger").rglob("*") if f.is_file() and f.suffix != ".json"]
    assert run.cache.misses == len(new_files) and run.cache.hits > 0  # only the rewritten ledger is read; the rest is cached


def test_without_the_hash_cache_the_digests_are_the_same(tmp_path, config, tsai_outputs):
    a = rp.run(config)
    cfg = write_config(tmp_path / "nocache.json", tsai_outputs, run_id="nocache")
    data = json.loads(cfg.read_text(encoding="utf-8"))
    data["hash_cache"] = False
    cfg.write_text(json.dumps(data), encoding="utf-8")
    b = rp.run(cfg)
    assert [s["digest"] for s in a["stages"]] == [s["digest"] for s in b["stages"]]
    assert not (tmp_path / "runs" / "nocache" / "cache").exists()


# --- Vijay's review of PR #46 (15 Nov) -------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["ledger.partial", "ledger.old", "deduped.lock", "ledger"])
def test_an_input_in_a_folder_the_run_writes_is_refused(tmp_path, tsai_outputs, name):
    """stages.clean.output at <run>/ledger.partial passed validation, and the ledger then deleted the cleaned parts. The
    config now stops before any stage runs, and the parts are untouched."""
    import shutil
    target = tmp_path / "runs" / "test-run" / name
    shutil.copytree(tsai_outputs["cleaned"], target)
    before = sorted(p.relative_to(target).as_posix() for p in target.rglob("*.parquet"))
    cfg = write_config(tmp_path / "c.json", {**tsai_outputs, "cleaned": target})
    with pytest.raises(rp.Stop, match="folder of the run itself"):
        rp.run(cfg)
    assert sorted(p.relative_to(target).as_posix() for p in target.rglob("*.parquet")) == before


def test_a_raw_folder_the_run_writes_is_refused(tmp_path, tsai_outputs):
    raw = tmp_path / "runs" / "test-run" / "ledger.old"
    raw.mkdir(parents=True)
    cfg = write_config(tmp_path / "c.json", tsai_outputs, ledger={"raw": str(raw)})
    with pytest.raises(rp.Stop, match="stages.ledger.raw .* is a folder of the run itself"):
        rp.run(cfg)
    assert raw.is_dir()
