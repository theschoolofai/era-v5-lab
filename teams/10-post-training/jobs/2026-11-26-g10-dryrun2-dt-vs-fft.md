# Job request: Dry run 2 matched-step SFT comparison (Full FT vs LoRA vs Deletion Tuning) — DRAFT, NOT RUNNABLE

Status: draft prepared on Week 4 D1 (21 Nov 2026) ahead of dry run 2 (Tue 24 Nov – Thu 26 Nov). **NOT RUNNABLE** until dry run 2 completes on D5 (Thu 26 Nov), Team 5 merges KE2/KAS head integration into `week2/model.py`, and a local stand-in test log on the dry-run-2 model class is attached.

Answers Gate 3 item 7 (Instructor ruling, 21 Nov 2026): compares **Deletion Tuning vs LoRA vs Full FT** at equal optimizer steps on the **dry run 2 checkpoint** (test-scale + untied KE2/KAS head `a10_kas_tokdrop` + Team 7 Checkpointer via `#608`) and saves the DT arm's three canary files (`model.safetensors`, `dt_keep_masks.bin`, `dt_keep_masks.bin.json`, `SHA256SUMS`) so the required **DT-then-RL chain** (`jobs/2026-11-17-dt-then-rl-code.md`) can run immediately after.

```
Team:            10-post-training
Owner:           10-post-training (lead saitej123)
Lead approval:   saitej123 (settings and protocol approved 21 Nov 2026; runnable once dry run 2 checkpoint + stand-in log land)
Question:        On the dry run 2 checkpoint (KE2/KAS untied head), at equal optimizer steps on the #587-selected OCR-2 slice, how do Deletion Tuning (paper-repo settings), LoRA, and Full FT compare on task NLL, chat-format validity, RL mixed groups, and held-out forgetting bpb?
Script:          teams/10-post-training/capstone/dryrun2_dt_compare.py (calls capstone/sft_g5.py, capstone/sft_slice_v1.py, capstone/day_one_probe.py, capstone/keep_weights.py)
Command:         G10_STDIO_RUNNER=docker G5=<G5> T5_OUT=<T5_OUT> STORE=/shared/ckpt TOKENIZER=<TOKENIZER> TABLE=<TABLE> HELDOUT=<HELDOUT> HELDOUT_SOURCES=<HELDOUT_SOURCES> WORK=work/ bash teams/10-post-training/capstone/dryrun2_job_chain.sh -- --heldout <HELDOUT> --heldout-sources <HELDOUT_SOURCES> --packs <PACK>/shard-00000/pack.firewalled.jsonl <PACK>/shard-00001/pack.firewalled.jsonl <PACK>/shard-00002/pack.firewalled.jsonl <PACK>/shard-00003/pack.firewalled.jsonl --rl-tasks <POOL>/out/v1/cc.jsonl --rl-ids teams/10-post-training/capstone/probe_rl_easy_ids.txt --slice-arm <A2_OR_A4_FROM_587> --steps 243 --batch 16 --full-lr 1e-4 --lora-lr 1e-3 --dt-lr 5e-4 --marker-lr 1e-2 --dt-targets g5_gate --dt-alpha-start 100 --dt-alpha-end 1000 --dt-eta 0.00048828125 --dt-lambda 1e-5 --dt-prior-strength 3.0 --keep-canary-state-dir keep_canary/ --keep-weights-dir keep_t7/ --keep-weights-arms full,lora,dt --deadline-minutes 115 --device cuda --out out/
Chain:           dryrun2_job_chain.sh (G10) runs, in order: (1) the run folder: Team 5's <T5_OUT> as it is if it still has checkpoint.pt, else rebuilt from the Team 7 store /shared/ckpt, run id dryrun2-1234 (capstone/run_folder_from_store.py --device cuda: Team 7 export, strict keys, probe bits on the training GPU class, model hash == summary.json); (2) capstone/make_probe_file.py, the probe g5_delivery needs; (3) capstone/router_bias_reach.py, report only; (4) the wrapper above, unchanged; (5) each arm's sft_report.json must say router_bias_unchanged; im_end at turn ends and mid-reply goes to work/arm_checks.json. Rehearsed end to end on a KAS V2 + bias_gamma 0.001 CPU stand-in whose store is laid out like /shared/ckpt/dryrun2-1234 (log attached below). The rebuilt run folder stays in work/, never in out/.
Router bias:     stays as delivered. Arm bias_gamma 0.001 (the model is built from the run's own manifest), update_router_bias() is never called in any arm (owner's rule, 23 Nov: "The bias stays as delivered. Do not keep updating it in SFT or RL"); each arm's report checks it (router_bias_unchanged). Never freeze it by setting bias_gamma 0: gamma 0 ignores the bias, and on the CPU stand-in 43-70% of positions then pick a different expert set.
Marker lr:       1e-2, not 1e-3 (work/adp-2026-11-24/PREREG_marker_lr.md + marker_lr/RESULT.md): the nine markers sit at the prior floor -18.79 nats; the rows lift at 0.94x the AdamW budget lr x sum|z|, so 1e-3 gives about 13.5 nats in 243 steps, short of the deficit.
                 With sft_g5's schedule (S = 134.1 multiplier-steps) and a base-trunk coherence proxy c 0.974 to 0.985, 1e-2 gives a 54.0-nat budget against the 28.3 needed. Higher is not safer: the rows alone lift im_end mid-reply at 0.55 of the turn-end lift.
Control:         the frozen arms get the nine marker rows, so part of their chat-format score is the rows alone. No matched rows-only arm runs in this job (day_one_probe's markers arm trains on Dolly at a fixed 1e-3 and its own step count, so it is not comparable). Read the chat column against each arm's im_end_at_targets (turn end vs mid-reply, before and after).
Config:          none (all settings on command line; DT settings match the 17 Nov paper-repo port check: `g5_gate`, `lr 5e-4`, `alpha 100 -> 1000`, `eta 1/2048`, `lambda 1e-5 -> 0`, `band_at_init` logged before step 1)
Inputs:          dry run 2 run folder (from Team 5 on D5, Thu 26 Nov, with KE2/KAS head & Team 7 Checkpointer `#608`); pinned OCR-2 firewalled pack shards 0–3 (`#565`); RL data v1 `cc.jsonl` (`#564`); Team 5 held-out v1; frozen p1536 tokenizer & KE2 byte table.
Hardware:        1 GPU (>= 40 GB)
Max time:        120 minutes (`--deadline-minutes 115`; Full FT sets completed step budget, LoRA and DT run exact equal steps)
Precision:       fp32 weights and AdamW state (same as `#587`; forgetting bpb compared with `forgetting.py`, Team 9 watcher scores ARC-Challenge/HellaSwag on `keep_t7/g10-dr2-{full,lora,dt}` in bf16 autocast)
Measures:        per arm (base, full, lora, dt): matched optimizer steps, eval NLL, held-out forgetting Δbpb (`0.05` limit, `0.01` at-limit mark), chat-format validity, closed turns, RL screen mixed groups / pass rate, DT `band_at_init` and `deletion_final`, reload parity, and SHA-256 of kept DT canary & Team 7 run folders.
Expected result: unknown on KE2/KAS head; surrogate baseline is `results/dt_vs_fft.md` (`SmolLM2-135M`/`1.7B`).
Outputs:         out/*.json and out/compare.md (under 5 MB) back to the repo. `keep_canary/dt/` (3 files + SHA256SUMS for Task 11 DT-then-RL) and `keep_t7/g10-dr2-{full,lora,dt}/` (Team 7 Checkpointer run folders for Team 9 watcher) to TSAI storage. No weights, training rows, or generations in Git.
Test log:        REQUIRED before sending. Offline unit tests pass (`capstone/test_dryrun2_dt_compare.py`). Attached so far: `2026-11-26-g10-dryrun2-dt-vs-fft.log` = the wrapper end to end, exit 0, all three arms + screens + both keep dirs, on the DENSE head, Mac CPU, a 20-step stand-in run folder, `--origin g10_rehearsal`. It is NOT the KE2/KAS head and NOT `g5_delivery`. Still to attach: a staged CPU stand-in log on Team 5's merged KE2/KAS `LanguageModel` once Team 5 lands dry run 2's `model.py`.
```

## Placeholders still open (questions, by owner)

- `<T5_OUT>` (Team 5): where is the dry run 2 job's `./out/dryrun2-1234` (manifest.json, summary.json) on the job machine, and is its checkpoint.pt kept? Without manifest + summary the weights cannot be bound to the run.
- `<HELDOUT>`, `<HELDOUT_SOURCES>`, `<TOKENIZER>` (Team 5 / TSAI): the exact `./inputs/heldout_v1.jsonl`, `heldout_v1_sources.jsonl` and `tokenizer_p1536.json` the run used (their hashes are in its manifest; the chain checks them).
- `<G5>` (TSAI): the lab checkout on the job machine, at a commit that has #717 and #748 (main eef1834d or later, same train_week2.py as the run).
- GPU class (TSAI): the same GPU model as the training run, so step 1 compares Team 7's probe bits instead of skipping them.
- Store (Team 7): `/shared/ckpt` with run id `dryrun2-1234` is read through Team 7's export by store root + run id; we do not call `ckpt.py pin`. Confirm no retention prunes the final step before this job.
- `<PACK>`, `<POOL>` (TSAI staging): the pinned OCR-2 shards 0-3 and RL data v1, as in dry run 1.

## Time with the KAS head

G6 measured the dry run 2 pretraining step at 1,378 ms with kas_v2 against 687 ms dense (A100-80GB, T2, 8 x 2048, bf16; vaibh27/era-v5-lab PR 97, results/speed_dryrun2.md): 2.0x. Training per arm is capped by the wrapper's `--max-train-seconds` (default 1,200 s), so 115 minutes still holds; what the 2.0x can cost is completed steps. Dry run 1's A2 measured 8.6-36 s per step at about 23,300 tokens; A4 (about 5,650 tokens) at 2.0x gives about 4.4-18 s per step, so Full FT completes 66-243 steps inside the cap, and LoRA and DT run the same number (the wrapper's rule). Evaluations and screens also run the KAS head; the wrapper stops a later arm at its deadline and names it. Not measured: the T2 SFT step on the job GPU with our path, and only one base-trunk proxy model for the coherence c.

## Blocked by

1. **Dry run 2 checkpoint (Team 5, D5 Thu 26 Nov).**
2. **Team 5 KE2/KAS head code on `main`** (`#694`/`#702` untied `a10_kas_tokdrop` integrated in `week2/model.py`, plus `#706` optimizer split) and a local stand-in test log verifying `sft_g5.py`, `team5_adapter.py`, `keep_weights.py`, and `dryrun2_dt_compare.py` against that exact `model.py`.
3. **`#587` result** (selects `--slice-arm a2` or `a4`; defaults to `a4`).
4. **Probe file** (if dry run 2 `#608` Checkpointer `probe_loss` is present, verify compatibility; otherwise generate via `capstone/make_probe_file.py`).

## Notes

- **Eval firewall:** this job never reads ARC-Challenge, HellaSwag, or any Team 9 benchmark. Team 9's watcher scores the kept Team 7 run folders (`keep_t7/g10-dr2-{full,lora,dt}/`) and hands fraction-scaled (`value/100`, `stderr/100`) rows to `sft/tests/forgetting.py`.
- **Gate 3 item 7 chain:** once `keep_canary/dt/` is stored, run `jobs/2026-11-17-dt-then-rl-code.md` against `keep_canary/dt/` to complete both required halves of Gate 3 item 7 (DT vs LoRA vs full FT + DT-then-RL).
