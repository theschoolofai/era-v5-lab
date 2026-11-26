"""D3 ownership tests use the real local store and OS locks, without CUDA."""

from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

TEAM = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(TEAM / "harness"), str(TEAM.parent / "07-infrastructure")]
from ckpt.store import Conflict, LocalStore
from week2.precommit import LocalOwnerGuard, PrecommitRecoveryError, claim_initial_state as _claim_initial_state


def claim_initial_state(*args, **kwargs):
    return _claim_initial_state(*args, identity_sha256="test-identity", **kwargs)


class PrecommitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = LocalStore(str(Path(self.temp.name) / "run"))

    def pointer(self):
        return self.store.get_json_ver("latest.json")

    def attempt(self):
        return SimpleNamespace(store=self.store, epoch=None, _ptr_ver=None)

    def seed(self):
        with LocalOwnerGuard(self.store.root) as guard:
            claim_initial_state(self.attempt(), guard)

    def test_recovery_requires_opt_in_and_preserves_old_writer_fencing(self):
        old = self.attempt()
        with LocalOwnerGuard(self.store.root) as guard:
            claim_initial_state(old, guard)
        before = self.pointer()
        with LocalOwnerGuard(self.store.root) as guard:
            with self.assertRaises(PrecommitRecoveryError):
                claim_initial_state(self.attempt(), guard)
            self.assertEqual(self.pointer(), before)
            new = self.attempt()
            info = claim_initial_state(new, guard, recovering=True)
            self.assertEqual(info, {"previous_epoch": 1, "epoch": 2})
            self.assertEqual(new._ptr_ver, self.pointer()[1])
        with self.assertRaises(Conflict):
            self.store.put_json_if("latest.json", {"path": "old-writer"}, old._ptr_ver)

    def test_live_owner_excludes_other_attempts_and_death_releases_lock(self):
        script = (
            "import sys,time; sys.path[:0]=sys.argv[2:]; "
            "from week2.precommit import LocalOwnerGuard; "
            "from ckpt.store import LocalStore; "
            "from types import SimpleNamespace; "
            "from week2.precommit import claim_initial_state; "
            "store=LocalStore(sys.argv[1]); guard=LocalOwnerGuard(store.root); guard.__enter__(); "
            "claim_initial_state(SimpleNamespace(store=store,epoch=None,_ptr_ver=None),guard,identity_sha256='test-identity'); "
            "print('locked',flush=True); time.sleep(60)"
        )
        owner = subprocess.Popen([sys.executable, "-c", script, self.store.root,
                                  str(TEAM / "harness"), str(TEAM.parent / "07-infrastructure")],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(owner.stdout.readline().strip(), "locked")
            before = self.pointer()
            with self.assertRaises(PrecommitRecoveryError):
                with LocalOwnerGuard(self.store.root):
                    self.fail("live owner's lock was acquired")
            self.assertEqual(self.pointer(), before)
        finally:
            owner.kill()
            owner.communicate(timeout=10)
        with LocalOwnerGuard(self.store.root) as guard:
            claim_initial_state(self.attempt(), guard, recovering=True)
        self.assertEqual(self.pointer()[0]["epoch"], 2)

    def test_only_one_recovery_can_use_an_inspected_claim(self):
        self.seed()
        before = self.pointer()
        write = self.store.put_json_if

        def competing_write(key, value, version):
            write(key, dict(before[0], epoch=2), version)
            return write(key, value, version)

        attempt = self.attempt()
        with LocalOwnerGuard(self.store.root) as guard, patch.object(self.store, "put_json_if", competing_write):
            with self.assertRaises(PrecommitRecoveryError):
                claim_initial_state(attempt, guard, recovering=True)
        self.assertIsNone(attempt.epoch)
        self.assertEqual(self.pointer()[0]["epoch"], 2)

    def test_unknown_malformed_and_committed_claims_hold_without_mutation(self):
        self.seed()
        valid = self.pointer()[0]
        cases = [
            {}, dict(valid, g5_owner_protocol="unknown"), dict(valid, epoch=True),
            dict(valid, g5_identity_sha256="different-inputs"),
            dict(valid, epoch=2), dict(valid, path="main/step_0-e1", step=0),
            dict(valid, branch="main"),
            {key: value for key, value in valid.items() if key != "path"},
        ]
        for claim in cases:
            with self.subTest(claim=claim):
                self.store.put_json("latest.json", claim)
                before = self.pointer()
                with LocalOwnerGuard(self.store.root) as guard:
                    with self.assertRaises(PrecommitRecoveryError):
                        claim_initial_state(self.attempt(), guard, recovering=True)
                self.assertEqual(self.pointer(), before)

    def test_any_commit_history_prevents_fresh_recovery(self):
        self.seed()
        for history in ('{"step":0,"path":"main/step_0-e1"}\n', 'torn-json\n'):
            with self.subTest(history=history):
                Path(self.store.root, "commits.jsonl").write_text(history)
                before = self.pointer()
                with LocalOwnerGuard(self.store.root) as guard:
                    with self.assertRaises(PrecommitRecoveryError):
                        claim_initial_state(self.attempt(), guard, recovering=True)
                self.assertEqual(self.pointer(), before)

    def test_missing_claim_or_unheld_guard_cannot_recover(self):
        with LocalOwnerGuard(self.store.root) as guard:
            with self.assertRaises(PrecommitRecoveryError):
                claim_initial_state(self.attempt(), guard, recovering=True)
        with self.assertRaises(PrecommitRecoveryError):
            claim_initial_state(self.attempt(), guard)
        self.assertEqual(self.pointer(), (None, None))

    def test_store_failure_holds_without_claiming(self):
        for method in ("get_json_ver", "put_json_if"):
            with self.subTest(method=method):
                attempt = self.attempt()
                with LocalOwnerGuard(self.store.root) as guard, patch.object(
                        self.store, method, side_effect=PermissionError("unavailable")):
                    with self.assertRaises(PrecommitRecoveryError):
                        claim_initial_state(attempt, guard)
                self.assertIsNone(attempt.epoch)

    def test_object_store_has_no_local_liveness_proof(self):
        store = SimpleNamespace(kind="s3")
        attempt = SimpleNamespace(store=store, epoch=None, _ptr_ver=None)
        with LocalOwnerGuard(self.store.root) as guard:
            with self.assertRaises(PrecommitRecoveryError):
                claim_initial_state(attempt, guard, recovering=True)
        self.assertIsNone(attempt.epoch)


if __name__ == "__main__":
    unittest.main()
