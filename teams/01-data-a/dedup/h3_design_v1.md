# H3 design v1: How translations are found

**Status:** draft, for dedup v1.1. Nothing here is agreed yet; the open decisions are listed before the decision log.
**Scope:** H3 of `diagnosis/DISEASES.md`, section H: "the same content in another source or language", for example a
translation of a document seen in English. `dedup_design_v1.md` covers H1 and H2 and leaves translations out of v1
(TSAI, 5 Nov). This file is the method for that half.

## Summary

| Topic | Proposal | Status |
|---|---|---|
| What H3 covers | The same content in two languages. Same-language copies from another source stay with H1/H2 | Proposed |
| Why remove | Train copies of held-out documents across languages (rule 0). Everything else is measured and reported first; removal is decided from the counts | Proposed |
| Score | Sentence coverage: aligned sentences / sentences of the shorter document | Proposed; threshold set by E5 |
| Method | Candidates from a multilingual encoder (LaBSE) and URL keys; confirmed by sentence alignment | Code written (`h3.py`); not run on real data |
| Scope | Indic ↔ English and Sanskrit ↔ Hindi, prose packs only | Proposed |
| Where it runs | After H1/H2 dedup, before F2: Clean → H1/H2 → H3 → F2 | Proposed |
| Which copy survives | Rule 0 first (held-out always survives). After that: open | Open |
| Speed | Batched on the GPU, no Python loop per document, sentence or pair (TSAI rule, 14 Nov) | Rework needed (see "Speed") |

## The H3 score

H1 compares SHA-256 hashes and H2 compares word 5-grams, so neither can match two languages: a translation shares no
hash and almost no 5-grams. H3 compares meaning, sentence by sentence:

| | Compared | Score | Rule |
|---|---|---|---|
| H1 | H1 key | SHA-256 | equal |
| H2 | word or token 5-grams | Jaccard: shared / all shingles | ≥ 0.80 (prose) |
| H3 | sentences, as vectors of a multilingual encoder | coverage: aligned sentences / sentences of the shorter document | ≥ 0.6 (provisional) |

Two sentences **align** when each is the other's best match among the two documents' sentences (mutual best, so one to
one) and their cosine is at least 0.7 (provisional). A page on the same topic scores high as a whole document, but its
sentences do not align one to one, which is why coverage is counted on sentences, not on whole documents (the same
reason H2 rejects same-topic pages, E3).

## Methods considered

