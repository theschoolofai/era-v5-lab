"""run_lab_ckpt.py --scorer <module>:<function>, on a checkpoint saved through Team 7's Checkpointer (CPU, no network).

Needs torch >= 2.14.1 and safetensors, as run_lab_ckpt.py does; skipped otherwise.

    python -m pytest teams/09-evaluation/harness_lab/tests/test_run_lab_ckpt_scorer.py -q
"""
import hashlib
import importlib.util
import json
import sys
import textwrap
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("safetensors")
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run_lab_ckpt", HERE.parent / "run_lab_ckpt.py")
rl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rl)   # puts Team 7's folders on sys.path
if torch.__version__ < rl.MIN_TORCH:
    pytest.skip(f"run_lab_ckpt.py needs torch {rl.MIN_TORCH}", allow_module_level=True)

STUB = textwrap.dedent('''
    import torch

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.lin = torch.nn.Linear(4, 4)

        def forward(self, x):
            return self.lin(x)

    def probe(model):
        with torch.no_grad():
            return float(model(torch.ones(2, 4)).square().mean())

    class Scorer:
        name = "stub"

        def __init__(self, argv):
            self.argv = argv

        def check(self, manifest):
            if "--refuse" in self.argv:
                raise SystemExit(f"refused step {manifest['step']}")

        def factory(self):
            torch.manual_seed(0)
            return Tiny()

        def probe(self, model):
            return probe(model)

        def score(self, model, device):
            return [{"task": "stub_task", "metric": "acc", "filter": "none", "primary": True,
                     "value": round(100 * probe(model), 2) % 100, "stderr": None, "n_items": 2,
                     "item_set": "limit:2", "num_fewshot": 0, "decoding": "loglikelihood", "notes": self.argv,
                     "seed": {"random": 7, "numpy": 7, "torch": 7, "fewshot": 7},
                     "harness": {"name": "stub", "version": "1"}, "dtype": "float32"}]

    def make(argv):
        return Scorer(argv)
''')


@pytest.fixture
def store(tmp_path, monkeypatch):
    """One commit at step 10 in Team 7's layout, and the stub scorer module on sys.path."""
    (tmp_path / "stub_scorer.py").write_text(STUB, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path / "events"))
    import stub_scorer
    from ckpt.ckpt import Checkpointer
    from trainer.tiny import SyntheticLoader

    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)
    model = stub_scorer.Scorer([]).factory()
    optim = torch.optim.AdamW(model.parameters(), lr=1e-3)
    ck = Checkpointer("run-s", str(tmp_path / "local"), str(tmp_path / "store"), seed=0)
    assert ck.save(10, model, optim, SyntheticLoader(0, 2, 0, 1), stub_scorer.probe, tokens=40) and ck.wait()
    yield tmp_path / "store" / "run-s"
    sys.modules.pop("stub_scorer", None)


def test_a_module_scorer_gets_the_unknown_arguments_and_sets_its_fields(store, tmp_path, capsys):
    out = tmp_path / "out.json"
    assert rl.main(["--run-dir", str(store), "--step", "10", "--scorer", "stub_scorer:make", "--out", str(out),
                    "--tier", "A", "--flag", "x"]) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    (rec,) = doc["records"]
    manifest = store / "main" / "step_00000010-e1" / "MANIFEST.json"
    assert rec["model_revision"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert rec["checkpoint"] == {"run": "run-s", "branch": "main", "step": 10, "epoch": 1, "tokens_seen": 40,
                                 "path": f"{store.as_posix()}/main/step_00000010-e1"}
    assert rec["notes"] == ["--tier", "A", "--flag", "x"]
    assert (rec["harness"]["name"], rec["seed"]["random"], rec["backend"]) == ("stub", 7, "lab")
    assert list(rec)[-4:] == ["seed", "harness", "hardware", "run_date"]
    printed = capsys.readouterr().out
    assert "probe loss bits equal the saved ones" in printed and "TIME export" in printed


def test_a_scorer_can_refuse_a_checkpoint(store, tmp_path):
    with pytest.raises(SystemExit, match="refused step 10"):
        rl.main(["--run-dir", str(store), "--scorer", "stub_scorer:make", "--out", str(tmp_path / "o.json"),
                 "--refuse"])
    assert not (tmp_path / "o.json").exists()


def test_smoke_refuses_unknown_arguments_and_cuda(store, tmp_path):
    for extra in (["--tier", "A"], ["--device", "cuda"]):
        with pytest.raises(SystemExit) as e:
            rl.main(["--run-dir", str(store), "--out", str(tmp_path / "o.json"), *extra])
        assert e.value.code == 2
