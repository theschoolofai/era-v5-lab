# G1 code audit — Revant Gupta

Task row 8 · Code domain · 100 cleaned TRAIN documents · Final preparation: 12 November 2026

## How it was read

Revant Gupta manually read the full cleaned text of all 100 selected documents and retained all seven AI-suggested findings below. The seven findings are reader-checked AI suggestions, recorded as `source=ai`, rather than claims of independent manual discovery.

The sample contains **34 JS/TS, 33 Python and 33 Rust** documents. The supplied `pick_docs.py` was used with seed **20261101**, loading **Part 1 before Part 2** within each pack and taking the first 34/33/33 shuffled IDs respectively. An independent picker check agreed. The appendix records all 100 selected IDs in their original picker order. Heldout documents were not downloaded or reviewed.

| Pack | Cleaned TRAIN files, in load order | Documents read |
|---|---|---:|
| code-js-ts | `code-js-ts_part1.parquet`, `code-js-ts_part2.parquet` | 34 |
| code-python | `code-python_part1.parquet`, `code-python_part2.parquet` | 33 |
| code-rust | `code-rust_part1.parquet`, `code-rust_part2.parquet` | 33 |

The cleaner and runner match official job commit **`8da2ac442dd114d093fe58c6fc14506010dcbe9f`** (`8da2ac4`). All six cleaned-part hashes match the official cleaned manifest. Four original TRAIN parts were additionally verified against the official input hashes: `code-js-ts_part1.parquet`, `code-js-ts_part2.parquet`, `code-python_part1.parquet`, and `code-python_part2.parquet`. Seven original/cleaned pairs match their actual parquet rows, and replaying the exact official cleaner with native metadata reproduces all seven published cleaned outputs. Those seven pairs include evidence for accepted findings and rejected harm theories; they are not a claim that all seven findings received an original-pair replay. No broader original-source verification is implied.

**AI assistance and authorship:** GPT-6.1 Sol with `high` reasoning performed the initial analysis of all 100 complete documents in ten batches, independent finding validation, ten negative checks, adjudication and report drafting. An earlier GPT-6 Luna pass was also available. Fast mode/service tier is unverified. Revant chose the model and review strategy, requested batched analysis and independent submission review, manually read the selected 100 documents, and retained the seven suggestions. AI performed the cleaner replays and other technical checks.

The audit used the reading README, `specv1.md`, `medicine_code.md` and `decisions_code.md`. The coordinator reading README was checked again on **12 November 2026** and remained unchanged (blob `49b42fa38730116804089744844d3aca7a6bf408`). The other GitHub references were checked on 10 November; the last authenticated Axiom chat snapshot remains **10 November, 13:07 IST**.

## Findings table

The final CSV retains **seven missed findings across seven distinct documents: 7% of the 100 documents read**. They are accepted audit findings proposing disease-coverage review; acceptance does not approve automatic drops, metadata changes or repairs. Percentages describe this selected sample, not population prevalence. Documents without a finding still count as read and are not certified free of problems.

| Code | Kind | Docs affected | % of docs read |
|---|---|---:|---:|
| E4 | missed | 3 | 3% |
| E1 | missed | 2 | 2% |
| C3 | missed | 2 | 2% |
| Total, distinct documents | missed | 7 | 7% |

Offsets are **zero-based, start-inclusive/end-exclusive character ranges in the cleaned text**; multiple ranges are separated by semicolons. Whole-document E1 spans identify the affected record because the strongest generation evidence includes metadata outside the text. All CSV `quote` fields are blank to follow the Admin instruction not to commit document text and the coordinator's merged [PR #1 positions-only precedent](https://github.com/mittalutkarsh/era-v5-lab/pull/1). IDs, offsets and explanations provide the submitted evidence without corpus excerpts, personal dataset values or secrets.

### E4 — three Python license-header candidates

All three records reach pack dispatch with their actual `pack_id=code-python` and `lang_label=code`. The internal comment selector recognizes Python hash comments only when the language label is literally `python`; the official factory therefore keeps the headers under actual metadata. Copies with only that label changed were used as **diagnostics**, not as actual normalization or approved repairs. The original records and datasets retain their native metadata.

