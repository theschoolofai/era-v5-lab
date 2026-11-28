#!/usr/bin/env python3
"""Measure Team 7's export_safetensors() against strip_ckpt.py on one commit with a real parameter layout.

In simple words: this builds a model with the parameter split of a recorded run (default: dry run 2, #869: 176,398,881
parameters, 165,740,544 of them trained by Muon with one buffer each, the rest by AdamW with two), takes one optimizer
step so the optimizer state exists, and saves it with Team 7's Checkpointer. One SGD-momentum optimizer keeps one
buffer for every parameter, so the commit is 42.6 MB (about 3%) smaller than dry run 2's would be (no second AdamW
buffer on 10.7M parameters). Then it runs, each in a fresh process:

- ``export``: Team 7's ``export_safetensors()`` exactly as ``run_lab_ckpt.py`` calls it (deterministic algorithms,
  one thread), with a probe of the same cost as ``lm_eval_lab.probe_loss`` (a forward pass over every weight for
  2 x 32 tokens);
- ``strip``: ``strip_ckpt.py`` with ``--verify files`` (and the variants in ``--variants``). For ``--verify
  fingerprints`` the build adds MANIFEST.json ``fingerprints`` for the ``model.*`` tensors, computed with Team 7's own
  ``fingerprints()``, as Team 7's save would keep them (``state_digest()`` already computes them).

For each it prints the wall time, the peak memory (RSS) and the bytes read and written (Linux), and checks that both
files hold the same tensors, bit for bit. ``--probe-device`` sets the device class of the saved probe bits: ``cpu``
(the export compares them) or a GPU name (a GPU-trained run: the export runs the probe but cannot compare).

    python teams/09-evaluation/harness_lab/tests/bench_strip.py --work /tmp/bench --scale 1
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
TEAM07 = LAB.parents[1] / "07-infrastructure"
PROBE_TOKENS = 64  # lm_eval_lab.PROBE_SHAPE = (2, 32)
DR2 = {"muon": 165_740_544, "adamw": 10_658_337}


def layout(scale: float) -> dict:
    """The Muon part as 512 x 2048 matrices, the AdamW part as 32 norm vectors of 512 and one embedding-like table, so
    a commit has about as many large tensors as a model (190 at scale 1). The real tensor count is not in #869."""
    muon, adamw = int(DR2["muon"] * scale), int(DR2["adamw"] * scale)
    full, rest = divmod(muon, 512 * 2048)
    return {"matrices": full, "matrix_tail": rest, "vectors": 32, "table": adamw - 32 * 512}


MODEL_DEF = r'''
import json
import torch

def make(L):
    """The parameter split of the recorded run (see layout())."""
    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            torch.manual_seed(0)
            mats = [torch.nn.Parameter(torch.randn(512, 2048) * 0.02) for _ in range(L["matrices"])]
            if L["matrix_tail"]:
                mats.append(torch.nn.Parameter(torch.randn(L["matrix_tail"] // 512, 512) * 0.02))
            self.mats = torch.nn.ParameterList(mats)
            vecs = [torch.nn.Parameter(torch.ones(512)) for _ in range(L["vectors"])]
            vecs.append(torch.nn.Parameter(torch.randn(L["table"]) * 0.02))   # the embedding-like table
            self.vecs = torch.nn.ParameterList(vecs)
    return Model


def probe(m):
    """Every weight once for 64 tokens: the cost of lm_eval_lab.probe_loss (PROBE_SHAPE (2, 32))."""
    g = torch.Generator().manual_seed(1234)
    with torch.no_grad():
        s = torch.zeros((), dtype=torch.float64)
        for w in m.mats:
            s = s + (torch.randn(64, w.shape[0], generator=g) @ w).double().square().mean()
        for v in m.vecs:
            s = s + v.double().mean()
    return float(s)
'''

BUILD = r'''
import json, os, sys, time
from pathlib import Path
sys.path[:0] = [sys.argv[1], sys.argv[1] + "/support/simulation", sys.argv[5]]
import torch
from ckpt.ckpt import Checkpointer
from trainer.tiny import SyntheticLoader
import model_def
L = json.loads(sys.argv[2]); out = Path(sys.argv[3]); probe_dev = sys.argv[4]
os.environ.setdefault("RANK", "0"); os.environ.setdefault("WORLD_SIZE", "1"); os.environ.setdefault("LOCAL_RANK", "0")
m = model_def.make(L)()
n = sum(p.numel() for p in m.parameters())
opt = torch.optim.SGD(m.parameters(), lr=1e-3, momentum=0.9)   # one buffer per weight, as Muon keeps
for p in m.parameters():
    p.grad = torch.randn_like(p) * 1e-3
opt.step()
torch.use_deterministic_algorithms(True); torch.set_num_threads(1)
ck = Checkpointer("bench", str(out / "local"), str(out / "store"), seed=0)
t0 = time.perf_counter()
assert ck.save(1, m, opt, SyntheticLoader(0, 2, 0, 1), model_def.probe, reason="interval") and ck.wait()
man_path = next((out / "store" / "bench").glob("main/step_*/MANIFEST.json"))
man = json.loads(man_path.read_text())
if probe_dev != "cpu":  # a GPU-trained run: the saved bits are for a GPU, so a CPU export cannot compare them
    man["probe_loss"] = {probe_dev: man["probe_loss"]["cpu"]}
from ckpt.ckpt import fingerprints  # what Team 7's save would keep: state_digest() computes these at every save
man["fingerprints"] = fingerprints({"model": m.state_dict()})
man_path.write_text(json.dumps(man))
print(json.dumps({"parameters": n, "save_s": round(time.perf_counter() - t0, 2),
                  "commit_bytes": sum(f.stat().st_size for f in man_path.parent.iterdir() if f.is_file())}))
'''

