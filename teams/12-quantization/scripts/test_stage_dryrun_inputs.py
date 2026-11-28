"""Tests of stage_dryrun_inputs.py (no network).

    python -m pytest test_stage_dryrun_inputs.py -q
"""
import hashlib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage_dryrun_inputs as s  # noqa: E402

MANIFEST = {
    "sources": {"code_contests": {"dataset": "deepmind/code_contests", "revision": "rev1"},
                "hendrycks_math": {"dataset": "EleutherAI/hendrycks_math", "revision": "rev2"},
                "unused": {"dataset": "x/y", "revision": "rev3"}},
    "slots": [{"source": "code_contests", "status": "resolved", "file": "a.parquet", "file_sha256": "aa"},
              {"source": "code_contests", "status": "resolved", "file": "b.parquet", "file_sha256": "bb"},
              {"source": "hendrycks_math", "status": "resolved", "file": "algebra/t.parquet", "file_sha256": "cc"},
              {"source": "hendrycks_math", "status": "unresolved", "file": "skipped.parquet", "file_sha256": "dd"}],
}


def test_manifest_sources_keeps_resolved_slots_and_drops_empty_sources():
    out = s.manifest_sources(MANIFEST)
    assert set(out) == {"code_contests", "hendrycks_math"}
    assert out["code_contests"]["files"] == {"a.parquet": "aa", "b.parquet": "bb"}
    assert out["hendrycks_math"]["files"] == {"algebra/t.parquet": "cc"}


def test_hf_urls_try_the_plain_path_then_data():
    urls = s.hf_urls("deepmind/code_contests", "rev1", "a.parquet")
    assert urls == ["https://huggingface.co/datasets/deepmind/code_contests/resolve/rev1/a.parquet",
                    "https://huggingface.co/datasets/deepmind/code_contests/resolve/rev1/data/a.parquet"]


def test_sha256_file(tmp_path):
    p = tmp_path / "f"; p.write_bytes(b"abc")
    assert s.sha256_file(p) == hashlib.sha256(b"abc").hexdigest()


def test_head_commit_detached_ref_and_packed(tmp_path):
    git = tmp_path / ".git"; git.mkdir()
    (git / "HEAD").write_text("deadbeef\n")
    assert s.head_commit(tmp_path) == "deadbeef"
    (git / "HEAD").write_text("ref: refs/heads/main\n")
    assert s.head_commit(tmp_path) is None
    (git / "packed-refs").write_text("# pack\n1234abcd refs/heads/main\n")
    assert s.head_commit(tmp_path) == "1234abcd"
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "refs" / "heads" / "main").write_text("feedface\n")
    assert s.head_commit(tmp_path) == "feedface"
    assert s.head_commit(tmp_path / "nowhere") is None


def test_check_flags_missing_sources(tmp_path, capsys):
    mf = tmp_path / "m.json"; mf.write_text(json.dumps(MANIFEST))
    args = type("A", (), dict(manifest=mf, inputs=tmp_path / "in", work=tmp_path / "w", tokenizer=None, model=None))()
    assert s.check(args) == 1
    assert "FAIL  code_contests: 2 pinned files" in capsys.readouterr().out


def test_pinned_constants_are_consistent():
    assert s.LLAMA_COMMIT.startswith("620d222") and s.LLAMA_TAG == f"b{s.LLAMA_BUILD}"
