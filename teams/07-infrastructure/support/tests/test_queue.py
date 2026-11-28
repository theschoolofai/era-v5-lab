"""The queue file (queue/job_queue.py) and the paths the cluster uses (ADR 0002)."""
import glob
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TEAM = os.path.join(HERE, "..", "..")
sys.path[:0] = [TEAM, os.path.join(TEAM, "queue")]
import job_queue  # noqa: E402
from ckpt.candidates import pick_candidates  # noqa: E402


def test_crash_loop_holds_on_the_third_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(job_queue, "CRASHLOOP_WINDOW_S", 60)
    got = []
    for node in ("gpu-1", "gpu-2", "gpu-3"):          # each requeue lands on another node: the count survives
        monkeypatch.setattr(job_queue, "node_name", lambda n=node: n)
        got.append(job_queue.crash_loop(str(tmp_path / "run")))
    assert got == [(False, 1), (False, 2), (True, 3)]
    assert not list(tmp_path.rglob("*.jsonl"))         # one object rewritten whole: no append (S3 has none)


def test_crash_ledger_down_retries_and_says_so(tmp_path, monkeypatch):
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path / "ev"))
    monkeypatch.setattr(job_queue, "open_store", lambda url: (_ for _ in ()).throw(OSError("S3 unreachable")))
    assert job_queue.crash_loop("s3://nowhere/run") == (False, 0)
    assert "crash_ledger_unavailable" in "".join(p.read_text() for p in (tmp_path / "ev").glob("*.jsonl"))


def fake_slurm(nodes, main_nodes=""):
    calls = []

    def run(cmd, timeout=30):
        calls.append(" ".join(cmd))
        out = {"sinfo": "\n".join(f"{n}|{s}" for n, s in nodes.items()), "squeue": main_nodes,
               "scontrol": "gpu-1 gpu-2" if cmd[1:3] == ["show", "hostnames"] else ""}[cmd[0]]
        return job_queue.subprocess.CompletedProcess(cmd, 0, out, "")
    return run, calls


def test_hot_spare_is_named_even_when_main_run_nodes_are_busy(monkeypatch, tmp_path):
    """The main run on gpu-1,2 (busy) must not count as the spare: gpu-3 is named explicitly."""
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path))
    run, calls = fake_slurm({"gpu-1": "alloc", "gpu-2": "alloc", "gpu-3": "idle", "gpu-4": "idle~"}, "gpu-[1-2]")
    monkeypatch.setattr(job_queue, "_slurm", run)
    out = job_queue.keep_spare()
    assert out["ok"] and out["spares"] == ["gpu-3"] and out["powered_up"] == []
    assert "scontrol update SuspendExcNodes=gpu-3" in calls


def test_no_free_node_powers_one_up(monkeypatch, tmp_path):
    """The spare took over a failed node: nothing is free, so the next powered-off node is booted and named."""
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path))
    run, calls = fake_slurm({"gpu-1": "alloc", "gpu-2": "alloc", "gpu-3": "drain", "gpu-4": "idle~",
                             "gpu-5": "idle~"}, "gpu-[1-2]")
    monkeypatch.setattr(job_queue, "_slurm", run)
    out = job_queue.keep_spare()
    assert out["ok"] and out["powered_up"] == ["gpu-4"]
    assert "scontrol update nodename=gpu-4 state=power_up" in calls
    assert "scontrol update SuspendExcNodes=gpu-4" in calls


def test_spot_notice_from_drill_file(tmp_path, monkeypatch):
    f = tmp_path / "spot_notice"
    monkeypatch.setattr(job_queue, "NOTICE_CMD", None)
    monkeypatch.setattr(job_queue, "NOTICE_FILE", str(f))
    assert job_queue.spot_notice() == ""
    f.write_text("")
    assert job_queue.spot_notice() == "spot notice (drill)"


