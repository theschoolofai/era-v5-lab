#!/usr/bin/env bash
# Sourced by submit and compute-node scripts; use absolute shared host paths.
export DOCKER_IMAGE=${DOCKER_IMAGE:-ghcr.io/murthyap63-a11y/team7-h100-env:latest}
export TEAM7_MODE=${TEAM7_MODE:-train}
export TRAIN_ENTRY=${TRAIN_ENTRY:-train_moe.py}
export TRAIN_CONFIG=${TRAIN_CONFIG:-configs/config_v1.yaml}
export TRAIN_DIR=${TRAIN_DIR:-}
export DATA_DIR=${DATA_DIR:-}
export CHECKPOINT_DIR=${CHECKPOINT_DIR:-}
export LOG_DIR=${LOG_DIR:-$INFRA_DIR/logs}

fail() { echo "[ERROR] $*" >&2; exit 2; }
absolute_dir() {
    [[ $1 == /* && -d $1 && -r $1 && -x $1 && $1 != *','* && $1 != *$'\n'* ]] || fail "Expected readable absolute directory without comma/newline: $1"
}
validate_paths() {
    [[ $TEAM7_MODE == train || $TEAM7_MODE == preflight ]] || fail 'TEAM7_MODE must be train or preflight'
    [[ -n $DOCKER_IMAGE && $DOCKER_IMAGE != -* && $DOCKER_IMAGE != *[[:space:]]* ]] || fail 'Invalid DOCKER_IMAGE'
    absolute_dir "$INFRA_DIR"
    local file
    for file in settings.sh run_container.sh container_entry.sh gpu_health.sh collective_smoke.py gpu_allocation.py; do
        [[ -r $INFRA_DIR/$file ]] || fail "Missing infrastructure helper: $file"
    done
    [[ $LOG_DIR == /* && $LOG_DIR != *'%'* && $LOG_DIR != *$'\n'* ]] || fail 'LOG_DIR must be absolute, without percent/newline'
    if [[ $TEAM7_MODE == train ]]; then
        [[ -n $TRAIN_DIR && -n $DATA_DIR && -n $CHECKPOINT_DIR ]] || fail 'Set TRAIN_DIR, DATA_DIR and CHECKPOINT_DIR to existing shared directories. Training code is not included.'
        absolute_dir "$TRAIN_DIR"; absolute_dir "$DATA_DIR"; absolute_dir "$CHECKPOINT_DIR"
        [[ -w $CHECKPOINT_DIR ]] || fail 'CHECKPOINT_DIR is not writable'
        command -v python3 >/dev/null || fail 'python3 required on submit and compute hosts'
        local path
        for path in "$TRAIN_ENTRY" "$TRAIN_CONFIG"; do
            [[ -n $path && $path != -* && $path != /* && /$path/ != *'/../'* && /$path/ != *'/./'* && -s $TRAIN_DIR/$path && -f $TRAIN_DIR/$path && -r $TRAIN_DIR/$path ]] || fail "Missing/invalid/empty training file: $TRAIN_DIR/$path"
        done
        python3 - <<'CHECK'
import os
from pathlib import Path
root = Path(os.environ['TRAIN_DIR']).resolve()
for key in ('TRAIN_ENTRY', 'TRAIN_CONFIG'):
    path = (root / os.environ[key]).resolve()
    if root not in path.parents:
        raise SystemExit(f'[ERROR] {key} escapes TRAIN_DIR through a symlink: {path}')
CHECK
    fi
}
