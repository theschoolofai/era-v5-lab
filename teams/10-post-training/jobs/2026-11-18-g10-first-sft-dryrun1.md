# Job request (DRAFT, not sent): G10 first SFT on the dry-run-1 checkpoint, 2,048-token code slice, traces vs short answers

Status: prepared ahead of the probe result (#558). Every `<PIN ...>` below is filled from the probe's result comment;
the list of pins and where each comes from is in "Pins still open". Nothing else changes when they are filled.

Why: the probe tells us whether dry run 1 can be fine-tuned at all (which method closes a chat turn, at what forgetting
cost, how fast the native sampler is). This job is the first SFT on that checkpoint with the data it would really get:
OCR-2 code rows, the SFT data v1 code set. Dry run 1 has a 2,048-token context and most OCR-2 rows are longer
(measured on the four shards used here: 4,050 of 30,615 rows fit, 13.2%; the whole-pack length table
`sft/results/sft_v1_lengths_p1536/sft-code-opencodereasoning-2.json` gives 18.5%), so the job trains on the rows that fit,
dropped and counted, never cut. G10's small-model study E9 (`results/e9_sft_before_rl.md`, SmolLM2 135M and 360M, one
seed) found that long reasoning traces make a weak model run out of token budget before it writes code, while the same
rows with the reasoning deleted give closed turns with running programs. That is a small-model finding; this job checks
it on our own architecture as the second arm.

```
Team:            10-post-training
Owner:           f20201351h-maker
Lead approval:   saitej123 (requested on this PR)
Question:        On the dry-run-1 checkpoint, which shape of the same OCR-2 SFT rows (those that fit 2,048 tokens) gives more RL-usable output on the easiest RL prompts, full reasoning traces (A2) or the same rows with the reasoning deleted (A4), and does either stay within +0.05 bits per byte of forgetting?
Script:          teams/10-post-training/capstone/sft_job_v1.py at this PR's head commit; it calls capstone/sft_slice_v1.py, sft_g5.py, day_one_probe.py (pins, arm cleanup, RL screen), rl-loop/team5_adapter.py and rl-data/stdio_check.py from the same commit
Command:         G10_STDIO_RUNNER=docker python teams/10-post-training/capstone/sft_job_v1.py --g5-root <G5> --run-folder <RUN> --tokenizer <TOKENIZER> --byte-table <TABLE> --heldout <HELDOUT> --heldout-sources <HELDOUT_SOURCES> --packs <PACK>/shard-00000/pack.firewalled.jsonl <PACK>/shard-00001/pack.firewalled.jsonl <PACK>/shard-00002/pack.firewalled.jsonl <PACK>/shard-00003/pack.firewalled.jsonl --rl-tasks <POOL>/out/v1/cc.jsonl --rl-ids teams/10-post-training/capstone/probe_rl_easy_ids.txt --rl-limit <PIN rl_limit> --rl-max-new 1536 --method <PIN method> --lr <PIN lr> --steps <PIN steps> --batch 16 --max-train-seconds <PIN cap_s> --gen-limit 16 --gen-max-new 1536 --seed 1 --device cuda --out out/
Config:          none: every setting is on the command line above
Seed:            1 (row order, sampling, LoRA init); the run folder's own seed 1234 is not used
Inputs:          see "Inputs and pins" (public, TSAI-staged, or stored by an earlier G10 job; sha256 for each)
Packages:        Python 3.12, torch (CUDA build), numpy, tokenizers, pyyaml, safetensors; Docker for the code verifier. CPU log used torch 2.14.1, numpy 2.5.4, tokenizers 0.23.3, pyyaml 6.0.3, safetensors 0.8.0
Hardware:        1 GPU
Max time:        <PIN max_time> minutes (at most 90, the T2 cap), enforced by TSAI's job runner on the whole process group (partial step files are valid on timeout)
Precision:       weights as stored (fp32), AdamW state fp32; the step-1 writeback check reports what bf16 storage would have kept
Measures:        pins (tokenizer and table against the run manifest); slice: rows read, dropped by reason, kept per length bucket and effort tier, sha256 of each built file; per arm: dev NLL, forgetting (held-out bpb before and after, per group), greedy format screen on 16 dev prompts (closed turn, validity, hit budget), RL screen on the easy prompts (k 8, temperature 1: code-fence share, programs that run, pass rate, mixed groups, reasons), step-1 writeback, frozen-weight and reload checks, steps done and training seconds; compare.json with the decision rule applied
Expected result: pins match; slice exactly as in the table below (3,903 train rows, 147 dev rows); base: no closed turns, RL pass 0; A2: closes some turns, many samples hit the 1,536-token budget, few programs run; A4: most samples close with a code fence and more programs run than A2, pass near 0; forgetting within +0.05 for A2, A4 unsure (E9 135M: +0.070 with repeated short rows; here A4 sees each row as often as A2); mixed groups 0-2 in both arms (E9: 0-3% below 1B parameters); total <PIN est> min (basis under "Time")
Outputs:         out/*.json, out/sft_a2/sft_report.json, out/sft_a4/sft_report.json, out/adapter.yaml (paths and hashes); no rows, generations or weights on ordinary exit; under 2 MB
Test log:        teams/10-post-training/jobs/2026-11-18-g10-first-sft-dryrun1.log (CPU, same script from a clean git archive of commit b2e0b0f, context-2,048 stand-in trained on p1536, the same four pack shards, reduced steps)
```

