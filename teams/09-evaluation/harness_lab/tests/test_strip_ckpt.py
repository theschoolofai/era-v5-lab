"""strip_ckpt.py and run_lab_ckpt.py --weights, on a commit saved through Team 7's Checkpointer (CPU, no network).

Needs torch >= 2.14.1 and safetensors, as run_lab_ckpt.py does; skipped otherwise.

    python -m pytest teams/09-evaluation/harness_lab/tests/test_strip_ckpt.py -q
"""
import hashlib
import importlib.util
import json
import os
import sys
import textwrap
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("safetensors")
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("run_lab_ckpt", HERE.parent / "run_lab_ckpt.py")
rl = importlib.util.module_from_spec(_spec)
sys.modules["run_lab_ckpt"] = rl
_spec.loader.exec_module(rl)   # puts Team 7's folders on sys.path
if rl.version_key(torch.__version__) < rl.version_key(rl.MIN_TORCH):
    pytest.skip(f"run_lab_ckpt.py needs torch {rl.MIN_TORCH}", allow_module_level=True)
_spec2 = importlib.util.spec_from_file_location("strip_ckpt", HERE.parent / "strip_ckpt.py")
sc = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(sc)

STUB = textwrap.dedent('''
    import torch

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.a = torch.nn.Linear(512, 512)
            self.b = torch.nn.Linear(512, 8)

        def forward(self, x):
            return self.b(torch.relu(self.a(x)))

    def probe(model):
        with torch.no_grad():
            return float(model(torch.ones(2, 512)).square().mean())

    class Scorer:
        name = "stub"

        def __init__(self, argv):
            self.argv = argv

        def check(self, manifest):
            pass

        def factory(self):
            torch.manual_seed(0)
            return Tiny()

        def probe(self, model):
            return probe(model)

        def score(self, model, device):
            return [{"task": "stub_task", "metric": "acc", "filter": "none", "primary": True,
                     "value": round(100 * probe(model), 4) % 100, "stderr": None, "n_items": 2,
                     "item_set": "limit:2", "num_fewshot": 0, "decoding": "loglikelihood", "notes": [],
                     "seed": {"random": 7, "numpy": 7, "torch": 7, "fewshot": 7},
                     "harness": {"name": "stub", "version": "1"},
                     "dtype": str(next(model.parameters()).dtype).removeprefix("torch.")}]

    def make(argv):
        return Scorer(argv)
''')
COMMIT = "main/step_00000010-e1"


@pytest.fixture
def store(tmp_path, monkeypatch):
    """One commit at step 10 (weights and AdamW state), probe bits for cpu; the stub scorer on sys.path."""
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
    model(torch.ones(2, 512)).sum().backward()
    optim.step()                                   # so the commit holds the optimizer state too
    ck = Checkpointer("run-s", str(tmp_path / "local"), str(tmp_path / "store"), seed=0)
    assert ck.save(10, model, optim, SyntheticLoader(0, 2, 0, 1), stub_scorer.probe, tokens=40) and ck.wait()
    yield tmp_path / "store" / "run-s"
    sys.modules.pop("stub_scorer", None)


def score(store, tmp_path, *extra) -> dict:
    out = tmp_path / f"out{len(list(tmp_path.glob('out*.json')))}.json"
    assert rl.main(["--run-dir", str(store), "--step", "10", "--scorer", "stub_scorer:make", "--out", str(out),
                    *extra]) == 0
    return json.loads(out.read_text(encoding="utf-8"))["records"][0]


def test_the_strip_holds_the_same_tensors_as_the_export(store, tmp_path):
    import stub_scorer
    from ckpt.ckpt import export_safetensors
    from safetensors.torch import load_file

    exported = tmp_path / "export.safetensors"
    export_safetensors(store.as_posix(), stub_scorer.Scorer([]).factory, stub_scorer.probe, str(exported), step=10)
    rec = sc.strip(store, 10, tmp_path / "s.safetensors")
    a, b = load_file(str(exported)), load_file(str(tmp_path / "s.safetensors"))
    assert set(a) == set(b) and all(a[k].dtype == b[k].dtype and torch.equal(a[k], b[k]) for k in a)
    manifest = store / COMMIT / "MANIFEST.json"
    assert rec["model_revision"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert rec["weights_sha256"] == hashlib.sha256((tmp_path / "s.safetensors").read_bytes()).hexdigest()
    assert rec["path"] == COMMIT and rec["step"] == 10 and rec["tensors"] == 4
    assert rec["parameters"] == 512 * 512 + 512 + 512 * 8 + 8


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="/proc/self/io counts the bytes read")
def test_the_strip_does_not_read_the_optimizer_state(store, tmp_path):
    """Weights 267,272 floats and AdamW 2 x 267,272: a weights-only load reads about a third of the shard file."""
    rec = sc.strip(store, 10, tmp_path / "s.safetensors", verify="none")
    weights = rec["parameters"] * 4
    shards = sum(f.stat().st_size for f in (store / COMMIT).glob("*.distcp"))
    assert shards > 2.5 * weights
    # read: the dcp metadata, the weight bytes, and the written file read back for its sha256 (2 x weights)
    assert rec["io"]["read_bytes"] < 0.8 * shards


