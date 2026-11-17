# Week 3 harness

## Optional MoE expert load

Pass `--expert-load-every STEPS` to sample every STEPS completed optimizer steps. The default is 0. For example, `--expert-load-every 100` samples steps 100, 200, and so on. The manifest records the cadence. Resume continues using absolute training step numbers and replays the telemetry already present in the checkpoint's metrics history.

Sampled rows include `expert_load`, a list in model layer order with one integer count per routed expert in expert-index order. Each count records top-k router picks across all training microbatches in that optimizer step. Padding positions, shared experts, and evaluation forwards are excluded. For each layer the counts sum to `train/scored_tokens * top_k`. Unsampled rows omit the field.

With `--logger-factory g5_adapter:make_writer`, the G8 JSONL includes the same counts. The existing metrics writer also derives `router_max_vio`, `expert_load_imbalance`, and dead-expert statistics from them. Sampling adds work to the sampled step's performance measurement.
