"""Run G5 through Team 7's real filesystem commit and restore path."""

import itertools
import json
import os
import signal
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import torch

from test_week2_model import TEAM, fixture
import train_week2


class Team7CheckpointTests(unittest.TestCase):
    def test_nonfinite_step_exits_78_before_update_or_checkpoint(self):
        team7 = TEAM.parent / "07-infrastructure"
        score = train_week2.scored_ntp_loss
        build = train_week2.build_optimizer
        for flags in ([], ["--no-consolidate-step-checks"]):
            for fault in ("loss", "gradient"):
                with self.subTest(flags=flags, fault=fault), TemporaryDirectory() as temp:
                    root = Path(temp)
                    cfg, byte_rows, _ = fixture()
                    cfg["model"]["ke_max_pos"] = byte_rows.shape[1]
                    artifacts = SimpleNamespace(
                        bytes=byte_rows, lengths=np.ones(len(byte_rows), dtype=np.int16),
                        pos_dim=byte_rows.shape[1], bos_id=0, pad_id=1,
                        encode=lambda text: [ord(char) - ord("a") + 2 for char in text],
                        identity=lambda: {}, normalize_input=False,
                    )
                    train, val = root / "train.jsonl", root / "val.jsonl"
                    train.write_text('{"text":"aaaa"}\n', encoding="utf8")
                    val.write_text('{"text":"bbbb"}\n', encoding="utf8")
                    args = [
                        "trainer", "--config", "fixture.yaml", "--tokenizer", "fixture.json",
                        "--byte-table", "fixture.npz", "--train-data", str(train),
                        "--heldout-data", str(val), "--out", str(root / "out"),
                        "--smoke", "--smoke-steps", "1", "--smoke-batch-size", "1",
                        "--checkpoint-store", str(root / "store"), "--run-id", "nonfinite", *flags,
                    ]
                    updates = []

                    def tracked_optimizer(*args, **kwargs):
                        optimizer = build(*args, **kwargs)
                        optimizer.step = Mock(wraps=optimizer.step)
                        updates.append(optimizer.step)
                        return optimizer

                    def faulty_score(model, *args, **kwargs):
                        value = score(model, *args, **kwargs)
                        if model.training:
                            if fault == "loss":
                                value = value * float("nan")
                            else:
                                value.register_hook(lambda grad: grad * float("nan"))
                        return value

                    with (
                        patch.object(sys, "argv", args),
                        patch.object(sys, "path", [str(team7), *sys.path]),
                        patch.object(train_week2, "load_runtime", return_value=cfg),
                        patch.object(train_week2, "Artifacts", return_value=artifacts),
                        patch.object(train_week2, "scored_ntp_loss", faulty_score),
                        patch.object(train_week2, "build_optimizer", tracked_optimizer),
                        patch.dict(os.environ, {"V5_RUNS_DIR": str(root / "notes")}),
                    ):
                        from ckpt.ckpt import Checkpointer
                        with patch.object(Checkpointer, "save") as save, self.assertRaises(SystemExit) as failure:
                            train_week2.main()
                        self.assertEqual(failure.exception.code, 78)
                        save.assert_not_called()
                    notes = list((root / "notes").rglob("exit-*.json"))
                    self.assertEqual(len(notes), 1)
                    note = json.loads(notes[0].read_text())
                    self.assertEqual(note["code"], 78)
                    self.assertEqual(note["cause"], "NonfiniteTrainingError")
                    self.assertLessEqual(len(note["detail"]), 400)
                    if fault == "gradient" and not flags:
                        self.assertIn("after clipping", note["detail"])
                        self.assertIn("tensors:", note["detail"])
                    elif fault == "loss":
                        self.assertIn("objective", note["detail"])
                    self.assertEqual(len(updates), 1)
                    updates[0].assert_not_called()
                    self.assertFalse((root / "out" / "checkpoint.pt").exists())
                    self.assertFalse((root / "out" / "summary.json").exists())

    def test_wall_clock_commits_and_bit_equal_resume(self):
        for optimizer, mtp in (("adamw", False), ("muon", False), ("adamw", True)):
            with self.subTest(optimizer=optimizer, inactive_mtp=mtp):
                self.check_resume(optimizer, mtp)

    def test_step_zero_commit_preserves_training_and_resumes(self):
        for optimizer, mtp in (("adamw", False), ("muon", False), ("adamw", True)):
            with self.subTest(optimizer=optimizer, inactive_mtp=mtp):
                self.check_resume(optimizer, mtp, at_start=True)

    def test_precommit_recovery_preserves_initialization_and_resumes(self):
        for optimizer in ("adamw", "muon"):
            with self.subTest(optimizer=optimizer):
                self.check_resume(optimizer, False, at_start=True, precommit=True)

    def test_normal_fresh_and_resume_do_not_call_initialization_adapter(self):
        with patch.object(train_week2, "claim_for_start", side_effect=AssertionError("initialization adapter called")):
            self.check_resume("adamw", False, check_fresh=True)

    def test_recovery_requires_step_zero_commit_before_any_optimizer_update(self):
        for failure in ("skipped", "upload", "fenced", "unconfirmed", "candidates", "competing"):
            with self.subTest(failure=failure):
                self.check_resume("adamw", False, precommit=True, failure=failure)

    def test_failed_native_export_preserves_previous_artifact(self):
        with TemporaryDirectory() as temp:
            checkpoint = Path(temp) / "checkpoint.pt"
            checkpoint.write_bytes(b"previous checkpoint")

            def fail_save(state, stream):
                stream.write(b"partial")
                raise OSError("interrupted write")

            with patch.object(torch, "save", side_effect=fail_save), self.assertRaises(OSError):
                train_week2.write_native_checkpoint({}, checkpoint)
            self.assertEqual(checkpoint.read_bytes(), b"previous checkpoint")
            self.assertEqual(list(Path(temp).iterdir()), [checkpoint])

    def test_quality_run_requires_team7_store_before_loading_inputs(self):
        args = ["trainer"]
        for name in ("config", "tokenizer", "byte-table", "train-data", "heldout-data", "out"):
            args.extend([f"--{name}", "unused"])
        with patch.object(sys, "argv", args), patch.object(train_week2, "load_runtime") as load:
            with self.assertRaises(SystemExit) as failure:
                train_week2.main()
        self.assertEqual(failure.exception.code, 2)
        load.assert_not_called()

    def check_resume(self, optimizer, mtp, at_start=False, precommit=False, device="cpu", failure=None, check_fresh=False):
        cfg, byte_rows, _ = fixture(mtp=mtp)
        cfg["model"].update(ke_max_pos=byte_rows.shape[1], mtp_weight=0.0)
        cfg["optim"].update(name=optimizer, muon_lr=0.01 if optimizer == "muon" else None)
        if device == "cuda":
            cfg["run"]["dtype"] = "bf16"
        artifacts = SimpleNamespace(
            bytes=byte_rows,
            lengths=np.ones(len(byte_rows), dtype=np.int16),
            pos_dim=byte_rows.shape[1],
            bos_id=0,
            pad_id=1,
            encode=lambda text: [ord(char) - ord("a") + 2 for char in text],
            identity=lambda: {},
            normalize_input=False,
        )
        team7 = TEAM.parent / "07-infrastructure"
        g8 = TEAM.parent / "08-monitoring" / "metrics_logger"
        with TemporaryDirectory() as temp:
            root = Path(temp)
            train = root / "train.jsonl"
            val = root / "val.jsonl"
            train.write_text('{"text":"aaaa"}\n{"text":"aaa"}\n', encoding="utf8")
            val.write_text('{"text":"bbbb"}\n', encoding="utf8")
            common = [
                "train_week2.py", "--config", "fixture.yaml",
                "--tokenizer", "fixture.json", "--byte-table", "fixture.npz",
                "--train-data", str(train), "--heldout-data", str(val),
                "--smoke", "--smoke-steps", "5", "--smoke-batch-size", "1",
                "--logger-factory", "g5_adapter:make_writer",
                "--device", device,
            ]
            if device == "cuda":
                common.extend(["--watchdog-s", "60"])
            store = root / "store"
            run_store = store / "g5-test"
            committed = [
                "--checkpoint-store", str(store), "--run-id", "g5-test",
            ]
            if at_start:
                committed.append("--checkpoint-at-start")
            if optimizer == "muon":
                committed.extend(["--checkpoint-interval-s", "600"])

            def run(name, *args):
                out = root / name
                clock = itertools.count(0, 300)
                with (
                    patch.object(sys, "argv", [*common, "--out", str(out), *args]),
                    patch.object(train_week2, "checkpoint_clock", side_effect=lambda: next(clock)),
                ):
                    train_week2.main()
                return out

            with (
                patch.object(train_week2, "load_runtime", return_value=cfg),
                patch.object(train_week2, "Artifacts", return_value=artifacts),
                patch.object(sys, "path", [str(team7), str(g8), *sys.path]),
                patch.dict(os.environ, {
                    "INTERVAL_S": "invalid" if optimizer == "muon" else "600",
                    "V5_RUNS_DIR": str(root / "exit-notes"),
                }),
            ):
                from ckpt.ckpt import Checkpointer, FencedError
                from ckpt.store import LocalStore

                baseline = run("baseline")
                if check_fresh:
                    with patch.object(train_week2, "evaluate", side_effect=SystemExit(9)):
                        with self.assertRaises(SystemExit) as early:
                            run("before-save", *committed)
                    self.assertEqual(early.exception.code, 9)
                    self.assertFalse((run_store / "latest.json").exists())
                if precommit:
                    # Ordinary startup still claims lazily at save time. Fail
                    # after that existing claim, before any upload/commit.
                    def interrupted_save(checkpointer, *args, **kwargs):
                        checkpointer.claim()
                        raise SystemExit(9)

                    with patch.object(Checkpointer, "save", interrupted_save):
                        with self.assertRaises(SystemExit) as interrupted:
                            run("interrupted", *committed)
                    self.assertEqual(interrupted.exception.code, 9)
                    initial_claim = json.loads((run_store / "latest.json").read_text())
                    self.assertIsNone(initial_claim["path"])
                    self.assertFalse((run_store / "commits.jsonl").exists())
                    # A sealed but unreferenced upload is still not a commit.
                    orphan = run_store / "main" / "step_00000000-e1"
                    orphan.mkdir(parents=True)
                    (orphan / "MANIFEST.json").write_text('{"step":0}')
                    if "--checkpoint-at-start" not in committed:
                        committed.append("--checkpoint-at-start")
                if failure is not None:
                    faults = {
                        "skipped": patch.object(Checkpointer, "save", return_value=False),
                        "upload": patch.object(LocalStore, "put_file", side_effect=OSError("upload failed")),
                        "fenced": patch.object(Checkpointer, "wait", side_effect=FencedError("new owner")),
                        "unconfirmed": patch.object(Checkpointer, "wait", return_value=False),
                        "candidates": patch.object(Checkpointer, "candidates", return_value=[{"path": "committed"}]),
                        "competing": patch.object(Checkpointer, "claim", side_effect=FencedError("competing claim")),
                    }
                    # For wait failures, simulate an accepted request without
                    # starting a real uploader that could commit after the test.
                    from contextlib import nullcontext
                    accepted = (patch.object(Checkpointer, "save", return_value=True)
                                if failure in ("fenced", "unconfirmed") else nullcontext())
                    with accepted, faults[failure], patch.object(train_week2, "set_lr_scale") as update:
                        with self.assertRaises(SystemExit) as stopped:
                            run("failed-recovery", *committed)
                    self.assertEqual(stopped.exception.code, 78 if failure in ("fenced", "candidates", "competing") else 75)
                    # set_lr_scale immediately precedes the optimizer update.
                    update.assert_not_called()
                    self.assertFalse((root / "failed-recovery" / "checkpoint.pt").exists())
                    self.assertFalse((root / "failed-recovery" / "summary.json").exists())
                    self.assertFalse((run_store / "commits.jsonl").exists())
                    notes = list((root / "exit-notes").rglob("exit-*.json"))
                    self.assertEqual(len(notes), 1)
                    note = json.loads(notes[0].read_text())
                    self.assertEqual(note["code"], stopped.exception.code)
                    if failure == "candidates":
                        self.assertIn("use --resume-committed", note["detail"])
                    return
                actions = []
                save = Checkpointer.save
                wait = Checkpointer.wait

                def track_save(checkpointer, *args, **kwargs):
                    actions.append(kwargs["reason"])
                    return save(checkpointer, *args, **kwargs)

                def track_wait(checkpointer):
                    actions.append("wait")
                    return wait(checkpointer)

                with patch.object(Checkpointer, "save", track_save), patch.object(Checkpointer, "wait", track_wait):
                    first = run("first", *committed, "--stop-after", "3")
                self.assertEqual(actions, (["start"] if at_start else [])
                                 + (["wait"] if at_start else []) + ["interval", "final", "wait"])

                if check_fresh:
                    pointer = (run_store / "latest.json").read_bytes()
                    with self.assertRaises(SystemExit) as duplicate:
                        run("duplicate-fresh", *committed)
                    self.assertEqual(duplicate.exception.code, 2)
                    self.assertEqual((run_store / "latest.json").read_bytes(), pointer)

                if at_start:
                    if precommit:
                        initialization = json.loads((first / "manifest.json").read_text())["team7_initialization"]
                        self.assertEqual(initialization, {"epoch": 2})
                    self.assertEqual(
                        (first / "losses.txt").read_text().splitlines(),
                        (baseline / "losses.txt").read_text().splitlines()[:3],
                    )
                    start_entries = [
                        json.loads(line) for line in (run_store / "commits.jsonl").read_text().splitlines()
                        if json.loads(line)["step"] == 0
                    ]
                    self.assertEqual(len(start_entries), 1)
                    start = start_entries[0]
                    start_manifest = json.loads((run_store / start["path"] / "MANIFEST.json").read_text())
                    self.assertEqual((start_manifest["step"], start_manifest["reason"]), (0, "start"))
                    start_extra = json.loads((run_store / start["path"] / "extra_rank0.json").read_text())
                    if optimizer == "adamw":
                        self.assertEqual(start_extra["loader"]["history"]["initial_optimizer"]["state"], {})
                    # Make step 0 the sole candidate to exercise its normal restore path.
                    (run_store / "commits.jsonl").write_text(json.dumps(start) + "\n")
                    (run_store / "latest.json").write_text(json.dumps(start))
                    from_start = run("from-start", *committed, "--resume-committed")
                    self.assertEqual((from_start / "losses.txt").read_bytes(), (baseline / "losses.txt").read_bytes())
                    start_summary = json.loads((from_start / "summary.json").read_text())
                    base_summary = json.loads((baseline / "summary.json").read_text())
                    self.assertEqual(start_summary["final_model_sha256"], base_summary["final_model_sha256"])
                    from ckpt.ckpt import run_retention
                    from ckpt.store import open_store
                    open_store(str(run_store)).put_json("pins.json", [0])
                    run_retention(str(run_store), keep=1)
                    self.assertTrue((run_store / start["path"] / "MANIFEST.json").exists())
                    self.assertFalse(any(entry["step"] == 0 for entry in [
                        json.loads(line) for line in (run_store / "commits.jsonl").read_text().splitlines()
                    ][1:]))
                    return
                if optimizer == "muon":
                    latest = json.loads((run_store / "latest.json").read_text())
                    extra = run_store / latest["path"] / "extra_rank0.json"
                    extra.write_bytes(extra.read_bytes() + b"corrupt checkpoint")
                resumed = run("resumed", *committed, "--resume-committed")

                if optimizer == "adamw" and not mtp:
                    with patch.object(Checkpointer, "save", return_value=False):
                        with self.assertRaises(SystemExit) as retry:
                            run("failed", *committed, "--run-id", "failed", "--stop-after", "1")
                    self.assertEqual(retry.exception.code, 75)
                    self.assertFalse((root / "failed" / "checkpoint.pt").exists())
                    self.assertFalse((root / "failed" / "summary.json").exists())

                    with patch.object(LocalStore, "put_file", side_effect=OSError("upload failed")):
                        with self.assertRaises(SystemExit) as upload_failure:
                            run("upload-failed", *committed, "--run-id", "upload-failed", "--stop-after", "1")
                    self.assertEqual(upload_failure.exception.code, 75)
                    self.assertFalse((root / "upload-failed" / "checkpoint.pt").exists())
                    self.assertFalse((root / "upload-failed" / "summary.json").exists())

                    with patch.object(Checkpointer, "save", side_effect=FencedError("new owner")):
                        with self.assertRaises(SystemExit) as fenced:
                            run("fenced", *committed, "--run-id", "fenced", "--stop-after", "1")
                    self.assertEqual(fenced.exception.code, 78)
                    self.assertFalse((root / "fenced" / "checkpoint.pt").exists())

                    next_batch = train_week2.BatchStream.next
                    signalled = False

                    def signal_after_batch(stream, device):
                        nonlocal signalled
                        batch = next_batch(stream, device)
                        if not signalled:
                            signalled = True
                            signal.raise_signal(signal.SIGTERM)
                        return batch

                    with patch.object(train_week2.BatchStream, "next", signal_after_batch):
                        with self.assertRaises(SystemExit) as stopped:
                            run("signal", *committed, "--run-id", "signal")
                    self.assertEqual(stopped.exception.code, 75)
                    signal_store = store / "signal"
                    signal_commit = json.loads((signal_store / "latest.json").read_text())
                    signal_manifest = json.loads((signal_store / signal_commit["path"] / "MANIFEST.json").read_text())
                    self.assertEqual((signal_manifest["step"], signal_manifest["reason"]), (1, "signal"))
                    self.assertFalse((root / "signal" / "checkpoint.pt").exists())

            commits = [
                json.loads(line) for line in (run_store / "commits.jsonl").read_text().splitlines()
            ]
            expected = [(2, "interval"), (3, "final")]
            expected += [(4, "interval")] if optimizer == "muon" else []
            expected += [(5, "final")]
            self.assertEqual([(entry["step"], entry["reason"]) for entry in commits], expected)
            for entry in commits:
                manifest = json.loads((run_store / entry["path"] / "MANIFEST.json").read_text())
                self.assertEqual(manifest["step"], entry["step"])
                self.assertEqual(manifest["run_id"], "g5-test")
            for filename in ("losses.txt", "total_losses.txt"):
                self.assertEqual((resumed / filename).read_bytes(), (baseline / filename).read_bytes())
            summaries = [json.loads((out / "summary.json").read_text()) for out in (baseline, resumed)]
            self.assertEqual(summaries[0]["final_model_sha256"], summaries[1]["final_model_sha256"])
            rows = [json.loads(line) for line in (resumed / "metrics.jsonl").read_text().splitlines()]
            self.assertEqual([row["step"] for row in rows], list(range(6)))
            self.assertTrue((first / "checkpoint.pt").is_file())
            self.assertTrue((resumed / "checkpoint.pt").is_file())
            self.assertEqual(summaries[1]["run_id"], "g5-test")
            latest = json.loads((run_store / "latest.json").read_text())
            self.assertEqual(summaries[1]["team7_checkpoint_path"], latest["path"])
            manifest = json.loads((resumed / "manifest.json").read_text())
            self.assertEqual(manifest["team7_checkpoint"]["interval_s"], 600)
            g8_rows = [
                json.loads(line) for line in (resumed / "g8" / "metrics.jsonl").read_text().splitlines()
            ]
            self.assertEqual([row["step"] for row in g8_rows], list(range(6)))
            self.assertEqual({row["run_id"] for row in g8_rows}, {"g5-test"})


if __name__ == "__main__":
    unittest.main()
