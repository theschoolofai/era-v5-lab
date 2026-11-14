"""Submit a validated TSAI v1 CPU package to Slurm using shared absolute paths."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from tsai_runner import ROOT, admit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('package', type=Path)
    p.add_argument('--run-dir', required=True, type=Path)
    p.add_argument('--dry-run', action='store_true')
    a = p.parse_args()
    try:
        spec, _, _ = admit(a.package)
        run = a.run_dir.resolve()
        run.mkdir(parents=True, exist_ok=True)
        r = spec['resources']
        args = ['sbatch', '--parsable', '--export=NONE', '--no-requeue', '--nodes=1', '--ntasks=1',
                f'--cpus-per-task={r["cpus"]}', f'--mem={r["memory_mb"]}M', f'--time={r["time_minutes"]}',
                f'--partition={r["partition"]}', f'--job-name={spec["job_id"]}', f'--chdir={ROOT}',
                f'--output={run}/slurm_%j.out', f'--error={run}/slurm_%j.err',
                str(ROOT/'tsai_batch.sh'), sys.executable, str(ROOT), str(a.package.resolve()), str(run)]
        if a.dry_run:
            print(json.dumps(args))
        else:
            subprocess.run(args, check=True)
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
