"""TSAI v1 CPU package admission and bounded process restart supervisor."""
import argparse
import fcntl
import json
import os
import platform
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

import ckpt

ROOT = Path(__file__).resolve().parent


def admit(package):
    package = Path(package).resolve()
    spec = json.loads(package.read_text())
    required = {'schema_version', 'job_id', 'owner', 'command', 'config', 'code', 'data', 'resources', 'restart'}
    if set(spec) != required or spec['schema_version'] != 1:
        raise ValueError('Expected exact TSAI v1 package fields')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', spec['job_id']):
        raise ValueError('Invalid job_id')
    if not isinstance(spec['owner'], str) or not spec['owner'].strip():
        raise ValueError('owner required')
    def source(relative):
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise ValueError('Input paths must be repository relative')
        p = (ROOT / relative).resolve()
        if ROOT not in p.parents or not p.is_file():
            raise ValueError('Missing input or path outside repository: ' + str(relative))
        return p
    config_path = source(spec['config'])
    config = json.loads(config_path.read_text())
    if not isinstance(config, dict) or not config:
        raise ValueError('Nonempty JSON training config required')
    code = spec['code']
    if not isinstance(code, list) or not code or len(set(code)) != len(code):
        raise ValueError('Nonempty unique code inventory required')
    code_hashes = {name: ckpt.digest(source(name)) for name in code}
    data = spec['data']
    if set(data) != {'id', 'manifest'} or not isinstance(data['id'], str) or not data['id']:
        raise ValueError('data requires id and manifest')
    data_hash = ckpt.digest(source(data['manifest']))
    command = spec['command']
    if not isinstance(command, list) or not command or any(not isinstance(s, str) or not s for s in command):
        raise ValueError('command must be an argv array')
    tokens = set(re.findall(r'\{[^{}]*\}', ' '.join(command)))
    allowed = {'{python}', '{repo}', '{config}', '{run_dir}', '{resume}'}
    if not tokens <= allowed or not {'{config}', '{run_dir}', '{resume}'} <= tokens:
        raise ValueError('command requires config/run_dir/resume placeholders; unknown placeholder')
    r = spec['resources']
    if set(r) != {'nodes', 'tasks', 'gpus', 'cpus', 'memory_mb', 'time_minutes', 'partition'}:
        raise ValueError('Invalid resources fields')
    for k in ('nodes', 'tasks', 'gpus', 'cpus', 'memory_mb', 'time_minutes'):
        if type(r[k]) is not int:
            raise ValueError('Resource values must be integers')
    if r['nodes'] != 1 or r['tasks'] != 1 or r['gpus'] != 0:
        raise ValueError('TSAI v1 supports one CPU task; GPU adapter not integrated')
    if min(r[k] for k in ('cpus', 'memory_mb', 'time_minutes')) <= 0 or not re.fullmatch(r'[A-Za-z0-9_-]+', r['partition']):
        raise ValueError('Positive finite resources and partition required')
    policy = spec['restart']
    if set(policy) != {'max_restarts', 'backoff_seconds', 'exit_codes'}:
        raise ValueError('Invalid restart fields')
    if type(policy['max_restarts']) is not int or not 0 <= policy['max_restarts'] <= 10:
        raise ValueError('max_restarts must be 0..10')
    if type(policy['backoff_seconds']) not in (float, int) or not 0 <= policy['backoff_seconds'] <= 60:
        raise ValueError('backoff_seconds must be 0..60')
    if not isinstance(policy['exit_codes'], list) or any(type(c) is not int or c not in (-9, -11, 75, 137) for c in policy['exit_codes']):
        raise ValueError('Only worker SIGKILL/SIGSEGV, temporary failure 75, and 137 are retryable')
    identity = {'package': spec, 'config': config, 'code_sha256': code_hashes, 'data_sha256': data_hash,
                'runtime': {'python': platform.python_version(), 'torch': str(ckpt.torch.__version__),
                            'numpy': str(ckpt.np.__version__), 'system': platform.system(), 'machine': platform.machine()}}
    return spec, config_path, identity


def event(root, kind, **fields):
    row = {'event': kind, 'time_ns': time.time_ns(), **fields}
    with open(root / 'events.jsonl', 'a') as f:
        f.write(json.dumps(row, sort_keys=True) + '\n')
        f.flush()
        os.fsync(f.fileno())
    print(json.dumps(row, sort_keys=True), flush=True)


