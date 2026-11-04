# If V5 trains with DeepSpeed: what changes in ADR 0001–0004

Team 07, 29 Oct 2026. Status: **proposal**. No ADR has been changed yet. Each section says what stays, what
changes, the new decision, the code change, and the test that proves it.

> **In simple words.** DeepSpeed is a library that splits a big model's memory across GPUs (ZeRO). It changes
> **who owns the training state**. Today our code reads the state from PyTorch and saves it with PyTorch's
> checkpoint tool. With DeepSpeed, the DeepSpeed "engine" owns the weights, the optimizer and its own save format.
> So most of ADR 0001 (checkpoint) changes. ADR 0002 (queue) changes in how jobs start. ADR 0003 (health) gains
> checks. ADR 0004 (cost) gets new numbers. The ideas stay the same: commit last, prove the restore, 0/75/78,
> drain bad nodes. Only the tools under them change.

Facts marked **[docs]** were checked on deepspeed.ai on 29 Oct 2026. Facts marked **[verify]** are from the
code or papers and must be checked against the DeepSpeed version we pin, before the ADR is changed.

---

## 0. The decisions this forces (summary)

| # | Decision | Recommendation | Why, in simple words |
|---|---|---|---|
| DS-1 | Checkpoint format | **DeepSpeed's own** (`engine.save_checkpoint`), wrapped in our commit protocol; drop `dcp.save` | DeepSpeed's ZeRO state cannot be read out cleanly for PyTorch DCP. Fighting the engine costs more than wrapping it |
| DS-2 | ZeRO stage | chosen from the model size with the formula in §1.2 (stage 1 if it fits, else stage 3); **never** CPU/NVMe offload on the GPU node | offload shares the NVMe and the PCIe link with checkpoints and data prefetch, and slows every save |
| DS-3 | Launcher | **`srun` starts every rank**; never the `deepspeed` launcher (hostfile + passwordless SSH) | SSH between nodes is a security hole; it also hides exit codes and escapes Slurm's cgroups and accounting |
| DS-4 | Save speed (stall) | measure the **synchronous** DeepSpeed save first; async engines only after their test passes | the async engines are new and limited (DataStates: tested on ZeRO-1 only, no universal) **[docs]** |
| DS-5 | Changing the world size | still **wait for the spare** (no automatic shrink); a resize is an **operator job**: `ds_to_universal.py` conversion, then `load_universal` | a normal ZeRO checkpoint is tied to its data-parallel size; converting a TB checkpoint takes time and memory |
| DS-6 | Bit-equal checks | keep all four proofs; compute the fingerprint on ZeRO's partitions (§1.6) | the V4 silent misload is the reason the checks exist. A new library is a new place for it to happen |
| DS-7 | Version pin | DeepSpeed version, pre-built ops and the full ds_config are part of the image and of `ENV_MUST_MATCH` | ZeRO bucket sizes and overlap settings change the order of the sums, so they change the bits |

---

## 1. ADR 0001 (checkpoint): the biggest change

### 1.1 What stays exactly as it is

- **Commit protocol:** save to local NVMe, upload to S3 with sha256, write `MANIFEST.json` **last**, then
  `latest.json`, then append `commits.jsonl`. DeepSpeed knows nothing about S3. Our layer is still the only
  thing that decides when a checkpoint "counts".
- `latest.json` is the only pointer. DeepSpeed's own `latest` file is turned off (`save_latest=False`).
  Note: the DataStates async engine does not write `latest` at all (open issue on its GitHub) **[docs]**, which
  is one more reason not to rely on it.
- The exit codes 0/75/78, the NaN and loss-spike guards, retention, pinning, `env_manifest`, and restore with
  fallback to the previous commit.
- One global data position (`loader_global`). DeepSpeed makes this **mandatory**, not just advised (§1.5).

### 1.2 Memory and checkpoint size: the numbers everything else depends on

