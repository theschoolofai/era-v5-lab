# One image for every role in the Docker Slurm test cluster: slurmdbd, slurmctld and the compute nodes.
# In simple words: a small copy of the real cluster that runs on a laptop, so we can test the queue,
# the checkpoint code and the health checks before we pay for a single GPU hour.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10
RUN apt-get update && apt-get install -y --no-install-recommends \
        slurm-wlm slurmdbd slurm-wlm-mysql-plugin munge mariadb-client \
        python3 python3-venv procps iproute2 ca-certificates tini \
    && rm -rf /var/lib/apt/lists/*

# Pinned versions: one stack only (ADR 0002 §2). CPU wheels, because the test cluster has no GPU.
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.5.1 \
    && /opt/venv/bin/pip install --no-cache-dir numpy==2.1.3 pyyaml==6.0.2 safetensors==0.4.5 pytest==8.3.3 boto3==1.35.99 "moto[s3,server]==5.1.10" \
    && /opt/venv/bin/pip install --no-cache-dir setuptools==75.6.0 wheel==0.45.1 \
    && DS_BUILD_OPS=0 /opt/venv/bin/pip install --no-cache-dir --no-build-isolation deepspeed==0.18.0 \
    && DS_ACCELERATOR=cpu /opt/venv/bin/python -c "import torch, yaml, safetensors, boto3, deepspeed; print('torch', torch.__version__, 'deepspeed', deepspeed.__version__)"
# DeepSpeed (support/docs/deepspeed_impact.md). No ops built: the trainer uses torch's AdamW and gloo, and there is
# no compiler in the image, so a missing op fails at once instead of compiling at job start. On the cloud, the image
# pre-builds the CUDA ops (DS-3). No GPU in this cluster: DeepSpeed's CPU accelerator, gloo.
ENV DS_ACCELERATOR=cpu
ENV PATH=/opt/venv/bin:$PATH

# The submit service user (ADR 0002 §7: students submit through one service user) and a user with
# no Slurm account, used to prove that jobs without an account are rejected.
RUN useradd -m -u 2000 svc && useradd -m -u 2001 noacct \
    && mkdir -p /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /run/munge /s3 /nvme /var/lib/v5-health \
    && chown -R slurm:slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm \
    && chmod 1777 /s3 /nvme

# The entrypoint is read from the mounted repo (/opt/v5), so a change to it needs no image rebuild.
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/v5/support/simulation/slurm-docker/entrypoint.sh"]
