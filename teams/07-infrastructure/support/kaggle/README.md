# GPU validation on Kaggle (2 GPUs, free)

In simple words: a Mac has no NVIDIA GPU, so the Docker Slurm test ran everything on CPU. This folder runs
the GPU-only parts on Kaggle's free 2-GPU machine. Total time is about 20–30 minutes.

## Steps

1. Build the package (on the laptop, from `teams/07-infrastructure`):
   ```
   python3 support/kaggle/make_package.py
   ```
   It writes `support/kaggle/dist/v5-infra-kaggle.zip` (the team folder, ~210 KB) and
   `support/kaggle/dist/v5_gpu_checks.ipynb`. `dist/` is ignored by git, because the repo does not allow zips.
2. kaggle.com → **Datasets → New Dataset** → upload `v5-infra-kaggle.zip` (Kaggle unzips it) → Create.
3. kaggle.com → **Code → New Notebook → File → Import Notebook** → pick `v5_gpu_checks.ipynb`.
4. Right panel: **Accelerator = the 2-GPU accelerator** (phone verification needed once); **Add Input** → your Dataset.
5. **Run all**. Cell 1 copies the code to `/kaggle/working` (the input folder is read-only); cell 3 runs
   `run_gpu_checks.py` (20–30 min); cell 4 shows `summary.md` and packs `gpu_results.zip`.
6. Output panel → download `gpu_results.zip` → unzip into `teams/07-infrastructure/support/kaggle/results/`.
   Bring back `summary.md` and `summary.json`; the `*.log` files only help if a step failed.

No Dataset? Turn **Internet = on** instead (needs a phone-verified Kaggle account): cell 1 then clones the
pushed `infrastructure` branch. The notebook file does not ask for Internet itself; if it did, the import would
fail with `Permission 'kernelSessions.enableInternet' was denied` on an unverified account.

**DeepSpeed tests (T18–T23) need Internet = on**: `run_gpu_checks.py` installs `deepspeed==0.18.0` (the same
version as the Docker cluster image), built without ops. With Internet off they are skipped, not failed, and
`summary.md` says `DeepSpeed not installed`.

No cloud keys, tokens or personal data are used or written.

## What each step proves

| Step | Proves | ADR |
|---|---|---|
| health_prolog / health_full | the health check reads real `nvidia-smi` values; missing DCGM/dmesg are `skipped`, never `pass` | 0003 §1 |
| allreduce | NCCL across 2 GPUs gives exact sums; measured bus bandwidth | 0003 §1 |
| nccl_timeout | a stuck GPU becomes a clean failure about 20 s after the timeout, with a flight-recorder trace | 0003 §2 |
| ckpt_tests_cuda | T1–T17 with the trainer on GPU: **bit-equal resume on CUDA** in deterministic mode; FSDP2 (T16) | 0001 §8 |
| ckpt_tests_cuda (DeepSpeed) | T18–T22 on GPU: ZeRO-1/2/3 save inside our commit protocol, bit-equal resume, `load_checkpoint` failure falls back, world change holds, `zero_to_fp32` export; T23: **fp16** resume bit-equal (the test GPU has no bf16) | impact doc §1 |
| bench_save | GPU → host copy speed (the stall) and save speed, replacing the cost model's assumptions | 0001 §2, 0004 §1 |

## Not covered on Kaggle

Kaggle's GPUs are an older generation on PCIe, not the main-run GPU with NVLink and a fast network. Bandwidth and speed numbers are Kaggle-GPU numbers.
No DCGM, no kernel log (Xid), no row remapping (not supported on that GPU), no Slurm. These wait for the
week-2 cloud node.
