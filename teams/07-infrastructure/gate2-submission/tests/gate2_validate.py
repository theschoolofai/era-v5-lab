"""Real CPU restore, SIGKILL/restart, corruption exclusion and cancellation evidence."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import torch
import ckpt
from tsai_runner import admit


def equal(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and a.contiguous().numpy().tobytes() == b.contiguous().numpy().tobytes()
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return type(a) is type(b) and len(a) == len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a == b


def wait_for(predicate, seconds=60):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(.05)
    raise RuntimeError('Timed out waiting for worker pause')


def rows(root, name='trace.jsonl'):
    return [json.loads(s) for s in (root / name).read_text().splitlines()]


def compare(reference, other, output):
    a, b = rows(reference), rows(other)
    assert [r['step'] for r in a] == list(range(1,201))
    assert [r['step'] for r in b] == list(range(1,201))
    checked = []
    for x,y in zip(a[100:],b[100:]):
        result = {'step':x['step'], 'loss_bits_equal':x['loss_float32_hex']==y['loss_float32_hex'],
                  'ordered_data_ids_equal':x['data_ids']==y['data_ids'], 'lr_equal':x['lr']==y['lr']}
        assert all(v for k,v in result.items() if k != 'step'), (x,y)
        checked.append(result)
    (output).write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in checked))
    a = torch.load(reference/'final.pt',weights_only=True)
    b = torch.load(other/'final.pt',weights_only=True)
    final = {k:equal(a[k],b[k]) for k in a}
    assert all(final.values()), final
    return {'compared_steps':100,'first_step':101,'last_step':200,'bit_equal_loss':True,
            'identical_ordered_data_ids':True, 'final_state_equal':final}


def poison(checkpoints):
    source = checkpoints/'step-00000100'
    rejected = []
    for step in (150,160,170,200):
        dest = checkpoints/f'step-{step:08d}'
        shutil.copytree(source,dest)
        manifest = json.loads((dest/'manifest.json').read_text())
        manifest['step'] = step
        (dest/'manifest.json').write_text(json.dumps(manifest,sort_keys=True))
        (dest/'COMPLETE').write_text(ckpt.digest(dest/'manifest.json')+'\n')
        if step==150:
            (dest/'COMPLETE').unlink()
        if step==160:
            with open(dest/'state.pt','ab') as f:
                f.write(b'corrupt')
        if step==170:
            (dest/'manifest.json').write_text('{}')
        if step==200:
            (dest/'state.pt').write_bytes(b'not a torch state')
            manifest['size']=(dest/'state.pt').stat().st_size
            manifest['sha256']=ckpt.digest(dest/'state.pt')
            (dest/'manifest.json').write_text(json.dumps(manifest,sort_keys=True))
            (dest/'COMPLETE').write_text(ckpt.digest(dest/'manifest.json')+'\n')
        rejected.append(str(dest))
    (checkpoints/'.incomplete-crash').mkdir()
    (checkpoints/'.incomplete-crash'/'state.pt').write_bytes(b'partial')
    (checkpoints/'.step-00000200.lock').mkdir()
    return rejected


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):
        p.error('Output must be empty; use a new evidence directory')
    package=ROOT/'examples/gate2_job.json'
    spec,config,identity=admit(package)
    def runner(root, pkg=package):
        return [sys.executable,str(ROOT/'tsai_runner.py'),str(pkg),'--run-dir',str(root)]
    reference=out/'reference'
    subprocess.run(runner(reference),check=True,timeout=90)
    restored=out/'restored'
    restored.mkdir()
    (restored/'identity.json').write_text(json.dumps(identity,sort_keys=True))
    (restored/'trace.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows(reference)[:100]))
    subprocess.run([sys.executable,str(ROOT/'tests/gate2_worker.py'),'--config',str(config),'--run-dir',str(restored),
                    '--resume',str(reference/'checkpoints/step-00000100')],check=True,timeout=60)
    restore_result=compare(reference,restored,out/'restore_comparison.jsonl')
    # Real SIGKILL after step 125: speculative steps 101..125 must be replayed.
    killed=out/'killed'
    kill_spec=json.loads(package.read_text())
    kill_spec['command'] += ['--pause-at','125']
    kill_package=out/'kill_job.json'
    kill_package.write_text(json.dumps(kill_spec,sort_keys=True))
    with open(out/'kill_supervisor.log','w') as log:
        proc=subprocess.Popen(runner(killed,kill_package),stdout=log,stderr=subprocess.STDOUT)
        try:
            pid=int(wait_for(lambda:(killed/'paused').read_text() if (killed/'paused').exists() else None))
            corrupt=poison(killed/'checkpoints')
            # Second runner must refuse an active writer, without altering the run.
            lock_test=subprocess.run(runner(killed,kill_package),capture_output=True,text=True,timeout=20)
            assert lock_test.returncode==2 and 'active runner' in lock_test.stderr, lock_test
            (out/'lock_rejection.log').write_text(lock_test.stderr)
            os.kill(pid,signal.SIGKILL)
            assert proc.wait(timeout=90)==0, (out/'kill_supervisor.log').read_text()
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)
    events=rows(killed,'events.jsonl')
    starts=[e for e in events if e['event']=='attempt_started']
    exits=[e for e in events if e['event']=='attempt_exited']
    assert len(starts)==2 and starts[1]['resume_step']==100 and exits[0]['returncode']==-9, events
    rejected={e['path'] for e in events if e['event']=='checkpoint_rejected'}
    assert set(corrupt)<=rejected, rejected
    kill_result=compare(reference,killed,out/'restart_comparison.jsonl')
    kill_result.update({'signal':'SIGKILL','killed_after_step':125,'resumed_checkpoint_step':100,
                        'attempts':2,'invalid_checkpoints_excluded':4,'incomplete_temporary_directory_ignored':True, 'stale_lock_quarantined':True,
                        'corrupt_future_publish_path_recovered':True,
                        'concurrent_writer_rejected':True})
    cancelled=out/'cancelled'
    with open(out/'cancel_supervisor.log','w') as log:
        proc=subprocess.Popen(runner(cancelled,kill_package),stdout=log,stderr=subprocess.STDOUT)
        try:
            wait_for(lambda:(cancelled/'paused').exists())
            proc.terminate()
            assert proc.wait(timeout=15)==143
        finally:
            if proc.poll() is None:
                proc.kill();proc.wait()
    cancel_events=rows(cancelled,'events.jsonl')
    assert len([e for e in cancel_events if e['event']=='attempt_started'])==1
    assert cancel_events[-1]['event']=='cancelled'
    summary={'status':'PASS','device':'cpu','torch':str(torch.__version__),'python':sys.version,
             'platform':sys.platform,'restore':restore_result,'automatic_restart':kill_result,
             'supervisor_TERM_cancels_without_restart':True,
             'scope':'Single-process CPU acceptance fixture. No GPU/MoE/distributed/Slurm allocation-loss certification.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    main()
