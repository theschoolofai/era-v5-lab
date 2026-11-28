# Team 9 mini-benchmark v1

`minibench_v1` is a fixed checkpoint suite for Teams 9, 10 and 12 (Lab 5 design 1). The full profile is the candidate for a dedicated evaluation GPU. Quick uses a subset of the task items and fixed prefixes of the full held-out documents, for CPU runs, rollout checks and quantization comparisons. Compare two models only on the same suite, profile and input hashes. The existing Tier A freeze guard still runs under its approved schedule.

**Draft for TSAI review.** Three tasks need TSAI's approval before anyone runs them on lab checkpoints (see [Clearance](#clearance-and-labels)). Until the suite is calibrated on real checkpoints, decisions stay with the Tier A guard.

## What runs

| Task | Full items | Quick items | Accuracy SE at chance, full / quick (points) | Gold bpb SE, full / quick | Use on lab checkpoints |
|---|---:|---:|---:|---:|---|
| ARC-Easy | 100 | 32 | 4.3 / 7.7 | 0.0671 / 0.1387 | Diagnostic, awaiting TSAI approval |
| ARC-Challenge | 100 | 32 | 4.3 / 7.7 | 0.1160 / 0.2777 | Diagnostic (TSAI, 12 Nov) |
| HellaSwag | 100 | 32 | 4.3 / 7.7 | 0.0281 / 0.0528 | Diagnostic, internal only (TSAI, 28 Nov) |
| MMLU, cloze, 57 subjects | 171 | 57 | 3.3 / 5.7 | 0.0709 / 0.1165 | Cleared by F2 v2 |
| MILU Hindi | 50 | 20 | 6.1 / 9.7 | 0.1076 / 0.2104 | Cleared by F2 v2 |
| MILU Telugu | 50 | 20 | 6.1 / 9.7 | 0.2060 / 0.2092 | Cleared by F2 v2 |
| MILU Tamil | 50 | 20 | 6.1 / 9.7 | 0.1421 / 0.2079 | Cleared by F2 v2 |
| MILU Bengali | 50 | 20 | 6.1 / 9.7 | 0.1001 / 0.1352 | Cleared by F2 v2 |
| HumanEval, reference code | 50 | 16 | — | 0.1278 / 0.1194 | Diagnostic, awaiting TSAI approval |
| MBPP, reference code | 50 | 16 | — | 0.1179 / 0.1881 | Diagnostic, awaiting TSAI approval |
| Two-digit addition | 50 | 20 | 6.1 / 9.7 | 0.0802 / 0.1099 | Generated locally |
| Two-digit subtraction | 50 | 20 | 6.1 / 9.7 | 0.0687 / 0.1321 | Generated locally |
| Three-digit addition | 50 | 20 | 6.1 / 9.7 | 0.0450 / 0.0638 | Generated locally |
| Two-by-one multiplication | 50 | 20 | 6.1 / 9.7 | 0.0582 / 0.0787 | Generated locally |
| Devanagari two-digit addition | 50 | 20 | 6.1 / 9.7 | 0.0836 / 0.1247 | Generated locally |
| **Total task items** | **1,021** | **365** | | | |

Held-out bpb uses another 1,059 documents for full and 60 source-document prefixes for quick. Quick takes four distinct documents per slice in a fixed hash order and caps each prefix at 1,024 UTF-8 bytes. The selected prefixes contain 56,310 raw bytes. The slice-level noise reference is below.

All choice tasks rank option text by log likelihood divided by continuation bytes. Accuracy SE is `100 × sqrt(0.25 × 0.75 / n)` under independent items at four-option chance. Gold bpb SE is the ratio-estimator standard error from item loss and byte counts in the full and quick replays. These estimates describe item sampling at initialization. The paired comparison computes 95% intervals for score changes on matched items. HumanEval and MBPP score the reference code as a continuation. Code generation and execution stay in the later code suite.

