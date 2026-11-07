# Dedup design v1: How duplicates are found

Status: **DRAFT v1 — agreed by the team (Data A), pending TSAI review.** Open questions to TSAI are on PR #255. The method follows the implemented `overlap.py` and `overlap_rules.py` (see "Pipeline and hand-off to TSAI"). English and five-pack local results are in (below); thresholds marked *(to test)* wait for the all-pack overlap job.

Covers the duplicate "diseases" defined in `diagnosis/DISEASES.md`, section H.

---

## Summary of decisions

| Code | Disease | Proposed decision |
|---|---|---|
| H1 | Exact duplicate in the pack | SHA-256 of the H1 key: spec v1 `normalize.match_key`, then NFKC, casefold, whitespace collapse |
| H2 | Near duplicate (small changes) | **Exact** Jaccard of word 5-grams for every pair (`overlap.py`); counts as a duplicate at ≥ 0.80 for prose (English evidence: E1), 0.90 + same numbers for math, and token 5-gram Jaccard ≥ 0.85 for code *(to test)*; a pair from two families must pass both families' rules |
| H3 | Same content in another source/language | Same-language copies from another source: H1/H2 within each pack; across packs only if E2 validates it. Translations: **out of scope for v1**, pending TSAI confirmation; v2 candidate is multilingual embeddings or translate-then-match |
| – | Where dedup runs | After `clean.py`. **v1 default: within each pack only** (the per-snapshot analogue). Cross-pack and cross-team passes are measured, and applied only if E2 validates them |
| – | What is recorded | One log row per removed document: `(pack_id, split, part, doc_id)` for both removed and kept copies, similarity, rule, priority rule that decided; plus a remove list for TSAI |
| – | How it was tested | Known duplicate pairs + known non-duplicate pairs + gold harm check on `build_gold.py` output, matched on `(pack_id, doc_id)`, failing if no gold IDs are in the input |

---

## H1 — Exact duplicates

**Normalisation: the H1 key** (applied only to compute the hash; the stored text is not changed). Implemented as `h1_key()` in `h1_sha256.py`:
1. Spec v1 `normalize.match_key(text)` from `spec_v1/tools/normalize.py`, unchanged (spec v1 is frozen): HTML entities decoded, control and invisible characters removed, NFC with its listed folds, casefold, spaces collapsed.
2. Then on top: Unicode NFKC, case-fold, every run of whitespace (spaces, tabs, newlines) to one space. NFKC is applied here, never inside `normalize.py`, so spec v1 and G9's fingerprints are unaffected.

**Hash:** SHA-256 of the UTF-8 bytes of the normalised text.

Documents with the same hash form a group; one survivor is chosen by `source_priority_v1.md`, the rest are removed. It is cheap and exact, so it runs before H2 and shrinks the input to H2.

**The H1 hash is a dedup key only.** It never replaces `doc_id`. `doc_id` is `sha256(utf-8 original text)[:16]`, set before cleaning and carried through `run_clean.py` and the sample job unchanged; dedup reads it as-is and never re-hashes the cleaned text.

*Not normalised on purpose:* punctuation and digits. Stripping them would merge math problems that differ only in a number (see H2, math).

## H2 — Near duplicates

**Terms.** A document's *shingles* are the set of its word 5-grams (overlapping 5-word windows of the H1 key; repeats count once). The *Jaccard similarity* of two documents is shingles in both ÷ shingles in either. Example with 3-word shingles: "the cat sat on the mat" vs "the cat sat on a mat" share 2 of 6 distinct shingles, J = 0.33; compared word by word they would score 5/6 = 0.83, which is why single words are not used.

**Method: exact Jaccard of every pair** (`overlap.py`, with `jaccard_matrix.py`). Each shingle is stored as an 8-byte BLAKE2b digest; the documents × shingles matrix times its transpose gives the shared count of every pair that shares a shingle, block by block. There is no sampling and no MinHash estimate, so the score is exact and is the value logged. On the four English packs (426,508 documents, 9 × 10¹⁰ pairs) this took 845 s and 3.4 GB on a laptop. **Fallback:** if a run does not fit (see Risk 4), MinHash + LSH proposes candidates and each candidate is scored by the same exact Jaccard.

