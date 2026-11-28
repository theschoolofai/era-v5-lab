"""run_report.py: the run report reads metrics.jsonl and gets the numbers right."""

from pathlib import Path
import json
import sys
from tempfile import TemporaryDirectory
import unittest

TEAM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM / "harness"))
import run_report as rr

DRYRUN1 = TEAM / "jobs/evidence/2026-11-15-dryrun1-full/metrics.jsonl"


def row(step, loss=5.0, norm=1.0, lr=1e-3, scored=100, positions=200, ms=1000.0, **extra):
    return {"step": step, "loss": loss, "gradient_norm": norm, "lr": lr, "train/scored_tokens": scored,
            "train/input_positions": positions, "perf/step_ms": ms, **extra}


class DryRun1Tests(unittest.TestCase):
    """The committed dry run 1 record: the report must reproduce its known numbers."""

    @classmethod
    def setUpClass(cls):
        cls.text = rr.report(rr.read_rows(DRYRUN1), "dryrun1")

    def test_health_and_steps(self):
        self.assertIn("1221 training rows, last step 1221", self.text)
        self.assertIn("Non-finite loss or gradient norm: none", self.text)

    def test_fill_matches_the_log(self):
        # 7,206,344 scored tokens in 20,004,864 input positions (36.0%), as #825 quotes.
        self.assertIn("7,206,344 scored tokens in 20,004,864 input positions (36.0%)", self.text)

    def test_heldout_bpb_at_each_eval(self):
        for step, bpb in [(0, "2.5052"), (611, "1.6217"), (1221, "1.5159")]:
            self.assertIn(f"| {step} | {bpb} |", self.text)

    def test_no_expert_load_recorded(self):
        self.assertIn("None recorded", self.text)


class ExpertLoadTests(unittest.TestCase):
    def test_layer_statistics(self):
        counts = [100] * 16
        counts[3] = 1000
        st = rr.layer_load(counts)
        self.assertAlmostEqual(st["busiest"], 1000 / 2500)
        self.assertAlmostEqual(st["max_over_mean"], 1000 / (2500 / 16))
        self.assertEqual((st["dead"], st["experts"]), (0, 16))
        self.assertEqual(rr.layer_load([5, 0, 5, 5])["dead"], 1)
        self.assertIsNone(rr.layer_load([0, 0]))

    def test_uniform_layer_has_fair_share(self):
        st = rr.layer_load([10] * 16)
        self.assertAlmostEqual(st["busiest"], 1 / 16)
        self.assertAlmostEqual(st["cv"], 0.0)

    def test_report_tracks_the_worst_layer(self):
        skew = [100] * 16
        skew[3] = 1000
        even = [100] * 16
        text = rr.report([row(1), row(50, expert_load=[even, skew]), row(100, expert_load=[even, even])], "x")
        self.assertIn("| 50 | 40.0% | 0 |", text)
        self.assertIn("| 100 | 6.2% | 0 |", text)
        self.assertIn("fair share 6.25% with 16 experts", text)


class ChartTests(unittest.TestCase):
    """--charts (#892, design task 4): the busiest-share table, the zero-choice runs and the three files."""

    def rows(self):
        even = [100] * 16
        skew = [100] * 16
        skew[2] = 1500                      # 1500 / 3000 = 50%: above the 31.25% line
        idle = [100] * 16
        idle[13] = 0                        # expert 13 gets nothing
        return [row(1), row(25, expert_load=[skew, even]), row(50, expert_load=[idle, even]),
                row(75, expert_load=[idle, idle]), row(100, expert_load=[even, idle])]

    def test_busiest_table(self):
        table = rr.busiest_table(self.rows())
        self.assertEqual([s for s, _, _ in table], [25, 50, 75, 100])
        self.assertAlmostEqual(table[0][1][0], 0.5)
        self.assertAlmostEqual(table[0][1][1], 1 / 16)
        self.assertEqual(table[1][2], [(0, 13)])

    def test_zero_choice_runs_count_logged_steps_in_a_row(self):
        streaks = rr.idle_streaks(rr.busiest_table(self.rows()))
        # Layer 0 expert 13: steps 50 and 75 (two in a row); layer 1 expert 13: steps 75 and 100.
        self.assertIn((0, 13, 50, 75, 2), streaks)
        self.assertIn((1, 13, 75, 100, 2), streaks)
        self.assertEqual(len(streaks), 2)

    def test_a_break_starts_a_new_run(self):
        idle = [100] * 4
        idle[1] = 0
        even = [100] * 4
        rows = [row(10, expert_load=[idle]), row(20, expert_load=[even]), row(30, expert_load=[idle])]
        self.assertEqual(sorted(rr.idle_streaks(rr.busiest_table(rows))), [(0, 1, 10, 10, 1), (0, 1, 30, 30, 1)])

    def test_charts_write_three_files(self):
        with TemporaryDirectory() as d:
            paths = rr.charts(self.rows(), Path(d) / "charts")
            self.assertEqual(sorted(p.name for p in paths),
                             ["busiest_share.svg", "busiest_share_heatmap.svg", "expert_load.md"])
            md = (Path(d) / "charts" / "expert_load.md").read_text(encoding="utf-8")
            self.assertIn("failure line (5 times even) 31.25%", md)
            self.assertIn("Logged steps at or above the failure line: 1 of 4 (first 25, last 25).", md)
            self.assertIn("| 0 | 13 | 50 | 75 | 2 |", md)
            for p in paths[:2]:
                self.assertTrue(p.read_text(encoding="utf-8").startswith("<svg"))

    def test_charts_need_expert_load(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                rr.charts([row(1)], d)


class RateAndIdleTests(unittest.TestCase):
    """Lab 5 compute rules: peak memory and time outside training steps (idle time) in the report."""

    def test_peak_memory_and_idle_time(self):
        rows = [row(1, ms=1000.0, gpu_peak_gb=5.5), row(2, ms=1000.0, gpu_peak_gb=6.25)]
        text = rr.report(rows, "x", summary={"wall_seconds": 10.0})
        self.assertIn("Peak GPU memory: 6.25 GiB.", text)
        self.assertIn("Wall time 0.2 min, of which 0.1 min (80%) outside training steps", text)

    def test_without_summary_no_idle_line(self):
        self.assertNotIn("outside training steps", rr.report([row(1)], "x"))


class InputTests(unittest.TestCase):
    def test_non_finite_rows_are_reported(self):
        text = rr.report([row(1), row(2, loss=float("nan")), row(3, norm=float("inf"))], "x")
        self.assertIn("2 rows, first at step 2", text)

    def test_real_token_throughput_ignores_padding(self):
        text = rr.report([row(1, scored=500, positions=2000, ms=1000.0)], "x")
        self.assertIn("Real (scored) tokens per second: 500", text)
        self.assertIn("(25.0%)", text)

    def test_bad_json_line_stops(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "metrics.jsonl"
            p.write_text(json.dumps(row(1)) + "\nnot json\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                rr.read_rows(p)


if __name__ == "__main__":
    unittest.main()
