"""Tests for check_gates.py: each gate on a small synthetic record, and the dry run 2 record (#869) end to end."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_gates as G

TEAM = HERE.parents[1]
DRYRUN2 = TEAM / "results/dryrun2-1234"
CFG = yaml.safe_load((HERE / "gates_v1.yaml").read_text(encoding="utf-8"))


def train_rows(n, tokens_per_step, loss=3.0, step_ms=1000.0, positions=None):
    return [{"step": s, "loss": loss, "gradient_norm": 1.0, "train/scored_tokens": tokens_per_step,
             "train/input_positions": positions or tokens_per_step, "perf/step_ms": step_ms} for s in range(1, n + 1)]


class Health(unittest.TestCase):
    def test_finite_passes(self):
        self.assertEqual(G.gate_health(train_rows(5, 10), CFG["run_health"])[0], G.PASS)

    def test_nan_fails(self):
        rows = train_rows(5, 10)
        rows[2]["loss"] = float("nan")
        state, msg = G.gate_health(rows, CFG["run_health"])
        self.assertEqual(state, G.FAIL)
        self.assertIn("step 3", msg)


class LossVsFit(unittest.TestCase):
    fit = {"E": 1.0, "A": 0.0, "alpha": 0.3, "B": 0.0, "beta": 0.3, "n_active": 1e9, "holdout_error": 0.02}

    def rows_with_evals(self, bpbs):
        rows = train_rows(100, 10_000_000)                     # 1e7 tokens per step: 1e9 at step 100
        for step, v in zip((85, 95, 100, 110, 120), bpbs):
            rows.append({"step": step, "val/bpb": v})
        return rows

    def test_no_fit_is_pending(self):
        self.assertEqual(G.gate_loss_vs_fit(self.rows_with_evals([1.0] * 3), CFG["loss_vs_fit"], None)[0], G.PENDING)

    def test_too_few_tokens_is_pending(self):
        rows = train_rows(10, 1000) + [{"step": 10, "val/bpb": 1.0}]
        self.assertEqual(G.gate_loss_vs_fit(rows, CFG["loss_vs_fit"], self.fit)[0], G.PENDING)

    def test_on_prediction_passes(self):
        state, _ = G.gate_loss_vs_fit(self.rows_with_evals([1.01, 0.99, 1.0]), CFG["loss_vs_fit"], self.fit)
        self.assertEqual(state, G.PASS)

    def test_far_above_prediction_fails(self):
        state, msg = G.gate_loss_vs_fit(self.rows_with_evals([1.30, 1.31, 1.29]), CFG["loss_vs_fit"], self.fit)
        self.assertEqual(state, G.FAIL, msg)

    def test_prediction_formula(self):
        f = {"E": 1.5, "A": 400.0, "alpha": 0.34, "B": 410.0, "beta": 0.28}
        self.assertAlmostEqual(G.predict(f, 1e9, 1e9), 1.5 + 400 / 1e9 ** 0.34 + 410 / 1e9 ** 0.28)


class Resume(unittest.TestCase):
    def write(self, obj):
        p = Path(tempfile.mkdtemp()) / "result.json"
        p.write_text(json.dumps(obj))
        return p

    def test_missing_is_pending(self):
        self.assertEqual(G.gate_resume(None, CFG["resume"])[0], G.PENDING)

    def test_restart_result_pass(self):
        p = self.write({"schema": "g7-job-result/1", "run_id": "x", "status": "pass", "numbers": {"optim": "muon"}})
        self.assertEqual(G.gate_resume(p, CFG["resume"])[0], G.PASS)

    def test_detail_fail(self):
        p = self.write({"pass": False, "first_diff": {"step": 101}, "optim": "muon"})
        self.assertEqual(G.gate_resume(p, CFG["resume"])[0], G.FAIL)

    def test_wrong_optimizer_fails(self):
        p = self.write({"pass": True, "first_diff": None, "optim": "adamw"})
        self.assertEqual(G.gate_resume(p, CFG["resume"])[0], G.FAIL)


class Router(unittest.TestCase):
    def test_even_passes(self):
        rows = [{"step": s, "expert_load": [[10] * 16, [10] * 16]} for s in (50, 300)]
        self.assertEqual(G.gate_router(rows, CFG["router_evenness"])[0], G.PASS)

    def test_five_times_even_fails(self):
        hot = [50] + [10] * 15                             # 50 / 200 = 25% is 4x; 80 / 230 is 5.57x
        rows = [{"step": 50, "expert_load": [hot]}, {"step": 100, "expert_load": [[80] + [10] * 15]}]
        state, msg = G.gate_router(rows, CFG["router_evenness"])
        self.assertEqual(state, G.FAIL)
        self.assertIn("step 100", msg)

    def test_idle_expert_after_warmup_fails(self):
        rows = [{"step": 150, "expert_load": [[0] + [10] * 15]}, {"step": 250, "expert_load": [[0] + [10] * 15]}]
        state, msg = G.gate_router(rows, CFG["router_evenness"])
        self.assertEqual(state, G.FAIL)
        self.assertIn("step 250", msg)


class Eval(unittest.TestCase):
    def write(self, values, items=None, step=0):
        recs = [{"model": "lab:run", "task": t, "primary": True, "value": v, "checkpoint": {"step": step},
                 "n_items": (items or {}).get(t, CFG["eval_pass"]["tasks"][t]["items"])} for t, v in values.items()]
        p = Path(tempfile.mkdtemp()) / "eval.json"
        p.write_text(json.dumps({"records": recs}))
        return p

    def chance(self):
        return {"mmlu": 25.0, "milu_Hindi": 26.0, "milu_Telugu": 25.0, "milu_Tamil": 34.0, "milu_Bengali": 22.0}

    def test_chance_passes(self):                           # milu_Tamil 34.0 passes only through its one-letter range
        self.assertEqual(G.gate_eval(self.write(self.chance()), "lab:run", CFG["eval_pass"])[0], G.PASS)

    def test_above_band_fails(self):
        v = self.chance() | {"mmlu": 40.0}
        self.assertEqual(G.gate_eval(self.write(v), "lab:run", CFG["eval_pass"])[0], G.FAIL)

    def test_short_item_count_fails(self):
        p = self.write(self.chance(), items={"milu_Hindi": 90})
        self.assertEqual(G.gate_eval(p, "lab:run", CFG["eval_pass"])[0], G.FAIL)

    def test_no_step0_is_pending(self):
        self.assertEqual(G.gate_eval(self.write(self.chance(), step=500), "lab:run", CFG["eval_pass"])[0], G.PENDING)


class Throughput(unittest.TestCase):
    def test_no_budget_is_pending(self):
        self.assertEqual(G.gate_throughput(train_rows(10, 1000), CFG["throughput"], None, None)[0], G.PENDING)

    def test_floor(self):
        rows = train_rows(10, 1000, step_ms=1000.0)          # 1,000 tokens/s
        cfg = CFG["throughput"]
        # 1,000 tokens/s for 0.9 x 10 h = 32.4M tokens
        self.assertEqual(G.gate_throughput(rows, cfg, 32.4e6, 10)[0], G.PASS)
        self.assertEqual(G.gate_throughput(rows, cfg, 33e6, 10)[0], G.FAIL)

    def test_counts_real_tokens_not_positions(self):
        tps, fill = G.measured_tps(train_rows(4, 500, step_ms=1000.0, positions=1000))
        self.assertEqual((tps, fill), (500.0, 0.5))


class Team9Holds(unittest.TestCase):
    def write(self, obj):
        p = Path(tempfile.mkdtemp()) / "holds.json"
        p.write_text(json.dumps(obj))
        return p

    def test_missing_is_pending(self):
        self.assertEqual(G.gate_team9(None, CFG["team9_holds"])[0], G.PENDING)

    def test_one_verdict_missing_is_pending(self):
        self.assertEqual(G.gate_team9(self.write({"early_quality": "go"}), CFG["team9_holds"])[0], G.PENDING)

    def test_both_go_passes(self):
        p = self.write({"early_quality": "go", "watcher": "go", "evidence": "#931"})
        self.assertEqual(G.gate_team9(p, CFG["team9_holds"])[0], G.PASS)

    def test_a_hold_fails(self):
        p = self.write({"early_quality": "go", "watcher": "hold"})
        state, msg = G.gate_team9(p, CFG["team9_holds"])
        self.assertEqual(state, G.FAIL)
        self.assertIn("watcher", msg)


class Sheet(unittest.TestCase):
    def test_every_gate_is_a_proposal(self):
        for name, g in CFG.items():
            self.assertTrue(g["status"].startswith("proposal"), name)

    def test_budgets_stay_empty(self):
        self.assertIsNone(CFG["throughput"]["token_budget"])
        self.assertIsNone(CFG["throughput"]["wall_hours"])


@unittest.skipUnless((DRYRUN2 / "metrics.jsonl").exists(), "dry run 2 record (#869) not present")
class DryRun2(unittest.TestCase):
    """The checker agrees with the dry run 2 report on #892: 8x the even share at step 50, over the 5x line to step 300."""

    def setUp(self):
        self.rows = G.read_metrics(DRYRUN2)

    def test_health_passes(self):
        self.assertEqual(G.gate_health(self.rows, CFG["run_health"])[0], G.PASS)

    def test_router_fails_as_reported(self):
        state, msg = G.gate_router(self.rows, CFG["router_evenness"])
        self.assertEqual(state, G.FAIL)
        self.assertIn("8.00x the even share (step 50", msg)
        self.assertIn("steps 50 to 300", msg)

    def test_real_tokens_per_second(self):
        tps, fill = G.measured_tps(self.rows)
        self.assertEqual(round(tps), 2299)
        self.assertAlmostEqual(fill, 0.418, places=3)

    def test_overall_is_no_go(self):
        code = G.main(["--run", str(DRYRUN2)])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