`overlap.py` measures and stores every pair at word Jaccard ≥ 0.5 (`floor`, at most 0.80 so no prose candidate is lost). `overlap_rules.py` then decides which pairs qualify as H1/H2 matches (`overlap_matches.csv`), with the settings below:

| Setting | Prose (English, science, Indic, `cadj-*`) | Code (`code-*`) | Math (`math-*`) |
|---|---|---|---|
| Shingles | word 5-grams of the H1 key | **token** 5-grams from the language's Pygments lexer; comments and a leading licence docstring dropped; strings and preprocessor directives kept | word 5-grams of the H1 key; numbers and LaTeX kept |
| Threshold (Jaccard) | **0.80** (English: E1) | **0.85** *(to test)* | **0.90** + the multisets of signed numbers must match (math: E1; see the numbers-rule finding) |
| Minimum length | 50 words; shorter documents get H1 only | 20 non-blank lines after comment removal | none; extra rule below |

**Families.** H1 compares every pack with every other and bypasses the length guards. For H2, a pair inside one family uses that family's rules. **A pair from two families must pass both families' rules on both documents** (the higher word threshold, the math numbers rule if math is involved, and the code token rule with the code member's lexer if code is involved). Notebooks (`cadj-notebooks`) and math pages can contain code, so mixed pairs are kept but judged strictly.

**Why 0.80 for prose.** It is the common setting in public pre-training pipelines and catches re-posted pages with changed boilerplate, dates or a few edited sentences, while pages that merely share a topic sit well below it. It is confirmed from the Jaccard histogram of all pairs (`overlap_histogram.csv`) on our packs: the threshold should sit in the gap between the "same text" cluster and the "related text" cluster.

**Why 5-grams.** Shorter shingles (1–3 words) make unrelated texts look similar through common phrases; longer ones make one edited word break many shingles. Five is the usual middle ground.

**Short documents.** In a 60-word document one changed word breaks 5 of about 56 shingles, so template pages that differ only in a name or date score about 0.82–0.85 (observed on the English packs). This is why H2 needs a minimum length.

**Code.** Files copied between forks differ in licence headers, comments and formatting, so code is compared on lexer tokens with comments and licence headers removed. Code/code pairs are scored in their own exact all-pairs pass, independent of the word-Jaccard floor, so a forked file whose comments lower its word score is still found. The higher threshold (0.85) avoids merging different files that share a lot of boilerplate (imports, generated code).

**Math.** Templated problems are the main risk: *"Solve 2x + 3 = 7"* and *"Solve 2x + 5 = 7"* are near-identical in text but are different problems. So for math packs a pair counts as a duplicate only if it passes the 0.90 threshold **and** the multiset of numbers in both documents is identical.

**Clusters.** Duplicate pairs are joined into clusters (union-find). One survivor per cluster is chosen by `source_priority_v1.md`.

## H3 — Same content in another source or language

`DISEASES.md` defines H3 as the same content in another source or language (e.g. a translation of a document seen in English). It has two halves, handled differently:

| Half | v1 | How |
|---|---|---|
| Same text from **another source**, same language | **Covered within each pack; across packs once validated** | H1 and H2 within each pack by default; the cross-pack pass is applied only if E2 validates it (see "Where dedup runs") |
| **Translation** into another language | **Out of scope for v1** | Not detected |

**Out of scope for v1: cross-language duplicates (the translation part of H3).** v1 finds exact (H1) and near (H2) duplicates by text within each pack, and across packs once the cross-pack pass is validated (E2), so the same text from another source in the same language is covered. A translation of a document into another language is not detected: that needs multilingual embeddings or translate-then-match, a different method and cost from hashing or MinHash, planned for **v2**. Within one document, `clean.py` already removes translation lines in Sanskrit (`DB-H3-001`, active on `ind-sa-fw2`); that rule stays and is not affected by this scope limit.

**Basis in the repo.** `spec_v1/README.md` lists H3 among the diseases regex cannot handle (needs a whole-pack check, a language model or a classifier). The instructor note of 30 Oct recorded there ("H3 has no rule") concerns code: a vendored copy is not a disease by itself, and the same file twice in a pack is H1 or H2. No TSAI ruling says dedup may skip the translation half, so this is stated as a **v1 limit pending TSAI confirmation**.

**Fallback if TSAI requires H3 for v1:** a narrow version for Sanskrit/Hindi/English only, where the Sanskrit packs are known to carry translations.

## Pipeline and hand-off to TSAI

```
raw sample ─▶ clean.py (TSAI, spec v1) ─▶ cleaned parts (doc_id, text, url, lang_label, pack_id)
                                              │
                                              ▼
                     overlap.py   MEASURES + QUALIFIES: H1 key, exact Jaccard of every pair, family rules
                                  → overlap_matches.csv, overlap_matrix.csv, overlap_docs.parquet, summary
                                              │
                                              ▼
                     dedup.py     DECIDES: scope, clusters, which copy survives
                                  → remove_list.csv, dedup_log.jsonl, dedup_summary.json
                                              │
                                              ▼
                     harm check   gold, matched on (pack_id, doc_id)
```

| Step | Code | Status |
|---|---|---|
| Measure and qualify | `overlap.py`, `overlap_rules.py`, `h1_sha256.py`, `jaccard_matrix.py`, `overlap_report.py`, `README_overlap.md`, tests; configs `overlap.json` (all 38 cleaned packs) and `overlap_local.json` (five-pack local run) | Written (Aneesha Das, Vijay Patil). Job request `jobs/2026-11-04-overlap.md` (38 packs; provisional 60 min / 32 GiB); `jobs/2026-11-04-overlap-en.md` is the earlier English-only request |
| Decide | `dedup.py` + `dedup.json`: read `overlap_matches.csv` and `overlap_docs.parquet`, apply the scope switch (within-pack default; cross-pack only if E2 validates it), join matches into clusters (union-find), pick survivors by `source_priority_v1.md`, write the remove list and log | To write |
| Check | harm check of the remove list against gold | With `dedup.py` |

**What TSAI receives:** the approved design (this file and `source_priority_v1.md`), the code and configs above with tests and test logs, and the job requests: (1) overlap on all 38 cleaned packs (`jobs/2026-11-04-overlap.md`; returns go to `jobs/results/2026-11-04-overlap/`, the reviewed matrix to `dedup/overlap_matrix.csv` by 13 Nov), (2) "which documents would v1 remove from sample v0, per pack and stage, and does it remove any gold?" After approval TSAI applies the **remove list** to the full data, as it applies spec v1. The data is filtered, never rewritten by our code, so every removal is reversible from the log.

## Where dedup runs

1. **After `clean.py`.** Cleaning removes boilerplate and fixes encoding, which can turn two different pages into identical ones; deduplicating earlier would miss those.
2. **Within each pack** (H1 then H2). **This is the v1 default.** It is the analogue of FineWeb's per-snapshot dedup, which trained better models than global dedup (Session 3, §7; Risk 1).
3. **Across packs** (H1 then H2 on the union of surviving documents) — covers the same-language half of H3. **Measured, not applied by default:** it is run and its removals logged, but applied to the data only if E2 shows it removes a modest share of each pack and no gold document.
4. **Across both teams' packs** (Data B's Indic and `cadj-*` packs are in the 38-pack job): same rule as step 3, plus the Indic check (E4).

