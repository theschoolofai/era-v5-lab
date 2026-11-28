"""Tests for ke2/heldout_code.py (R3): the cleaner pin and its CRLF form, identifier counts, the out-folder checks."""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import heldout_code as hc  # noqa: E402

CLEANER = b'def clean(doc):\n    return ("keep", doc["text"])\n'
PIN = hashlib.sha256(CLEANER).hexdigest()


def test_cleaner_with_the_pinned_bytes_loads(tmp_path):
    p = tmp_path / "clean.py"
    p.write_bytes(CLEANER)
    mod, crlf = hc.load_cleaner(p, PIN)
    assert crlf is False
    assert mod.clean({"text": "x"}) == ("keep", "x")


def test_cleaner_with_crlf_runs_its_lf_form(tmp_path):
    p = tmp_path / "clean.py"
    p.write_bytes(CLEANER.replace(b"\n", b"\r\n"))
    mod, crlf = hc.load_cleaner(p, PIN)
    assert crlf is True
    assert mod.clean({"text": "y"}) == ("keep", "y")


def test_cleaner_off_the_pin_is_refused(tmp_path):
    p = tmp_path / "clean.py"
    p.write_bytes(CLEANER + b"# changed\n")
    with pytest.raises(SystemExit, match="differs from the pin"):
        hc.load_cleaner(p, PIN)


def test_compound_identifiers():
    got = hc.identifiers(["x_velocity = xVelocity + speed", "x_velocity; _private; HTTPServer; a1_b2"])
    # x_velocity (twice), xVelocity, a1_b2 are compound; speed, _private (no inner _), HTTPServer (no lower-to-upper) are not
    assert got == {"compound_distinct": 3, "compound_total": 4}


def test_text_key_is_exact():
    assert hc.text_key("a b") == hc.text_key("a b")
    assert hc.text_key("a b") != hc.text_key("a  b")
    assert hc.text_key(None) == hc.text_key("")


def test_out_must_be_inside_repo_out(tmp_path):
    with pytest.raises(SystemExit, match="inside the repository's out/"):
        hc.main(["--packs", str(tmp_path), "--out", str(tmp_path / "r3")])


def test_out_must_be_empty(tmp_path):
    out = hc.REPO / "out" / "test_heldout_code_not_empty"
    out.mkdir(parents=True, exist_ok=True)
    (out / "x").write_text("x")
    try:
        with pytest.raises(SystemExit, match="is not empty"):
            hc.main(["--packs", str(tmp_path), "--out", str(out)])
    finally:
        (out / "x").unlink()
        out.rmdir()
