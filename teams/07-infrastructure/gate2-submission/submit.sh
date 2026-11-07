#!/usr/bin/env bash
set -Eeuo pipefail
# Explicit options override SBATCH_* environment values for topology/logs.
# Site-specific options (partition/account/QoS/time/memory) may be passed below.
[[ ${1:-} == --dry-run ]] && { dry_run=1; shift; } || dry_run=0
for arg in "$@"; do
    case "$arg" in
        --partition=*|--account=*|--qos=*|--constraint=*|--time=*|--mem=*|--cpus-per-task=*) ;;
        *) echo "Usage: bash submit.sh [--dry-run] [--partition=NAME] [--account=NAME] [--qos=NAME] [--constraint=NAME] [--time=HH:MM:SS] [--mem=SIZE] [--cpus-per-task=N]" >&2; exit 2 ;;
    esac
done
export INFRA_DIR
INFRA_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source "$INFRA_DIR/settings.sh"
validate_paths
# Slurm opens logs before the batch script starts. Never defer mkdir to launch.sh.
mkdir -p -- "$LOG_DIR"
[[ -w $LOG_DIR && -x $LOG_DIR ]] || fail 'LOG_DIR is not writable/searchable'
cmd=(sbatch --parsable --export=ALL --nodes=1 --ntasks=1 --ntasks-per-node=1 --exclusive
    --chdir="$INFRA_DIR" --output="$LOG_DIR/train_%j.log" --error="$LOG_DIR/train_%j.err")
if [[ $dry_run == 1 ]]; then
    printf ' %q' "${cmd[@]}" "$@" "$INFRA_DIR/launch.sh"; printf '\n'
    echo "mode=$TEAM7_MODE image=$DOCKER_IMAGE; 1 Slurm task -> 1 container -> 8 workers"
    echo 'Preview only: compute-node GPU/runtime checks have not run.'
    exit 0
fi
command -v sbatch >/dev/null || fail 'sbatch unavailable: submit from a Slurm login host; Mac tests use tests/cpu_smoke.py.'
exec "${cmd[@]}" "$@" "$INFRA_DIR/launch.sh"
