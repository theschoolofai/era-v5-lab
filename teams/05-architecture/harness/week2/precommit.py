"""Draft D3 recovery protocol for a shared filesystem with working OS file locks.

The lock is held for the entire trainer invocation. It is never expired by age,
deleted, or replaced. Only claims written while holding this lock are eligible
for recovery; legacy claims and object stores remain operator-held.
"""

import os
import platform
import time
from pathlib import Path


PROTOCOL = "g5-local-owner-lock/1"
LOCK_NAME = ".g5-owner.lock"


class PrecommitRecoveryError(RuntimeError):
    """Recovery cannot establish exclusive ownership; hold rather than guess."""


class LocalOwnerGuard:
    def __init__(self, root):
        self.path = Path(root) / LOCK_NAME
        self.file = None

    def __enter__(self):
        try:
            self.file = self.path.open("a+b")
            if self.path.stat().st_size == 0:
                self.file.write(b"\0")
                self.file.flush()
            self.file.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, ImportError) as error:
            if self.file is not None:
                self.file.close()
                self.file = None
            raise PrecommitRecoveryError("Cannot acquire the G5 run-owner lock; another trainer may be live") from error
        return self

    def __exit__(self, *_):
        # Closing releases the OS lock, including on process death. Never unlink
        # its path: another process might otherwise lock a different inode.
        self.file.close()
        self.file = None


def claim_initial_state(checkpointer, guard, *, identity_sha256, recovering=False):
    """CAS one fresh claim and seed G7's existing fencing state; never retry CAS.

    G7's normal claim() can take over an existing owner. D3 must instead hold
    the lifetime lock AND compare the exact inspected pointer version. The
    epoch/_ptr_ver assignments below are the draft integration seam with G7;
    save()/claim() then use their usual conditional-commit behavior unchanged.
    """
    try:
        store = checkpointer.store
        if not isinstance(identity_sha256, str) or not identity_sha256:
            raise PrecommitRecoveryError("A resolved G5 training identity is required")
        if (getattr(store, "kind", None) != "local" or guard.file is None
                or guard.path != Path(store.root) / LOCK_NAME):
            raise PrecommitRecoveryError("Precommit recovery requires the held shared-filesystem owner lock")
        if checkpointer.epoch is not None:
            raise PrecommitRecoveryError("This attempt has already claimed the run")
        claim, version = store.get_json_ver("latest.json")
        history = Path(store.root) / "commits.jsonl"
        try:
            commits = history.read_text(encoding="utf8")
        except FileNotFoundError:
            commits = ""
        # Any history (including malformed history) forbids fresh initialization.
        if commits.strip():
            raise PrecommitRecoveryError("Commit history exists; use committed resume, not fresh recovery")
        if recovering:
            if not isinstance(claim, dict) or claim.get("g5_owner_protocol") != PROTOCOL:
                raise PrecommitRecoveryError("Legacy or unknown claim: owner liveness cannot be established")
            if claim.get("g5_identity_sha256") != identity_sha256:
                raise PrecommitRecoveryError("G5 code/config/artifact/data/device/software identity changed")
            if not {"path", "step", "branch", "epoch", "g5_owner_epoch"}.issubset(claim):
                raise PrecommitRecoveryError("Claim is missing required pointer fields")
            epoch = claim.get("epoch")
            if (type(epoch) is not int or epoch < 1
                    or type(claim.get("g5_owner_epoch")) is not int or claim["g5_owner_epoch"] != epoch
                    or claim.get("path") is not None
                    or claim.get("step") is not None or claim.get("branch") is not None):
                raise PrecommitRecoveryError("Claim is malformed or already names a checkpoint; refusing fresh recovery")
        elif claim is not None or version is not None:
            raise PrecommitRecoveryError("Run already has a claim; explicit recovery or committed resume is required")
        previous_epoch = claim["epoch"] if claim is not None else 0
        new = {"path": None, "step": None, "branch": None, "epoch": previous_epoch + 1,
               "job": os.environ.get("SLURM_JOB_ID"), "host": platform.node(),
               "claimed_at": time.time(), "g5_owner_protocol": PROTOCOL,
               "g5_owner_epoch": previous_epoch + 1, "g5_identity_sha256": identity_sha256}
        pointer_version = store.put_json_if("latest.json", new, version)
        checkpointer.epoch = new["epoch"]
        checkpointer._ptr_ver = pointer_version
        return {"previous_epoch": previous_epoch, "epoch": new["epoch"]}
    except PrecommitRecoveryError:
        raise
    except Exception as error:
        raise PrecommitRecoveryError("Cannot safely read or claim the run; metadata may have changed or be inaccessible") from error