def test_spot_notice_from_command(monkeypatch):
    """On a cloud node a command (V5_SPOT_NOTICE_CMD) asks for the notice; empty output or an error = none."""
    monkeypatch.setattr(job_queue, "NOTICE_CMD", "echo 'terminate in 120 s'")
    assert job_queue.spot_notice() == "terminate in 120 s"
    monkeypatch.setattr(job_queue, "NOTICE_CMD", "exit 1")
    assert job_queue.spot_notice() == ""
    monkeypatch.setattr(job_queue, "NOTICE_CMD", "true")
    assert job_queue.spot_notice() == ""


def test_without_slurm_nothing_crashes(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path))
    monkeypatch.setattr(job_queue.shutil, "which", lambda name: None)
    assert job_queue.drain("drill_force_fail", "c1") is False      # reported as an event, not an exception
    assert job_queue.ask_jobs_to_save_and_stop("c1") == []
    assert job_queue.status() == 1 and "squeue is not available" in capsys.readouterr().out


def test_default_trainer_exists():
    assert os.path.exists(job_queue.TRAIN_SCRIPT), job_queue.TRAIN_SCRIPT


def test_every_cluster_path_exists():
    """/opt/v5 is the team folder in every container. A moved file must not leave a dangling path behind."""
    files = glob.glob(os.path.join(TEAM, "slurm", "*")) + \
        glob.glob(os.path.join(TEAM, "support", "simulation", "slurm-docker", "*")) + \
        [os.path.join(TEAM, "support", "simulation", "run_sim.py")]
    planned = {"slurm/node_suspend.sh", "slurm/node_resume.sh"}   # week 2, need the cloud
    missing = set()
    for f in files:
        for p in re.findall(r"/opt/v5/([\w./-]+\.(?:py|sh|sbatch|conf))", open(f).read()):
            if p not in planned and not os.path.exists(os.path.join(TEAM, p)):
                missing.add(f"{os.path.basename(f)}: /opt/v5/{p}")
    assert not missing, sorted(missing)


# ---- Team 05 main-run start mode ---------------------------------------------------------------
def write_manifest(run_root, path="main/step_0-e1", step=0):
    target = run_root / path / "MANIFEST.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "step": step, "files": {}, "env": {}, "keys": {}, "world_size": 1,
        "state_digest": "digest", "probe_loss": {}, "frozen": {}, "tokens": 0, "next_batch": "batch-0",
    }))


def test_start_mode_distinguishes_fresh_commit_and_claim(tmp_path, monkeypatch):
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path / "events"))
    root = tmp_path / "store"
    root.mkdir()
    assert job_queue.start_mode(str(root), "r1", wait_s=0) == "fresh"
    assert not (root / "r1").exists()                 # a read-only check must not create the run

    st = job_queue.open_store(str(root / "r1"))
    st.put_json("latest.json", {"epoch": 1, "path": None, "step": None})
    assert job_queue.start_mode(str(root), "r1", wait_s=0) == "claimed_only"

    (root / "r1" / "commits.jsonl").write_text(
        '{"step": 0, "branch": "main", "path": "main/step_0-e1"}\n')
    write_manifest(root / "r1")
    assert job_queue.start_mode(str(root), "r1", wait_s=0) == "resume"
    (root / "r1" / "commits.jsonl").unlink()
    st.put_json("latest.json", {"epoch": 2, "branch": "main", "path": "main/step_0-e1", "step": 0})
    assert job_queue.start_mode(str(root), "r1", wait_s=0) == "resume"
    assert "job.start_mode" in "".join(p.read_text() for p in (tmp_path / "events").glob("*.jsonl"))


