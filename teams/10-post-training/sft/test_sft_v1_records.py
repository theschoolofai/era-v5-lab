"""Tests for sft_v1_worklist.py, sft_v1_records.py and the batched path of convert.py.

Fixture rows are hand-written; the toy tokenizer is a character-level one built here, so no data and no external
tokenizer file is needed.
"""

from __future__ import annotations

import importlib.util
import json
import string
from pathlib import Path

import pytest

tokenizers = pytest.importorskip("tokenizers")
np = pytest.importorskip("numpy")

HERE = Path(__file__).resolve().parent

# A named decorator: pr-guard takes a dotted decorator line of a diff for an email address.
fixture = pytest.fixture


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


convert = _load("g10_convert_t", "convert.py")
records = _load("g10_records_t", "sft_v1_records.py")
worklist = _load("g10_worklist_t", "sft_v1_worklist.py")
T = convert.T


@fixture(scope="module")
def toy_tokenizer(tmp_path_factory) -> str:
    """One token per character plus the nine chat markers as added (special) tokens."""
    from tokenizers import Regex, Tokenizer, decoders, models, normalizers, pre_tokenizers

    chars = string.printable + "éèàǜ"
    vocab = {c: i for i, c in enumerate(dict.fromkeys(chars))}
    vocab["[UNK]"] = len(vocab)
    tok = Tokenizer(models.WordLevel(vocab, unk_token="[UNK]"))
    tok.normalizer = normalizers.NFC()
    tok.pre_tokenizer = pre_tokenizers.Split(Regex("[\\s\\S]"), "isolated")
    tok.decoder = decoders.Fuse()
    tok.add_special_tokens([T[k] for k in ("endoftext", "im_start", "im_end", "think", "think_end", "tool_call",
                                           "tool_call_end", "tool_result", "tool_result_end")])
    path = tmp_path_factory.mktemp("tok") / "toy.json"
    tok.save(str(path))
    return str(path)


COMMIT = {"commit": "c", "instruction": "Write add(a, b).", "response": "def add(a, b):\n    return a + b\n"}
CODEFORCES = {"id": "1/A", "finish_reason": "stop", "messages": [
    {"role": "user", "content": "Sum two numbers."},
    {"role": "assistant", "content": "<think>\nRead, add.\n</think>\n\nprint(1 + 1)"}]}
AGENT = {"uuid": "u1", "tools": [{"name": "f", "parameters": {}}], "messages": [
    {"role": "user", "content": "Call f."},
    {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "f", "arguments": {"x": 1}}, "id": "c1"}]},
    {"role": "tool", "content": "42"},
    {"role": "assistant", "content": "It returned 42."}]}


def _write_rows(toy, set_id, rows, tmp_path, limit=None):
    out = tmp_path / "o.jsonl"
    with open(out, "w", encoding="utf-8") as sink:
        _, manifest = convert.convert(set_id, rows, limit, toy, 0, sink)
    return out, manifest


def test_batched_convert_equals_row_by_row(toy_tokenizer, tmp_path):
    """Chunked `encode_batch` gives the lines, counters and hash of one-row-at-a-time processing."""
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(toy_tokenizer)
    rows = [CODEFORCES, dict(CODEFORCES, finish_reason="length"), CODEFORCES] * 40  # 120 rows: several chunks, mixed skips
    _, manifest = _write_rows(toy_tokenizer, "sft-code-codeforces-cots", rows, tmp_path)
    digest, lines = __import__("hashlib").sha256(), 0
    skipped = {}
    for i, row in enumerate(rows):  # reference: the pre-batching loop, written out with convert_row
        try:
            effort, text, spans = convert.convert_row(convert.codeforces_cots(row), lambda t: len(tok.encode(t, add_special_tokens=False).ids))
        except convert.Skip as exc:
            skipped[str(exc)] = skipped.get(str(exc), 0) + 1
            continue
        enc = tok.encode(text, add_special_tokens=False)
        sample = {"id": f"sft-code-codeforces-cots/{i}", "set": "sft-code-codeforces-cots", "source_id": row["id"], "effort": effort,
                  "text": text, "train_spans": [list(s) for s in spans], "input_ids": enc.ids,
                  "loss_mask": convert.token_mask(spans, enc.offsets)}
        digest.update((json.dumps(sample, ensure_ascii=False) + "\n").encode("utf-8"))
        lines += 1
    assert manifest["rows"] == lines == 80 and manifest["skipped"] == skipped
    assert manifest["content_sha256"] == digest.hexdigest()