Our packs are split by domain or source, not by crawl time as FineWeb's snapshots were, so a copy found in two of our packs is closer to a true duplicate than a page repeated across crawls. The analogy is therefore partial: it does not prove cross-pack dedup harmful here, only that the wider scope should not be the default until checked.

Dedup is not a cleaning job request: TSAI applies the approved spec v1 rules to the full data.

## What is recorded

For every removed document, one row in `dedup_log.jsonl`:

| Field | Meaning |
|---|---|
| `removed_pack_id` | Pack of the removed document |
| `removed_split` | `train` or `heldout` |
| `removed_part` | Part of the removed document |
| `removed_id` | `doc_id` of the removed document, unchanged |
| `kept_pack_id` | Pack of the survivor |
| `kept_split` | `train` or `heldout` |
| `kept_part` | Part of the survivor |
| `kept_id` | `doc_id` of the surviving copy it duplicated, unchanged |
| `rule` | `H1`, `H2` or `H3` |
| `similarity` | 1.0 for H1; exact Jaccard for H2/H3 |
| `priority_rule` | Which `source_priority_v1.md` rule chose the survivor (0–4) |
| `stage` | `within_pack`, `cross_pack` or `cross_team` |

**Why both sides carry pack, split and part.** `doc_id` is a hash of the original text, so exact copies share it. Within one part this cannot happen (the sample job stops on a duplicate `doc_id`), but across parts or packs it can, giving `removed_id == kept_id`; `overlap.py` reports such IDs as `ids_used_by_2_or_more_documents`. A document is therefore identified by `(pack_id, split, part, doc_id)`, never by `doc_id` alone. (`overlap.py` names a document `<pack_id>-<doc_id>` and gives split and part in separate columns.) No current gold ID appears in two packs (checked across all 3,269), but this can change after a full run.

