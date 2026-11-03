"""CPU-safe regression tests. Stubbed GPU/Docker calls are not H100 validation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import signal
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gpu_allocation import resolve
from xid_scan import critical_xids


class InfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(('SLURM_', 'SBATCH_', 'TRAIN_', 'TEAM7_', 'DOCKER_', 'DATA_DIR', 'CHECKPOINT_DIR', 'LOG_DIR'))}
        self.env.update(INFRA_DIR=str(ROOT), LOG_DIR=str(self.path / 'logs'))

    def run_script(self, name, *args):
        return subprocess.run(['bash', str(ROOT / name), *args], env=self.env, text=True, capture_output=True)

    def stub(self, name, body):
        path = self.path / name
        path.write_text('#!' + sys.executable + '\n' + body)
        path.chmod(0o755)
        self.env['PATH'] = str(self.path) + os.pathsep + os.environ['PATH']

    def test_shell_syntax(self):
        for path in ROOT.glob('*.sh'):
            subprocess.run(['bash', '-n', str(path)], check=True)

    def test_no_allocation(self):
        result = self.run_script('launch.sh')
        self.assertEqual(result.returncode, 2)
        self.assertIn('submit.sh', result.stderr)

    def test_missing_training_blocks_submission(self):
        result = self.run_script('submit.sh', '--dry-run')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Training code is not included', result.stderr)
        self.env.update(TRAIN_DIR=str(self.path), DATA_DIR=str(self.path), CHECKPOINT_DIR=str(self.path))
        result = self.run_script('submit.sh', '--dry-run')
        self.assertEqual(result.returncode, 2)
        self.assertIn('train_moe.py', result.stderr)

    def test_preflight_preview_creates_logs_without_sbatch(self):
        self.env['TEAM7_MODE'] = 'preflight'
        result = self.run_script('submit.sh', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.path / 'logs').is_dir())
        self.assertIn('ghcr.io/murthyap63-a11y/team7-h100-env:latest', result.stdout)

    def test_one_srun_and_failure_propagation(self):
        self.stub('srun', 'import json, os, sys\nopen(os.environ["CALLS"], "w").write(json.dumps(sys.argv[1:]))\nsys.exit(17)\n')
        self.env.update(SLURM_JOB_ID='999', SLURM_NNODES='1', SLURM_NTASKS='1', CALLS=str(self.path / 'calls'))
        result = self.run_script('launch.sh')
        self.assertEqual(result.returncode, 17)
        args = json.loads((self.path / 'calls').read_text())
        self.assertIn('--ntasks=1', args)
        self.assertNotIn('[SUCCESS]', result.stdout)
        self.env['SLURM_NTASKS'] = '8'
        self.assertEqual(self.run_script('launch.sh').returncode, 2)

    def test_gpu_mapping_rejects_missing_duplicate_alias_and_wrong_hardware(self):
        rows = [[str(i), f'GPU-{i}', 'NVIDIA H100 80GB HBM3', 'Disabled'] for i in range(8)]
        ids = ','.join(str(i) for i in range(8))
        self.assertEqual(resolve(ids, rows), ','.join(f'GPU-{i}' for i in range(8)))
        for invalid in ('', '0,1', '0,0,1,2,3,4,5,6', '0,GPU-0,2,3,4,5,6,7', '0,1,2,3,4,5,6,9'):
            with self.assertRaises(ValueError):
                resolve(invalid, rows)
        rows[0][3] = 'Enabled'
        with self.assertRaises(ValueError):
            resolve(ids, rows)
        rows[0][3] = 'Disabled'
        rows[0][2] = 'NVIDIA A100'
        with self.assertRaises(ValueError):
            resolve(ids, rows)

    def container_fixture(self):
        self.stub('python3', 'import os, sys\nif sys.argv[1] == \"-c\": print(\"0,1,2,3,4,5,6,7\")\nelse: os.execv(sys.executable, [sys.executable, *sys.argv[1:]])\n')
        self.stub('uname', 'import sys\nprint("Linux" if sys.argv[1] == "-s" else "x86_64")\n')
        self.stub('nvidia-smi', 'print("\\n".join(f"{i}, GPU-{i}, NVIDIA H100, Disabled" for i in range(8)))\n')
        self.stub('docker', '''import json, os, sys
args = sys.argv[1:]
if args[0] == '--host': args = args[2:]
with open(os.environ['CALLS'], 'a') as stream:
    stream.write(json.dumps(args) + '\\n')
if args[0] == 'context': print('unix:///var/run/docker.sock')
if args[0] == 'info': print('linux')
if args[:2] == ['image', 'inspect']:
    print('linux/amd64' if args[-1] == '{{.Os}}/{{.Architecture}}' else 'sha256:test-image')
if args[0] == 'run': sys.exit(23)
''')
        # Only test fixtures in a temporary folder; no functional trainer is created.
        (self.path / 'train_moe.py').write_text('# temporary CLI fixture\n')
        (self.path / 'configs').mkdir()
        (self.path / 'configs/config_v1.yaml').write_text('# temporary path fixture\n')
        self.env.update(SLURM_NNODES='1', SLURM_NTASKS='1', SLURM_MEM_PER_NODE='131072', SLURM_JOB_ID='999', SLURM_JOB_GPUS='0,1,2,3,4,5,6,7', SLURM_CPUS_PER_TASK='32', TRAIN_DIR=str(self.path), DATA_DIR=str(self.path), CHECKPOINT_DIR=str(self.path), CALLS=str(self.path / 'calls'))

    def test_container_arguments_and_failure(self):
        self.container_fixture()
        result = self.run_script('run_container.sh')
        self.assertEqual(result.returncode, 23, result.stderr)
        calls = [json.loads(line) for line in (self.path / 'calls').read_text().splitlines()]
        runs = [args for args in calls if args[0] == 'run']
        self.assertEqual(len(runs), 1)
        args = runs[0]
        self.assertEqual(args[args.index('--gpus') + 1], '"device=GPU-0,GPU-1,GPU-2,GPU-3,GPU-4,GPU-5,GPU-6,GPU-7"')
        self.assertIn('sha256:test-image', args)
        self.assertEqual(args[args.index('--memory') + 1], '131072m')
        self.assertEqual(args[args.index('--cpus') + 1], '32')
        self.assertIn('--cpuset-cpus', args)
        self.assertNotIn('--ipc=host', args)
        self.assertNotIn('--network=host', args)
        self.assertTrue(any('dst=/workspace/training,readonly' in arg for arg in args))
        self.assertTrue(any('dst=/workspace/datasets,readonly' in arg for arg in args))
        self.assertTrue(any('dst=/workspace/checkpoints' in arg for arg in args))
        self.assertFalse(any('WORLD_SIZE=' in arg for arg in args))
        self.assertTrue(any(call[0] == 'stop' for call in calls))
        self.env['DOCKER_HOST'] = 'tcp://remote:2375'
        self.assertEqual(self.run_script('run_container.sh').returncode, 2)

    def test_step_gpu_allocation_overrides_job_allocation(self):
        self.container_fixture()
        self.env['SLURM_STEP_GPUS'] = '0,1'
        result = self.run_script('run_container.sh')
        self.assertEqual(result.returncode, 1)
        self.assertIn('eight distinct', result.stderr)
        calls = (self.path / 'calls').read_text()
        self.assertNotIn('"run"', calls)

    def test_memory_and_topology_rejected_before_docker_run(self):
        self.container_fixture()
        for updates in ({'SLURM_MEM_PER_NODE': '0'}, {'SLURM_MEM_PER_NODE': 'unknown'}, {'SLURM_CPUS_PER_TASK': '4'}, {'SLURM_NTASKS': '8'}, {'SLURM_PROCID': '1'}):
            original = self.env.copy()
            self.env.update(updates)
            result = self.run_script('run_container.sh')
            self.assertEqual(result.returncode, 2, result.stderr)
            self.env = original
        self.assertNotIn('"run"', (self.path / 'calls').read_text())

    def test_submit_options_keep_topology_fixed(self):
        self.env.update(TEAM7_MODE='preflight', SBATCH_NTASKS='8')
        result = self.run_script('submit.sh', '--dry-run', '--partition=h100', '--account=team7')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--ntasks=1', result.stdout)
        self.assertIn('--partition=h100', result.stdout)
        self.assertEqual(self.run_script('submit.sh', '--dry-run', '--nodes=2').returncode, 2)
        self.assertEqual(self.run_script('submit.sh', '--dry-run', 'unexpected').returncode, 2)

    def test_term_stops_only_owned_container(self):
        self.container_fixture()
        self.stub('docker', '''import json, os, sys, time
args = sys.argv[1:]
if args[0] == '--host': args = args[2:]
with open(os.environ['CALLS'], 'a') as stream: stream.write(json.dumps(args) + '\\n')
if args[0] == 'context': print('unix:///var/run/docker.sock')
if args[0] == 'info': print('linux')
if args[:2] == ['image', 'inspect']: print('linux/amd64' if args[-1] == '{{.Os}}/{{.Architecture}}' else 'sha256:test-image')
if args[0] == 'run':
    open(os.environ['READY'], 'w').write(str(os.getpid()))
    time.sleep(20)
if args[0] == 'stop':
    import signal
    os.kill(int(open(os.environ['READY']).read()), signal.SIGTERM)
''')
        self.env['READY'] = str(self.path / 'ready')
        proc = subprocess.Popen(['bash', str(ROOT / 'run_container.sh')], env=self.env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 10
            while not (self.path / 'ready').exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue((self.path / 'ready').exists())
            proc.send_signal(signal.SIGTERM)
            out, err = proc.communicate(timeout=10)
            self.assertEqual(proc.returncode, 143, err)
            calls = [json.loads(line) for line in (self.path / 'calls').read_text().splitlines()]
            run = next(args for args in calls if args[0] == 'run')
            stop = next(args for args in calls if args[0] == 'stop')
            self.assertEqual(stop[-1], run[run.index('--name') + 1])
            self.assertNotIn('[SUCCESS]', out)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()

    def test_training_path_must_stay_inside_mount(self):
        self.env.update(TRAIN_DIR=str(self.path), DATA_DIR=str(self.path), CHECKPOINT_DIR=str(self.path))
        (self.path / 'train_moe.py').write_text('# fixture, not training\n')
        outside = self.path / 'outside.yaml'
        outside.write_text('fixture: true\n')
        (self.path / 'config.yaml').symlink_to('/etc/hosts')
        self.env['TRAIN_CONFIG'] = 'config.yaml'
        result = self.run_script('submit.sh', '--dry-run')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('escapes TRAIN_DIR', result.stderr)
        self.env['TRAIN_CONFIG'] = '../outside.yaml'
        self.assertEqual(self.run_script('submit.sh', '--dry-run').returncode, 2)

    def test_batch_term_forwards_to_srun(self):
        self.stub('srun', '''import os, signal, time, sys
open(os.environ['READY'], 'w').write('ready')
def stop(*args):
    open(os.environ['SIGNALLED'], 'w').write('TERM')
    sys.exit(143)
signal.signal(signal.SIGTERM, stop)
time.sleep(20)
''')
        self.env.update(SLURM_JOB_ID='999', SLURM_NNODES='1', SLURM_NTASKS='1', READY=str(self.path/'ready'), SIGNALLED=str(self.path/'signalled'))
        proc = subprocess.Popen(['bash', str(ROOT / 'launch.sh')], env=self.env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 10
            while not (self.path / 'ready').exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue((self.path / 'ready').exists())
            proc.send_signal(signal.SIGTERM)
            out, err = proc.communicate(timeout=10)
            self.assertEqual(proc.returncode, 143, err)
            self.assertEqual((self.path / 'signalled').read_text(), 'TERM')
            self.assertNotIn('[SUCCESS]', out)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()

    def test_xid_real_kernel_format(self):
        self.assertEqual(critical_xids('NVRM: Xid (PCI:0000:01:00): 79, pid=0, GPU fallen off bus'), [79])
        self.assertEqual(critical_xids('NVRM: Xid (PCI:0000:01:00): 790, pid=0'), [])
        self.assertEqual(critical_xids('NVRM: Xid: 31, process abc'), [31])
        self.assertEqual(critical_xids('normal log'), [])

    def test_ecc_failures(self):
        self.stub('nvidia-smi', 'import os, sys\nprint(os.environ["ECC"] if any("uncorrected" in s for s in sys.argv) else "GPU inventory stub")\n')
        for value in ('1', '[N/A]', ''):
            self.env['ECC'] = value
            result = self.run_script('gpu_health.sh')
            self.assertEqual(result.returncode, 1)
            self.assertIn('Uncorrected ECC', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
