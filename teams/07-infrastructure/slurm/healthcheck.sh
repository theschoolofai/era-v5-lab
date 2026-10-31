#!/bin/bash
# Slurm HealthCheckProgram: runs every HealthCheckInterval on every node (ADR 0003).
# Slurm ignores this script's exit code, so health_check.py drains the node itself on "fail" and asks
# the jobs on it to save and stop (they exit 75 and requeue onto a healthy node).
# Slurm starts this with a bare environment: without a full PATH, nvidia-smi/dcgmi in /usr/local/bin are
# "not found" and the GPU checks report skipped instead of failing (found in the Docker drill health_fakes).
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH:+:$PATH}"
source /etc/v5/node.env 2>/dev/null || true
export V5_EVENTS_DIR="${V5_EVENTS_DIR:-/var/log/v5/events}"
/opt/venv/bin/python /opt/v5/health/health_check.py --mode periodic > /var/log/slurm/health-last.json 2>&1
exit 0