## Design (one question, one change between arms)

- **Rows.** The firewalled OCR-2 pack v1 (p1536), shards 0-3: SFT data v1 code rows after the eval firewall (no problem
  used to evaluate RL or effort is in them). Rows longer than the model's block size are dropped and counted. Each kept
  row is re-tokenised with the run's own tokenizer and table and must give exactly the pack's ids and loss mask.
- **The one change.** A2 trains on the rows as they are (reasoning trace, then the code). A4 trains on the same rows,
  same order, with the `<|think|>` ... `<|/think|>` block deleted; nothing is written, only admitted text is removed (the
  E9 A4 rule). A row without a reasoning block or without code after it is dropped from both arms (none on these four
  shards). A4 runs exactly the optimizer steps A2 completed, so a training-time cap cannot make the arms unequal; A4
  therefore sees fewer tokens per step. Same method, learning rate, batch, seed and evaluation for both.
- **Length buckets.** The slice keeps the pack's own length mix inside the limit and reports it per bucket; it is not
  resampled. Here 84% of training rows are 1,025-2,048 tokens long, so the arms train mostly on the longest rows that fit.
- **Dev split.** 5% of problems by a salted hash of the user turn (the system turn names the effort tier, which differs
  between completions of one problem, so it is left out); every completion of a problem is on one side. The pack's own
  held-out split (`heldout_eval_v1`) is not read.
- **Head rows.** Dry run 1's input side has no per-token embedding rows (KE2 maps each token's byte code through one
  shared projection, `teams/05-architecture/harness/week2/model.py`), and its output head is untied (#556: config v1
  leaves `ke2_output_dim` empty). So the nine chat-marker tokens have trainable rows only in `head.weight`. With
  `--method full` the whole head trains; with `--method lora_markers` LoRA adapters plus those nine head rows train
  (`--marker-rows`, weight decay 0). The probe picks which (pin `method`).
- **Evaluation (eval_v1, code part).** Forgetting: Team 5's own `evaluate()` on the held-out file dry run 1 scored
  (G5 protocol). Format validity: `chat-format/render.py` parse of greedy generations on dev prompts. Execution: the RL
  reward's sandboxed verifier (`rl-data/stdio_check.py`) on the 48 easiest RL prompts of the probe
  (`capstone/probe_rl_easy_ids.txt`), the same ids the probe screens on the base model. Not covered here: the bench's
  sealed test split and eval-mini (Team 9), and the tool-call, Indic and safety sets (chat data, not code).
- **Decision rule (applied in `compare.json`).** Among arms within +0.05 bpb forgetting, the arm with more mixed groups,
  then more running programs, becomes the default SFT row shape for the next SFT job on a TSAI checkpoint. "RL signal"
  needs at least 2 mixed groups of 48. If neither arm has it, RL on this checkpoint size waits; the SFT recipe still
  takes the winning shape. One seed and 48 prompts: a difference of one or two mixed groups is within noise and is
  reported as such.
- **What does not transfer.** Dry run 1 is a T2 checkpoint (8 layers, width 512, 16+1 experts, 1,221 steps). A
  verdict here is about a weak checkpoint at a 2,048 context; the capstone model will be larger, trained longer and may
  have a longer context, so the short-vs-long answer must be re-measured on it. SFT data v1 Dolly and Indic rows are not
  in this job (one change per comparison).

