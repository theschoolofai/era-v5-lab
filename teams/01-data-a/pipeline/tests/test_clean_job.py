"""The pipeline's clean job (pipeline/clean_job.py), with made-up rows only.

  python -m pytest teams/01-data-a/pipeline/tests/test_clean_job.py -q      (from the repository root)

The real job and the real spec v1.1 clean.py run on four tiny parts. Covers the job's input checks (the cleaner's pin, the
manifest, the config), the per-part processing and its counts, and resume: a failure is injected into one part, then the
job is run again with "resume": true.
"""
import csv
import json
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import clean_job as job
from conftest import PIPELINE

CLEAN = (PIPELINE.parent / "spec_v1_1" / "clean.py").resolve()
PIN = job.digest(CLEAN)
job.load_clean(CLEAN, PIN)
PARTS = [("train", "en-dclm", 0), ("train", "en-dclm", 1), ("heldout", "en-dclm", 0), ("train", "cadj-commits", 0)]
TEXTS = ["Area of a circle.\n", "Area​ of a circle.\n", "Subscribe to our newsletter\n"]


def write_part(root, split, pack, n, texts=TEXTS):
    """One made-up raw part under root/split/pack; returns its manifest entry."""
    rows = [dict(doc_id=f"{split}-{pack}-{n}-d{i}", text=text, pack_id=pack, lang_label="en", url="") for i, text in enumerate(texts)]
    path = root / split / pack / f"part-{n:05d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), path)
    return dict(path=f"{split}/{pack}/part-{n:05d}.parquet", pack_id=pack, split=split, rows=len(rows),
                bytes=path.stat().st_size, sha256=job.digest(path))


def write_manifest(path, shards):
    path.write_text(json.dumps(dict(name="made up", total_docs=sum(s["rows"] for s in shards), shards=shards)))
    return job.digest(path)


@pytest.fixture
def sample(tmp_path, monkeypatch):
    """Four made-up parts, a manifest for them, and a config; the job runs from tmp_path (it writes below ./out)."""
    monkeypatch.chdir(tmp_path)
    shards = [write_part(tmp_path / "input", *part) for part in PARTS]
    config = dict(clean=str(CLEAN), clean_sha256=PIN, manifest=str(tmp_path / "manifest.json"),
                  manifest_sha256=write_manifest(tmp_path / "manifest.json", shards), expected_parts={"train": 3, "heldout": 1},
                  batch_size=2, unsupported_policy="passthrough_with_explicit_status", audit_samples=5, input_root="input", output_root="out/job")

    def run(out="out/job", resume=False, only=(), drop=(), **extra):
        data = {k: v for k, v in dict(config, output_root=out, **({"resume": resume} if resume is not False else {}), **extra).items()
                if k not in drop}
        path = tmp_path / f"config-{out.replace('/', '_')}.json"
        path.write_text(json.dumps(data))
        return job.main(["--config", str(path), "--input-root", str(tmp_path / "input"), *[a for p in only for a in ("--only", p)]])

    run.config = config
    return tmp_path, shards, run


def fail_on(monkeypatch, part):
    real = job.process_part

    def flaky(source, shard, output, batch_size, **more):
        if shard["path"] == part:
            raise job.JobError("injected failure: " + part)
        return real(source, shard, output, batch_size, **more)

    monkeypatch.setattr(job, "process_part", flaky)


def outputs(folder):
    """What a finished job must make the same however it got there: each part's bytes, the rule counts, the cleaned manifest."""
    manifest = json.loads((folder / "cleaned_manifest.json").read_text())
    return (manifest, (folder / "rule_counts.csv").read_text(),
            {p["part"]: job.digest(folder / p["part"]) for p in manifest["parts"]})


def interrupted(monkeypatch, run, part="train/en-dclm/part-00001.parquet"):
    """Run the job until it fails on `part`: parts before it are finished, the others are not started."""
    with monkeypatch.context() as m:
        fail_on(m, part)
        with pytest.raises(job.JobError, match="injected failure"):
            run()


# --- the cleaner: the file the config names, once its sha256 is the pin ----------------------------------------------------
def test_the_cleaner_is_the_file_the_config_names_and_the_job_reports_it(sample):
    tmp, shards, run = sample
    assert run() == 0
    assert Path(job.clean.__file__).resolve() == CLEAN
    summary = json.loads((tmp / "out/job/job_summary.json").read_text())
    assert (summary["clean_sha256"], summary["clean_path"]) == (PIN, str(CLEAN))


