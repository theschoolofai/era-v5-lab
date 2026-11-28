"""Periodic check of the rollout copy on Team 9's mini-benchmark (rl/fast_rollouts_v1.md section 3).

The trainer never runs the benchmark: the lab's evaluation firewall keeps benchmark items out of training jobs. Every
`every` steps it writes the weights, a separate evaluation job (Team 9's scorer) writes score files beside them, and the
trainer reads only those score files.

    <dir>/check.json                                                          the run it belongs to and its settings
    <dir>/step_000010/learner.safetensors, rollout.safetensors, model.json    written by the trainer
    <dir>/step_000010/request.json                                            written last: the folder is ready to score
    <dir>/step_000010/learner.score.json, rollout.score.json                  written by minibench_lab.py --out
    <dir>/step_000010/verdict.json                                            written by the trainer or by `judge`

    train.rollout_check: {dir: <folder>, every: 10, action: report | stop, control: <check folder of the bf16 run>,
                          min_bpb: 0.01, max_pending: 3}

Rule: Team 9's paired comparison (minibench_compare.py, lab PR 929), candidate minus baseline, on the tasks its card lets
decide (MMLU, MILU, arithmetic). A task is worse when the 95% interval of its gold bits-per-byte change lies above zero, or
that of its accuracy change lies below zero (about two standard errors of the paired difference). A bits-per-byte rise
below `min_bpb` does not count: the interval also excludes zero for tiny shifts, such as the same weights scored on two
devices. Held-out bits per byte has no interval there, so it is reported and never decides. Diagnostic tasks are neither
judged nor copied. The two score files of a step must come from the same device, dtype and hardware.
Baseline: the control run's rollout copy at the same step when `control` is set (the bf16 control arm; only the rollout
copy is written then), otherwise this run's learner at the same step (the effect of the quantized copy alone).

A weights file is removed once its score has gone into a verdict; with `control`, as soon as its matching score arrives, so
that a step the control run never exported cannot hold disk. Without `control` both files of a step need a score, and the
weights stay while the two cannot be compared. Scores of Team 9's smoke profile (execution evidence only) never decide. While
`max_pending` steps still hold weights, no further step is exported (the last step and a stopping step always are).

    python rl-loop/rollout_check.py judge --check-dir <dir> [--control <dir>]    # for scores that arrived after the run
    python rl-loop/rollout_check.py files <baseline.score.json> <candidate.score.json>
Exit codes: 0 all ok, 3 scores still missing or unusable, 4 at least one check is worse.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

COMPARE_SCRIPT = Path(__file__).resolve().parents[2] / "09-evaluation" / "harness_lab" / "minibench_compare.py"
DECIDING = ("mmlu_", "milu_", "arith_")  # Team 9's card; its other tasks are diagnostics
ROLES = ("learner", "rollout")
CONFIG_KEYS = {"dir", "every", "action", "control", "compare_script", "min_bpb", "max_pending"}
MAX_PENDING = 3
# Team 9's published quick scores of one set of weights move a deciding task by up to 0.0086 bpb between CPU and GPU
MIN_BPB = 0.01
SAME_SCORER = ("device", "dtype", "hardware")
# the benchmark and tokenizer files behind a score; Team 9's comparison refuses two files that differ in any of them
SUITE_HASHES = ("suite_sha256", "items_sha256", "heldout_sha256", "heldout_sources_sha256", "tokenizer_sha256")


def load_compare(script: Path | str | None = None):
    """`compare(baseline, candidate)` from Team 9's script, loaded by path: the team folders are not packages."""
    path = Path(script) if script else COMPARE_SCRIPT
    if not path.is_file():
        raise FileNotFoundError(f"Team 9's comparison script is not at {path} (lab PR 929: merge it or set "
                                "train.rollout_check.compare_script)")
    spec = importlib.util.spec_from_file_location("team9_minibench_compare", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.compare


def _write_json(path: Path, doc: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=1, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _step_dir(root: Path, step: int) -> Path:
    return root / f"step_{step:06d}"


def _steps(root: Path) -> list[tuple[int, Path]]:
    found = ((p.name.removeprefix("step_"), p) for p in Path(root).glob("step_*") if p.is_dir())
    return sorted((int(n), p) for n, p in found if n.isdigit())


def _unlink(step_dir: Path, *names: str) -> None:
    for name in names:
        (step_dir / name).unlink(missing_ok=True)


_VERDICT_FILES = ("request.json", "verdict.json", *(f"{r}.score.json" for r in ROLES))


def export(check_dir: Path, step: int, learner, rollout, scheme: str, model_spec: dict,
           tokenizer_sha256: str | None = None) -> Path:
    """Write the state dicts (no learner file when `learner` is None) and the model config for
    `minibench_lab.py --weights-safetensors`; request.json comes last."""
    from safetensors.torch import save_file  # noqa: PLC0415

    d = _step_dir(Path(check_dir), step)
    d.mkdir(parents=True, exist_ok=True)
    _unlink(d, *_VERDICT_FILES, *(f"{r}.safetensors" for r in ROLES))  # a redone step starts from nothing
    weights = {}
    for role, model in zip(ROLES, (learner, rollout)):
        if model is None:
            continue
        path = d / f"{role}.safetensors"
        tmp = d / f"{role}.safetensors.tmp"
        save_file({k: v.detach().to("cpu", copy=True).contiguous() for k, v in model.state_dict().items()}, str(tmp))
        os.replace(tmp, path)
        with path.open("rb") as stream:
            weights[role] = {"file": path.name, "sha256": hashlib.file_digest(stream, "sha256").hexdigest()}
    config = {"config": {"model": model_spec}}
    if tokenizer_sha256:
        config["artifacts"] = {"tokenizer_sha256": tokenizer_sha256}
    _write_json(d / "model.json", config)
    _write_json(d / "request.json", {
        "step": step, "scheme": scheme, "model_config": "model.json", "weights": weights,
        "scores": {r: f"{r}.score.json" for r in weights},
        # the file holds weights only: w8a8_sim also rounds activations while sampling, which a score cannot see
        "scores_cover_the_whole_scheme": scheme != "w8a8_sim",
    })
    return d


def judge(baseline: dict, candidate: dict, compare, min_bpb: float = MIN_BPB) -> dict:
    """The verdict on two score documents: task names, aggregate differences, both weight revisions and the suite hashes."""
    result = compare(baseline, candidate)
    tasks = {name: r for name, r in result["tasks"].items() if name.startswith(DECIDING)}
    if not tasks:
        raise ValueError("the score files hold none of the deciding tasks")
    worse = []
    for name, r in sorted(tasks.items()):
        if r["gold_bpb_ci95"][0] > 0 and r["gold_bpb_delta"] >= min_bpb:
            worse.append(f"{name}: gold bpb {r['gold_bpb_delta']:+.4f}")
        if "accuracy_ci95_points" in r and r["accuracy_ci95_points"][1] < 0:
            worse.append(f"{name}: accuracy {r['accuracy_delta_points']:+.1f} points")
    return {"verdict": "worse" if worse else "ok", "worse": worse, "tasks": tasks, "min_bpb": min_bpb,
            "heldout_bpb_delta": result.get("heldout_bpb_delta", {}), "profile": result.get("profile"),
            "revision": {"baseline": baseline.get("model_revision"), "candidate": candidate.get("model_revision")},
            "suite_hashes": {k: candidate.get(k) for k in SUITE_HASHES}}


def _score(step_dir: Path, role: str, request: dict) -> dict:
    doc = _read_json(step_dir / request["scores"][role])
    want = request["weights"][role]["sha256"], request["step"]
    if (doc.get("model_revision"), doc.get("step")) != want:
        raise ValueError(f"{step_dir / request['scores'][role]} does not score the {role} weights of step {request['step']}")
    return doc


def judge_step(step_dir: Path, compare, control: Path | None = None, min_bpb: float = MIN_BPB) -> dict | None:
    """Judge one exported step and write verdict.json; None while a needed score file is missing."""
    request = _read_json(step_dir / "request.json")
    base_dir, base_role, base_request = step_dir, "learner", request
    if control is not None:
        base_dir, base_role = Path(control) / step_dir.name, "rollout"
        if not (base_dir / "request.json").is_file():
            return None
        base_request = _read_json(base_dir / "request.json")
    needed = [(step_dir, "rollout", request), (base_dir, base_role, base_request)]
    if any(not (d / r["scores"][role]).is_file() for d, role, r in needed):
        return None
    base, cand = _score(base_dir, base_role, base_request), _score(step_dir, "rollout", request)
    if "smoke" in (base.get("profile"), cand.get("profile")):
        raise ValueError("smoke profile scores are execution evidence only (Team 9): score with quick or full")
    differ = [k for k in SAME_SCORER if base.get(k) != cand.get(k)]
    if differ:
        raise ValueError("the two score files differ in " + ", ".join(f"{k} ({base.get(k)} / {cand.get(k)})" for k in differ))
    verdict = judge(base, cand, compare, min_bpb)
    verdict.update(step=request["step"], scheme=request["scheme"],
                   baseline=(f"control run's rollout copy ({base_request['scheme']})" if control is not None
                             else "learner at the same step"))
    _write_json(step_dir / "verdict.json", verdict)
    return verdict


def _drop_scored_weights(step_dir: Path) -> None:
    """Remove each weights file whose matching score file has arrived."""
    if not any((step_dir / f"{r}.safetensors").is_file() for r in ROLES):
        return
    request = _read_json(step_dir / "request.json")
    for role, entry in request["weights"].items():
        try:
            _score(step_dir, role, request)
        except Exception:  # noqa: BLE001  (missing or not for these weights: they are still needed)
            continue
        _unlink(step_dir, entry["file"])


def poll(check_dir: Path, compare, control: Path | None = None, up_to: int | None = None, min_bpb: float = MIN_BPB) -> dict:
    """Judge every exported step whose scores have arrived. {"new": verdicts, "pending": steps, "errors": messages}."""
    out = {"new": [], "pending": [], "errors": []}
    for step, d in _steps(check_dir):
        if (up_to is not None and step > up_to) or not (d / "request.json").is_file():
            continue
        try:
            judged = (d / "verdict.json").is_file()
            verdict = None if judged else judge_step(d, compare, control, min_bpb)  # raises: the weights stay
            if judged or verdict is not None or control is not None:
                _drop_scored_weights(d)
        except Exception as e:  # noqa: BLE001  (whatever a score file holds, it must not end a training run)
            out["errors"].append(f"step {step}: {type(e).__name__}: {e}"[:300])
            continue
        if judged:
            continue
        if verdict is None:
            out["pending"].append(step)
        else:
            out["new"].append(verdict)
    return out


def verdicts(check_dir: Path, up_to: int | None = None) -> list[dict]:
    return [_read_json(d / "verdict.json") for step, d in _steps(check_dir)
            if (up_to is None or step <= up_to) and (d / "verdict.json").is_file()]


def short(verdict: dict) -> dict:
    """What a metrics row and the summary keep of a verdict."""
    keys = ("step", "verdict", "worse", "baseline", "heldout_bpb_delta", "scheme", "profile", "revision", "suite_hashes")
    return {k: verdict[k] for k in keys}


class RolloutCheck:
    """train.rollout_check inside the trainer."""

    def __init__(self, cfg: dict):
        unknown = set(cfg) - CONFIG_KEYS
        every = cfg.get("every", 10)
        action = cfg.get("action", "report")
        max_pending = cfg.get("max_pending", MAX_PENDING)
        min_bpb = cfg.get("min_bpb", MIN_BPB)
        counts_ok = all(type(n) is int and n >= 1 for n in (every, max_pending))
        floor_ok = isinstance(min_bpb, (int, float)) and 0 <= min_bpb < float("inf")
        if unknown or not cfg.get("dir") or not counts_ok or not floor_ok or action not in ("report", "stop"):
            raise ValueError("train.rollout_check is {dir, every and max_pending (integers >= 1), action: report | stop, "
                             f"control, compare_script, min_bpb (number >= 0)}}; got {cfg}")
        self.dir, self.every, self.action = Path(cfg["dir"]), every, action
        self.control = Path(cfg["control"]) if cfg.get("control") else None
        if self.control is not None and self.control.resolve() == self.dir.resolve():
            raise ValueError("train.rollout_check.control is this run's own folder: it would be compared with itself")
        self.min_bpb, self.max_pending = float(min_bpb), max_pending
        self.compare = load_compare(cfg.get("compare_script"))

    def start(self, state_dir: Path | None, start_step: int) -> None:
        """Claim the folder. Exports may only be found there by a restart of the same resumable run (same state_dir, also
        one that died before its first saved state); what it exported after `start_step` is removed and redone."""
        owner = None if state_dir is None else str(state_dir)
        marker = self.dir / "check.json"
        old = _steps(self.dir)
        if old and (owner is None or not marker.is_file() or _read_json(marker).get("state_dir") != owner):
            raise ValueError(f"train.rollout_check.dir {self.dir} already holds checks of another run")
        for step, d in old:
            if step > start_step:
                _unlink(d, *_VERDICT_FILES, *(f"{r}.safetensors" for r in ROLES))
        self.dir.mkdir(parents=True, exist_ok=True)
        _write_json(marker, {"state_dir": owner, "min_bpb": self.min_bpb,
                             "control": None if self.control is None else str(self.control)})

    def has_room(self) -> bool:
        """Fewer than max_pending exported steps still have weights on disk."""
        waiting = sum(any((d / f"{r}.safetensors").is_file() for r in ROLES) for _, d in _steps(self.dir))
        return waiting < self.max_pending

    def due(self, step: int, last_step: int) -> bool:
        return step % self.every == 0 or step == last_step

    def exported(self, step: int) -> bool:
        return (_step_dir(self.dir, step) / "request.json").is_file()

    def row(self, step: int) -> tuple[dict, dict | None]:
        """(fields for this step's metrics row, the first worse verdict on disk up to this step). The verdict is read from
        disk, not only from this poll, so one judged just before a crash, or by `judge` from outside, still counts."""
        got = poll(self.dir, self.compare, self.control, step, self.min_bpb)
        fields = {"rollout_check_pending": len(got["pending"])}
        if got["new"]:
            fields["rollout_check"] = [short(v) for v in got["new"]]
        if got["errors"]:
            fields["rollout_check_errors"] = got["errors"]
        return fields, next((v for v in verdicts(self.dir, step) if v["verdict"] == "worse"), None)

    def summary(self, steps_done: int) -> dict:
        got = poll(self.dir, self.compare, self.control, steps_done, self.min_bpb)
        return {"dir": str(self.dir), "every": self.every, "action": self.action,
                "control": None if self.control is None else str(self.control), "min_bpb": self.min_bpb,
                "verdicts": [short(v) for v in verdicts(self.dir, steps_done)],
                "pending_steps": got["pending"], "errors": got["errors"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    j = sub.add_parser("judge", help="judge every exported step whose scores have arrived, and list all verdicts")
    j.add_argument("--check-dir", type=Path, required=True)
    j.add_argument("--control", type=Path, help="default: the run's own setting (check.json)")
    f = sub.add_parser("files", help="judge two score files directly (nothing is written or removed)")
    f.add_argument("baseline", type=Path)
    f.add_argument("candidate", type=Path)
    for p in (j, f):
        p.add_argument("--compare-script", type=Path)
        p.add_argument("--min-bpb", type=float, help=f"a smaller bits-per-byte rise does not count (default: the run's "
                                                     f"own setting, else {MIN_BPB})")
    a = ap.parse_args(argv)
    compare = load_compare(a.compare_script)
    if a.command == "files":
        v = judge(_read_json(a.baseline), _read_json(a.candidate), compare, MIN_BPB if a.min_bpb is None else a.min_bpb)
        print(json.dumps(v, indent=1, sort_keys=True))
        return 4 if v["verdict"] == "worse" else 0
    marker = a.check_dir / "check.json"
    run = _read_json(marker) if marker.is_file() else {}  # judge as the run would have: same baseline, same floor
    control = a.control or (Path(run["control"]) if run.get("control") else None)
    min_bpb = run.get("min_bpb", MIN_BPB) if a.min_bpb is None else a.min_bpb
    got = poll(a.check_dir, compare, control, min_bpb=min_bpb)
    found = verdicts(a.check_dir)
    print(json.dumps({"verdicts": [short(v) for v in found], "pending_steps": got["pending"], "errors": got["errors"]},
                     indent=1))
    if any(v["verdict"] == "worse" for v in found):
        return 4
    return 3 if got["pending"] or got["errors"] or not found else 0


if __name__ == "__main__":
    raise SystemExit(main())
