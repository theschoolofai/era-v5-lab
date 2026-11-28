#!/usr/bin/env python3
"""Strip a real Team 5 LanguageModel commit and check it against Team 7's export, the strict load and the probe.

In simple words: ``make_lab_store.py`` saves a real Team 5 ``LanguageModel`` (an arm YAML, the frozen p1536 tokenizer
and Team 4's byte table) through Team 7's Checkpointer. For every commit this script then checks that

1. ``strip_ckpt.py`` writes the same tensors as ``export_safetensors()``, bit for bit (keys, dtypes, values);
2. the strip loads strictly into a fresh Team 5 model (the scorer's ``factory()``), in the saved dtype and in bf16;
3. ``run_lab_ckpt.load_stripped()`` finds the probe loss bits equal to the saved ones (the commit is made on CPU);
4. tensors that share memory in the model (tied weights) are reported, with what the commit and the strip hold.

No benchmark item is read: equal tensors in the same model class give equal scores.

    python teams/09-evaluation/harness_lab/tests/check_strip_team5.py --arm teams/05-architecture/configs/arms/t2.yaml \\
        --tokenizer <p1536 tokenizer.json> --work <empty dir>

Exit 0 when every check passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path[:0] = [str(LAB)]
P1536 = "e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b"
TABLE = LAB.parents[1] / "04-ke2" / "results" / "tables" / "p1536-s0" / "raw_table_P32.npz"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], epilog=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--tokenizer", type=Path, required=True)
    ap.add_argument("--byte-table", type=Path, default=TABLE)
    ap.add_argument("--n-layer", type=int, help="a smaller model (the same tensor kinds per layer)")
    ap.add_argument("--commits", type=int, default=2)
    ap.add_argument("--work", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.work.exists() and any(a.work.iterdir()):
        ap.error(f"{a.work} is not empty")
    cmd = [sys.executable, str(HERE / "make_lab_store.py"), "--arm", str(a.arm), "--tokenizer", str(a.tokenizer),
           "--tokenizer-sha256", P1536, "--byte-table", str(a.byte_table), "--commits", str(a.commits), "--final",
           "--out", str(a.work)] + (["--n-layer", str(a.n_layer)] if a.n_layer else [])
    t0 = time.perf_counter()
    made = subprocess.run(cmd, capture_output=True, text=True)
    if made.returncode:
        print(f"make_lab_store.py exit {made.returncode}"
              + (" (killed by a signal: -9 is the out-of-memory killer)" if made.returncode < 0 else ""))
        print(made.stdout[-3000:], made.stderr[-3000:], sep="\n")
        return 1
    print(made.stdout.strip().splitlines()[0], f"(store made in {time.perf_counter() - t0:.1f} s)")

    import torch
    import run_lab_ckpt as rl
    import strip_ckpt as sc
    from ckpt.ckpt import export_safetensors
    from lm_eval_lab import build_model, load_model_config, probe_loss, week2
    from safetensors.torch import load_file

    m = load_model_config(a.work / "model.json")
    Artifacts, _ = week2()
    art = Artifacts(a.tokenizer, a.byte_table, expected_tokenizer_sha=P1536, expected_vocab=m["vocab_size"])

    class Scorer:  # the parts of the scorer contract that load_stripped uses
        def factory(self):
            return build_model(m, art)

        def probe(self, model):
            return probe_loss(model)

    scorer = Scorer()
    run_dir = a.work / "store" / "lab-store"
    ok = True

    def check(cond, text):
        nonlocal ok
        ok &= bool(cond)
        print(f"{'PASS' if cond else 'FAIL'} {text}")

    fresh = scorer.factory()
    sd = fresh.state_dict()
    by_ptr = {}
    for k, v in sd.items():
        by_ptr.setdefault(v.data_ptr(), []).append(k)
    tied = [ks for ks in by_ptr.values() if len(ks) > 1]
    print(f"model: {sum(p.numel() for p in fresh.parameters()):,} parameters, {len(sd)} state_dict tensors, "
          f"tied (shared memory): {tied or 'none'}")
    commits = [json.loads(x) for x in (run_dir / "commits.jsonl").read_text().splitlines() if x.strip()]
    for c in commits:
        step = c["step"]
        torch.use_deterministic_algorithms(True)
        torch.set_num_threads(1)
        t = time.perf_counter()
        exported = a.work / f"export-{step}.safetensors"
        export_safetensors(run_dir.as_posix(), scorer.factory, scorer.probe, str(exported), step=step)
        t_export = time.perf_counter() - t
        t = time.perf_counter()
        rec = sc.strip(run_dir, step, a.work / f"strip-{step}.safetensors")
        t_strip = time.perf_counter() - t
        e, s = load_file(str(exported)), load_file(str(a.work / f"strip-{step}.safetensors"))
        same = set(e) == set(s) and all(e[k].dtype == s[k].dtype and torch.equal(e[k], s[k]) for k in e)
        check(same, f"step {step}: strip == export, bit for bit ({len(s)} tensors; export {t_export:.1f} s, "
                    f"strip {t_strip:.1f} s with --verify {rec['verify']})")
        facts = rl.checkpoint_facts(run_dir, run_dir.as_posix(), rl.read_pointer(run_dir, step), None)
        try:
            model = rl.load_stripped(a.work / f"strip-{step}.safetensors", facts, scorer)
            check(True, f"step {step}: strict load into a fresh Team 5 model, probe checked (see the line above)")
        except SystemExit as err:
            check(False, f"step {step}: load_stripped refused: {err}")
            continue
        missing = sorted(set(sd) - set(s))
        check(not missing, f"step {step}: every state_dict key is in the strip"
                           + (f" (missing {missing[:3]})" if missing else ""))
        rec16 = sc.strip(run_dir, step, a.work / f"strip16-{step}.safetensors", dtype="bfloat16")
        m16 = scorer.factory()
        m16.load_state_dict(load_file(str(a.work / f"strip16-{step}.safetensors")), strict=True)
        check(rec16["weights_bytes"] < 0.6 * rec["weights_bytes"] or not any(
            v.dtype == torch.float32 for v in s.values()), f"step {step}: bf16 strip loads strictly "
                                                           f"({rec16['weights_bytes']:,} against {rec['weights_bytes']:,} bytes)")
        for ks in tied:
            in_strip = [k for k in ks if k in s]
            equal = len(in_strip) < 2 or all(torch.equal(s[in_strip[0]], s[k]) for k in in_strip[1:])
            loaded = model.state_dict()
            still_tied = len({loaded[k].data_ptr() for k in ks}) == 1
            check(equal and still_tied, f"step {step}: tied {ks}: in the strip {in_strip}, equal values {equal}, "
                                        f"still one tensor after the load {still_tied}")
    print(f"RESULT {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