Plus `remove_list.csv` (`pack_id, split, part, doc_id`: what TSAI filters out) and a summary per pack: documents in, removed by H1, removed by H2, removed cross-pack, documents out.

## How it was tested

1. **Known duplicate pairs** (must be caught): an exact copy; a whitespace/case variant; a copy with one sentence edited; a copy with a licence header added (code); a truncated copy.
2. **Known non-duplicate pairs** (must be kept): two math problems that differ only in a number; two pages on the same topic from different sources; two code files sharing imports only.
3. **Harm check:** no gold document is removed.
   - **Gold source:** `<pack>_gold.csv` (`doc_id,reader_1,reader_2`) written by `build_gold.py`, read by `harm_test.py --gold`. A document is gold only if two different reviewers marked it `read=full`, `verdict=clean` in the same pack, with no disease other than D3. The raw `labels.csv` votes are never read. Data A gold: `teams/01-data-a/gold/`; Data B (Indic, cadj): `teams/02-data-b/gold/`, same format.
   - **Matching:** a gold document counts as removed if `(pack_id, doc_id)` appears on the removed side of `dedup_log.jsonl`. Matching on `doc_id` alone would wrongly flag a gold document whose identical copy was kept.
   - **Coverage first:** gold comes from the week-1 diagnosis packs (~500 docs each); the tokenizer sample (1.44M docs) is a separate draw. Before the check, count how many gold IDs are present in the dedup input and report that number with the result. **If it is zero, the harm check fails**, because it tested nothing. Preferred: run the harm check on the diagnosis packs, where gold coverage is guaranteed.
   - `harm_test.py` already refuses a gold file whose IDs are missing from the pack, so a mismatched pack and gold file fails loudly.
   - Any gold removal is listed and reviewed by hand.
4. **Threshold check:** the Jaccard histogram of all pairs (`overlap_histogram.csv`) and the pair counts at 0.70–0.95 per family, plus a hand review of ~20 pairs just above and ~20 just below each threshold.
5. **Real counts:** duplicates found per rule per pack, reported in the summary table.

## Risks

**1. Wider scope can remove better text.** Deduplicating across a wider scope removes more documents, but more removal is not automatically better. FineWeb found that global dedup (across all crawl snapshots) trained worse models than per-snapshot dedup; in its oldest snapshot, the documents kept by global dedup were worse than the ones it removed (Session 3, §7). The reason: text repeated across many crawls tends to be good text that is reposted and linked; global dedup cut it to one copy while unique, often low-quality text was untouched, so the low-quality share of the mix grew. Our cross-pack and cross-team passes are the wider kind.
- *Survivor choice does not fix this.* `source_priority_v1.md` picks the better **copy** (licence, provenance, completeness), but the FineWeb risk is about how much **weight** popular content keeps in the mix, which any one-copy rule reduces.
- *Mitigation:* within-pack dedup is the v1 default; the cross-pack pass is measured but applied only if E2 validates it. Each log row records the `stage`, so within-pack and cross-pack removals are counted separately, and each removed document points to its survivor, so cross-pack removals can be reversed. Every dedup scope decision is treated as an ablation, not a given (Session 3, §11).

**2. Thresholds may not transfer to Indic text.** The thresholds are tested on the Data A packs (English, code, math, science) only. Word 5-grams split on whitespace may behave differently on Indic scripts (agglutinative words, code-mixing, varied spacing), and methods tuned on English text are known to erase Indic content (Session 3, §8).
- *Required check:* the 38-pack job includes 22 Indic packs, which get the prose rules. Before H2 removals are applied to Indic data, run E4: the threshold check (histogram and hand review either side of 0.80) on at least one Indic pack, with Indic removal rates reported separately.

