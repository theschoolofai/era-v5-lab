#!/usr/bin/env python3
"""Strip one Team 7 store commit to a weights-only safetensors file, once, for every scorer that reads it.

In simple words: Team 7's ``export_safetensors()`` copies the whole commit (weights and optimizer state) to a local
folder, builds the model twice on CPU, and runs the probe batch on CPU even when the saved probe bits are for a GPU and
so are never compared. This script reads the commit in place and loads only the ``model.*`` tensors, in their saved
dtype (or bf16 with ``--dtype bf16``), with no model class and no second copy. It writes one file and a small JSON
record beside it. ``run_lab_ckpt.py --weights <file>`` scores that file, and Team 12's ``run_loop.py --weights`` can
quantize the same file, so a commit is converted once and not once per reader.

    python teams/09-evaluation/harness_lab/strip_ckpt.py --run-dir <store>/<run> --step 1221 \\
        --out <dir>/step_1221.safetensors

The checks it keeps:
- the pointer is the ``commits.jsonl`` line of the step (or ``latest.json``), never a directory listing, as in
  ``run_lab_ckpt.py``;
- the weights are checked before they are written. ``--verify files``: every file the commit's MANIFEST.json lists is
  hashed (sha256) and compared, as ``export_safetensors()`` does while it copies; files are hashed in parallel
  (``--jobs``) and nothing is copied, but the optimizer bytes are read too. ``--verify fingerprints``: each loaded
  ``model.*`` tensor is checked against MANIFEST.json ``fingerprints`` (Team 7's logical fingerprints, the ones
  ``state_digest()`` already computes at every save), so only the weight bytes are read. ``--verify auto`` (default)
  uses fingerprints when MANIFEST.json has them and files otherwise;
- the ``model.*`` keys, shapes and dtypes must equal MANIFEST.json ``keys``, and dcp's own metadata must hold them;
- the written file is read back and hashed; its sha256 and the commit's ``model_revision`` (the sha256 of
  MANIFEST.json) go into the record, so a reader can check that the file is this commit's weights.

The probe-loss check is not done here: it needs the model class. ``run_lab_ckpt.py --weights`` runs it when the saved
bits are for the device class it scores on, and says "not compared" otherwise.

Exit codes: 0 written, 1 a check failed (nothing written), 2 bad arguments.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import resource
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEAM07 = HERE.parents[1] / "07-infrastructure"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TEAM07))

RECORD_SCHEMA = "strip_v1"
MANIFEST = "MANIFEST.json"
MODEL = "model."


class StripError(Exception):
    """A check failed: the commit is damaged, incomplete, or not the one asked for."""


def sha256_file(path: Path, block: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block):
            h.update(chunk)  # hashlib releases the GIL for large updates, so threads hash files in parallel
    return h.hexdigest()


def io_counters() -> dict:
    """Bytes this process read and wrote through system calls (Linux /proc/self/io), or {} elsewhere."""
    try:
        rows = dict(line.split(": ") for line in Path("/proc/self/io").read_text().splitlines())
        return {"read_bytes": int(rows["rchar"]), "written_bytes": int(rows["wchar"])}
    except (OSError, KeyError, ValueError):
        return {}


def peak_rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024  # macOS reports bytes, Linux kilobytes


def torch_dtype(name: str):
    import torch
    d = getattr(torch, name.removeprefix("torch."), None)
    if not isinstance(d, torch.dtype):
        raise StripError(f"unknown dtype {name!r} in MANIFEST.json keys")
    return d


def verify_files(folder: Path, files: dict, jobs: int) -> None:
    """sha256 of every file MANIFEST.json lists, in parallel; the first mismatch stops the strip."""
    def one(item):
        name, spec = item
        path = folder / name
        if not path.is_file():
            raise StripError(f"{path} is missing")
        got = sha256_file(path)
        if got != spec["sha256"]:
            raise StripError(f"{path} is damaged: sha256 {got[:16]}, MANIFEST.json says {spec['sha256'][:16]}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        for f in [pool.submit(one, item) for item in sorted(files.items())]:
            f.result()


def strip(run_dir: Path, step: int | None, out: Path, dtype: str = "saved", verify: str = "auto",
          jobs: int = 8) -> dict:
    """Write the weights of one commit to ``out`` and the record to ``out`` + ``.json``. Returns the record.

    A file of the commit that disappears while it is read (retention deleted the commit) is a StripError, and so is a
    disk without room for the file: nothing is left behind in either case."""
    from torch.distributed.checkpoint.api import CheckpointException  # dcp wraps a missing or unreadable file in it

    tmps = [out.with_name(f".{out.name}.{os.getpid()}.tmp"), out.with_name(f".{out.name}.json.{os.getpid()}.tmp")]
    try:
        return _strip(run_dir, step, out, dtype, verify, jobs, tmps)
    except (OSError, CheckpointException) as e:
        raise StripError(f"reading or writing failed (was the commit deleted by retention?): {e}") from None
    except json.JSONDecodeError as e:
        raise StripError(f"MANIFEST.json of the commit is not valid JSON: {e}") from None
    finally:
        for t in tmps:
            t.unlink(missing_ok=True)


def _strip(run_dir, step, out, dtype, verify, jobs, tmps) -> dict:
    import torch
    import torch.distributed.checkpoint as dcp
    from safetensors.torch import save_file
    from run_lab_ckpt import read_pointer

    t0 = time.perf_counter()
    io0 = io_counters()
    pointer = read_pointer(run_dir, step)
    folder = run_dir / pointer["path"]
    raw = (folder / MANIFEST).read_bytes() if (folder / MANIFEST).exists() else None
    if raw is None:
        raise StripError(f"{folder / MANIFEST} not found: the commit is incomplete (MANIFEST.json is written last)")
    man = json.loads(raw)
    if man.get("backend") == "deepspeed":
        raise StripError("a DeepSpeed commit: use Team 7's export_safetensors (ckpt.ds_ckpt.export_ds)")
    want = {k: v for k, v in man["keys"].items() if k.startswith(MODEL)}
    if not want:
        raise StripError("MANIFEST.json keys has no model.* tensor")
    saved_fp = {k: v for k, v in (man.get("fingerprints") or {}).items() if k.startswith(MODEL)}
    if verify == "auto":
        verify = "fingerprints" if set(saved_fp) == set(want) else "files"
    if verify == "fingerprints" and set(saved_fp) != set(want):
        raise StripError("--verify fingerprints: MANIFEST.json has no fingerprints for every model.* key")
    t_verify = time.perf_counter()
    if verify == "files":
        verify_files(folder, man["files"], jobs)
    t_verify = time.perf_counter() - t_verify

    t_load = time.perf_counter()
    meta = dcp.FileSystemReader(str(folder)).read_metadata().state_dict_metadata
    missing = sorted(k for k in want if k not in meta)
    if missing:
        raise StripError(f"dcp metadata lacks {len(missing)} model key(s), first {missing[:3]}")
    # A conversion is done by the load itself (dcp copies each stored tensor into its target), so the whole model is
    # never held twice. Fingerprints are made on the saved bits, so with them the conversion comes after the check.
    load_as = torch_dtype(dtype) if dtype != "saved" and verify != "fingerprints" else None
    target = {}
    for key, (shape, dt) in want.items():
        if list(meta[key].size) != list(shape):
            raise StripError(f"{key}: dcp shape {list(meta[key].size)}, MANIFEST.json {shape}")
        saved_dt = torch_dtype(dt)
        target[key[len(MODEL):]] = torch.empty(shape, dtype=load_as if load_as and saved_dt.is_floating_point
                                               else saved_dt)
    state = {"model": target}
    dcp.load(state, checkpoint_id=str(folder))  # loads only the keys asked for; the optimizer state is not loaded
    weights = state["model"]
    t_load = time.perf_counter() - t_load
    if verify == "fingerprints":
        from ckpt.ckpt import fingerprints
        t_verify = time.perf_counter()
        got = fingerprints(state)                  # the same function Team 7 saves with, on the loaded tensors
        bad = sorted(k for k in want if got.get(k) != saved_fp[k])
        if bad:
            raise StripError(f"{len(bad)} model tensor(s) differ from their MANIFEST.json fingerprint, first {bad[:3]}")
        t_verify = time.perf_counter() - t_verify
        if dtype != "saved":
            to = torch_dtype(dtype)
            for k in list(weights):                # one tensor at a time, so the two dtypes overlap by one tensor only
                if weights[k].is_floating_point():
                    weights[k] = weights[k].to(to)

    t_write = time.perf_counter()
    out.parent.mkdir(parents=True, exist_ok=True)
    need = sum(v.numel() * v.element_size() for v in weights.values())
    free = shutil.disk_usage(out.parent).free
    if free < need * 1.05 + (64 << 20):
        raise StripError(f"{out.parent} has {free / 1e9:.1f} GB free, the file needs {need / 1e9:.1f} GB")
    tmp = tmps[0]
    save_file({k: v.contiguous() for k, v in weights.items()}, str(tmp),
              metadata={"run_id": man["run_id"], "step": str(man["step"]), "path": pointer["path"],
                        "model_revision": hashlib.sha256(raw).hexdigest(), "dtype": dtype})
    weights_sha = sha256_file(tmp)
    os.replace(tmp, out)
    t_write = time.perf_counter() - t_write

    io1 = io_counters()
    record = {
        "schema": RECORD_SCHEMA,
        "run_dir": run_dir.as_posix(),
        "path": pointer["path"],
        "step": man["step"],
        "model_revision": hashlib.sha256(raw).hexdigest(),
        "weights": out.name,
        "weights_sha256": weights_sha,
        "weights_bytes": out.stat().st_size,
        "dtype": dtype,
        "tensors": len(weights),
        "parameters": sum(v.numel() for v in weights.values()),
        "commit_bytes": sum((folder / name).stat().st_size for name in man["files"]),
        "probe_loss": man.get("probe_loss") or {},
        "verify": verify,
        "seconds": {"verify": round(t_verify, 3), "load": round(t_load, 3), "write": round(t_write, 3),
                    "total": round(time.perf_counter() - t0, 3)},
        "peak_rss_bytes": peak_rss_bytes(),
    }
    if io0 and io1:
        record["io"] = {k: io1[k] - io0[k] for k in io0}
    tmp_rec = tmps[1]
    tmp_rec.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp_rec, out.with_name(out.name + ".json"))  # written last: a record means the file is complete
    return record


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    ap.add_argument("--run-dir", type=Path, required=True, help="<remote_root>/<run_id> on a local or mounted path")
    ap.add_argument("--step", type=int, help="the commit of this step (default: the one latest.json names)")
    ap.add_argument("--out", type=Path, required=True, help="the .safetensors file to write (record: <out>.json)")
    ap.add_argument("--dtype", default="saved", choices=["saved", "bfloat16", "float32"],
                    help="saved: as in the commit (the scores do not change); bfloat16 halves the file of an fp32 run "
                         "(no float16: fp32 weights above 65,504 would become inf)")
    ap.add_argument("--verify", default="auto", choices=["auto", "fingerprints", "files", "none"],
                    help="fingerprints: each weight against MANIFEST.json fingerprints (reads the weights only); "
                         "files: sha256 of every file MANIFEST.json lists (as export_safetensors); auto: fingerprints "
                         "if MANIFEST.json has them, else files")
    ap.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1), help="files hashed in parallel")
    a = ap.parse_args(argv)
    try:
        rec = strip(a.run_dir.resolve(), a.step, a.out.resolve(), a.dtype, a.verify, a.jobs)
    except StripError as e:
        print(f"strip_ckpt: {e}", file=sys.stderr)
        return 1
    s = rec["seconds"]
    print(f"stripped step {rec['step']} ({rec['path']}): {rec['tensors']} tensors, {rec['parameters']:,} parameters, "
          f"{rec['weights_bytes']:,} bytes ({rec['dtype']}) -> {a.out}")
    print(f"weights sha256 {rec['weights_sha256']}; model_revision {rec['model_revision']}")
    io = rec.get("io")
    moved = f"; read {io['read_bytes'] / 1e6:.0f} MB, written {io['written_bytes'] / 1e6:.0f} MB" if io else ""
    print(f"TIME verify {s['verify']:.2f} s, load {s['load']:.2f} s, write {s['write']:.2f} s, "
          f"total {s['total']:.2f} s; peak RSS {rec['peak_rss_bytes'] / 1e6:.0f} MB{moved}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