def test_start_mode_rejects_malformed_commit_history(tmp_path):
    root = tmp_path / "store"
    run = root / "r1"
    run.mkdir(parents=True)
    (run / "commits.jsonl").write_text("not-json\n")
    with pytest.raises(OSError, match="invalid JSON"):
        job_queue.start_mode(str(root), "r1", tries=1, wait_s=0)
    (run / "commits.jsonl").write_text('{"step": 0, "path": "main/step_0-e1"}\n')
    with pytest.raises(OSError, match="branch"):
        job_queue.start_mode(str(root), "r1", tries=1, wait_s=0)
    (run / "commits.jsonl").write_text(
        '{"step": 0, "branch": "main", "path": "main/missing"}\n')
    (run / "latest.json").write_text('{"epoch": 1, "step": 0, "branch": "main", "path": "main/missing"}')
    with pytest.raises(OSError, match="missing main/missing/MANIFEST.json"):
        job_queue.start_mode(str(root), "r1", tries=1, wait_s=0)
    (run / "commits.jsonl").write_text(
        '{"step": 0, "branch": "main", "path": "../outside"}\n')
    with pytest.raises(OSError, match="normalized relative"):
        job_queue.start_mode(str(root), "r1", tries=1, wait_s=0)
    (run / "commits.jsonl").unlink()
    (run / "latest.json").write_text('{"epoch": null, "path": null}')
    with pytest.raises(OSError, match="epoch"):
        job_queue.start_mode(str(root), "r1", tries=1, wait_s=0)


def test_start_mode_holds_commit_history_without_latest(tmp_path):
    """Restore would find no candidate here (Checkpointer.candidates() needs latest.json), so start-mode must not
    answer resume: it raises, and mainrun.sbatch holds."""
    root = tmp_path / "store"
    run = root / "r1"
    run.mkdir(parents=True)
    (run / "commits.jsonl").write_text('{"step": 0, "branch": "main", "path": "main/step_0-e1"}\n')
    write_manifest(run)
    with pytest.raises(OSError, match="latest.json is missing"):
        job_queue.start_mode(str(root), "r1", tries=1, wait_s=0)


def test_candidate_rule_is_shared_by_start_mode_and_restore():
    commits = [{"step": s, "branch": "main", "path": f"main/step_{s}-e1"} for s in (0, 50, 100)]
    claim = {"epoch": 1, "path": None, "step": None}
    newest = dict(commits[1], epoch=2)
    assert pick_candidates(commits, None) == []                                   # no latest.json
    assert pick_candidates([], None) == []
    assert pick_candidates([], claim) == []                                       # a claim and nothing committed
    assert pick_candidates(commits, claim) == commits[::-1]                       # a claim: history, newest first
    assert pick_candidates(commits, newest) == [newest, commits[2], commits[0]]   # latest.json first, once
    assert pick_candidates(commits, newest, from_step=50) == [commits[1]]         # rollback ignores latest.json
    assert pick_candidates(commits, None, from_step=50) == [commits[1]]
    assert pick_candidates(commits, newest, from_step=7) == []


def test_start_mode_fails_closed_without_store(tmp_path):
    root = tmp_path / "not-mounted"
    with pytest.raises(OSError, match="does not exist"):
        job_queue.start_mode(str(root), "r1", tries=1, wait_s=0)
    assert not root.exists()
    with pytest.raises(ValueError, match="run ID"):
        job_queue.start_mode(str(tmp_path), "../other", tries=1, wait_s=0)


def test_start_mode_fails_closed_on_s3_error(monkeypatch):
    class Denied:
        kind = "s3"

        def list(self, prefix=""):
            raise PermissionError("AccessDenied")

    monkeypatch.setattr(job_queue, "open_store", lambda url: Denied())
    monkeypatch.setattr(job_queue.time, "sleep", lambda seconds: None)
    with pytest.raises(OSError, match="after 3 tries"):
        job_queue.start_mode("s3://bucket/ckpt", "r1")


def test_start_mode_cli_reports_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path / "events"))
    monkeypatch.setattr(job_queue.time, "sleep", lambda seconds: None)
    rc = job_queue.main(["start-mode", "--remote-root", str(tmp_path / "gone"), "--run-id", "r1"])
    assert rc == 3
    assert "cannot read the checkpoint store" in capsys.readouterr().err


