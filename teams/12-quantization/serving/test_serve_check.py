"""Tests for serve_check.py's checks and request building. CPU only, no server.

    python -m pytest teams/12-quantization/serving/test_serve_check.py -q
"""
from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import serve_check as sc  # noqa: E402

TOOLS = json.loads((HERE / "tools_v1.json").read_text(encoding="utf-8"))
ROWS = {r["id"]: r for r in map(json.loads, (HERE / "prompts_v1.jsonl").read_text(encoding="utf-8").splitlines())}


def _resp(reasoning=None, content=None, calls=()):
    return {"status": 200, "reasoning": reasoning, "content": content,
            "tool_calls": [{"name": n, "arguments": a, "id": "c"} for n, a in calls]}


def test_prompt_set():
    cats = [r["category"] for r in ROWS.values()]
    assert len(ROWS) == 100
    assert {c: cats.count(c) for c in set(cats)} == {"chat": 25, "reason": 25, "tool": 30, "tool_result": 10,
                                                     "no_tool": 10}
    for r in ROWS.values():
        assert all(t in TOOLS for t in r["tools"] or [])
        if r["category"] == "tool":
            assert r["expect"]["tool"] in r["tools"]


def test_reasoning_left_in_content_fails_the_field_check():
    row = ROWS["reason-01"]
    good = sc.check_row(row, _resp("17*23", "391"), TOOLS)
    assert good["fields_ok"] and good["behaviour_ok"] and good["answer_ok"]
    bad = sc.check_row(row, _resp(None, "<|think|>\n17*23\n<|/think|>\n391"), TOOLS)
    assert not bad["fields_ok"] and bad["marker_leaks"] == ["<|/think|>", "<|think|>"]
    assert not bad["behaviour_ok"]


def test_unparsed_tool_call_fails_the_field_check():
    row = ROWS["tool-01"]
    good = sc.check_row(row, _resp(None, None, [("get_weather", '{"city": "Bengaluru"}')]), TOOLS)
    assert good["fields_ok"] and good["behaviour_ok"]
    raw = '<|tool_call|>\n{"arguments": {"city": "Bengaluru"}, "name": "get_weather"}\n<|/tool_call|>'
    bad = sc.check_row(row, _resp(None, raw), TOOLS)
    assert not bad["fields_ok"] and not bad["behaviour_ok"]


def test_tool_arguments_checked_against_schema():
    row = ROWS["tool-23"]                                    # convert_currency: amount, from_currency, to_currency
    missing = sc.check_row(row, _resp(None, None, [("convert_currency", '{"amount": 250}')]), TOOLS)
    assert missing["tool_args_ok"] is False and not missing["behaviour_ok"]
    not_json = sc.check_row(row, _resp(None, None, [("convert_currency", "amount=250")]), TOOLS)
    assert not_json["tool_args_ok"] is False


def test_native_markers_are_reported_not_failed():
    r = sc.check_row(ROWS["chat-01"], _resp(None, "<think>hmm</think> answer"), TOOLS)
    assert r["fields_ok"] and r["native_markers"] == ["</think>", "<think>"]


def test_indic_digits_count_as_answers():
    assert sc.has_number("উত্তর ৫৬", "56")
    assert sc.has_number("ಉತ್ತರ ೧೬೮ ಗಂಟೆಗಳು", "168")
    assert sc.has_number("Total: 1,000 rupees", "1000")
    assert not sc.has_number("about 5600", "56")


def test_body_puts_tools_in_system_message_and_effort_in_template_kwargs():
    args = Namespace(format_hint="on", tools_in_system_on=True, max_tokens=64, temperature=0.0, seed=0)
    body = sc.build_body(ROWS["tool-01"], TOOLS, args, "m")
    assert body["messages"][0]["role"] == "system" and "get_weather" in body["messages"][0]["content"]
    assert body["tools"][0]["function"]["name"] == "get_weather" and body["tool_choice"] == "auto"
    assert body["skip_special_tokens"] is False
    body = sc.build_body(ROWS["reason-02"], TOOLS, args, "m", stream=True)
    assert body["chat_template_kwargs"] == {"effort": "4k"} and body["stream"]
    args.format_hint, args.tools_in_system_on = "off", False
    body = sc.build_body(ROWS["chat-01"], TOOLS, args, "m")
    assert body["messages"] == ROWS["chat-01"]["messages"]


def test_stream_comparison_ignores_argument_spacing():
    a = _resp("r", "c", [("f", '{"x": 1}')])
    b = _resp("r", "c", [("f", '{"x":1}')])
    assert sc.same_fields(a, b)
    assert not sc.same_fields(a, _resp("r", "c2", [("f", '{"x": 1}')]))