def test_the_cleaner_is_not_run_unless_it_has_the_pinned_sha256(tmp_path, monkeypatch):
    fake = tmp_path / "clean.py"
    fake.write_text(f"open({str(tmp_path / 'ran')!r}, 'w').close()\n")
    monkeypatch.setattr(job, "clean", job.clean)  # load_clean replaces it; put the real one back afterwards
    with pytest.raises(job.JobError, match="clean.py differs from the pin: .*, the config pins 111111111111"):
        job.load_clean(fake, "1" * 64)
    assert not (tmp_path / "ran").exists()  # the file was hashed, not run
    module = job.load_clean(fake, job.digest(fake))
    assert (tmp_path / "ran").exists() and module.__file__ == str(fake) and job.clean is module


def test_a_cleaner_that_is_not_there_is_named(tmp_path):
    with pytest.raises(job.JobError, match="the cleaner .*nowhere.py is not there"):
        job.load_clean(tmp_path / "nowhere.py", PIN)


def test_a_config_with_another_pin_stops_the_job_before_anything_is_written(sample):
    tmp, shards, run = sample
    with pytest.raises(job.JobError, match="clean.py differs from the pin"):
        run(clean_sha256="0" * 64)
    assert not (tmp / "out").exists()


# --- the input set: any manifest that matches the run config ---------------------------------------------------------------
def test_a_manifest_of_any_size_is_accepted_when_the_config_says_so(sample):
    tmp, shards, run = sample
    one = tmp / "one.json"
    pin = write_manifest(one, shards[:1])  # one part, not the 86 of sample v0
    assert run(manifest=str(one), manifest_sha256=pin, expected_parts={"train": 1}) == 0
    summary = json.loads((tmp / "out/job/job_summary.json").read_text())
    assert summary["completed_parts"] == summary["expected_parts"] == 1 and summary["scope"] == "full manifest"


def test_a_manifest_that_is_not_the_pinned_file_stops_the_job(sample):
    tmp, shards, run = sample
    with pytest.raises(job.JobError, match="manifest.json has sha256 .*, the pin is 000000000000"):
        run(manifest_sha256="0" * 64)
    assert not (tmp / "out").exists()


def test_a_manifest_that_does_not_match_expected_parts_stops_the_job(sample):
    tmp, shards, run = sample
    with pytest.raises(job.JobError, match="expected_parts says"):
        run(expected_parts={"train": 48, "heldout": 38})
    assert not (tmp / "out").exists()


def test_only_must_name_parts_of_the_manifest(sample):
    tmp, shards, run = sample
    with pytest.raises(job.JobError, match="not in the manifest: train/en-dclm/part-00009.parquet"):
        run(only=["train/en-dclm/part-00009.parquet"])
    assert not (tmp / "out").exists()


def test_only_runs_those_parts_and_says_the_run_is_partial(sample):
    tmp, shards, run = sample
    assert run(only=["train/en-dclm/part-00001.parquet"]) == 0
    summary = json.loads((tmp / "out/job/job_summary.json").read_text())
    assert summary["scope"] == "partial (--only)" and summary["completed_parts"] == 1 and summary["expected_parts"] == 4
    assert json.loads((tmp / "out/job/cleaned_manifest.json").read_text())["complete_sample"] is False


@pytest.mark.parametrize("key", ["clean", "clean_sha256", "manifest", "manifest_sha256", "expected_parts", "batch_size", "unsupported_policy", "audit_samples"])
def test_a_config_without_a_required_key_names_it(sample, key):
    tmp, shards, run = sample
    with pytest.raises(job.JobError, match=f"the config lacks .*{key}"):
        run(drop=(key,))
    assert not (tmp / "out").exists()


def test_a_config_without_folders_needs_them_on_the_command_line(sample):
    tmp, shards, run = sample
    config = tmp / "c.json"
    config.write_text(json.dumps({k: v for k, v in run.config.items() if k not in ("input_root", "output_root")}))
    with pytest.raises(job.JobError, match="lacks input_root or output_root"):
        job.main(["--config", str(config)])