# ---- mainrun.sbatch command construction -------------------------------------------------------
REQUIRED_ARGS = (
    "--config=cfg.yaml",
    "--runtime=runtime.yaml",
    "--resolution=resolution.yaml",
    "--tokenizer-release=v1",
    "--tokenizer=tokenizer.json",
    "--byte-table=bytes.json",
    "--train-data=train.jsonl",
    "--heldout-data=heldout.jsonl",
    "--heldout-sources=heldout-sources.json",
    "--heldout-sha256=heldout.sha256",
    "--heldout-report=heldout-report.json",
    "--seed=7",
)


def run_mainrun(tmp_path, env=None, args_lines=None):
    """Run mainrun.sbatch with fake Slurm commands; return process and the fake srun record."""
    env = dict(env or {})
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    scontrol = bin_dir / "scontrol"
    scontrol.write_text('#!/bin/bash\n[[ "$1 $2" == "show hostnames" ]] && echo node1\nexit 0\n')
    srun = bin_dir / "srun"
    record = tmp_path / "srun.json"
    srun.write_text(
        f"#!{sys.executable}\nimport json, os, sys\n"
        f"json.dump({{'argv': sys.argv[1:], 'env': dict(os.environ)}}, open({str(record)!r}, 'w'))\n"
    )
    for path in (scontrol, srun):
        path.chmod(0o755)

    script_text = open(os.path.join(TEAM, "slurm", "mainrun.sbatch")).read()
    script_text = script_text.replace("/opt/venv/bin/python", sys.executable).replace("/opt/v5", os.path.abspath(TEAM))
    script = tmp_path / "mainrun.sbatch"
    script.write_text(script_text)

    trainer_dir = tmp_path / "trainer"
    trainer_dir.mkdir(exist_ok=True)
    trainer = trainer_dir / "train_week2.py"
    trainer.write_text("")
    args_file = tmp_path / "mainrun.args"
    lines = REQUIRED_ARGS if args_lines is None else args_lines
    args_file.write_text("# Team 05 reviewed inputs\n\n" + "\n".join(lines) + "\n")
    store = tmp_path / "store"
    store.mkdir(exist_ok=True)
    out = tmp_path / "out"
    base = {
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "HOME": str(tmp_path),
        "RUN_ID": "r1",
        "SLURM_JOB_ID": "42",
        "SLURM_RESTART_COUNT": "1",
        "SLURM_JOB_NODELIST": "node1",
        "SLURM_NTASKS": "1",
        "SLURM_NTASKS_PER_NODE": "1",
        "SLURM_JOB_NUM_NODES": "1",
        "SLURM_GPUS_ON_NODE": "8",
        "V5_TRAIN_SCRIPT": str(trainer),
        "V5_TRAIN_ARGS_FILE": str(args_file),
        "V5_REMOTE_ROOT": str(store),
        "V5_OUT_ROOT": str(out),
        "V5_EVENTS_DIR": str(tmp_path / "events"),
        "V5_RUNS_DIR": str(tmp_path / "runs"),
        "V5_DRILL_DIR": str(tmp_path / "must-not-reach-production"),
        "V5_TEST_CRASH_BEFORE_SEAL": "1",
        "V5_DEVICE": "cpu",
        "INTERVAL_S": "8",
        "WATCHDOG_S": "20",
    }
    base.update(env)
    base = {key: value for key, value in base.items() if value is not None}
    if record.exists():
        record.unlink()
    process = subprocess.run(["bash", str(script)], env=base, capture_output=True, text=True, timeout=60)
    got = json.loads(record.read_text()) if record.exists() else {"argv": [], "env": {}}
    return process, got


def trainer_args(got):
    index = next(i for i, arg in enumerate(got["argv"])
                 if arg.endswith("train_week2.py") or arg.endswith("/support/simulation/trainer/train.py"))
    return got["argv"][index + 1:]


