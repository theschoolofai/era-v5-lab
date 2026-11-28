# Team 1 (Data A): Lab 5 evidence list

Kept by Sourav Dhar · GitHub: sourav-dhar · Team 1 (Data A), as the brief asks ("Name one person who owns your team's
evidence list"). Last update: **28 Nov 2026, 20:00 IST**. Due: **Wed 2 Dec, 7:00 AM IST**; 70% by Mon 30 Nov.

Owners are from the team doc's Lab 5 table and the claims in G1. A row is **done** when its output exists, a reviewer
can reproduce it from the command in the PR, it passes the check TSAI names, and every difference from that check is
written down (the brief's "What counts as done"). Rows with no PR yet say so. Corrections: tell Sourav in G1, or edit
this file in a PR.

## Tasks

| # | Task (brief) | Owner | Evidence (PR, log, hash) | TSAI's check | Status |
|---|---|---|---|---|---|
| B1 / D1 | Dataset list; unique tokens for a 20T Stage 1 and their supply, gaps and fixes | Tejaskumar Reddy J (TEJASKUMAR-REDDY-J) | none yet; first table planned for Mon 30 Nov (G1, 28 Nov 12:26 IST) | list file; "compare with TSAI's list only after you finish yours" | claimed |
| B2 | Sources outside the 38 packs: clean rules, pack_table row, parquet parts | Vijay Patil (patilvijay23) | none yet (G1, 28 Nov 18:58 IST) | pack_table refusal on null fields | claimed |
| B3 | Exact-hash dedup across all packs; text-hash column; hash-only provenance | Aneesha Das (aneeshads) | [#898](https://github.com/theschoolofai/era-v5-lab/pull/898) (head `75d48176`): `dedup/hash_overlap.py`, `text_hash` in the clean job, `provenance.py`; 1% run: all pipeline checks pass, overlap 18.5 s → 0.9 s, byte-identical shards; TSAI accepted the format (review, 28 Nov); rerun by Sourav on another Mac gave the same rows per pack and stage (comment on #898, 28 Nov) | provenance chain | in review |
| B4 / D4 | Validation shards from a fixed-seed held-out slice; train-vs-validation leak check; the mix in the shard manifest | Smita Sasindran (smitasasindran) | none yet (G1, 28 Nov 10:54 IST) | `verify_shards.py`; leak check | claimed |
| B5 | Shard writer twice on the same input: byte-identical files, tokens per second per core | Narasimha Teja (narasimhatejav), with Kunal Sinha (kunal2016) | none yet; Kunal's pointers (G1, 28 Nov 14:11 IST): the 19 Nov rehearsal's `compare_shards_two_runs.txt` (144/144 data files identical) | two-run sha comparison | claimed |
| B6 | Licence rule 1: NC, ND and unstated allowed; licence column kept | Narasimha Teja (narasimhatejav) | none yet; TSAI's rule is now lab rule 1 (CAP, 28 Nov 16:06 IST) | pack_table licence fields | claimed |
| B7 | F2 at full scale | Sourav Dhar (sourav-dhar) | [#935](https://github.com/theschoolofai/era-v5-lab/pull/935): `pipeline/f2_full_scale_v1.md` (rates on the 38 packs, where the time goes, plan, command), logs `jobs/logs/2026-11-28-b7-f2-rates-mac/` | measured rate before scaling (rule 4) | in review |
| D2 | Pass diagram, cut passes, 1% sample report, overlap peak RAM | Aneesha Das (aneeshads), Kunal Sinha (kunal2016) | [#898](https://github.com/theschoolofai/era-v5-lab/pull/898): `pipeline/passes_design_v1.md`, 1% logs; section 4 (peak RAM) by Kunal; [#807](https://github.com/theschoolofai/era-v5-lab/pull/807) (MinHash row ranges, draft) | the pass diagram with rates | in review |
| D3 | What must be frozen before the full tokenizing run, each proved on a sample | Kunal Sinha (kunal2016) | none yet (G1, 28 Nov 12:50 IST) | | claimed |
| D5 | Quality classifier; drop or down-weight the bottom tier; proxy run | Kunal Sinha (kunal2016) | none yet (team doc) | proxy run (49M, 500M tokens, 2 seeds) | claimed |
| D6 | Find the mix by experiment (proxy runs, lane weights) | **no owner** | | proxy runs with error bars | open |
| D7 | Annealing data (best 5% to 10%), with a proxy run | **no owner** (team doc: "UNK"; depends on D5) | | proxy run | open |
| D8 | Missing kinds of data: long documents, reasoning traces, tool calls, code with execution results | Vijay Patil (patilvijay23) in the doc; Sourav Dhar writing it up from #914 (G1, 28 Nov 19:25 IST) | the numbers: [#914](https://github.com/theschoolofai/era-v5-lab/pull/914) §3 and §4 | | in progress |
| D9 | Data for post-training: reply to Team 10's request (#882) | Sourav Dhar (sourav-dhar) | [#914](https://github.com/theschoolofai/era-v5-lab/pull/914) (draft): RL math pool v1 (109,246 rows, parquet sha256 `56394b30…`, F2 full set 0 flagged), SFT and long-context survey | F2 (`decontam_check.py`, set `2826a3b8…`) and `canary_scan.py`, 0 flagged | in progress; reply in #882 on Mon 30 Nov |
| — | Corpus-v1 token count | Sourav Dhar (sourav-dhar); Smita verifies, Vijay publishes | tools ready; waits on TSAI's corpus-v1 production run | | blocked (TSAI) |

## Findings sent to TSAI

| Finding | Owner | PR / issue | TSAI's ruling | Status |
|---|---|---|---|---|
| spec v1.1 `clean.py` applies NFKC in DA-A5-002 (lines 3398, 3405) | Aneesha Das | [#912](https://github.com/theschoolofai/era-v5-lab/pull/912), issue [#915](https://github.com/theschoolofai/era-v5-lab/issues/915) | DA-A5-002 deferred; one cleaner change with one new pin before corpus-v1, passing tests, 1% rerun | tests marked strict xfail; fix PR by Aneesha |
| DA-B4-001 deletes LaTeX bracket groups in math docs (line 3495) | Sourav Dhar | [#911](https://github.com/theschoolofai/era-v5-lab/pull/911), issue [#926](https://github.com/theschoolofai/era-v5-lab/issues/926); collated into #912's branch by aneeshads/era-v5-lab#1 | fixed in the same cleaner change as #912 | tests marked strict xfail; fix in Aneesha's PR |

## Requests between teams

| From | Request | Team 1 owner | Evidence | Status |
|---|---|---|---|---|
| Team 10 | SFT and RL data (#882) | Sourav Dhar (RL math, code, agentic, tool calling, math / general, long context) | [#914](https://github.com/theschoolofai/era-v5-lab/pull/914) | reply in #882 on Mon 30 Nov |
| Team 4 (KE2) | R1 word frequency table, R3 held-out code with identifiers | Kunal Sinha asked to take them (G1, 28 Nov 14:11 IST) | none yet | reply due Mon 30 Nov 18:00 IST |
| Team 9 | F2 fingerprints | (Team 9 gives) | fingerprints v2, `set_sha256 2826a3b8…` | in use |

## Pending items from TSAI's status (28 Nov)

| Item | Evidence | Status |
|---|---|---|
| #858 (E5c files) | merged 27 Nov | done |
| H3 per-pair removal | [#860](https://github.com/theschoolofai/era-v5-lab/pull/860), merged 28 Nov | done |
| `data_card_v1.md` | Sourav Dhar assembling it from each owner's part (G1, 28 Nov 19:25 IST) | in progress |
