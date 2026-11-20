# Job request: Deletion Tuning SFT on dry run 1, keeping the canary's three input files (DRAFT, NOT RUNNABLE)

Status: draft, not sent. NOT RUNNABLE until every item under "Blocked by" is cleared and a test log is attached.
Follows: `2026-11-18-g10-first-sft-dryrun1.md` (#587), same inputs and pins. That job runs `--method full` and deletes every weight at its exit. This request runs the same job with `--method dt_markers` (Deletion Tuning plus the nine marker rows) and keeps one arm's state, so that the Task 11 canary (`2026-11-17-dt-then-rl-code.md`) has its inputs.

```
Team:            10-post-training
Owner:           10-post-training (lead saitej123)
Lead approval:   pending (saitej123)
Question:        Does the DT SFT arm leave the three files the Task 11 canary reads (model.safetensors, dt_keep_masks.bin, dt_keep_masks.bin.json) with sha256 values that match what the job reports?
Script:          teams/10-post-training/capstone/sft_job_v1.py
Command:         G10_STDIO_RUNNER=docker python teams/10-post-training/capstone/sft_job_v1.py <the #587 arguments unchanged> --method dt_markers --keep-canary-state-dir keep/ --keep-arm a2 --out out/
Config:          none: every setting is on the command line. DT settings: the defaults of sft_g5.py (--dt-targets g5_mlp, alpha 100 to 1000, lambda 1e-5, eta 0.05, prior strength 3.0, unseen official, 64 calibration rows). Whether these are the right values for dry run 1 is not decided here
Inputs:          the same as #587 (run folder from #475, pack shards, RL pool, tokenizer, byte table, held-out files)
Hardware:        1 GPU
Max time:        as #587 (90 minutes, --deadline-minutes 85); the DT arm's time on the real shape is not measured
Precision:       weights as stored (fp32), AdamW state fp32
Measures:        the #587 measures for each arm, plus DT: deletion at init and final, mask checks, frozen-weight check; and the sha256 of the three kept files
Expected result: unknown. The stand-in only shows that the files are written and the canary loads them
Outputs:         out/*.json reports to the repo. keep/a2/ (model.safetensors about 0.95 GB in fp32 for 237,052,416 parameters, two mask files, SHA256SUMS) to TSAI storage. No weights in the repo
Test log:        CPU, stand-in model, from the job script itself: exit 0, 5 of 5 steps, three files with sha256 equal to summary.json; the staged canary then loaded them with the sha pins and ran 3 updates (stand-in reward) with deleted-nonzero 0. See the Update 20 Nov 2026 section of `2026-11-17-dt-then-rl-code.md`
```

## Blocked by

1. **The #587 result.** It decides the arm (A2 or A4) and the rows.
2. **DT settings.** The values of the DT flags for the real model are the lead's and the Task 11 owner's choice; the defaults above are only what the stand-in used.
3. **A probe expectation for the #475 checkpoint,** computed by Team 5's own loading path (see `2026-11-19-g10-rl-dryrun1.md`, "Questions for TSAI", item 4), because the adapter refuses a delivered run folder without it.
4. **Lead approval** and the mask file size on the real shape (stand-in: 81 KB for 1.67 million targeted weights; the real size is not measured).

## What leaves the job and what does not

One folder `keep/a2/` (or `a4`): three files and `SHA256SUMS`. The job's own output folder still has both arms' mask files next to the reports (as for any DT arm); it never holds a weight file, the built rows, the held-out answers or the generations. The other arm's weights are deleted.

## Notes

- The A2/A4 equal-steps rule is unchanged: A4 runs for the steps A2 completed. Whether that is the right comparison for DT is not decided here.
- No benchmark item text goes into any file in this request.
