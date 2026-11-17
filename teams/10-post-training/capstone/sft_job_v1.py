"""G10 first real SFT job on a Team 5 run folder: OCR-2 code rows that fit the model's context, full traces vs short answers.

    python capstone/sft_job_v1.py --g5-root <lab checkout> --run-folder <dir with manifest.json/checkpoint.pt/summary.json> \
        --tokenizer tokenizer.json --byte-table raw_table_P32.npz --heldout H.jsonl --heldout-sources S.jsonl \
        --packs <shard-00000>/pack.firewalled.jsonl ... --rl-tasks cc.jsonl --rl-ids capstone/probe_rl_easy_ids.txt \
        --device cuda --out out/

One question: on this checkpoint, which shape of the same code SFT rows gives more RL-usable output within the model's
context, full reasoning traces (A2) or the same rows with the reasoning deleted (A4, the E9 short-answer rule), and at
what forgetting cost?

Steps (each writes out/<step>.json; summary.json last; exit 1 if any step failed):
  pins        tokenizer sha256 and byte-table content hash against the run manifest (day_one_probe.check_pins); a
              mismatch stops the job before any rows are built
  inputs      capstone/sft_slice_v1.py: firewalled pack shards (sha256-checked against the committed firewall record),
              rows <= the model's block size, re-tokenised and checked against the pack ids, dev split by statement,
              A2 and A4 forms of the same rows. Rows live in out/_inputs/ and are deleted at exit
  sft_a2      capstone/sft_g5.py on the A2 rows: base evaluation first (dev NLL, forgetting bpb on the run's held-out,
              greedy format screen on dev prompts, RL screen k samples per easy prompt), then training, then the same
              evaluation; mask, step-1 writeback, frozen-weight and reload checks
  sft_a4      the same on the A4 rows, run for exactly the optimizer steps sft_a2 completed (so a training-time cap
              cannot make the arms unequal) and with --no-before (the base was measured in sft_a2)
  compare     per arm: change in forgetting bpb, format validity, closed turns, code-fence share, programs that run,
              pass rate and mixed groups, with the decision rule of the job request applied
Outputs are aggregates only: each arm's weights and generations are deleted after its reload check (day_one_probe
run_sft_arm), the rows at exit. Network: none. Writes only to --out. Resumable state is not saved (see the request).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEAM10 = HERE.parent
sys.path.insert(0, str(TEAM10 / "rl-loop"))
sys.path.insert(0, str(HERE))

import day_one_probe as probe  # noqa: E402

FORGET_LIMIT_BPB = 0.05  # the team's forgetting limit (E9 RESULTS, PREREG)
MIXED_MIN = 2            # decision rule: an arm "gives RL signal" with at least this many mixed groups


def arm_metrics(rep: dict, before: dict | None) -> dict:
    """Deltas and RL-usable counts from one arm's sft_report-derived result (run_sft_arm output)."""
    after = rep.get("after") or {}
    out: dict = {"steps": len(rep.get("log") or []) or None, "stopped_early": rep.get("stopped_early"),
                 "train_seconds": rep.get("train_seconds")}
    if before and before.get("forgetting") and after.get("forgetting"):
        b, a = before["forgetting"], after["forgetting"]
        out["forgetting_delta_bpb"] = a["val/bpb"] - b["val/bpb"] if "val/bpb" in a and "val/bpb" in b else None
        out["forgetting_delta_by_group"] = {k.split("/")[-1]: a[k] - b[k] for k in a
                                            if k.startswith("val/groups/") and k in b}
    g = after.get("generation") or {}
    out.update({k: g.get(k) for k in ("format_validity", "closed_im_end", "hit_budget", "mean_gen_tokens")})
    rl = after.get("rl_screen")
    if rl:
        n = max(rl["prompts"] * rl["k"], 1)
        reasons = rl.get("reasons", {})
        runs = reasons.get("pass", 0) + reasons.get("wrong answer on a test", 0)
        out.update({"rl_prompts": rl["prompts"], "rl_pass_rate": rl["pass_rate"], "rl_mixed_groups": rl["groups"]["mixed"],
                    "rl_code_fence_share": rl["samples_with_code_fence"] / n, "rl_runs_share": runs / n,
                    "rl_skipped_too_long": rl["skipped_too_long"]})
    return out


def decide(a2: dict, a4: dict) -> dict:
    """The request's decision rule, applied mechanically; the reading stays with the team."""
    def ok(m):
        d = m.get("forgetting_delta_bpb")
        return d is not None and d <= FORGET_LIMIT_BPB
    eligible = {k: m for k, m in (("A2", a2), ("A4", a4)) if ok(m)}
    if not eligible:
        return {"verdict": "neither arm within the forgetting limit", "default_shape": None}
    best = max(eligible, key=lambda k: (eligible[k].get("rl_mixed_groups") or 0, eligible[k].get("rl_runs_share") or 0))
    mixed = eligible[best].get("rl_mixed_groups") or 0
    return {"verdict": ("RL signal" if mixed >= MIXED_MIN else "no RL signal at this size"), "default_shape": best,
            "rule": f"within +{FORGET_LIMIT_BPB} bpb forgetting; more mixed groups, then more running programs; "
                    f"'RL signal' needs >= {MIXED_MIN} mixed groups"}


