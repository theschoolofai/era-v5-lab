# Evaluation server design v0 (Team 9, Lab 5 design task 3)

**Status:** draft v0 for review by the Team 9 lead and TSAI. Task owner: `Nisarg189`.

The task (Capstone Lab 5 briefing, Team 9, design task 3): "Design the evaluation server so that it never takes GPU time
from training: where checkpoints are pulled from, how it picks the next checkpoint, what hardware it needs, what happens
when it falls behind, and how it alarms. A watcher that survives a restart and scores every commit." Evidence asked for
the design tasks: "the server design, the cost per checkpoint".

How to read it: **Fact** lines give a source. **Proposal** lines are Team 9's choice, for TSAI to accept or change.
**Open** lines wait for another team or TSAI. Section 10 lists them. Every number comes with the file or the formula
that gives it.

## 1. What we know

- **Fact (planning assumption, not a decision):** one node, 8 GPUs with 80 GB each (Lab 5 briefing, Teams 5 and 7). Team
  5 designs a model of about 30B total parameters (8% to 10% active) and one of about 100B (2% to 3% active).
- **Fact:** the checkpoint interval rule gives "10 min at 64 to 256 GPUs and up to 30 min on a single 8-GPU node"
  (`../07-infrastructure/docs/checkpoint_interval.md`, summary). Dry run 2 saved every 600 s: its interval commits are
  660 s to 697 s apart, and the final commit came 340 s after the one before
  (`../05-architecture/results/dryrun2-1234/commits.jsonl`, #869).
- **Fact:** dry run 2 had 176,398,881 parameters: 165,740,544 trained by Muon (one buffer each) and 10,658,337 by AdamW
  (two buffers each) (`manifest.json` of #869, keys `parameters`, `optimizer.muon_parameters`,
  `optimizer.adamw_parameters`).
- **Fact:** the scoring path today. `harness_lab/eval_watcher.py` follows `commits.jsonl` and runs
  `harness_lab/run_lab_ckpt.py` once per owned commit. For a Team 7 store, `run_lab_ckpt.py` calls Team 7's
  `export_safetensors()` (`../07-infrastructure/ckpt/ckpt.py`) on CPU, with deterministic algorithms and one thread,
  then scores on the GPU. Team 12's `run_loop.py` (#886, merged) calls the same `export_safetensors()` in its `strip`
  stage, then quantizes and scores each format.
- **Fact:** measured time per checkpoint at the dry run 1 shape (T2, 237M): Tier A 168.8 s and Tier B 112.3 s on the
  eval slot (`--team5-run`, #549); on a Tesla T4 the store path took 95.6 s (export 43.2 s) for Tier A and 133.5 s
  (export 51.5 s) for Tier B (`harness_lab/logs/watcher_gpu_test.log`). At a 600 s interval that is 7.2 to 8.9 GPU-hours
  a day (`eval_schedule.md`, section 3).
- **Fact:** the eval job never runs on a training node, and eval files live only in an approved Team 9 job's folder
  (`firewall/eval_firewall.md`, section 3, rule 4).
- **Fact:** the lag alarm `../08-monitoring/alarms/eval_lag.py` (#769, #822) pages when the newest Tier A score lags the
  newest training step by more than `--intervals` (default 2) checkpoint intervals, and its help says "k+1 if Tier A
  scores every k-th commit". Each check writes a row to `eval_lag_checks`. Panel 29 shows the lag, and panel 31 the
  seconds since the last check and since the newest batch, so a dead alarm and a dead watcher look different
  (`../08-monitoring/grafana/private_v1.json`).
- **Fact:** the watcher survives SIGKILL and SIGTERM at any point, with no commit missed or scored twice and never two
  scorers on one slot (Team 9 task 3, #902: `harness_lab/watcher_restart_test.py`, `logs/watcher_restart_test.log`).

## 2. Where the server runs, and why it takes no GPU time from training

**Proposal:**

```text
 training node (8 GPUs)                      checkpoint store                        eval node
 trainer ──save──> Team 7 Checkpointer ──> MANIFEST.json, shards, ──read only──> watcher (Tier A, Tier B)
                                           commits.jsonl, latest.json            │  one GPU slot lock
                                                                                 ├─ pull weights only
 eval_lag.py <── eval_mini (ClickHouse) <──────── rows ──────────────────────────├─ score (mini-benchmark)
     │                                                                           └─ quantize + score (Team 12)
     └─ page
```

1. **Its own GPUs.** The eval server is a separate node (or a separate job slot with its own GPUs), never a training
   node. This is rule 4 of the firewall, and it is the only way to "never take GPU time from training". A GPU on the
   training node that sits idle is still not free: the trainer's collectives, its memory headroom and its restart plan
   assume all 8.
2. **Read only on the store.** It reads `commits.jsonl`, `MANIFEST.json` and shard files. It never writes to the store
   and never deletes from it (`eval_watcher.py`: "It is read-only on the store").
3. **A possible race with saves for the store.** GPU time is not the only shared cost. The trainer writes each commit
   to the store the eval node reads from. A read at full speed while the next save runs can slow the save, and a slow
   save is training time lost (`checkpoint_interval.md`: "1.2 x save pipeline"). This is not measured. Proposal: read
   only the weight bytes (section 4), start the read only after the commit line exists (the watcher already does), and
   cap the read rate if a test shows that saves slow down. **Open:** the store's read and write bandwidth, and a save
   timed with and without an eval read beside it (Team 7).

## 3. Where checkpoints are pulled from

- **Fact:** Team 7's store is a local or mounted folder, or `s3://bucket/prefix` (`../07-infrastructure/ckpt/store.py`).
  The watcher reads `commits.jsonl` from a path on disk, so today "it cannot follow an s3:// store directly"
  (`jobs/2026-11-21-eval-watcher-dry-run-2.md`, Inputs).
- **Proposal:** a mounted store is the first choice (no extra copy). If the main run uses S3, the watcher reads the
  commit log through Team 7's `open_store()` instead of a path. That is one small change in `CommitLog` and in
  `manifest_gone()`, with the same rules (a complete line is a commit, a torn tail waits). It must not list the bucket,
  as now.
- **Open:** which store the main run uses, and whether the eval node mounts it (TSAI, Team 7).

## 4. Pull and convert: the cost that grows with the model

What `export_safetensors()` does per checkpoint today (`../07-infrastructure/ckpt/ckpt.py`):

1. it copies every file of the commit to a local folder (weights and optimizer state, in one dcp checkpoint);
2. it builds the model on CPU and loads the dcp state into it;
3. it writes a full safetensors copy;
4. it builds a second model and loads the copy back;
5. it runs the probe batch through that model on CPU, then compares the bits with the saved ones only if the saved probe
   is for the same device class (`saved is None or bits == saved`).

At the dry run sizes this costs 43 s to 52 s on the T4 (section 1). At the main-run size it is the largest part of the
cost per checkpoint. The numbers below are formulas for the main-run sizes (bytes = parameters x 4 for fp32), with the
storage dtype as the assumption; the measured rows at dry run 2 size follow the findings:

| | Dry run 2 (176M) | 30B | 100B |
|---|---:|---:|---:|
| Weights, fp32 | 705.6 MB | 120 GB | 400 GB |
| Weights and one optimizer buffer, fp32 (what step 1 copies) | 1,453.8 MB (with AdamW's two buffers on 10.7M) | about 240 GB | about 800 GB |
| Weights share of the bytes copied | 48.5% | about 50% | about 50% |
| CPU memory for steps 2 and 4 (two fp32 models) | 1.4 GB | 240 GB | 800 GB |
| Read time of the whole commit at 1 GB/s / 5 GB/s | 1.5 s / 0.3 s | 240 s / 48 s | 800 s / 160 s |
| Read time of the weights only, bf16, at 1 GB/s / 5 GB/s | 0.4 s / 0.1 s | 60 s / 12 s | 200 s / 40 s |

How the numbers are made: bytes = parameters x 4 for fp32 (x 2 for bf16); "one optimizer buffer" is Muon's momentum,
which holds most parameters (165.7M of 176.4M in dry run 2). 1 and 5 GB/s are example read rates, not measurements.

**Findings (checked in the code, then measured):**

- **F1. Half the bytes copied are not needed.** Step 1 copies the optimizer state too; scoring needs only the
  `model.*` tensors. Measured on a commit of one tenth of dry run 2's size: a dcp load of the model keys alone read
  76.5 MB of a 147.8 MB shard file (weights 70.6 MB, the rest dcp metadata), so dcp reads only the bytes it is asked
  for, in place, from a mounted store.
- **F2. Two fp32 models on CPU** (steps 2 and 4): 240 GB of RAM at 30B and 800 GB at 100B. Step 4 exists only to check
  that the file round-trips.
- **F3. The probe forward pass on CPU is wasted for a GPU-trained run.** The trainer saves the probe bits for its own
  device class (`probe_loss: {device_class: bits}`, where a GPU class is `cuda:<GPU name>`), so the CPU export never
  compares them. Step 5 still runs the full forward pass, on one CPU thread. The probe is 2 x 32 tokens
  (`lm_eval_lab.PROBE_SHAPE`), so at 30B it is about 2 x 30e9 x 64 = 3.8 TFLOP on one CPU thread, with 120 GB of fp32
  weights in RAM, for a result nobody reads.
- **F4. Each checkpoint is converted twice.** The watcher's scorer and Team 12's `run_loop.py` `strip` stage each call
  `export_safetensors()` on the same commit (#886 says so: "a 'keep the exported file' option in
  `run_lab_ckpt.export_store` would remove that copy").
- **F5. The integrity check reads the optimizer bytes too.** Both the export and a strip that hashes the files read the
  whole commit to compare sha256 values. Team 7's save already computes a logical fingerprint of every tensor inside
  `state_digest()` and keeps only the digest. If MANIFEST.json kept the `model.*` fingerprints (a few bytes per
  tensor, no extra compute at save), a reader could check the weights it loads and read nothing else.

**Built: `harness_lab/strip_ckpt.py`, and `run_lab_ckpt.py --weights`.** The strip reads the commit in place, loads
only the `model.*` tensors in their saved dtype (or bf16, converted by the load itself), checks them, and writes one
safetensors file plus a record (`<file>.json`: commit path, `model_revision`, weights sha256, written last). Checks:
`--verify files` hashes every file MANIFEST.json lists, in parallel, as the export does; `--verify fingerprints` checks
each loaded weight against MANIFEST.json `fingerprints` (F5); `--verify auto` (default) takes fingerprints when they are
there. `run_lab_ckpt.py --weights <file>` scores the file with no export: the record must name this commit and the file
sha256 must match; the probe is compared where it can be (saved bits for `cpu`, weights in the saved dtype) and
"not compared" is printed otherwise, as the export prints. 16 tests (`tests/test_strip_ckpt.py`), among them a commit
saved by FSDP2 over 2 ranks (DTensor shards in 2 files, an int16 buffer): one process strips it to exactly the full
tensors, and the fingerprints made on the shards match the ones the strip makes on the full tensors. A file that
disappears during the strip (retention) and a disk without room are clean errors that leave nothing behind.

**Measured** (`logs/strip_bench.log`: a commit with dry run 2's parameter split, 176,398,881 parameters, 1,412 MB on
disk, saved by Team 7's Checkpointer; Linux, 4 CPUs, torch 2.15.0 CPU, page cache warm; each path in a fresh process):

| Path | Wall time | Peak RSS | Read | Written |
|---|---:|---:|---:|---:|
| `export_safetensors()`, as `run_lab_ckpt.py` calls it | 3.74 s | 2,690 MB | 3,546 MB | 2,118 MB |
| strip, `--verify files` (the same guarantee) | 1.00 s | 1,185 MB | 2,830 MB | 706 MB |
| strip, `--verify fingerprints` (F5) | 0.81 s | 1,513 MB | 1,418 MB | 706 MB |
| strip, `--verify files --dtype bfloat16` | 0.75 s | 822 MB | 2,477 MB | 353 MB |

The strip with `--verify files` writes the same tensors as the export, bit for bit. Against the export it is 3.7
times faster, holds 2.3 times less memory and writes 3.0 times less. With fingerprints it reads 2.5 times less than
the export. At one tenth of the size every row scales about linearly (the export 0.47 s, the strip 0.10 s). If that
holds at 30B (not measured: 170 times the size), the export would need about 450 GB of RAM (2,690 MB x 170) where the
strip in bf16 needs about 140 GB (822 MB x 170). What remains in the strip is the check (0.51 s of 1.00 s) and the
write with its read-back for the sha256 (0.39 s); the load itself is 0.09 s.

**Proposal (one strip per checkpoint):**
1. The eval node runs `strip_ckpt.py` once per commit. The Tier A scorer, the Tier B scorer and Team 12's quantize
   stages all read its one file (`run_lab_ckpt.py --weights`, `run_loop.py --weights`). The file is deleted when every
   stage that reads it has its marker (the newest 2 strips are kept, plus any commit still waiting for a stage).
2. Team 7 keeps the `model.*` fingerprints in MANIFEST.json (F5); the strip then uses them by itself (`--verify auto`).
3. The probe check runs only where it can compare. **Open:** whether bits saved on the training GPUs can match on the
   eval GPUs (the same GPU model and the same deterministic settings are needed: Team 7).
4. The watcher calls the strip before its scorers. That is a watcher change, after #896 and #902 merge.

## 5. How it picks the next checkpoint

- **Fact:** today each watcher scores every commit it owns (`--every N`), oldest first, and marks a commit `superseded`
  when its step is committed again (checked before scoring and after the wait for the slot), or `gone` when retention
  deleted it first.
- **Fact:** retention keeps the newest 9 commits and protects every 10th: "`--keep 9 --protect-every 10` from dry run 2
  on" (`../07-infrastructure/docs/runbook.md`). So an unprotected commit lives about 9 intervals (90 min at 600 s, 4.5 h
  at 1,800 s).

**Proposal:**
1. **Order in normal running:** oldest owned commit first, as now. The trend panel needs every Tier A point.
2. **After an outage** (the watcher was down, or it is behind by more than 2 intervals): score the **newest** owned
   commit first, so the dashboard shows the current model within one scoring time, then go back to the older ones,
   oldest first. Commits that retention deletes meanwhile are `gone`, which is a recorded gap, not a silent one. Tier B
   commits are protected, so Tier B never loses one.
3. **Priority on the slot:** Tier A before Tier B. Today the two tiers take the slot lock in whatever order they ask. A
   Tier A commit waiting for a long Tier B scoring adds the Tier B time to the Tier A lag. Proposal: Tier B waits while
   a Tier A commit is pending (one more lock file, the "Tier A pending" flag).

Points 2 and 3 are watcher changes. They are not built yet.

## 6. What hardware it needs

- **GPU memory for scoring (weights in bf16, formula):** 30B is 60 GB, so it fits one 80 GB GPU with about 20 GB left
  for activations of short multiple-choice prompts. 100B is 200 GB, so it needs 3 GPUs in bf16, or 2 at 8 bits (about
  100 GB), or 1 at 4 bits (about 50 GB) through Team 12's copies.
- **Proposal:** for the 30B model, one 80 GB GPU per tier is enough to hold the model; the number of GPUs comes from the
  time per checkpoint (section 7). For the 100B model, score the bf16 model on 4 GPUs (3 for the weights, room for
  activations) and the quantized copies on 1 GPU each. This is also the setup Team 12's loop needs.
- **CPU and disk:** the strip of section 4 holds the weights once (measured: 1,185 MB peak for 706 MB of fp32 weights,
  822 MB in bf16), against about 3.8 times the weights for the export (2,690 MB). At 30B in bf16 that is about 140 GB of
  CPU memory for the strip. Local disk holds 2 stripped files at a time: 120 GB at 30B in bf16, 400 GB at 100B.
- **Fact:** the eval slot GPU type is not in the record (`manifest.json` of #869 has `gpu: redacted`). **Open:** the
  eval node's GPU type and count (TSAI).

## 7. Cost per checkpoint, and what happens when it falls behind

Cost per checkpoint `T_c` = pull + strip + Tier A + Tier B / 10 + the quantize stages (Team 12, on their own slot or on
ours). It keeps up when `T_c` is at most the interval `I` (600 s in dry run 2, up to 1,800 s on one 8-GPU node).

- **Fact:** at dry run 1 size `T_c` is about 223 s on the store path (estimate in `eval_schedule.md` section 3).
- **Open:** `T_c` at the main-run size. The scoring part grows with the active parameters times the tokens scored; the
  pull and strip parts grow with the total parameters (section 4). Both are measured on the first main-run commit, and
  the mini-benchmark (design task 1) sets the tokens scored.

**Proposal (keep-up rule):**
1. If `T_c` is above `I`, Tier A scores every k-th commit, with `k = ceil(T_c / I)`. For example, at `I` = 600 s a `T_c`
   of 900 s gives k = 2 and 1,500 s gives k = 3. At `I` = 1,800 s, a `T_c` up to 1,800 s keeps k = 1. This is the rule
   of `eval_schedule.md` section 3, with the number written down.
2. With k above 1, `eval_lag.py` runs with `--intervals k+1` (its help text already says so), and Team 7's
   `--protect-every` is set to a multiple of k, so a Tier A commit is never deleted before it is scored.
3. A second GPU (or GPU set) for Tier A is the other choice. It halves `T_c` for scoring only. It does not help the
   pull, which is bound by the store's read rate.
4. The watcher already writes the cost data: each commit's scorer time, slot wait and lag (`seconds`, `slot_wait_s`,
   `lag_s` in `state.json`). Proposal: load these into ClickHouse as well, so the panel shows `T_c` next to `I`.

## 8. How it alarms

| What fails | How it is seen | Alarm | State |
|---|---|---|---|
| The watcher dies (SIGKILL, out of memory, node reboot) | The supervisor restarts it after exit 75 or a death by signal; it goes on from `state.json` | none needed if it restarts; the lag alarm below if it does not | built (task 3). Supervisor: proposal below |
| The watcher stops with exit 1 (a checkpoint failed `--max-attempts` times) or 78 (fatal) | The supervisor does not restart it (restarting would loop) | Page: "eval watcher exit 1/78", with the last lines of its log | proposal |
| The watcher is alive but too slow, or stuck | Tier A lags training by more than `--intervals` | `eval_lag.py` page | built (#769, #822) |
| The alarm itself is dead | No new row in `eval_lag_checks` | Panel 31 (seconds since the last check) apart from panel 29 (lag) | built (#822) |
| The store is not readable | `eval.store_unavailable` event, exit 75; nothing is marked | Page if it lasts more than 1 interval | event built; page: proposal |
| A commit is deleted before it is scored | status `gone` in the state, `eval.skipped` event | Page on any Tier B `gone` (Tier B commits are protected, so a `gone` means a retention mistake) | event built; page: proposal |
| A score is out of its band (step 0) or drops (in-run) | `eval_schedule.md` sections 5.2 and 6 | Post in G9; "recommend stop" goes to TSAI | rule written; check by hand today |

**Proposal (supervisor):** run each watcher as a systemd service (or the job system's equivalent) with
`Restart=on-failure`, `RestartSec=30` and `RestartPreventExitStatus=0 1 78`, so it restarts after 75 or a signal and
stops after done, failed or fatal. This is the rule `watcher_restart_test.py` tested.

## 9. A watcher that survives a restart and scores every commit

Done in task 3 (`harness_lab/watcher_restart_test.py`, `logs/watcher_restart_test.log`): the replay of the dry run 2
commit log, with SIGKILL while scoring, after the result is written, during a ClickHouse load, SIGTERM, a restore and 12
random kills, on a fake scorer and on the real Team 7 store with the real smoke scorer. Every owned commit was done
exactly once and two scorers never shared the slot. The fixes: the scorer holds the slot lock it inherits, Linux ends it
with its watcher (`PR_SET_PDEATHSIG`), a result written before a kill is kept (`in_flight`), and a step committed again
during the slot wait is superseded.

## 9b. Edge cases checked, and what is still not tested

Checked in the code or by a test (the source is given):

| Case | Result |
|---|---|
| A commit sharded over several ranks (the main run saves from 8 GPUs) | Tested with FSDP2 over 2 ranks: the strip gives exactly the full tensors; fingerprints match across sharding (`test_strip_ckpt.py`) |
| A non-float tensor (Team 5's int16 length buffer) with `--dtype bfloat16` | Stays int16 (same test) |
| Retention deletes the commit during the strip | A StripError, nothing left (test); the watcher then marks the commit `gone` (`eval_watcher.py`) |
| No room for the stripped file | Refused before writing (test) |
| Two strips of one commit at once | Each writes its own temporary files; the file and the record that remain agree, and no temporary file is left (test) |
| fp32 weights cast to float16 | Not offered: values above 65,504 would become inf. bf16 keeps the fp32 range |
| A strip of another commit given to the scorer, or a changed file | Refused: the record must name the commit and the file sha256 must match (test) |
| The trainer's DeepSpeed backend | Refused by the strip; Team 7's `export_ds` handles it |

Found in this review, not yet in the sections above:

1. **Clocks.** The watcher's `lag_s` is the eval node's clock minus the commit time written by the trainer's clock, and
   `eval_lag.py` compares `eval_mini.loaded_at` (the ClickHouse server's clock) with the alarm host's clock
   (`eval_lag.py`: `time.time()` and `max(loaded_at)`). So the training node, the eval node, the ClickHouse host and the
   alarm host must run NTP. A skew of S seconds moves every lag by S. **Proposal:** a check at start that compares the
   eval node's clock with the ClickHouse server's `now()` and warns above 5 s.
2. **Team 12 scores the full model a second time.** `run_loop.py` runs `score_full` (Team 9's scorer on the full
   weights) on every commit, also when `--watcher-json` gives the watcher's scores, which it uses only to compare
   (`run_loop.py`, `score_full` and the report). That is one extra full scoring per commit on the GPU. **Proposal:**
   run `--stages strip,quantize,report` with `--watcher-json` on every commit, and `score_full` as a cross-check on the
   first commit only (Team 12).
3. **Each reader hashes the stripped file.** `run_lab_ckpt.py --weights` reads the whole file once for its sha256: at
   the measured 3.42 GB/s for one thread, 60 GB (30B in bf16) is about 18 s per reader, from a local disk. With Tier A,
   Tier B and Team 12 reading one file, that is up to 3 reads. **Proposal:** score Tier A and, on a Tier B commit, Tier
   B in one process on one loaded model, so the file is hashed and loaded once (not built yet).
4. **The firewall rule and a long-running server.** Rule 4 places eval files only for an approved Team 9 job and deletes
   them when the job ends. A server that runs for the whole main run is one approved job that lasts the run, with its
   files in that job's folder. **Open:** TSAI to confirm this reading for the main run.
5. **State on the eval node.** `state.json` and the out folder hold which commits are done. If the eval node's disk is
   lost, a new watcher scores again every owned commit still in the store. That is safe (each load first deletes the
   run_id's rows, so no row is doubled) but costs GPU time. **Proposal:** keep the out folder on storage that outlives
   the node.
6. **One active eval node.** The state lock is a local file lock (`fcntl.flock`). On a network file system that lock
   may not hold across hosts. **Proposal:** one eval node at a time; a standby starts only after the first is stopped.

Not tested yet (needs hardware or data we do not have):

- A real GPU, the real eval slot, and the step 1,221 weights of dry run 2 (TSAI shares them later).
- Any size above dry run 2's 176M parameters: the numbers at 30B and 100B are formulas or linear estimates.
- A network store, and a cold page cache: every timing above is warm. On a network store the bytes read set the time.
- A commit saved by 8 ranks (tested: 2), and tensor parallelism (tested: FSDP2 only).

## 10. Open items

| # | Item | Owner |
|---|---|---|
| 1 | Which store the main run uses (mounted folder or S3), and whether the eval node mounts it | TSAI, Team 7 |
| 2 | The store's read and write bandwidth; a save timed with and without an eval read beside it (section 2) | Team 7 |
| 3 | The eval node: GPU type and count, CPU memory, local disk | TSAI |
| 4 | Whether probe bits saved on training GPUs can match on the eval GPUs | Team 7 |
| 5 | Keep the `model.*` fingerprints in MANIFEST.json (F5), so the strip reads only the weights | Team 7 |
| 5b | The watcher runs the strip once per commit; Team 12's loop reads the same file (`--weights`) | Team 9 (after #896, #902), Team 12 |
| 6 | Newest-first after an outage, and Tier A priority on the slot (section 5) | Team 9 |
| 7 | `T_c` at the main-run size and the tokens of the mini-benchmark | Team 9 (design task 1), after the first main-run commit |
| 8 | Pages for exit 1/78, a store outage and a Tier B `gone` (section 8) | Team 8 with Team 9 |
| 9 | Load `seconds`, `slot_wait_s`, `lag_s` into ClickHouse for a cost panel | Team 9 with Team 8 |
| 10 | NTP on the training node, the eval node, ClickHouse and the alarm host; a clock check at watcher start (9b.1) | TSAI, Team 9 |
| 11 | Team 12 `run_loop.py` with `--watcher-json` skips `score_full` after the first commit (9b.2) | Team 12 |
| 12 | One scorer process for Tier A and Tier B on a Tier B commit (9b.3) | Team 9 |
| 13 | The main-run eval server as one approved job that lasts the run (9b.4) | TSAI |
| 14 | The eval out folder on storage that outlives the node; one active eval node (9b.5, 9b.6) | TSAI, Team 9 |

## Sources

Capstone Lab 5 briefing (Team 9, Team 5, Team 7 and Team 12 sections); `eval_schedule.md` sections 3, 4 and 6;
`firewall/eval_firewall.md` section 3; `harness_lab/eval_watcher.py`; `harness_lab/run_lab_ckpt.py`;
`harness_lab/logs/watcher_gpu_test.log`; `jobs/2026-11-21-eval-watcher-dry-run-2.md`;
`../07-infrastructure/ckpt/ckpt.py` (`export_safetensors`); `../07-infrastructure/ckpt/store.py`;
`../07-infrastructure/docs/checkpoint_interval.md`; `../08-monitoring/alarms/eval_lag.py`;
`../05-architecture/results/dryrun2-1234/` (#869); #549, #769, #822, #886; #902 (Team 9 task 3);
`harness_lab/strip_ckpt.py`, `harness_lab/tests/bench_strip.py`, `harness_lab/logs/strip_bench.log`.