@pytest.mark.parametrize("extra, why", [(dict(optional_f2=True), "F2 is its own stage"),
                                        (dict(unsupported_policy="drop"), "unsupported pack policy must be explicit"),
                                        (dict(batch_size=0), "batch_size must be a positive integer"),
                                        (dict(batch_size="2"), "batch_size must be a positive integer"),
                                        (dict(batch_size=True), "batch_size must be a positive integer"),
                                        (dict(audit_samples=-1), "audit_samples must be a whole number"),
                                        (dict(audit_samples="5"), "audit_samples must be a whole number"),
                                        (dict(audit_samples=True), "audit_samples must be a whole number")])
def test_settings_the_job_does_not_accept_are_refused(sample, extra, why):
    tmp, shards, run = sample
    with pytest.raises(job.JobError, match=why):
        run(**extra)
    assert not (tmp / "out").exists()


# --- one part -----------------------------------------------------------------------------------------------------------
def part(tmp_path, pack="en-dclm", split="train"):
    shard = write_part(tmp_path / "input", split, pack, 0)
    path = tmp_path / "input" / shard["path"]
    rows = pq.read_table(path).to_pylist()
    return path, shard, rows


@pytest.mark.parametrize("platform, rss", [("darwin", 512 * 1024 * 1024), ("linux", 512 * 1024)])
def test_peak_memory_uses_platform_units(platform, rss, monkeypatch):
    monkeypatch.setattr(job, "resource", SimpleNamespace(RUSAGE_SELF=0, getrusage=lambda _: SimpleNamespace(ru_maxrss=rss)))
    monkeypatch.setattr(job.sys, "platform", platform)
    assert job.peak_rss_mib() == 512.0


def test_peak_memory_is_unavailable_without_resource(monkeypatch):
    monkeypatch.setattr(job, "resource", None)
    assert job.peak_rss_mib() is None


def test_counting_runs_actual_cleaner_with_identical_results():
    rows = [dict(doc_id="d", text=t, pack_id="en-dclm", lang_label="en", url="") for t in TEXTS]
    expected = [job.clean.clean(row) for row in rows]
    original_run, original_ids = job.clean._run, dict(job.clean._ID)
    counter = job.RuleCounter()
    with counter.instrument():
        assert [job.clean.clean(row) for row in rows] == expected
    assert job.clean._run is original_run and job.clean._ID == original_ids
    assert counter.counts["DA-A1-004"]["fix"] == 1
    assert sum(counter.counts["DA-F1-005"].values()) == 2  # drop short-circuits later rules


def test_streaming_output_and_rule_counts_match_cleaner(tmp_path):
    path, shard, rows = part(tmp_path)
    out = tmp_path / "out"
    result = job.process_part(path, shard, out, batch_size=1)
    expected = [(row["doc_id"], job.clean.clean(row)) for row in rows]
    written = pq.read_table(out / shard["path"]).to_pylist()
    assert [(row["doc_id"], row["text"]) for row in written] == [(d, value[1]) for d, value in expected if value[0] != "drop"]
    assert result["actions"] == {"keep": 1, "fix": 1, "drop": 1}
    assert result["rule_counts"]["DA-F1-005"]["not_reached"] == 1
    assert result["input_rows"] == result["output_rows"] + result["actions"]["drop"]
    with pytest.raises(job.JobError, match="overwrite"):
        job.process_part(path, shard, out, 1)


def test_unknown_pack_is_explicit_passthrough(tmp_path):
    path, shard, rows = part(tmp_path, "cadj-commits")
    out = tmp_path / "out"
    result = job.process_part(path, shard, out, 2)
    assert result["status"] == "unsupported_passthrough"
    assert result["rule_counts"] == {} and result["actions"] == {"keep": 3}
    assert pq.read_table(out / shard["path"]).to_pylist() == rows


def test_heldout_and_train_outputs_are_separate(tmp_path):
    out = tmp_path / "out"
    for split in ("train", "heldout"):
        path, shard, _ = part(tmp_path, split=split)
        job.process_part(path, shard, out, 2)
    assert (out / "train/en-dclm/part-00000.parquet").is_file()
    assert (out / "heldout/en-dclm/part-00000.parquet").is_file()


def test_hash_resolution_handles_browser_rename_but_rejects_wrong_bytes(tmp_path):
    path, shard, _ = part(tmp_path)
    target = tmp_path / "organized/en-dclm/train/part-00000_part2.parquet"
    target.parent.mkdir(parents=True)
    path.rename(target)
    assert job.resolve_input(tmp_path / "organized", shard, {}) == target
    target.write_bytes(b"wrong data")
    with pytest.raises(job.JobError, match="checksum"):
        job.resolve_input(tmp_path / "organized", shard, {})


