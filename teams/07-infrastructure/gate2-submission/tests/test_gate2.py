"""Checkpoint integrity, package admission and bounded restart regression tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import torch
import ckpt
import tsai_runner


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.model=torch.nn.Linear(2,1)
        self.optimizer=torch.optim.Adam(self.model.parameters())
        self.config={'seed':1}

    def save(self,step):
        return ckpt.save(self.root,self.model,self.optimizer,None,step=step,sampler_cursor=step*8,
                         sampler_state={'cursor':step*8},config=self.config)

    def test_publish_is_atomic_and_validated(self):
        rename=ckpt.os.rename
        def observed(src,dst):
            self.assertFalse(list(self.root.glob('step-*')))
            self.assertTrue((Path(src)/'COMPLETE').is_file())
            rename(src,dst)
        with patch.object(ckpt.os,'rename',observed):
            path=self.save(100)
        self.assertEqual(ckpt.verify(path)['step'],100)
        meta=ckpt.load(path,self.model,self.optimizer,None,expected_config=self.config)
        self.assertEqual(meta['sampler_state'],{'cursor':800})
        with self.assertRaises(FileExistsError):
            self.save(100)

    def test_failed_save_never_publishes(self):
        def broken(state,stream):
            stream.write(b'partial')
            raise OSError('simulated disk full')
        with patch.object(ckpt.torch,'save',broken),self.assertRaises(OSError):
            self.save(100)
        self.assertEqual(list(self.root.iterdir()),[])

    def test_incomplete_corrupt_and_malformed_state_skipped(self):
        good=self.save(100)
        incomplete=self.save(110)
        (incomplete/'COMPLETE').unlink()
        corrupt=self.save(120)
        (corrupt/'state.pt').write_bytes(b'bad')
        malformed=self.save(130)
        torch.save({'step':130},malformed/'state.pt')
        manifest=json.loads((malformed/'manifest.json').read_text())
        manifest.update(size=(malformed/'state.pt').stat().st_size,sha256=ckpt.digest(malformed/'state.pt'))
        (malformed/'manifest.json').write_text(json.dumps(manifest))
        (malformed/'COMPLETE').write_text(ckpt.digest(malformed/'manifest.json'))
        rejected=[]
        self.assertEqual(ckpt.latest_complete(self.root,rejected=rejected),good)
        self.assertEqual(len(rejected),3)

    def test_no_valid_checkpoint_and_foreign_config_fail(self):
        with self.assertRaises(FileNotFoundError):
            ckpt.latest_complete(self.root)
        path=self.save(100)
        with self.assertRaises(ValueError):
            ckpt.latest_complete(self.root,expected_config={'seed':2})
        with self.assertRaises(ValueError):
            ckpt.load(path,self.model,self.optimizer,None,expected_config={'seed':2})

    def test_stale_lock_and_distributed_are_refused(self):
        (self.root/'.step-00000100.lock').mkdir()
        with self.assertRaises(FileExistsError):
            self.save(100)
        with patch.object(torch.distributed,'is_initialized',return_value=True),patch.object(torch.distributed,'get_world_size',return_value=8),self.assertRaises(RuntimeError):
            self.save(200)

    def test_symlink_checkpoint_excluded(self):
        path=self.save(100)
        (self.root/'step-00000200').symlink_to(path,target_is_directory=True)
        self.assertEqual(ckpt.latest_complete(self.root),path)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.spec=json.loads((ROOT/'examples/gate2_job.json').read_text())
        self.package=self.root/'package.json'

    def write(self):
        self.package.write_text(json.dumps(self.spec))

    def invoke(self):
        self.write()
        return subprocess.run([sys.executable,str(ROOT/'tsai_runner.py'),str(self.package),'--run-dir',str(self.root/'run')],capture_output=True,text=True,timeout=45)

    def fixture(self,mode):
        self.spec['command']=['{python}','{repo}/tests/restart_fixture.py','--config','{config}',
                              '--run-dir','{run_dir}','--resume','{resume}','--mode',mode]
        self.spec['code'].append('tests/restart_fixture.py')
        self.spec['restart']['max_restarts']=1

    def events(self):
        return [json.loads(s) for s in (self.root/'run/events.jsonl').read_text().splitlines()]

    def test_budget_is_bounded_and_persisted(self):
        self.fixture('temporary')
        self.assertEqual(self.invoke().returncode,1)
        self.assertEqual(len([e for e in self.events() if e['event']=='attempt_started']),2)
        self.assertEqual(self.invoke().returncode,1)
        self.assertEqual(len([e for e in self.events() if e['event']=='attempt_started']),2)

    def test_no_checkpoint_refuses_restart_from_scratch(self):
        self.fixture('no-checkpoint')
        self.assertEqual(self.invoke().returncode,1)
        self.assertEqual(len([e for e in self.events() if e['event']=='attempt_started']),1)
        self.assertIn('No valid COMPLETE',self.events()[-1]['reason'])

    def test_fatal_exit_is_not_retried(self):
        self.fixture('fatal')
        self.assertEqual(self.invoke().returncode,1)
        self.assertEqual(len([e for e in self.events() if e['event']=='attempt_started']),1)

    def test_changed_identity_refused(self):
        self.fixture('fatal')
        self.invoke()
        self.spec['data']['id']='changed-dataset'
        result=self.invoke()
        self.assertEqual(result.returncode,2)
        self.assertIn('inputs changed',result.stderr)

    def test_bad_resource_placeholder_and_path_are_rejected(self):
        for change in ('gpu','placeholder','path','budget'):
            with self.subTest(change=change):
                original=json.loads(json.dumps(self.spec))
                if change=='gpu': self.spec['resources']['gpus']=8
                if change=='placeholder': self.spec['command'].append('{unknown}')
                if change=='path': self.spec['config']='../../outside.json'
                if change=='budget': self.spec['restart']['max_restarts']=100
                self.write()
                with self.assertRaises(ValueError):
                    tsai_runner.admit(self.package)
                self.spec=original

    def test_slurm_preview_keeps_cpu_resource_contract(self):
        self.write()
        result=subprocess.run([sys.executable,str(ROOT/'tsai_submit.py'),str(self.package),'--run-dir',str(self.root/'run'),'--dry-run'],capture_output=True,text=True,check=True)
        command=json.loads(result.stdout)
        for flag in ('--no-requeue','--nodes=1','--ntasks=1','--cpus-per-task=1','--mem=2048M','--partition=cpu'):
            self.assertIn(flag,command)
        self.assertNotIn('--gres=gpu:8',command)


if __name__=='__main__':
    unittest.main(verbosity=2)
