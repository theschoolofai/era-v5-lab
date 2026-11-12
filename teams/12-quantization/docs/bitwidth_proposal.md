# Bit-width proposal (G12)

**Keep bf16, Q8_0, Q6_K, Q5_K_M and Q4_K_M. Do not keep Q3_K_M or Q2_K.** Ship bf16 as the reference and Q4_K_M as the quantized file. The numbers below are the most negative drop, in points versus bf16 on the same items, that a kept format may have on each task.

This follows [`bitwidth_vs_drop.md`](bitwidth_vs_drop.md). The full ladder is OLMoE-1B-7B @ `6d84c48581ec`. Later runs check Q4_K_M only, on other models. Every quantized file still keeps `output.weight` at Q8_0 and the router (`ffn_gate_inp`) at F32.

## Formats

| Decision | Formats | Why |
|---|---|---|
| Ship | bf16, Q4_K_M | bf16 is the reference. Q4_K_M is the smallest format inside every limit on OLMoE: 4.90 bits per weight, 4.24 GB, 3.3× smaller than the 13.84 GB bf16 file. |
| Keep, ship only if Q4_K_M misses a limit | Q8_0, then Q6_K, then Q5_K_M | All three pass every limit on OLMoE. Q8_0 is the fallback (7.36 GB). Q5_K_M then Q6_K are the steps between Q4 and Q8 when a model fails Q4 on one task. |
| Do not keep | Q3_K_M, Q2_K | Q3_K_M misses MMLU (−4.2, p 0.004) and HumanEval+ (−3.7, p 0.031). Q2_K misses ARC-C, HellaSwag, MMLU and GSM8K. |

A new model is not given Q4_K_M until it has been scored against its own bf16 and passes the limits. Sarvam-30B does not: its Q4_K_M GSM8K drop is −9.5.

## Drop limit per task

The limit is on the paired point estimate (format minus bf16). A drop equal to the limit passes. A more negative drop fails. A gain does not fail. A task also fails if McNemar p < 0.01, which is the bar already used for a bold cell in [`eval_mini/results/RESULTS.md`](../eval_mini/results/RESULTS.md). TruthfulQA-mc2 has no McNemar test; only its point limit applies.

| Task | Items | Drop limit | OLMoE Q4_K_M | OLMoE Q3_K_M | What sets the number |
|---|---|---|---|---|---|
| ARC-C | 500 | −2 | +0.2 | −0.2 | Q4 and Q3 are inside the noise. Q2_K is −7.6. |
| HellaSwag | 400 | −2 | −0.2 | −1.2 | Same pattern. Q2_K is −4.5. |
| MMLU | 570 | −3 | −1.9 | **−4.2** | The cut between Q4 and Q3. Q4's interval still includes zero (p 0.13). |
| GSM8K | 200 | −4 | +1.0 | −1.5 | Q2_K is −5.5 (p 0.052). The widest Q4 drop on a later model whose test does not call it a loss is Llama-3.2-1B at −4.0 (p 0.23). |
| TruthfulQA-mc2 | 200 | −2 | −0.5 | −0.6 | No format on the ladder misses this. The largest move is Q2_K at +1.5. |
| HumanEval+ | 164 | −3 | −1.8 | **−3.7** | Q3 is the first significant code loss (p 0.031). |
| MBPP+ | 378 | −3 | −0.5 | −1.6 | Same bar as HumanEval+, so a code task is not held more loosely. Q3 fails on HumanEval+, not here. |

Indic tasks (Belebele, MILU) have no limit. On OLMoE they sit near the 25% chance line, and the 4096-token context truncates most of those prompts. They are not used to keep or reject a format.

The 100-item GSM8K inside the code + Indic run is not a second gate. Its standard error is about twice the 200-item task. The GSM8K row above is the 200-item eval_mini task.

Perplexity ratio and KL are not gates. On OLMoE they already rank the same way: Q4_K_M is 1.023× bf16 and KL 0.023; Q3_K_M is 1.065 and 0.058. A format that passes the task limits is kept even though KL rises at every step.

## Q4_K_M against the limits

| Model | Worst drop | Inside the limits |
|---|---|---|
| OLMoE-1B-7B | MMLU −1.9 | yes |
| Llama-3.2-1B-Instruct | GSM8K −4.0 | yes (equal to the GSM8K limit; p 0.23) |
| Phi-3-mini-4k-instruct | GSM8K −3.0 | yes |
| Qwen3-4B | MMLU −2.5 | yes on the point limit. The 95% interval is −4.7 to −0.2 (p 0.049), so record the cell. p is not under 0.01, so it is not a reject. |
| Qwen3-4B-Thinking-2507 | GSM8K −2.0 | yes |
| Sarvam-30B | GSM8K **−9.5** | no (p 0.037; interval −17.9 to −1.1). Do not ship Q4_K_M for this model. The next format to measure is Q5_K_M, not Q3_K_M. |

Sources: [`eval_mini/results/RESULTS.md`](../eval_mini/results/RESULTS.md), [`eval_code_indic/results/RESULTS.md`](../eval_code_indic/results/RESULTS.md), and the paired tables under `eval_mini/results/` for Llama-3.2-1B, Phi-3-mini, Qwen3-4B, Qwen3-4B-Thinking-2507 and Sarvam-30B.