def test_a_damaged_shard_is_refused_and_nothing_is_written(store, tmp_path):
    shard = next((store / COMMIT).glob("*.distcp"))
    data = bytearray(shard.read_bytes())
    data[len(data) // 2] ^= 0xFF
    shard.write_bytes(bytes(data))
    with pytest.raises(sc.StripError, match="damaged"):
        sc.strip(store, 10, tmp_path / "s.safetensors")
    assert not (tmp_path / "s.safetensors").exists() and not (tmp_path / "s.safetensors.json").exists()
    assert sc.main(["--run-dir", str(store), "--step", "10", "--out", str(tmp_path / "s.safetensors")]) == 1


def test_an_incomplete_commit_is_refused(store, tmp_path):
    (store / COMMIT / "MANIFEST.json").unlink()
    with pytest.raises(sc.StripError, match="incomplete"):
        sc.strip(store, 10, tmp_path / "s.safetensors")


def add_fingerprints(store):
    """MANIFEST.json fingerprints of the model.* tensors, as Team 7's save would keep them (proposal)."""
    import torch.distributed.checkpoint as dcp
    from ckpt.ckpt import fingerprints
    path = store / COMMIT / "MANIFEST.json"
    man = json.loads(path.read_text())
    want = {k[len("model."):]: torch.empty(v[0]) for k, v in man["keys"].items() if k.startswith("model.")}
    dcp.load({"model": want}, checkpoint_id=str(store / COMMIT))
    man["fingerprints"] = fingerprints({"model": want})
    path.write_text(json.dumps(man))
    return man


def model_byte(store, key):
    """The file and the offset of one byte inside the stored data of a model tensor."""
    import torch.distributed.checkpoint as dcp
    meta = dcp.FileSystemReader(str(store / COMMIT)).read_metadata()
    for index, info in meta.storage_data.items():
        if index.fqn == key:  # the middle of the item: the tensor's data, not the zip header or directory
            return store / COMMIT / info.relative_path, info.offset + info.length // 2
    raise KeyError(key)


def test_auto_uses_fingerprints_when_the_manifest_has_them(store, tmp_path):
    assert sc.strip(store, 10, tmp_path / "a.safetensors")["verify"] == "files"     # no fingerprints yet
    add_fingerprints(store)
    rec = sc.strip(store, 10, tmp_path / "b.safetensors")
    assert rec["verify"] == "fingerprints"
    from safetensors.torch import load_file
    a, b = load_file(str(tmp_path / "a.safetensors")), load_file(str(tmp_path / "b.safetensors"))
    assert all(torch.equal(a[k], b[k]) for k in a)


def test_fingerprints_catch_a_damaged_weight(store, tmp_path):
    add_fingerprints(store)
    shard, at = model_byte(store, "model.a.weight")
    data = bytearray(shard.read_bytes())
    data[at] ^= 0x10
    shard.write_bytes(bytes(data))
    with pytest.raises(sc.StripError, match="differ from their MANIFEST.json fingerprint"):
        sc.strip(store, 10, tmp_path / "s.safetensors", verify="fingerprints")
    assert not (tmp_path / "s.safetensors").exists()


def test_fingerprints_asked_for_but_missing_is_an_error(store, tmp_path):
    with pytest.raises(sc.StripError, match="no fingerprints"):
        sc.strip(store, 10, tmp_path / "s.safetensors", verify="fingerprints")


def test_a_shard_deleted_during_the_strip_is_a_clean_error(store, tmp_path):
    """Retention can delete a commit while it is read: a StripError, no traceback, nothing left behind."""
    next((store / COMMIT).glob("*.distcp")).unlink()
    for verify in ("files", "none"):
        with pytest.raises(sc.StripError):
            sc.strip(store, 10, tmp_path / "s.safetensors", verify=verify)
    assert sorted(p.name for p in tmp_path.iterdir() if "s.safetensors" in p.name) == []


def test_two_strips_of_one_commit_at_once_leave_a_matching_file_and_record(store, tmp_path):
    """Two processes strip the same commit to the same file at the same moment: each writes its own temporary files,
    and the file and the record that remain agree."""
    import subprocess
    out = tmp_path / "s.safetensors"
    cmd = [sys.executable, str(HERE.parent / "strip_ckpt.py"), "--run-dir", str(store), "--step", "10",
           "--out", str(out)]
    procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
    assert [p.wait(timeout=120) for p in procs] == [0, 0]
    rec = json.loads(out.with_name(out.name + ".json").read_text())
    assert rec["weights_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert sorted(p.name for p in tmp_path.iterdir() if p.name.startswith(".")) == []   # no temporary file left


def test_no_room_on_the_disk_is_refused_before_writing(store, tmp_path, monkeypatch):
    real = sc.shutil.disk_usage
    monkeypatch.setattr(sc.shutil, "disk_usage", lambda p: real(p)._replace(free=1000))
    with pytest.raises(sc.StripError, match="GB free"):
        sc.strip(store, 10, tmp_path / "s.safetensors")
    assert [p for p in tmp_path.iterdir() if "s.safetensors" in p.name] == []


FSDP = textwrap.dedent('''
    import json, os, socket, sys
    from pathlib import Path
    sys.path[:0] = sys.argv[2].split(os.pathsep)
    import torch, torch.distributed as dist, torch.multiprocessing as mp

    def run(rank, world, out, port):
        os.environ.update(MASTER_ADDR="127.0.0.1", MASTER_PORT=str(port), RANK=str(rank), WORLD_SIZE=str(world),
                          LOCAL_RANK=str(rank), V5_EVENTS_DIR=str(out / "events"))
        dist.init_process_group("gloo", rank=rank, world_size=world)
        from torch.distributed.fsdp import fully_shard
        from ckpt.ckpt import Checkpointer, fingerprints
        from trainer.tiny import SyntheticLoader
        torch.manual_seed(0)
        m = torch.nn.Sequential(torch.nn.Linear(512, 512), torch.nn.ReLU(), torch.nn.Linear(512, 8))
        m.register_buffer("lens", torch.arange(7, dtype=torch.int16))
        fully_shard(m)
        opt = torch.optim.AdamW(m.parameters(), lr=1e-3)
        m(torch.ones(2, 512)).sum().backward()
        opt.step()
        probe = lambda mm: float(mm(torch.ones(2, 512)).square().mean().detach())
        ck = Checkpointer("fsdp", str(out / f"local{rank}"), str(out / "store"), seed=0)
        assert ck.save(1, m, opt, SyntheticLoader(0, 2, rank, world), probe) and ck.wait()
        fp = fingerprints({"model": m.state_dict()})      # on the shards (collective), as Team 7's save makes them
        full = {k: (v.full_tensor() if hasattr(v, "full_tensor") else v) for k, v in m.state_dict().items()}
        if rank == 0:
            torch.save(full, out / "full.pt")
            (out / "fingerprints.json").write_text(json.dumps(fp))
        dist.barrier()
        dist.destroy_process_group()

    if __name__ == "__main__":
        out = Path(sys.argv[1])
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        mp.spawn(run, args=(2, out, port), nprocs=2)
''')


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="2 gloo processes; run on the Linux test image")
def test_a_commit_sharded_over_two_ranks_strips_to_the_full_tensors(tmp_path):
    """FSDP2 over 2 ranks (DTensor shards in 2 files, an int16 buffer): one process strips it to the full tensors, and
    fingerprints made on the shards match the ones made on the full tensors."""
    import subprocess
    from safetensors.torch import load_file
    script = tmp_path / "fsdp_save.py"
    script.write_text(FSDP)
    paths = os.pathsep.join(str(HERE.parents[2] / "07-infrastructure" / x) for x in ("", "support/simulation"))
    subprocess.run([sys.executable, str(script), str(tmp_path), paths], check=True, capture_output=True, timeout=300)
    run_dir = tmp_path / "store" / "fsdp"
    folder = next(run_dir.glob("main/step_*"))
    assert len(list(folder.glob("*.distcp"))) == 2
    man = json.loads((folder / "MANIFEST.json").read_text())
    assert man["world_size"] == 2
    full = torch.load(tmp_path / "full.pt")
    rec = sc.strip(run_dir, 1, tmp_path / "s.safetensors", verify="files")
    got = load_file(str(tmp_path / "s.safetensors"))
    assert set(got) == set(full) and all(torch.equal(got[k], full[k]) for k in full) and rec["tensors"] == 5
    man["fingerprints"] = json.loads((tmp_path / "fingerprints.json").read_text())
    (folder / "MANIFEST.json").write_text(json.dumps(man))
    rec = sc.strip(run_dir, 1, tmp_path / "h.safetensors", dtype="bfloat16")
    half = load_file(str(tmp_path / "h.safetensors"))
    assert rec["verify"] == "fingerprints" and half["lens"].dtype == torch.int16
    assert all(torch.equal(half[k], full[k].to(torch.bfloat16) if full[k].is_floating_point() else full[k])
               for k in full)


def test_bf16_halves_the_file_and_rounds_as_a_cast_does(store, tmp_path):
    from safetensors.torch import load_file
    full = sc.strip(store, 10, tmp_path / "f.safetensors")
    half = sc.strip(store, 10, tmp_path / "h.safetensors", dtype="bfloat16")             # converted by the load
    assert half["dtype"] == "bfloat16" and half["weights_bytes"] < 0.6 * full["weights_bytes"]
    add_fingerprints(store)
    half_fp = sc.strip(store, 10, tmp_path / "g.safetensors", dtype="bfloat16")          # converted after the check
    assert half_fp["verify"] == "fingerprints"
    f, h, g = (load_file(str(tmp_path / n)) for n in ("f.safetensors", "h.safetensors", "g.safetensors"))
    assert all(h[k].dtype == torch.bfloat16 and torch.equal(h[k], f[k].to(torch.bfloat16)) and torch.equal(h[k], g[k])
               for k in f)


def test_weights_score_the_same_as_the_export_and_check_the_probe(store, tmp_path, capsys):
    via_export = score(store, tmp_path)
    sc.strip(store, 10, tmp_path / "s.safetensors")
    capsys.readouterr()
    via_strip = score(store, tmp_path, "--weights", str(tmp_path / "s.safetensors"))
    assert via_strip["value"] == via_export["value"] and via_strip["model_revision"] == via_export["model_revision"]
    assert via_strip["checkpoint"] == via_export["checkpoint"]
    assert "probe loss bits equal the saved ones" in capsys.readouterr().out


def test_weights_converted_to_bf16_are_not_probe_compared(store, tmp_path, capsys):
    sc.strip(store, 10, tmp_path / "h.safetensors", dtype="bfloat16")
    capsys.readouterr()
    score(store, tmp_path, "--weights", str(tmp_path / "h.safetensors"))
    assert "probe not compared (the weights were converted to bfloat16)" in capsys.readouterr().out


def test_weights_of_another_commit_or_a_changed_file_are_refused(store, tmp_path):
    w = tmp_path / "s.safetensors"
    sc.strip(store, 10, w)
    rec_path = w.with_name(w.name + ".json")
    rec = json.loads(rec_path.read_text())
    rec_path.write_text(json.dumps(dict(rec, model_revision="ab" * 32)))
    with pytest.raises(SystemExit, match="is the strip of"):
        score(store, tmp_path, "--weights", str(w))
    rec_path.write_text(json.dumps(rec))
    data = bytearray(w.read_bytes())
    data[-1] ^= 0x01
    w.write_bytes(bytes(data))
    with pytest.raises(SystemExit, match="its record says"):
        score(store, tmp_path, "--weights", str(w))
    w.unlink()
    rec_path.unlink()
    sc.strip(store, 10, w)
    rec_path.unlink()                              # the record is written last: no record, no finished strip
    with pytest.raises(SystemExit, match="did not finish"):
        score(store, tmp_path, "--weights", str(w))


def test_weights_with_a_team5_run_is_an_error(tmp_path):
    with pytest.raises(SystemExit) as e:
        rl.main(["--team5-run", str(tmp_path), "--scorer", "no_such_module:make", "--weights", str(tmp_path / "w")])
    assert e.value.code == 2