def test_limit_stops_inside_a_chunk(toy_tokenizer, tmp_path):
    _, manifest = _write_rows(toy_tokenizer, "sft-code-commitpackft", [COMMIT] * 100, tmp_path, limit=37)
    assert manifest["rows_in"] == 37 and manifest["rows_scanned"] == 37 and manifest["rows"] == 37


def test_record_checks_pass_on_clean_rows_and_count_tool_blocks(toy_tokenizer, tmp_path):
    out, _ = _write_rows(toy_tokenizer, "sft-agentic-nemotron-agentic-v1", [AGENT, dict(AGENT, uuid="u2")], tmp_path)
    res = records.check_files([out], toy_tokenizer)
    assert res["checks_ok"], res["checks_failed"]
    assert res["rows"] == 2 and res["tool_call_blocks"] == 2 and res["tool_result_blocks"] == 2
    assert res["train_spans"] == 4 and res["unique_ids"] and res["tool_call_tokens_untrained"] == 0
    assert 0 < res["trained_share"] < 1 and res["shifted_supervised_targets"] == res["trained_tokens"]


def _break_first_row(out: Path, edit) -> None:
    lines = out.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[0])
    edit(row)
    lines[0] = json.dumps(row, ensure_ascii=False)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_check_catches_a_trained_tool_result_token(toy_tokenizer, tmp_path):
    out, _ = _write_rows(toy_tokenizer, "sft-agentic-nemotron-agentic-v1", [AGENT], tmp_path)
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(toy_tokenizer)

    def edit(row):
        enc = tok.encode(row["text"], add_special_tokens=False)
        a = row["text"].index(T["tool_result"])
        i = next(k for k, (s, e) in enumerate(enc.offsets) if s >= a + len(T["tool_result"]) + 1 and e > s)
        row["loss_mask"][i] = 1

    _break_first_row(out, edit)
    res = records.check_files([out], toy_tokenizer)
    assert not res["checks_ok"]
    assert {"tool_result_token_trained", "trained_token_outside_span"} <= set(res["checks_failed"])


def test_check_catches_a_trained_eos_a_duplicate_id_and_changed_ids(toy_tokenizer, tmp_path):
    out, _ = _write_rows(toy_tokenizer, "sft-code-commitpackft", [COMMIT, COMMIT], tmp_path)
    lines = out.read_text(encoding="utf-8").splitlines()
    first, second = json.loads(lines[0]), json.loads(lines[1])
    first["loss_mask"][-1] = 1
    second["id"] = first["id"]
    second["input_ids"][5] = (second["input_ids"][5] + 1) % 50
    out.write_text("\n".join(json.dumps(r) for r in (first, second)) + "\n", encoding="utf-8")
    res = records.check_files([out], toy_tokenizer)
    assert {"eos_missing_or_trained", "duplicate_id", "input_ids_differ_from_fresh_encode", "decode_differs_from_text"} <= set(res["checks_failed"])


def test_check_catches_a_changed_effort_line(toy_tokenizer, tmp_path):
    out, _ = _write_rows(toy_tokenizer, "sft-code-commitpackft", [COMMIT], tmp_path)
    _break_first_row(out, lambda row: row.update(effort="64k"))
    assert "parse_effort_differs" in records.check_files([out], toy_tokenizer)["checks_failed"]


def test_normaliser_only_decode_difference_is_not_a_failure(toy_tokenizer, tmp_path):
    row = dict(COMMIT, response="café au lait")  # e + combining acute: NFC turns it into one character
    out, _ = _write_rows(toy_tokenizer, "sft-code-commitpackft", [row], tmp_path)
    res = records.check_files([out], toy_tokenizer)
    assert res["checks_ok"] and res["info"] == {"decode_equals_normalised_text_only": 1}