def test_errors_are_counted_and_partial_output_is_not_published(tmp_path, monkeypatch):
    path, shard, _ = part(tmp_path)

    def broken(doc):
        raise ValueError("synthetic private content that must not appear in reports")

    monkeypatch.setattr(job.clean, "_PIPELINES", {"english": (lambda: broken,)})
    # Replace the registered factory consistently so the actual clean() path raises.
    failed_factory = job.clean._PIPELINES["english"][0]
    monkeypatch.setattr(job.clean, "_RULE", {"DA-A1-004": failed_factory, "f1_rule.py": job.clean._shared_f1_rule})
    monkeypatch.setattr(job.clean, "_ID", {failed_factory: "DA-A1-004", job.clean._shared_f1_rule: "f1_rule.py"})
    out = tmp_path / "out"
    with pytest.raises(job.JobError, match="ValueError"):
        job.process_part(path, shard, out, 1)
    text = (out / "failure.json").read_text()
    assert "synthetic private content" not in text
    assert json.loads(text)["rule_counts"]["DA-A1-004"]["error"] == 1
    assert not (out / shard["path"]).exists()


def test_output_and_part_paths_are_bounded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert job.output_folder("out/job") == tmp_path / "out/job"
    for bad in ("out", "../elsewhere", "/tmp/elsewhere"):
        with pytest.raises(job.JobError, match="output"):
            job.output_folder(bad)
    with pytest.raises(job.JobError, match="unexpected part path"):
        job.safe_path("../train/escape.parquet")
    with pytest.raises(job.JobError, match="unexpected part path"):
        job.safe_path("val/en-dclm/part-00000.parquet")  # only train and heldout


def test_all_dropped_part_still_has_a_valid_parquet_schema(tmp_path):
    shard = write_part(tmp_path / "input", "train", "en-dclm", 0, texts=["Subscribe to our newsletter\n"] * 3)
    path = tmp_path / "input" / shard["path"]
    out = tmp_path / "out"
    result = job.process_part(path, shard, out, 1)
    table = pq.read_table(out / shard["path"])
    assert table.num_rows == result["output_rows"] == 0
    assert table.schema == pq.read_schema(path)
    assert result["actions"] == {"drop": 3}


def test_aggregate_includes_zero_rules_and_explicit_partial_manifest(tmp_path):
    path, shard, _ = part(tmp_path, "cadj-commits")
    out = tmp_path / "out"
    report = job.process_part(path, shard, out, 2)
    summary = job.write_aggregate(out, [report], {"sample": "synthetic"}, 86)
    assert summary["unsupported_parts"] == [shard["path"]]
    assert json.loads((out / "cleaned_manifest.json").read_text())["complete_sample"] is False
    counts = list(csv.DictReader((out / "rule_counts.csv").open()))
    assert len(counts) == len(job.clean._RULE)
    assert all(row["invocations"] == "0" for row in counts)


# --- resume --------------------------------------------------------------------------------------------------------------
def test_a_fresh_job_writes_its_state_and_one_attempt(sample):
    tmp, shards, run = sample
    assert run() == 0
    out = tmp / "out/job"
    state = json.loads((out / "job_state.json").read_text())
    assert [a["status"] for a in state["attempts"]] == ["complete"] and state["attempts"][0]["resumed"] is False
    assert sorted(state["fingerprint"]) == ["clean_sha256", "manifest_sha256", "runner_sha256", "selected_parts"]
    summary = json.loads((out / "job_summary.json").read_text())
    assert summary["resumed_parts"] == 0 and summary["completed_parts"] == 4 and summary["attempts"] == state["attempts"]


def test_an_interrupted_job_is_not_continued_without_resume_and_nothing_changes(sample, monkeypatch):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    out = tmp / "out/job"
    before = sorted((p.relative_to(out).as_posix(), p.stat().st_mtime_ns) for p in out.rglob("*") if p.is_file())
    with pytest.raises(job.JobError, match='"resume": true'):
        run()
    assert before == sorted((p.relative_to(out).as_posix(), p.stat().st_mtime_ns) for p in out.rglob("*") if p.is_file())