def test_mainrun_defaults_to_team05_fresh_start(tmp_path):
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 0, process.stderr
    args = trainer_args(got)
    attempt = tmp_path / "out" / "r1" / "42.1"
    assert args[:len(REQUIRED_ARGS)] == list(REQUIRED_ARGS)
    assert args[-1] == "--checkpoint-at-start"
    assert args[args.index("--checkpoint-store") + 1] == str(tmp_path / "store")
    assert args[args.index("--device") + 1] == "cuda"
    assert args[args.index("--checkpoint-interval-s") + 1] == "600"
    assert args[args.index("--watchdog-s") + 1] == "600"
    assert args[args.index("--out") + 1] == str(attempt / "train")
    assert not (attempt / "train").exists()
    assert got["env"]["TORCH_NCCL_DEBUG_INFO_TEMP_FILE"] == str(attempt / "nccl_trace" / "rank_")
    assert (attempt / "nccl_trace").is_dir()
    assert "V5_DRILL_DIR" not in got["env"]
    assert "V5_TEST_CRASH_BEFORE_SEAL" not in got["env"]
    assert got["env"]["V5_REMOTE_ROOT"] == str(tmp_path / "store")
    assert "--gpus-per-task=1" in got["argv"]
    assert not {"--step-sleep", "--drill-dir", "--remote-root", "--local-root", "--steps", "--interval-s"} & set(args)


def test_mainrun_resumes_committed_history(tmp_path):
    run = tmp_path / "store" / "r1"
    run.mkdir(parents=True)
    (run / "latest.json").write_text('{"epoch": 2, "path": null, "step": 0}')
    (run / "commits.jsonl").write_text(
        '{"step": 0, "branch": "main", "path": "main/step_0-e1"}\n')
    write_manifest(run)
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 0, process.stderr
    args = trainer_args(got)
    assert "--resume-committed" in args
    assert "--checkpoint-at-start" not in args


def claim_only(tmp_path, job="7"):
    """A run with a claim and no commit, claimed by Slurm job `job` (None: latest.json has no job field)."""
    run = tmp_path / "store" / "r1"
    run.mkdir(parents=True, exist_ok=True)
    claim = {"epoch": 1, "path": None, "step": None}
    if job is not None:
        claim["job"] = job
    (run / "latest.json").write_text(json.dumps(claim))


