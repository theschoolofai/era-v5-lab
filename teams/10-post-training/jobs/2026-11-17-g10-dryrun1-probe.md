# Job request: G10 day-one probe of the dry-run-1 run folder

TSAI agreed on 16 Nov to run this probe on the dry run 1 checkpoint (#475). It reads the #475 run folder in place: no
checkpoint leaves TSAI's machine, nothing is written outside `out/`, and every input is public or already staged by
TSAI. Nothing private has to be handed over.

```
Team:            10-post-training
Owner:           f20201351h-maker
Lead approval:   saitej123 (requested on this PR)
Question:        On the dry-run-1 checkpoint, which SFT setup makes the base model close a chat turn (full, LoRA, LoRA + marker head rows, Deletion Tuning, marker rows only), and does the base or SFT'd model get any RL signal on the easiest RL prompts?
Script:          teams/10-post-training/capstone/day_one_probe.py at this PR's head commit (base: main 5aed520); it calls capstone/probe_inputs.py, sft_g5.py, bench_sampling_g5.py, mismatch_g5.py, rl-loop/team5_adapter.py and rl-data/stdio_check.py from the same commit
Command:         G10_STDIO_RUNNER=docker python teams/10-post-training/capstone/day_one_probe.py --g5-root <G5> --run-folder <G5>/out/dryrun1-1234 --tokenizer <G5>/inputs/tokenizer_c3.json --byte-table <G5>/inputs/raw_table_c3_P32.npz --heldout <G5>/inputs/heldout_v1.jsonl --heldout-sources <G5>/inputs/heldout_v1_sources.jsonl --sft-dolly <DATA>/databricks-dolly-15k.jsonl --rl-tasks <POOL>/out/v1/cc.jsonl --rl-ids teams/10-post-training/capstone/probe_rl_easy_ids.txt --rl-limit 48 --rl-max-new 512 --sft-steps 300 --sft-max-train-seconds 480 --device cuda --out out/
Config:          none: every setting is on the command line above
Seed:            1 (sampling and SFT); the run folder's own seed 1234 is not used
Inputs:          see "Inputs and pins" below (all public or TSAI-staged; sha256 for each)
Packages:        Python 3.12, torch (CUDA build), numpy, tokenizers, pyyaml, safetensors; Docker for the code verifier. CPU log used torch 2.14.1, numpy 2.5.4, tokenizers 0.23.3, pyyaml 6.0.3, safetensors 0.8.0
Hardware:        1 GPU
Max time:        60 minutes, enforced by TSAI's job runner on the whole process group (partial reports are valid on timeout)
Precision:       weights as stored (fp32); the mismatch step also measures bf16 autocast
Measures:        adapter status and hashes; held-out bpb per slice; native sampler tokens/s (last-position head vs KV cache, identical tokens); share of tokens outside objective_v1's trust region from numerics alone and expert-set flips (1 row vs 8, fp32 vs bf16) on CUDA; base format screen (64 prompts); RL screen (48 prompts x 8 samples: pass rate, mixed groups, failure reasons); per SFT arm: closed <|im_end|> on 64 eval prompts, eval NLL, forgetting (held-out bpb before/after), step-1 writeback (fp32 vs what bf16 storage would keep), frozen-weight and reload checks, RL screen after full and LoRA + markers
Expected result: inputs: 5,255 train / 589 eval rows with the sha256 below; base: 0 closed turns, RL pass 0 with "no code block"; full and LoRA + marker rows close most turns, LoRA and DT alone close none (seen on the d128 stand-in, 2 seeds); RL screen after SFT still 0 (Dolly has no code); mismatch below 0.5% (stand-in: 0.11-0.17% bf16 vs fp32 on MPS/CPU); total 30-55 min (ESTIMATE, basis under "Time")
Outputs:         out/*.json, out/sft_*/sft_report.json, out/adapter.yaml (paths and hashes); no rows, generations or weights on ordinary exit; under 2 MB
Test log:        teams/10-post-training/jobs/2026-11-17-g10-dryrun1-probe.log (CPU, same script from a clean git archive of commit 3accc41, d128 stand-in, reduced steps)
```

## Inputs and pins

`<G5>` is the checkout #475 ran from (`train_week2.py` at 71bc0fb with the #474 patch) with #475's own staged
`inputs/` and its run folder `out/dryrun1-1234`. The adapter refuses a run folder whose manifest source hashes differ
from `<G5>`'s harness, so it must be that checkout.

| Input | Where TSAI gets it | Pin |
| :--- | :--- | :--- |
| Run folder | #475 output, kept by TSAI | `manifest.json`, `checkpoint.pt`, `summary.json`; the adapter checks `model_hash` against `summary.json` |
| Tokenizer | #475's staged frozen C3 | sha256 `15468e66457b43af79f695cbe585c0d03e3cfe7a4a5d04d189dd3c6b9f02ddc3` |
| Byte table | #475's staged raw P32 table (`build_tables.py --pos-dims 32`) | file `dfbb3207bba13cb46899afc7aad06e876a84961f6a4e206980cd39071f2926d3`, content `fc5e5f8ffacbe93ecdedc276661edfd43ed9a13621eb4a68166ef80e24e88f9b` |
| Held-out | the heldout_v1 file and source map #475 scored | as recorded in #475's `manifest.json` |
| Dolly-15k | public: `databricks/databricks-dolly-15k` @ `bdd27f4d94b9c1f951818a7da7fd7aeea5dbff1a`, file `databricks-dolly-15k.jsonl` (CC-BY-SA-3.0, human-written) | sha256 `2df9083338b4abd6bceb5635764dab5d833b393b55759dffb0959b6fcbf794ec`, 13,085,339 bytes |
| RL tasks | `out/run/out/v1/cc.jsonl` of the RL data v1 pool job (`jobs/2026-11-18-rl-data-v1-pool.md`) | sha256 `91ee99512f0411aea2de4ca5eaf10b87b2d8f785ca73747bf8deb45dd6ea9be0` (the `expected` value in `rl-data/rebuild_v1/pins_v1.json`) |
| RL ids | in this PR: `capstone/probe_rl_easy_ids.txt`, 48 ids | sha256 `452178c10e7325bc1cea62b0ad567a68dc32f6596f273b97dc8a36728f985c6f` |

The SFT rows are built inside the job (step `inputs`, `capstone/probe_inputs.py`): row i of the Dolly file becomes
`sft-dolly-15k/i`, is rendered by `sft/convert.py` in G10 chat format v0 (assistant body plus `<|im_end|>` trained),
re-tokenised with the run's own tokenizer and checked byte for byte against the table; the pre-training half of Dolly
is refused by id hash and rows over 256 tokens are dropped, not cut. With the C3 tokenizer and table above the job
must report:

| Built file | Rows | Bytes | sha256 |
| :--- | ---: | ---: | :--- |
| `sft_train.jsonl` | 5,255 | 5,824,801 | `ce978dd10132f6371cc6f4a64407b9c8ba2f4b338e90fc4b915fecfc78d6bd6c` |
| `sft_eval.jsonl` | 589 | 652,723 | `fedddcc0d4dc0ef0ca5d39135e17fad293fee9f74a0d6fad677469b597543082` |

`out/inputs.json` records these values; a different sha256 means a different Dolly file, tokenizer or table. The rows
live in `out/_inputs/` during the run and are deleted at exit, on success and on failure.

Why the rows are built in the job: #475 trained with the frozen C3 tokenizer, while the rehearsal rows were p1536 ids.
The text is the same, but 102 of the 5,255 train rows get different ids under C3, so p1536 rows would feed the
checkpoint partly wrong tokens. With the p1536 tokenizer the same builder reproduces the rehearsal files byte for byte
(`c273a4d7...`, `f77fc96c...`), which checks that it is the same pipeline.

The RL ids are RL data v1 code_contests problems (codechef/hackerearth, statement up to 310 p1536 tokens), a random 48
of 754 with seed 20261116. Under C3 the statements fit the 2,048-token context with room for 512 new tokens; any that
does not is counted as `skipped_too_long`, not dropped silently.

## Time

Measured (CPU log attached, clean export of commit 3accc41, Apple M1 Pro, d128 stand-in with 24.7M parameters,
reduced settings): all 12 steps ok in 800 s wall. Inputs 4.4 s, adapter 1.9 s, forgetting 25.3 s, sampling 21.6 s,
mismatch 116.1 s, format 19.4 s, RL screen 7.7 s (4 prompts), SFT arms 113.7-132.0 s each, of which training was
14.4-22.2 s (30 steps) and the rest was evaluation, generation, forgetting and the reload check.

Estimated for the job (not measured; no GPU run of this script on the T2 checkpoint exists):

| Part | Bound | Basis |
| :--- | :--- | :--- |
| Five SFT arms, training | at most 40 min (5 x 480 s cap) | 300 steps of 16 rows of at most 256 tokens is about a quarter of a T2 pre-training step's tokens per step; the cap stops an arm that is slower |
| Evaluation, generation, forgetting, three RL screens, mismatch | about 10-15 min | three screens of 48 prompts x 8 samples x up to 512 new tokens with the KV-cache sampler; the base and Dolly-trained models are expected to write no code block, so the verifier mostly returns at once |
| Loading, inputs, adapter | under 1 min | 6.3 s on the CPU log |

So 30-55 minutes, inside the 60-minute limit even if every arm hits its cap. If the runner stops the job at 60
minutes, the step files already written are valid and `summary.json` is missing; the arms run in the order full,
markers, LoRA, LoRA + markers, DT, so the most important comparison finishes first.

## Execution limits and failure reporting

The five 480-second limits cover training loops only, checked between optimizer steps. Loading, calibration,
evaluation, generation and verification add time. The Python entry point does not enforce a 60-minute global deadline:
TSAI must enforce `Max time` on the whole process group. A deadline can leave some steps unfinished; the completed
step JSON files stay valid. On ordinary success or failure each arm removes its weights and generations, and the probe
removes `out/_inputs/`; an abrupt process kill needs the job runner's cleanup of `out/_inputs/` and
`out/sft_*/model.safetensors` before results are returned. The script continues independent checks after an ordinary
step failure, writes `summary.json`, and exits nonzero if any step failed. If the `inputs` step fails, nothing else
runs (every later step reads its rows).

The code verifier runs each sample in a Python temporary directory (removed after each check) inside Docker. If
Docker is not available, `G10_STDIO_RUNNER=local` (uid-isolated, needs root); if neither is allowed, drop
`--rl-tasks/--rl-ids` and the job still answers the SFT half of the question. If the pool job's `cc.jsonl` is not in
TSAI storage yet, drop the same two flags.

DT is an exploratory diagnostic arm. Calibration can miss experts and initialize more deletion than the intended prior;
the report records uncovered layers and deletion at initialization. It is not an endorsed training recipe. No CUDA or
full-width performance claim is made from CPU evidence.