| Method | How | Strength | Weakness | Use in v1.1 |
|---|---|---|---|---|
| URL key | The same site and path with only a language marker changed (`hi.`, `/hi/`, `?lang=hi`) | Exact, nearly free; the cleaned parts have `url` | Finds only multilingual sites | Candidates |
| Language-neutral anchors | Numbers (any script's digits), Latin-script names | Cheap | Weak alone | Hand-review aid |
| Document embedding | One multilingual vector per document; cosine | Fast candidate search | Same-topic pages score high | Candidates |
| Sentence alignment | Sentence vectors, mutual best match, coverage | Separates translations from same-topic pages | Needs the model on every candidate sentence | Decision |
| Translate, then H2 | Machine translation (IndicTrans2, NLLB), then Jaccard | Familiar score | Very costly; machine output rarely reaches 0.80 against a human translation | Second opinion on a sample only |
| Transliterate, then H2 | One script, then Jaccard | Reuses H2 | Same language in another script only (D2), not translations | Not H3 |

**Encoder:** LaBSE (`sentence-transformers/LaBSE`, Apache-2.0), built for finding translation pairs; AI4Bharat used it
to mine English–Indic pairs for Samanantar. Its model card lists 110 language tags; Sanskrit and Odia must be checked
before their packs are relied on. Alternatives to compare in E5 if LaBSE is weak on a language: LASER/SONAR,
multilingual-e5, BGE-M3. Only the safetensors weights and the small config files are needed (about 1.9 GB of the 9.44 GB
repo).

## Pipeline

```
cleaned parts (TSAI, spec v1) ──▶ H1/H2: overlap.py ─▶ dedup.py ─▶ remove_list.csv
        │                                                              │
        │   (H1/H2 removals are skipped, so each duplicate group is    │
        ▼    compared once)                                            ▼
  h3.py  1. read      configured packs only; split sentences; skip short documents; head = first 4 sentences
         2. encode    one vector per document (head), batched; cached per part
         3. url       language-neutral URL key: exact join
         4. retrieve  per language pair: each document's top_k nearest documents in the other language;
                      a candidate must be mutual and at cosine >= doc_floor
         5. verify    length-ratio check; sentence vectors; mutual best sentence matches; coverage
         ──▶ h3_matches.csv (rule H3, stage cross_language), h3_candidates.csv, h3_docs.parquet, h3_summary.json
                                              │
                                              ▼
  dedup.py   H3 matches join the clusters: rule 0 (held-out survives), then the H3 survivor rule (open)
                                              │
                                              ▼
  TSAI       filters with the remove list ─▶ F2 (G9's fingerprints) ─▶ deduplicated sample
```

| Stage | What it does | Cost | Settings (provisional) |
|---|---|---|---|
| read | Selects parts by their `pack_id` column; sentences end at `.`, `!`, `?`, `।`, `॥` or a line break; sentences under 20 characters are dropped | Text processing | `min_chars` 200, `min_sentences` 3, `max_sentences` 16 |
| encode | The head of each document | One encoder pass per document | `head_sentences` 4, `max_seq_length` 128 |
| url | One language marker removed from the URL; home pages excluded | Negligible | `url_group_max` 20 |
| retrieve | Exact cosine by blocked matrix products; no approximate index | Grows with the product of the two languages' documents | `top_k` 3, `doc_floor` 0.5, `mutual` true |
| verify | URL pairs first, then by cosine; at most `max_verify` pairs | One encoder pass per candidate sentence | `max_length_ratio` 4, sentence cosine 0.7, coverage 0.6 |

Every threshold is provisional, as 0.80 was for H2 before E1: E5's sweep and hand review set them.

**Outputs** (IDs, scores and counts only; no text leaves `out/`):

| File | Contents |
|---|---|
| `h3_docs.parquet` | row → document: `row, id, doc_id, pack, lang, split, part, row_in_part, chars, sentences` |
| `h3_candidates.csv` | every verified pair at or above `report_floor`, and every URL pair: cosine, length ratio, sentences, aligned, coverage |
| `h3_matches.csv` | pairs at or above the coverage threshold: `row_a, row_b, rule (H3), stage (cross_language), pack, split, coverage` |
| `h3_by_pack.csv`, `h3_histogram.csv` | per pack pair: retrieved, URL, verified, qualifying; histograms of cosine and coverage |
| `h3_summary.json` | counts, stage times and rates, an estimate for all documents, model weights' SHA-256, package versions, output SHA-256 |

**Hand-off to `dedup.py`:** `h3_matches.csv` rows use `h3_docs.parquet`'s row numbers, not overlap's. `dedup.py` needs
a small change to read both match files and join them on `(pack_id, split, part, row_in_part, doc_id)` before forming
clusters. Until the survivor rule is decided, H3 matches are reported, not removed. The first version of `h3.py` does
not yet skip the rows in `remove_list.csv`; that is a small addition (an `exclude` key in the config).

## Which copy survives

| Case | Proposal |
|---|---|
| A train document and a held-out document in two languages | Rule 0, unchanged: the held-out copy survives, the train copy is removed. This is the strongest reason for H3: without it the model trains on held-out content in another language |
| Two held-out documents | Reported, not removed (rule 0) |
| A machine-translated copy of an English page | Overlaps with D4 (bad machine translation) and D5 (translationese). Removal is defensible; decide from E5 |
| A good human translation | Keep and report: it is new text in a language with less data (Risk 2 of `dedup_design_v1.md`) |

## Speed (TSAI rule, 14 Nov)

The job would run on 1 GPU. Code for a TSAI run must use batched operations, no Python loops over tokens, documents or
pairs, and no avoidable host-device syncs, and the PR must give the wall time of a short run, the exact command and the
last lines of its output. The current `h3.py` is a CPU/NumPy first version; before any TSAI run it needs:

| Part | Now | Needed |
|---|---|---|
| Read | Python loop per document (sentences, length, URL key) | pyarrow compute on whole columns: regex split, `utf8_length`, list offsets for the head, `binary_join`; the scalar functions stay as test references |
| Encode | Each batch copied back to the host | Vectors kept on the device (`convert_to_tensor`); bf16 on CUDA |
| Retrieve | NumPy on the CPU | torch `matmul` and `topk` on the GPU, in blocks |
| Verify | One alignment call per pair | Padded `[pairs, 16, d]` tensors, one batched product and a masked argmax per chunk |
| Signals | Numbers and Latin names per pair, in the job | Moved to a local hand-review script, as `e4_review.py` does for E4 |
| Evidence | — | `set_sync_debug_mode("warn")` with no warnings; a timed run on full packs; the PR's Speed and End-to-end sections |

Kept from the first version: the cache (a rerun with other thresholds encodes nothing again), the time limit
(`max_minutes`; an incomplete run writes only its summary), the per-stage timing and the estimate for all documents,
which gives the job request's Max time.

**Offline:** `JOB_REQUEST.md` rule 1 allows no network, so the model is loaded only from a local folder with the Hugging
Face libraries set offline. TSAI needs the same LaBSE folder as an input; the summary records the weights' SHA-256.

## Validation

| # | Check | What it shows | Status |
|---|---|---|---|
| E5a | **Known pairs:** a translation is caught; a same-topic page, a page sharing only names or numbers, and a same-URL page with other content are kept; train ↔ held-out keeps the held-out copy | The rules behave as specified | Done with a fake encoder: 44 tests (`tests/test_h3.py`, `test_h3_signals.py`, `test_h3_align.py`) |
| E5b | **Local timed run** on the raw packs `ind-sa-fw2`, `ind-hi-fw2` and `en-fineweb-edu` (`h3_local.json`) | Stage times, the estimate for all documents, first counts | Waiting for the model download |
| E5c | **Measurement job** on the cleaned sample (TSAI), removing nothing | H3 counts per language pair; cosine and coverage histograms | After the speed rework |
| E5d | **Threshold sweep and hand review:** bilingual readers label pairs on both sides of the threshold, blind | Where the coverage threshold sits | After E5c; the readers' labels are the result |
| Harm | No gold document removed | No harm to reviewed clean documents | After a removal rule exists |

## Risks

1. **Removing scarce Indic text.** A translation is new text in another language. *Mitigation:* rule 0 only, until E5
   shows what the other pairs are.
2. **Same-topic pages as false matches.** *Mitigation:* sentence coverage, not document cosine, decides; E5a tests it.
3. **Encoder coverage.** LaBSE may be weak on Sanskrit or Odia. *Mitigation:* check coverage, compare an alternative
   encoder in E5, report per language pair.
4. **Sentence splitting.** Scripts and pages without clear sentence marks give long "sentences". *Mitigation:*
   `max_sentences` and the length checks; per-pack sentence counts in `h3_docs.parquet`.
5. **Cost.** Retrieval grows with the product of the two languages' documents. *Mitigation:* language-pair scope,
   blocked GPU products, `max_verify`, the time limit and the estimate before the job.

## Open decisions (team, then TSAI)

- Whether H3 joins dedup in v1.1 at all, and its scope: Indic ↔ English and Sanskrit ↔ Hindi first; Data A ↔ Data B
  translations need TSAI's agreement (out of v1, 5 Nov).
- The survivor rule after rule 0, and whether anything beyond train ↔ held-out is removed.
- The encoder, after the coverage check.
- Thresholds: from E5d.
- Order in the pipeline: after H1/H2 (as above) or in the same pass.

## Decision log

| Date | Decision | Agreed by | Where |
|---|---|---|---|
| 5 Nov 2026 | H3: translations out of scope for v1; H1/H2 cover same-language copies from another source; `DB-H3-001` stays | TSAI | PR #255, TSAI comment of 5 Nov, point 1 |
| 5 Nov 2026 | Rule 0: a held-out copy always survives; held-out ↔ held-out duplicates are reported, not removed | TSAI | PR #255, point 4 |
| 14 Nov 2026 | First draft of this file; `h3.py` first version with 44 tests (fake encoder) | Aneesha Das (draft) | not yet in a PR |
