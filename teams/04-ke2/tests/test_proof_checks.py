"""Theorem 1 on the real tokenizer (proof.md section 4), and results/proof_checks.json against a fresh run.

Skipped unless BRAHMIC_TOKENIZER_DIR points to a folder with tokenizer.json and special_tokens_map.json.
"""

import json
import os
from pathlib import Path

import pytest

from forward import CAUSES

tok_dir = os.environ.get("BRAHMIC_TOKENIZER_DIR")
pytestmark = pytest.mark.skipif(
    not (tok_dir and (Path(tok_dir) / "tokenizer.json").is_file()),
    reason="set BRAHMIC_TOKENIZER_DIR to run on the real tokenizer",
)
RESULTS = Path(__file__).resolve().parents[1] / "results" / "proof_checks.json"
_cache = {}


def result():
    """Run the check once per test session (it takes about two minutes)."""
    if "r" not in _cache:
        pytest.importorskip("tokenizers")
        from proof_checks import run

        _cache["r"] = run(Path(tok_dir))
    return _cache["r"]


def test_raw_table_has_no_collision():
    res = result()
    for P in (32, 64):
        for dtype in ("float32", "bfloat16"):
            r = res[f"P{P}_raw"][dtype]
            assert r["distinct_codes"] == res["vocab"], (P, dtype)
            assert r["partitions_equal"], (P, dtype)
        assert res[f"P{P}_raw"]["groups"] == 0, P


def test_theorem1_on_decode_table():
    res = result()
    for P in (32, 64):
        for dtype in ("float32", "bfloat16"):
            assert res[f"P{P}_decode"][dtype]["partitions_equal"], (P, dtype)
        causes = res[f"P{P}_decode"]["pair_causes"]
        assert None not in causes, P  # every colliding pair has a cause
        assert set(causes) <= set(CAUSES), P


def test_results_file_matches_a_fresh_run():
    saved = json.loads(RESULTS.read_text(encoding="utf-8"))
    saved.pop("env", None)
    if saved["tokenizer_json_sha256"] != result()["tokenizer_json_sha256"]:
        pytest.skip("results/proof_checks.json was made with another tokenizer.json")
    assert saved == json.loads(json.dumps(result()))
