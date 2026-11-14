"""Protect the Slurm source snapshot from local build/runtime artifacts."""
from pathlib import Path
import tempfile
from unittest import TestCase, main
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slurm_gate2

class SourceSnapshotTests(TestCase):
    def test_allowed_worker_and_blocked_runtime_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (
                "tests/gate2_worker.py",
                ".venv/bin/python",
                "evidence/host/summary.json",
                "out/run/result.json",
                "other/state.pt",
            ):
                f = root / name
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("fixture")
            with patch.object(slurm_gate2, "ROOT", root):
                self.assertTrue(slurm_gate2.should_stage_source(root / "tests/gate2_worker.py"))
                for name in (".venv/bin/python", "evidence/host/summary.json",
                             "out/run/result.json", "other/state.pt"):
                    with self.subTest(name=name):
                        self.assertFalse(slurm_gate2.should_stage_source(root / name))

if __name__ == "__main__":
    main()
