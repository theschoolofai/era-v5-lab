# Job request: first SFT on dry run 1, keeping one checked weights file for Team 9 (DRAFT, NOT RUNNABLE)

Status: in PR #634 for lead review. NOT RUNNABLE: TSAI must not run this until every item under "Blocked by" is cleared and a test log is attached.
Follows: `2026-11-18-g10-first-sft-dryrun1.md` (#587). That job returns reports only; its weights are deleted after the
reload check. This request is the same SFT with the weights kept, so that Team 9 can run the forgetting benchmarks
(`2026-11-18-g10-eval-mini-forgetting.md`) and later RL can load them.

```
Team:            10-post-training
Owner:           10-post-training (lead saitej123)
Lead approval:   pending (saitej123)
Question:        Does the SFT arm chosen by the #587 decision rule, rerun with its weights kept, reproduce its #587 held-out numbers and leave one checked safetensors file in TSAI storage?
Script:          teams/10-post-training/capstone/sft_g5.py (`--team7-ckpt-remote` calls `teams/07-infrastructure/ckpt/ckpt.py` `Checkpointer.save` + `export_safetensors`, verified locally on single-process PyTorch in `capstone/test_team7_ckpt_save.py`). `capstone/sft_job_v1.py` still deletes weights by default until a keep-weights flag is wired.
Command:         python teams/10-post-training/capstone/sft_g5.py --adapter-config <CFG> --train <ARM_ROWS> --eval <DEV_ROWS> --method full --team7-ckpt-remote <REMOTE_ROOT> --team7-run-id <RUN_ID> --out out/ (exact arm TBD after #587)
Config:          the #587 settings (block size 2,048, seed 1, AdamW, full method, the same pins). Arm: A2 or A4, whichever #587's decision rule picks (see #587 "Decision rule").
Inputs:          the same as #587: the firewalled OCR-2 pack shards 0-3 (TSAI-stored, #565), the RL pool files (#564), and the dry run 1 run folder (#475). Nothing new.
Hardware:        1 GPU
Max time:        90 minutes for the training and reports (as #587), plus the export time, which is not yet estimated
Precision:       weights fp32, AdamW state fp32 (as #587)
Measures:        the #587 measures (held-out bpb, format validity, execution pass, forgetting) to reproduce, the sha256 of the kept safetensors file, and a reload check that gives the same held-out bpb as the saved weights
Expected result: the #587 numbers within the reload check's tolerance. Storage estimate: about 0.95 GB of fp32 weights (237,052,416 parameters from the #587 config x 4 bytes). Estimate only.
Outputs:         out/*.json reports (under 2 MB) to the repo. One safetensors file to TSAI storage, named with its sha256. No weights in the repo.
Test log:        REQUIRED before sending. Not yet attached. Run the save and reload path on our own machine with a small stand-in model and attach the log.
```

## Blocked by

1. **#587 results.** The arm is picked by #587's decision rule. Until TSAI returns #587, the arm is unknown.
2. **Code PR for the save step (partially done).** `capstone/sft_g5.py` now supports `--team7-ckpt-remote` (calling Team 7 `Checkpointer.save` + `export_safetensors` on single-process non-DeepSpeed PyTorch; verified in `capstone/test_team7_ckpt_save.py` with exact `float_bits` probe parity and `logits_max_abs_diff == 0.0`). Still open: wire a pass-through flag into `sft_job_v1.py` if run via the two-arm wrapper, and confirm Team 7 remote store credentials/URL.
3. **Route decision (lead).** Two options:
   - (a) Team 7's `Checkpointer` and `export_safetensors`, as the instructor's `#587` note asks for later SFT jobs that keep weights.
   - (b) TSAI stores the exported safetensors file with its sha256, on the same route as the OCR-2 pack (#565) and the RL pool (#564).
4. **Team 9 confirmation of format.** Team 9's watcher reads `--run-dir`. Team 9's `run_eval_mini.py` takes a model directory (the bench passes one). Confirm which one Team 9 will use, and the file layout.
5. **Test log** (rule 2 of `JOB_REQUEST.md`).
6. **Lead approval** on this PR.

## Notes

- One job answers one question. The eval-mini scoring is a separate request, so the two can be sent apart.
- No benchmark item text goes into any file in this request.
