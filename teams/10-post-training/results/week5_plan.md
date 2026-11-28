# Team 10 Lab 5 (Week 5) Execution Plan & Evidence Tracker

Active branch: `g10-week5-post-training` (cut cleanly from `upstream/main` `317b31f3`).  
Deadlines: **70% due Mon 30 Nov (Day 3)** · **100% due Wed 2 Dec, 7:00 AM IST** · **Next class: Sat 5 Dec**.  
Evidence list owner: `saitej123`. Public text names teams only.

## Lab Rules for All Teams (TSAI 28 Nov) & Done-Gate

1. **Licence:** **NC, ND and unstated licences are allowed** for all data, post-training data included. Record the licence and where found; if a model made the data, also write the model and its licence terms.
2. **Text cleaning:** Unicode NFC only. Never NFKC. Never remove `ZWJ` (`U+200D`) or `ZWNJ` (`U+200C`).
3. **No red tests on `main`:** failing-test-first PRs mark tests `xfail(strict=True)` with the issue number, or land together with the fix.
4. **PR bodies:** carry your name, GitHub handle, and team; no personal e-mail address.
5. **Plans do not state a production model scale:** write `"at the production scale TSAI sets"`.
6. **Every speed or kernel claim comes with a gradient-coverage check:** after one forward and backward, list every trainable parameter whose gradient is `None` or all zero, explain why each one is allowed, and compare fast-path ON vs OFF.
7. **The model licence and what is released** are TSAI's decision.
8. **Done-Gate:** output exists and is reproducible from the command, passes its named check, and writes down every difference from the reference check (including negative results and scope limits).

## Lab 5 Task Matrix (Status & External Dependencies)

| # | Brief Item | Status (28 Nov) | Deliverable & Check | External Dependency (Who to Contact) |
|---|---|---|---|---|
| **I1** | 2-hour channel ack + evidence owner | **Done** | Team channel ack posted; Rule #1 (NC/ND allowed) resolved by TSAI 28 Nov | **None** |
| **I2** | Close `#781` with the two reader OKs | **Done (`#781` CLOSED)** | All 6 Indic templates (`hi` x 4, `ta` x 2) `eligibility: train` on `main` via `#861` | **None** |
| **I3** | TSAI staging recipe for dry run 2 jobs | **Done (`#882` merged)** | `jobs/2026-11-28-g10-dryrun2-staging-recipe.md` (`#564`, `#565` shards `0:4`, `sha256sum -c`); `#186` adds `unseen_report`, stale-folder skip, and `--dt-unseen keep` (**needs lead yes**) | **TSAI:** stage the 7 files, fix Docker runner on job machine, run `#861`/`#186` jobs |
| **D0** | Written SFT & RL data request to Teams 1 & 2 (by Sun 29 Nov) | **Team 1 `#914` received (`#183` updated); Team 2 pending** | `docs/data_request_teams1_2_v1.md` (`rl-math-omr-aops-v1` built by Team 1; DeepScaleR/RLVR-GSM dropped from request) | **Team 2 (Data B, `@shankarpandala`):** reply with native Indic SFT + remaining 8 Indic RL languages |
| **T1** | Licence row for every new source before staging | **Eval rows (`#179`) + Team 1 RL math rows (`#183`) merged** | `licences/licence_table.md` (`rl-math-omr-aops-v1` `TSAI reserves`, `rl-math-stack-overflow` & `DeepMath-103K` `needs TSAI decision`, `test_specs.py` PASS) | **Team 2 (`@shankarpandala`):** any new Indic sources |
| **T2** | Confirm Team 3 `special_tokens.md` (`#873`) | **Done (`#882` merged + `#873` Option (a))** | `special-tokens/special_tokens_v1.md` synced to `e6b93a93...` | **TSAI / Team 3 (`@rjvim`, `@sohamniyogi`):** merge `#873` |
| **T3** | Indic prompts inventory (sources, size, checker, missing) | **Done (`#882` merged)** | `rl/indic_prompts_v0.md` §0 (`6/6` `train`, `12/12` `reward.py --type indic`) | **Team 2 (Data B, `@shankarpandala`):** human templates + native-reader OKs for `te, kn, bn, mr, gu, ml, or, pa` |
| **T4 + D1** | Base-to-chat plan + SFT plan & small SFT run | **Plan merged (`#882`); small SFT runs committed** | `docs/post_training_plan_v1.md`, `results/small_sft.md`, `results/dt_vs_fft.md`, `results/lab5_dt_muon_recompute.md` | **Team 2:** Indic SFT pointer; **Team 11 (`@pyru`)** cites `#882` |
| **D2 + Optim + Rule #6** | Hybrid Muon + DT SFT & GRPO + recompute + `--dt-unseen` + size threshold + gradient-coverage check | **Done (`#882` + `#178` + `#182` + `#184` + `#186` + `#187`)** | `capstone/hybrid_optim.py`, `dt/run_lab5_dt_study.py`, `dt/paper_size_table.py`, `dt/check_grad_coverage.py`, `results/lab5_dt_study.md`, `results/dt_paper_size_threshold.md`, `results/lab5_dt_muon_recompute.md`, `results/lab5_grad_coverage.md` | **Team 5 (`@shivman`) / TSAI:** fix `optim.py:78` (`#875`); **TSAI:** run `dryrun2-1234` comparison + `#142` 4B/8B ladder; **Team 12 (`@SomaKorada07`):** `results/dt_quantized_base.md` (`#889`) |
| **D3** | GRPO setup + small working run + Team 8 metrics feed | **Done (`#882` + `#184` + `#185`)** | `docs/post_training_plan_v1.md` §3, `rl-loop/metrics_feed.py`, `results/small_rl.md`, `results/dt_then_rl.md`, `results/lab5_grpo_dt_vs_fft.md` | **Team 8 (`@sandeepkunkunuru`):** confirm `metrics_feed.py` fields; **TSAI:** run `jobs/2026-11-17-dt-then-rl-code.md` on `dryrun2-1234` |
| **T5 + D4** | Fast RL rollouts survey + Quantized-rollout GRPO + Periodic Team 9 mini-bench check | **Training loop (`#185`), rollout check (`#188`), & `#894`/`#180` merged** | `rl/fast_rollouts_v1.md`, `rl-loop/quant_rollout.py`, `rl-loop/rollout_check.py`, `results/quant_rollout_mismatch_pytorch.md`, `results/lab5_quant_rollouts.md`, `results/lab5_rollout_check.md` | **Team 12 (`@SreekanthZipsy`, `@SomaKorada07`):** balanced 50-prompt PyTorch-ref runs (`sarvam-1` + `Qwen2.5-Coder-1.5B` w/ `bf16` speed row) + quantized policy copy; **Team 9 (`@rahulni`):** merge `#929` (`minibench_lab.py`) |
| **D5** | Forgetting vs learning separation | **Tooling & plan done** | `sft/tests/forgetting.py`, `capstone/forget_bpb_kept.py`, `capstone/watcher_rows_to_report.py`, `docs/post_training_plan_v1.md` §4 | **Team 9 (`@rahulni`):** Tier B watcher rows on `dryrun2-1234` base + kept arms (`g10-dr2-{full,lora,dt}`, `g10-rl-final`) |
| **D6** | Waste elimination (shared base weights, rollout cache, restartable stages) | **Done & tested** | `capstone/dryrun2_dt_compare.py` (`--no-before`), `rl-loop/rollout_cache.py` (`66.67%` hit rate across 3 GRPO arms), `dt/test_lab5_grpo_and_cache.py` | **None** |