def test_resume_finishes_the_job_with_the_output_of_a_job_that_was_never_interrupted(sample, monkeypatch):
    tmp, shards, run = sample
    run(out="out/fresh")
    interrupted(monkeypatch, run)
    out = tmp / "out/job"
    assert (out / "train/en-dclm/part-00000.parquet").is_file() and not (out / "train/en-dclm/part-00001.parquet").exists()
    assert run(resume=True) == 0
    assert outputs(out) == outputs(tmp / "out/fresh")
    summary = json.loads((out / "job_summary.json").read_text())
    assert summary["resumed_parts"] == 1 and summary["completed_parts"] == 4
    statuses = [a["status"] for a in summary["attempts"]]
    assert statuses == ["failed", "complete"] and summary["attempts"][1]["resumed"] and summary["attempts"][1]["kept_parts"] == 1
    assert "injected failure" in summary["attempts"][0]["error"]
    assert not (out / "failure.json").exists()


def test_the_failure_record_of_an_earlier_attempt_is_kept_in_its_attempt(sample, monkeypatch):
    tmp, shards, run = sample
    out = tmp / "out/job"
    out.mkdir(parents=True)
    interrupted(monkeypatch, run)
    (out / "failure.json").write_text(json.dumps({"part": "x", "doc_id": "d", "error_type": "ValueError"}))  # as process_part writes it
    run(resume=True)
    state = json.loads((out / "job_state.json").read_text())
    assert state["attempts"][0]["failure"] == {"part": "x", "doc_id": "d", "error_type": "ValueError"}
    assert not (out / "failure.json").exists()


def test_a_killed_attempt_is_recorded_as_interrupted(sample, monkeypatch):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    out = tmp / "out/job"
    state = json.loads((out / "job_state.json").read_text())
    state["attempts"][0].update(status="running")  # a process that was killed never wrote how it ended
    (out / "job_state.json").write_text(json.dumps(state))
    run(resume=True)
    assert [a["status"] for a in json.loads((out / "job_state.json").read_text())["attempts"]] == ["interrupted", "complete"]


def test_a_part_without_its_report_and_a_tmp_file_are_redone(sample, monkeypatch):
    tmp, shards, run = sample
    run(out="out/fresh")
    interrupted(monkeypatch, run, part="train/cadj-commits/part-00000.parquet")  # the first three parts are finished
    out = tmp / "out/job"
    (out / "reports/train/en-dclm/part-00001.parquet.json").unlink()  # published, but killed before its report
    (out / "heldout/en-dclm/part-00000.parquet.tmp").write_bytes(b"half a part")
    run(resume=True)
    assert not (out / "heldout/en-dclm/part-00000.parquet.tmp").exists()
    assert outputs(out) == outputs(tmp / "out/fresh")
    assert json.loads((out / "job_summary.json").read_text())["resumed_parts"] == 2


def test_a_finished_part_that_does_not_verify_stops_the_job_naming_the_part_and_the_files_to_delete(sample, monkeypatch):
    tmp, shards, run = sample
    run(out="out/fresh")
    interrupted(monkeypatch, run, part="train/cadj-commits/part-00000.parquet")
    out = tmp / "out/job"
    bad = out / "train/en-dclm/part-00001.parquet"
    bad.write_bytes(bad.read_bytes() + b"x")
    orphan = out / "heldout/en-dclm/part-00000.parquet"
    (out / "reports/heldout/en-dclm/part-00000.parquet.json").unlink()  # would be redone, but only after every check passes
    with pytest.raises(job.JobError) as stop:
        run(resume=True)
    message = str(stop.value)
    assert "train/en-dclm/part-00001.parquet" in message and "nothing was changed" in message
    assert "out/job/train/en-dclm/part-00001.parquet and out/job/reports/train/en-dclm/part-00001.parquet.json" in message
    assert orphan.exists()  # not deleted: the job stopped before changing anything
    # the two files it names are deleted, and the next run goes on from there
    bad.unlink()
    (out / "reports/train/en-dclm/part-00001.parquet.json").unlink()
    assert run(resume=True) == 0
    assert outputs(out) == outputs(tmp / "out/fresh")