Mixed-precision Adam uses Ψ = number of parameters. Per parameter: bf16 weights 2 B, bf16 gradients 2 B, and
optimizer state 12 B (fp32 master copy 4 B + Adam m 4 B + Adam v 4 B). These are the ZeRO paper's numbers.
N = data-parallel GPUs.

| | Memory per GPU (without activations) | 7B on 16 GPUs | 70B on 16 GPUs |
|---|---|---|---|
| ZeRO-1 (optimizer split) | 2Ψ + 2Ψ + 12Ψ/N | 33 GB | 333 GB: **does not fit** |
| ZeRO-2 (+ gradients split) | 2Ψ + 14Ψ/N | 20 GB | 201 GB: **does not fit** |
| ZeRO-3 (+ weights split) | 16Ψ/N | 7 GB | 70 GB: fits on a the GPU node |

**Checkpoint size ≈ 14 B × Ψ:** bf16 weights plus the 12 B of optimizer state. Gradients are not saved.

| Ψ | Checkpoint | Per node, 2 nodes | Per node, 4 nodes |
|---|---|---|---|
| 7B | ≈ 98 GB | 49 GB | 25 GB |
| 70B | ≈ 980 GB | 490 GB | 245 GB |

**Rank-0 hotspot (ZeRO-1/2):** the bf16 model weights are written **whole**, by data-parallel rank 0 only
(`mp_rank_00_model_states.pt`). For 7B that is 14 GB from one process, on one node, on top of that rank's
optimizer shard. ZeRO-3 writes the weights split across ranks (`zero_pp_rank_*_model_states.pt`). **[verify]**
the file names for our version. Two consequences:
- **NVMe sizing (ADR 0002 §3):** the node with rank 0 needs more free disk. `ckpt.py` checks free space with
  `last_rank_bytes × ranks per node`, which is wrong for that node. It must use the real per-node bytes from the
  last manifest.
- **Stall:** under ZeRO-1/2, rank 0 is the slowest writer, so it sets the stall (§1.4).

The real Ψ comes from Team 05 (`config_v0.yaml` is still empty). Until then the ADR says "ZeRO stage chosen by
the table above".

### 1.3 Save: what the code becomes

Today (`ckpt.py save`): `get_state_dict(model, optim)` → fingerprint → probe → `dcp.async_save`. With DeepSpeed:

```python
# every rank, at the same step (DeepSpeed's own docs: if only rank 0 calls it, the job hangs) [docs]
digest = zero_fingerprint(engine)              # §1.6, collective
probe  = float_bits(probe_fn(engine))          # forward on every rank (ZeRO-3 gathers weights: collective)
engine.save_checkpoint(local_dir, tag=f"step_{step:08d}",
                       client_state={"step": step, "tokens": tokens, "loader": loader.state_dict()},
                       save_latest=False,
                       exclude_frozen_parameters=True)   # KE2 tables: saved and fingerprinted once, not every time [verify]
write_json(f"{local_dir}/extra_rank{rank}.json", {"rng": rng_capture()})  # DeepSpeed does not save RNG [verify]
# then exactly as today: background upload of THIS rank's files → sums_rank<r>.json → rank 0 MANIFEST last
```

Config that must be set:

```json
"checkpoint": {
  "tag_validation": "Fail",           // every rank must use the same tag, or stop (default is only "Warn") [docs]
  "use_node_local_storage": true      // each node keeps its own ranks' files; no shared file system needed [docs]
}
```

`use_node_local_storage` matters: without it, DeepSpeed assumes every rank can see every file (a shared FS),
and ADR 0002 §3 says there is none. With it, a restore needs **only this node's ranks' files**, so restore
downloads only those files (§1.7), not the whole checkpoint to every node.

