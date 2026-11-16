# RL data v1 close (work-order task 2): pool flags, verifier evidence, Team 9 handoff

State on 16 Nov 2026, Apple M1 Pro, CPU and Docker 29.9.2. The data files stay local; this branch holds metadata. It
follows `rl_data_v1_closure.md` (15 Nov) and does not repeat it.

## 1. Rebuild reproduces, now from the repo

`rl-data/rebuild_v1/rebuild_v1.py` is the rebuild kit: `pins_v1.json` names every input by file name, size and sha256
(no local paths) and holds the 12 expected outputs; the four step scripts beside it are byte copies of the 11 Nov
scripts (the driver refuses a changed copy); the driver stages their inputs for one run, runs pins → build → decontam
(Team 9 tools `b470b4c0`, fingerprints v2 `2826a3b8…`, both sets) → MATH-500 guard → assemble, writes the four Team 9
pool files and compares all 12 outputs. Run from this branch:

```
python rl-data/rebuild_v1/rebuild_v1.py --cc-dir <code_contests@802411c3>/data --math-dir <hendrycks_math@21a56338> \
    --math500 <MATH-500 test.jsonl> --g9-tools <Team 9 decontam @ b470b4c0> --out <run dir>
{"outputs_checked": 12, "mismatches": {}, "ok": true, "code_pool": 3577, "math_reserved": 7209, "seconds": {"pins": 5.7, "build": 15.6, "decontam": 63.9, "assemble": 65.7, "total": 66.7}}
```

The 12 outputs: `cc.jsonl` `91ee9951…` (3,723), `math.jsonl` `630c6dae…` (7,234), both task files, both decontam inputs,
both clean files (`84b0a645…`, `ca1073f2…`), and the pool files below; the first 8 equal the 11 Nov record. Both decontam
records equal the 11 Nov records except `run_at`. code_contests: 5,092 in, 1,369 flagged (livecodebench 1,222,
codeforces 207, hle 3, milu 1, heldout_g5_v1 1), 0 canary. MATH: 7,498 in, 175 flagged (mmlu 92, aime_2024 67,
aime_2025 61, hle 4, livecodebench 2), 0 canary, plus 91 removed by the MATH-500 13-word guard (2 of them also flagged).
Tests without data: `rl-data/test_rebuild_v1.py` (pins agree with the v1 manifests, step-script guard, staging passes
the real pin check and a changed file fails it, output comparison).

## 2. Pool flags (`rl-data/rl_v1_close.py` → `rl-data/manifests/rl_data_v1_close.json`)

Each flag is a manifest field that a ruling can reverse with one switch. The v1 files are unchanged. Ids are private
(the manifest holds the sha256 of each sorted id list).

| Flag | Applied | Tasks | Detail | Reversed / applied by |
|---|---|---:|---|---|
| `statement_less`: under 40 characters before the first Example/Input heading | yes | 116 | aizu 102, hackerearth 10, atcoder 3, codechef 1 (same as the 15 Nov finding R6) | `--keep-statement-less`, after a human look at the private list |
| `effort_suite`: ids in `eval/effort_manifest.json` `training_exclusion` | yes | 55 listed, **55 present**: 30 code (aizu 8, atcoder 7, codechef 7, hackerearth 8), 25 MATH | none also statement-less; 0 listed ids missing from v1 | only if the suite is retired or re-drawn |
| `python2_only`: codechef and hackerearth (human references are Python 2 only) | **no, open** | 1,545 in v1, 1,519 still in the pool | keep: code pool 3,577. Drop: code pool 2,058 (aizu 1,860, atcoder 198) | `--drop-python2` (lead / TSAI decision) |
| `math_reserved`: the MATH part | yes, as a separate part | 7,209 (7,234 minus the 25 effort-suite tasks) | not in the RL pool: TSAI has not admitted Hendrycks MATH and this branch's licence table has no row for it | TSAI admission with a licence-table row adds the part as is |

**Code pool after the applied flags: 3,577 tasks** (3,723 − 116 − 30): aizu 1,860, hackerearth 1,038, codechef 481,
atcoder 198. The code part stands alone; MATH is reserved.

## 3. Verifier evidence: one correct answer scores 1, one wrong answer scores 0

Every verifier in the tree, run today unless the row says otherwise.

| Verifier | Tasks it scores | Correct → 1 | Wrong → 0 | Result today | Command |
|---|---|---|---|---|---|
| stdio, `rl-data/stdio_check.py` (via `survey.score_one`, Docker) | RL data v1 code_contests, one task per judge: aizu, atcoder, codechef, hackerearth | the row's human solution from the pinned parquet (codechef, hackerearth: Python 2 via lib2to3) | same program + `print(0)` | **4 of 4 judges pass** | `check_v1_human_references.py` (1) |
| math, `rl-data/math_check.py` (math-verify 0.9.0) | RL data v1 MATH (reserved part), 5 tasks | `\boxed{reference}` | `\boxed{reference+1}` | **5 of 5 pass** | same file (1) |
| `rl/verifier.py` (code functions) | 10 tasks in `rl/tasks` (written by an AI assistant: evaluation only, not RL data) | `reference.py` | a stub returning `None` | **10 of 10 pairs**; `test_verifier.py` 50 passed incl. Docker correct/wrong | `rl/reward.py --check-all` (2) |
| SWE, `swe-envs/verify.py` through `rl/reward.py` (Docker, arm64 images) | 21 envs in `swe-envs/` | the env's `gold.patch` | a no-op patch | **21 of 21 pairs** | `rl/reward.py --check-all` (2) |
| SWE-rebench pilot | 5 envs in `swe-envs/rebench-pilot/` | upstream fix | no patch | recorded 5/5 runs each on arm64 and amd64 (`swe_rebench_pilot.md`); **not re-run today**: `reward.py` does not list this folder | `swe-envs/rebench_pilot.py` |
| Indic, `rl/indic/indic_verifier.py` | 6 tasks in `rl/indic/tasks` | the task's accepted answer | the task's listed wrong answer | **6 of 6 pairs**; `test_indic_verifier.py` 59 passed | `rl/reward.py --check-all` (2) |
| Go, `rl/go/go_verifier.py` | 10 tasks in `rl/go/tasks` (AI-written, evaluation only by their README) | the task's reference | the task's wrong answer | **10 of 10 tasks, in both the process and the Docker sandbox**; `pytest rl/go` 91 passed, 0 skipped (Go 1.23.12 installed and the `g10-go-rl:1` image built from `go.Dockerfile` for this run) | `pytest rl/go -rs` (3) |

