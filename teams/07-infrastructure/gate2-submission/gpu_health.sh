#!/usr/bin/env bash
set -Eeuo pipefail
command -v nvidia-smi >/dev/null || { echo '[ERROR] nvidia-smi missing; requires NVIDIA compute node/runtime' >&2; exit 1; }
nvidia-smi --query-gpu=index,uuid,name,temperature.gpu,memory.free,utilization.gpu --format=csv
# Fail on unknown or nonzero uncorrected ECC; corrected counters are inventory only.
ecc=$(nvidia-smi --query-gpu=ecc.errors.uncorrected.volatile.device --format=csv,noheader,nounits)
while IFS= read -r value; do
    value=${value//[[:space:]]/}
    [[ $value == 0 ]] || { echo "[ERROR] Uncorrected ECC counter is nonzero or unknown: $value" >&2; exit 1; }
done <<< "$ecc"
python3 - <<'CHECK'
import os
import torch
expected = int(os.environ.get('TEAM7_EXPECTED_GPUS', '8'))
if not torch.cuda.is_available() or torch.cuda.device_count() != expected:
    raise SystemExit(f'[ERROR] Expected {expected} CUDA GPUs, visible={torch.cuda.device_count()}, available={torch.cuda.is_available()}')
for i in range(expected):
    name = torch.cuda.get_device_name(i)
    if 'H100' not in name:
        raise SystemExit(f'[ERROR] Device {i} is {name}, expected H100')
    with torch.cuda.device(i):
        assert (torch.ones(4, device=f'cuda:{i}') + 1).sum().item() == 8
print('[PASS] H100 inventory, zero uncorrected ECC, and CUDA tensor operations; NCCL tested separately')
CHECK
