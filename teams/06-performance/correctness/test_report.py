"""perfkit/report.py: compare() refuses a baseline pair that does not time the same committed code."""
from __future__ import annotations

import copy

from perfkit import report
from perfkit.schema import example_run


def _pair(**b_meta):
    a = example_run()
    b = copy.deepcopy(a)
    b["meta"].update(tag="b", **b_meta)
    return a, b


def test_same_clean_commit_passes():
    _, ok, problems = report.compare(*_pair())
    assert ok and problems == []


def test_different_commit_is_refused():
    _, ok, problems = report.compare(*_pair(commit="1" * 40))
    assert not ok and any("different commit" in p for p in problems)


def test_dirty_or_unknown_tree_is_refused():
    for dirty in (True, None):
        _, ok, problems = report.compare(*_pair(dirty=dirty))
        assert not ok and any(f"dirty={dirty}" in p for p in problems)
