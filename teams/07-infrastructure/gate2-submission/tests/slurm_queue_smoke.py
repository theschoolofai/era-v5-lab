"""Run on the Mac against the EXISTING CPU cluster; never submits a GPU job.
Requires user1/user2 UIDs to match across controller/workers and two idle nodes.
Creates only its own jobs and output directories; cancels only its own jobs on error.
"""
import datetime
from pathlib import Path
import subprocess
import time

CONTROLLER = 'slurmctld'

def command(*args):
    result = subprocess.run(['docker', 'exec', CONTROLLER, *args], check=True, capture_output=True, text=True)
    if result.stderr:
        print(result.stderr, end='', flush=True)
    return result.stdout.strip()

def as_user(user, *args):
    return command('runuser', '-u', user, '--', *args)

def state(job):
    return command('squeue', '-h', '-j', job, '-o', '%T|%r')

def wait_for(predicate, label, seconds=75):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(1)
    raise RuntimeError('Timed out: ' + label)

jobs = []
try:
    print(command('scontrol', 'ping'), flush=True)
    if command('squeue', '-h'):
        raise RuntimeError('Existing jobs present; leave them alone and rerun when idle')
    print(command('sinfo', '-Nel'), flush=True)
    nodes = command('sinfo', '-h', '-N', '-p', 'cpu', '-o', '%N|%T').splitlines()
    if len(nodes) != 2 or any(line.split('|')[-1] != 'idle' for line in nodes):
        raise RuntimeError('Requires exactly two responsive idle CPU nodes; inspect state/reason before changing anything')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    base = '/data/team7-smoke-' + stamp
    print('Queue test outputs: ' + base, flush=True)
    command('mkdir', '-p', base)
    for user in ('user1', 'user2'):
        command('install', '-d', '-m', '755', '-o', user, '-g', user, base + '/' + user)
    first = as_user('user1', 'sbatch', '--parsable', '--partition=cpu', '--nodes=2', '--ntasks=2', '--ntasks-per-node=1', '--exclusive', '--time=00:02:00', '--job-name=team7_cpu_user1', '--chdir=' + base + '/user1', '--output=' + base + '/user1/%j.out', '--wrap=srun --ntasks=2 bash -c \'id -un; hostname; sleep 30\'').split(';')[0]
    jobs.append(first)
    wait_for(lambda: state(first).startswith('RUNNING'), 'user1 running')
    print('user1 job=' + first + ' ' + state(first), flush=True)
    second = as_user('user2', 'sbatch', '--parsable', '--partition=cpu', '--nodes=1', '--ntasks=1', '--time=00:01:00', '--job-name=team7_cpu_user2', '--chdir=' + base + '/user2', '--output=' + base + '/user2/%j.out', '--wrap=id -un; hostname; echo QUEUE_SMOKE_DONE').split(';')[0]
    jobs.append(second)
    pending = wait_for(lambda: state(second) if state(second).startswith('PENDING') else '', 'user2 queued')
    print('user2 job=' + second + ' ' + pending, flush=True)
    print(command('squeue', '-j', first + ',' + second, '-o', '%.12i %.10u %.12T %.20R'), flush=True)
    wait_for(lambda: not state(first) and not state(second), 'both jobs finish', seconds=90)
    for job, user in ((first, 'user1'), (second, 'user2')):
        def terminal_accounting():
            row = command('sacct', '-nP', '-X', '-j', job, '--format=JobID,User,State,ExitCode,NodeList')
            fields = row.split('|')
            return row if len(fields) >= 4 and fields[2] not in ('PENDING', 'RUNNING', 'COMPLETING') else ''
        accounting = wait_for(terminal_accounting, 'terminal accounting')
        print(accounting, flush=True)
        if '|COMPLETED|0:0|' not in accounting:
            raise RuntimeError('CPU job failed: ' + accounting)
        output = command('cat', base + '/' + user + '/' + job + '.out')
        print(user + ' output:\n' + output, flush=True)
        if user not in output.splitlines():
            raise RuntimeError('Worker identity mismatch')
        if user == 'user2' and 'QUEUE_SMOKE_DONE' not in output:
            raise RuntimeError('Queued job did not execute')
    print('[PASS] user1 occupied both CPU nodes, user2 queued, then completed after resources freed. This does not test CUDA, training, fair-share or account limits.', flush=True)
finally:
    if jobs:
        subprocess.run(['docker', 'exec', CONTROLLER, 'scancel', *jobs], capture_output=True)