## Inputs and pins

`<G5>`, `<RUN>`, `<TOKENIZER>`, `<TABLE>`, `<HELDOUT>`, `<HELDOUT_SOURCES>` are the same TSAI-side paths the probe
(#558) used; `pins` refuses a tokenizer or table the run manifest does not record, and the adapter refuses a run folder
whose source hashes differ from `<G5>`.

| Input | Where TSAI gets it | Pin |
| :--- | :--- | :--- |
| Run folder, tokenizer, table, held-out | as for the probe (#558) | tokenizer `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`; table content `21072027b19ef6f05d57ead7a2fc9fb4c52129e491186bf38d0ba079e8d5168a` |
| OCR-2 pack, shards 0-3 (`<PACK>`) | `out/firewalled/shard-0000N/pack.firewalled.jsonl` of the OCR-2 pack job (#565), stored by TSAI | the firewalled sha256 in `sft/results/ocr2_eval_firewall_v1.json` (`applied_locally`), listed in the next table; any other file is refused before it is read |
| RL tasks (`<POOL>`) | `out/run/out/v1/cc.jsonl` of the RL data v1 pool job (`jobs/2026-11-18-rl-data-v1-pool.md`) | sha256 `91ee99512f0411aea2de4ca5eaf10b87b2d8f785ca73747bf8deb45dd6ea9be0` |
| RL ids | in the repo: `capstone/probe_rl_easy_ids.txt`, 48 ids (the probe's) | sha256 `452178c10e7325bc1cea62b0ad567a68dc32f6596f273b97dc8a36728f985c6f` |

| Pack shard | Bytes | sha256 (firewalled) |
| :--- | ---: | :--- |
| 0 | 608,603,588 | `227d97e37ede3b203b8f07a4d5e247c83ab1f1f202b1376ba755d435f2a25c06` |
| 1 | 604,823,777 | `8a5c19ac8c6793ee701c983ff76a93b14d75073267d6ce8269d2ffe398aa312f` |
| 2 | 594,146,724 | `0143f11095ac75a103f2c5d752baf758dcdcee7f275eaecc6e845dca086b698b` |
| 3 | 605,885,024 | `c2b530f12a166cc28f35e45ddb30c36c3bf14f56d35f413ab02850dd5f738e2c` |

The slice is built inside the job (step `inputs`); with the p1536 tokenizer, the committed table and these four
shards, at a block size of 2,048, it must give (measured on the CPU log, `out/inputs.json` records the same fields):

| Built file | Rows | Tokens | Trained tokens | sha256 |
| :--- | ---: | ---: | ---: | :--- |
| `a2_train.jsonl` | 3,903 | 5,686,666 | 4,582,876 | `19ac5d12d8bd79665c4d8bee2d76a42ad4d112af0cbca0fe1e3815a333669a17` |
| `a4_train.jsonl` | 3,903 | 1,377,452 | 273,662 | `c39626735fe7c25f28821a6252e65df394201396d713460f781e4685f0e9b3e5` |
| `dev.jsonl` | 147 | 217,560 | 168,892 | `29f69de4c467c27a80126b373c9820c6d7d40210225efe932a0406f7c7888538` |

Training rows by length: 15 up to 512 tokens, 615 from 513 to 1,024, 3,273 from 1,025 to 2,048; effort tiers 1k 1,576
and 4k 2,327 (no 16k or longer row fits). Token counts p50/p90/p99: A2 1,507/1,946/2,033, A4 333/527/722. The rows live
in `out/_inputs/` during the run and are deleted at exit, on success and on failure.

**Data route and what it costs.** The job reads the stored pack and needs nothing handed over by G10. Building the slice
inside the job from the public sources instead was weighed and not taken: it would run `sft/run_ocr2.py` (join, decontam,
render, pack) on four shards first, about 40 CPU-minutes per shard with one worker (median 2,374 s per shard, the
p1536 build record `sft/results/ocr2_pack_v1_p1536.md`), and it would still need the private evaluation-firewall family
list handed over, the same file the pack job needs. If #565 is not run when this job is approved, the cheapest route is
for TSAI to run #565's own two commands with `--shards 0:4` first (same code, same pins, CPU only, about 40 minutes with
four workers); this job then reads those four files unchanged and checks them by sha256.

## Time

Measured (CPU log attached, clean export, Apple M1 Pro, context-2,048 stand-in with 10,611,008 parameters trained on
p1536, reduced settings): all 5 steps ok in 289 s wall. Pins 0.0 s, slice 20.2 s, A2 202.1 s (10 steps of 16 rows: 76.1 s training, the rest evaluation, generation, forgetting and the RL screen), A4 66.1 s (the same 10 steps: 6.3 s training; no base evaluation), compare 0.0 s. These show the steps run on rows of the real length; they are not T2 timings.

Estimated for the job, from the probe's own measurements on dry run 1 (filled from #558's result):

| Part | Bound | Basis |
| :--- | :--- | :--- |
| Pins and slice | under 1 min | CPU log: slice 20 s for 2.4 GB of packs (hash 1.5 s, scan 18 s) |
| A2 training | `<PIN cap_s>` s cap, `<PIN steps>` steps | probe `sft_full` seconds per step at 16 rows x up to 256 tokens, scaled by tokens per step (A2 here: 16 x 1,457 mean = about 23,300) |
| A4 training | about a quarter of A2's | same steps, 16 x 353 mean = about 5,650 tokens per step |
| Three evaluations (base, after A2, after A4) | `<PIN eval_min>` min | probe `forgetting.json` seconds, `format.json` tokens/s for 16 greedy prompts x up to 1,536 tokens, `rl_screen.json` seconds scaled from 512 to 1,536 new tokens for `<PIN rl_limit>` prompts x 8 |

If the runner stops the job at Max time, the step files already written are valid; A2 runs first, so a timeout loses A4
and the comparison, not A2.

## Saving and resuming

The job saves no resumable state. TSAI asked that pre-training runs save through Team 7's Checkpointer (G7 restore drill,
#573; dry run 2 on 24-26 Nov is planned under the Team 7 supervisor and Checkpointer). This job is one GPU, at most 90
minutes, returns reports only (each arm's weights are deleted after the reload check, as in the probe), so a kill costs
at most one re-run of the job. A later SFT job whose weights are kept for RL or Team 9 evaluation should save through
`teams/07-infrastructure/ckpt` (`Checkpointer.save`, then `export_safetensors()`); that is not this job.

## Execution limits and failure reporting

The `--max-train-seconds` cap covers A2's training loop only, checked between optimizer steps; A4 runs A2's completed
step count. Loading, evaluation, generation and verification add time; the Python entry point does not enforce a global
deadline, so TSAI enforces `Max time` on the process group. On ordinary success or failure each arm removes its weights
and generations and the job removes `out/_inputs/`; an abrupt kill needs the runner's cleanup of `out/_inputs/` and
`out/sft_*/model.safetensors`. If `pins` fails nothing else runs (exit 1); if `inputs` fails (a pack whose sha256 is
not in the firewall record, or a block size other than 2,048 changing the slice) nothing else runs. If A2 fails, A4 runs
with its own base evaluation and `compare` reports the failure.

The verifier runs each sample in a temporary directory inside Docker; `G10_STDIO_RUNNER=local` (uid-isolated, needs
root) is the fallback. No CUDA or full-width performance claim is made from CPU evidence.

## Run-gate evidence (speed and executability)

- Runs end to end: the attached CPU log, `exit 0, `{"ok": true, "steps": 5, "failed_steps": []}`, built files with exactly the sha256 above, A4 ran A2's 10 steps, mask checks and reload parity pass in both arms, 52 KB of output with rows and weights removed`.
- Hot path added by this job: the slice builder. Counting ids from the raw line and parsing only the rows that fit
  (about one in seven) instead of parsing every 600 MB shard: 23.05 s before, 3.94 s after (3.96 s on a repeat) over the same four shards on the Mac CPU, the same 4,050 rows kept (row-id list sha256 `97655a80...`), identical output files (sha256 above).
- Step-1 writeback on the CPU log: at the first warmup learning rate (1e-5) fp32 storage kept every update to the watched
  tensor, bf16 storage would have kept 8%; the job keeps fp32 weights and optimizer state for that reason.
- Training, evaluation and the RL screen are the existing `sft_g5.py` and `day_one_probe.py` paths (no new per-token or
  per-expert Python loops). The only change to `sft_g5.py` is an opt-in `--no-before`, which saves the second base
  evaluation (forgetting, format screen and RL screen of an unchanged model).
