"""Tests of test_llamacpp_lm.py's optional settings (EVAL_GUARD_CHECK4, EVAL_GUARD_CACHE_TOL), with no GGUF.

    python -m pytest test_guard_options.py -q

A scripted stand-in replaces LlamaCppLM, so each check can be made to pass or miss by a chosen amount. What is tested:
the defaults are unchanged (check 4 fatal, check 3 at 0.05); EVAL_GUARD_CHECK4=warn turns a check 4 miss into a printed
warning; EVAL_GUARD_CACHE_TOL moves check 3 only, and checks 1 and 2 stay at 0.05.
"""
import importlib.util, sys, types
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
RIGHT, WRONG = " Carbon dioxide", " Oxygen"


def fake_module(scores_cached, scores_fresh, lp=-0.50, lp_gen=-0.50):
    """A llamacpp_lm stand-in. scores_cached / scores_fresh: log-probs of the four answers, cached and one by one."""
    class LLM:
        scores = np.array([[-9.0, -9.0, -9.0, -9.0, -0.2, -9.0, -9.0, -9.0]] * 6)   # off-by-one value far from lp

        def detokenize(self, tokens):
            return b" Paris"

        def create_completion(self, **kw):
            return {"choices": [{"logprobs": {"top_logprobs": [{" Paris": lp_gen, " the": -2.0}]}}]}

        def reset(self):
            pass

    class LM:
        def __init__(self, gguf, n_ctx):
            self.llm, self.single = LLM(), iter(scores_fresh)

        def _encode_pair(self, context, continuation):
            return [1, 2, 3], [4]

        def loglikelihood(self, reqs, disable_tqdm=True):
            if len(reqs) == 4:
                return [(s, True) for s in scores_cached]
            if reqs[0].args[0].startswith("Question"):
                return [(next(self.single), True)]
            return [(lp, True)]

    mod = types.ModuleType("llamacpp_lm")
    mod.LlamaCppLM = LM
    return mod


def load(monkeypatch, env, **scripts):
    for k in ("EVAL_GUARD_CHECK4", "EVAL_GUARD_CACHE_TOL", "EVAL_GUARD_CONTEXT", "EVAL_GUARD_ANSWER"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setitem(sys.modules, "llamacpp_lm", fake_module(**scripts))
    spec = importlib.util.spec_from_file_location("guard_under_test", HERE / "test_llamacpp_lm.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GOOD = dict(scores_cached=[-1.0, -2.0, -3.0, -4.0], scores_fresh=[-1.0, -2.0, -3.0, -4.0])
WRONG_FIRST = dict(scores_cached=[-1.60, -1.53, -3.0, -4.0], scores_fresh=[-1.60, -1.53, -3.0, -4.0])
CACHE_OFF = dict(scores_cached=[-1.0, -2.0, -3.0, -4.0], scores_fresh=[-1.0784, -2.0, -3.0, -4.0])   # check 3: 0.0784


def test_defaults_are_unchanged(monkeypatch):
    g = load(monkeypatch, {}, **GOOD)
    assert (g.CHECK4, g.CACHE_TOL, g.TOL) == ("fail", 0.05, 0.05)
    assert g.check("x.gguf") == []


def test_check4_miss_is_fatal_by_default(monkeypatch):
    fails = load(monkeypatch, {}, **WRONG_FIRST).check("x.gguf")
    assert len(fails) == 1 and fails[0].startswith("4.")


def test_check4_warn_does_not_stop_and_prints(monkeypatch, capsys):
    fails = load(monkeypatch, {"EVAL_GUARD_CHECK4": "warn"}, **WRONG_FIRST).check("x.gguf")
    out = capsys.readouterr().out
    assert fails == []
    assert "WARN 4. easy item answered wrong" in out and "check 4 warn only (EVAL_GUARD_CHECK4)" in out


def test_invalid_check4_value_stops(monkeypatch):
    with pytest.raises(SystemExit):
        load(monkeypatch, {"EVAL_GUARD_CHECK4": "ignore"}, **GOOD)


def test_check3_default_limit_and_override(monkeypatch, capsys):
    fails = load(monkeypatch, {}, **CACHE_OFF).check("x.gguf")
    assert len(fails) == 1 and fails[0].startswith("3.")
    fails = load(monkeypatch, {"EVAL_GUARD_CACHE_TOL": "0.10"}, **CACHE_OFF).check("x.gguf")
    assert fails == [] and "check 3 limit 0.1 (EVAL_GUARD_CACHE_TOL)" in capsys.readouterr().out


def test_cache_tol_does_not_loosen_check_1(monkeypatch):
    # the score differs from the model's own generation by 0.07: check 1 (limit 0.05) must still fail
    fails = load(monkeypatch, {"EVAL_GUARD_CACHE_TOL": "0.10"}, lp=-0.57, lp_gen=-0.50, **GOOD).check("x.gguf")
    assert len(fails) == 1 and fails[0].startswith("1.")
