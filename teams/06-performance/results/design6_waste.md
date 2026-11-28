# Design 6 (Lab 5): waste, GPU idle time and loader stalls per step

**Owners:** Shashank, Sunil (official table on Sunil's GPU).
**Status:** bring-up done on Colab Tesla T4 with the small G6 model; tool and tests in this PR. Official table pending: Sunil's GPU against the 1(b) baseline (SHA, config, seeds), and Vaibhav's loader after S3/S5.
**Raw results:** https://gist.github.com/shank343/fcd2fc2ed9e21f51f8d3d249319d4133 (result JSONs, run log, Dry Run 2 analysis).
**Brief:** "6. Waste. Report GPU idle time between jobs and loader stalls per step." Raj (28 Nov): idle = both, within a run (`GpuSampler` + loader wait per step) and between lab jobs (queue gaps; #869/#805 walls).

## Tool

`perfkit/waste.py` (new; `bench.py` unchanged), tests in `correctness/test_waste.py`.

- `within`: runs warmup + N training steps through `bench.build` / `bench.train_step` and times each step on the GPU timeline with CUDA events (no synchronize inside the steps):
  - `host_gap_ms`: GPU idle from the end of step i-1 until the host enters `next_batch` for step i.
  - `loader_ms`: from entering `next_batch` until the batch is on the GPU: loader host work the GPU waited for, plus the host-to-device copy of one `[B, T+1]` int64 batch and two device-side slices.
  - `step_ms`: batch on the GPU to the end of step i (forward, backward, optimizer).
  - GPU waiting share = sum(`host_gap_ms` + `loader_ms`) / sum(cycle). A step counts as loader-stalled when `loader_ms` > 0.5 ms.
  - `GpuSampler` (nvidia-smi, 1 s) over the same steps.
- `between`: a finished G5-trainer run from its record files (`summary.json`, `metrics.jsonl`, `commits.jsonl`): wall time outside `perf/step_ms`, split by checkpoint interval, with the evaluations in each interval.

## 1. Within a run (bring-up)

GPU **Tesla T4**, dtype **fp16** (bench fallback: T4 has no bf16), base `081b6efe` = class main + #888 head (dirty: only `perfkit/waste.py` and `correctness/test_waste.py` added), `configs/base.yaml` (d=256, 6 layers, MoE off, eager attention, reversible), B=16, T=256, 4,096 positions per step, 10 warmup + 100 measured steps, seed 42, one run per arm. Real data: 2 FineWeb train shards of 2M tokens (`dataio.prepare_fineweb`, pinned Brahmic tokenizer). Medians over 100 steps.

| Arm | Step | Loader wait | Gap between steps | GPU waiting share | Steps loader > 0.5 ms | GPU util (sampler) | Positions/s (cycle) | Peak alloc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A FineWeb, prefetch on | 218.92 ms | 0.022 ms | 0.003 ms | 0.013% | 0/100 | 100% | 18,707 | 6.54 GiB |
| B FineWeb, prefetch off | 219.90 ms | 0.021 ms | 0.003 ms | 0.016% | 1/100 (max 0.98 ms) | 100% | 18,624 | 6.54 GiB |
| C synthetic (no loader work) | 223.13 ms | 0.022 ms | 0.003 ms | 0.013% | 0/100 | 100% | 18,355 | 6.54 GiB |

Host time to prepare a batch (`data_host_ms`, median): A 0.709 ms, B 0.702 ms, C 0.485 ms.

Official bench, arm A (`bench.py --modes clean,trace`): 18,320 positions/s = scored tokens/s (no document mask in this loader), 120,637 bytes/s, MFU 7.0% (`g6-v1`), trace GPU busy 98.1%, 1,210 kernels per step.

**Finding.** On this GPU and model the loader causes no measurable stall: the GPU waits 0.013% to 0.016% of the step cycle, and turning prefetch off changes nothing, because one step keeps the GPU busy about 219 ms while the host needs under 1 ms for the next batch. A and C differ by under 2%.

**What this cannot tell.** The T4 is slow for this model, so the GPU is the bottleneck and hides host work. On TSAI's GPU the dry-run-1 profile (#486) had the GPU busy 31.1% of the step and out of queued work in 20 of 20 steps, so the same measurement there may show real gaps. The data mix, the new mixture-aware loader (packing, document mask) and the V4/KAS model are not in this run.

## 2. Outside the steps: Dry Run 2 (class #869)

Record files from #869 head `0d3df057` (`teams/05-architecture/results/dryrun2-1234/`). In `train_week2.py`, `perf/step_ms` is synchronized at both ends and includes `stream.next` (data loading); evaluation (every 50 steps, `configs/runtime.yaml`), checkpoint saves (`--checkpoint-interval-s 600`) and logging are outside it.

| | Value |
|---|---|
| Wall (`summary.json`) | 4,788.2 s |
| Sum of `perf/step_ms` (1,221 steps) | 3,638.2 s |
| Outside the steps | 1,150.0 s (24.0%) |
| Evaluations | 26 (step 0, every 50, final) |

By checkpoint interval (commit times in `commits.jsonl`):

| Steps | Wall | In steps | Outside | Evals |
|---|---:|---:|---:|---:|
| 0 to 195 | 664.6 s | 494.1 s | 170.6 s | 3 |
| 195 to 350 | 693.2 s | 473.9 s | 219.3 s | 4 |
| 350 to 513 | 660.5 s | 490.4 s | 170.1 s | 3 |
| 513 to 672 | 659.5 s | 488.4 s | 171.1 s | 3 |
| 672 to 836 | 663.8 s | 491.5 s | 172.3 s | 3 |
| 836 to 993 | 660.2 s | 487.4 s | 172.8 s | 3 |
| 993 to 1150 | 697.3 s | 483.0 s | 214.3 s | 4 |
| 1150 to 1221 | 339.5 s | 229.5 s | 110.0 s | 2 |

Least-squares fit over the first seven intervals: outside = 35.0 s + 45.5 s per evaluation. An estimate from interval totals, not a direct timing of evaluation or saving.

**Finding.** About a quarter of Dry Run 2's wall time is outside training steps, and it follows the evaluation count: each evaluation costs about 45 s (about 15 steps' worth at 3 s per step), plus about 35 s per 10-minute checkpoint interval. Loader time is inside `perf/step_ms` and is not part of this gap.

**Open.** The first-to-last commit span (5,038.8 s) is longer than `wall_seconds` (4,788.2 s); the record does not say why, so the shares above use `wall_seconds`.

## 3. Between lab jobs

#805 (`dryrun2-sdpa-1234`) completed; TSAI posted ratios only (1.33x wall, 1.48x median tokens/s vs eager, 28 Nov). Neither #869 nor the #805 post gives job start or end times, so queue gaps between lab jobs cannot be computed from what is published. Needs job start and end times from TSAI.

## Next

1. Official table on Sunil's GPU against the 1(b) baseline: `within` at the baseline shapes, at least 2 seeds.
2. Again on Vaibhav's mixture-aware loader after S3 and S5 (packing and document mask add host work).
3. Between lab jobs: ask TSAI for job start and end times.

## Commands

```bash
cd teams/06-performance
python -m dataio.prepare_fineweb --out /content/fineweb-brahmic131k --train-shards 2 --tokens-per-shard 2000000
python -B perfkit/waste.py within --steps 100 --warmup 10 --out within_A_fineweb_prefetch.json run.dtype=bf16 run.batch_size=16 data.dir=/content/fineweb-brahmic131k data.source=fineweb10b data.prefetch=true
python -B perfkit/waste.py within --steps 100 --warmup 10 --out within_B_fineweb_noprefetch.json run.dtype=bf16 run.batch_size=16 data.dir=/content/fineweb-brahmic131k data.source=fineweb10b data.prefetch=false
python -B perfkit/waste.py within --steps 100 --warmup 10 --out within_C_synthetic.json run.dtype=bf16 run.batch_size=16 data.source=synthetic data.prefetch=true
python -B perfkit/bench.py --modes clean,trace --steps 100 --warmup 10 --tag design6_A_tesla_t4 run.dtype=bf16 run.batch_size=16 data.dir=/content/fineweb-brahmic131k data.source=fineweb10b data.prefetch=true
python -B perfkit/waste.py between --run-dir <#869 dryrun2-1234 files> --out between_dryrun2-1234.json
python -m pytest correctness/test_waste.py -q
```

`run.dtype=bf16` was requested; on the T4 the bench used fp16, as the result files record.

## Files (sha256)

| File | sha256 |
|---|---|
| `within_A_fineweb_prefetch.json` | `c96c8de4da94fd93877aaf5a39858a755a20a2a0b3da79377d0c93e27e78a3fc` |
| `within_B_fineweb_noprefetch.json` | `2cda4e49260c5872ab9be2ea42ac11410342b06163eab284a705ace8a04d161a` |
| `within_C_synthetic.json` | `503c82b6b71cd3bac1983644ff8360124f8c0ff0e3ad0a37fc3e319ddeff55cf` |
| `design6_A_tesla_t4.json` (bench) | `468209bf13c769c4b3b826c88616ae15200de406af15020f798cac639dbaa89d` |
| `between_dryrun2-1234.json` | `35fd83c371d4ba5c33fab8ba15e5697f1c36c946aed584ec7b7d18fd7cb7ffee` |
| `design6_tesla_t4.log` | `01fbe9a639ea0934a2bccb6caf2e233b99c61567e3a35daca4c0c3fe1ac03872` |
| #869 `summary.json` | `be354857da34af3566e2080b007a65cbddce7e01b692e610bf332ab4aeae08a0` |
| #869 `metrics.jsonl` | `2b7645019ca8abf5575272a76ebd5784e6698b7c707d045c351c859d828cfa9a` |
| #869 `commits.jsonl` | `05a052c390e6f80b7303eacd3be9b284c9a6a430e38478be5880012f75a2e0e8` |
