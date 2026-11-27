"""D3 uses G7 public claim/candidate/fencing contracts without pointer extensions."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import torch

TEAM = Path(__file__).resolve().parents[1]
G7 = TEAM.parent / "07-infrastructure"
sys.path[:0] = [str(TEAM / "harness"), str(G7), str(G7 / "support" / "simulation")]
from ckpt.ckpt import Checkpointer, CheckpointError, FencedError
from trainer.tiny import TinyLM, SyntheticLoader, make_probe_fn
from week2.precommit import claim_for_start


def state():
    torch.manual_seed(1234)
    model = TinyLM(1234)
    return model, torch.optim.AdamW(model.parameters(), lr=1e-3), SyntheticLoader(1234, 8, 0, 1), make_probe_fn(1234)


class PrecommitTests(unittest.TestCase):
    def test_public_call_order_and_no_private_writes(self):
        calls = []
        attempt = SimpleNamespace(
            claim=Mock(side_effect=lambda: calls.append("claim") or 2),
            candidates=Mock(side_effect=lambda: calls.append("candidates") or []),
        )
        self.assertEqual(claim_for_start(attempt), 2)
        self.assertEqual(calls, ["claim", "candidates"])
        self.assertEqual(set(vars(attempt)), {"claim", "candidates"})

    def test_fresh_and_claim_only_use_unmodified_pointer_schema(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            for epoch in (1, 2):
                attempt = Checkpointer("run", str(root / f"local-{epoch}"), str(root / "store"))
                self.assertEqual(claim_for_start(attempt), epoch)
                pointer = attempt.store.get_json("latest.json")
                self.assertEqual(pointer["epoch"], epoch)
                self.assertIsNone(pointer["path"])
                self.assertFalse(any("identity" in key or key.startswith("g5_") for key in pointer))

    def test_old_attempt_commit_after_takeover_is_fenced(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            old = Checkpointer("run", str(root / "old"), str(root / "store"))
            old.claim()
            new = Checkpointer("run", str(root / "new"), str(root / "store"))
            self.assertEqual(claim_for_start(new), 2)
            self.assertTrue(old.save(0, *state(), reason="start"))
            self.assertFalse(old.wait())
            self.assertTrue(old.any_fenced())
            self.assertEqual(new.store.get_json("latest.json")["epoch"], 2)
            self.assertIsNone(new.store.get_json("latest.json")["path"])
            self.assertEqual(new.commits(), [])

    def test_existing_candidates_refused_after_claim_preserving_checkpoint(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            old = Checkpointer("run", str(root / "old"), str(root / "store"))
            self.assertTrue(old.save(0, *state(), reason="start"))
            self.assertTrue(old.wait())
            previous = old.store.get_json("latest.json")
            new = Checkpointer("run", str(root / "new"), str(root / "store"))
            with self.assertRaisesRegex(CheckpointError, "use --resume-committed"):
                claim_for_start(new)
            pointer = new.store.get_json("latest.json")
            self.assertEqual(pointer["epoch"], 2)
            self.assertEqual(pointer["path"], previous["path"])
            self.assertTrue(new.store.exists(previous["path"] + "/MANIFEST.json"))

    def test_old_commit_during_claim_is_retried_then_detected_as_candidate(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            old = Checkpointer("run", str(root / "old"), str(root / "store"))
            old.claim()
            new = Checkpointer("run", str(root / "new"), str(root / "store"))
            put = new.store.put_json_if
            calls = []
            def race(key, value, version):
                calls.append(value)
                if len(calls) == 1:
                    self.assertTrue(old.save(0, *state(), reason="start"))
                    self.assertTrue(old.wait())
                return put(key, value, version)
            with patch.object(new.store, "put_json_if", race):
                with self.assertRaisesRegex(CheckpointError, "use --resume-committed"):
                    claim_for_start(new)
            self.assertEqual(len(calls), 2)
            self.assertEqual(new.epoch, 2)
            self.assertEqual(new.store.get_json("latest.json")["step"], 0)

    def test_competing_claim_is_fenced_without_candidate_lookup(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            Checkpointer("run", str(root / "old"), str(root / "store")).claim()
            new = Checkpointer("run", str(root / "new"), str(root / "store"))
            winner = Checkpointer("run", str(root / "winner"), str(root / "store"))
            put = new.store.put_json_if
            def race(key, value, version):
                winner.claim()
                return put(key, value, version)
            with patch.object(new.store, "put_json_if", race), patch.object(new, "candidates") as candidates:
                with self.assertRaises(FencedError):
                    claim_for_start(new)
            candidates.assert_not_called()
            self.assertIsNone(new.epoch)
            self.assertEqual(new.store.get_json("latest.json")["epoch"], 2)

    def test_metadata_errors_hold_instead_of_resetting(self):
        for stage in ("claim", "candidates"):
            with self.subTest(stage=stage):
                attempt = SimpleNamespace(claim=Mock(return_value=2), candidates=Mock(return_value=[]))
                getattr(attempt, stage).side_effect = PermissionError("unavailable")
                with self.assertRaisesRegex(CheckpointError, "Cannot claim or classify"):
                    claim_for_start(attempt)

    def test_two_rank_initialization_commits_step_zero(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            Checkpointer("run", str(root / "old"), str(root / "store")).claim()
            env = {**os.environ, "OMP_NUM_THREADS": "1", "V5_ASYNC_SAVE": "0"}
            worker = TEAM / "tests" / "precommit_distributed_worker.py"
            processes = [subprocess.Popen(
                [sys.executable, "-B", str(worker), str(root), str(rank)],
                env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            ) for rank in range(2)]
            try:
                for process in processes:
                    stdout, stderr = process.communicate(timeout=90)
                    self.assertEqual(process.returncode, 0, stdout + stderr)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                        process.communicate()
            results = [json.loads((root / f"rank-{rank}.json").read_text()) for rank in range(2)]
            self.assertEqual(results, [{"epoch": 2, "step": 0, "world": 2}] * 2)
            pointer = json.loads((root / "store" / "run" / "latest.json").read_text())
            self.assertEqual((pointer["epoch"], pointer["step"]), (2, 0))
            manifest = json.loads((root / "store" / "run" / pointer["path"] / "MANIFEST.json").read_text())
            self.assertEqual(manifest["world_size"], 2)


if __name__ == "__main__":
    unittest.main()