**3. Benchmark contamination is not covered.** Dedup removes repeated documents within the training data. Exact and fuzzy matching against held-out benchmark sets is a separate evaluation-integrity step (Session 3, §12) and is **not** part of this design. Passing dedup does not mean the data is free of test leakage. (Train/held-out copies inside the sample are handled: `source_priority_v1.md` rule 0.)

**4. Exact all-pairs scoring may not fit the code packs.** The English run took 845 s and 3.4 GB. Code shares much more boilerplate (imports, licence text, generated code), so far more pairs share a shingle and the matrix product grows. The all-pack overlap job will show it. If it does not fit, use the MinHash + LSH fallback for the affected family; the exact score of each candidate is unchanged.

## Experiments before final

E1 and E2 run on the Week-2 tokenizer sample v0 with `overlap.py` (Task 5: Aneesha, Narasimha Teja). E3 runs on hand-built pairs (`tests/test_overlap.py` covers the scoring). The harm check also runs on the week-1 diagnosis packs, where gold coverage is guaranteed. Results come back into the final version of this file.

| # | Experiment | What is measured | What would change the design |
|---|---|---|---|
| E1 | **Threshold sweep** per family (English and math done; code and science after the all-pack run): pairs at 0.70, 0.75, 0.80, 0.85, 0.90, 0.95 | Jaccard histogram of all pairs; hand review of ~20 pairs just above and ~20 just below each proposed threshold; removals per threshold | Move a threshold if the gap between "same text" and "related text" sits elsewhere, or if hand review finds distinct documents above it |
| E2 | **Within-pack vs cross-pack**: run the within-pack pass alone, then add the cross-pack pass | Removal counts per pack and per stage; harm check on each output separately | **Decides whether the cross-pack pass is applied.** Apply it only if it removes a modest share of each pack and no gold document; otherwise report it but keep within-pack dedup only (Risk 1) |
| E3 | **Known-pair tests**: the duplicate and non-duplicate pairs listed in "How it was tested" | Every duplicate pair caught; every non-duplicate pair kept | If math problems differing only in a number are merged, tighten the math rule; if a known copy is missed, revisit normalisation or shingle size |
| E4 | **Indic threshold check** (required: Indic packs are in the 38-pack job): E1 on at least one Indic pack | Same as E1; Indic removal rate reported separately | Use separate Indic thresholds or shingling (e.g. character n-grams) if the English settings over- or under-remove (Risk 2) |

### Results so far: English packs (sample v0, train + heldout, 426,508 documents)

From `jobs/logs/2026-11-04-overlap-en-local.txt`:

| | Within pack | Cross pack | All |
|---|---:|---:|---:|
| Exact (H1) pairs | 16 | 0 | 16 |
| Pairs at Jaccard ≥ 0.80 | 44 | 11 | 55 |

- **H1:** 9 groups, 21 documents, all inside `en-nemotroncc`; removing all but one per group removes 12 documents.
- **E1 (prose threshold):** pairs at or above 0.70: 135, 0.75: 90, **0.80: 55**, 0.85: 43, 0.90: 33, 0.95: 25. Hand review of pairs around 0.80 is still to do before the threshold is final.
- **E2 (scope, English):** cross-pack dedup would remove **at most 11 of 426,508 documents** (11 cross-pack pairs at ≥ 0.80), about 0.003%. Risk 1 is negligible for English; whether to apply the cross-pack pass is decided per family once the all-pack run is in.
- **Still to count:** train/held-out pairs (rule 0) and gold documents involved, from `overlap_pairs.csv`.

### Results so far: five-pack local run (sample v0 parts, not cleaned)

From `jobs/logs/2026-11-04-overlap-local/` (`code-rust`, `en-fineweb-edu`, `ind-hi-hplt`, `ind-mr-sangraha-v`, `math-finemath`; 183,976 documents; 571 s, 2.76 GiB):

