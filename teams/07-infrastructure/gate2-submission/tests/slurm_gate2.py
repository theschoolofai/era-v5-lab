"""Host-side real tests on the existing Docker Slurm CPU demo (no cluster changes)."""
import argparse
import datetime
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CONTROLLER = 'slurmctld'


def command(*args):
    result = subprocess.run(['docker','exec',CONTROLLER,*args],capture_output=True,text=True,check=True)
    return result.stdout.strip()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--python',default='/data/team7-gate2-py312/bin/python')
    a=p.parse_args()
    out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):
        p.error('Output must be empty')
    if command('squeue','-h'):
        raise RuntimeError('Existing jobs present; rerun when demo is idle')
    nodes=command('sinfo','-h','-N','-p','cpu','-o','%N|%T').splitlines()
    if len(nodes)!=2 or any(s.split('|')[-1]!='idle' for s in nodes):
        raise RuntimeError('Expected two healthy idle CPU demo nodes; inspect before resuming')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    base='/data/team7-gate2-'+stamp
    command('mkdir','-p',base+'/infra')
    with tempfile.TemporaryDirectory() as tmp:
        archive=Path(tmp)/'source.tar'
        with tarfile.open(archive,'w') as tf:
            for path in sorted(ROOT.rglob('*')):
                rel=path.relative_to(ROOT)
                if path.is_file() and not any(s in ('.git','__pycache__','logs','evidence') for s in rel.parts):
                    tf.add(path,arcname=str(rel),recursive=False)
        subprocess.run(['docker','cp',str(archive),CONTROLLER+':'+base+'/source.tar'],check=True)
    command('tar','xf',base+'/source.tar','-C',base+'/infra')
    command('chown','-R','user1:user1',base)
    def user(*args):
        return command('runuser','-u','user1','--',*args)
    jobs=[]
    transcript=[]
    def wait(job):
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            accounting=command('sacct','-nP','-X','-j',job,'--format=JobID,User,State,ExitCode,NodeList')
            if '|COMPLETED|0:0|' in accounting:
                transcript.append(accounting)
                print(accounting,flush=True)
                return
            if any('|'+state+'|' in accounting for state in ('FAILED','CANCELLED','TIMEOUT','NODE_FAIL','OUT_OF_MEMORY')):
                raise RuntimeError(accounting)
            time.sleep(1)
        raise RuntimeError('Slurm test timed out: '+job)
    try:
        user('mkdir','-p',base+'/package-run')
        job=user(a.python,base+'/infra/tsai_submit.py',base+'/infra/examples/gate2_job.json','--run-dir',base+'/package-run').split(';')[0]
        if not job.isdigit():
            raise RuntimeError(job)
        jobs.append(job)
        wait(job)
        validator_cmd=shlex.join([a.python,base+'/infra/tests/gate2_validate.py','--output',base+'/gate2'])
        job=user('sbatch','--parsable','--partition=cpu','--nodes=1','--ntasks=1','--cpus-per-task=1','--mem=2048M','--time=5',
                 '--job-name=team7_gate2_acceptance','--chdir='+base+'/infra','--output='+base+'/validation_%j.out',
                 '--error='+base+'/validation_%j.err','--wrap=exec '+validator_cmd).split(';')[0]
        jobs.append(job)
        wait(job)
        summary=json.loads(command('cat',base+'/gate2/summary.json'))
        assert summary['status']=='PASS'
        env=command(a.python,'-m','pip','freeze')
        (out/'linux-requirements.txt').write_text(env+'\n')
        (out/'slurm_accounting.txt').write_text('\n'.join(transcript)+'\n')
        subprocess.run(['docker','cp',CONTROLLER+':'+base+'/.',str(out)],check=True)
        (out/'slurm_metadata.json').write_text(json.dumps({'jobs':jobs,'shared_path':base,'controller':CONTROLLER,
                'python':a.python,'slurm_version':command('scontrol','--version'),'scope':'Local Linux ARM64 CPU containers; worker SIGKILL inside a live allocation, not node/allocation recovery.'},indent=2)+'\n')
        print(json.dumps({'status':'PASS','jobs':jobs,'shared_path':base,'output':str(out)}),flush=True)
    finally:
        if jobs:
            subprocess.run(['docker','exec',CONTROLLER,'scancel',*jobs],capture_output=True)


if __name__=='__main__':
    main()
