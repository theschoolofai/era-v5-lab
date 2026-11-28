# Team 9 Lab 5 benchmark and evaluation gates

Draft for Team 5, Team 10, Team 11 and the F2 owner. Keep the existing checkpoint guard in force while the [mini-benchmark](minibench_v1_card.md) establishes its timing and early signal. Release runs use the model, prompts, shots and scorer recorded in the run manifest. Public reporting requires clearance for the exact benchmark split and protocol. [Current benchmark inventory](../benchmarks_v1.md) · [Firewalled evaluations](../firewall/eval_firewall.md)

## Benchmarks to report

| Area | Planned checks | Contamination and use |
|---|---|---|
| English knowledge and reasoning | MMLU, GPQA Diamond and an internal ARC-Challenge diagnostic | MMLU and GPQA have F2 entries. ARC needs coverage before a release score. |
| Math | GSM8K, MATH and seeded arithmetic | GSM8K has F2 coverage and is currently limited to decontamination for model scores. MATH requires pinned sources, licence review and F2. Reserve seed-generated arithmetic for internal trend checks, and use fresh private seeds for a release holdout. |
| Code | HumanEval, MBPP and a dated LiveCodeBench window | HumanEval and MBPP need F2 coverage. Existing LiveCodeBench F2 coverage applies to its pinned release. Any new live window needs a revised fingerprint set and licence review. A post-cutoff window restricts exposure and still needs screening against SFT/RL data. |
| Long context | Seeded RULER-style retrieval and aggregation, ONERULER Hindi and Tamil, LongBench v2 as a later check | Generate private seeds after the training-data freeze and check final SFT/RL inputs. LongBench v2 has a pinned F2 entry. |
| Tool calling | BFCL single-turn and multi-turn subsets, plus a private synthetic schema set | BFCL needs F2. Generate private evaluation schemas and functions apart from the training pool. Score schema validity, tool and argument exact match, and end-to-end task completion separately. |
| Indic | MILU, IndicGenBench, IN22 and Belebele | MILU and IN22 have F2 entries. IN22 stays decontamination-only until an evaluation use is approved. IndicGenBench and Belebele need F2 for reported slices. Keep per-language counts, metrics and provenance. |
| Safety and refusal | Held-out harmful-request refusal, safe completions, benign look-alike compliance, multilingual variants and tool boundaries | Keep prompt text private and screen SFT/RL candidates against it. Use the chat model after post-training. Report harmful compliance and benign over-refusal independently, per language and category with denominators and intervals. |

Tanmay's F2 refresh needs the exact counted split and revision for every reported static task. Run the benchmark overlap check on normalized text in the tokenization pass, record the F2 set SHA and flagged count, and use canaries as a separate evidence line. Recheck reconstructions from tokenized shards where appropriate. A changed unit list can break token-sequence matching even when the underlying words are identical, so retain the decoded-text check and its normalization pin. [F2 registry](../decontam/benchmarks.toml) · [Known gaps](known_failures.md)

## Long contexts for Architecture

For #891, a local p1536 tokenization of the pinned 1,059-document Team 5 held-out set found 43 documents at or above 2,048 tokens, 15 at or above 4,096, two at or above 8,192 (Telugu and Punjabi), and zero at or above 16,384. Count without added special tokens on the canonical JSONL and use the source index to recover slices. The p1536 hash is recorded in the [tokenizer release](../../03-tokenizer/release/SPECIAL_TOKENS.md). Send Architecture document IDs and units only after the lengths are fixed. Use private seeded RULER-style tasks for balanced 8K-plus evidence and any 4× training-length comparison. Include random near/middle/far probe placement, a short-length control and language and task counts. Keep synthetic samples out of training data. [Team 5 length plan](https://github.com/theschoolofai/era-v5-lab/pull/891)

## Go or hold for the main run

| Check | Proposed threshold or evidence |
|---|---|
| Launch integrity | Model, tokenizer, byte table and held-out hashes match pins. Every expected task and slice is present. Invalid, missing or nonfinite scores block the evaluation pass. |
| Step 0 | Apply the existing Tier A item-count and bias-aware chance check, including the documented Tamil answer imbalance. Use the existing 970-item 22.2-point pooled floor and 3.9-point baseline gap for the agreed matched guard comparison. |
| Early quality | Report pooled bpb and the English, code and Indic group values at matching training token counts, with the same held-out hashes. Compare at least two seeds against the accepted baseline. Use Team 5's three-seed spread rule when all required seeds are present. Hold when coverage is incomplete or a sustained score regression exceeds the matched baseline's measured variation. Agree on numeric bpb tolerances with Team 5 from the matched main-run baseline before using this gate. |
| Watcher integrity and lag | Replay the nine dry run 2 commits, record killed/restarted states, and confirm once-only scored keys including rollback epoch. Require a separate eval device and investigate a Tier A age above the approved 30-minute limit. |

The router and throughput gates are owned by Team 5. The two teams need to sign off on the early quality comparison and any pause threshold before launch. [Existing freeze guard](config_freeze_proposal.md) · [Evaluation schedule](../eval_schedule.md) · [Architecture go/no-go draft](https://github.com/theschoolofai/era-v5-lab/pull/893)

## Rollout checkpoints and prompt sets

Team 10's #882 needs the same fixed quick profile on the reference policy and rollout policy. Record the optimizer step, checkpoint identity, tokenizer, format, suite hashes and hardware. Start with the initial policy, then evaluate every configured `N` steps and on final/exported weights. Choose `N` with Team 10 after measuring a complete quick pass against rollout cadence. Run on the eval worker with deduplication by policy revision, suite profile and format. Use paired comparisons for the score delta and Team 12's same-prefix agreement and KL metrics for policy mismatch. Keep Tier B forgetting checks on base/full/LoRA/DT/RL weights as their own existing run. [Team 10 plan](https://github.com/theschoolofai/era-v5-lab/pull/882) · [Team 12 rollout evidence](../../12-quantization/rollout/results/rollout_mismatch_sarvam-1.md)

For design 10, the held-out instruction, code, math and Indic sets need a private immutable manifest with prompt ID, source revision, licence, language, expected check, content hash and split. Keep authored instruction constraints, executable code tests, exact-answer math and native Indic prompt verification in distinct subsets. Use independent eval-only caches and source families or generators separated from SFT/RL training. Record F2 and canary results for each training delivery, including the fingerprint set SHA. Return aggregate results and item IDs through Team 9. The prompt set owner still needs to confirm the source and test counts with Team 10.