| Document ID | Cleaned offsets | Evidence and limits |
|---|---|---|
| `a0d94ae2c8f0d393` | `0-1067` | Four long comment lines contain a substantial license grant, retention condition and disclaimer. With the following modification annotation, the leading run satisfies the rule's five-line minimum and density condition when hash comments are recognized. Its verified original pair and exact replay match the published cleaned text; the license remains. The counterfactual deletion removes 1,118 characters and would also remove the useful modification annotation, so that broader removal is not approved as safe. |
| `811ce55eef413610` | `49-624` | A substantial leading license block survives beyond the short-notice exemption. The diagnostic removes 579 characters while retaining interpreter/encoding lines. The verified original pair and exact replay match the published cleaned document. |
| `11aa7a16ad5a2061` | `0-707` | The complete leading notice is longer than the exempt short attribution note. The diagnostic removes the 707-character header. Its original pair shows no cleaner edits and replays unchanged. |

These are internal coverage candidates under `DA-E4-010`, not a claim that pack dispatch skipped Python or that attribution may be discarded. Preserve licensing provenance and settle the intended short-notice treatment before any rule change.

### E1 — two generated-wrapper candidates

| Document ID | Cleaned offsets | Evidence and limits |
|---|---|---|
| `8f07828d5c3af2a6` | `0-911` | Path metadata indicates a generated schema directory and a generator; the complete body is a mechanical three-field wrapper. The official `DA-E1-008` factory keeps it because a leading-at-sign directory spelling misses the build-path expression and the remaining predicates are false. A copied-path spelling diagnostic triggers a drop. Generation is inferred from metadata plus structure, not confirmed against upstream generator history; whether a short readable wrapper should be excluded remains a policy decision. |
| `d840fa74b5200b65` | `0-2771` | Generated-library metadata and a mechanical schema object with repeated accessors, validation setters and mappings jointly support generation. The official `DA-E1-004` factory keeps it because the first 15 lines contain no generator banner and the alternative Rust-attribute predicate is absent. Original-pair evidence shows no cleaner change. Upstream generator history is unverified; some manually written wrapper content remains possible. |

These cases propose detector coverage review. They do not establish failed execution of the current predicates or authorize automatic drops.

### C3 — two inherited redaction-damage candidates

The specification defines C3 broadly and explicitly routes code cut by redaction from B4 to C3. **`DA-C3-002` is Go-only and correctly excludes both documents below.** These are disease-coverage gaps, not Go-lexer bugs or a proposal to apply the Go lexer to Python/TypeScript. A future rule would need a language-appropriate integrity policy and harm review.

| Document ID | Pack | Cleaned offsets | Evidence and limits |
|---|---|---|---|
| `df63f98851068f39` | code-python | `3693-3714;13273-13291` | The verified original places redaction markers inside two executable references: a parameter-derived reference and a callable. Surrounding declarations, assertions and adjacent calls provide concrete evidence of severed source relationships. Nineteen other quoted dummy markers do not support this C3 claim. After metadata removal the original fails Python parsing; the cleaned text parses, but neutralization does not restore those relationships. Exact B3/B4 replay proves the damage was inherited. Exact pre-redaction identifiers are unavailable. |
| `7d0432188888631b` | code-js-ts | `5564-5609` | Two original redactions cut a member-expression root and part of a property identifier. Neighboring intact configuration references support inherited source damage beyond an arbitrary undefined-name suspicion. Verified original/cleaned row hashes and exact B3/B4 replay reject the earlier B4-caused-harm theory. The pre-redaction source is unavailable; no TypeScript parser result or exact restoration is claimed. |

The independent adjudication supports these two C3 candidates while rejecting causal B4 harm. Neutral replacement tokens by themselves, dummy literals and generic unresolved names are insufficient evidence for a C3 finding. No automatic drop or source reconstruction is approved.

### Other AI hypotheses

Three uncertain hypotheses remain outside the CSV in the private AI review ledger: one SVG asset-policy question and two credential-authenticity questions. Valid SVG source may be useful; example-like signing values are not established private secrets. None is counted as a confirmed miss, and no credential was tested against an external service.