The held-out path uses Team 5's `DocumentWindows` and `evaluate()`. Each document starts with BOS. Later windows start with the preceding token, and only document text counts toward the UTF-8 denominator. Sum negative log likelihood in nats, divide by `ln(2)`, then divide by raw UTF-8 bytes. Compute slice ratios before reporting the equal-language Indic mean. Team 5's reference has Assamese, Bengali, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil and Telugu. Sanskrit waits for a pinned Data B slice. Assamese and Punjabi are transfer probes for the current pack list. [Team 5 reference](../../05-architecture/heldout_v1/README.md)

| Input | SHA-256 |
|---|---|
| Team 5 full held-out JSONL | `21c6e4b2df8dae9d69e254f4a00fc934d2a3c70f0675065a03724299d94312bb` |
| Team 5 full held-out source index | `95585a25bdccb077130432d49b6427c5ff5f756d5b43b9c7033803326f65e0d6` |
| Quick held-out prefixes | `08f366c146057fa563bedb18a2ff411d54715d6ee459367ea0675cfb35bc0046` |
| Quick held-out source index | `5ef3be35c8857e3882d2161ac9eaf39429730d316d9d78e59c8c7e1fd5c55dbe` |
| Rendered full task items | `01fe24d16955131b71f7511e6daba040a2087be677fe52663e8deb0c5766556e` |
| Rendered quick task items | `ec2a00275f444e5064cf640c633a3b30415c3069644dedaa06080bdaa37520a0` |

The task pins, selection counts and arithmetic seed are in [`minibench_v1.yaml`](../harness_lab/minibench_v1.yaml).

## Clearance and labels

