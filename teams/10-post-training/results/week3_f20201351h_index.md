# Week 3 contribution index: f20201351h-maker

One consolidated draft PR targets `saitej123:g10-week3-post-training`. Original component commits and branches are retained; the earlier PRs remain historical evidence links. This index records scope, not completion of every week-3 acceptance gate.

| Component | Report / entry point | Verified scope | Remaining gates |
|---|---|---|---|
| OCR-2 pack (former #79) | `../sft/results/ocr2_pack_v1.md`, `../sft/results/ocr2_pack_v1_manifest.json` | 70 shards; 418,496 train rows; 8,507 held-out; hashes/reconciliation | 14 source spot checks; full private split-seed/row-ID manifest handoff; other stated admission conditions |
| SFT/format bench (former #81) | `small_sft.md`, `../sft/bench/` | Surrogate training/evaluation harness and measured full-FT/LoRA results | Exploratory data/protocol limits; no capstone improvement claim |
| DT comparison (former #85) | `dt_sft_surrogate.md`, `../dt/` | SmolLM2-135M and 1.7B base/instruct comparisons, marker hybrid and small fresh supplement | Additional seeds, deletion/layer sweeps, capstone test and DT-then-RL remain unrun |
| C3 SFT measurements (former #86) | `../sft/results/sft_v1_token_records.md` | 23 prefixes + 3 full sets; full Proofs 920,881 unique rows / 10,383,997,134 tokens; all 26 records checked | Further full-mix builds; reserved/held-source rulings; decontamination, held-out exclusions and length dropping before packing |
| Actual RL trainer and verifier checks (former #87) | `objective_v1_trainer.md`, `rl_data_v1_closure.md` | Lead objective integrated in batched trainer; loss/gradient/optimizer tests; identical local RL data rebuild and human-reference checks | Actual Team 5 inputs; external data/pool handoff and MATH licence decision |
| Bounded code-RL pilot (former #87) | `wp5_code_rl_pilot.md` | 1.5B screen NO-GO (7 mixed); 7B GO (22 mixed), four real updates | Final held-out evaluation timed out, no final score/CI/checkpoint; no reward-rise claim or WP6 completion |

## Integration verification

After merging all component heads and the current week-3 branch: 611 passed, 31 skipped in 152.20 s, Apple M1 Pro CPU. Required private bench slice/tokenizer and pinned Team 9 tools were supplied. Skips: 25 Team 5 checkpoint/tokenizer inputs, five math-verify cases absent from this base environment, one missing Team 12 template. Earlier dependency-backed math checks are recorded in the component reports; they are not additive unique-test counts.

Runtime code is preserved from the measured component commits. Their reports retain exact commands, hardware, matched timings and output contracts; this consolidation claims no new speedup and launches no paid job. The only post-merge report corrections record TSAI's confirmed 2% holdout and the latest dry-run-1 dense-untied-head ruling. Pack policy/data hashes, counts, and experimental measurements are unchanged. The private holdout ID list is not published by this consolidation.

The lead's canonical `rl/objective_v1.*`, `results/small_rl.md` and `results/dt_vs_fft.md` are preserved. Our additional experimental reports have distinct names. The original five PR heads are ancestors of the consolidated head. No teammate PR was reviewed as part of this housekeeping task.