def sft_cmd(a, cfg: Path, rows: Path, dev: Path, arm_out: Path, steps: int, no_before: bool) -> list[str]:
    method = (["--method", "full", "--lr", str(a.lr)] if a.method == "full" else
              ["--method", "lora", "--lr", str(a.lr), "--marker-rows", "--wd", "0", "--marker-lr", str(a.marker_lr)])
    return [sys.executable, str(HERE / "sft_g5.py"), "--adapter-config", str(cfg), "--train", str(rows),
            "--eval", str(dev), *method, "--steps", str(steps), "--batch", str(a.batch),
            "--max-train-seconds", str(a.max_train_seconds), "--device", a.device, "--seed", str(a.seed),
            "--gen-limit", str(a.gen_limit), "--gen-max-new", str(a.gen_max_new), "--heldout", str(a.heldout),
            *(["--heldout-sources", str(a.heldout_sources)] if a.heldout_sources else []),
            *(["--rl-tasks", str(a.rl_tasks), "--rl-ids", str(a.rl_ids), "--rl-max-new", str(a.rl_max_new),
               "--rl-limit", str(a.rl_limit), "--rl-k", str(a.rl_k)] if a.rl_tasks and a.rl_ids else []),
            *(["--no-before"] if no_before else []), "--out", str(arm_out)]


def run_arm(out: Path, arm: str, cmd: list[str]) -> dict:
    """day_one_probe.run_sft_arm (weights and generations removed even on failure) plus the optimizer steps done."""
    res = probe.run_sft_arm(out, arm, cmd)
    res["steps_completed"] = len(json.loads((out / f"sft_{arm}" / "sft_report.json").read_text()).get("log", []))
    return res


def run(a, out: Path) -> int:
    results = {"pins": probe.step(out, "pins", lambda: probe.check_pins(a.run_folder, a.tokenizer, a.byte_table))}
    if not results["pins"]["ok"]:
        return probe.finish(out, results)
    from make_adapter_config import write_config  # noqa: PLC0415
    cfg = write_config(out / "adapter.yaml", a.g5_root, a.run_folder, a.tokenizer, a.byte_table, TEAM10, a.origin,
                       not a.no_git)
    inp = out / "_inputs"

    def inputs():
        import sft_slice_v1  # noqa: PLC0415
        return sft_slice_v1.build(a.packs, a.tokenizer, a.byte_table, a.max_tokens, inp, a.dev_rows,
                                  check_hashes=not a.no_pack_check)
    results["inputs"] = probe.step(out, "inputs", inputs)
    if not results["inputs"]["ok"]:
        return probe.finish(out, results)
    dev = inp / "dev.jsonl"
    results["sft_a2"] = probe.step(out, "sft_a2", lambda: run_arm(
        out, "a2", sft_cmd(a, cfg, inp / "a2_train.jsonl", dev, out / "sft_a2", a.steps, False)))
    a2 = results["sft_a2"]
    steps_a4 = a2.get("steps_completed") or a.steps
    before = a2.get("before") if a2["ok"] else None
    results["sft_a4"] = probe.step(out, "sft_a4", lambda: run_arm(
        out, "a4", sft_cmd(a, cfg, inp / "a4_train.jsonl", dev, out / "sft_a4", steps_a4, before is not None)))

    def compare():
        m = {}
        for arm in ("a2", "a4"):
            r = results[f"sft_{arm}"]
            if r["ok"]:
                rep = json.loads((out / f"sft_{arm}" / "sft_report.json").read_text())
                m[arm.upper()] = arm_metrics(rep, before or rep.get("before"))
        if len(m) < 2:
            raise RuntimeError(f"only {sorted(m)} finished: no comparison")
        return {"arms": m, "steps_matched": m["A2"]["steps"] == m["A4"]["steps"], "decision": decide(m["A2"], m["A4"]),
                "base": {k: (before or {}).get(k) for k in ("forgetting", "generation", "rl_screen")}}
    results["compare"] = probe.step(out, "compare", compare)
    return probe.finish(out, results)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--g5-root", type=Path, required=True)
    ap.add_argument("--run-folder", type=Path, required=True)
    ap.add_argument("--tokenizer", type=Path, required=True)
    ap.add_argument("--byte-table", type=Path, required=True)
    ap.add_argument("--heldout", type=Path, required=True)
    ap.add_argument("--heldout-sources", type=Path)
    ap.add_argument("--packs", type=Path, nargs="+", required=True, help="firewalled OCR-2 pack shards (sha256-checked)")
    ap.add_argument("--no-pack-check", action="store_true", help="tests only: accept packs not in the firewall record")
    ap.add_argument("--max-tokens", type=int, default=2048, help="row length limit (dropped, never cut); = block size")
    ap.add_argument("--dev-rows", type=int, default=256)
    ap.add_argument("--rl-tasks", type=Path)
    ap.add_argument("--rl-ids", type=Path)
    ap.add_argument("--rl-k", type=int, default=8)
    ap.add_argument("--rl-max-new", type=int, default=1536)
    ap.add_argument("--rl-limit", type=int, default=48)
    ap.add_argument("--method", choices=("full", "lora_markers"), default="full",
                    help="lora_markers = LoRA plus the nine marker rows of the untied output head")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--marker-lr", type=float, default=1e-3)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--max-train-seconds", type=float, default=1200.0, help="training cap of the A2 arm")
    ap.add_argument("--gen-limit", type=int, default=32)
    ap.add_argument("--gen-max-new", type=int, default=1536)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--origin", default="g10_rehearsal", choices=("g10_rehearsal", "g5_delivery"))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", type=Path, required=True)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    a = parse_args(argv)
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    try:
        return run(a, out)
    finally:
        shutil.rmtree(out / "_inputs", ignore_errors=True)  # built rows never leave the job


if __name__ == "__main__":
    raise SystemExit(main())