(1) `G10_RL_V1_DIR=<rebuild>/out/v1 G10_CC_SOURCE_DIR=<code_contests@802411c3>/data python -m pytest rl-data/check_v1_human_references.py -v` → `2 passed in 17.78s`.
(2) `python rl/reward.py --check-all --workers 1` → `{"checked": 74, "wrong": 0}`, 135 s (code 20, SWE 42, Indic 12); after the fix below, `--workers 2` gives the same 74 verdicts in 123 s.
(3) `PATH=<go 1.23.12>/bin:$PATH python -m pytest rl/go -v -rs` → `91 passed in 183.57s`; 20 `test_reference_scores_one` and 20 `test_wrong_answer_scores_zero…` cases (10 tasks x 2 sandboxes).
Peer suites: `pytest rl/test_verifier.py rl/test_reward.py rl/indic/test_indic_verifier.py swe-envs/test_verify.py` →
228 passed, 0 skipped (`rl/test_reward.py` includes the parallel SWE gold 1 / no-op 0 test).

Found and fixed while running: `rl/reward.py --check-all` with more than one worker crashed before scoring anything
(`AttributeError: module 'g10_rl_pool' has no attribute 'verifier_module'`): `_pool()` published the module before
`exec_module` finished, so a second thread got a half-run module. The same loader serves a trainer's scorer threads.
`_pool()` now publishes the module after it has run, under a lock. Regression test
`rl/test_reward.py::test_pool_module_loads_once_and_whole_when_many_threads_ask_at_once` (16 threads at a barrier):
fails 5 of 5 runs on the old file, passes 5 of 5 on the fix. `--check-all --workers 2`: 74 checks, 0 wrong, every
verdict equal to the `--workers 1` run; 123 s against 135 s on the loaded host (before the fix it did not run).

## 4. Team 9 pool check: what Team 9 needs

| Item | Value |
|---|---|
| Manifests | `rl-data/manifests/rl-code-code-contests-noncf.v1.json`, `rl-math-hendrycks-math-train.v1.json`, `rl_data_v1_close.json` |
| v1 files | `cc.jsonl` 3,723 rows `91ee99512f04…`; `math.jsonl` 7,234 rows `630c6dae44cd…` |
| Pool files, JSONL `{id, text}` for `decontam_check.py --id-field id` | code close pool 3,577 rows `71e000f4a340…`; MATH reserved 7,209 rows `f90a7b1fe5a6…`; the full v1 pools 3,723 rows `84b0a645882f…` and 7,234 rows `5148ce7a52f8…` |
| Decontam record | Team 9 tools `b470b4c0`, fingerprints v2 `2826a3b8…`; records equal to 11 Nov except `run_at` (manifest `decontam` fields) |
| Counts and funnel | `rl_data_v1_closure.md` (funnel) and section 2 above (flags) |
| Rebuild | `rl-data/rebuild_v1/rebuild_v1.py` (section 1); 12 of 12 outputs reproduce from the repo copy |
| Job request | `jobs/2026-11-18-rl-data-v1-pool.md` (draft, lead approval pending): TSAI rebuilds and stores the pool files for Team 9 |

The lead can instead hand the close pools (8.7 MB) to Team 9 directly; that is the lead's call.

## 5. Recommendation for evaluation (not a change to the reward)

Score held-out evaluation on the kept tests **plus the unused source tests** where they exist. RL data v1 keeps 20
tests per code_contests task; the pinned source rows hold more (median 101). In the 15 Nov audit, 5 of 162
rewarded completions at step 0 (3.1%) failed an unused test (3 runtime errors, 2 wrong answers), and 19 of 627 (3.0%)
from the trained state. The trained model's held-out gain survived the strict check (reward 26.0%, strict 25.7%).
Evidence: `verifier_data_note_20261115.md` (R5), `code_rl_e1_20261115.md` section 4 (R5b),
`fable_20261115_evidence/reward_audit_e1a.json`, `reward_audit_trained_e1a.json`. The training reward stays at the
kept 20 tests; only the evaluation would add the unused ones. Also in `../rl-data/README.md`.

## 6. Open (needs someone else)

- Python-2-only references: keep (pool 3,577) or drop (2,058). Lead / TSAI.
- The 116 statement-less tasks are flagged out by a regex; a human look at the private list may clear some.
- Hendrycks MATH admission for RL (TSAI); the 7,209-task part is ready as is.
- Pass-rate filtering on the real starting model (needs the checkpoint).
- `rl/go/test_go_verifier.py::test_lint_accepts_a_prompt_that_only_shows_visible_calls` fails on a machine without Go (it calls `go` with no skip guard). It passes with Go installed. That file is another member's, left unchanged.
