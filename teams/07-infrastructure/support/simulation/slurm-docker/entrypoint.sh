#!/bin/bash
# Starts one role of the test cluster: slurmdbd | slurmctld | slurmd.
set -euo pipefail
role="${1:?role: s3emu|slurmdbd|slurmctld|slurmd}"

# The S3 emulator (moto): stands in for the S3 bucket, so the real S3 code path (boto3) is tested.
if [[ "$role" == "s3emu" ]]; then
  moto_server -H 0.0.0.0 -p 9000 &
  until python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9000')" 2>/dev/null; do sleep 1; done
  python3 -c "import boto3; boto3.client('s3', endpoint_url='http://127.0.0.1:9000', \
aws_access_key_id='test', aws_secret_access_key='test').create_bucket(Bucket='v5-ckpt')"
  wait
fi

# The munge key is shared through a volume. The controller creates it once; the others wait for it.
if [[ "$role" == "slurmdbd" && ! -s /etc/munge/munge.key ]]; then
  dd if=/dev/urandom of=/etc/munge/munge.key bs=1 count=1024 status=none
fi
until [[ -s /etc/munge/munge.key ]]; do sleep 1; done
chown munge:munge /etc/munge /etc/munge/munge.key && chmod 400 /etc/munge/munge.key
mkdir -p /run/munge && chown munge:munge /run/munge
runuser -u munge -- /usr/sbin/munged --force

# Per-node settings read by the prolog, health check and job scripts (on cloud nodes: written by the node image build).
# On the cloud /var/log/v5 is each node's own disk, shipped to S3 by the log agent (ADR 0002 §7). Here it points at the
# shared volume, which plays the part of that shipped copy, so the drills can read every node's events.
ln -sfn /s3 /var/log/v5
mkdir -p /etc/v5
# GPU nodes (2 placeholder GPUs each) get the fake nvidia-smi and expect 2 GPUs, so the real GPU checks run;
# every node gets the fake dmesg (a container cannot read the kernel log).
gpus=0
case "$(hostname)" in c[1-3]) gpus=2
  install -m 755 /opt/v5/support/simulation/slurm-docker/fake-nvidia-smi /usr/local/bin/nvidia-smi ;; esac
install -m 755 /opt/v5/support/simulation/slurm-docker/fake-dmesg /usr/local/bin/dmesg
mkdir -p /run/fake
# Test users for the limit drills (fixed UIDs, the same in every container): alice is in arch, bob in perf,
# carol has no Slurm account (ideas from millermuttu's and uz9ai's tests, team 07).
for u in alice:2101 bob:2102 carol:2103; do id "${u%%:*}" >/dev/null 2>&1 || useradd -m -u "${u##*:}" "${u%%:*}"; done
printf '%s\n' "export V5_EVENTS_DIR=/s3/events" "export V5_EXPECT_GPUS=$gpus" "export V5_COLL_MAX_MB=16" \
  "export V5_NVME_MIN_FREE_GB=1" "export V5_MEM_MIN_GB=0.2" "export V5_DEVICE=cpu" \
  "export V5_S3_ENDPOINT=http://s3emu:9000" "export V5_S3_ACCESS_KEY=test" "export V5_S3_SECRET_KEY=test" \
  "export V5_REMOTE_ROOT=s3://v5-ckpt/ckpt" > /etc/v5/node.env

# Slurm reads its config from /etc/slurm; the files come from the repo, read-only.
mkdir -p /etc/slurm
cp /opt/v5/slurm/slurm.conf /opt/v5/support/simulation/slurm-docker/nodes.conf /opt/v5/support/simulation/slurm-docker/cgroup.conf \
   /opt/v5/support/simulation/slurm-docker/site.conf /opt/v5/support/simulation/slurm-docker/gres.conf /etc/slurm/
install -o slurm -g slurm -m 600 /opt/v5/support/simulation/slurm-docker/slurmdbd.conf /etc/slurm/slurmdbd.conf

case "$role" in
  slurmdbd)
    until mariadb-admin ping -h mariadb -u slurm -psimonly --silent; do sleep 1; done
    exec runuser -u slurm -- /usr/sbin/slurmdbd -D
    ;;
  slurmctld)
    until (echo > /dev/tcp/slurmdbd/6819) 2>/dev/null; do sleep 1; done
    # The cluster must exist in the accounting database before slurmctld registers.
    sacctmgr -i add cluster v5sim >/dev/null 2>&1 || true
    exec runuser -u slurm -- /usr/sbin/slurmctld -D -i
    ;;
  slurmd)
    until (echo > /dev/tcp/slurmctld/6817) 2>/dev/null; do sleep 1; done
    # The spot-notice watcher runs on every node (ADR 0002 §5). In the test it reads a file, not the instance metadata service.
    nohup python3 /opt/v5/queue/job_queue.py spot-watch >/var/log/slurm/spot_watcher.log 2>&1 &
    touch /dev/v5gpu0 /dev/v5gpu1          # placeholder GPU devices for gres.conf (Docker test only)
    # No systemd in the container (cgroup.conf IgnoreSystemd=yes): make the slice slurmd expects.
    mkdir -p /sys/fs/cgroup/system.slice
    exec /usr/sbin/slurmd -D -N "$(hostname)"
    ;;
esac
