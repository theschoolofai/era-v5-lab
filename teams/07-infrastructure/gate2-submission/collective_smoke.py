"""Small bounded distributed check, not model training (Gloo CPU or NCCL GPU)."""
import argparse
import datetime
import os
import torch
import torch.distributed as dist

parser = argparse.ArgumentParser()
parser.add_argument('--backend', choices=('gloo', 'nccl'), required=True)
args = parser.parse_args()
device = torch.device('cpu')
if args.backend == 'nccl':
    device = torch.device('cuda', int(os.environ['LOCAL_RANK']))
    torch.cuda.set_device(device)
dist.init_process_group(args.backend, timeout=datetime.timedelta(seconds=90))
try:
    tensor = torch.tensor([dist.get_rank() + 1.0], device=device)
    dist.all_reduce(tensor)
    expected = dist.get_world_size() * (dist.get_world_size() + 1) / 2
    if tensor.item() != expected:
        raise RuntimeError(f'all_reduce got {tensor.item()}, expected {expected}')
    print(f'[PASS] backend={args.backend} rank={dist.get_rank()} world={dist.get_world_size()} sum={tensor.item()}', flush=True)
finally:
    dist.destroy_process_group()
