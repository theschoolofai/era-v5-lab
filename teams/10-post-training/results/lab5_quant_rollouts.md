# Lab 5: GRPO rollouts from a quantized copy of the policy

28 November 2026. Team 10. Laptop CPU. This is the training-loop side: Team 12's sampler and mismatch runs are in
[`quant_rollout_mismatch_pytorch.md`](quant_rollout_mismatch_pytorch.md).

## What was built

- `rl-loop/quant_rollout.py`: before every rollout call it rebuilds a copy of the current weights under a scheme, samples
  from the copy and records each token's log-probability under the copy. Router weights are not quantized (`bf16` / `fp16`
  cast everything).
- `rl-loop/train.py`, `train.sampler: quant`: the learner scores the same tokens; `mismatch_k3` and
  `mismatch_abs_logratio` are logged; `objective_v1`'s trust region (or TIS for GRPO) works on the ratio; held-out
  evaluation stays on the learner and, with `guard`, is repeated with the copy; `max_k3` stops the run (exit code 4), and
  the stop survives a restart.
- `rl-loop/metrics_feed.py`: Team 8's metric names from `metrics.jsonl`.
- Smoke run: `python rl-loop/train.py --config rl-loop/config/smoke_tiny_olmoe_quant.yaml` (CPU, 13 s here; held-out
  reward 0.08 to 0.55, mean k3 0.0098, router unchanged).

| Scheme | Kernels | Speed means something | Models |
|---|---|---|---|
| `copy` | learner's own | control only | all |
| `bf16`, `fp16` | real | yes | all |
| `int8_dynamic` | real int8, CPU only | yes, on CPU | Hugging Face only |
| `w8a8_sim`, `w4a16_sim` | **simulated** (rounded weights, stored dtype) | **no**, mismatch only | all |

## 1. Rollout speed (measured)

Random-weight Llama, 124.7M parameters (hidden 768, 8 layers, vocabulary 32,000), fp32 learner. 4 prompts of 128 tokens,
8 samples each, 128 new tokens: 4,096 generated tokens per call. 5 repeats, schemes interleaved, one warm-up call each.
Intel Core Ultra 5 135H (AVX2, AVX-VNNI, no AVX-512), 8 torch threads, torch 2.7.1+cpu. 1-minute load average 5.3 before
and 9.0 after (the benchmark itself is part of it).

| Scheme | tokens/s, median (min to max) | Against `copy` | Without the refresh | Refresh per call | k3 |
|---|---|---:|---:|---:|---:|
| `copy` (fp32) | 274 (228 to 286) | 1.00x | 275 | 0.05 s | 0 |
| `int8_dynamic` | 315 (302 to 328) | **1.15x** | 350 (1.27x) | 1.23 s | 0.0018 |
| `bf16` | 148 (136 to 150) | **0.54x** | 148 | 0.10 s | 0.00003 |

- int8 is faster in decoding, and rebuilding the int8 copy takes 1.23 s, about 9% of a call of this size. A shorter
  rollout would give back less of the 1.27x.
- bf16 is slower than fp32 on this CPU. Lower precision is not automatically faster.
- The k3 values come from random weights. They say nothing about a trained model.

```bash
python teams/10-post-training/rl-loop/bench_quant_rollout.py speed --schemes copy int8_dynamic bf16 \
  --repeats 5 --threads 8 --out teams/10-post-training/results/lab5_quant_speed.json
```

### 1b. GPU Rollout Speed & Peak VRAM (measured, NVIDIA RTX 5070 Ti CUDA)

Random-weight Llama, `551.3M` parameters (`hidden 1536`, `12` layers, `12` heads, `vocab 32,000`), `fp32` learner on **NVIDIA GeForce RTX 5070 Ti (16 GB VRAM, PyTorch `2.15.0+cu132`, CUDA)**. `8` prompts of `128` tokens, `8` samples each, `128` new tokens (`8,192` generated tokens per call). `5` interleaved repeats after `1` warm-up call per scheme, CUDA-synchronised around each call (`results/lab5_quant_speed_gpu.json`).

| Scheme | `tokens/s`, median (min to max) | Against `copy` | Decode `tok/s` (no refresh) | Refresh per call | Peak VRAM (GB) | `k3` (random weights) |
|---|---:|---:|---:|---:|---:|---:|
| `copy` (`fp32`) | 374 (331 to 497) | 1.00x | 374 | 0.0075 s | 6.479 | `5.0e-12` |
| `bf16` | **1,742** (1,662 to 2,020) | **4.66x** | 1,746 | 0.0095 s | **4.277** (-34.0%) | `0.00016` |
| `fp16` | **1,935** (1,743 to 2,019) | **5.18x** | 1,940 | 0.0094 s | **4.277** (-34.0%) | `2.5e-06` |

- On GPU Tensor Cores (unlike CPU above), `bf16` and `fp16` rollout copies deliver **4.66x–5.18x** end-to-end throughput over an `fp32` rollout copy while cutting peak VRAM by **34.0%** (`6.479 -> 4.277 GB`), with weight refresh taking under `10 ms` (`~0.2%` of call time).
- `k3` values here are on random weights (`0.0%` tokens outside `[0.8, 1.2]`); trained-model mismatch for quantized copies (`Q8_0`, `Q6_K`, `Q5_K_M`, `Q4_K_M`) is in [`quant_rollout_mismatch_pytorch.md`](quant_rollout_mismatch_pytorch.md).

