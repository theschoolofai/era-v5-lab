"""The experiment runner's plumbing: commands, summary and report. Fast; no tokenizer needed."""

import json
import sys
from pathlib import Path

import pytest

import run_experiment as rx


def test_run_accepts_paths_and_reports_failures(tmp_path):
    ok = rx._run([sys.executable, "-c", "import sys; print(sys.argv[1])", tmp_path / "x"])
    assert ok.stdout.strip() == str(tmp_path / "x")
    with pytest.raises(rx.subprocess.CalledProcessError):
        rx._run([sys.executable, "-c", "raise SystemExit(3)"])


def test_every_step_has_a_function():
    assert set(rx.STEPS) == set(rx.STEP_FUNCS)


def test_summary_and_report_survive_missing_outputs(tmp_path):
    ctx = rx.Context(tmp_path, (32, 64), tmp_path / "results", 16, 0)
    summary = rx.summarize(ctx)
    assert set(summary["per_pos_dim"]) == {"32", "64"}
    text = rx.render_markdown(summary, ctx.pos_dims)
    assert text.startswith("# KE2 experiment") and "P=64 raw" in text


def test_summary_reads_step_outputs(tmp_path):
    results = tmp_path / "results"

    def write(rel, data):
        path = results / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))

    write("tables/manifest.json", {
        "tokenizer": {"sha256": "abc", "vocab_size": 10},
        "max_raw_byte_length": 5,
        "tables": {"raw_table_P32.npz": {"sha256": "r32", "n_unique_rows": 10, "n_colliding_tokens": 0}},
    })  # fmt: skip
    write("proof_checks.json", {"P32_raw": {"float32": {"partitions_equal": True, "distinct_codes": 10},
                                            "bfloat16": {"partitions_equal": True}, "groups": 0}})  # fmt: skip
    write("decode_ref/summary.json", {"runs": {"raw_P32": {"vectors": 4, "ids_recovered": 4, "bytes_recovered": 4,
                                                           "ties": 0, "min_margin": 0.5, "median_margin": 0.9,
                                                           "fresh_process_sha256_equal": True, "sha256": "h"}}})  # fmt: skip
    write("tokenizer_decode_cpu_metadata.json", {"all_match": True, "runs": [{"sha256": "cpu"}] * 3})
    ctx = rx.Context(tmp_path, (32,), results, 4, 0)
    summary = rx.summarize(ctx)
    raw = summary["per_pos_dim"]["32"]["raw"]
    assert raw["table_sha256"] == "r32" and raw["theorem1_partitions_equal"] is True
    assert raw["decode_ref"]["ids_recovered"] == 4
    assert summary["cpu_decode_determinism"] == {"all_match": True, "sha256": "cpu", "runs": 3}
    text = rx.render_markdown(summary, ctx.pos_dims)
    assert "| decode_ref: IDs recovered | – | 4 / 4 |" in text
    assert "`cpu`" in text and "`h`" in text


def test_main_skips_every_step_and_still_writes_the_report(tmp_path):
    tok = tmp_path / "tok"
    tok.mkdir()
    md = tmp_path / "experiment.md"
    rc = rx.main(["--tokenizer-dir", str(tok), "--results", str(tmp_path / "results"), "--summary-md", str(md),
                  "--skip", *rx.STEPS])  # fmt: skip
    assert rc == 0 and md.is_file()
    assert Path(tmp_path / "results" / "experiment" / "summary.json").is_file()