- **0 H1 groups; 372 qualifying H2 pairs: 371 within packs, 1 cross-pack** (`en-fineweb-edu` ↔ `math-finemath`).
- Largest share: `code-rust`, 57 of 60,738 documents (0.09%) have a match in their own pack. Indic: `ind-hi-hplt` 2 of 8,840; `ind-mr-sangraha-v` 0.
- This shows the scripts run on real data; it is **not** the final result (raw parts, 5 of 38 packs). The final numbers come from the TSAI 38-pack job.

### Results so far: math packs, E1 (sample v0 parts, not cleaned)

`math-finemath` and `math-megamath`, train + heldout, 47,250 documents; config `overlap_math.json`; 97 s, 1.0 GB. Log: `jobs/logs/2026-11-04-overlap-math-local.txt`.

| | |
|---|---|
| H1 exact groups | 0 |
| Pairs by word Jaccard ≥ 0.70 / 0.75 / 0.80 / 0.85 / 0.90 / 0.95 | 369 / 243 / 131 / 68 / 46 / 18 |
| Of the 46 at ≥ 0.90: qualify / rejected by the numbers rule | 36 / 10 |
| Qualifying matches: within `megamath` / within `finemath` / cross-pack | 32 / 3 / 1 |
| Clusters → documents removed | 10 clusters, 28 documents → **18 removed (0.04%)** |
| Train ↔ held-out matches | 1 (rule 0: the train copy is removed) |
| Gold IDs present in this input | 0 of 112 |

Hand review of all 10 rejected pairs and the lowest-scoring kept pairs:

1. **The numbers rule rejects true copies whose only numeric difference is a header.** Two pairs are the same page saved twice (Jaccard 0.987 and 0.972), differing only in a date line ("Dec 10, 2015 · 15 minute read") or a number in the title ("UVa 11357"), plus Markdown formatting. Both pairs share their URL.
2. **Template pages pass 0.90.** The largest cluster (7 documents) is slideserve.com pages: different presentations ("projectile motion", "the preprocessor", …) inside ~117 words of identical site boilerplate. They pass the threshold and any word minimum; only the title differs. They are low-value pages, but they are not copies of one document: this is a quality-filter problem, not a dedup one. (The same effect as the 0.82–0.85 template pages in English.)
3. **The rule works where it should.** Two chemistry textbook chapters with different worked values are kept apart.
4. **A same-URL copy is missed just below 0.90.** reference.com's "examples of quadrilaterals" appears in `finemath` train and `megamath` held-out with the identical URL, at Jaccard 0.894.
5. **The gold harm check cannot be run on the sample.** None of the 112 math gold IDs are in it, which confirms that the harm check must run on the diagnosis packs.

Proposed changes for the final version (to agree with the team):
- **Numbers rule:** compare numbers in the body only (ignore the title and first line), or skip the numbers check when both copies have the same normalised URL.
- **Same URL as a signal:** two documents with the same normalised URL (scheme, `www.` and trailing `/` ignored) count as H2 duplicates at word Jaccard ≥ 0.80, in any family.
- **Template pages:** recorded as a known limit of H2; passed to the quality filter rather than handled by dedup.

**Training ablation (not run in v1; budget-dependent).** The definitive test of dedup scope is to train small proxy models on the data after within-pack dedup only and after within- plus cross-pack dedup, and compare downstream scores (Session 3, §7 and §11). v1 does not run this; scope is checked by removal counts and the harm check only. If proxy-training budget becomes available, this is the first dedup experiment to run, because it is the only one that can show whether the wider scope helps or hurts the model. It is only worth running for a family where cross-pack dedup removes a measurable share (≥ 1% of a pack); for English it does not.

## Open questions for the team

- Confirm 0.80 for prose after the hand review; agree 0.85 (code) after the all-pack overlap run. Math 0.90 holds on E1.
- Math numbers rule: body-only numbers, or skip it for same-URL pairs? Add same URL as an H2 signal? (Math E1 findings.)
- Is 50 words the right minimum length for H2 on prose? (Short template pages score 0.82–0.85.)
- Who writes `dedup.py`: Task 4 or Task 5?
- **Asked TSAI on PR #255:** H3 translation scope; Data B in the cross-team pass (the 38-pack job already includes it); pack order; held-out copies; remove list as the hand-off; folder location.
