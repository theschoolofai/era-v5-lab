# Job request: Deletion Tuning SFT, then code RL, on the capstone checkpoint (draft, not sent)

```
Team:            10-post-training
Owner:           f20201351h-maker
Lead approval:   saitej123
Question:        On real code prompts, after SFT with Deletion Tuning (plus marker rows) does the objective_v1 verifier reward still rise as much as after LoRA (plus marker rows) SFT, and do the deleted weights stay exactly zero through RL?
Script:          teams/10-post-training/capstone/sft_g5.py (SFT arms), teams/10-post-training/rl-loop/train.py (RL; config keys model.init_state, train.keep_zero), teams/10-post-training/capstone/dt_then_rl.py (analysis)
Command:         not final. Per arm: sft_g5.py --method dt --dt-unseen keep --marker-rows --wd 0 ... then train.py --config <stdio-task config with model.init_state and, for the DT arm, train.keep_zero.path>; arms and seeds as in results/dt_then_rl.md
Config:          RL data v1 easiest rung only (codechef/hackerearth, statements <= 310 tokens) with the verifier of rl/verifier.py; the screen of mixed groups on the SFT'd model decides whether an arm has signal
Inputs:          the delivered G5 checkpoint (see 2026-11-17-g10-checkpoint-export-ask.md); SFT rows from SFT data v1 once its gates close; RL data v1 pool (decontaminated)
Hardware:        1 GPU with >= 40 GB; bf16 autocast, FP32 master weights (train.autocast: bf16)
Max time:        to be set after a 3-step canary on the real checkpoint
Precision:       bf16 autocast, FP32 master weights; the stored-update check must pass on step 1
Measures:        per step: mean reward, kept groups, trust-region masked fraction, share of exactly-zero weights, DT-deleted weights that are nonzero (must be 0), stored-update share; held-out reward first vs last with a paired bootstrap over prompts; failure breakdown (no code block, wrong answer, timeout)
Expected result: unknown. At small width on a toy reward the DT arm rose about 0.76 times as fast as LoRA (results/dt_then_rl.md); on real code the first question is whether DT+markers SFT produces a closed turn with a code block at all, because RL has no signal before that
Outputs:         per-run metrics.jsonl, evals.jsonl, summary.json (each under 5 MB); generations stay private
Test log:        none yet; the CPU runs behind this draft are in results/dt_then_rl.md
```

Not to be sent before: the checkpoint export ask is answered, SFT data v1 gates are closed, and a screen on the SFT'd model finds
mixed-reward groups (CLAUDE.md "G10 GRPO review" check on the real trainer first). Whether DT is used at all is TSAI's decision.
