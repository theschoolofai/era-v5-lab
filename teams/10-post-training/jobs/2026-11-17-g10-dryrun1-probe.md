# Job request: G10 day-one probe of the dry-run-1 run folder

Probe request for the completed #475 run; lead approval is requested, not yet granted. Reads the #475 run
folder in place: no checkpoint leaves TSAI's machine, nothing is written outside `out/`.

```
Team:            10-post-training
Owner:           f20201351h-maker
Lead approval:   pending saitej123
Question:        On the dry-run-1 checkpoint, which SFT setup makes the base model close a chat turn (full, LoRA, LoRA + marker head rows, Deletion Tuning, marker rows only), and does the base or SFT'd model get any RL signal on the easiest RL prompts?
Script:          teams/10-post-training/capstone/day_one_probe.py   (in this PR)
Command:         G10_STDIO_RUNNER=docker python teams/10-post-training/capstone/day_one_probe.py --g5-root <checkout #475 ran from> --run-folder <#475 run folder> --tokenizer <p1536 tokenizer.json> --byte-table <p1536 raw_table_P32.npz used by #475> --heldout <heldout file #475 scored> --heldout-sources <its sources file> --sft-train <inputs>/sft_train.jsonl --sft-eval <inputs>/sft_eval.jsonl --rl-tasks <RL data v1 cc.jsonl from the PR 97 rebuild kit> --rl-ids <inputs>/rl_easy_ids.txt --rl-limit 48 --rl-max-new 512 --sft-steps 300 --sft-max-train-seconds 600 --device cuda --out out/
Config:          none: every setting is on the command line above
Seed:            1 (sampling and SFT); the run folder's own seed 1234 is not used
Inputs:          #475 run folder (manifest.json, checkpoint.pt, summary.json); p1536 tokenizer and Team 4 table as used by #475; SFT rows: Dolly-15k SFT half (human-written, CC-BY-SA-3.0) rendered in G10 chat format v0 with p1536 ids and assistant-only masks, 5,255 train / 589 eval rows <= 256 tokens (~6 MB); RL: 48 ids from RL data v1's easiest rung (code_contests, codechef/hackerearth, statement <= 310 tokens; CC-BY-4.0)
Hardware:        1 GPU
Max time:        60 minutes, enforced by TSAI job runner (partial reports are valid on timeout)
Precision:       weights as stored (fp32); the mismatch step also measures bf16 autocast
Measures:        adapter status and hashes; held-out bpb per slice; native sampler tokens/s (last-position head vs KV cache, identical tokens); share of tokens outside objective_v1's trust region from numerics alone and expert-set flips (1 row vs 8, fp32 vs bf16) on CUDA; base format screen (64 prompts); RL screen (48 prompts x 8 samples: pass rate, mixed groups, failure reasons); per SFT arm: closed <|im_end|> on 64 eval prompts, eval NLL, forgetting (held-out bpb before/after), step-1 writeback (fp32 vs what bf16 storage would keep), frozen-weight and reload checks, RL screen after full and LoRA + markers
Expected result: base: 0 closed turns, RL pass 0 with "no code block"; full and LoRA + marker rows close most turns, LoRA and DT alone close none (seen on the d128 stand-in, 2 seeds); RL screen after SFT still 0 (Dolly has no code); mismatch below 0.5% (stand-in: 0.11-0.17% bf16 vs fp32 on MPS/CPU); total ~25-40 min (ESTIMATE: the CPU test log took 53 min on a loaded laptop at 1/10 the parameters but with 30 SFT steps and 8 RL prompts; on one GPU the evaluation passes dominate and the five 300-step arms are capped at 10 min each, so 25-40 minutes is uncertain; the runner must enforce the 60-minute total deadline and may stop unfinished arms)
Outputs:         out/*.json and out/sft_*/sft_report.json plus adapter.yaml (paths/hashes), no rows or generations on ordinary exit; under 2 MB expected at these settings
Test log:        evidence/2026-11-16-g10-capstone-rehearsal/validation.md (attached CPU logs; d128 reduced --sft-steps 30 --rl-limit 8, plus current-code d64 publication smoke)
```

Notes for the reviewer
- `<inputs>` = three files G10 hands to TSAI through the usual data route, not committed to the repo (G10 keeps task
  ids and rendered rows out of Git): `sft_train.jsonl` (sha256 `c273a4d7a7b6fb9a0520829a8c15a1feb00899e4fa0f0deb60931de39b7cbd62`), `sft_eval.jsonl` (`f77fc96c15be384e5634124f4655f43ee2513857547f0b3cc3992fdb984a556e`),
  `rl_easy_ids.txt` (48 ids, `452178c10e7325bc1cea62b0ad567a68dc32f6596f273b97dc8a36728f985c6f`). The CPU test log used the same SFT files; its RL screen used the
  <= 160-token subset of the same rung, because the d128 stand-in's context is 256.
- The adapter refuses a run folder whose manifest source hashes differ from `--g5-root`'s harness: run from the
  checkout #475 ran from. If #475 was launched with a tokenizer-identity override (Team 5's `artifacts.py` pins v0),
  the manifest records p1536 and the adapter checks against that.
- heldout_v1's bn/pa/as documents do not round-trip under p1536 with Team 5's strict loader. Pass whichever held-out
  file #475 actually scored.
- `--sft-max-train-seconds 600` caps each of the five arms; `--rl-limit 48` caps the RL screens; every step records
  its own time and a failed step is recorded without stopping the rest.
- If Docker is not available, `G10_STDIO_RUNNER=local` (uid-isolated, needs root); if neither is allowed, drop
  `--rl-tasks/--rl-ids` and the job still answers the SFT half of the question.

## Execution limits and failure reporting

The five 600-second limits cover training loops only, checked between optimizer steps. Loading, calibration, evaluation, generation and verification add time. The Python entry point does not enforce a 60-minute global deadline: TSAI must enforce `Max time` on the whole process group. A deadline can leave some steps unfinished; report that explicitly, retaining completed JSON. On ordinary success or failure each arm removes its weights and generations; an abrupt process kill requires job-runner cleanup before returning artifacts. The script continues independent checks after an ordinary step failure, writes `summary.json`, and exits nonzero if any step failed.

DT is an exploratory diagnostic arm. Calibration can miss experts and initialize more deletion than the intended prior; the report records uncovered layers and deletion at initialization. It is not an endorsed training recipe. No CUDA or full-width performance claim is made from CPU evidence.
