"""The queue file (queue/job_queue.py) and the paths the cluster uses (ADR 0002)."""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEAM = os.path.join(HERE, "..", "..")
sys.path[:0] = [TEAM, os.path.join(TEAM, "queue")]
import job_queue  # noqa: E402


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