EXPORT = r'''
import json, resource, sys, time
from pathlib import Path
sys.path[:0] = [sys.argv[1], sys.argv[1] + "/support/simulation", sys.argv[5]]
import torch
from ckpt.ckpt import export_safetensors
import model_def
L = json.loads(sys.argv[4])
def io():
    try:
        r = dict(x.split(": ") for x in Path("/proc/self/io").read_text().splitlines())
        return int(r["rchar"]), int(r["wchar"])
    except OSError:
        return 0, 0
r0, w0 = io(); t0 = time.perf_counter()
torch.use_deterministic_algorithms(True); torch.set_num_threads(1)   # as run_lab_ckpt.py around the export
export_safetensors(sys.argv[2], model_def.make(L), model_def.probe, sys.argv[3])
t = time.perf_counter() - t0; r1, w1 = io()
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
print(json.dumps({"seconds": round(t, 2), "peak_rss_bytes": rss, "read_bytes": r1 - r0, "written_bytes": w1 - w0}))
'''


def run(cmd: list[str]) -> dict:
    """Run one measured step in a fresh process; its last stdout line is its JSON result."""
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd[:3])} ...\n{p.stdout[-2000:]}\n{p.stderr[-3000:]}")
    return json.loads(p.stdout.strip().splitlines()[-1])


def same_tensors(a: Path, b: Path) -> bool:
    from safetensors.torch import load_file
    import torch
    x, y = load_file(str(a)), load_file(str(b))
    return set(x) == set(y) and all(x[k].dtype == y[k].dtype and torch.equal(x[k], y[k]) for k in x)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", type=Path, required=True, help="an empty folder (the commit and the files go here)")
    ap.add_argument("--scale", type=float, default=1.0, help="model size as a multiple of dry run 2 (1 = 176M)")
    ap.add_argument("--probe-device", default="cuda:NVIDIA H100 80GB HBM3",
                    help="device class of the saved probe bits: cpu, or a GPU name (default: a GPU-trained run)")
    ap.add_argument("--variants", default="files,fingerprints,none,files-bf16",
                    help="strip variants: files (sha256 of every file), fingerprints (each weight against MANIFEST.json "
                         "fingerprints, added by the build as Team 7's save would keep them), none, files-bf16")
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument("--group-mb", type=int, help="passed to strip_ckpt.py --group-mb (the streaming strip only)")
    ap.add_argument("--strip", type=Path, default=LAB / "strip_ckpt.py",
                    help="the strip_ckpt.py to measure (an older version too, for a before and after)")
    a = ap.parse_args(argv)
    a.work.mkdir(parents=True, exist_ok=True)
    if any(a.work.iterdir()):
        ap.error(f"{a.work} is not empty")
    code = a.work / "code"
    code.mkdir()
    (code / "model_def.py").write_text(MODEL_DEF)
    build_py, export_py = code / "build.py", code / "export.py"
    build_py.write_text(BUILD)
    export_py.write_text(EXPORT)
    lay = layout(a.scale)
    built = run([sys.executable, str(build_py), str(TEAM07), json.dumps(lay), str(a.work), a.probe_device, str(code)])
    run_dir = a.work / "store" / "bench"
    print(f"commit: {built['parameters']:,} parameters, {built['commit_bytes'] / 1e6:,.1f} MB on disk "
          f"(saved in {built['save_s']} s); probe bits for {a.probe_device!r}", flush=True)
    rows = []
    ex = run([sys.executable, str(export_py), str(TEAM07), str(run_dir), str(a.work / "export.safetensors"),
              json.dumps(lay), str(code)])
    rows.append(("export_safetensors (as run_lab_ckpt.py)", ex))
    for v in [x for x in a.variants.split(",") if x]:
        verify, _, dt = v.partition("-")
        out = a.work / f"strip-{v}.safetensors"
        cmd = [sys.executable, str(a.strip), "--run-dir", str(run_dir), "--out", str(out), "--verify",
               verify, "--jobs", str(a.jobs)] + (["--dtype", "bfloat16"] if dt == "bf16" else []) + \
            (["--group-mb", str(a.group_mb)] if a.group_mb else [])
        subprocess.run(cmd, check=True, capture_output=True)
        rec = json.loads(out.with_name(out.name + ".json").read_text())
        rows.append((f"strip --verify {verify}" + (" --dtype bfloat16" if dt else ""),
                     {"seconds": rec["seconds"]["total"], "peak_rss_bytes": rec["peak_rss_bytes"],
                      "read_bytes": rec.get("io", {}).get("read_bytes", 0),
                      "written_bytes": rec.get("io", {}).get("written_bytes", 0), "file": out}))
    print("\n| Path | Wall time | Peak RSS | Read | Written |\n|---|---:|---:|---:|---:|")
    for name, r in rows:
        print(f"| {name} | {r['seconds']:.2f} s | {r['peak_rss_bytes'] / 1e6:,.0f} MB | "
              f"{r['read_bytes'] / 1e6:,.0f} MB | "
              f"{r['written_bytes'] / 1e6:,.0f} MB |")
    same = same_tensors(a.work / "export.safetensors", a.work / "strip-files.safetensors") \
        if "files" in a.variants.split(",") else None
    print(f"\nstrip --verify files gives the same tensors as export_safetensors, bit for bit: {same}")
    return 0 if same in (True, None) else 1


if __name__ == "__main__":
    sys.exit(main())
