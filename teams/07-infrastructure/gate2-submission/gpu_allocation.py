"""Resolve only Slurm's eight allocated physical H100 GPUs to Docker UUIDs."""
import os
import subprocess


def resolve(ids, inventory):
    tokens = ids.split(',') if ids else []
    if len(tokens) != 8 or len(set(tokens)) != 8:
        raise ValueError('SLURM_JOB_GPUS must contain eight distinct global GPU indices or full GPU UUIDs; ask the cluster operator if unavailable')
    selected = []
    for token in tokens:
        matches = [row for row in inventory if len(row) == 4 and token in (row[0], row[1])]
        if len(matches) != 1 or 'H100' not in matches[0][2] or not matches[0][1].startswith('GPU-') or matches[0][3] != 'Disabled':
            raise ValueError(f'Allocated GPU {token!r} is not an identifiable physical H100 with MIG disabled')
        selected.append(matches[0][1])
    if len(set(selected)) != 8:
        raise ValueError('GPU aliases resolved to duplicate UUIDs')
    return ','.join(selected)


if __name__ == '__main__':
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=index,uuid,name,mig.mode.current', '--format=csv,noheader,nounits'], check=True, capture_output=True, text=True)
        rows = [[field.strip() for field in row.split(',')] for row in result.stdout.splitlines()]
        print(resolve(os.environ.get('TEAM7_GPU_IDS', ''), rows))
    except (ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'[ERROR] GPU allocation validation: {exc}')
