"""pytest setup for the correctness tests.

  * Puts teams/06-performance on sys.path, so `pytest teams/06-performance/correctness` works from the
    repo root (the Gate 1 command) as well as from teams/06-performance.
  * `device` fixture: cuda if available, else cpu.
  * A test that hits a stub (NotImplementedError) is reported as SKIPPED with the stub's name, not failed.
    `pytest -rs` lists them. At Gate 1 no skip may be left.
  * At the end of the run: a table of every pair's worst output and gradient error and its tolerances.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

fixture = pytest.fixture
hookimpl = pytest.hookimpl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@fixture
def device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


@hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if call.excinfo is not None and call.excinfo.errisinstance(NotImplementedError):
        rep.outcome = "skipped"
        rep.longrepr = (str(item.path), item.location[1] or 0, f"stub: {call.excinfo.value}")


def pytest_terminal_summary(terminalreporter):
    """Each pair's worst error against its tolerance (the Instructor asked for every test's error)."""
    from correctness.framework import RESULTS
    if not RESULTS:
        return
    tr = terminalreporter
    tr.section("correctness errors (worst per pair, fast vs fp64 reference)")
    tr.write_line(f"{'pair':34s} {'dtype':8s} {'out':>9s} {'tol':>7s} {'grad':>9s} {'grad_tol':>8s} {'tensors':>7s}")
    for name in sorted(RESULTS):
        r = RESULTS[name]
        grad = "-" if r["grad"] is None else f"{r['grad']:.2e}"
        tr.write_line(f"{name:34s} {r['dtype']:8s} {r['out']:9.2e} {r['tol']:7.0e} {grad:>9s} "
                      f"{r['grad_tol']:8.0e} {r['n']:7d}")