- **Cleared:** MMLU and the four MILU languages are covered by fingerprints v2 and form the freeze set. The F2 set also protects `heldout_g5_v1`. Arithmetic items are generated locally from a fixed seed.
- **Approved diagnostics:** TSAI's decision on #357 (12 Nov, [`benchmarks_v1.md`](../benchmarks_v1.md) Decision 7) lets ARC-Challenge and HellaSwag run on lab checkpoints as diagnostics. Every such number is labelled "diagnostic, not cleared for contamination". It never picks or blocks a candidate, and it is never shown as a model score outside the lab.
- **Awaiting approval:** ARC-Easy, HumanEval and MBPP are cleared in Decision 7 only as harness checks on public models. **We ask TSAI to approve them as diagnostics on lab checkpoints under the same conditions.** Fingerprints v3 (#909, open) would add HumanEval and MBPP, and covers ARC-Easy only in part, because short questions have no usable n-gram. If TSAI says no, they leave the suite and the item hashes change before anyone depends on them.
- **HellaSwag:** TSAI on #909 (28 Nov): `skip` for fingerprints after the wikiHow takedown, no item text published anywhere, internal scoring allowed, and TSAI decides what appears in public tables. The suite keeps it as an internal diagnostic.

The labels travel with every copy of a score. The `eval_mini_v1` records carry them in `notes`. The continuous sidecar lists `diagnostic_tasks`, `awaiting_approval_tasks` and `internal_only_tasks`. Team 12's loop writes diagnostic scores under a separate `minibench/diagnostic/` metric prefix. Decisions that pick or block a format, a rollout policy or a checkpoint use only held-out bpb, MMLU, MILU and arithmetic. Results carry task names, item IDs and scores only. Rendered benchmark text, answers and code stay in memory. [Firewall](../firewall/eval_firewall.md)

## Cost per checkpoint and early signal

These are seeded replays of the dry run 2 model shape (untrained weights, seed 1234), so they time scoring without checkpoint loading. Each GPU and quick CPU row is the median of three runs on an otherwise idle laptop, with the range in brackets. An earlier set of runs on the same laptop took 1.5 to 2 times as long, most likely because other work was running. Laptop timings are a guide, and the eval worker needs its own.

| Run | Hardware and software | Total | Held-out | Tasks |
|---|---|---:|---:|---:|
| Full | RTX 3070 Laptop GPU, bf16, Torch 2.11.0+cu126 | 61.4 s (60.4–61.4) | 53.7 s | 5.9 s |
| Quick | RTX 3070 Laptop GPU, bf16, Torch 2.11.0+cu126 | 6.7 s (6.6–6.7) | 2.3 s | 2.4 s |
| Full | Ryzen 9 5900HX, 8 threads, fp32, Torch 2.14.1 CPU | 2,586.3 s (one run) | 2,180.4 s | 404.0 s |
| Quick | Ryzen 9 5900HX, 8 threads, fp32, Torch 2.14.1 CPU | 129.2 s (129.2–139.3) | 24.7 s | 103.5 s |
| Existing Tier A reference | Eval slot, 1 GPU, bf16 | 168.8 s | | 970 items, plus checkpoint loading |
| Existing Tier A reference | Laptop CPU, fp32 | 658.8 s | | 970 items on the T1 shape, including export |

Full has 549,042 held-out tokens and quick has 7,703. Peak allocated GPU memory was 1.98 GiB for both profiles. Setup (inputs, hashes, rendering the items) took under 1 s once the files were in the OS cache. The full GPU replay gives 2.1607 bpb on the canonical held-out set, the trainer's step-0 value to four decimal places. Repeats gave identical scores. The CPU and GPU replays used identical inputs and seed. They disagreed on two of 333 choice outcomes on quick and seven of 921 on full, with device, precision and Torch version all different. Held-out bpb agreed to four decimal places on full.

Quick fits inside one dry run 2 commit interval (660–697 s) on a laptop CPU. Full takes about 43 minutes on the same CPU, close to four commit intervals, so full is for a GPU. The production entry point needs Torch 2.14.1 and an end-to-end timing on the eval worker, with checkpoint load, scoring and result writing timed separately. [Evaluation timing](../eval_schedule.md#3-interval-time-per-checkpoint-and-the-gpu-slot) · [Dry run 2 commits](../../05-architecture/results/dryrun2-1234/commits.jsonl)

| Held-out metric | Step 0 → 1,221 | Spearman with step | Late checkpoint variation (bpb) |
|---|---:|---:|---:|
| English | 3.1880 → 1.7687 | −1.000 | 0.0035 |
| Code | 4.1426 → 3.4073 | −0.870 | 0.0559 |
| Math | 4.1350 → 2.4825 | −0.997 | 0.0150 |
| Science | 3.0340 → 1.6108 | −1.000 | 0.0045 |
| Assamese | 1.8544 → 2.2327 | −0.141 | 0.1607 |
| Bengali | 1.7753 → 2.1579 | −0.132 | 0.1578 |
| Gujarati | 1.7269 → 2.0647 | −0.207 | 0.1715 |
| Hindi | 1.3230 → 1.8982 | −0.103 | 0.1284 |
| Kannada | 1.6985 → 1.8780 | −0.252 | 0.1531 |
| Malayalam | 1.4898 → 1.7142 | −0.187 | 0.1303 |
| Marathi | 1.3736 → 1.8624 | −0.214 | 0.1191 |
| Odia | 1.5378 → 1.7946 | −0.218 | 0.1633 |
| Punjabi | 1.9737 → 2.2553 | −0.056 | 0.1668 |
| Tamil | 1.4283 → 1.7834 | −0.136 | 0.1247 |
| Telugu | 1.6855 → 1.8892 | −0.368 | 0.1419 |
| Equal-language Indic mean | 1.6243 → 1.9573 | −0.194 | 0.1438 |
| Equal-weight English, code and Indic groups | 2.9849 → 2.3778 | −0.880 | 0.0521 |
| All bytes pooled | 2.1607 → 2.0561 | −0.539 | 0.1060 |

The table uses all 26 trainer validation records of dry run 2 on the full held-out set. Late variation is the sample standard deviation of successive bpb differences across the 14 records from step 600 onward, divided by `sqrt(2)`. It measures how scores changed between nearby checkpoints in this run. Dry run 2 trained on about 20M tokens (1,221 steps × 8 sequences × 2,048 tokens) from one English web shard. So this table is below the 100M–1B range, and the Indic slices had no Indic training text. The English signal was strong. Code, math and science also moved. [Trainer metrics](../../05-architecture/results/dryrun2-1234/metrics.jsonl) · [Run record](../../05-architecture/results/dryrun2-1234/README.md)

At 100M–1B training tokens, use fixed-slice bpb as the first signal, especially for slices represented in the mixture. Treat choice accuracy, arithmetic and code bpb as exploratory until they are measured on the early checkpoint ladder. Recheck each metric at about 100M, 250M, 500M and 1B tokens with at least two seeds and unchanged inputs. A metric counts as signal when it moves in the expected direction with a Spearman magnitude of at least 0.5, its total change is at least twice the seed standard deviation, and, for choice accuracy, it clears chance by three sampling standard errors. A pinned 100M–1B ladder and per-document bpb uncertainty are still to come.

## Design checks

1. **Arithmetic shortcuts.** Options are equally spaced, have the same number of digits and stay inside the operation's valid answer range. The gold answer's display position and numerical rank are balanced in blocks of four. Multiplication options are all multiples of the shown multiplier. Picking the smallest option gives 63/250 (25.2%) on full and 25/100 (25.0%) on quick. A distance rule that scored 42.7% on an earlier layout gives 25.4% on full, with uniform tie-breaking and a uniform fallback when the rule selects no option.
2. **Code token boundaries.** Joint encoding of prompt and reference code changed the prompt's own token prefix on 50/50 full HumanEval items and 19/50 full MBPP items. Both scorers therefore score explicit token pairs from a separately encoded prompt and reference code, with the prompt's trailing whitespace kept in context. The shared scorer checks each part against the tokenizer's byte table, divides by the original continuation bytes and rejects truncation. All 100 full reference-code pairs fit the 2,048-token window. [Native scorer](../harness_lab/lm_eval_lab.py) · [GGUF scorer](../harness_lab/minibench_gguf.py)
3. **Quick coverage.** All 15 held-out slices have four source documents in quick. Quick suits smoke checks and paired comparisons. One answer still moves a single quick MILU score by 5 points, so language-level decisions need full, or paired document-level intervals.
4. **Tokenizer normalization.** The sidecar's `encode_fallbacks` (144 full, 60 quick) counts texts whose tokenizer IDs do not rebuild the raw UTF-8. All of them are MILU texts, 143 Bengali and one Hindi on full. p1536's normalizer applies NFC and then recomposes Bengali and Gurmukhi nukta letters (for example য + ় becomes য়), as well as the Malayalam chillu forms. The scorer uses the tokenizer's IDs, the same IDs as the watcher, and divides by the raw bytes.
5. **Native and GGUF parity.** The seeded model was saved with its KAS V2 output bias (`head.unigram`) set to zero, because no GGUF export can carry that bias. Team 12's `export_hf.py` exported it as Granite MoE Shared, and test A1 passed: largest logit difference 2.8e-6, same top-1 on 4,096 of 4,096 positions. llama.cpp b11669's converter then wrote a bf16 GGUF. On quick (CPU), the native fp32 score and `minibench_gguf.py` with `llama-cpp-python` 0.3.36 agree: pooled held-out bpb 2.33429 against 2.33436 (+0.00007), largest slice difference 0.00097, two of 333 choice outcomes different (both arithmetic near-ties), and every task's gold bpb within 0.0033. The GGUF run took 135 s on the same CPU. Dropping the bias itself is a large change: the same seeded model scores 2.0210 bpb with it and 2.3343 without, so at initialization it is worth 0.31 bpb. This is why Team 12's loop reports the native-to-bf16 export gap separately from the quantization gaps. These checks use an untrained model. The real check is the same comparison on step 1,221.

## Running and reading the suite

Stage the pinned test Parquet files in a separate eval cache with Hugging Face's `datasets--<owner>--<repo>/snapshots/<revision>/` layout. Existing Team 9 caches cover MMLU, the four MILU test splits, ARC-Challenge and HellaSwag. Add the ARC-Easy test, HumanEval test and MBPP `full` test files at their pins. The scorer reads local Parquet files only and stops on a missing input. The cache and any benchmark material stay inside the evaluation firewall.

```bash
python teams/09-evaluation/harness_lab/run_lab_ckpt.py \
  --run-dir <store>/dryrun2-1234 --step 1221 --device cuda \
  --scorer minibench_lab:team5 --out out/mini.json \
  --model-config teams/05-architecture/results/dryrun2-1234/manifest.json \
  --tokenizer <p1536>/tokenizer.json \
  --tokenizer-sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b \
  --byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz \
  --profile full --cache <eval-hub-cache>
```

For timing with the published manifest and a seeded untrained model, use `minibench_lab.py --init-only` with `--device`, `--out` and the scorer options above. `--cache` can be repeated for separately staged snapshots. The scorer records hardware, Python, Torch and CUDA versions, time by phase, CPU threads and peak GPU memory. The JSON includes checkpoint identity when it scores a real commit.

For a weights-only delivery, use `minibench_lab.py --weights-safetensors <model.safetensors> --weights-sha256 <file SHA-256> --step 1221` with the same scorer arguments. Team 12's loop uses that path and the same inputs for each quantized format. `minibench_gguf.py --gguf <file> --format <bf16|Q8_0|...>` scores one GGUF with the same token IDs, in a Python environment that also has `llama-cpp-python` 0.3.36. Run Team 12's export and the llama.cpp converter in an environment built from llama.cpp's converter requirements (transformers 4.57.6). With transformers 5.x, `export_hf.py`'s check stops on the renamed expert tensors.

- `mini.json` is `eval_mini_v1`, with primary accuracy in points. Ingest it through Team 8's existing schema.
- `mini.continuous.json` carries bpb, byte and token counts, timing, labels and per-item numeric evidence. Its `result_sha256` binds it to `mini.json`. Team 8 can map continuous metrics to its metrics store once the metric names and run identity are agreed.
- `python teams/09-evaluation/harness_lab/minibench_compare.py baseline.continuous.json candidate.continuous.json` compares matched inputs and reports paired intervals for task items. Its deltas are candidate minus baseline. Held-out bpb deltas are aggregate values without an interval.

## Team 12 and dashboard handoff

```bash
python teams/12-quantization/scripts/run_loop.py \
  --weights <model.safetensors> --step 1221 \
  --manifest teams/05-architecture/results/dryrun2-1234/manifest.json \
  --tokenizer <p1536>/tokenizer.json \
  --tokenizer-sha256 e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b \
  --minibench-profile quick --minibench-cache <eval-hub-cache> \
  --minibench-byte-table teams/04-ke2/results/tables/p1536-s0/raw_table_P32.npz \
  --mini-python <eval-python-with-torch-and-llama-cpp-python> --out out/dryrun2-mini \
  --formats bf16,Q8_0,Q6_K,Q4_K_M --drop-router-bias --drop-head-bias
```

The loop scores the standalone native weights and each GGUF format, writes stage markers, and reports the native-to-bf16 export difference beside the quantization deltas against the same-export bf16 GGUF. This command uses the Granite MoE Shared export, where the two bias flags mark the KAS V2 export as relaxed. For the ERNIE export of #907, which keeps the router bias, replace the two flags with `--drop-head-bias --qe-args --target ernie4_5_moe`. Use `--run-dir <store>/<run>` in place of `--weights` for committed checkpoints. Keep output directories distinct across checkpoints scored at the same time. Each format writes one `mini/<format>/metrics.jsonl` row for the step: `minibench/<held-out key>`, `minibench/gold_bpb/<task>` and `minibench/accuracy_points/<task>`, with diagnostic tasks under `minibench/diagnostic/`. Team 8 still needs to agree on the production run identifiers and ingest those rows. [Merged Team 12 loop](https://github.com/theschoolofai/era-v5-lab/pull/886)

## Evidence

The [`minibench_v1/`](minibench_v1/) folder holds the replay sidecars (per-item IDs and numbers only, no item text), their console logs and `timings.json` with every repeat. `parity-native-quick-cpu.json` and `parity-gguf-bf16-quick-cpu.json` are the native and GGUF scores of design check 5. Each log starts with the command.