# --- work list -----------------------------------------------------------------------------------

def test_generator_flags():
    flags = worklist.generator_flags
    assert flags("sft-dolly-15k", "none (human-written; no model generator)") == []
    assert flags("sft-code-opencodereasoning", "DeepSeek-R1 (MIT, open weights)") == []
    assert flags("sft-x", "GPT-OSS-120B (Apache-2.0), Qwen3-32B (Apache-2.0)") == []
    assert "closed_model" in flags("sft-x", "GPT-4o (OpenAI, proprietary closed)")
    assert "use_restricted_or_llama" in flags("sft-x", "Llama-3.3-70B-Instruct (Llama 3.3 Community Licence)")
    assert "modified_mit_generator" in flags("sft-x", "Kimi-K2-Instruct (Modified MIT)")
    assert "unknown_generator" in flags("sft-x", "unknown generator")
    got = flags("sft-chat-nemotron-if-v1", "chat split open; structured-outputs split has unknown generator (exclude structured-outputs split)")
    assert "adapter_reads_unknown_generator_split:structured_outputs" in got


def test_worklist_rules_hold_on_the_branch_documents():
    w = worklist.build(None)
    by = {r["set"]: r for r in w["sets"]}
    assert by["sft-code-opencodereasoning-2"]["track"] == "owned"
    for r in w["sets"]:
        if r["decision_class"] == "excluded" or not r["adapter"] or not r["in_proposal_text"]:
            assert r["track"] in ("out", "owned"), r["set"]
        if r["track"] in ("allowed", "reserved"):
            assert not r["flags"] and r["adapter"] and r["in_proposal_text"] and r["decision_class"] != "excluded"
        if r["track"] == "allowed":
            assert r["decision"].startswith("allowed")
        if r["track"] == "reserved":
            assert r["decision"].startswith("TSAI reserves")
    assert by["sft-chat-nemotron-if-v1"]["track"] == "hold"
    assert set(w["lists"]["allowed"]).isdisjoint(w["lists"]["reserved"])
    assert w["counts"]["stage1_sets"] == len(w["sets"])


def test_convert_reads_the_pinned_revision(monkeypatch):
    seen = []

    class Boom(Exception):
        pass

    def fake_urlopen(url, timeout=0):
        seen.append(url if isinstance(url, str) else url.full_url)
        raise Boom

    monkeypatch.setattr(convert.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(convert, "REVISIONS", {"org/repo": "a" * 40})
    with pytest.raises(Boom):
        list(convert._one_file_rows("org/repo", "data/x.jsonl", 0, 1))
    with pytest.raises(Boom):
        list(convert._one_file_rows("other/repo", "data/x.jsonl", 0, 1))
    assert seen[0] == f"https://huggingface.co/datasets/org/repo/resolve/{'a' * 40}/data/x.jsonl"
    assert seen[1].endswith("/other/repo/resolve/main/data/x.jsonl")


def test_hub_byte_guard_stops_a_run(monkeypatch):
    monkeypatch.setenv("G10_MAX_HUB_BYTES", "100")
    monkeypatch.setattr(convert, "BYTES_READ", 101)
    with pytest.raises(SystemExit):
        convert._guard_bytes()
    monkeypatch.setattr(convert, "BYTES_READ", 99)
    convert._guard_bytes()


# --- ledger integration --------------------------------------------------------------------------

def _c3_rec(**kw):
    rec = {"set_id": "sft-dolly-15k", "scope": "first 1,000 rows, C3", "rows_in": 1000, "rows": 1000, "sequence_tokens": 193844,
           "shifted_supervised_targets": 84057, "tokenizer_sha256": "a" * 64, "content_sha256": "b" * 64,
           "length": {"p50": 129, "p95": 536, "max": 2549}, "rows_over_max_len": 0, "checks_ok": True}
    rec.update(kw)
    return rec


def test_ledger_takes_c3_records_with_their_own_scope(tmp_path):
    mi = _load("g10_mix_inventory_t", "mix_inventory.py")
    path = tmp_path / "c3.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in (
        _c3_rec(), _c3_rec(scope="full set, converted, not decontaminated", rows=15011),
        _c3_rec(set_id="sft-not-in-the-table"))) + "\n", encoding="utf-8")
    records = mi.collect(HERE.parent, None, None, path)
    c3 = [r for r in records if r["type"] == "c3_token_record"]
    assert [r["scope"] for r in c3] == ["first 1,000 rows, C3", "full set, converted, not decontaminated"]
    assert c3[0]["licence_decision"] == "allowed"
    meta = records[0]
    assert meta["counts"]["sets_with_c3_records"] == 1 and meta["counts"]["c3_records"] == 2
    assert any(r["type"] == "contradiction" and r["kind"] == "c3_record_set_not_in_licence_table" for r in records)
    md = mi.render_markdown(records)
    assert "## 8. C3 token records (WP14), by scope" in md and "not the current C3 pack state" in md
    assert mi.dump_jsonl(records) == mi.dump_jsonl(mi.collect(HERE.parent, None, None, path))  # deterministic
    # measured-token supply is untouched: a C3 record is not a kept-row record
    assert meta["counts"]["sets_with_measured_tokens"] == 1