@pytest.mark.parametrize("damage, why", [
    (lambda r: r.update(input_sha256="1" * 64), "input_sha256"),
    (lambda r: r.update(output_rows=r["output_rows"] + 1), "add up"),
    (lambda r: r.update(status="unsupported_passthrough"), "status"),
    (lambda r: r.update(errors=1), "errors"),
])
def test_a_report_that_disagrees_with_the_manifest_or_the_part_is_named(sample, monkeypatch, damage, why):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    report_path = tmp / "out/job/reports/train/en-dclm/part-00000.parquet.json"
    report = json.loads(report_path.read_text())
    damage(report)
    report_path.write_text(json.dumps(report))
    with pytest.raises(job.JobError, match=f"train/en-dclm/part-00000.parquet: .*({why})"):
        run(resume=True)


def test_a_part_with_other_rows_than_its_report_is_named(sample, monkeypatch):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    out = tmp / "out/job"
    part_file = out / "train/en-dclm/part-00000.parquet"
    pq.write_table(pq.read_table(part_file).slice(0, 1), part_file)  # a valid Parquet file, but not the part the report describes
    with pytest.raises(job.JobError, match="train/en-dclm/part-00000.parquet: the part has 1 rows, its report says 2"):
        run(resume=True)


def test_a_report_without_its_part_is_named(sample, monkeypatch):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    (tmp / "out/job/train/en-dclm/part-00000.parquet").unlink()
    with pytest.raises(job.JobError, match="train/en-dclm/part-00000.parquet: a report without its part"):
        run(resume=True)


@pytest.mark.parametrize("key", ["clean_sha256", "runner_sha256", "manifest_sha256", "selected_parts"])
def test_a_job_started_with_something_else_is_not_resumed(sample, monkeypatch, key):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    state_path = tmp / "out/job/job_state.json"
    state = json.loads(state_path.read_text())
    state["fingerprint"][key] = "1" * 64 if key != "selected_parts" else ["train/en-dclm/part-00000.parquet"]
    state_path.write_text(json.dumps(state))
    with pytest.raises(job.JobError, match=f"cannot resume: the job was started with another {key}"):
        run(resume=True)


def test_a_different_part_selection_is_not_resumed(sample, monkeypatch):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    with pytest.raises(job.JobError, match="another selected_parts"):
        run(resume=True, only=["train/en-dclm/part-00000.parquet"])


def test_a_finished_job_is_never_resumed_or_overwritten(sample):
    tmp, shards, run = sample
    run()
    before = (tmp / "out/job/job_summary.json").read_bytes()
    for resume in (False, True):
        with pytest.raises(job.JobError, match="finished job"):
            run(resume=resume)
    assert (tmp / "out/job/job_summary.json").read_bytes() == before


def test_a_folder_that_is_not_a_job_of_this_runner_is_not_resumed(sample):
    tmp, shards, run = sample
    (tmp / "out/job").mkdir(parents=True)
    (tmp / "out/job/something.txt").write_text("x")
    for resume in (False, True):
        with pytest.raises(job.JobError, match="not an interrupted job"):
            run(resume=resume)


def test_resume_with_no_folder_yet_is_a_fresh_job(sample):
    tmp, shards, run = sample
    assert run(resume=True) == 0
    state = json.loads((tmp / "out/job/job_state.json").read_text())
    assert state["attempts"][0]["resumed"] is False


def test_resume_must_be_true_or_false(sample):
    tmp, shards, run = sample
    with pytest.raises(job.JobError, match="resume must be true or false"):
        run(resume="yes")
    assert not (tmp / "out/job").exists()


def test_resume_skips_hashing_the_inputs_of_finished_parts(sample, monkeypatch):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    asked = []
    real = job.resolve_input
    monkeypatch.setattr(job, "resolve_input", lambda root, shard, hashes: asked.append(shard["path"]) or real(root, shard, hashes))
    run(resume=True)
    assert asked == ["train/en-dclm/part-00001.parquet", "heldout/en-dclm/part-00000.parquet", "train/cadj-commits/part-00000.parquet"]


def test_the_rule_counts_of_a_resumed_job_are_the_sum_of_every_part(sample, monkeypatch):
    tmp, shards, run = sample
    interrupted(monkeypatch, run)
    run(resume=True)
    rows = {r["rule_id"]: r for r in csv.DictReader((tmp / "out/job/rule_counts.csv").open())}
    reports = [json.loads(p.read_text()) for p in sorted((tmp / "out/job/reports").rglob("*.json"))]
    for rid, row in rows.items():
        for kind in ("keep", "fix", "drop", "error"):
            assert int(row[kind]) == sum(r["rule_counts"].get(rid, {}).get(kind, 0) for r in reports)
