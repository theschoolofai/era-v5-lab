"""Tests of tokens_per_text.py (arithmetic and the counting step; no model, no network).

    python -m pytest test_tokens_per_text.py -q
"""
import json, math, sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tokens_per_text as t  # noqa: E402


def test_make_chunks_joins_whole_lines_and_stops_at_max():
    lines = ["a" * 40, "", "b" * 40, "c" * 40, "d" * 40, "e" * 40, "f" * 10]
    ch = t.make_chunks(lines, 80, 2)
    assert len(ch) == 2 and ch[0] == "a" * 40 + "\n" + "b" * 40 and ch[1] == "c" * 40 + "\n" + "d" * 40


def test_make_chunks_drops_an_unfinished_last_chunk():
    assert t.make_chunks(["x" * 30, "y" * 30], 100, 5) == []


def test_fit_line_recovers_a_line():
    a, b = t.fit_line([0, 1000, 2000, 4000], [2.0 + 0.001 * x for x in (0, 1000, 2000, 4000)])
    assert math.isclose(a, 2.0, abs_tol=1e-9) and math.isclose(b, 0.001, abs_tol=1e-12)


def test_kv_bytes_per_token():
    assert t.kv_bytes_per_token(8, 2, 64) == 2 * 8 * 2 * 64 * 2 == 4096
    assert t.kv_bytes_per_token(8, 2, 64, 1) == 2048


def test_decode_seconds_is_steps_times_step_time_plus_the_context_term():
    assert math.isclose(t.decode_seconds(100, 2.0, 0.0), 0.2)                       # 100 steps x 2 ms
    assert math.isclose(t.decode_seconds(3, 2.0, 1.0), (3 * 2.0 + 1.0 * 3) / 1000)  # positions 0, 1, 2: 2 + 3 ms extra


COUNTS = {"chunk_chars": 1000, "tokenizers": ["base", "small"], "languages": {
    "hi": {"chunks": 2, "chars": 2000, "bytes": 5000, "words": 400, "tokens": {"base": 1000, "small": 600},
           "tokens_per_chunk": {"base": [500, 500], "small": [300, 300]}}}}
MODEL = {"points": [{"context": 0, "ms_per_token": 2.0}, {"context": 1000, "ms_per_token": 2.0}], "kv_bytes_per_token": 4096}


def test_project_scales_steps_time_and_kv_with_the_token_count():
    pr = t.project(COUNTS, MODEL, "base")["languages"]["hi"]
    assert pr["base"]["steps_per_1000_chars"] == 500 and pr["small"]["steps_per_1000_chars"] == 300
    assert math.isclose(pr["small"]["steps_vs_base"], 0.6) and pr["base"]["steps_vs_base"] == 1.0
    assert pr["small"]["kv_bytes_per_1000_chars"] == 300 * 4096
    assert math.isclose(pr["base"]["seconds_per_1000_chars"], 500 * 2.0 / 1000)     # flat step time: steps x 2 ms
    assert math.isclose(pr["small"]["seconds_vs_base"], 0.6)


def test_render_and_combine_write_the_tables(tmp_path):
    speed = {"machine": "test", "decode_tokens": 64, "models": {"m.gguf": MODEL}}
    md = t.render(COUNTS, speed, "base")
    assert "| hi | 500 | 300 (0.60x) |" in md and "## m.gguf" in md and "KV-cache KB" in md
    cp, sp, out = tmp_path / "c.json", tmp_path / "s.json", tmp_path / "o.md"
    cp.write_text(json.dumps(COUNTS)); sp.write_text(json.dumps(speed))
    ns = type("A", (), dict(counts=str(cp), speed=str(sp), base="base", out=str(out)))()
    assert t.combine_command(ns) == 0 and "Decode steps" in out.read_text()
    with pytest.raises(SystemExit):
        t.combine_command(type("A", (), dict(counts=str(cp), speed=str(sp), base="nope", out=str(out)))())


def test_count_command_on_a_tiny_tokenizer(tmp_path):
    tk = pytest.importorskip("tokenizers")
    from tokenizers import Tokenizer, models, pre_tokenizers
    vocab = {"[UNK]": 0, "ab": 1, "cd": 2, "a": 3, "b": 4, "c": 5, "d": 6}
    tok = Tokenizer(models.WordLevel(vocab, unk_token="[UNK]")); tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tpath = tmp_path / "tok.json"; tok.save(str(tpath))
    texts = tmp_path / "texts"; texts.mkdir()
    (texts / "xx.txt").write_text("\n".join(["ab cd ab cd ab cd ab cd"] * 6))
    out = tmp_path / "counts.json"
    ns = type("A", (), dict(texts=str(texts), tokenizer=[f"toy={tpath}"], chunk_chars=40, max_chunks=2, out=str(out)))()
    assert t.count_command(ns) == 0
    row = json.loads(out.read_text())["languages"]["xx"]
    assert row["chunks"] == 2 and row["tokens"]["toy"] == sum(row["tokens_per_chunk"]["toy"]) == row["words"]
