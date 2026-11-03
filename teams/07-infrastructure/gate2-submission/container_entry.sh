#!/usr/bin/env bash
set -Eeuo pipefail
[[ ${TEAM7_MODE:-} == train || ${TEAM7_MODE:-} == preflight ]] || { echo '[ERROR] Invalid TEAM7_MODE' >&2; exit 2; }
command -v torchrun >/dev/null || { echo '[ERROR] torchrun missing' >&2; exit 2; }
if [[ $TEAM7_MODE == train ]]; then
    # Check content/path containment without importing or inventing a trainer.
    python3 - <<'CHECK'
import ast
import os
from pathlib import Path
import yaml
root = Path('/workspace/training').resolve()
for key in ('TRAIN_ENTRY', 'TRAIN_CONFIG'):
    path = (root / os.environ[key]).resolve()
    if root not in path.parents or not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f'[ERROR] Invalid training dependency {key}: {path}')
ast.parse((root / os.environ['TRAIN_ENTRY']).read_text())
config = yaml.safe_load((root / os.environ['TRAIN_CONFIG']).read_text())
if not isinstance(config, dict) or not config:
    raise SystemExit('[ERROR] Training config must be a nonempty YAML mapping; model-specific schema still requires its owner')
CHECK
fi
bash /opt/team7-infra/gpu_health.sh
# This exercises NCCL, but does not certify NVLink topology or training correctness.
unset WORLD_SIZE RANK LOCAL_RANK LOCAL_WORLD_SIZE GROUP_RANK ROLE_RANK ROLE_WORLD_SIZE MASTER_ADDR MASTER_PORT
torchrun --standalone --nnodes=1 --nproc-per-node=8 --max-restarts=0 --monitor-interval=5 /opt/team7-infra/collective_smoke.py --backend nccl
[[ $TEAM7_MODE == preflight ]] && { echo '[SUCCESS] GPU preflight and eight-rank NCCL collective passed'; exit 0; }
# Model must implement --config, LOCAL_RANK device selection and distributed init.
exec torchrun --standalone --nnodes=1 --nproc-per-node=8 --max-restarts=0 --monitor-interval=5 "$TRAIN_ENTRY" --config "$TRAIN_CONFIG"