Four rejected AI suggestions also remain traceable: three alleged B4-caused harms already had the relevant mismatch or redaction damage before cleaning, and one Rust notice fits the short-notice exemption. Rejected harm theories and separately supported C3 coverage findings can concern the same document. These are AI technical adjudications; Revant's acceptance of the seven retained findings does not claim personal adjudication of all other hypotheses.

## New diseases

**No new disease category was established.** E1, E4 and C3 are existing categories with proposed coverage gaps. The unresolved SVG and credential hypotheses do not contribute to a new-category count.

## Harm

**No cleaner-caused harm was established.** Original-pair evidence rejects the three proposed B4 harm claims because the relevant damage predates the pinned cleaner. Copied-record diagnostic removals do not establish historical harm or authorize a repair.

## Open questions for the lead

1. **B4 reference versions:** the reading-branch references replace typed email placeholders, while the executed cleaner deliberately preserves them. Which version/policy governs this audit? The 18 retained email placeholders are not counted as confirmed missed production defects.
2. **E1 generated-source policy:** should short readable generated wrappers be excluded, and what corroboration beyond metadata plus repetitive structure is required? Upstream generation has not been confirmed for either E1 finding.
3. **C3 coverage:** how should language-appropriate coverage handle independently evidenced redaction-cut Python/TypeScript source while preserving intentional examples? The Go-only detector is operating within its stated scope.
4. **E4 treatment:** should internal comment selection follow the Python pack with generic `lang_label=code`, and what must be retained when a license block shares a leading run with useful annotations? The copied-label diagnostics are not approved repairs.
5. **Positions-only evidence:** if a finding needs more support, what additional positions-only evidence would help resolve it while respecting the Admin instruction?

## Appendix — all 100 documents read

These are the exact selected IDs in picker order, grouped by pack. Revant confirmed reading their full cleaned text; AI also reviewed all 100. Detailed technical evidence is retained privately outside the course repository.

### code-js-ts — 34 documents

| Sample index | Selection rank | Document ID |
|---:|---:|---|
| 1 | 1 | `afff8f976bfdef93` |
| 2 | 2 | `21ba922033930fab` |
| 3 | 3 | `c9a967ad9934da5a` |
| 4 | 4 | `af0ccb896ecd2871` |
| 5 | 5 | `965279d25e44c342` |
| 6 | 6 | `845c3c3ad6e7816e` |
| 7 | 7 | `db15a707c02f96a1` |
| 8 | 8 | `53f6bbeba2c80613` |
| 9 | 9 | `4645cf1537c80cd6` |
| 10 | 10 | `130cf898052983cc` |
| 11 | 11 | `94ac25a9dccf0f0e` |
| 12 | 12 | `017da9ee931395ad` |
| 13 | 13 | `992ffbfbe58ced39` |
| 14 | 14 | `d8893783f4f4aef9` |
| 15 | 15 | `3451e6aeaabea68f` |
| 16 | 16 | `e1235b0c35f8a562` |
| 17 | 17 | `7d0432188888631b` |
| 18 | 18 | `c4d50c90f0a1405a` |
| 19 | 19 | `9c46773d2360402b` |
| 20 | 20 | `8a62db627f12c339` |
| 21 | 21 | `1d4402e4e79b836f` |
| 22 | 22 | `f76295446028b9df` |
| 23 | 23 | `0a527feabf3ace20` |
| 24 | 24 | `cf24e08ba209caad` |
| 25 | 25 | `c3b31e8f09b0f401` |
| 26 | 26 | `e420994dc153c367` |
| 27 | 27 | `6088df606f1a9b80` |
| 28 | 28 | `25d6325089e79f63` |
| 29 | 29 | `f7e56d6a6056c091` |
| 30 | 30 | `07137474c772af79` |
| 31 | 31 | `30c7c1a70d585a6b` |
| 32 | 32 | `8f07828d5c3af2a6` |
| 33 | 33 | `8eba56463fda0499` |
| 34 | 34 | `4077a0947d822df1` |

