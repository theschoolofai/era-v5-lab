# Source Priority v1 : Which copy survives

Status: **DRAFT v1 — agreed by the team (Data A), pending TSAI review** (questions on PR #255).

When dedup (`dedup_design_v1.md`) finds a group of duplicates, exactly one copy survives. The rules below are applied **in order**; each rule only breaks ties left by the one above. The rule that decided is recorded in `dedup_log.jsonl` (`priority_rule`).

| Order | Rule | What it means |
|---|---|---|
| 0 | Held-out first | Dedup never removes a held-out document; a train copy of one is removed |
| 1 | Licence first | Only copies with a usable licence can win |
| 2 | Provenance | Prefer the copy with a source URL |
| 3 | Completeness | Prefer the longer (complete) copy over a truncated one |
| 4 | Fixed pack order | Deterministic final tie-break |

## 0. Held-out first

The sample splits every pack into `train/` and `heldout/`. G3 (tokenizer) uses the held-out documents to choose and check the tokenizer, not to train it: the text mix is chosen on the even-numbered held-out documents and confirmed on the odd ones, and the results are reported as "sample held-out" (`teams/03-tokenizer/COMPARE.md`). G3 already drops held-out documents that overlap the training corpus (`teams/03-tokenizer/train/v2_spec.md`).

So **dedup never removes a held-out document**. Removing one would shrink the held-out set and change G3's results.

| Pair | What happens |
|---|---|
| train ↔ train | Normal dedup: rules 1–4 choose the survivor |
| train ↔ held-out | The held-out copy survives and the train copy is removed; this also removes the leak |
| held-out ↔ held-out | Nothing is removed; the pair is reported to G3 |

In a group with held-out copies, every held-out copy survives and every train copy is removed. Rule 0 overrides rule 1: a held-out document is kept even if its pack's licence would rule it out (it should then be reported, not deduplicated). *(Asked TSAI on PR #255.)*

## 1. Licence first

- **Usable:** permissive licences (e.g. MIT, Apache-2.0, BSD, CC-BY, CC0/public domain) and CC-BY-SA.
- **Not usable:** any NC (non-commercial), any ND (no derivatives), and unstated licences.
- A copy with an unusable licence **never wins**, even if it is better on every other rule.
- If **no** copy in the group has a usable licence, the whole group is removed (none of it should be in the data anyway).
- **Applied per pack.** The sample has no per-document licence column (its columns are `doc_id`, `text`, `url`, `lang_label`, `pack_id`), so each pack's licence comes from the licence table and is the same for every document in the pack. `dedup.json` holds the pack-to-licence map.

Source: Week 2 licence rule; licence classification follows G10's table, `teams/10-post-training/licences/licence_table.md`.

## 2. Provenance

Prefer the copy with a **non-empty `url`**. Dataset and licence are known for every document from its pack (rule 1), so in the sample the source URL is the only part of provenance that differs between copies.

The provenance record of the survivor (source URL, and its pack's dataset and licence) is kept with the surviving document. The removed copies' IDs are kept in the dedup log, so their provenance remains traceable.

## 3. Completeness

Prefer the copy with the **longer normalised text**, so a complete copy wins over a truncated one.

**"Fewer fixes" is dropped for v1.** No per-document fix record exists:

| Where | Per document | In total |
|---|---|---|
| `clean.py` | only the action (`keep`/`fix`/`drop`) and the new text | nothing |
| `run_clean.py` summary | dropped and error `doc_id`s | counts of keep, fix, drop |
| `run_tokenizer_sample.py` | nothing | per-rule keep/fix/drop counts per part (`rule_counts.csv`) |

**v2 candidate: measure how much cleaning changed each copy.** Raw text (sample input) and cleaned text (job output) share a `doc_id`, so for each duplicate pair dedup can compute the change, e.g. `1 - difflib ratio` or the character difference, and keep the copy that changed least. This needs no code change to the cleaning tools, and it is a better signal than a rule count: one rule may touch one character or rewrite half a document. Cost: reading both texts, only for the pairs dedup finds.

(Alternative considered: have the sample job's per-rule wrapper write a fix count or the rule IDs into each output row. It is a change to Vijay's tool and the job evidence would need rerunning, so it is not planned for v1.)

## 4. Fixed pack order

Final tie-break so that every run gives the same result. Pack order: **to be agreed** (proposal: the order in which `clean.py` lists the 13 packs). Within one pack, the lowest `(split, part, doc_id)` wins.

## Example

Three copies of the same article:

| Copy | Pack, split | Pack licence | `url` | Truncated | Result |
|---|---|---|---|---|---|
| A | science, train | CC-BY-NC | yes | no | out at rule 1 (NC) |
| B | science, train | CC-BY | empty | no | out at rule 2 |
| C | math, train | CC-BY-SA | yes | no | **survives** (decided by rule 2) |

If B were in `heldout/`, B would survive at rule 0 and A and C would be removed.

## Open questions for the team

- Agree the pack order for rule 4.
- Confirm rule 0 (held-out first) with TSAI and G3.
- Fill in the pack-to-licence map from G10's licence table.
