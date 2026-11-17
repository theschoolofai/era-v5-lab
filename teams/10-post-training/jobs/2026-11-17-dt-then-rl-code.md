# Job request draft — Deletion Tuning SFT followed by code RL

**Status:** Pending private inputs, local verification of the staged configuration, and lead approval. The request has not been sent. The three-step canary checks integration and RL signal. The full run measures held-out reward change.

```text
Team:            10-post-training
Owner:           Hema Varshini Palpandian (Hemaaaa04)
Lead approval:   pending saitej123
Question:        After Deletion Tuning SFT, can the delivered Team 5 model take code-verifier RL updates while its deleted weights stay zero?
Script:          teams/10-post-training/rl-loop/train.py
Command:         G10_STDIO_RUNNER=docker python teams/10-post-training/rl-loop/train.py --config teams/10-post-training/rl-loop/config/task11_code_canary.yaml
Config:          teams/10-post-training/rl-loop/config/task11_code_canary.yaml (stage inputs and fill checkpoint SHA-256 first)
Inputs:          Team 5 delivered run folder and adapter dependencies, DT+marker-row SFT model.safetensors with dt_keep_masks.bin and dt_keep_masks.bin.json, screened RL data v1 Code Contests cc.jsonl and disjoint canary ID lists
Hardware:        1 GPU, requested >=40 GB, Python verifier image preloaded
Max time:        Proposed 30 minutes for the canary, subject to lead review
Precision:       bf16 compute, fp32 master weights
Measures:        Mixed groups, verifier failure reasons, optimizer updates and stored-update share, deleted nonzero count, held-out reward at step 0 and at the last completed step
Expected result: Mixed groups and code reward are unknown. The mask check should see a positive deletion count and zero regrowth.
Outputs:         under out/task11-code-canary/. Return aggregate status, counts, rewards and timing. Per-problem records, IDs, paths and generations stay private.
Test log:        CPU trainer and mask handoff checks in ../results/dt_then_rl_evidence/validation.md. Staged code-canary test log pending.
```

## Staging and acceptance

- Produce the DT SFT checkpoint with [the Team 5 SFT driver](../capstone/sft_g5.py), using the approved SFT rows and the delivered checkpoint. Stage the baked state, its matching mask files, and the verified adapter config together. Record their input hashes. The adapter selection must include the masked parameters and keep the router frozen.
- Stage 16 training prompts from the easiest admitted RL data v1 Code Contests rung and an 8-prompt held-out subset fixed before sampling. Check that the lists are disjoint and that the rendered prompt plus completion allowance fits the delivered model. This path uses the same [Python stdio verifier](../rl-data/stdio_check.py) as Task 6 with the Team 5 sampler.
- The canary screens 16 train prompts with 8 samples each. Fewer than four mixed groups yields `NO_GO_MIXED_BAND`. With enough signal, check that at least one optimizer update changes stored weights, that the initial deletion count is positive, that the maximum deleted-nonzero count is zero, and that the router checksum stays fixed. Return the failure breakdown if the canary stops.
- After a successful canary and lead approval, set the training budget and time cap for the full run. Freeze the held-out split and sampling settings before that run. Record step-0 and final rewards on the DT SFT checkpoint, their paired prompt-level difference and interval, optimizer updates, and deletion integrity. Task 6's Qwen 7B result used a different model and sampler. Use its protocol as a reference and interpret Task 11's gain against its own step 0.