`_own_files()` in `ckpt.py` matches DCP names (`__{rank}_*.distcp`). It becomes a match on DeepSpeed's names:
`zero_pp_rank_{dp}_mp_rank_{mp}_optim_states.pt`, `*_model_states.pt` (rank 0 under ZeRO-1/2), and
`zero_to_fp32.py`, which rank 0 copies into the folder. Rule: **each file is uploaded by exactly one rank**. A
test lists the folder after a save and fails on any file that no rank owns, or that two ranks own.

### 1.4 The stall: the claim in ADR 0001 §2 changes

`engine.save_checkpoint` uses `torch.save`, which is **synchronous**: training waits until every rank has
written its files to NVMe, not just until the GPU-to-host copy. So "the stall is only the GPU-to-host copy" is
**false** with DeepSpeed's default engine, and the ADR must say so.

Estimate, to be measured on the week-2 node: each rank writes its shard at about 1–2 GB/s (one stream), 8
ranks per node in parallel.
- 7B, 2 nodes, ZeRO-1: shards ≈ 5 GB per rank → ≈ 3–5 s. Plus rank 0's 14 GB of weights → **≈ 10–15 s stall**.
- 70B, 2 nodes, ZeRO-3: 490 GB per node / ~10 GB/s → **≈ 50 s stall**.

