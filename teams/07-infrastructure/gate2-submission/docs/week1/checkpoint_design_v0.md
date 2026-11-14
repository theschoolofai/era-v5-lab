# Checkpoint design v0 — Team 7, Week 1

Status: proposed design with a tested single-process CPU reference. This is not yet a sharded distributed checkpoint implementation.

## Saved state and boundary

Save immediately after optimizer.step and scheduler.step, before drawing the next batch. Save model parameters/buffers, optimizer state, scheduler state, global step, next sampler cursor, training/eval mode, Python RNG, NumPy RNG and Torch CPU/CUDA RNG. Finish gradient accumulation before saving. Mid-accumulation gradients, AMP scaler, streaming loader workers and independent RNG generators require explicit integration adapters and are not supported by this reference.

The run config should include architecture, optimizer/scheduler settings, tokenizer hash, dataset/shard manifest hash, seed, batch/accumulation settings, code commit and parallel layout. ckpt.py validates the supplied config hash; the training integration is responsible for providing those fields.

## Publication and verification

Write under a temporary directory on the same filesystem. Flush and fsync state.pt, create a versioned manifest with byte count and SHA-256, then write COMPLETE containing the manifest checksum. Sync the temporary directory and rename it atomically to step-NNNNNNNN. Sync the parent directory. Never overwrite a published step. An atomic lock prevents concurrent writers of the same step. After a process crash, an operator must inspect any leftover lock; do not delete it while another writer may still be active.

The loader requires a published directory, COMPLETE, supported version, matching step, matching config and verified payload hashes. It uses torch.load(weights_only=True) for lab-created state dictionaries. Checksums detect corruption; they do not authenticate an untrusted author. No data is loaded before the payload hash has been checked. Load failures must terminate/restart a fresh training process, since model state can be partially applied before a later integration error.

latest_complete scans published steps and skips missing markers or corrupt checkpoints. It does not choose by modification time. Keep the last verified checkpoint until a newer one has been successfully restored. Retention and S3 cleanup are operator decisions.

## CPU restore acceptance proof

checkpoint_demo.py runs a baseline process for three steps, saves, and continues for five more. A new interpreter constructs a differently seeded model, restores the checkpoint and runs the same five steps. It requires exact tensor equality for all five losses, final parameters, AdamW moments, scheduler state, sampler cursor and all captured RNG states. Dropout and three RNG sources make missing-state bugs observable. No numeric tolerance is accepted.

```bash
python3 checkpoint_demo.py
python3 -m unittest discover -s tests -v
```

This proves repeatability for the tested CPU model/software combination. It does not promise bit equality across GPU types, PyTorch versions, parallel layouts or nondeterministic kernels.

## Week 2 integration design

For distributed/sharded state, use the training framework's distributed checkpoint facilities, one manifest listing every rank's payload, a coordination barrier and a single publisher. ckpt.save currently rejects initialized multi-rank jobs to prevent an unsafe partial save. Integrate AMP scaler, worker/sampler state and all model-specific state before claiming training recovery.

S3 is object storage: do not assume rename is atomic. TSAI uploads immutable state objects first, verifies checksums, uploads the manifest, then publishes COMPLETE last. A restore downloads to a local staging directory, validates every object and only then starts the job. TSAI keeps credentials. The CPU reference implements local publication only.

Recovery resumes the last verified completed step; work since that checkpoint must be replayed. “No lost work” is the target recovery guarantee for published state, not a claim that every in-flight GPU operation survives a crash. Week 2 requires a timed node restore and bounded automatic restart; those tests remain pending lab access.