def run(package, run_dir):
    spec, config_path, identity = admit(package)
    root = Path(run_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with open(root / '.runner.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Run already has an active runner/worker')
        identity_path = root / 'identity.json'
        if identity_path.exists():
            if json.loads(identity_path.read_text()) != identity:
                raise ValueError('Run inputs changed: use a new run directory')
        else:
            ckpt.write_synced(identity_path, json.dumps(identity, sort_keys=True))
        history = [json.loads(s) for s in (root / 'events.jsonl').read_text().splitlines()] if (root / 'events.jsonl').exists() else []
        if any(row['event'] == 'succeeded' for row in history):
            raise ValueError('Run already succeeded; use a new run directory')
        attempts = sum(row['event'] == 'attempt_started' for row in history)
        allocation_deadline = time.monotonic() + spec['resources']['time_minutes'] * 60
        stopped = []
        child = None
        def stop(sig, frame):
            stopped.append(sig)
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        old = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
        try:
            while attempts <= spec['restart']['max_restarts']:
                if stopped:
                    return 128 + stopped[0]
                if admit(package)[2] != identity:
                    raise ValueError("Run inputs changed during execution")
                rejected = []
                try:
                    checkpoint = ckpt.latest_complete(root / 'checkpoints', expected_config=identity, rejected=rejected)
                except FileNotFoundError:
                    checkpoint = None
                for item in rejected:
                    source = Path(item['path'])
                    quarantine = root / 'checkpoints' / '.rejected'
                    quarantine.mkdir(exist_ok=True)
                    destination = quarantine / (source.name + '-' + str(time.time_ns()))
                    os.rename(source, destination)
                    ckpt.sync_dir(source.parent)
                    event(root, 'checkpoint_rejected', **item, quarantined=str(destination))
                # The run lock (also inherited by workers) proves no writer remains.
                # Preserve crash debris so a stale per-step lock cannot block replay.
                for source in sorted((root / 'checkpoints').glob('.step-*.lock')) + sorted((root / 'checkpoints').glob('.incomplete-*')):
                    quarantine = root / 'checkpoints' / '.rejected'
                    quarantine.mkdir(exist_ok=True)
                    destination = quarantine / (source.name + '-' + str(time.time_ns()))
                    os.rename(source, destination)
                    ckpt.sync_dir(source.parent)
                    event(root, 'crash_debris_quarantined', path=str(source), quarantined=str(destination))
                if checkpoint is None and (attempts or (root / 'checkpoints').exists() and any((root / 'checkpoints').iterdir())):
                    event(root, 'failed', reason='No valid COMPLETE checkpoint; refuse restart from scratch')
                    return 1
                values = {'python': sys.executable, 'repo': str(ROOT), 'config': str(config_path),
                          'run_dir': str(root), 'resume': str(checkpoint) if checkpoint else 'none'}
                command = [s.format(**values) for s in spec['command']]
                attempts += 1
                with open(root / f'attempt-{attempts:02d}.log', 'a') as output:
                    # Child retains lock if supervisor is killed, preventing concurrent writers.
                    child = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                             start_new_session=True, pass_fds=(lock.fileno(),))
                    event(root, 'attempt_started', attempt=attempts, pid=child.pid, command=command,
                          resume_step=ckpt.verify(checkpoint)['step'] if checkpoint else 0)
                    while child.poll() is None:
                        if not stopped and time.monotonic() >= allocation_deadline:
                            event(root, 'deadline_exceeded')
                            stop(signal.SIGTERM, None)
                        if stopped:
                            try:
                                child.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                os.killpg(child.pid, signal.SIGKILL)
                            break
                        time.sleep(.05)
                    rc = child.wait()
                event(root, 'attempt_exited', attempt=attempts, returncode=rc)
                if stopped:
                    event(root, 'cancelled', signal=stopped[0])
                    return 128 + stopped[0]
                if rc == 0:
                    event(root, 'succeeded', attempts=attempts)
                    return 0
                if rc not in spec['restart']['exit_codes'] or attempts > spec['restart']['max_restarts']:
                    event(root, 'failed', reason='Exit code not retryable or restart budget exhausted', returncode=rc)
                    return 1
                deadline = time.monotonic() + spec['restart']['backoff_seconds']
                while not stopped and time.monotonic() < deadline:
                    time.sleep(.05)
            event(root, 'failed', reason='Restart budget exhausted')
            return 1
        finally:
            for sig, handler in old.items():
                signal.signal(sig, handler)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path)
    p.add_argument('--run-dir', type=Path)
    p.add_argument('--validate', action='store_true')
    a = p.parse_args()
    try:
        if a.validate:
            spec, _, identity = admit(a.package)
            print(json.dumps({'status': 'valid', 'job_id': spec['job_id'], 'identity_sha256': ckpt.config_hash(identity)}))
            return 0
        if not a.run_dir:
            p.error('--run-dir required unless --validate')
        return run(a.package, a.run_dir)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