def test_ledger_without_c3_records_has_no_section_8():
    mi = _load("g10_mix_inventory_t2", "mix_inventory.py")
    md = mi.render_markdown(mi.collect(HERE.parent, None, None))
    assert "## 8." not in md and "sets_with_c3_records" not in json.dumps(mi.collect(HERE.parent, None, None)[0])


def test_c3_record_needs_its_scope_and_hash(tmp_path):
    mi = _load("g10_mix_inventory_t3", "mix_inventory.py")
    bad = tmp_path / "bad.jsonl"
    rec = _c3_rec()
    del rec["scope"]
    bad.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        mi.read_c3_records(bad)


# --- guards of the full-conversion command -------------------------------------------------------

def test_only_the_c3_tokenizer_is_accepted(tmp_path):
    other = tmp_path / "other.json"
    other.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        records.require_c3(str(other))
    records.require_c3(str(other), allow_other=True)


def test_global_budget_refuses_a_start_that_would_pass_it(tmp_path):
    import argparse

    (tmp_path / "earlier-set").mkdir()
    (tmp_path / "earlier-set" / "part0000.jsonl.gz").write_bytes(b"x" * 2_000_000)  # 2 MB already written by another set
    a = argparse.Namespace(set="sft-dolly-15k", tokenizer="unused", allow_other_tokenizer=True, threads=1, out_dir=str(tmp_path),
                           budget_gb=0.0005, global_budget_gb=0.002)  # 0.5 MB more would pass 2 MB (0.002 GiB = 2.1 MB)
    with pytest.raises(SystemExit) as err:
        records.cmd_full(a)
    assert "global budget" in str(err.value)


def test_verify_local_checks_the_pinned_sha256(tmp_path, capsys):
    import argparse
    import hashlib

    repo, name = "databricks/databricks-dolly-15k", "databricks-dolly-15k.jsonl"
    root = tmp_path / "hub"
    (root / repo).mkdir(parents=True)
    data = b'{"a": 1}\n'
    (root / repo / name).write_bytes(data)
    pins = {"datasets": {repo: {"sha": "a" * 40, "files": {name: {"size": len(data), "lfs_sha256": hashlib.sha256(data).hexdigest()}}}}}
    pin_file = tmp_path / "pins.json"
    pin_file.write_text(json.dumps(pins), encoding="utf-8")
    a = argparse.Namespace(set="sft-dolly-15k", root=str(root), revisions_json=str(pin_file))
    assert records.cmd_verify_local(a) == 0
    (root / repo / name).write_bytes(b'{"a": 2}\n')  # same size, different bytes
    assert records.cmd_verify_local(a) == 1
    assert "DIFFER" in capsys.readouterr().out
