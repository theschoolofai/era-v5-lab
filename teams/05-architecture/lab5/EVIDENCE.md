# Team 5, Lab 5: evidence list

**Owner of this list:** Stephen Raj Arokiasamy (the brief asks each team to name one person; claimed in 05 Architecture, 28 Nov).
**Due:** Wed 2 Dec 2026, 07:00 IST, with 70% by Mon 30 Nov (three-day rule).
**State as of:** Sat 28 Nov, lab main `493e8da3`. Updated again on Mon 30 Nov and at the deadline.

How to read it: one row per brief item. **Evidence** names the command or the file behind each number. **Kind** says
whether the numbers are *measured* (a run or a count), *computed* (exact arithmetic from configs), *estimated* (a
formula with assumptions) or *not yet* (approach only). An item is done when a reviewer can reproduce it from the
command, it passes its named check, and every difference from the reference is written down (brief, "What counts as done").

Owners: keep your PR description current; this list is built from the PRs and the claims in 05 Architecture.

## Tasks (evidence: a PR with the packed format and the config)

| Item | Owner | PR | State | Evidence | Kind | Open |
|---|---|---|---|---|---|---|
| Packed-row format with document mask, and how the trainer reads it; match Team 6's loader | Deepjyoti Saha | #890 | draft | `lab5/packed_rows/` (format spec, `measure_fill.py`, `measure_attention.py`), `tests/test_packed_rows.py`; fill on all 41 sample-v0 shards | measured | Team 6 to confirm the five fields |
| Fill `data.seq_len` | Revant Gupta | #825 (merged) | input only | `docs/long_context_plan.md`, `harness/context_length_profile.py`: 2,048 to start, 4,096 as the first extension | measured (profile) | `config_v1.yaml` stays empty until TSAI accepts |
| Fill the model size | Shivanshu Thapliyal | none yet | waits | input: `harness/sizing.py` (#821, merged), exact against the model at T1/T2/T3 and dry run 2 | computed | waits on the corpus-v1 token count |
| Sequence-length strategy, and review of pre-training speed-ups (TST first) | Deepjyoti Saha | #891 | draft, approach | `lab5/sequence_length/README.md` | not yet | stage table and review; split with lead addition 11 being agreed |

## Design tasks from TSAI

| Item | Owner | PR | State | Evidence | Kind | Open |
|---|---|---|---|---|---|---|
| 1. Study table (Qwen3/3.5, Kolibri-1, DeepSeek-V3/V4, GLM-4.5, MiniMax M2) | Tanmay Sharma | #906 | draft | `docs/model_study_table.md`, `scripts/model_study_table.py` (counts from each `config.json`) | computed | |
| 2. Two sparse designs (30B at 8-10% active, 100B at 2-3% active) | Tanmay Sharma | #906 | draft | `docs/model_designs_v1.md`, `scripts/model_design_search.py`. A1: 29.71B / 2.53B (8.5%). B3: 98.33B / 3.96B (4.0%) | counts computed; memory estimated | **B3's 4.0% is outside the brief's 2-3%.** B3 does not fit 8 x 80 GB with FP32 weights and gradients (#906 section 1); lead keeps the fit limit in the note |
| 3. Growth path from a small dense model, kill and resume at every stage | Udit Singhania | #897 | draft, approach | `lab5/growth/README.md`; local conversion checks reported in 05 Architecture, real-data runs pending | not yet | also owns the learning-rate reset after growth (from #893) |
| 4. Router balance | Deepjyoti Saha | #892 | draft | `lab5/router_balance/dryrun2_report.md` from `run_report.py` (#829) on #869; #951's checker gives the same result | measured (dry run 2) | the six test arms (GPU) |
| 5. Residual stream | Shivanshu Thapliyal | #946 | draft | `lab5/design_5_6/residual_stream.py`, `residual_stream_result.json`, `test_residual_stream.py`: width 32, 4 layers, 2 seeds, synthetic tokens | measured (tiny, synthetic) | not at 49M-100M, not held-out bpb |
| 5b. When to introduce DroPE | Shivanshu Thapliyal | #946 | not run | `lab5/design_5_6/README.md` (plan) | not yet | |
| 6. Architecture discovery at 49M-100M (four comparisons) | Shivanshu Thapliyal | #946 | not run | `lab5/design_5_6/README.md` (plan) | not yet | |
| 7. Speed profile of one step, test two fusions or overlaps | Vedang Patel | none yet | claimed 28 Nov | baseline trace promised Mon 30 | not yet | |
| 8. bf16 vs fp8 (per-tensor, block) for the expert matmuls | Anusha Umashankar | none yet | claimed 28 Nov | | not yet | |
| Optimizer rule: Muon on every 2D matrix, AdamW on 1D, no weight decay on Muon | Udit Singhania | #913 | approved by lead | `harness/week2/optim.py` grouping | code | merge |
| Optimizer rule: idle experts (exact-zero gradients) | Udit Singhania | #919 (fix), #875 (merged, xfail tests) | draft | `tests/test_week2_muon_idle.py`; `harness/week2/test_muon_zero_grad.py` | code + tests | |
| Optimizer rule: save and restore Muon momentum | Team 7 | #899 (merged), #945 | #945 open | Team 7 `support/tests/test_ckpt.py` T32-T34 | tests | #945 merge |

## Lead additions

| Item | Owner | PR | State | Evidence | Kind | Open |
|---|---|---|---|---|---|---|
| 9. Scaling-law fit (3 sizes x 3 token budgets, one held back) | Shivanshu Thapliyal | #946 | not run | `lab5/design_5_6/README.md` (plan) | not yet | the 9 runs; the gate in #951 needs the fit |
| 10. Training recipe (schedule, batch, reset after growth, spike guards, checkpoint averaging; two tests at 100M) | Deepjyoti Saha | #893 | draft, approach | `lab5/recipe_and_gates/README.md` | not yet | LR reset after growth with Udit (#897) |
| 11. Context plan (which stage at which length; recalibration and/or a longer stage) | Vardhan Walavalkar | none yet | claimed 28 Nov | | not yet | split with #891 proposed by Deepjyoti |
| 12. Go / no-go gates for the main run | Stephen Raj Arokiasamy | #951 | draft | `lab5/go_no_go/check_gates.py`, `gates_v1.yaml`, 31 tests; every gate a proposal. Dry run 2: health PASS, router FAIL, five PENDING | measured (dry run 2) | the fit (9), the token and time budgets (empty until posted), Team 7's main-config restart test, Team 9's step-0 scores and its #931 holds; router and tokens/s numbers from #892/#893 |

## Tasks for every team

| Item | State | Evidence |
|---|---|---|
| Reply in the team channel within 2 hours | done | 05 Architecture, 28 Nov |
| Every number in a PR comes with a command or a file | checked per row above | |
| Name one person who owns the evidence list | done | this file |
| TSAI status: fix the stale comment in `dryrun2.yaml` | done | #871 (merged) |

## Checks run for this list

1. **#906's parameter counts against `harness/sizing.py`** (exact against the real model, #821), with the shapes in
   #906 and no shared expert:

   ```
   python3 -c "import sys; sys.path.insert(0, 'teams/05-architecture/harness'); import sizing as s
   for n, a in [('A1', (3072, 32, 24, 4, 768, 128, 8)), ('B3', (4096, 40, 32, 8, 768, 256, 6))]:
       c = s.count(s.spec(*a[:5], num_experts=a[5], num_shared=0, top_k=a[6]))
       print(n, round(c['total'] / 1e9, 2), round(c['active'] / 1e9, 2), round(c['active'] / c['total'], 3))"
   ```

   | Design | #906 | sizing.py | Difference |
   |---|---|---|---|
   | A1 | 29.71B / 2.53B (8.5%) | 29.73B / 2.55B (8.6%) | 0.02B |
   | B3 | 98.33B / 3.96B (4.0%) | 98.38B / 4.01B (4.1%) | 0.05B |

   The two agree within the small terms (#906 says within 0.02B; norms and the KAS head's unigram and tok_u terms).
   With one shared expert (the Gate 2 setting), the active ratio rises: A1 9.3%, B3 4.4%. In both cases **B3 is outside
   the brief's 2-3% active band.**

2. **The router result on dry run 2, two ways.** `run_report.py` (#892) and `check_gates.py` (#951) on #869's
   `metrics.jsonl` agree: 8 x the even share at step 50, over the 5 x line until step 300, zero-token experts late in
   the run; 2,299 real tokens/s at 41.8% row fill.

## Gaps for the Mon 30 Nov check (70%)

- No PR yet for design tasks 7 and 8 and lead addition 11.
- Design tasks 5b and 6 and lead addition 9 are plans with no run.
- Every GPU item (router arms, recipe tests, growth runs, architecture discovery) has no measured result yet.
- The model size and `data.seq_len` stay empty in `config_v1.yaml`, by the lead's decision, until the corpus-v1 count.