Options, in order:
1. **Measure sync first** (`support/tools/bench_save.py --deepspeed`, new mode). If the stall is ≤ 2% of the
   interval (Team 06's budget), keep it. That is the simplest correct choice.
2. **FastPersist** (DeepSpeed's fast writer on DeepNVMe; needs `libaio` in the image) **[verify]** config name.
   Same files, faster writes; still synchronous.
3. **Async engines**:
   - DataStates-LLM: `"datastates_ckpt": {"host_cache_size": 16}`. It is only tested with ZeRO-1 and no
     offload, and has no universal or elastic checkpoint support **[docs]**.
   - DeepSpeed's newer Decoupled/Fast checkpoint engines: a 2026 fix (PR #8502) restores the full training
     state with them, which says they were incomplete before **[verify]**.

   Adopt one only after T1, T3, T4 and T6 pass with it, and never with universal resharding.

Young's interval goes up with the stall: interval = √(2 · stall · MTBF). For stall 50 s and MTBF 8 h:
√(2 · 50 · 28 800) ≈ 1 700 s ≈ 28 min, still under the 30-min cap. For stall 10 s: ≈ 13 min. The interval
formula in `cost_model.py` is unchanged; only its input changes. The **emergency save** (spot notice, health
drain) is now about one stall long. A 50 s save fits in the 2-minute spot warning, but a 70B ZeRO-1/2 rank-0
write might not: another reason for ZeRO-3 at that size.

### 1.5 Data position: `client_state` is saved once

`client_state` goes into the model-states file, which **one** rank writes **[verify]**. Every rank gets the
same dict back. A per-rank data position cannot survive that. `loader_global=True` (one ledger offset, the
same on every rank, from the week-1 review fix) becomes a **hard requirement**: the save refuses to run
(`ReshardError`-like exit 78) if ranks disagree. RNG still goes to our own `extra_rank<r>.json`, because it
*is* per rank.

**Global batch at another world size:** DeepSpeed checks
`train_batch_size = micro_batch × gradient_accumulation_steps × data-parallel size`. After a resize, the job
must recompute the accumulation steps to keep the same global batch, so the ledger offset still means "global
batch N". So `ds_config` is generated by the job script from `config_v0.yaml` + the world size, not a fixed file.

### 1.6 The four restore proofs with DeepSpeed (ADR 0001 §8)

| Proof | Today | With DeepSpeed |
|---|---|---|
| State digest | `get_state_dict` → DTensor shards, positional fingerprint, one all-reduce | **Fingerprint ZeRO's own partitions** (below). `torch.distributed.checkpoint.state_dict` does not understand the engine |
| Probe loss | forward on every rank | `engine.module.eval()` + forward on every rank (ZeRO-3 gathers weights: collective). Same rule as the week-1 fix |
| Next batch | `loader.next_batch_id()` | unchanged |
| Frozen hashes | fingerprint of frozen buffers | unchanged if frozen tensors are module buffers; if they are frozen parameters and `exclude_frozen_parameters=True`, they are saved **once** per run and fingerprinted then |

**ZeRO fingerprint, practical design.** The week-1 fingerprint only needs: for each piece of a tensor this rank
holds, its **offset in the logical tensor**. ZeRO has that:
- **ZeRO-3:** each parameter is split on its own. Rank r holds `param.ds_tensor` (fp32 partition, flat), which
  starts at element `r × ds_tensor.ds_numel` of the flattened parameter. The last rank's partition is padded,
  so mask elements ≥ `param.ds_numel`. That is exactly `_fingerprint_piece(flat_piece, (r·n,), (numel,))`.
- **ZeRO-1/2:** parameters are flattened into groups. Rank r holds a slice of the group's flat fp32 buffer.
  Use DeepSpeed's tensor-fragment API (`deepspeed.utils.safe_get_local_fp32_param`,
  `safe_get_local_optimizer_state(p, "exp_avg")`) to get this rank's fragment of each parameter. Each fragment's
  start offset in that parameter comes from the param's fragment mapping (`_hp_mapping`) **[verify]**: internal,
  so isolate it in one function with a version check.
- **Never** fingerprint with `safe_get_full_fp32_param`: it gathers the whole parameter on every rank, which is
  far too slow at TB size.
- Cover fp32 master, Adam `exp_avg`, `exp_avg_sq` and the step count. The bf16 weights are `bf16(fp32 master)`,
  so fingerprinting the master is enough.
- This keeps "equal at any world size" true. ZeRO's partitioning padding changes with N, but padding is masked
  and the logical offsets do not change.
- Test T18 (new): fingerprint on 2 GPUs = fingerprint on 1 GPU of the same state (Kaggle (2 GPUs)).

**Bit-equal continuation (T1, T6):** at the same world size it should still hold, but only with every reduce
setting pinned:
- `reduce_bucket_size`, `allgather_bucket_size`, `overlap_comm`, `contiguous_gradients`,
  `communication_data_type`;
- `NCCL_ALGO` / `NCCL_PROTO` fixed for the comparison run.

That is why DS-7 puts the ds_config sha in `ENV_MUST_MATCH`. After a universal reshard, the *state* must still
match bit for bit (digest), but the *loss curve* will not, because the sums happen in a different order. The ADR
already says this for resharding.

### 1.7 Restore: what the code becomes

```python
files = [f for f in man["files"] if owned_by_this_node(f)]   # use_node_local_storage: only our ranks' files
download(files) → check each sha256 (as today)
strict key check: man["param_shapes"] (from DeepSpeed's model-states file) vs the model built now  # before loading
load_path, client = engine.load_checkpoint(local_dir, tag=man["tag"], load_module_strict=True,
                                           load_optimizer_states=True, load_lr_scheduler_states=True)
if load_path is None:            # DeepSpeed returns (None, None) and only WARNS when it finds nothing [verify]
    raise IntegrityError(...)    # we must turn that into a fallback, never into "start from step 0"
rng_restore(extra_rank<r>.json); loader.load_state_dict(client["loader"]); checks of §1.6
```

The `load_path is None` line is the most important line in this section. A silent fresh start would look like
a successful restore and **overwrite good checkpoints** with an untrained model. Test T19 (new): delete one
rank's file after the commit, then restore. It must fall back to the previous commit, never start at step 0.

**Measured (DeepSpeed 0.19.8, 29 Oct):** with the weights file missing, `load_checkpoint` does not return None,
it fails an `assert` (`AssertionError`). So `ckpt/ds_ckpt.py` treats both the same way: None *or* an
exception from `load_checkpoint` becomes `IntegrityError`, and restore tries the previous commit. T19 passes.

### 1.8 Security: checkpoints are now pickles

`.pt` files are loaded with `torch.load`, and DeepSpeed needs full pickle loading (`weights_only=False`) for
its optimizer objects **[verify]**. A pickle can run code. So anyone who can write to the checkpoint bucket can
run code on every GPU node. The sha256-in-manifest check (ADR 0001 §5) becomes a **security control**, not only
an integrity check:
- the manifest is checked **before** `torch.load` touches any file (already the case, so keep it);
- write access to `s3://…/ckpt/` only for the training role (ADR 0002 §11);
- exports for other teams stay **safetensors** (no code), via `zero_to_fp32.py` (§1.9).

### 1.9 Export for Teams 09/11/12

`ckpt.py export` changes from "DCP → safetensors" to "DeepSpeed → `zero_to_fp32` → safetensors". The script
builds the full fp32 model in CPU memory (4 B × Ψ): 28 GB for 7B, **280 GB for 70B**. `nodes.cloud.conf` has
`cpu-[1-4]` with 250 GB, which is too small for 70B. Either run export on a GPU node with ≥ 2 TB RAM, or use the
script's sharded output **[verify]** flags (`--safe_serialization`, `--max_shard_size`). The probe-loss check
after export stays: the exported weights must give the same bits.

### 1.10 Changing the world size (resharding)

- **ZeRO-1/2/3 at another data-parallel size:** convert first:
  `python deepspeed/checkpoint/ds_to_universal.py --input_folder <ckpt> --output_folder <uni>`. Then load with
  `"checkpoint": {"load_universal": true}` **[docs]**.
- **Expert parallel:** only AutoEP models are supported. "Native DeepSpeed MoE / Megatron-DeepSpeed expert
  checkpoints" need "a separate model-specific migration step" **[docs]**. If Team 05's MoE uses native DeepSpeed
  MoE, **the expert-parallel degree can never change** during the run. Write that into the ADR as a constraint.
- The conversion reads the whole checkpoint. Run it as a **CPU job on a big-memory node** that writes a new
  committed checkpoint on a new branch (`resharded-w<N>`), with the four proofs before and after. It is an
  operator runbook step, not an automatic restart path. This confirms ADR 0002 B2 ("two nodes down → wait, no
  automatic shrink").

### 1.11 Tests: what changes in T1–T17

| Test | Change |
|---|---|
| T1, T6 (bit-equal resume, SIGUSR1) | run with a DeepSpeed tiny trainer (`train.py --deepspeed --zero {1,3}`) |
| T2, T16, T17 (reshard) | become: save at DP=2 → `ds_to_universal` → load at DP=1; digest equal |
| T3, T4 (flipped byte, crash before seal) | unchanged logic, new file names |
| T5 (renamed key) | uses `param_shapes` from the model-states file |
| T8 (export) | via `zero_to_fp32` |
| new T18 | ZeRO fingerprint invariant across DP size |
| new T19 | a missing rank file must fall back, never start fresh |
| new T20 | every file in the folder owned by exactly one rank |

**Where they run:** DeepSpeed on CPU needs its CPU accelerator and oneCCL, not gloo **[verify]**. So the Docker
cluster keeps the DDP trainer for queue and health drills. The DeepSpeed tests run on Kaggle (2 GPUs). Those GPUs have no
bf16, so they run fp16 with loss scaling there and bf16 on the GPU node in week 2. fp16 adds one more reason
to hold: `engine.skipped_steps` grows on overflow. Track it (§4).

### 1.12 Built and measured (29 Oct)

The plan above is now code: `ckpt/ds_ckpt.py` (`DSCheckpointer`, `export_ds`), `train.py --deepspeed
--zero-stage {0,1,2,3} --ds-precision {fp32,fp16,bf16}`, and tests T18–T23 in `support/tests/test_ckpt.py`.
The [verify] above about CPU is **answered: wrong.** DeepSpeed's CPU accelerator works with plain gloo (0.18.0 in
the cluster image, 0.19.8 on a Mac), so the Docker cluster can run every drill with the DeepSpeed trainer too
(`run_sim.py --deepspeed`). On 29 Oct that run passed every drill; `restore_smaller_world` passes by being *held*
(exit 78, `ReshardError`, names `ds_to_universal.py`). Earlier runs found findings 6 (bucket memory, OOM) and 7
(below). **That run was before the merge and the folder changes, so its results are not part of the submission;**
the evidence for DeepSpeed is the unit tests below (T18–T22, re-run on the current code). DeepSpeed is an
**optional** backend: off unless the trainer runs with `--deepspeed`, and imported only by `ckpt/ds_ckpt.py`.

Test numbers below are the built ones; they replace the planned list in §1.11.

| Test | What it proves | Where it passed |
|---|---|---|
| T18 ×3 | ZeRO-1, 2 and 3: save inside our commit protocol, new process, loss equal as raw bits at every step; DeepSpeed's `latest` never written | laptop CPU, 2 ranks |
| T19 | `load_checkpoint` cannot load → previous commit, never step 0 | laptop CPU |
| T20 | world 2 → 1 is held (exit 78, `ReshardError`, names `ds_to_universal.py`) even with `--allow-env-change` | laptop CPU |
| T21 | ZeRO-3 weights digest from the pieces = ZeRO-1 digest from full weights (no gather) | laptop CPU |
| T22 ×2 | `zero_to_fp32` export (ZeRO-1 and 3): rebuilt weights give the saved weights digest bit for bit | laptop CPU |
| T23 | fp16 with dynamic loss scale: resume bit-equal | Kaggle (2 GPUs) only (pending) |

Five things we only learned by running it:

1. **`load_checkpoint` does not only return None.** With the weights file missing it fails an `assert`. Both now
   become `IntegrityError` → previous commit (§1.7).
2. **ZeRO-3 changes the probe loss bits** for the same weights: DeepSpeed swaps `F.linear` for its own function
   (matmul, then add bias), which rounds differently from one fused `addmm`. Restore is still exact (same stage on
   both sides; `zero_stage` is in the environment check). Export at ZeRO-3 compares the weights digest, not the
   probe. Cross-stage comparisons must use the weights digest.
3. **The ZeRO-3 piece layout** is: flatten, pad to a multiple of the world size, rank r holds flat elements
   `[r·n, r·n + n)`; the last piece carries the padding. Fingerprinting each piece at that offset in the flattened
   weight gives exactly the full weight's fingerprint (T21). No gather needed, at any size.
4. **DeepSpeed compiles ops at job start unless told not to** (DS-3 confirmed): in the cluster image the CPU
   accelerator tried to build its shared-memory all-reduce on the first job and failed (no compiler on the node).
   Its kernels are x86-only (AVX), so on ARM (Apple-silicon Docker) it cannot build at all: the test trainer marks
   it unavailable on non-x86 CPUs and gloo does the work. On the cloud, the CUDA ops are built into the image.
5. **The stall is the whole synchronous write** (§1.4): `stall_s` in `checkpoint.committed` now includes
   `engine.save_checkpoint`'s write; `ds_write_s` in the manifest shows that part alone.
6. **Default bucket sizes are a memory bill, whatever the model size.** The first DeepSpeed cluster run lost its
   main job to the kernel OOM killer: each tiny-model trainer jumped from 340 MB to 2.2 GB during normal steps,
   because ZeRO's default `reduce_bucket_size` / `allgather_bucket_size` are 5e8 values (2 GB in fp32). Set to
   2^20 for the tiny model, peak RSS is 343 MB and ZeRO-1/2/3 still resume bit-equal. For V5 these buckets (and
   ZeRO-3's prefetch and live-parameter limits) are memory we must budget per GPU next to the §1.2 numbers,
   tune once on the GPU node, and pin in ds_config (DS-7): a default left in place is 2 GB per bucket per rank.
7. **Check the world size before the environment.** ds_config holds the per-GPU batch size, so a smaller world
   also changes `ds_config_sha256`. Checked first, the environment error hid the real cause (and its fix,
   `ds_to_universal.py`). Now `ReshardError` comes first; T20 runs without `--allow-env-change` to prove it.

---

## 2. ADR 0002 (job queue, Slurm)

### 2.1 Launch: `srun`, not the `deepspeed` launcher

The `deepspeed` launcher reads a hostfile and needs "machines accessible via passwordless SSH" **[docs]**. On
our cluster that would mean:
- SSH keys between all GPU nodes (ADR 0002 §11 forbids that);
- processes outside Slurm's cgroups (GPU isolation and accounting lost);
- exit codes mixed by the launcher, which breaks 0/75/78.

So `mainrun.sbatch` keeps `srun` and the trainer maps Slurm's variables itself, as the test trainer does today:

```bash
srun --kill-on-bad-exit=1 bash -c '
  export RANK=$SLURM_PROCID LOCAL_RANK=$SLURM_LOCALID WORLD_SIZE=$SLURM_NTASKS
  exec python train.py --deepspeed_config $DS_CONFIG ...'
```

```python
deepspeed.init_distributed(dist_backend="nccl", timeout=timedelta(seconds=NCCL_TIMEOUT_S))  # ADR 0003 §2 value
```

The NCCL timeout **must** be passed here: DeepSpeed has its own default, and the hang drill depends on ours
**[verify]** the default in our version.

### 2.2 The image (ADR 0002 §7)

- **Pin** `deepspeed==<x.y.z>`.
- **Pre-build the ops** we use when building the image, e.g. `DS_BUILD_FUSED_ADAM=1`, plus `DS_BUILD_AIO=1`
  only if we use FastPersist (needs `libaio-dev`). Otherwise each node compiles them with JIT on first start.
  That takes minutes per restart, needs the CUDA toolkit and ninja on the node, and 8 ranks race on
  `~/.cache/torch_extensions`. In a requeue loop, that is minutes of paid GPU time per restart.
- `ds_report` output saved in the image build log; its op list goes into `env_manifest`.
- No `pdsh`, no `mpi4py` needed.

### 2.3 Signals, exit codes, crash loop

These stay as they are. One rule is new: **every save decision must be agreed by all ranks before
`save_checkpoint`**. A SIGUSR1 arrives at one rank. Today the trainer all-reduces the stop flag every step
(T6). With DeepSpeed that all-reduce is required: if one rank calls `save_checkpoint` and the others do not,
the job hangs until the watchdog fires and loses the emergency save.

### 2.4 Storage (§3)

`use_node_local_storage=true` fits the "no shared FS" rule. NVMe per node must hold:
- `keep_local` (2) × this node's share,
- plus 1.2 × headroom,
- plus the rank-0 hotspot under ZeRO-1/2,
- plus the data prefetch cache.

For 70B on 2 nodes: 2 × 490 GB + headroom ≈ 1.2 TB for checkpoints, against the tens of TB of local NVMe a generic 8-GPU node has.
That is fine. But **never put ZeRO-Infinity NVMe offload on the same disk** (DS-2).

---

## 3. ADR 0003 (node health)

| Change | Why |
|---|---|
| `allreduce_test.py` also tests **reduce-scatter and all-gather** bandwidth | ZeRO-2/3 spend most of their communication on these, not on all-reduce; a slow the fast network link shows there first |
| new prolog check: `ds_report` ops compatible + `python -c "import deepspeed"` | a node with a broken CUDA toolkit or a missing op fails in the prolog (seconds), not after 8 ranks start |
| hang runbook: "ZeRO-3 all-gather mismatch" | ZeRO-3 hangs if ranks call modules in different orders (MoE routing, a rank skipping a layer). The NCCL flight recorder shows one rank in a different all-gather; the watchdog still catches it |
| stall drill: emergency save must finish inside the 120 s spot warning at the chosen ZeRO stage | the save is now synchronous (§1.4) |

Unchanged: nvidia-smi, Xid, DCGM (diag in prolog only, `health -c` periodic), drain + save + move.

---

## 4. ADR 0004 (cost and alerting)

**Cost model inputs that change:**
- stall: measured sync DeepSpeed save, not the host copy;
- Young's interval follows from it;
- emergency save time = stall;
- restore time = per-node download (smaller with node-local storage) + `load_checkpoint`;
- export and universal conversion = CPU node hours (new line);
- JIT op build = 0 if ops are pre-built (if not, minutes × nodes per restart; this is why §2.2 matters).

**New metrics** (catalog.yaml), each with a why and an action, as now:

| ID | Metric | Alert | Action |
|---|---|---|---|
| CK-12 | DeepSpeed save time (sync) | ≥ 2% of interval | Team 06: FastPersist / async engine trial; check the rank-0 hotspot |
| CK-13 | `load_checkpoint` returned no path | any | HIGH: never a fresh start; the restore fell back. Check the missing file in the manifest |
| T-xx | `engine.skipped_steps` growth (fp16 only) | > 0.1% of steps | loss-scale problem; lower LR or move to bf16 |
| H-xx | reduce-scatter / all-gather bus bandwidth | < 80% of node baseline | drain; the fast network or NVLink problem |

DeepSpeed's own `monitor` (TensorBoard / W&B / `csv_monitor`), `wall_clock_breakdown` and `comms_logger` can
supply step time and communication numbers. Map them into our `emit()` events, so `watch.py` stays the one
place alerts come from.

---

## 5. What to do, in order

| When | What | Who |
|---|---|---|
| now | agree on DS-1…DS-7 with Team 05 (model, ZeRO stage, MoE type) and Team 06 (stall budget) | 07 lead |
| week 1 ✅ | `train.py --deepspeed --zero-stage {1,2,3}` in the tiny trainer; `ds_ckpt.py` behind the same `Checkpointer` API; T18–T23; Docker drills with `--deepspeed` (§1.12) | 07 |
| week 1 | run T1–T23 on Kaggle (2 GPUs) (fp16): `support/kaggle/`, Internet on | 07 |
| week 1 | `bench_save.py --deepspeed`: sync stall per ZeRO stage on T4 | 07 |
| week 2 | GPU node: bf16, real Ψ, real stall, `ds_to_universal` timing on a real-size checkpoint, export memory | 07 + 05 |
| then | update ADR 0001 §2/§5/§8/§10, ADR 0002 §3/§5/§7, ADR 0003 §1, ADR 0004 §1 from the measured numbers | 07 |

**What not to do:** no `deepspeed` launcher; no ZeRO-Infinity NVMe offload; no automatic resize; no async engine
before T1/T3/T4/T6 pass with it; no fresh start when `load_checkpoint` finds nothing.

## Sources

- DeepSpeed config: <https://www.deepspeed.ai/docs/config-json/> (checkpoint: `tag_validation`,
  `load_universal`, `use_node_local_storage`)
- Universal checkpointing: <https://www.deepspeed.ai/tutorials/universal-checkpointing/>
- DataStates async engine: <https://www.deepspeed.ai/tutorials/datastates-async-checkpointing/>
- Getting started (launcher, save/load on all ranks): <https://www.deepspeed.ai/getting-started/>
- PR #8502 (checkpoint writer engines restore full state): <https://github.com/deepspeedai/DeepSpeed/pull/8502>
- DataStates "no latest file": <https://github.com/DataStates/datastates-llm/issues/7>
- ZeRO paper (memory formula): Rajbhandari et al., 2020, arXiv:1910.02054