### code-python — 33 documents

| Sample index | Selection rank | Document ID |
|---:|---:|---|
| 35 | 1 | `a90c1a6e5703dac7` |
| 36 | 2 | `bd73db82072a4e03` |
| 37 | 3 | `3ee6d6246a38dd04` |
| 38 | 4 | `171ca54722d1f215` |
| 39 | 5 | `44053e733989764b` |
| 40 | 6 | `f4859169fff1393d` |
| 41 | 7 | `4b8c6bf045b2b607` |
| 42 | 8 | `3f49ae646eb9fd82` |
| 43 | 9 | `4f32c04f929e92e2` |
| 44 | 10 | `873504a74c71d42a` |
| 45 | 11 | `ca7f9b398cafc25e` |
| 46 | 12 | `a0d94ae2c8f0d393` |
| 47 | 13 | `c6fbcfaea9ee6efd` |
| 48 | 14 | `fcde40f8e1317786` |
| 49 | 15 | `b7ff87271d63c558` |
| 50 | 16 | `45b66e179b291500` |
| 51 | 17 | `e1498fe821767de7` |
| 52 | 18 | `811ce55eef413610` |
| 53 | 19 | `c6043621d0931c0f` |
| 54 | 20 | `4d11590471a8247e` |
| 55 | 21 | `7248ae606c659606` |
| 56 | 22 | `73ca595927fa64d5` |
| 57 | 23 | `e9bab9704e0c5392` |
| 58 | 24 | `d840fa74b5200b65` |
| 59 | 25 | `d18bb294ffc0a443` |
| 60 | 26 | `9fda01ee5644b09c` |
| 61 | 27 | `f988f68ba7378872` |
| 62 | 28 | `11aa7a16ad5a2061` |
| 63 | 29 | `1abaf0fd427e2909` |
| 64 | 30 | `3296ac8988f47fff` |
| 65 | 31 | `273cc3f1debb431c` |
| 66 | 32 | `df63f98851068f39` |
| 67 | 33 | `6c59906ea6790733` |

### code-rust — 33 documents

| Sample index | Selection rank | Document ID |
|---:|---:|---|
| 68 | 1 | `4e4987237c1d373a` |
| 69 | 2 | `128fc15625fbccd3` |
| 70 | 3 | `7b5f958e10c33b85` |
| 71 | 4 | `6504450944ef79e2` |
| 72 | 5 | `134345ddd917e7cf` |
| 73 | 6 | `26f2f49e44852c5c` |
| 74 | 7 | `fdcd86ea0657c869` |
| 75 | 8 | `073400d32c7d8255` |
| 76 | 9 | `2b4cac34e8830a03` |
| 77 | 10 | `8dd7c2e44ed6347a` |
| 78 | 11 | `23132f017a48db7d` |
| 79 | 12 | `ec8a9e90b2233fe2` |
| 80 | 13 | `42b72aa11449c6ce` |
| 81 | 14 | `313176cc482b3086` |
| 82 | 15 | `d75f555193222923` |
| 83 | 16 | `f35cff6fe5f66e5b` |
| 84 | 17 | `32fd3bb24144c542` |
| 85 | 18 | `ba6deadef9f60d15` |
| 86 | 19 | `decd49e6b2b70db1` |
| 87 | 20 | `11c17c159c98f613` |
| 88 | 21 | `d585661a520924a4` |
| 89 | 22 | `071e7d9077a6584d` |
| 90 | 23 | `534cb8773d6479b6` |
| 91 | 24 | `9f0265e1738aeadb` |
| 92 | 25 | `23bc0d372c0b160d` |
| 93 | 26 | `0dceae272384074b` |
| 94 | 27 | `a551355d91e05f5a` |
| 95 | 28 | `cfc3f7641dd618b8` |
| 96 | 29 | `265ea245a3e3edd3` |
| 97 | 30 | `18cfd5db80cb1826` |
| 98 | 31 | `208e0c5830f48a5e` |
| 99 | 32 | `b5a36b02c2eb440c` |
| 100 | 33 | `f377ce768a90638a` |