def fake_sacct(tmp_path, stdout="", returncode=0, stderr=""):
    """A sacct on PATH for run_mainrun (its bin dir is tmp_path/bin). Records the arguments it was called with."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    sacct = bin_dir / "sacct"
    sacct.write_text(f"#!{sys.executable}\nimport sys\nopen({str(tmp_path / 'sacct.args')!r}, 'w').write(' '.join(sys.argv[1:]))\n"
                     f"sys.stdout.write({stdout!r})\nsys.stderr.write({stderr!r})\nsys.exit({returncode})\n")
    sacct.chmod(0o755)


def test_mainrun_holds_claim_without_commit(tmp_path):
    """No sacct on the node: the earlier job is not confirmed ended. The job holds and says so."""
    claim_only(tmp_path)
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 78 and got["argv"] == []
    assert "claim but no committed checkpoint" in process.stderr
    assert "not confirmed ended" in process.stderr and "confirm in sacct that it has ended" in process.stderr
    assert "resubmit with a new RUN_ID" in process.stderr and "nothing was committed" in process.stderr
    assert "--recover-precommit" not in process.stderr


@pytest.mark.parametrize("state", ["RUNNING", "PENDING", "REQUEUED", "SUSPENDED", "COMPLETING", "CONFIGURING", "WEIRD"])
def test_claimed_only_with_an_active_or_unknown_job_is_not_confirmed(tmp_path, state):
    claim_only(tmp_path, job="7")
    fake_sacct(tmp_path, f"7|{state}\n")
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 78 and got["argv"] == []
    assert f"job 7 is not confirmed ended (sacct state {state})" in process.stderr
    assert (tmp_path / "sacct.args").read_text() == "-j 7 -X -n -P -o JobID,State"


@pytest.mark.parametrize("state", ["COMPLETED", "FAILED", "CANCELLED by 1000", "TIMEOUT", "NODE_FAIL",
                                   "OUT_OF_MEMORY", "BOOT_FAIL", "DEADLINE", "PREEMPTED"])
def test_claimed_only_with_an_ended_job_still_holds_until_the_trainer_can_start_over_it(tmp_path, state):
    """The sacct check passes, but train_week2.py refuses --checkpoint-at-start over a claim until #826. No trainer
    starts, and the flag is not passed."""
    claim_only(tmp_path, job="7")
    fake_sacct(tmp_path, f"7|{state}\n")
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 78 and got["argv"] == []
    assert f"job 7 has ended (sacct state {state.split()[0]})" in process.stderr
    assert "resubmit with a new RUN_ID" in process.stderr and "nothing was committed" in process.stderr
    assert "not confirmed ended" not in process.stderr


def test_claimed_only_checks_the_newest_row_of_a_requeued_job(tmp_path):
    """sacct normally prints only the newest record of a requeued job. If it prints several, the last one counts."""
    claim_only(tmp_path, job="7")
    fake_sacct(tmp_path, "7|REQUEUED\n7|REQUEUED\n7|FAILED\n")
    process, _ = run_mainrun(tmp_path)
    assert "job 7 has ended (sacct state FAILED)" in process.stderr
    fake_sacct(tmp_path, "7|REQUEUED\n7|FAILED\n7|REQUEUED\n")
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 78 and got["argv"] == []
    assert "job 7 is not confirmed ended (sacct state REQUEUED)" in process.stderr


def test_claimed_only_claim_made_by_this_job_counts_as_ended(tmp_path):
    """A requeue of the same job (SLURM_JOB_ID 42): its earlier restart has stopped. sacct is not even asked."""
    claim_only(tmp_path, job="42")
    fake_sacct(tmp_path, "42|RUNNING\n")
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 78 and got["argv"] == []
    assert "the claim was made by this job (42)" in process.stderr
    assert not (tmp_path / "sacct.args").exists()


@pytest.mark.parametrize("job", [None, "", "abc", "12_3", "7; rm -rf /", 7])
def test_claimed_only_without_a_usable_job_in_latest_json_is_not_confirmed(tmp_path, job):
    claim_only(tmp_path, job=job)
    fake_sacct(tmp_path, "7|COMPLETED\n")
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 78 and got["argv"] == []
    assert "latest.json names no Slurm job" in process.stderr and "not confirmed ended" in process.stderr
    assert not (tmp_path / "sacct.args").exists()


@pytest.mark.parametrize("stdout, returncode, message", [
    ("", 0, "sacct has no record of job 7"),
    ("8|COMPLETED\n", 0, "sacct has no record of job 7"),
    ("7.batch|COMPLETED\n", 0, "sacct has no record of job 7"),
    ("", 1, "sacct failed for job 7: slurmdbd down"),
])
def test_claimed_only_when_sacct_cannot_say_is_not_confirmed(tmp_path, stdout, returncode, message):
    claim_only(tmp_path, job="7")
    fake_sacct(tmp_path, stdout, returncode, stderr="slurmdbd down" if returncode else "")
    process, got = run_mainrun(tmp_path)
    assert process.returncode == 78 and got["argv"] == []
    assert message in process.stderr and "not confirmed ended" in process.stderr


def test_claimed_only_hold_sends_the_job_held_event_with_the_sacct_state(tmp_path):
    claim_only(tmp_path, job="7")
    fake_sacct(tmp_path, "7|RUNNING\n")
    process, _ = run_mainrun(tmp_path)
    assert process.returncode == 78
    events = held_events(tmp_path)
    assert len(events) == 1 and events[0]["cause"] == "startup_check_failed"
    assert "job 7 is not confirmed ended (sacct state RUNNING)" in events[0]["detail"]


def test_claim_owner_command_exit_codes(tmp_path, monkeypatch, capsys):
    run = tmp_path / "store" / "r1"
    run.mkdir(parents=True)
    (run / "latest.json").write_text(json.dumps({"epoch": 1, "path": None, "step": None, "job": "7"}))
    args = ["claim-owner", "--remote-root", str(tmp_path / "store"), "--run-id", "r1"]

    class Done:
        returncode, stderr = 0, ""
        stdout = "7|COMPLETED\n"

    monkeypatch.setattr(job_queue, "_slurm", lambda cmd, timeout=30: Done())
    assert job_queue.main(args) == 0
    assert "job 7 has ended (sacct state COMPLETED)" in capsys.readouterr().out
    Done.stdout = "7|RUNNING\n"
    assert job_queue.main(args) == 3
    monkeypatch.setattr(job_queue, "_slurm", lambda cmd, timeout=30: None)
    assert job_queue.main(args) == 3
    assert job_queue.main(["claim-owner", "--remote-root", str(tmp_path / "missing"), "--run-id", "r1"]) == 3
    assert job_queue.main(["claim-owner", "--remote-root", str(tmp_path / "store"), "--run-id", "bad id"]) == 3


def test_mainrun_rejects_incomplete_or_unsafe_commands(tmp_path):
    cases = [
        ({"SLURM_NTASKS": "2"}, None, "requires exactly one task"),
        ({"SLURM_JOB_NUM_NODES": "2"}, None, "requires exactly one node"),
        ({"SLURM_GPUS_ON_NODE": "2"}, None, "must allocate all 8 GPUs"),
        ({"V5_TRAIN_SCRIPT": "/tmp/not-the-trainer.py"}, None, "must name Team 05's train_week2.py"),
        ({"V5_TRAIN_ARGS_FILE": "/tmp/missing.args"}, None, "readable main-run argument file"),
        ({"V5_OUT_ROOT": "relative/out"}, None, "must be absolute"),
        ({}, REQUIRED_ARGS[:-1], "needs explicit values for: --seed"),
        ({}, REQUIRED_ARGS + ("--seed=8",), "sets --seed more than once"),
        ({}, REQUIRED_ARGS + ("--seed",), "sets --seed more than once"),
        ({}, REQUIRED_ARGS + ("--seed=",), "sets --seed more than once"),
        ({}, REQUIRED_ARGS + ("--out=/tmp/other",), "may not override mainrun.sbatch's --out"),
        ({}, REQUIRED_ARGS + ("--resume-c",), "may not override mainrun.sbatch's --resume-committed"),
        ({}, REQUIRED_ARGS + ("--see=8",), "abbreviates reviewed option --seed"),
        ({}, REQUIRED_ARGS + ("--log=writer:make",), "abbreviates reviewed option --logger-factory"),
        ({}, REQUIRED_ARGS + ("--unknown=x",), "is not an approved train_week2.py main-run option"),
        ({}, REQUIRED_ARGS + ("--stop-after=1",), "main runs do not support --stop-after"),
        ({}, REQUIRED_ARGS + ("--lr",), "--lr requires a non-empty --option=value argument"),
        ({}, REQUIRED_ARGS + ("--lr=0.1", "--lr=0.2"), "sets --lr more than once"),
        ({}, REQUIRED_ARGS + ("--consolidate-step-checks=true",), "is a bare switch and does not take a value"),
        ({}, REQUIRED_ARGS + ("--consolidate-step-checks", "--no-consolidate-step-checks"),
         "choose only one of --consolidate-step-checks and --no-consolidate-step-checks"),
        ({"TRAIN_EXTRA": "--config=other.yaml"}, None, "TRAIN_EXTRA is simulation-only"),
        ({"TRAIN_EXTRA": "--from-step 10 --skip 2 --branch b1"}, None, "TRAIN_EXTRA is simulation-only"),
        ({"V5_TRAINER": "sim"}, None, "also requires V5_SIMULATION=1"),
        ({"V5_TRAINER": "other"}, None, "must be week2 or sim"),
        ({"RUN_ID": "../other"}, None, "RUN_ID must begin with a letter or digit"),
    ]
    for index, (env, args, message) in enumerate(cases):
        case = tmp_path / str(index)
        case.mkdir()
        process, got = run_mainrun(case, env, args)
        assert process.returncode == 78 and got["argv"] == [], (index, process.stderr)
        assert message in process.stderr, (index, process.stderr)


def held_events(tmp_path):
    return [json.loads(line) for f in sorted((tmp_path / "events").glob("*.jsonl"))
            for line in f.read_text().splitlines() if '"job.held"' in line]


def test_mainrun_startup_hold_sends_job_held_event(tmp_path):
    """Q-02 counts job.held. A startup check that holds the job (exit 78) must send it, with the reason."""
    cases = [
        ("a", {"SLURM_NTASKS": "2"}, "requires exactly one task"),
        ("b", {"TRAIN_EXTRA": "--from-step 10 --skip 2 --branch b1"}, "TRAIN_EXTRA is simulation-only"),
        ("c", {"V5_REMOTE_ROOT": str(tmp_path / "not-mounted")}, "cannot determine the start mode"),
    ]
    for name, env, message in cases:
        case = tmp_path / name
        case.mkdir()
        process, got = run_mainrun(case, env)
        assert process.returncode == 78 and got["argv"] == [], (name, process.stderr)
        events = held_events(case)
        assert len(events) == 1, (name, events)
        assert events[0]["cause"] == "startup_check_failed" and events[0]["severity"] == "high"
        assert message in events[0]["detail"] and events[0]["run_id"] == "r1" and events[0]["job_id"] == "42"
    claim = tmp_path / "d"
    claim.mkdir()
    run = claim / "store" / "r1"
    run.mkdir(parents=True)
    (run / "latest.json").write_text('{"epoch": 1, "path": null, "step": null}')
    process, _ = run_mainrun(claim)
    assert process.returncode == 78
    assert "claim but no committed checkpoint" in held_events(claim)[0]["detail"]


def test_mainrun_hold_event_failure_keeps_exit_78(tmp_path):
    not_a_dir = tmp_path / "events-file"
    not_a_dir.write_text("")
    process, _ = run_mainrun(tmp_path, {"SLURM_NTASKS": "2", "V5_EVENTS_DIR": str(not_a_dir)})
    assert process.returncode == 78
    assert "requires exactly one task" in process.stderr


def test_hold_event_cli_records_one_job_held(tmp_path, monkeypatch):
    monkeypatch.setenv("V5_EVENTS_DIR", str(tmp_path / "events"))
    assert job_queue.main(["hold-event", "--reason", "V5 test reason"]) == 0
    events = held_events(tmp_path)
    assert [e["detail"] for e in events] == ["V5 test reason"]
    assert job_queue.lookup("startup_check_failed")["alert"] == "Q-02"


def test_mainrun_holds_when_store_root_is_missing(tmp_path):
    missing = tmp_path / "not-mounted"
    process, got = run_mainrun(tmp_path, {"V5_REMOTE_ROOT": str(missing)})
    assert process.returncode == 78 and got["argv"] == []
    assert "cannot determine the start mode" in process.stderr
    assert not missing.exists()


def test_mainrun_simulation_keeps_legacy_flags(tmp_path):
    process, got = run_mainrun(
        tmp_path,
        {"V5_TRAINER": "sim", "V5_SIMULATION": "1",
         "V5_TRAIN_ARGS_FILE": None, "STEPS": "10", "INTERVAL_S": "8", "STEP_SLEEP": "0.05",
         "TRAIN_EXTRA": "--from-step 3 --skip 5 --branch b1"},
    )
    assert process.returncode == 0, process.stderr
    args = trainer_args(got)
    assert args == [
        "--run-id", "r1", "--remote-root", str(tmp_path / "store"), "--local-root", "/nvme/ckpt",
        "--steps", "10", "--interval-s", "8", "--watchdog-s", "20", "--step-sleep", "0.05",
        "--drill-dir", str(tmp_path / "must-not-reach-production"),
        "--from-step", "3", "--skip", "5", "--branch", "b1",
    ]
    assert got["env"]["V5_DRILL_DIR"] == str(tmp_path / "must-not-reach-production")
    assert "V5_TRAIN_SCRIPT" not in got["env"]