```bash
uv run --no-project --with numpy --with transformers --with pyyaml --with safetensors --with torch \
  python teams/10-post-training/rl-loop/bench_quant_rollout.py speed --schemes copy bf16 fp16 --device cuda \
  --hidden 1536 --layers 12 --heads 12 --prompts 8 --k 8 --prompt-len 128 --max-new 128 --repeats 5 \
  --out teams/10-post-training/results/lab5_quant_speed_gpu.json
```

## 2. Does learning change? (toy task, 10 seeds)

The trainer's tiny OLMoE smoke model and toy task, `objective_v1` (trust region 0.2), 80 steps, 1 update epoch, 256
sampled tokens per step. Held-out reward on the learner, 64 prompts x 8.

| Sampler | Held-out end, mean (min to max) | Minus exact, paired, 95% interval | Mean k3 | Largest single-step k3 | Seeds with a step above 0.05 | Tokens masked |
|---|---|---|---:|---:|---:|---:|
| exact | 0.582 (0.336 to 0.771) | | | | | 0 |
| `copy` | 0.582 (0.336 to 0.771) | 0.000 (identical) | 0 | 0 | 0 / 10 | 0 |
| `int8_dynamic` | 0.552 (0.389 to 0.773) | -0.031 ± 0.093 | 0.0027 | 0.68 | 5 / 10 | 0.5% |
| `w8a8_sim` | 0.608 (0.375 to 0.840) | +0.026 ± 0.156 | 0.0021 | 0.87 | 3 / 10 | 0.2% |
| `w4a16_sim` | 0.610 (0.375 to 0.824) | +0.028 ± 0.128 | 0.0229 | 1.54 | 10 / 10 | 5.4% |

- The exact-copy sampler reproduces the exact run seed for seed, so the path itself changes nothing.
- No reward difference is detected. The intervals are about ±0.1 to ±0.16, so a difference smaller than that would not
  show.
- Fewer bits give more mismatch and more masked tokens (`w4a16_sim`).
- A `max_k3` of 0.05 applied to every single step would have stopped 5 of the 10 int8 runs, although their mean k3 is
  0.0027. A step here is only 256 tokens. Before a real run, decide whether the limit applies to one step or to a window.

```bash
# 246 s with one thread; a second run gave the same per-seed values
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python teams/10-post-training/rl-loop/bench_quant_rollout.py learn \
  --seeds 1 2 3 4 5 6 7 8 9 10 --out teams/10-post-training/results/lab5_quant_learn.json
```

## 3. Gradient coverage, quantized sampler off and on

TSAI's rule for speed claims. One forward and backward of the learner (sum of -log probability) on the tokens each
scheme sampled, compared with the tokens of the exact copy. Trainable parameters with a `None` or all-zero gradient:

| Model | Device | Trainable tensors | Schemes | `None` | All zero | Lists identical to `copy` |
|---|---|---:|---|---:|---:|---|
| Speed model (random Llama, 124.7M) | CPU | 75 | `copy`, `int8_dynamic`, `bf16` | 0 | 0 | yes |
| Tiny OLMoE, router frozen | CPU | 43 | `copy`, `int8_dynamic`, `w8a8_sim`, `w4a16_sim`, `bf16` | 0 | 0 | yes |
| Speed model (random Llama, 551.3M) | CUDA (RTX 5070 Ti) | 111 | `copy`, `bf16`, `fp16` | 0 | 0 | yes |
| Tiny OLMoE, router frozen | CUDA (RTX 5070 Ti) | 23 | `copy`, `bf16`, `fp16`, `w8a8_sim`, `w4a16_sim` | 0 | 0 | yes |

The sampler changes which tokens the learner sees, not the learner's backward. The two schemes' gradients are therefore
not compared value by value. (Tiny OLMoE reports 23 trainable tensors under newer `transformers` fused expert layout vs 43 on the CPU env; zero `None` and zero all-zero gradients in both.)

```bash
python teams/10-post-training/rl-loop/bench_quant_rollout.py coverage \
  --out teams/10-post-training/results/lab5_quant_coverage.json   # 135 s, 6 threads, peak 4.2 GB
uv run --no-project --with numpy --with transformers --with pyyaml --with safetensors --with torch \
  python teams/10-post-training/rl-loop/bench_quant_rollout.py coverage \
  --schemes copy bf16 fp16 --olmoe-schemes copy bf16 fp16 w8a8_sim w4a16_sim --device cuda \
  --hidden 1536 --layers 12 --heads 12 --prompts 2 --k 2 --prompt-len 64 --max-new 32 \
  --out teams/10-post-training/results/lab5_quant_coverage_gpu.json
```

## Not measured

- No vLLM, SGLang, or live `Q8_0` GGUF rollout engine inside the RL loop, and no Team 5 dry run 2 checkpoint yet (awaits Team 12's balanced 50-prompt run + quantized policy copy).
- No quality check beyond held-out toy reward. The periodic check on Team 9's mini-benchmark is wired into the trainer
  ([`lab5_rollout_check.md`](lab5_rollout_check.md)), but no benchmark has been run through it (`#929` open).
- Team 5's model: the simulated and `bf16` paths are tested on a small model built from Team 5's classes. Only `nn.Linear`
  weights are rounded in the simulated schemes, so a head or expert held as a bare tensor stays exact. `int8_dynamic` does
  not support this model.
- Deletion Tuning with a quantized sampler is refused by the trainer.
