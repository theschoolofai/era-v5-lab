# Public code timing on the p1536 raw table

This is a short CPU check of Team 6's `models.ke2.KE2Embedding` and Team 4's
`decode_ref.py`, using Team 6's `perfkit.timer.StepTimer`. The public
`embedding=ke2` setting computes the projected public V1 code using
`embedding_bag`. The measurements below apply to that public implementation.

The verified p1536-s0 P=32 table has tokenizer SHA-256
`e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`
and content SHA-256 `21072027b19ef6f05d57ead7a2fc9fb4c52129e491186bf38d0ba079e8d5168a`.
The synthetic training batch is 2 × 16 token IDs, with a one-block, width-64
Team 6 GPT. The reference decoder checks 16 unprojected float64 code vectors
against all 131,072 raw table rows. It recovered all 16 IDs. Decode is an
inference reference operation, outside the timed training step.

Exact command from the lab repository root:

```bash
/Users/ai/ERAV5/.eraenv/bin/python teams/04-ke2/src/timing/bench_public_ke.py \
  --device cpu --batch-size 2 --seq-len 16 --decode-queries 16 \
  --warmup 2 --steps 10 \
  --out teams/04-ke2/results/timing/public_ke_p1536_cpu.json
```

Last output lines:

```text
p1536 table 21072027b19ef6f05d57ead7a2fc9fb4c52129e491186bf38d0ba079e8d5168a decoded 16/16 sampled IDs
training_input_embedding_forward: median 0.140 ms (n=10)
training_output_head_forward: median 1.360 ms (n=10)
output_token_argmax: median 0.851 ms (n=10)
complete_training_step: median 20.428 ms (n=10)
reference_code_encode_cpu_float64: median 0.059 ms (n=10)
reference_code_decode_cpu_float64: median 113.875 ms (n=10)
wall_seconds: 2.143
```

The JSON records the platform, PyTorch version, thread count, workload,
timer statistics and table hash. The training step includes forward, backward
and AdamW. The separately timed output head is a dense logit projection;
`argmax` chooses an ID from its logits. Neither is the code-vector decoder.
The hot path uses batched tensor/NumPy operations, and CUDA event readings
occur after timed steps. This CPU run is descriptive: ten samples do not meet
Team 6's 100-step comparison gate, and no GPU timing is claimed.
