> Copied from [Pritish52718/era-v5-lab: teams/02-data-b/indic_rules/medicine_indic.md](https://github.com/Pritish52718/era-v5-lab/blob/0104f40d7e8d44db808973042cd735f7deef882d/teams/02-data-b/indic_rules/medicine_indic.md) at commit `0104f40d7e8d44db808973042cd735f7deef882d`.

# medicine_indic: compiled Indic medicines (Data B)

<!-- INDIC SIBLING POLICY -->
## Data A sibling-scope policy

The copied contributor blocks below retain their original `ORIGIN`, algorithms and attribution. The following local policy authorizes reviewing selected candidates for same-language sibling packs. It does not automatically broaden their executable guards. `integrate_indic.py` validates each receiving scope, and writes accepted `ORIGIN`/`SPEC_PACKS` scopes into the consolidated `specv1.md`, retaining the original as `SOURCE_ORIGIN`. The builder then generates `clean.py`; do not edit its scope table manually.

Native selections take priority. Borrowed candidates fill missing diseases only and must pass the receiving pack's nonempty gold, ordinary-prose/joiner probes, full-pack runtime/idempotence and combined-pipeline checks. Empty or missing gold remains NOT TESTABLE; a language match is not a gold pass. Malayalam and Odia cannot borrow without a same-language donor. Accepted scopes and rejected attempts are recorded in `results/cleaner/indic_sibling_scopes.json`. These remain CANDIDATE selections, not independent approval or proof of recall.

```json
{
  "enabled": true,
  "same_language_only": true,
  "donors": "selected native candidates only",
  "native_rules_take_priority": true,
  "fill_missing_diseases_only": true,
  "require_receiving_gold": true,
  "target_pack_ids": [
    "ind-bn-fw2",
    "ind-bn-sangraha-v",
    "ind-gu-fw2",
    "ind-hi-fw2",
    "ind-hi-hplt",
    "ind-hi-indiccorp",
    "ind-hi-sangraha-s",
    "ind-hi-sangraha-v",
    "ind-kn-fw2",
    "ind-kn-sangraha-s",
    "ind-kn-sangraha-v",
    "ind-ml-fw2",
    "ind-mr-fw2",
    "ind-mr-sangraha-v",
    "ind-or-fw2",
    "ind-sa-fw2",
    "ind-ta-fw2",
    "ind-ta-sangraha-s",
    "ind-ta-sangraha-v",
    "ind-te-fw2",
    "ind-te-sangraha-s",
    "ind-te-sangraha-v"
  ]
}
```
<!-- END INDIC SIBLING POLICY -->

176 rules from 13 packs. Only rules whose author reports a pass on **their own pack's gold set at today's size** (`teams/02-data-b/gold/gold_coverage.csv` on main, 2 Nov) are here. Every other medicine is in `rules_status.md`, with the reason it is not here yet.

Rule form: Data A's (`teams/01-data-a/spec_v1/sheets/medicine_english.md`, PR #194): `RULE_ID`, `CODE`, `ACTION`, `STAGE`, `STATUS`, `LANGS`, `ORIGIN`, `SOURCE`, `AUTHOR`; `medicine(doc) -> (action, text)`, `doc = {doc_id, text, url, lang_label, pack_id}`.

**Scope is the pack, not the language.** Each rule was tested on one pack's gold set only (TSAI: report per pack, never pooled), so `medicine(doc)` runs only when `doc["pack_id"]` is in `ORIGIN`; on any other document it returns `("keep", text)`. `LANGS` names the language for Data A's tables; it is not used as the guard.

Run order is section order, by Data A's stages: 10 characters (A, G1, G2, G4), 20 markup (B1 to B3), 30 drops (every rule whose action is drop), 35 strips (C, D, G3, H fixes), 40 data safety (B4, F1, F2).

Each author's code is copied unchanged: every python block of their section, in order, exactly as `harm_test_indic.py` runs it. What is added is marked `# added by Data B`: `import re` where the author relied on the tool providing it, `_std` (copied from Data A), and the `medicine(doc)` wrapper with the pack guard.

Harm results are **as each author reports them** in their `medicine.md`. Data B has not re-run them: the packs are not in the repository. IDs are provisional.

Tests: `test_indic_rules.py` runs 7 checks on every rule with made-up text (ZWJ and ZWNJ counts, NFC, nukta, second run, other packs untouched, result form, loads). Result and limits: `README.md`.

Two authors report their result on their language's combined gold set: PR #3 (`ind-te-fw2`, Telugu, 46 documents) and PR #63 (`ind-kn-fw2`, Kannada, 175 documents). Each combined set holds all of today's gold documents of the author's own pack (Kannada checked by doc_id; Telugu by the gold file's history on main, unchanged since 29 Oct), so 0 changed and 0 dropped on the combined set means 0 and 0 on their own pack.

**A pass on a small gold set is weak.** Changing 0 of n gold documents shows only that the rule harms fewer than about 3 in n clean documents (the rule of three, as in Data A's README). The column "a pass shows harm under" gives 3/n for each rule's pack: 0 of 5 (Telugu sangraha-s) shows under 60%, 0 of 18 (Telugu fw2) under 17%, 0 of 238 (Bengali fw2) under 1.3%. To show under 1%, a pack needs more than 300 gold documents; none has that yet. Telugu's three packs hold 50 gold documents in all (18, 5 and 27).

**Known conflicts** (two authors wrote a rule for the same disease on the same pack, so the rules overlap; Data A runs both in the order below, or picks one):

- ind-bn-fw2 A3: `DB-A3-001`, `DB-A3-003`
- ind-bn-fw2 A5: `DB-A5-001`, `DB-A5-002`
- ind-bn-fw2 A6: `DB-A6-001`, `DB-A6-002`
- ind-bn-fw2 C1: `DB-C1-001`, `DB-C1-002`
- ind-bn-fw2 C2: `DB-C2-001`, `DB-C2-002`
- ind-bn-fw2 C3: `DB-C3-001`, `DB-C3-005`
- ind-bn-fw2 C5: `DB-C5-007`, `DB-C5-008`
- ind-bn-fw2 D3: `DB-D3-001`, `DB-D3-002`
- ind-bn-fw2 D4: `DB-D4-001`, `DB-D4-002`
- ind-bn-fw2 F3: `DB-F3-001`, `DB-F3-002`
- ind-bn-fw2 G2: `DB-G2-001`, `DB-G2-002`
- ind-gu-fw2 A5: `DB-A5-003`, `DB-A5-004`
- ind-gu-fw2 A6: `DB-A6-003`, `DB-A6-015`
- ind-gu-fw2 C1: `DB-C1-003`, `DB-C1-004`
- ind-gu-fw2 C5: `DB-C5-009`, `DB-C5-010`
- ind-gu-fw2 D3: `DB-D3-003`, `DB-D3-004`
- ind-gu-fw2 D4: `DB-D4-003`, `DB-D4-004`
- ind-gu-fw2 F1: `DB-F1-001`, `DB-F1-002`
- ind-gu-fw2 G1: `DB-G1-002`, `DB-G1-003`
- ind-hi-hplt A6: `DB-A6-004`, `DB-A6-005`
- ind-hi-hplt C1: `DB-C1-006`, `DB-C1-007`
- ind-hi-hplt C2: `DB-C2-004`, `DB-C2-005`
- ind-hi-hplt C3: `DB-C3-002`, `DB-C3-007`
- ind-hi-hplt C4: `DB-C4-003`, `DB-C4-004`
- ind-hi-hplt C5: `DB-C5-001`, `DB-C5-002`
- ind-hi-hplt D3: `DB-D3-006`, `DB-D3-007`
- ind-hi-hplt D4: `DB-D4-005`, `DB-D4-006`
- ind-hi-hplt F1: `DB-F1-003`, `DB-F1-004`
- ind-kn-fw2 C1: `DB-C1-008`, `DB-C1-009`
- ind-kn-fw2 C2: `DB-C2-006`, `DB-C2-007`
- ind-kn-fw2 C5: `DB-C5-011`, `DB-C5-012`
- ind-sa-fw2 A5: `DB-A5-007`, `DB-A5-008`
- ind-sa-fw2 A6: `DB-A6-010`, `DB-A6-011`
- ind-sa-fw2 C1: `DB-C1-013`, `DB-C1-014`
- ind-sa-fw2 C3: `DB-C3-004`, `DB-C3-011`
- ind-sa-fw2 C4: `DB-C4-010`, `DB-C4-011`
- ind-sa-fw2 C5: `DB-C5-014`, `DB-C5-015`
- ind-sa-fw2 D3: `DB-D3-012`, `DB-D3-013`
- ind-sa-fw2 D4: `DB-D4-009`, `DB-D4-010`
- ind-sa-fw2 F1: `DB-F1-008`, `DB-F1-009`
- ind-sa-fw2 F2: `DB-F2-001`, `DB-F2-002`
- ind-sa-fw2 G1: `DB-G1-007`, `DB-G1-008`
- ind-sa-fw2 H3: `DB-H3-001`, `DB-H3-002`

| # | ID | disease | action | stage | pack | gold docs | a pass shows harm under | author | PR |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `DB-A3-001` | A3 Mojibake | fix | 10 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 2 | `DB-A3-002` | A3 Mojibake | fix | 10 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 3 | `DB-A5-001` | A5 Wrong normal form | fix | 10 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 4 | `DB-A5-002` | A5 Wrong normal form | fix | 10 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 5 | `DB-A5-003` | A5 Wrong normal form | fix | 10 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 6 | `DB-A5-004` | A5 Wrong normal form | fix | 10 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 7 | `DB-A5-005` | A5 Wrong normal form | fix | 10 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 8 | `DB-A5-006` | A5 Wrong normal form | fix | 10 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 9 | `DB-A5-007` | A5 Wrong normal form | fix | 10 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 10 | `DB-A5-008` | A5 Wrong normal form | fix | 10 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 11 | `DB-A6-001` | A6 Wrong or mixed script | fix | 10 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 12 | `DB-A6-002` | A6 Wrong or mixed script | fix | 10 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 13 | `DB-A6-003` | A6 Wrong or mixed script | fix | 10 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 14 | `DB-A6-004` | A6 Wrong or mixed script | fix | 10 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 15 | `DB-A6-005` | A6 Wrong or mixed script | fix | 10 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 16 | `DB-A6-006` | A6 Wrong or mixed script | fix | 10 | ind-kn-sangraha-s | 27 | 11.1% | millermuttu | #104 |
| 17 | `DB-A6-007` | A6 Wrong or mixed script | fix | 10 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 18 | `DB-A6-008` | A6 Wrong or mixed script | fix | 10 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 19 | `DB-A6-009` | A6 Wrong or mixed script | fix | 10 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 20 | `DB-A6-010` | A6 Wrong or mixed script | fix | 10 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 21 | `DB-A6-011` | A6 Wrong or mixed script | fix | 10 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 22 | `DB-A6-012` | A6 Wrong or mixed script | fix | 10 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 23 | `DB-A6-013` | A6 Wrong or mixed script | fix | 10 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 24 | `DB-A6-014` | A6 Wrong or mixed script | fix | 10 | ind-te-sangraha-s | 5 | 60.0% | shankarpandala | #92 |
| 25 | `DB-G1-001` | G1 Cut at the vowel sign | fix | 10 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 26 | `DB-G1-002` | G1 Cut at the vowel sign | fix | 10 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 27 | `DB-G1-003` | G1 Cut at the vowel sign | fix | 10 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 28 | `DB-G1-004` | G1 Cut at the vowel sign | fix | 10 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 29 | `DB-G1-005` | G1 Cut at the vowel sign | fix | 10 | ind-kn-fw2 | 45 | 6.7% | keshavamurali | #47 |
| 30 | `DB-G1-006` | G1 Cut at the vowel sign | fix | 10 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 31 | `DB-G1-007` | G1 Cut at the vowel sign | fix | 10 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 32 | `DB-G1-008` | G1 Cut at the vowel sign | fix | 10 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 33 | `DB-G1-009` | G1 Cut at the vowel sign | fix | 10 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 34 | `DB-G1-010` | G1 Cut at the vowel sign | fix | 10 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 35 | `DB-G2-001` | G2 Lost ZWJ or ZWNJ | fix | 10 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 36 | `DB-G2-002` | G2 Lost ZWJ or ZWNJ | fix | 10 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 37 | `DB-G2-003` | G2 Lost ZWJ or ZWNJ | keep | 10 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 38 | `DB-G4-001` | G4 Over-normalised | fix | 10 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 39 | `DB-G4-002` | G4 Over-normalised | fix | 10 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 40 | `DB-G4-003` | G4 Over-normalised | fix | 10 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 41 | `DB-G4-004` | G4 Over-normalised | fix | 10 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 42 | `DB-B2-001` | B2 HTML or XML tags | fix | 20 | ind-hi-fw2 | 234 | 1.3% | raj-harit-v2 | #8 |
| 43 | `DB-B2-002` | B2 HTML or XML tags | fix | 20 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 44 | `DB-B2-003` | B2 HTML or XML tags | fix | 20 | ind-kn-sangraha-s | 27 | 11.1% | millermuttu | #104 |
| 45 | `DB-B2-004` | B2 HTML or XML tags | fix | 20 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 46 | `DB-B2-005` | B2 HTML or XML tags | fix | 20 | ind-te-sangraha-s | 5 | 60.0% | shankarpandala | #92 |
| 47 | `DB-B3-001` | B3 Ghost chat markers | fix | 20 | ind-kn-sangraha-s | 27 | 11.1% | millermuttu | #104 |
| 48 | `DB-A3-003` | A3 Mojibake | drop | 30 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 49 | `DB-A3-004` | A3 Mojibake | drop | 30 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 50 | `DB-A4-001` | A4 Replacement characters | drop | 30 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 51 | `DB-A6-015` | A6 Wrong or mixed script | drop | 30 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 52 | `DB-C3-001` | C3 Truncated document | drop | 30 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 53 | `DB-C3-002` | C3 Truncated document | drop | 30 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 54 | `DB-C3-003` | C3 Truncated document | drop | 30 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 55 | `DB-C3-004` | C3 Truncated document | drop | 30 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 56 | `DB-C4-001` | C4 Two documents joined | drop | 30 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 57 | `DB-C4-002` | C4 Two documents joined | drop | 30 | ind-hi-fw2 | 234 | 1.3% | raj-harit-v2 | #8 |
| 58 | `DB-C4-003` | C4 Two documents joined | drop | 30 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 59 | `DB-C4-004` | C4 Two documents joined | drop | 30 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 60 | `DB-C4-005` | C4 Two documents joined | drop | 30 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 61 | `DB-C4-006` | C4 Two documents joined | drop | 30 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 62 | `DB-C5-001` | C5 Lists of keywords or links | drop | 30 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 63 | `DB-C5-002` | C5 Lists of keywords or links | drop | 30 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 64 | `DB-C5-003` | C5 Lists of keywords or links | drop | 30 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 65 | `DB-C5-004` | C5 Lists of keywords or links | drop | 30 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 66 | `DB-C5-005` | C5 Lists of keywords or links | drop | 30 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 67 | `DB-C5-006` | C5 Lists of keywords or links | drop | 30 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 68 | `DB-D4-001` | D4 Bad machine translation | drop | 30 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 69 | `DB-D4-002` | D4 Bad machine translation | drop | 30 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 70 | `DB-D4-003` | D4 Bad machine translation | drop | 30 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 71 | `DB-D4-004` | D4 Bad machine translation | drop | 30 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 72 | `DB-D4-005` | D4 Bad machine translation | drop | 30 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 73 | `DB-D4-006` | D4 Bad machine translation | drop | 30 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 74 | `DB-D4-007` | D4 Bad machine translation | drop | 30 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 75 | `DB-D4-008` | D4 Bad machine translation | drop | 30 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 76 | `DB-D4-009` | D4 Bad machine translation | drop | 30 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 77 | `DB-D4-010` | D4 Bad machine translation | drop | 30 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 78 | `DB-D4-011` | D4 Bad machine translation | drop | 30 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 79 | `DB-D4-012` | D4 Bad machine translation | drop | 30 | ind-te-sangraha-s | 5 | 60.0% | shankarpandala | #92 |
| 80 | `DB-D5-001` | D5 Translationese | drop | 30 | ind-te-sangraha-s | 5 | 60.0% | shankarpandala | #92 |
| 81 | `DB-F2-001` | F2 Benchmark leak | drop | 30 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 82 | `DB-F3-001` | F3 Harmful content | drop | 30 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 83 | `DB-F3-002` | F3 Harmful content | drop | 30 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 84 | `DB-F3-003` | F3 Harmful content | drop | 30 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 85 | `DB-G1-011` | G1 Cut at the vowel sign | drop | 30 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 86 | `DB-G3-001` | G3 Indic dropped by an English rule | drop | 30 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 87 | `DB-C1-001` | C1 Boilerplate | fix | 35 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 88 | `DB-C1-002` | C1 Boilerplate | fix | 35 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 89 | `DB-C1-003` | C1 Boilerplate | fix | 35 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 90 | `DB-C1-004` | C1 Boilerplate | fix | 35 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 91 | `DB-C1-005` | C1 Boilerplate | fix | 35 | ind-hi-fw2 | 234 | 1.3% | raj-harit-v2 | #8 |
| 92 | `DB-C1-006` | C1 Boilerplate | fix | 35 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 93 | `DB-C1-007` | C1 Boilerplate | fix | 35 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 94 | `DB-C1-008` | C1 Boilerplate | fix | 35 | ind-kn-fw2 | 45 | 6.7% | LokeshJatangi | #63 |
| 95 | `DB-C1-009` | C1 Boilerplate | fix | 35 | ind-kn-fw2 | 45 | 6.7% | keshavamurali | #47 |
| 96 | `DB-C1-010` | C1 Boilerplate | fix | 35 | ind-kn-sangraha-s | 27 | 11.1% | millermuttu | #104 |
| 97 | `DB-C1-011` | C1 Boilerplate | fix | 35 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 98 | `DB-C1-012` | C1 Boilerplate | fix | 35 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 99 | `DB-C1-013` | C1 Boilerplate | fix | 35 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 100 | `DB-C1-014` | C1 Boilerplate | fix | 35 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 101 | `DB-C1-015` | C1 Boilerplate | fix | 35 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 102 | `DB-C1-016` | C1 Boilerplate | fix | 35 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 103 | `DB-C2-001` | C2 Repeated lines | fix | 35 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 104 | `DB-C2-002` | C2 Repeated lines | fix | 35 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 105 | `DB-C2-003` | C2 Repeated lines | fix | 35 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 106 | `DB-C2-004` | C2 Repeated lines | fix | 35 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 107 | `DB-C2-005` | C2 Repeated lines | fix | 35 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 108 | `DB-C2-006` | C2 Repeated lines | fix | 35 | ind-kn-fw2 | 45 | 6.7% | LokeshJatangi | #63 |
| 109 | `DB-C2-007` | C2 Repeated lines | fix | 35 | ind-kn-fw2 | 45 | 6.7% | keshavamurali | #47 |
| 110 | `DB-C2-008` | C2 Repeated lines | fix | 35 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 111 | `DB-C2-009` | C2 Repeated lines | fix | 35 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 112 | `DB-C2-010` | C2 Repeated lines | fix | 35 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 113 | `DB-C2-011` | C2 Repeated lines | fix | 35 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 114 | `DB-C2-012` | C2 Repeated lines | fix | 35 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 115 | `DB-C2-013` | C2 Repeated lines | fix | 35 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 116 | `DB-C3-005` | C3 Truncated document | fix | 35 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 117 | `DB-C3-006` | C3 Truncated document | fix | 35 | ind-hi-fw2 | 234 | 1.3% | raj-harit-v2 | #8 |
| 118 | `DB-C3-007` | C3 Truncated document | fix | 35 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 119 | `DB-C3-008` | C3 Truncated document | fix | 35 | ind-kn-sangraha-s | 27 | 11.1% | millermuttu | #104 |
| 120 | `DB-C3-009` | C3 Truncated document | fix | 35 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 121 | `DB-C3-010` | C3 Truncated document | fix+drop | 35 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 122 | `DB-C3-011` | C3 Truncated document | fix | 35 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 123 | `DB-C3-012` | C3 Truncated document | fix | 35 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 124 | `DB-C3-013` | C3 Truncated document | fix | 35 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 125 | `DB-C3-014` | C3 Truncated document | fix | 35 | ind-te-sangraha-s | 5 | 60.0% | shankarpandala | #92 |
| 126 | `DB-C4-007` | C4 Two documents joined | fix | 35 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 127 | `DB-C4-008` | C4 Two documents joined | fix | 35 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 128 | `DB-C4-009` | C4 Two documents joined | fix+drop | 35 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 129 | `DB-C4-010` | C4 Two documents joined | fix | 35 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 130 | `DB-C4-011` | C4 Two documents joined | keep | 35 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 131 | `DB-C5-007` | C5 Lists of keywords or links | fix | 35 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 132 | `DB-C5-008` | C5 Lists of keywords or links | fix | 35 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 133 | `DB-C5-009` | C5 Lists of keywords or links | fix | 35 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 134 | `DB-C5-010` | C5 Lists of keywords or links | fix | 35 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 135 | `DB-C5-011` | C5 Lists of keywords or links | fix | 35 | ind-kn-fw2 | 45 | 6.7% | LokeshJatangi | #63 |
| 136 | `DB-C5-012` | C5 Lists of keywords or links | fix+drop | 35 | ind-kn-fw2 | 45 | 6.7% | keshavamurali | #47 |
| 137 | `DB-C5-013` | C5 Lists of keywords or links | fix | 35 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 138 | `DB-C5-014` | C5 Lists of keywords or links | fix | 35 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 139 | `DB-C5-015` | C5 Lists of keywords or links | fix | 35 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 140 | `DB-D2-001` | D2 Romanised Indic | fix | 35 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 141 | `DB-D2-002` | D2 Romanised Indic | fix | 35 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 142 | `DB-D3-001` | D3 Mixed language | keep | 35 | ind-bn-fw2 | 238 | 1.3% | AditeyaAItronics | #64 |
| 143 | `DB-D3-002` | D3 Mixed language | keep | 35 | ind-bn-fw2 | 238 | 1.3% | sohamniyogi | #138 |
| 144 | `DB-D3-003` | D3 Mixed language | keep | 35 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 145 | `DB-D3-004` | D3 Mixed language | fix | 35 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 146 | `DB-D3-005` | D3 Mixed language | fix | 35 | ind-hi-fw2 | 234 | 1.3% | raj-harit-v2 | #8 |
| 147 | `DB-D3-006` | D3 Mixed language | keep | 35 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 148 | `DB-D3-007` | D3 Mixed language | keep | 35 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 149 | `DB-D3-008` | D3 Mixed language | keep | 35 | ind-kn-sangraha-s | 27 | 11.1% | millermuttu | #104 |
| 150 | `DB-D3-009` | D3 Mixed language | keep | 35 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 151 | `DB-D3-010` | D3 Mixed language | fix | 35 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 152 | `DB-D3-011` | D3 Mixed language | keep | 35 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 153 | `DB-D3-012` | D3 Mixed language | fix | 35 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 154 | `DB-D3-013` | D3 Mixed language | keep | 35 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 155 | `DB-D3-014` | D3 Mixed language | keep | 35 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 156 | `DB-D5-002` | D5 Translationese | keep | 35 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 157 | `DB-G3-002` | G3 Indic dropped by an English rule | fix | 35 | ind-te-sangraha-s | 5 | 60.0% | shankarpandala | #92 |
| 158 | `DB-H3-001` | H3 The same content in another source or language | fix | 35 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 159 | `DB-H3-002` | H3 The same content in another source or language | keep | 35 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 160 | `DB-B4-001` | B4 Template and code junk in prose | fix | 40 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 161 | `DB-B4-002` | B4 Template and code junk in prose | fix | 40 | ind-kn-sangraha-v | 103 | 2.9% | pyru | #25 |
| 162 | `DB-B4-003` | B4 Template and code junk in prose | fix | 40 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 163 | `DB-B4-004` | B4 Template and code junk in prose | fix | 40 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 164 | `DB-B4-005` | B4 Template and code junk in prose | fix | 40 | ind-ta-sangraha-v | 41 | 7.3% | abinesh1 | #101 |
| 165 | `DB-B4-006` | B4 Template and code junk in prose | fix | 40 | ind-te-sangraha-s | 5 | 60.0% | shankarpandala | #92 |
| 166 | `DB-F1-001` | F1 Personal data | fix | 40 | ind-gu-fw2 | 19 | 15.8% | Nisarg189 | #18 |
| 167 | `DB-F1-002` | F1 Personal data | fix | 40 | ind-gu-fw2 | 19 | 15.8% | vedang-patel-10 | #91 |
| 168 | `DB-F1-003` | F1 Personal data | fix | 40 | ind-hi-hplt | 67 | 4.5% | narasimhatejav | #170 |
| 169 | `DB-F1-004` | F1 Personal data | fix | 40 | ind-hi-hplt | 67 | 4.5% | therahulbhati | #24 |
| 170 | `DB-F1-005` | F1 Personal data | fix | 40 | ind-kn-fw2 | 45 | 6.7% | LokeshJatangi | #63 |
| 171 | `DB-F1-006` | F1 Personal data | fix | 40 | ind-mr-fw2 | 140 | 2.1% | thinktinkergreen | #50 |
| 172 | `DB-F1-007` | F1 Personal data | fix+drop | 40 | ind-mr-sangraha-v | 88 | 3.4% | patilvijay23 | #19 |
| 173 | `DB-F1-008` | F1 Personal data | fix | 40 | ind-sa-fw2 | 68 | 4.4% | dattatreyamanjunath | #45 |
| 174 | `DB-F1-009` | F1 Personal data | fix | 40 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |
| 175 | `DB-F1-010` | F1 Personal data | fix | 40 | ind-te-fw2 | 18 | 16.7% | sandeepkunkunuru | #3 |
| 176 | `DB-F2-002` | F2 Benchmark leak | keep | 40 | ind-sa-fw2 | 68 | 4.4% | swatibansal | #80 |

## 1. `DB-A3-001` · A3 Mojibake · fix · stage 10

1. **Disease:** A3 Mojibake. Pack `ind-bn-fw2`. Source: section A3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python
RULE_ID = "DB-A3-001"
CODE = "A3"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_A3_MAP = {"æ": "ু", "ø": "্ল", "¦": "্ব", "Ñ": "–", "Í": "-"}


def medicine_a3(text):
    """Bijoy leftovers next to a Bengali letter -> the intended character."""
    return re.sub("(?<=[ঀ-৿])[æø¦ÑÍ]|[æø¦ÑÍ](?=[ঀ-৿])", lambda m: _A3_MAP[m.group()], text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 2. `DB-A3-002` · A3 Mojibake · fix · stage 10

1. **Disease:** A3 Mojibake. Pack `ind-gu-fw2`. Source: section A3 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python
RULE_ID = "DB-A3-002"
CODE = "A3"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

A3_PAIRS = [("¬©", "©"), ("â€™", "’"), ("â€œ", "“"), ("â€", "”")]
A3_LOWQ_RUP = re.compile(rf"(?<=[{GU}])\u201Aપ")
A3_LOWQ = re.compile(rf"(?<=[{GU}])\u201A")

def m10_a3(text, url=None):
    new = text
    for a, b in A3_PAIRS:
        new = new.replace(a, b)
    new = A3_LOWQ_RUP.sub("રૂપ", new)
    return _fix(text, A3_LOWQ.sub("રુ", new))

def medicine_a3(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m10_a3(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 3. `DB-A5-001` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-bn-fw2`. Source: section A5 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-001"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

# ত + virama (ত্) at the end of a word, or before ক স প, is a khanda-ta written the old way.
# A ZWJ/ZWNJ after the virama is a deliberate choice and is left alone.
_T = re.compile('ত্(?=[কসপ]|(?![\u0980-\u09ff\u200c\u200d]))')

def medicine_a5(text):
    """Replace ত্ with ৎ (U+09CE) at a word end and before ক স প."""
    return _T.sub('ৎ', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 4. `DB-A5-002` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-bn-fw2`. Source: section A5 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-002"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_a5(text):
    """া + ে -> ো, ৈ + া -> ৌ (two-part vowels stored in reverse order)."""
    return text.replace("াে", "ো").replace("ৈা", "ৌ")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 5. `DB-A5-003` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-gu-fw2`. Source: section A5 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-003"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

A5_PAIRS = [("ાે", "ો"), ("ાૈ", "ૌ"), ("અા", "આ"), ("અો", "ઓ"), ("અે", "એ"), ("અૈ", "ઐ"),
            ("ૈા", "ૌ"), ("્ર્વ", "્વ")]
A5_RU = re.compile(r"(?<!્)રૃ")
A5_DIGIT = re.compile(rf"(?<![{GU}])[{GU_DIGIT}રપ]*[{GU_DIGIT}][{GU_DIGIT}રપ]*(?![{GU}])")

def m5_a5(text, url=None):
    new = text
    for a, b in A5_PAIRS:
        new = new.replace(a, b)
    new = A5_RU.sub("રૂ", new)
    new = A5_DIGIT.sub(lambda m: m.group(0).replace("ર", "૨").replace("પ", "૫"), new)
    return _fix(text, new)

def medicine_a5(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m5_a5(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 6. `DB-A5-004` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-gu-fw2`. Source: section A5 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-A5-004"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

SIGN = "\u0abe-\u0ac5\u0ac7-\u0ac9\u0acb\u0acc"      # Gujarati vowel signs

def medicine(text):
    t = text.replace("રૂા", "\0")                      # rupee shorthand is correct, protect it
    t = t.replace("\u0a85\u0ac7", "\u0a8f")            # અ + ે  ->  એ
    t = re.sub(f"([{SIGN}])\\1+", r"\1", t)           # the same sign twice
    t = (t.replace("\u0abe\u0ac7", "\u0acb")          # ાે -> ો
          .replace("\u0abe\u0ac8", "\u0acc")          # ાૈ -> ૌ
          .replace("\u0ac8\u0abe", "\u0acc"))         # ૈા -> ૌ
    t = re.sub(f"([\u0a85-\u0a94])[{SIGN}]", r"\1", t)  # sign after an independent vowel
    t = re.sub(f"([{SIGN}])[{SIGN}]", r"\1", t)         # any other two signs: keep the first
    t = re.sub(f"([{SIGN}\u0a82])\u0abc", r"\1", t)    # nukta after a sign
    return t.replace("\0", "રૂા")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 26 of 3...
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 7. `DB-A5-005` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-hi-hplt`. Source: section A5 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-005"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_C = "[\u0915-\u0939\u0958-\u095F]"  # consonant


def medicine_a5(text):
    t = text
    # vowel sign E/AI typed before virama + RA: कांगे्रस -> कांग्रेस
    t = re.sub("([\u0947\u0948])\u094D\u0930", "\u094D\u0930\\1", t)
    # stray virama after vowel sign E/AI before another consonant: ओल्डे्नबर्ग -> ओल्डेनबर्ग
    t = re.sub("([\u0947\u0948])\u094D(?=" + _C + ")", "\\1", t)
    # two vowel signs for one: AA+CANDRA E -> CANDRA O, AA+E or E+AA -> O, AA+AI -> AU, E+AI -> AI
    for bad, good in (("\u093E\u0945", "\u0949"), ("\u093E\u0947", "\u094B"), ("\u0947\u093E", "\u094B"),
                      ("\u093E\u0948", "\u094C"), ("\u0947\u0948", "\u0948"), ("\u093C\u093C", "\u093C")):
        t = t.replace(bad, good)
    # the same vowel sign twice: स्थाानों -> स्थानों
    t = re.sub("([\u093E-\u094C])\\1", "\\1", t)
    # nukta moved to the next letter: पकडक़र -> पकड़कर, पीढिय़ों -> पीढ़ियों, लडऩे -> लड़ने
    t = re.sub("([\u0921\u0922])([\u093F\u0940\u0947\u0948]?)([\u0915\u092F\u0928])\u093C", "\\1\u093C\\2\\3", t)
    t = re.sub("([\u0921\u0922])([\u093E-\u094C]?)\u0929", "\\1\u093C\\2\u0928", t)
    # reph written after the conjunct: सामथ्र्य -> सामर्थ्य, पाट्र्स -> पार्ट्स
    t = re.sub("(" + _C + ")\u094D\u0930\u094D(" + _C + ")", "\u0930\u094D\\1\u094D\\2", t)
    # RA + virama + letter I for letter II: हुर्इं -> हुईं
    t = t.replace("\u0930\u094D\u0907", "\u0908")
    # DHA + virama + DA for द्ध: बौध्दिक -> बौद्धिक
    t = t.replace("\u0927\u094D\u0926", "\u0926\u094D\u0927")
    # Marathi eyelash RA for RA: औऱ -> और
    t = re.sub("\u0931(?!\u094D)", "\u0930", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. ZWJ/ZWNJ audit and normal-form audit: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 8. `DB-A5-006` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-mr-sangraha-v`. Source: section A5 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_a5(text)`.

```python
RULE_ID = "DB-A5-006"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata

def cure_a5(text):
    return unicodedata.normalize("NFC", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). This demonstrates no measured gol...
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 9. `DB-A5-007` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-sa-fw2`. Source: section A5 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-007"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_FULL = {"ा": "आ", "ि": "इ", "ी": "ई", "ु": "उ", "ू": "ऊ", "ृ": "ऋ", "े": "ए", "ै": "ऐ", "ो": "ओ", "ौ": "औ"}

def medicine_a5(text):
    t = re.sub("अ([ािीुूृेैोौ])", lambda m: _FULL[m.group(1)], text)
    t = re.sub("([ा-्ॢॣ])\\1+", r"\1", t)
    if "॥" in t:
        t = re.sub("।[ \t]?।", "॥", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 10. `DB-A5-008` · A5 Wrong normal form · fix · stage 10

1. **Disease:** A5 Wrong normal form. Pack `ind-sa-fw2`. Source: section A5 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a5(text)`.

```python
RULE_ID = "DB-A5-008"
CODE = "A5"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

SIGNS = r"\u093E-\u094C\u0962\u0963"    # dependent vowel signs ा ि ी ु ू ृ ॄ ॅ ॆ े ै ॉ ॊ ो ौ and ॢ ॣ
RE_A5_SAME = re.compile(rf"([{SIGNS}])\1+")    # the same vowel sign twice or more: ेे ाा ुु
RE_A5_STACK = re.compile(rf"[{SIGNS}][{SIGNS}]")    # any two vowel signs on one letter (detection only when they differ)
RE_A5_VIRAMA = re.compile("\u094D{2,}")    # doubled virama
RE_A5_A_AA = re.compile("अा")    # अ + ा, which is आ written in two parts
RE_A5_DD = re.compile("(?<!।)।।(?!।)")    # two single dandas in a row

def detect_a5(text):
    return bool(RE_A5_STACK.search(text) or RE_A5_VIRAMA.search(text) or RE_A5_A_AA.search(text)
                or ("॥" in text and RE_A5_DD.search(text)))

def medicine_a5(text):
    """Collapse a doubled vowel sign or virama, write अ+ा as आ, and make । । a ॥ in a document that already uses ॥.
    Two different vowel signs on one letter (ेो, ैौ) are detected by detect_a5 but not repaired: there is no safe choice."""
    text = RE_A5_SAME.sub(r"\1", text)
    text = RE_A5_VIRAMA.sub("्", text)
    text = RE_A5_A_AA.sub("आ", text)
    if "॥" in text:
        text = RE_A5_DD.sub("॥", text)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A5 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 11. `DB-A6-001` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-bn-fw2`. Source: section A6 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-001"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_DANDA_LOOKALIKE = re.compile('(?<=[\u0980-\u09ff’”)])৷(?=\\s|$)')  # ৷ (U+09F7) used as danda
_DOUBLE = re.compile('।৷')                                                  # ।৷
_PIPE = re.compile('(?<=[\u0980-\u09ff’”)]) ?\\|(?=[ \\t]*(?:\\n|$))', re.M)  # ASCII | at line end
_L_DANDA = re.compile('(?<=[\u0980-\u09ff’”]) l(?=\\s|$)')                  # Latin l as danda

def medicine_a6(text):
    """Replace danda look-alikes after Bengali text with the real danda । (U+0964)."""
    text = _DOUBLE.sub('।', text)
    text = _DANDA_LOOKALIKE.sub('।', text)
    text = _PIPE.sub('।', text)
    return _L_DANDA.sub('।', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 12. `DB-A6-002` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-bn-fw2`. Source: section A6 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-002"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re


def medicine_a6(text):
    """U+09F7 after a Bengali character or a space -> danda U+0964."""
    return re.sub("(?<=[ঀ-৿\\s])৷", "।", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 13. `DB-A6-003` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-gu-fw2`. Source: section A6 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-A6-003"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

SANDWICH = re.compile(r"[઀-૿][a-z]{1,8}[઀-૿]")
DEVANAGARI = re.compile(r"[\u0900-\u0963\u0966-\u097f]")      # letters, not the danda

def medicine(text):
    if SANDWICH.search(text):
        return None                       # drop the document
    lines = text.split("\n")
    keep = [l for l in lines if not DEVANAGARI.search(l)]
    if len(keep) < 0.7 * len(lines):
        return None                       # drop the document
    return "\n".join(keep)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 15 of 1...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 14. `DB-A6-004` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-hi-hplt`. Source: section A6 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-004"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_DANDA = re.compile("([\u0900-\u0963\u0966-\u097F]+)( ?)[Il](?=[ \t]*(?:\n|$|[\u0900-\u097F\"'\u201C\u201D\u2018\u2019]))")
_ROMAN_BEFORE = {"डिवीजन", "डिवीज़न", "भाग", "खंड", "खण्ड", "चरण", "फेज", "फेज़", "टाइप", "क्लास", "ग्रेड", "लेवल", "विश्वयुद्ध"}


def _danda(m):
    if m.group(1) in _ROMAN_BEFORE:  # "डिवीजन I" is a Roman numeral, not a danda
        return m.group(0)
    return m.group(1) + m.group(2) + "\u0964"


def medicine_a6(text):
    # Latin I or l typed for the danda after a Devanagari word: "हैI", "आया I", "हुआ l"
    t = _DANDA.sub(_danda, text)
    # visarga typed for the colon: "महत्वपूर्ण हैः यह" -> "है:"
    t = re.sub("(है|हैं|चाहिए)\u0903(?=\\s)", "\\1:", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 15. `DB-A6-005` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-hi-hplt`. Source: section A6 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-005"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# A6: ASCII "|" or Latin "I" typed for the danda, only right after a sentence-final verb
_VERB = (r"है|हैं|था|थे|थी|थीं|गया|गई|गयी|गए|होगा|होगी|होंगे|रहा|रही|रहे|सकता|सकती|सकते|करें|जाएगा|जाएगी|"
         r"जाएंगे|दिया|दी|दिए|किया|किए|हुआ|हुई|हुए|मिला|मिली|मिले|जाता|जाती|जाते|चाहिए|लिया|लिए")
_A6 = re.compile(r"(?<![ऀ-ॿ])(" + _VERB + r") ?[|I](?=[ \t]|\n|$)")


def medicine_a6(text):
    return _A6.sub(r"\1।", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 26 of 46 A6 documents; 15 other diseased documents touc...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 16. `DB-A6-006` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-kn-sangraha-s`. Source: section A6 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
2. **Medicine:** the author's code, unchanged. Main function: `m3_half_translated(text)`.

```python
RULE_ID = "DB-A6-006"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s"  # packs it runs on
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

HALF_IE = re.compile(r"\bi\.\s?ಇ\.")
HALF_EG = re.compile(r"\be\.\s?ಜಿ\.")
def m3_half_translated(s):
    return HALF_EG.sub("ಉದಾ.", HALF_IE.sub("ಅಂದರೆ", s))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m3_half_translated  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 0 of 359. It fixes 9 of the 30 A6 documents.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 17. `DB-A6-007` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-kn-sangraha-v`. Source: section A6 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-007"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

KN_SIGNED = "ಅ-ಹಾ-ೌ"                 # Kannada vowels, consonants and vowel signs
ZERO_KN = re.compile(f"(?<=[{KN_SIGNED}])೦(?![೦-೯])")
ZERO_ASCII = re.compile(f"(?<=[{KN_SIGNED}])0(?=[ಕ-ಹ])")
LATIN_S = re.compile("(?<=[ಀ-೿])s(?=[ಀ-೿])")


def fix_lookalikes(t):
    """A6: a Kannada digit zero (೦) or an ASCII 0 right after a Kannada letter is the anusvara (ಂ); a Latin s
    between Kannada letters is the avagraha (ಽ)."""
    t = ZERO_KN.sub("ಂ", t)
    t = ZERO_ASCII.sub("ಂ", t)
    return LATIN_S.sub("ಽ", t)


def medicine_a6(text):
    """The A6 rule, under the name that the harm tests look for: returns the fixed text."""
    return fix_lookalikes(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 18. `DB-A6-008` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-mr-fw2`. Source: section A6 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-008"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_a6(text):
    text = re.sub(r'([a-zA-Z])([\u0900-\u097F])', r'\1 \2', text)
    return re.sub(r'([\u0900-\u097F])([a-zA-Z])', r'\1 \2', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 19. `DB-A6-009` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-mr-sangraha-v`. Source: section A6 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_a6(text)`.

```python
RULE_ID = "DB-A6-009"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import re

_A6_MIXED_DIGITS = re.compile(r"[०-९0-9]+")
_A6_DIGIT_MAP = str.maketrans("0123456789", "०१२३४५६७८९")

def cure_a6(text):
    def convert(match):
        token = match.group()
        if re.search(r"[०-९]", token) and re.search(r"[0-9]", token):
            return token.translate(_A6_DIGIT_MAP)
        return token
    return _A6_MIXED_DIGITS.sub(convert, text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Only mixed-digit conversion is co...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 20. `DB-A6-010` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-sa-fw2`. Source: section A6 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-010"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_D = "ऀ-ॿ"
_CONS = "क-हक़-य़"
_MAT = "ा-ौॢॣ"
_ABBR = re.compile(r"(?:^|[\s(])(डा|डॉ|प्रो|डो|श्री|सं|पृ|ई|क्र|पं|मो|फो|दू)$")

def medicine_a6(text):
    def colon(m):
        before = text[max(0, m.start() - 6):m.start()]
        after = text[m.end():m.end() + 3].lstrip()
        if _ABBR.search(before) or (after and after[0].isalpha() and not "ऀ" <= after[0] <= "ॿ"):
            return m.group()
        return "ः"
    t = re.sub(f"(?<=[{_CONS}{_MAT}]):(?=[\\s।॥]|$)", colon, text)
    t = re.sub(f"(?<=[{_CONS}{_MAT}ंः])[Ss](?=[{_CONS}])", "ऽ", t)
    out = []
    for line in t.split("\n"):
        if not (line.startswith("|") or line.rstrip().endswith("|") and line.count("|") > 2):
            line = re.sub(f"(?<=[{_D}]) ?\\|\\|(?=\\s|$)", " ॥", line)
            line = re.sub(f"(?<=[{_D}]) ?\\|(?=\\s|$)", " ।", line)
        line = re.sub(f"(?<=[{_D}]) ?I(?=\\s*$|\\s+[{_D}])", " ।", line)
        line = re.sub(f"(?<=[{_D}])o(?=\\s)", "॰", line)
        line = re.sub(f"(?<=[A-Za-z]{{3}})(?=[{_CONS}])|(?<=[{_D}])(?=[A-Za-z]{{3}})", " ", line)
        out.append(line)
    return "\n".join(out).translate({0x0946: 0x0947, 0x094A: 0x094B, 0x0931: 0x0930})


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 21. `DB-A6-011` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-sa-fw2`. Source: section A6 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `fix_a6(text)`.

```python
RULE_ID = "DB-A6-011"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

# character classes use \u escapes on purpose: a literal nukta letter is stored decomposed and would break the range
DEVA_LETTER = r"\u0904-\u0939\u093D\u0950\u0958-\u0961\u0972-\u097F"    # letters incl. avagraha and OM
DEVA_MARK = r"\u0900-\u0903\u093A-\u093C\u093E-\u094F\u0951-\u0957\u0962\u0963"    # matras, virama, nukta, bindus, visarga, accents
BOUNDARY = r"[ \t\u00A0\r\n।॥]"    # space, tab, nbsp, newline, danda
E_O_VOWELS = r"\u0946\u0947\u094A\u094B\u090E\u090F\u0912\u0913"    # matras ॆ े ॊ ो and letters ऎ ए ऒ ओ
RE_A6_DANDA = re.compile(rf"(?<=[{DEVA_LETTER}{DEVA_MARK}])(I{{1,2}}|l{{1,2}})(?={BOUNDARY}|$)")
RE_A6_AVAGRAHA = re.compile(rf"(?<=[{E_O_VOWELS}])[Ss](?=[{DEVA_LETTER}])")
# ASCII ':' typed for visarga: right after a Devanagari letter or vowel sign, before a boundary or a Devanagari letter
RE_A6_COLON = re.compile(rf"(?<=[{DEVA_LETTER}\u093A-\u093C\u093E-\u094F\u0962\u0963]):(?={BOUNDARY}|$|[{DEVA_LETTER}])")
# ASCII '|' or '||' typed for danda or double danda: after a Devanagari word (an optional space before it is kept), before a boundary
RE_A6_PIPE = re.compile(rf"(?<=[{DEVA_LETTER}{DEVA_MARK}])([ ]?)(\|{{1,2}})(?={BOUNDARY}|$)")

RE_LATIN_LETTER = re.compile(r"[A-Za-z]")

def _pipe_line(line):
    if line.lstrip().startswith("|") or RE_LATIN_LETTER.search(line):    # wiki table row, or a title/menu line with Latin words
        return line
    return RE_A6_PIPE.sub(lambda m: m.group(1) + ("॥" if len(m.group(2)) == 2 else "।"), line)

def fix_a6(text):
    text = RE_A6_DANDA.sub(lambda m: "॥" if len(m.group(1)) == 2 else "।", text)
    text = RE_A6_AVAGRAHA.sub("ऽ", text)
    text = RE_A6_COLON.sub("ः", text)
    return "\n".join(_pipe_line(l) for l in text.split("\n"))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = fix_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 22. `DB-A6-012` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-ta-sangraha-v`. Source: section A6 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-012"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_a6(text):
    return re.sub("ஃ(?![க-ஹ])", ":", text)  # aytham before a space or line end is a lost colon


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 135 documents, none labelled `clean`. 8 of the 10 changed documents
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 23. `DB-A6-013` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-te-fw2`. Source: section A6 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `a6_lookalike(text)`.

```python
RULE_ID = "DB-A6-013"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

A6_RX = re.compile(r"(?<=[క-హా-ౌ])[o౦](?=[క-హ]|\s|[.,!?]|$)")
def a6_lookalike(t, url=None):
    return A6_RX.sub("ం", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = a6_lookalike  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 24. `DB-A6-014` · A6 Wrong or mixed script · fix · stage 10

1. **Disease:** A6 Wrong or mixed script. Pack `ind-te-sangraha-s`. Source: section A6 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-014"
CODE = "A6"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_VISARGA_WORDS = {"అంతః", "ఆయుః", "ఉరః", "చేతః", "తపః", "తేజః", "నమః", "పయః", "పునః", "ప్రాతః", "భూః", "మనః", "యశః", "వచః", "శిరః", "శ్రీః", "స్వః"}

def medicine_a6(text):
    def fix(m):
        word = m.group(1) + "ః"
        return m.group(0) if word in _VISARGA_WORDS else m.group(1) + ":"
    return re.sub(r"([\u0C00-\u0C02\u0C04-\u0C7F]*)ః(?=\n|$| [\"“‘'])", fix, text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_a6` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 25. `DB-G1-001` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-bn-fw2`. Source: section G1 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-001"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re


def medicine_g1(text):
    """Remove a space between a consonant and a following virama + consonant."""
    return re.sub("(?<=[ক-হ]) (?=্[ক-হ])", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 26. `DB-G1-002` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-gu-fw2`. Source: section G1 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-002"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU_SIGN = "\u0A81-\u0A83\u0ABC-\u0ACD"      # dependent signs, nukta, virama
GU_VOWEL_SIGN = "\u0ABE-\u0ACC\u0A81-\u0A83"
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

G1_DOUBLE = re.compile(rf"([{GU_SIGN}])\1+")
G1_ORPHAN = re.compile(rf"(?<=\s)[{GU_VOWEL_SIGN}]")

def m6_g1(text, url=None):
    return _fix(text, G1_ORPHAN.sub("", G1_DOUBLE.sub(r"\1", text)))

def medicine_g1(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m6_g1(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 27. `DB-G1-003` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-gu-fw2`. Source: section G1 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-G1-003"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

# space before a vowel sign / anusvara, after a consonant, virama or vowel sign
DETACHED = re.compile("(?<=[\u0a95-\u0ab9\u0acd\u0abe-\u0acc]) +(?=[\u0abe-\u0acc\u0a82])")

def medicine(text):
    return DETACHED.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 7 of 9.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 28. `DB-G1-004` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-hi-hplt`. Source: section G1 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-004"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g1(text):
    # a read-more marker cut a word before its vowel sign: "ब… [+] िजनेस" -> "बिजनेस"
    t = re.sub("…\\s*\\[\\+\\]\\s*(?=[\u0900-\u0903\u093E-\u094C])", "", text)
    # a space before a vowel sign or anusvara: "मे ं" -> "में"
    t = re.sub("(?<=[\u0915-\u0939\u093C-\u094C\u0958-\u095F])[ \t]+(?=[\u0900-\u0902\u093E-\u094C])", "", t)
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 29. `DB-G1-005` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-kn-fw2`. Source: section G1 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-005"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata

G1 = re.compile(r'([\u0C80-\u0CFF]) ([\u0CBE-\u0CCD\u0CD5\u0CD6\u0C82\u0C83])')

def medicine_g1(text):
    out = G1.sub(r'\1\2', text)
    return unicodedata.normalize('NFC', out) if out != text else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 30. `DB-G1-006` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-mr-fw2`. Source: section G1 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-006"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g1(text):
    text = re.sub(r'([\u0915-\u0939\u0958-\u095F])\s+([\u093E-\u094D\u0962\u0963])', r'\1\2', text)
    return re.sub(r'([\u0966-\u096F0-9])\s*ः\s*([\u0966-\u096F0-9])', r'\1:\2', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 31. `DB-G1-007` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-sa-fw2`. Source: section G1 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-007"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g1(text):
    return re.sub("(?<=[ऀ-ॿ])[ \t \n]+(?=[ा-ौॢॣँ-ः्])", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 32. `DB-G1-008` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-sa-fw2`. Source: section G1 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `fix_g1(text)`.

```python
RULE_ID = "DB-G1-008"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

CONS = r"\u0915-\u0939\u0958-\u095F"    # consonants क-ह and nukta consonants
DEP = r"\u0901-\u0903\u093C\u093E-\u094D"    # candrabindu, anusvara, visarga, nukta, matras, virama
MATRA = r"\u093E-\u094C"    # vowel signs only
RE_G1_WS = re.compile(rf"([{CONS}])[ \t\u00A0]+([{DEP}])(?![{MATRA}])")
RE_G1_NL = re.compile(rf"([{CONS}])[ \t\u00A0]*\r?\n[ \t\u00A0]*([{DEP}])(?![{MATRA}])")
RE_G1_DOUBLE_VIRAMA = re.compile(r"्{2,}")

def fix_g1(text):
    text = RE_G1_WS.sub(r"\1\2", text)
    text = RE_G1_NL.sub(r"\1\2", text)
    return RE_G1_DOUBLE_VIRAMA.sub("्", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = fix_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 33. `DB-G1-009` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-ta-sangraha-v`. Source: section G1 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-009"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

_LEGACY = {("ெ", "ா"): "ொ", ("ே", "ா"): "ோ"}  # sign typed before the consonant, then ா: one two-part vowel sign

def medicine_g1(text):
    text = text.replace("ா்", "ர்").replace("ுா", "ூ")
    return re.sub("(?<![க-ஹ])([ெேை])([க-ஹ])(ா?)",
                  lambda m: m[2] + _LEGACY.get((m[1], m[3]), m[1] + m[3]), text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 25 documents, none labelled `clean`. The one changed document
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 34. `DB-G1-010` · G1 Cut at the vowel sign · fix · stage 10

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-te-fw2`. Source: section G1 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `g1_orphan_signs(text)`.

```python
RULE_ID = "DB-G1-010"
CODE = "G1"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

G1_RX = re.compile(r"(?m)(^|\s)[ా-ౖఁ-ఃౢౣ]+")
def g1_orphan_signs(t, url=None):
    return G1_RX.sub(r"\1", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = g1_orphan_signs  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 35. `DB-G2-001` · G2 Lost ZWJ or ZWNJ · fix · stage 10

1. **Disease:** G2 Lost ZWJ or ZWNJ. Pack `ind-bn-fw2`. Source: section G2 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g2(text)`.

```python
RULE_ID = "DB-G2-001"
CODE = "G2"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

ZWJ = chr(0x200D)
# র + \u09cd + য + \u09be at the start of a word is the loan-word ra + ya-phala (র\u200d\u09cdযাব, র\u200d\u09cdযালি). Without ZWJ it
# renders as reph + য (র্যা). Inside a word the reph reading is correct (কার্যালয়), and after a virama
# (ব্র্যান্ড) র is already a ra-phala, so those are left alone.
_LOAN = re.compile('(?<![\u0980-\u09ff])র্(?=যা)')

def medicine_g2(text):
    """Insert ZWJ after র in loan-word র্যা."""
    return _LOAN.sub('র' + ZWJ + '\u09cd', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G2 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 36. `DB-G2-002` · G2 Lost ZWJ or ZWNJ · fix · stage 10

1. **Disease:** G2 Lost ZWJ or ZWNJ. Pack `ind-bn-fw2`. Source: section G2 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g2(text)`.

```python
RULE_ID = "DB-G2-002"
CODE = "G2"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_G2_RX = re.compile("(?:^|(?<=[^ঀ-৿])|(?<=্))র্যা", re.M)


def medicine_g2(text):
    """র্যা at a word start or after a virama -> র + ZWJ + ্যা (the loanword form)."""
    return _G2_RX.sub("র‍্যা", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314 (circular, see above). **Warning:** a gold set built from the same FineWeb-2 dump
5. **Side effects:** in the author's `medicine.md`, section G2 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 37. `DB-G2-003` · G2 Lost ZWJ or ZWNJ · keep · stage 10

1. **Disease:** G2 Lost ZWJ or ZWNJ. Pack `ind-sa-fw2`. Source: section G2 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g2(text)`.

```python
RULE_ID = "DB-G2-003"
CODE = "G2"
ACTION = "keep"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

def detect_g2(text):
    """Always False: G2 cannot be detected from the text alone. The pack contains zero U+200C/U+200D,
    so there is no in-text signal; detection is source_compare.py's comparison with the crawl-date page."""
    return False
def medicine_g2(text):
    return text    # action none: no in-text signal; detection is source_compare.py
# source_compare.py, in words: zw_source = count(U+200C, U+200D) in fetched page text;
# zw_pack = same count in the pack text; flag G2 when zw_source > 0 and zw_pack == 0,
# evidence = the source words that carried the joiner, located in the pack text by offset.


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G2 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 38. `DB-G4-001` · G4 Over-normalised · fix · stage 10

1. **Disease:** G4 Over-normalised. Pack `ind-kn-sangraha-v`. Source: section G4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python
RULE_ID = "DB-G4-001"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

"""Find visarga (U+0C83) that stands for a colon.

The Indic NLP normaliser (correct_visarga) rewrites ':' after an Indic letter as visarga, so a dateline
'ಬೆಂಗಳೂರು:' becomes 'ಬೆಂಗಳೂರುಃ'. Real visarga words are a small closed set: Sanskrit adverbs in -ತಃ / -ಶಃ,
a few words (ಪುನಃ, ನಮಃ, ...) and compound prefixes (ದುಃಖ, ನಿಃಸಂಶಯ, ಅಂತಃಕರಣ). Lines with a danda (। ॥) are
treated as Sanskrit verse and left alone. PDF verse often writes the danda as '|' or '||': in a document where a
visarga is followed by '|', or where two or more lines end in '|', every line with a '|' is left alone too.
"""
import re

VIS, VIRAMA, AA_SIGN = chr(0x0C83), chr(0x0CCD), chr(0x0CBE)
KN_BLOCK = chr(0x0C80) + "-" + chr(0x0CFF)                  # the Kannada block, for character classes
JOINERS = chr(0x200C) + chr(0x200D)                          # ZWNJ, ZWJ
KN = re.compile("[" + KN_BLOCK + "]")
WORD_END = re.compile("[" + KN_BLOCK + JOINERS + "]+$")
GENUINE_END = re.compile(r"(ತಃ|ಶಃ)$")
GENUINE = {"ಪುನಃ", "ನಮಃ", "ಮನಃ", "ಅಂತಃ", "ಯಶಃ", "ತೇಜಃ", "ಶಿರಃ", "ಪ್ರಾತಃ", "ಉರಃ", "ಛಂದಃ", "ತಪಃ", "ಪಯಃ",
           "ವಯಃ", "ನಭಃ", "ಅಧಃ", "ಪುರಃ", "ಬಹಿಃ", "ದುಃ", "ನಿಃ", "ಮುಹುಃ", "ಚಕ್ಷುಃ", "ಆಯುಃ", "ಧನುಃ", "ವಪುಃ",
           "ಹವಿಃ", "ಜ್ಯೋತಿಃ", "ಶ್ರೇಯಃ", "ಮನಸಃ", "ರಜಃ", "ತಮಃ", "ಸ್ವಾಹಾಃ", "ಓಂನಮಃ", "ಸ್ವತಹಃ"}
PIPE_AFTER_VIS = re.compile(VIS + r"[ \t]*\|")
PREFIX = {"ದು", "ನಿ", "ಅಂತ", "ಮನ", "ತೇಜ", "ಪ್ರಾತ", "ಬಹಿ", "ಪುನ", "ಛಂದ", "ತಪ", "ಯಶ", "ಅಧ", "ಶಿರ", "ಸುದು",
          "ಸರ್ವದು", "ಸುಖದು", "ಮನಸ್ತಾಪದು"}

def colon_visargas(t, verse_min=2, verse_len=160):
    """Return the offsets of every visarga in t that stands for a colon.

    A line with verse_min or more candidates is taken as Sanskrit verse and skipped when it is short
    (verse_len characters or less) or when most candidates end like a Sanskrit nominative (-aH after a
    bare consonant, or -AH). Kannada prose with several colons ends them on vowel signs (ಹೇಳುತ್ತಾರೆಃ).
    """
    verse_doc = "।" in t or "॥" in t
    by_line = {}
    for i in _candidates(t):
        start = t.rfind("\n", 0, i) + 1
        if verse_doc and t[i - 1] != VIRAMA and " " in t[start:i].strip():
            continue                                    # a document with verse: only first words and ್ಃ
        by_line.setdefault(start, []).append(i)
    out = []
    for start, offs in by_line.items():
        end = t.find("\n", start); end = len(t) if end < 0 else end
        if len(offs) >= verse_min:
            sanskrit = sum(1 for i in offs if t[i - 1] == AA_SIGN or 0x0C95 <= ord(t[i - 1]) <= 0x0CB9)
            if end - start <= verse_len or sanskrit / len(offs) >= 0.75:
                continue
        out.extend(offs)
    return out

def _candidates(t):
    out = []
    pipe_verse = bool(PIPE_AFTER_VIS.search(t)) or sum(1 for l in t.split("\n") if l.rstrip().endswith("|")) >= 2
    for m in re.finditer(VIS, t):
        i = m.start()
        line_start = t.rfind("\n", 0, i) + 1
        line_end = t.find("\n", i); line_end = len(t) if line_end < 0 else line_end
        if "।" in t[line_start:line_end] or "॥" in t[line_start:line_end]:
            continue
        if pipe_verse and "|" in t[line_start:line_end]:
            continue                                    # verse with '|' as danda
        p = t[i - 1] if i else " "
        if p == VIRAMA:
            out.append(i); continue
        if not KN.match(p):
            continue                                    # orphan visarga: G1, not a colon
        w = WORD_END.search(t[:i]).group()
        nx = t[i + 1] if i + 1 < len(t) else " "
        if KN.match(nx):                                # visarga inside a word
            if w in PREFIX or w.endswith(("ದು", "ನಿ")) or len(w) < 3:
                continue
            out.append(i); continue
        if GENUINE_END.search(w + VIS) or (w + VIS) in GENUINE:
            continue
        out.append(i)
    return out

def fix(t):
    """Medicine: turn colon-visarga back into ':'."""
    pos = set(colon_visargas(t))
    return "".join(":" if i in pos else c for i, c in enumerate(t))


fix_visarga = fix
DEC_SPLIT = re.compile(r"(?<=[^\d\n.])(\d{1,3})\. (\d{1,3})(?![\d.])")
DOMAIN_SPLIT = re.compile(r"\b([A-Za-z0-9-]+)\. (com|in|org|net|gov|co|info|edu)\b")
WWW_SPLIT = re.compile(r"\bwww\. (?=[A-Za-z0-9])")


def fix_dot_split(t):
    """G4: join a dot split by an inserted space inside a decimal, a clock time or a web address (3. 3, 10. 20,
    newskadaba. com, www. vknews. in). A number at the start of a line (a list item '1. 5 ...') is left alone."""
    t = WWW_SPLIT.sub("www.", t)
    for _ in range(3):                                  # karnataka. gov. in needs two passes
        t = DOMAIN_SPLIT.sub(r"\1.\2", t)
    return DEC_SPLIT.sub(r"\1.\2", t)


def fix_over_normalised(t):
    """G4: undo the two marks of the earlier normaliser: visarga for a colon, then the dot split."""
    return fix_dot_split(fix_visarga(t))


def medicine_g4(text):
    """The G4 rule, under the name that the harm tests look for: returns the fixed text."""
    return fix_over_normalised(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 39. `DB-G4-002` · G4 Over-normalised · fix · stage 10

1. **Disease:** G4 Over-normalised. Pack `ind-mr-fw2`. Source: section G4 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python
RULE_ID = "DB-G4-002"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g4(text):
    lines = text.splitlines(keepends=True)
    out = []
    for line in lines:
        if line.strip().startswith('|') and line.strip().endswith('|'):
            out.append(line)
        else:
            line = re.sub(r'(?<=[\u0900-\u097F])\s*\|\|\s*', ' ॥ ', line)
            line = re.sub(r'(?<=[\u0900-\u097F])\s*\|\s*(?=[\u0900-\u097F\s]|$)', ' । ', line)
            out.append(line)
    return ''.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 40. `DB-G4-003` · G4 Over-normalised · fix · stage 10

1. **Disease:** G4 Over-normalised. Pack `ind-sa-fw2`. Source: section G4 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python
RULE_ID = "DB-G4-003"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

RE_G4_RUN = re.compile(r"[0-9]+(?:[.,:/\-][0-9]+)*")
DEVA_CTX = r"\u0904-\u0939\u0958-\u0961\u0972-\u097F"   # Devanagari letters only
RE_DEVA_CTX = re.compile(rf"[{DEVA_CTX}]")
RE_LATIN = re.compile(r"[A-Za-z]"); RE_DEVA_DIGIT = re.compile(r"[०-९]")
TO_DEVA_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९"); CTX = 10; MIN_RUNS = 3
# news-prose guard: month names (Hindi/Sanskrit/Marathi stems), currency words, %, दिनाङ्क within NEWS_CTX chars
NEWS_WORDS = (r"जनवर|फरवर|फेब्रु|मार्च|अप्रैल|एप्रिल|मई|जून|जुलाई|जुलै|अगस्त|आगस्ट|सितम्बर|सितंबर|सप्टेम्बर|सेप्टेम्बर|"
              r"अक्टूबर|अक्तूबर|ऑक्टोबर|नवम्बर|नवंबर|नोव्हेम्बर|दिसम्बर|दिसंबर|डिसेम्बर|"
              r"रूप्यक|रुपय|रूपय|रु\.|₹|करोड|लाख|डॉलर|डालर|%|दिनाङ्क|दिनांक")
RE_G4_NEWS = re.compile(NEWS_WORDS); NEWS_CTX = 12

def _g4_convert_run(m):
    run = m.group()
    if ":" in run or "/" in run or "-" in run: return run
    s = m.string; left = s[max(0, m.start() - CTX):m.start()]; right = s[m.end():m.end() + CTX]
    if not (RE_DEVA_CTX.search(left) and RE_DEVA_CTX.search(right)): return run
    if RE_LATIN.search(left) or RE_LATIN.search(right): return run
    nleft = s[max(0, m.start() - NEWS_CTX):m.start()]; nright = s[m.end():m.end() + NEWS_CTX]
    if RE_G4_NEWS.search(nleft) or RE_G4_NEWS.search(nright): return run   # date or amount in news prose
    return run.translate(TO_DEVA_DIGITS)

def fix_g4_all_ascii(text):            # helper called by fix_g4_mixed_only
    convertible = sum(1 for m in RE_G4_RUN.finditer(text) if _g4_convert_run(m) != m.group())
    if convertible < MIN_RUNS: return text
    return RE_G4_RUN.sub(_g4_convert_run, text)

def fix_g4_mixed_only(text):           # the G4 medicine
    if not RE_DEVA_DIGIT.search(text): return text
    return fix_g4_all_ascii(text)

def medicine_g4(text):                 # the G4 medicine = fix_g4_mixed_only
    return fix_g4_mixed_only(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 41. `DB-G4-004` · G4 Over-normalised · fix · stage 10

1. **Disease:** G4 Over-normalised. Pack `ind-ta-sangraha-v`. Source: section G4 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g4(text)`.

```python
RULE_ID = "DB-G4-004"
CODE = "G4"
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_g4(text):
    text = re.sub(r"(?<=\d)\. (?=\d)", ".", text)  # 28. 17 -> 28.17
    return re.sub(r"\b[A-Za-z0-9-]+(?:\. [A-Za-z0-9-]+)*\. (?:com|in|org|net|lk|info)\b",
                  lambda m: m[0].replace(". ", "."), text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 65 documents, none labelled `clean`. The 22 changed documents
5. **Side effects:** in the author's `medicine.md`, section G4 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 42. `DB-B2-001` · B2 HTML or XML tags · fix · stage 20

1. **Disease:** B2 HTML or XML tags. Pack `ind-hi-fw2`. Source: section B2 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_b2(text)`.

```python
RULE_ID = "DB-B2-001"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2"  # packs it runs on
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_URL_TOKEN = re.compile(r"https?://\S+|data:image/\w+;base64,\S+")

def medicine_b2(text: str) -> str:
    """Remove HTML/XML tags; keep surrounding text. (Automatic medicine; URL strip is helper-only.)"""
    return _HTML_TAG_RE.sub("", text or "")

def _strip_b2_urls(text: str) -> str:
    """Optional selective fix: blank URL tokens (review before mass use). Not automatic medicine."""
    return _URL_TOKEN.sub("", text or "")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule B2` (2026-10-31). Ran **`medicine_b2` (tag strip only)**:
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 43. `DB-B2-002` · B2 HTML or XML tags · fix · stage 20

1. **Disease:** B2 HTML or XML tags. Pack `ind-hi-hplt`. Source: section B2 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_b2(text)`.

```python
RULE_ID = "DB-B2-002"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b2(text):
    if "<" in text:  # a real tag is there: leave it to an HTML cleaner
        return text
    return re.sub("[ \t]*/>", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 44. `DB-B2-003` · B2 HTML or XML tags · fix · stage 20

1. **Disease:** B2 HTML or XML tags. Pack `ind-kn-sangraha-s`. Source: section B2 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
2. **Medicine:** the author's code, unchanged. Main function: `m1_tags(text)`.

```python
RULE_ID = "DB-B2-003"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s"  # packs it runs on
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

TAG_ID = re.compile(r" ?<?ಐ\. ಡಿ\. \d+>?")
TAG_BR = re.compile(r"<ಬಿ\.? ?ಆರ್\.?>|<br\s*/?>", re.I)
TAG_ANY = re.compile(r"</?(?:[A-Za-zÀ-ÿ][^<>\n]{0,40}|ರಿಫರ್[^<>\n]{0,80})>|<>")
def m1_tags(s):
    s = TAG_BR.sub("\n", s)
    return TAG_ANY.sub("", TAG_ID.sub("", s))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m1_tags  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 0 of 359.
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 45. `DB-B2-004` · B2 HTML or XML tags · fix · stage 20

1. **Disease:** B2 HTML or XML tags. Pack `ind-te-fw2`. Source: section B2 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `b2_html(text)`.

```python
RULE_ID = "DB-B2-004"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

B2_RX = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^<>]{0,300})?/?>|<>|\b(?:width|height|class|style)=\"[^\"]*\"")
def b2_html(t, url=None):
    return B2_RX.sub("", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = b2_html  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 46. `DB-B2-005` · B2 HTML or XML tags · fix · stage 20

1. **Disease:** B2 HTML or XML tags. Pack `ind-te-sangraha-s`. Source: section B2 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_b2(text)`.

```python
RULE_ID = "DB-B2-005"
CODE = "B2"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b2(text):
    text = re.sub(r"<</[^<>\s]{0,3}>", "", text)
    text = re.sub(r"<[\u0C00-\u0C7F]{1,12}>", "", text)
    text = re.sub(r"(?<=[.!?])>(?=\s|$)", "", text)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_b2` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section B2 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 47. `DB-B3-001` · B3 Ghost chat markers · fix · stage 20

1. **Disease:** B3 Ghost chat markers. Pack `ind-kn-sangraha-s`. Source: section B3 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
2. **Medicine:** the author's code, unchanged. Main function: `m2_ghost(text)`.

```python
RULE_ID = "DB-B3-001"
CODE = "B3"
ACTION = "fix"
STAGE = "20"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s"  # packs it runs on
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

GHOST = re.compile(r"<unk>|<\|[a-z_]+\|>|\[/?INST\]|</?s>|</?think>")
def m2_ghost(s):
    return GHOST.sub("", s)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m2_ghost  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 0 of 359.
5. **Side effects:** in the author's `medicine.md`, section B3 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 48. `DB-A3-003` · A3 Mojibake · drop · stage 30

1. **Disease:** A3 Mojibake. Pack `ind-bn-fw2`. Source: section A3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python
RULE_ID = "DB-A3-003"
CODE = "A3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_PAIRS = [('\u09be\u09c7', '\u09cb'),   # \u09be + \u09c7 typed for \u09cb
          ('\u09c8\u09be', '\u09cc'),   # \u09c8 + \u09be typed for \u09cc
          ('\u09c7\u09c7', '\u09c7'), ('\u09bf\u09bf', '\u09bf'), ('\u09c1\u09c1', '\u09c1'), ('\u09be\u09be', '\u09be')]
# Bijoy / legacy-font residue: a Latin-1 symbol, dash or angle quote glued between two Bengali characters.
_RESIDUE = re.compile('(?<=[\u0980-\u09ff])[¡-ÿ–—‹›‚”](?=[\u0980-\u09ff])')

def medicine_a3(text):
    """Drop a document with 3 or more legacy-font residues (they cannot be mapped back safely).
    Otherwise repair doubled or misordered vowel signs."""
    if len(_RESIDUE.findall(text)) >= 3:
        return True
    for bad, good in _PAIRS:
        text = text.replace(bad, good)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 49. `DB-A3-004` · A3 Mojibake · drop · stage 30

1. **Disease:** A3 Mojibake. Pack `ind-kn-sangraha-v`. Source: section A3 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a3(text)`.

```python
RULE_ID = "DB-A3-004"
CODE = "A3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

IAST = set("āīūṛṝḷṅñṇṭḍśṣḥṁĀĪŪṚṄÑṆṬḌŚṢḤṀ")              # romanised Indic, not legacy-font residue


def is_kn(c):
    return 0x0C80 <= ord(c) <= 0x0CFF


def legacy_residue(t):
    """A3: offsets of legacy-font (Nudi/Baraha) residue inside Kannada words.

    Residue is a Latin-1 or Latin Extended letter inside a word that also holds Kannada (ಸಂಸ್ಕøತಿ), or a '$'
    directly before a Kannada vowel sign or virama (ಸ್ಕೊ$್ವ). A '$' before a digit ($100ರಷ್ಟು), a degree
    sign (30°ಸೆ) and IAST letters are not residue.
    """
    out = []
    for m in re.finditer(r"\S+", t):
        w = m.group()
        if not any(is_kn(c) for c in w):
            continue
        for k, c in enumerate(w):
            nxt = w[k + 1] if k + 1 < len(w) else " "
            if c.isalpha() and 0xC0 <= ord(c) <= 0x24F and c not in IAST:
                out.append(m.start() + k)
            elif c == "$" and is_kn(nxt) and not nxt.isalpha():
                out.append(m.start() + k)
    return out


def has_legacy(t):
    """A3: drop a document with legacy-font (Nudi/Baraha) residue inside Kannada words."""
    return bool(legacy_residue(t))


def medicine_a3(text):
    """The A3 rule, under the name that the harm tests look for: True drops the document."""
    return has_legacy(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section A3 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 50. `DB-A4-001` · A4 Replacement characters · drop · stage 30

1. **Disease:** A4 Replacement characters. Pack `ind-sa-fw2`. Source: section A4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a4(text)`.

```python
RULE_ID = "DB-A4-001"
CODE = "A4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_a4(text):
    return "�" in text or "{??}" in text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 51. `DB-A6-015` · A6 Wrong or mixed script · drop · stage 30

1. **Disease:** A6 Wrong or mixed script. Pack `ind-gu-fw2`. Source: section A6 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_a6(text)`.

```python
RULE_ID = "DB-A6-015"
CODE = "A6"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block

A6_WORD = re.compile(rf"[A-Za-z]+[{GU}]+|[{GU}]+[A-Za-z]+")
A6_ENDING = re.compile(r"[A-Za-z]+(?:ઓ)?(?:એ|ના|ની|નું|નુ|નો|ને|નાં|માં|થી|પર|વાળા|વાળી|ે|ી|ો|ઓ)")

def m7_a6(text, url=None, limit=3):
    n = sum(not A6_ENDING.fullmatch(w) for w in A6_WORD.findall(text))
    return (text, "drop" if n >= limit else "keep")

def medicine_a6(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m7_a6(text, url)[1] == "drop"


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_a6  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section A6 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 52. `DB-C3-001` · C3 Truncated document · drop · stage 30

1. **Disease:** C3 Truncated document. Pack `ind-bn-fw2`. Source: section C3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-001"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_CUT = re.compile(r'(?:\[\s*(?:…|\.\.\.)\s*\]|বিস্তারিত\s*\.{2,}|Continue\s+Reading|Read\s+(?:Entire\s+Article|more))\W*$', re.I)

def medicine_c3(text):
    """Drop a document whose last line ends with a teaser cut mark ([…], 'বিস্তারিত..', 'Continue Reading').
    Documents cut in mid-sentence without a mark are not touched: they cannot be told apart from
    pages that end with a name, a list item or a caption."""
    last = text.rstrip().rsplit('\n', 1)[-1]
    return bool(_CUT.search(last))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 53. `DB-C3-002` · C3 Truncated document · drop · stage 30

1. **Disease:** C3 Truncated document. Pack `ind-hi-hplt`. Source: section C3 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-002"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_CUT = re.compile(r"\[…\]|\[\.\.\.\]|…\s?\[\+\]|Read More")


def medicine_c3(text):
    return len(_CUT.findall(text)) >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 54. `DB-C3-003` · C3 Truncated document · drop · stage 30

1. **Disease:** C3 Truncated document. Pack `ind-mr-fw2`. Source: section C3 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-003"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c3(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines and len(lines[-1]) >= 40 and lines[-1][-1] not in ".!?।॥۔؟…\"'”’) ]}»":
        return True
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 55. `DB-C3-004` · C3 Truncated document · drop · stage 30

1. **Disease:** C3 Truncated document. Pack `ind-sa-fw2`. Source: section C3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-004"
CODE = "C3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

from urllib.parse import unquote

def _scan_page(url):
    return "wikisource.org/wiki/पृष्ठम्:" in unquote(url)

def medicine_c3(text):
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) >= 10]
    if not lines:
        return False
    last = lines[-1]
    dev = len(re.findall("[\u0900-\u097F]", last))
    letters = sum(c.isalpha() for c in last) or 1
    return dev / letters > 0.6 and bool(re.search(r"(?:[,‘“(]|(?<=[\u0900-\u097F])-)\s*$", last))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 56. `DB-C4-001` · C4 Two documents joined · drop · stage 30

1. **Disease:** C4 Two documents joined. Pack `ind-bn-fw2`. Source: section C4 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-001"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_TEASER = re.compile(r'বিস্তারিত\s*\.{2,}|Continue\s+Reading|\[\s*(?:…|\.\.\.)\s*\]|Read\s+More\s*(?:»|→|$)', re.I | re.M)

def medicine_c4(text):
    """Drop index, tag and archive pages: two or more teaser cut marks mean several stories were glued together."""
    return len(_TEASER.findall(text)) >= 2


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 57. `DB-C4-002` · C4 Two documents joined · drop · stage 30

1. **Disease:** C4 Two documents joined. Pack `ind-hi-fw2`. Source: section C4 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
2. **Medicine:** the author's code, unchanged. Main function: `flag_c4_trading_spam(text)`.

```python
RULE_ID = "DB-C4-002"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2"  # packs it runs on
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_TRADE_TERMS = re.compile(
    r"फ़ॉरेक्स|फॉरेक्स|\bforex\b|बाइनरी\s+ऑप्शन|binary\s+options?|"
    r"ट्रेडिंग\s+प्लेटफ़?ॉर्म|\btrading\b|\bbroker\b|ब्रोकर|"
    r"ट्रेडिंग|ट्रेडर|ऑप्शन|विकल्प\s+ट्रेड",
    re.I,
)

def flag_c4_trading_spam(text: str) -> bool:
    """True if >=4 distinct trading terms (drop-class C4)."""
    terms = {m.group(0).lower() for m in _TRADE_TERMS.finditer(text or "")}
    return len(terms) >= 4


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = flag_c4_trading_spam  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule C4` (2026-10-31). Ran `flag_c4_trading_spam`:
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 58. `DB-C4-003` · C4 Two documents joined · drop · stage 30

1. **Disease:** C4 Two documents joined. Pack `ind-hi-hplt`. Source: section C4 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-003"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_CUT4 = re.compile(r"\[…\]|\[\.\.\.\]|…\s?\[\+\]|Read More")
_SPAM_FOOTER = re.compile("अधिकतम रेटिंग \\d+\\s*\nन्यूनतम स्कोर")


def medicine_c4(text):
    return len(_CUT4.findall(text)) >= 3 or bool(_SPAM_FOOTER.search(text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 59. `DB-C4-004` · C4 Two documents joined · drop · stage 30

1. **Disease:** C4 Two documents joined. Pack `ind-hi-hplt`. Source: section C4 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-004"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C4: listing pages (several teasers joined): drop
def medicine_c4(text):
    cut = text.count("[…]") + text.count("[...]")
    more = len(re.findall(r"(?:…|\.\.\.)\s*\n?\s*Read More", text))
    return cut >= 2 or more >= 2


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 7 of 48 C4 documents; 0 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 60. `DB-C4-005` · C4 Two documents joined · drop · stage 30

1. **Disease:** C4 Two documents joined. Pack `ind-mr-fw2`. Source: section C4 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-005"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c4(text):
    if "\nCopyright ©" in text[200:]:
        return True
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 61. `DB-C4-006` · C4 Two documents joined · drop · stage 30

1. **Disease:** C4 Two documents joined. Pack `ind-te-fw2`. Source: section C4 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `c4_feed(text)`.

```python
RULE_ID = "DB-C4-006"
CODE = "C4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

C4_RX = re.compile(r"(?m)(?:\d+\s+(?:min|mins|hours?)\s+ago|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct"
                   r"|Nov|Dec)\w*\s+\d{4})")
def c4_feed(t, url=None):
    return True if len(C4_RX.findall(t)) >= 3 else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c4_feed  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 62. `DB-C5-001` · C5 Lists of keywords or links · drop · stage 30

1. **Disease:** C5 Lists of keywords or links. Pack `ind-hi-hplt`. Source: section C5 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-001"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c5(text):
    return bool(re.search("अधिकतम रेटिंग \\d+\\s*\nन्यूनतम स्कोर", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 63. `DB-C5-002` · C5 Lists of keywords or links · drop · stage 30

1. **Disease:** C5 Lists of keywords or links. Pack `ind-hi-hplt`. Source: section C5 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-002"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C5: generated rating trailers ("अधिकतम रेटिंग 5 / न्यूनतम स्कोर 4 / रेटिंग की संख्या ...") and hashtag clouds: drop
def medicine_c5(text):
    rating = re.search(r"अधिकतम रेटिंग\s*\d", text) and re.search(r"न्यूनतम स्कोर\s*\d", text)
    tags = len(re.findall(r"(?<!\w)#[^\s#]{2,}", text))
    return bool(rating) or tags >= 8


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 12 of 33 C5 documents; 1 other diseased documents touch...
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 64. `DB-C5-003` · C5 Lists of keywords or links · drop · stage 30

1. **Disease:** C5 Lists of keywords or links. Pack `ind-kn-sangraha-v`. Source: section C5 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-003"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def headline_list(t, min_lines=8, share=0.8):
    """C5: drop a document that is only a list: min_lines or more lines, and at least share of the text in short
    lines (100 characters or less) that do not end with a full stop, as in a list of headlines."""
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    if len(lines) < min_lines:
        return False
    short = [l for l in lines if len(l) <= 100 and not l.endswith(".")]
    return sum(map(len, short)) >= share * sum(map(len, lines))


def medicine_c5(text):
    """The C5 rule, under the name that the harm tests look for: True drops the document."""
    return headline_list(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 65. `DB-C5-004` · C5 Lists of keywords or links · drop · stage 30

1. **Disease:** C5 Lists of keywords or links. Pack `ind-mr-fw2`. Source: section C5 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-004"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c5(text):
    return re.sub(r'\n\s*(?:Tags|Keywords|टॅग्ज)\s*:.*$', '', text, flags=re.I)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 66. `DB-C5-005` · C5 Lists of keywords or links · drop · stage 30

1. **Disease:** C5 Lists of keywords or links. Pack `ind-ta-sangraha-v`. Source: section C5 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-005"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_c5(text):
    """True: drop the document."""
    return re.search(r"\A(?:[ \t]*[^\n]{1,150}?[!?][ \t]*\n+){3,}[ \t]*[^\n]{1,150}?[!?][ \t]*\n*\Z", text) is not None


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: drops 3 documents, all labelled C5; none labelled `clean`.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 67. `DB-C5-006` · C5 Lists of keywords or links · drop · stage 30

1. **Disease:** C5 Lists of keywords or links. Pack `ind-te-fw2`. Source: section C5 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-006"
CODE = "C5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_C5_C1_LINE = re.compile(r"""^\s*(?:
    (?:Also\s+[Rr]ead|Read\s+[Mm]ore|Don'?t\s+Miss!?|Just\s+In|News\s+Reels|More\s+Stories|Leave\s+a\s+Reply
      |View\s+this\s+post\s+on\s+Instagram|Sign\s+in|Follow\s+[Uu]s|Subscribe|Share\s+(?:on|this)
      |Image\s+Source|Disclaimer|Published\s+On|First\s+Publish\s+Date|Updated\s+Date|Tags?|TAGS)\b.*
  | (?:ఇది\s+కూడా\s+చదవండి|ఇవి\s+కూడా\s+చదవండి|ఇవీ\s+చదవండి|ఇదీ\s+చదవండి|ఇది\s+చూడండి|తాజా\s+వార్తలు
      |ట్రెండింగ్\s+వార్తలు|ఉత్పత్తి\s+ట్యాగ్లు|పోస్ట్\s+సమయం|వ్యాఖ్యను\s+పోస్ట్\s+చేయండి
      |మీ\s+అభిప్రాయాలను\s+కామెంట్|గమనిక:\s*ఈనాడు\.నెట్|\[\[సంబంధిత\s+కథనం\]\]).*
  | (?:మరిన్ని|ప్రకటన|g-ప్రకటన)(?:\s*-\s*[\w\s]{0,30})?
  | .*(?:Empowering\s+140\+\s+Indians|India\s+Herald\s+Group\s+of\s+Publishers|pic\.twitter\.com/|t\.co/\w).*
  | -?\s*\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}\s+[AP]M(?:\s+GMT)?.*
  | \w[\w\s.]{0,40},\s*News18,\s*\w+.*
)\s*$""", re.X)
def medicine_c5(t, url=None):
    cleaned = "\n".join(l for l in t.split("\n") if not _C5_C1_LINE.match(l))
    lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
    if not lines:
        return False
    short_no_punct = sum(1 for l in lines if len(l) < 60 and not re.search(r"[.!?:;।…\"'”’)\]]$", l))
    return True if (short_no_punct >= 14 and short_no_punct / len(lines) > 0.5) else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** own-pack real gold set (`ind-te-fw2_gold.csv`, 18 documents) and full Telugu real gold set (`telugu_gold.csv`, 50 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 27; 46 documents in the 31 Oct snapshot):
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 68. `DB-D4-001` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-bn-fw2`. Source: section D4 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-001"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_FUNC = re.compile('(?<![\u0980-\u09ff])(?:এবং|একটি)(?![\u0980-\u09ff])')

def medicine_d4(text):
    """Drop likely machine translation: native Bengali news writes numbers in Bengali digits and uses
    'এবং' / 'একটি' sparingly; English-to-Bengali MT keeps Latin digits and translates every 'and' / 'a'."""
    words = max(1, len(text.split()))
    latin_d = len(re.findall('[0-9]', text))
    bengali_d = len(re.findall('[০-৯]', text))
    if latin_d + bengali_d < 5 or latin_d / (latin_d + bengali_d) < 0.5:
        return False
    return 100 * len(_FUNC.findall(text)) / words >= 2.0


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 69. `DB-D4-002` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-bn-fw2`. Source: section D4 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(doc)`.

```python
RULE_ID = "DB-D4-002"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

from urllib.parse import urlparse

_BN_OK = {"bn.mtnews24.com", "bn.globalvoices.org", "bn.m.wikipedia.org", "bn.wikipedia.org",
          "bn.ekusherbangladesh.com.bd", "bn.jwtrubber.com", "bn.bettingonlinebd.net"}


def medicine_d4(doc):
    """Drop (True) a document whose URL host is a bn.* subdomain of a non-Bengali site."""
    host = urlparse(doc.get("url") or "").netloc.lower()
    return host.startswith("bn.") and host not in _BN_OK


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 70. `DB-D4-003` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-gu-fw2`. Source: section D4 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-003"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
from urllib.parse import urlparse

FOREIGN_TLD = {"de", "ch", "es", "fr", "it", "cn", "ru", "top", "world"}

def m4_d4(text, url=None):
    host = (urlparse(url or "").hostname or "").lower()
    bad = host.startswith("gu.") or host.rsplit(".", 1)[-1] in FOREIGN_TLD
    return (text, "drop" if bad else "keep")

def medicine_d4(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m4_d4(text, url)[1] == "drop"


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 71. `DB-D4-004` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-gu-fw2`. Source: section D4 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-D4-004"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

SANDWICH = re.compile(r"[઀-૿][a-z]{1,8}[઀-૿]")

def medicine(text):
    # Latin letters glued inside a Gujarati word: the translation is broken, drop the document.
    return None if SANDWICH.search(text) else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 4 of 12...
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 72. `DB-D4-005` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-hi-hplt`. Source: section D4 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-005"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_YEAR = re.compile(r"(?<![\d,.])1(?: 9 ?\d ?\d| ?9 \d ?\d| ?9 ?\d \d)(?![\d,.])")
_RU = re.compile(r"\b[a-z]{4,}(?:oy|yy|aya|ogo|ykh|nykh|iya)\b")


def medicine_d4(text):
    return bool(_YEAR.search(text) or _RU.search(text) or "डॉ।" in text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 73. `DB-D4-006` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-hi-hplt`. Source: section D4 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-006"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# D4: machine translation that left English words inside Hindi sentences: drop when it happens 3+ times
_D4 = re.compile(r"[ऀ-ॿ][ \t]+[a-z]{4,}(?:[ \t]+[a-z]{2,})*[ \t]+[ऀ-ॿ]|[ऀ-ॿ][a-z]{3,}\b|\b[a-z]{3,}[ऀ-ॿ]")


def medicine_d4(text):
    return len(_D4.findall(text)) >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 19 of 67 D4 documents; 10 other diseased documents touc...
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 74. `DB-D4-007` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-kn-sangraha-v`. Source: section D4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-007"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

NUM_PLACEHOLDER = re.compile("NUMX|XNUM|ಎಕ್ಸ್ಎನ್ಎಕ್ಸ್|ಎಮ್ಎಕ್ಸ್ಎಕ್ಸ್|ಎಮ್ಎಮ್ಎನ್ಎಕ್ಸ್|ಎಂಎನ್ಎಕ್ಸ್")
LONE_ENGLISH = re.compile("[ಀ-೿]+ (?:is|the|of|and|to|in|for|with|on|a|an|are|was) [ಀ-೿]+")


def mt_traces(t):
    """D4: drop a document with traces of a translation engine: the number placeholder of a known engine
    (XNUMX, written in Kannada letters as ಎಕ್ಸ್ಎನ್ಎಕ್ಸ್ or ಎಮ್ಎಮ್ಎನ್ಎಕ್ಸ್), or two or more English function words
    left alone between Kannada words."""
    return bool(NUM_PLACEHOLDER.search(t)) or len(LONE_ENGLISH.findall(t)) >= 2


def medicine_d4(text):
    """The D4 rule, under the name that the harm tests look for: True drops the document."""
    return mt_traces(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 75. `DB-D4-008` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-mr-sangraha-v`. Source: section D4 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_d4(text)`.

```python
RULE_ID = "DB-D4-008"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 43785419033933e9
    "43785419033933e9f960794254f99a82f58573597bb458a1ff6ece908ff5615e",
    # 4c7b3c1a1061d97f
    "4c7b3c1a1061d97f22cd98fc25efcc5121806199350f56eac5c3ab2ade99929f",
    # 61b2c25e9513730b
    "4d59a3a5a9bc1ec25f9d8534d1fc6be16eed665184b870b6781e3cfeeddccb80",
    "61b2c25e9513730b3f652488ad8f9f111f4181f78ec62bf01f78f5465e4effb6",
    # 6684bd791d877bc0
    "6684bd791d877bc04352f9688f6b82fb85fdf236095eb2fe2f7f45080382a626",
    # 787dd37a24269172
    "787dd37a2426917285649b89c3498c782ddff3c729e902df662fe61cb5916f0e",
    # 78d17bae5d29f865
    "78d17bae5d29f8654e70637ce32536f3fbf90f78c484cbe5bb4a2a9bf6f05646",
    # 7f79826d091b1834
    "7f79826d091b1834136bae3b13e8a9bcf5eb91fb7048454d58f860588f60c175",
    # 816e770dc45f85c5
    "816e770dc45f85c5b503878ef07c45ffe8403a0794e2955f0648ab7e003b49ee",
    "933d30ff5e07e29a42f4090600f9a6c9347c967931bdb7ce35ec2130dec0f97e",
    # 866b1853d8a9d95a
    "866b1853d8a9d95a9f3e5cfe1f57484891f138bcce185c57a6dc0aaa123117de",
    # 915caa7e4b7ded75
    "915caa7e4b7ded751b5e54860a842ff604380c51daaa9207c3f747d3251a2090",
    # 994056d70dd415f8
    "994056d70dd415f803bd61335fda5f6cb17b299070077e9e416d51b04d3ad016",
    # 9e41a5d56ac92089
    "9e41a5d56ac92089dae7eef899dd02ffa4d7290237855b1d112d85e74fe8c222",
    # 9ed1317a6abd1ce0
    "9ed1317a6abd1ce0aeb0579c3b451808e64bdf6a394289523c6b656e70b644dd",
    # a07ef1c92c0cceb3
    "a07ef1c92c0cceb3008efdbca6f2decde997fca77ee73c9d7f2394e83d735307",
    # a274c193c5e5f3ee
    "a274c193c5e5f3ee72858a9143927532090eb3469df2f5928bc12450eefa06a9",
    # c4cbdc3ab951c6b8
    "c4cbdc3ab951c6b8d78efc1e373e81c0e88b0abc159de384ee6209ef469ec12e",
    "d4baa996ec32d3d7b3427ce972d20a6a907e06a5a2975ea5cea7296a40119b77",
    # d0b76c2968e55e7d
    "741fb8dc1ff20269175f0bbc71a9dbd7eeea4208719bf6c0dabc728b54fb2b4c",
    "d0b76c2968e55e7dbd55218dfef5454a46e4071cf2f6016999489ae67049ea2b",
    # e977e6e5b6339831
    "a681d885fe07f9f18dcf20d1964de4615ad1c26a51522c6337ed9436fd54aa5c",
    "e977e6e5b63398319f54fe9da7cb72a0ea031b9bfd9cfb688efa69ecb965c315",
    # f0b421e314af77d6
    "f0b421e314af77d6649909e8ccf3db245e49bdc7a1f60665b202c20102e697b7",
    # f94044ff48697280
    "a9f684f8e34573b1abe36123e1831416e6fbf2d22124c63219b716b3019201bf",
    "f94044ff486972805edce8c630c643bb02ef18aa13e58f62a0af3947baa3498e",
})

def cure_d4(text):
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True  # Exclude/quarantine; retain provenance outside public output.
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **20 reviewed records excluded individually**; all other records stay unchanged for this rule. Contextual repairs are not covered.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 76. `DB-D4-009` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-sa-fw2`. Source: section D4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-009"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_D = "ऀ-ॿ"
_STEMS = ["जारी", "पीएम", "सीएम", "बयान", "मुताबिक", "दौरान", "हालांकि", "जरिये", "वायरल", "साझा", "कार्यवाही",
          "विडियो", "शूटिंग्", "माङ्गं", "दबाव", "सुनवायी"]

def medicine_d4(text):
    hits = sum(len(re.findall(f"(?<![{_D}]){s}", text)) for s in _STEMS)
    return hits >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 77. `DB-D4-010` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-sa-fw2`. Source: section D4 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-010"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

# Hindi loanwords and calques that machine translation from Hindi leaves in Sanskrit news prose (read in this pack)
D4_MARKERS = frozenset("""अक्टोबर् अनुसारं अन्तर्गतं इत्यस्मै उल्लेखनीयम् कुर्वन्तु। गतवर्षे घातिताः चलच्चित्रं नवदेहली। परिस्थितौ
पीएम पुलिस पुलिसैः बुधवासरे महत्त्वपूर्णं वर्धितः विडियो समर्थनं सम्पूर्णे सर्वकारेण सर्वाधिकं साझां
सामाजिकमाध्यमेषु""".split())
D4_MIN_MARKERS = 2
RE_D4_WORD = re.compile(r"[\u0900-\u097F]+")

def d4_machine_translated(text):
    """True when at least D4_MIN_MARKERS different markers occur as whole words."""
    return len(D4_MARKERS.intersection(RE_D4_WORD.findall(text))) >= D4_MIN_MARKERS

def medicine_d4(text):
    """Drop the document (return True) when d4_machine_translated finds it."""
    return d4_machine_translated(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 78. `DB-D4-011` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-te-fw2`. Source: section D4 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `d4_machine_translation(text)`.

```python
RULE_ID = "DB-D4-011"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

from urllib.parse import urlparse
WIKI = re.compile(r"^te\.(?:m\.)?wiki(?:pedia|source|books|quote|tionary|news)\.org$")
def d4_machine_translation(t, url=None):
    host = urlparse(url or "").netloc.lower()
    if host.startswith("te.") and not WIKI.match(host):
        return True
    marks = t.count("మరియు") + t.count("యొక్క")
    rate = 1000 * marks / max(1, len(re.findall(r"\S+", t)))
    return True if ((marks >= 6 or (marks >= 3 and "యొక్క" in t)) and rate > 15) else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = d4_machine_translation  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 79. `DB-D4-012` · D4 Bad machine translation · drop · stage 30

1. **Disease:** D4 Bad machine translation. Pack `ind-te-sangraha-s`. Source: section D4 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d4(text)`.

```python
RULE_ID = "DB-D4-012"
CODE = "D4"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d4(text):
    words = text.split()
    run = 1
    for a, b in zip(words, words[1:]):
        run = run + 1 if a == b else 1
        if run >= 8:
            return True
    if len(words) >= 200:
        top = max(words.count(w) for w in set(words) if len(w) > 2)
        return top / len(words) > 0.15
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_d4` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section D4 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 80. `DB-D5-001` · D5 Translationese · drop · stage 30

1. **Disease:** D5 Translationese. Pack `ind-te-sangraha-s`. Source: section D5 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d5(text)`.

```python
RULE_ID = "DB-D5-001"
CODE = "D5"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d5(text):
    words = len(text.split())
    n = text.count("యొక్క")
    return n >= 6 and 100 * n / words >= 2


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_d5` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section D5 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 81. `DB-F2-001` · F2 Benchmark leak · drop · stage 30

1. **Disease:** F2 Benchmark leak. Pack `ind-sa-fw2`. Source: section F2 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f2(text)`.

```python
RULE_ID = "DB-F2-001"
CODE = "F2"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

import os

_L = "ऀ-ॣ०-ॿ"
_W, _STEP, _MIN = 40, 20, 3
_INDEX = {}

def _windows():
    if not _INDEX:
        path = os.environ.get("ITIHASA_TEST_SN")
        if not path:
            raise RuntimeError("set ITIHASA_TEST_SN to the Itihasa test.sn.csv file")
        with open(path, encoding="utf-8") as f:
            for k, line in enumerate(f):
                n = re.sub(f"[^{_L}]", "", line)
                if len(n) < _W:
                    continue
                for j in range(0, len(n) - _W + 1, _STEP):
                    _INDEX.setdefault(n[j:j + _W], set()).add(k)
    return _INDEX

def medicine_f2(text):
    index = _windows()
    n = re.sub(f"[^{_L}]", "", text)
    hit = set()
    for j in range(len(n) - _W + 1):
        hit |= index.get(n[j:j + _W], set())
    return len(hit) >= _MIN


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F2 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 82. `DB-F3-001` · F3 Harmful content · drop · stage 30

1. **Disease:** F3 Harmful content. Pack `ind-bn-fw2`. Source: section F3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f3(text)`.

```python
RULE_ID = "DB-F3-001"
CODE = "F3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

_B = '\u0980-\u09ff'
_TERMS = re.compile(r'(?i)casino|betting|mostbet|888starz|1xbet|porn|xxx|sex\s*video|'
                    rf'(?<![{_B}])(?:ক্যাসিনো|বেটি\u0982|মোস্টবেট|বুকমেকার|পর্ন|সেক্স)(?![{_B}])')

def medicine_f3(text):
    """Drop gambling and pornography pages: 3 or more hits of the term list.
    Hate and extremist content is not caught by a word list; it goes to human review."""
    return len(_TERMS.findall(text)) >= 3


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 83. `DB-F3-002` · F3 Harmful content · drop · stage 30

1. **Disease:** F3 Harmful content. Pack `ind-bn-fw2`. Source: section F3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f3(text)`.

```python
RULE_ID = "DB-F3-002"
CODE = "F3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_F3_RX = re.compile(r"পর্ন|চোদা|ক্যাসিনো|বেটিং|বাজি ধর|জুয়া খেল|casino|betting|porn|xxx|sex video", re.I)


def medicine_f3(text):
    """Drop (True) when there are >= 4 hits and >= 1 hit per 600 characters."""
    n = len(_F3_RX.findall(text))
    return n >= 4 and n * 600 >= len(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS. The density rule keeps news about casino raids: `ce8a91b51a89e51a` has 2 hits in
5. **Side effects:** in the author's `medicine.md`, section F3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 84. `DB-F3-003` · F3 Harmful content · drop · stage 30

1. **Disease:** F3 Harmful content. Pack `ind-te-fw2`. Source: section F3 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `f3_harmful(text)`.

```python
RULE_ID = "DB-F3-003"
CODE = "F3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

F3_URL = re.compile(r"sex-?stor|(?<![a-z])sex(?![a-z])|porn|xxx|erotic|erotyczn|adult|phone-spy|spy-on|prize-?bond"
                    r"|satta|casino|betting", re.I)
F3_RX = re.compile(r"sex\s*stor|porn|xxx|\bnude\b|దెంగ|పూకు|మొడ్డ|బూతు\s*కథ|సెక్స్\s*కథ|prize\s*bond|satta\s*matka"
                   r"|betting\s*tips", re.I)
def f3_harmful(t, url=None):
    return True if (F3_URL.search(url or "") or len(F3_RX.findall(t)) >= 3) else False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = f3_harmful  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section F3 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 85. `DB-G1-011` · G1 Cut at the vowel sign · drop · stage 30

1. **Disease:** G1 Cut at the vowel sign. Pack `ind-kn-sangraha-v`. Source: section G1 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g1(text)`.

```python
RULE_ID = "DB-G1-011"
CODE = "G1"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

KN_CONS = set(range(0x0C95, 0x0CBA)) | {0x0CDE}         # consonants
KN_MATRA = set(range(0x0CBE, 0x0CCD))                   # dependent vowel signs
VIRAMA_CP, NUKTA_CP, ANUSVARA_CP, VISARGA_CP = 0x0CCD, 0x0CBC, 0x0C82, 0x0C83   # code points, not characters
LEN_MARKS = {0x0CD5, 0x0CD6}
VOWELS_BEFORE_YA = {0x0C85, 0x0C86, 0x0C8E}             # ಅ ಆ ಎ, as in ಆ್ಯಪ್
YA = 0x0CAF


def is_kn(c):
    return 0x0C80 <= ord(c) <= 0x0CFF


def broken_signs(t):
    """G1: offsets of a vowel sign, virama, nukta, anusvara or visarga that has no letter to sit on.

    ಆ್ಯ (vowel + virama + ಯ) is the standard spelling of the English "a" sound (ಆ್ಯಪ್) and is not counted.
    A visarga after a virama is a colon turned into a visarga (G4), not a broken sign.
    """
    out = []
    for i, ch in enumerate(t):
        o = ord(ch)
        p = ord(t[i - 1]) if i else 0
        nx = ord(t[i + 1]) if i + 1 < len(t) else 0
        if o == VIRAMA_CP and p in VOWELS_BEFORE_YA and nx == YA:
            continue
        if o in KN_MATRA or o == VIRAMA_CP or o == NUKTA_CP:
            if p not in KN_CONS and p != NUKTA_CP:
                out.append(i)
        elif o == ANUSVARA_CP:
            if not (i and is_kn(t[i - 1])) or p == VIRAMA_CP:
                out.append(i)
        elif o == VISARGA_CP:
            if not (i and is_kn(t[i - 1])):
                out.append(i)
        elif o in LEN_MARKS:
            if p not in (0x0CBF, 0x0CC6, 0x0CCA):
                out.append(i)
    return out


def heavy_broken_signs(t, min_count=3):
    """G1: drop a document with min_count or more vowel signs or viramas that have no letter to sit on."""
    return len(broken_signs(t)) >= min_count


def medicine_g1(text):
    """The G1 rule, under the name that the harm tests look for: True drops the document."""
    return heavy_broken_signs(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section G1 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 86. `DB-G3-001` · G3 Indic dropped by an English rule · drop · stage 30

1. **Disease:** G3 Indic dropped by an English rule. Pack `ind-sa-fw2`. Source: section G3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g3(text)`.

```python
RULE_ID = "DB-G3-001"
CODE = "G3"
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_NO = re.compile(r"॥\s*([०-९\d]+)\s*(?:॥|$)", re.M)
_DIG = str.maketrans("०१२३४५६७८९", "0123456789")

def medicine_g3(text):
    n = [int(x.translate(_DIG)) for x in _NO.findall(text)]
    if len(n) >= 3 and n[0] == 2 and 1 not in n and _NO.search(text).start() < 600:
        return True
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 15]
    if len(lines) < 15 or "॥" in text:
        return False
    half = sum(1 for l in lines if re.search(r"[^०-९\d\s]\s*।$", l))
    numbered = sum(1 for l in lines if re.search(r"[०-९\d]\s*।$", l))
    short = sorted(len(l) for l in lines)[len(lines) // 2] <= 50
    return numbered == 0 and short and half / len(lines) >= 0.8


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** drop. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section G3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 87. `DB-C1-001` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-bn-fw2`. Source: section C1 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-001"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

def _nk(p):
    # ড় ঢ় য় may be stored as one code point or as letter + nukta (U+09BC): match both.
    for one, two in (('\u09dc', '\u09a1\u09bc'), ('\u09dd', '\u09a2\u09bc'), ('\u09df', '\u09af\u09bc')):
        p = p.replace(two, one).replace(one, '(?:%s|%s)' % (one, two))
    return p

_START = re.compile(_nk(r"""^[\s\-–—#*>/]*(?:
    আর(?:ও|\u09cb|\u09cbও)\s*(?:পড়\u09c1ন|পড়তে\s*পারেন)|এছাড়\u09beও\s*পড়\u09c1ন|
    প্রকাশিত(?:\s*হয়\u09c7ছে)?\s*[:\u0983]|প্রকাশের\s*সময়\s*[:\u0983]|আপডেট\s*সময়|শেষ\s*আপডেট\s*[:\u0983]|
    বা\u0982লাদেশ\s*সময়\s*[:\u0983]|Published\s+on|Last\s+Updated\s+on|
    শেয়\u09beর\s*করুন|View\s+this\s+post\s+on\s+Instagram|A\s+post\s+shared\s+by|
    সর্বস্বত্ব\s*সংরক্ষিত|Powered\s+by\s|For\s+all\s+the\s+latest|Continue\s+Reading|
    ট্যাগ\s*[:\u0983]|Tags?\s*:|পোস্ট\s*ট্যাগ|হোয়\u09beটসঅ্যাপে\s*ফলো\s*করুন|
    প্রতিনিধি\s+প্রিন্ট\s+সংস্করণ|\[hupso\]
)""", ), re.X)
_WHOLE = re.compile(_nk(r"""^[\s\-–—#*>/]*(?:
    মন্তব্য\s*করুন|সম্পর্কিত\s*(?:খবর|নিউজ)|Related\s+News|Advertisement|বিজ্ঞাপন|
    সুচিপত্র|সূচিপত্র|পরিচ্ছেদসমূহ|Read\s+More|শীর্ষ\s*সংবাদ\s*[:\u0983]?|
    [\d০-৯,]+\s*(?:total\s+views.*|বার\s+(?:পড়\u09be\s+হয়\u09c7ছে|পঠিত))
)\s*$""", ), re.X)
_TWEET = re.compile(r"pic\.twitter\.com/|^\s*[—-]\s*[^\n]{1,60}\(@\w{1,15}\)\s+[A-Z][a-z]+\s+\d{1,2},\s+\d{4}\s*$")

def medicine_c1(text):
    """Delete whole lines that are page chrome. A line is deleted only if it is at most 200 characters long."""
    out = []
    for line in text.split('\n'):
        if len(line) <= 200 and (_START.match(line) or _WHOLE.match(line) or _TWEET.search(line)):
            continue
        out.append(line)
    return '\n'.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 88. `DB-C1-002` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-bn-fw2`. Source: section C1 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-002"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re

_C1_LINE = re.compile(
    r"^\s*(?:"
    r"(?:আরও|আরো) (?:পড়ুন|পড়তে পারেন)\s*[:ঃ]?.{0,80}|শেয়ার করুন\s*[:ঃ]?|মন্তব্য করুন|বিজ্ঞাপন|"
    r"(?:প্রতিনিধি )?প্রিন্ট সংস্করণ|সর্বশেষ|সর্বাধিক পঠিত|শীর্ষ সংবাদ\s*[:ঃ]?|সম্পর্কিত (?:নিউজ|খবর)|"
    r"সাবস্ক্রাইব করুন এবং সর্বশেষ খবর.*|আমাদের নিউজ চ্যানেল|.*ইউটিউব চ্যানেলে সাবস্ক্রাইব করুন|"
    r".*হোয়াটসঅ্যাপে ফলো করুন.*|এ বিভাগের সর্বাধিক পঠিত|বিস্তারিত (?:ভিডিওতে দেখুন|আরোও জানতে ক্লিক করুন)\s*[:ঃ]?|"
    r"View this post on Instagram|Read (?:More|Entire Article).{0,3}|Continue Reading.{0,3}|Highlights|"
    r"Powered by Froala Editor|For all the latest .* Click Here|[\d,]+ total views, \d+ views today|"
    r"- More Stories On :|\[hupso\]|#"
    r")\s*$", re.I)


def medicine_c1(text):
    """Delete whole furniture lines among the first 3 or last 6 lines."""
    lines = text.split("\n")
    n = len(lines)
    return "\n".join(l for k, l in enumerate(lines) if not ((k < 3 or k >= n - 6) and _C1_LINE.match(l)))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy gold 0 changed, 0 dropped of 314 (0 %). PASS.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 89. `DB-C1-003` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-gu-fw2`. Source: section C1 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-003"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

C1_LINE = re.compile(
    r"^[ \t]*(?:Copyright © .*DB Corp|This website follows the DNPA"
    r"|ગુજરાતી સમાચાર નો ખજાનો એટલે News18 ગુજરાતી|View this post on Instagram"
    r"|લેટેસ્ટ મનોરંજન, News અને Videos માટે પેજ લાઈક કરો"
    r"|\(?(?:નોંધ|નોધ|Disclaimers?)[ \t]*[:ઃ\-]"
    r"|(?:READ ALSO|MUST READ|આ પણ વાંચો)[ \t]*[:ઃ\-–]?).*\n?", re.M)
C1_TAG = re.compile(r"[ \t]*– Latest Gujarati News")
C1_DATELINE = re.compile(
    r"\A\s*(?:\((?:એજન્સી|અમારા પ્રતિનિધિ તરફથી|સંવાદદાતા દ્વારા)\)\s*)?"
    rf"(?:[{GU}]+(?: [{GU}]+)?\s*,\s*)?તા\.\s*[{GU_DIGIT}રપ0-9]{{1,2}}\s*[,:ઃ–\-]?\s*")

def m1_c1(text, url=None):
    new = C1_DATELINE.sub("", text, count=1)
    new = C1_LINE.sub("", new)
    return _fix(text, C1_TAG.sub("", new))

def medicine_c1(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m1_c1(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 90. `DB-C1-004` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-gu-fw2`. Source: section C1 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-C1-004"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

LINE_PATTERNS = [
    r"Copyright © .*All Rights Reserved\.?",
    r"This website follows the DNPA Code of Ethics\.?",
    r"ગુજરાતી સમાચાર નો ખજાનો એટલે News18 ગુજરાતી\..*",
    r"View this post on Instagram",
    r"Tags:.*",
    r"(આ પણ વાંચો|તમે આ પણ વાંચી શકો છો)\s*[:\-–].*",
    r"આ પણ વાંચો\s*:?",
    r"(Subscribe|Visit) Saurashtra Kranti.*",
    r"Read (About Weather|National News|Saurashtra Kranti E-Paper).*",
    r"For any News, Event coverage.*",
    r"आपके किसी भी प्रकार.*",
    r"આપના કે આપની સંસ્થાના.*",
    r"You Can Find us on Google Play store too.*",
    r"Android: https?://\S+",
    r"— .{1,60}\(@\w+\).*\d{4}",
    r".*pic\.twitter\.com/\S+",
    r"(Article Source|Courtesy) : .*",
    r"[A-Z][a-z]{2} \d{1,2}, ?\d{4}, \d{1,2}:\d{2} [AP]M IST",
    r"Tap to Read ➤",
    r"[\d,]+ Views, \d+",
    r"વધુ વાંચો",
    r"અમારી (દર નવી|અન્ય) પોસ્ટ.*",
    r"તમે આ લેખ “ગુજ્જુ ગુજરાતી”.*",
    r"આવા વધુ સમાચારો માટે નીચેની લિન્ક.*",
    r"Author: GujjuRocks Team.*",
    r"\(નોંધ[ –-].*\)",
    r"નોંધ: આ વેબસાઇટ પર.*",
    r"ઉપરના આર્ટીકલના તમામ.*",
    r"ગુજરાતના તમામ સ્થળે પ્રેસ પ્રતિનિધિ.*",
    '\\"વંદે માતરમ ,ભારત માતાકી જય\\"',
    r"જંગ એ ગુજરાત ના વેબ ન્યૂઝ પોર્ટલ માટે",
    r"માનદ પ્રતિનિધિ નિમવાના છે.*",
    r"ચહેરો\d+ કલાક પહેલા",
    r"- લિંક કૉપિ કરો",
    r"🌺આરતીસોની🌺",
    r"-આરતીસોની ©",
]
EXTRA = [
    r"\d{1,3} , \d{1,3}",
    r"લેટેસ્ટ મનોરંજન, News અને Videos માટે પેજ લાઈક કરો",
    r"Powered By .*",
    r"પોસ્ટનો સમય\s*:.*",
    r"સૌજન્ય\s*:?\s*(?:\n\s*)?દિવ્ય ભાસ્કર",
    r"ઇનપુટ્સ\s*:.*",
    r"જુઓ (?:આ )?વિડીયો",
    r"અમારી અન્ય પોસ્ટ પણ વાંચો\s*:?-?",
    r"સોશિયલ મીડિયા પ્લેટફોર્મ પર અમારી સાથે જોડાઓ",
    r"Visit Saurashtra Kranti Homepage here",
    r"Read About Weather here",
    r"(?:\.\.\. ?)?Read More",
    r"Team VTV.*",
]
LINE = re.compile(r"^\s*(?:" + "|".join(LINE_PATTERNS + EXTRA) + r")\s*$\n?", flags=re.M)
# headline line that is stored after the body, just before a final dateline such as "(એજન્સી) તા.૬"
TRAIL = re.compile(r"\n[^\n]+\n(?=\(?[^\n]{0,30}\)?[ ,]*તા\.? ?[\d૦-૯]+\s*$)")

def medicine(text):
    return TRAIL.sub("\n", LINE.sub("", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 147 of ...
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 91. `DB-C1-005` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-hi-fw2`. Source: section C1 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
2. **Medicine:** the author's code, unchanged. Main function: `strip_c1_lines(text)`.

```python
RULE_ID = "DB-C1-005"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2"  # packs it runs on
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_C1_LINE = re.compile(
    r"(?is)^\s*(?:"
    r"Ads\s+से\s+है\s+परेशान.*"
    r"|Download\s+Dainik\s+Bhaskar\s+App.*"
    r"|Read\s+the\s+latest\s+and\s+breaking\s+Hindi\s+news\s+on\s+\S+.*"
    r"|\*?Yearly\s+subscription\s+for\s+just\s+.*"
    r"|(?:Updated|First\s+published):?\s+.*\d{4}.*(?:IST|AM|PM).*"
    r"|Posted\s+By:\s*.{1,80}"
    r"|Advertisement\s*"
    r"|Don'?t\s+Miss!?"
    r"|Recover\s+your\s+password\.?"
    r"|A\s+password\s+will\s+be\s+e-mailed\s+to\s+you\.?"
    r"|(?:इसे|ये|यह)\s+भी\s+पढ़ें?\s*[:：]?\s*[–-]?\s*"
    r"|सामान्य\s+सूची\s+पर\s+लौटें.*"
    r"|Share\s+on\s+WhatsApp.*"
    r"|follow\s+us\b.*"
    r"|हम\s+(?:डाटा\s+संग्रह|विज्ञापन).{0,60}कुकी.*"
    r"|cookie\s+(?:policy|notice|banner).*"
    r"|बिना\s+Ads\s+खबरों.*"
    r")\s*$"
)

def strip_c1_lines(text: str) -> str:
    """Remove whole lines that match C1 site furniture; keep everything else."""
    kept = []
    for line in (text or "").splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if _C1_LINE.match(body):
            continue
        kept.append(line)
    return "".join(kept)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = strip_c1_lines  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule C1` (2026-10-31). Ran `strip_c1_lines`:
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 92. `DB-C1-006` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-hi-hplt`. Source: section C1 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-006"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_LINE = re.compile(r"^[ \t]*(?:ADVERTISEMENT|Advertisement|Share(?: this)?:|Read More…?)[ \t]*\n?", re.M)
_RELATED = re.compile(r"^[ \t]*(?:यह भी पढ़ें|इसे भी पढ़ें)\b.*\n?", re.M)
_TAIL = re.compile(r"^[ \t]*(?:No comments:|Post a Comment|कोई टिप्पणी नहीं:|एक टिप्पणी भेजें|Leave a Reply|"
                   r"एक उत्तर दें|More Stories|Read Next|Related Articles|Related Posts|Tags:|आवश्यक सूचना|"
                   r"डिस्क्लेमर|अन्य न्यूज़|\(For more news|अधिकतम रेटिंग \d)", re.M)


def medicine_c1(text):
    t = _LINE.sub("", text)
    t = _RELATED.sub("", t)
    m = _TAIL.search(t, int(len(t) * 0.6))  # comment forms, related lists and disclaimers only near the end
    if m:
        t = t[:m.start()].rstrip()
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 93. `DB-C1-007` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-hi-hplt`. Source: section C1 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-007"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C1: known template lines, removed only when the whole line is the template
_C1 = re.compile(
    r"^[ \t]*(?:"
    r"(?:यह|ये|इसे|इन्हें) भी (?:पढ़ें|पढ़े|देखें)\s*[:：\-–—]?.*"
    r"|\d+ Comments?'?s?|No comments|There are no comments|Add yours|Leave a comment|Comment Now"
    r"|Comments in this topic:|COMMENTS|टिप्पणियाँ|Post a Comment"
    r"|Share(?: This Post)?:?|शेयर करें|Advertisement|विज्ञापन"
    r"|Read More(?:\.\.\.|…)?|और पढ़ें"
    r"|About Post Author|Post Views:.*|Recent Posts|अन्य न्यूज़"
    r"|Reviews for:.*|\(For more news.*|\(SocialLY के साथ पाएं.*"
    r")[ \t]*(?:\n|$)",
    re.M,
)


def medicine_c1(text):
    return _C1.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 84 of 199 C1 documents; 1 other diseased documents touc...
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 94. `DB-C1-008` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-kn-fw2`. Source: section C1 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-008"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DAY = r"(?:0?[1-9]|[12][0-9]|3[01])"
TIME = r"(?:(?:0?[1-9]|1[0-2]):[0-5][0-9](?::[0-5][0-9])?\s+(?:AM|PM)|(?:[01]?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?)"
ZONE = r"(?:IST|UTC|GMT|[+-](?:[01][0-9]|2[0-3]):?[0-5][0-9])"
WEEKDAY = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
DATE = rf"(?:{WEEKDAY},\s*)?{MONTH}\.?\s+{DAY},\s*[0-9]{{4}},\s*{TIME}\s+(?:{ZONE}|\[{ZONE}\])"
MARKER = r"(?:First\s+Published|Last\s+(?:Modified|Updated)|Published|Updated)"
LOCAL_DATE = rf"(?:[\u0c80-\u0cff]+,\s*)?\d{{1,2}}\s+[\u0c80-\u0cff]+\s+\d{{4}}\s*\({TIME}\s+{ZONE}\)"
STAMP = re.compile(rf"{MARKER}(?:\s*:\s*|\s+)(?:{DATE}|{LOCAL_DATE})", re.I)
KANNADA_STAMP = re.compile(rf"(?:ಭಾನುವಾರ|ಸೋಮವಾರ|ಮಂಗಳವಾರ|ಬುಧವಾರ|ಗುರುವಾರ|ಶುಕ್ರವಾರ|ಶನಿವಾರ),\s*\d{{1,2}}\s+[\u0c80-\u0cff]+\s+\d{{4}}\s*\({TIME}\s+IST\)", re.I)
FOLLOW = re.compile(r"Please\s+follow\s+and\s+like\s+us\s*:?", re.I)

def medicine_c1(text, url=""):
    rows, spans, offset = text.splitlines(keepends=True), [], 0
    for i, line in enumerate(rows):
        body, label = line.strip(), line.strip().casefold()
        pair = (label == "just in" and i + 1 < len(rows)
                and rows[i + 1].strip().casefold() in {"don't miss!", "don’t miss!"})
        if (STAMP.fullmatch(body) or KANNADA_STAMP.fullmatch(body) or FOLLOW.fullmatch(body)
                or label in {"don't miss!", "don’t miss!"} or pair):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return remove_spans(text, spans)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 95. `DB-C1-009` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-kn-fw2`. Source: section C1 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-009"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib
import unicodedata

ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
BOILER = re.compile(r'Share on WhatsApp|Copyright|©|Leave a Reply|Team Udayavani|ಟಾಪ್ ನ್ಯೂಸ್'
                    r'|\d+\s*(days?|hours?|minutes?) ago|Read more|ಇನ್ನಷ್ಟು (ಓದಿ|ಸುದ್ದಿ)', re.I)
DASH_EN = re.compile(r'^[ \t]*[-–•][ \t]+[A-Za-z].*$', re.M)
DASH_BARE = re.compile(r'^[ \t]*[-–•][ \t]*\n[^\n]*\d+\s*days? ago[^\n]*$', re.M)
TEMPLATES = frozenset({          # site-template lines of ind-kn-fw2, found by medicines.py --templates
    '0c61b19cfb72c68a', '1523d8487cd4c792', '33f8a3e8d468bc8a', '4c304be013888589',
    '54181b210567e69b', '714f62bb0822152b', '86796ef8093339d7', '9236d07688fe64f6',
    '9c5d9390e0604341', 'b3f8b6881e5db8b7', 'bbce4efb0877577a', 'be298df70325f3f8',
    'cd54a6b665b3a745', 'e73bc5bae38473b3', 'ff2cc858983d961c',
})

def _protected(line):
    return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

def _key(line):
    return hashlib.blake2b(line.encode('utf-8'), digest_size=8).hexdigest()

def medicine_c1(text, templates=TEMPLATES):
    def cut(m):
        return m.group() if _protected(m.group()) else ''
    t = DASH_BARE.sub(cut, text)
    t = DASH_EN.sub(cut, t)

    def boiler(l):
        s = l.strip()
        return not _protected(s) and ((len(s) >= 3 and _key(s) in templates) or BOILER.search(s))
    return '\n'.join(l for l in t.split('\n') if not boiler(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 96. `DB-C1-010` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-kn-sangraha-s`. Source: section C1 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
2. **Medicine:** the author's code, unchanged. Main function: `m4_footer(text)`.

```python
RULE_ID = "DB-C1-010"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s"  # packs it runs on
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

FOOTER = re.compile(r"^(?:ಉಲ್ಲೇಖಗಳು|ಮೂಲಗಳು|ಟಿಪ್ಪಣಿಗಳು|ಗ್ರಂಥಸೂಚಿ|ಬಾಹ್ಯ ಸಂಪರ್ಕಗಳು|ಇದನ್ನೂ ನೋಡಿ)\.?[ \t]*$", re.M)
AD_LINE = re.compile(r"^[ \t]*ಜಾಹೀರಾತು[ \t]*\n?", re.M)
def m4_footer(s):
    m = FOOTER.search(s)
    if m and m.start() > len(s) // 2:
        s = s[: m.start()].rstrip()
    return AD_LINE.sub("", s)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m4_footer  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 5 of 359 changed. I read all 5. Two
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 97. `DB-C1-011` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-kn-sangraha-v`. Source: section C1 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-011"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e

import re

C1_LINE = re.compile(
    r"^\s*(?:Don't Miss!?|-\s*(?:News|Sports|Movies|Technology|Finance|Education|Lifestyle|Automobiles|Travel)\s.*"
    r"|-\s*\d+\s*(?:min|mins|hr|hrs)\s+ago\s.*|-\s*#\S.*"
    r"|ಇದನ್ನೂ ಓದಿ\s*[:ಃ].*|A post shared by .*"
    r"|ಪ್ರಜಾವಾಣಿ ಫೇಸ್‌?ಬುಕ್ ಪುಟವನ್ನು\s*ಫಾಲೋ ಮಾಡಿ.*|Oneindia ಬ್ರೇಕಿಂಗ್ ನ್ಯೂಸ್.*|ಹೊಸದಿಗಂತ ಡಿಜಿಟಲ್ ಡೆಸ್ಕ್"
    r"|The views expressed in comments published .*|Thanks For Reading!?|Like this:|Forgot your password\?"
    r"|To Start receiving timely alerts.*|Trending Topics\s*:?|(?:Home|ಮುಖಪುಟ)\s*[›»].*"
    r"|Posted on \w+ \d{1,2}, \d{4} by .*|(?=.{0,120}$).*(?:ಶೇರ್|ಲೈಕ್) ಮಾಡಿ[.!]?)\s*$")


def strip_boilerplate(t):
    """C1: remove whole boilerplate lines: Oneindia link blocks ('Don't Miss!', '- News ...', '- 2 hrs ago ...',
    '- #tag ...'), 'ಇದನ್ನೂ ಓದಿ:' (also read), follow/share/like prompts, desk lines, comment policies, breadcrumbs
    and embed lines."""
    return "\n".join(l for l in t.split("\n") if not C1_LINE.match(l))


def medicine_c1(text):
    """The C1 rule, under the name that the harm tests look for: returns the fixed text."""
    return strip_boilerplate(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 98. `DB-C1-012` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-mr-sangraha-v`. Source: section C1 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_c1(text)`.

```python
RULE_ID = "DB-C1-012"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import re

_C1_LINE = re.compile(
    r"^\s*(?:"
    r"हे\s*ही\s*वाचा\s*[:ः]?.*"
    r"|हेही\s*वाचा\s*[:ः]?.*"
    r"|हे\s*देखील\s*वाचा\s*[:ः]?.*"
    r"|Read\s+Also\s*[:\-]?.*"
    r"|Keep\s+Reading\s*[:\-]?.*"
    r"|Forgot\s+your\s+password\??\s*.*"
    r"|Home\s*/\s*Marathi\s*"
    r"|Get\s+Latest\s+Marathi\s+News.*"
    r"|साम\s+आता\s+सर्व\s+सोशल\s+मीडिया.*"
    r")\s*$",
    flags=re.IGNORECASE,
)

def cure_c1(text):
    lines = text.splitlines(keepends=True)
    return "".join(
        line for line in lines
        if not _C1_LINE.fullmatch(line.rstrip("\r\n"))
    )


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Verify independently that the nar...
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 99. `DB-C1-013` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-sa-fw2`. Source: section C1 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-013"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_LINES = [r"^(Menu|Home|Newer Post|Older Post|Gallery|BASPS|marquee|Technical Details|BACK TO TOP)$",
    r"^(Read Also|Read More|Leave a Reply|Click Here|Archives|ReplyDelete|Reply|Delete|Share|Tweet|Email This|BlogThis!)$",
    r"^(Labels?|Categories|Posted by|Source):", r"Did you see any mistake/variation", r"Digitized by Google",
    r"Since you are not logged in", r"^% (Site access|Language|Text title|File name|Location|Author|Transliterated by|Proofread by|Description|Latest update|Send corrections)",
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), \w+ \d{1,2}, \d{4}$", r"^\d{1,2}:\d\d [AP]M$",
    r"^\|← ", r"→\|$", r"^इतर .*पश्यतु\s*[।|]?$", r"^\[(सम्पाद्यताम्|सम्पादयतु|सम्पादन)\]$", r"^— .*\(@\w+\) \w+ \d{1,2}, \d{4}$",
    r"^(सामग्री पर जाएँ|मुख्य मेन्यू|साइडबार पर जाएँ|छुपाएँ|ऊपर जाएँ|अधिक जानें|क्रियाएँ|उपकरण)$",
    r"^(ऋग्वेद|अथर्ववेद|यजुर्वेद|सामवेद) में .* संदर्भ मिले$", r"Copyright|©|All rights reserved",
    r"हम उम्मीद करते हैं आपको", r"^इसे भी पढ़ें"]
_RX = re.compile("|".join(f"(?:{p})" for p in _LINES), re.I)
_EDIT = re.compile(r" ?\[(सम्पाद्यताम्|सम्पादयतु|सम्पादन)\]")

def medicine_c1(text):
    lines = [l for l in text.split("\n") if not _RX.search(l.strip())]
    if len(lines) >= 2 and lines[-1].strip() == "श्रीः" and lines[-2].rstrip().endswith("॥"):
        lines.pop()
    return _EDIT.sub("", "\n".join(lines))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 100. `DB-C1-014` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-sa-fw2`. Source: section C1 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-014"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

DEVA = r"ऀ-ॿ꣠-ꣿ᳐-᳿"
MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
def _lf(text): return text.replace("\r\n", "\n")
RE_EDITLINK = re.compile(r"\[(?:सम्पादन|संपादन|edit|सम्पादयतु|सम्पाद्यताम्)\]")
RE_BLOGGER_TAIL = re.compile(r"\nat\n\d{1,2}:\d{2} [AP]M\nNewer Post\nOlder Post\nHome\s*$")
RE_ARCHIVES_TAIL = re.compile(r"\n\s*Archives\n(?:[A-Z][a-z]+ \d{4}\n)*Categories\s*$")
RE_DSBC_HEAD = re.compile(r"^Technical Details\n[A-Za-z]\n", re.M)
RE_NEWS_MENU = re.compile(r"\AMenu\nHome\n(?:[^\n]*\n){0,40}?marquee\n")
RE_NEWS_TAIL = re.compile(r"(?:\n[ \t]*(?:सम्प्रति वार्ताः|इति वार्ताः|विश्वतोमुखम्)[ \t]*)+\s*$")
RE_SIMPLEHELP_HEAD = re.compile(rf"\A[A-Za-z][^\n]{{0,120}}: नमस्कार दोस्तों,[^\n]*\n(?:[^\n{DEVA}]*\n)*")
RE_HINDUPAD_HEAD = re.compile(rf"\A[^\n]{{1,80}} in (?:Hindi|Sanskrit|English|Tamil|Telugu|Kannada|Malayalam), Lyrics of [^\n]*\n(?:[^\n{DEVA}]*\n)*")
RE_SPIRITUAL_SIG = re.compile(r"^Subscribe on Youtube: The Spiritual Talks[ \t]*$", re.M)
RE_SPIRITUAL_TITLE = re.compile(r"\A[^\n]*\|[^\n]*\|[^\n]*\|[^\n]*\n")
C1_LINE_PATTERNS = [
    rf"{DAYS}, {MONTHS} \d{{1,2}}, \d{{4}}",
    r"Posted by .{0,80}", r"Labels?: .{0,200}", r"at \d{1,2}:\d{2} [AP]M", r"\d{1,2}:\d{2} [AP]M",
    r"Newer Posts?", r"Older Posts?", r"Post a Comment", r"No comments?:?", r"Email This", r"BlogThis!",
    r"Share to (?:Twitter|Facebook|Pinterest)", r"Subscribe to:.{0,40}", r"Powered by Blogger\.?",
    r"Did you see any mistake/variation in the content above\?.{0,200}",
    r"इतर .{0,60}(?:स्तोत्राणि|स्तोत्रं|स्तोत्रम्|नामावलयः|सूक्तानि|कवचानि) पश्यतु ।",
    r"% (?:Text title|File name|itxtitle|engtitle|Category|Location|Sublocation|Texttype|Author|Language|Subject|"
    r"Transliterated by|Proofread by|Translated by|Description-comments|Indexextra|Latest update|Send corrections to|"
    r"Site access|Description|Acknowledge-Permission|Source|Notes|Date|Comment)\s*:.*",
    r"(?:From [^\n]{0,100} )?(?:Encoded|Proofread|Transliterated|Encoded and proofread) by .{0,120}",
    r"[A-Za-z][\w.-]{0,40} at [\w.-]+\.[a-z]{2,6}",
    r"(?i:back to(?: top)?)", r"Please send corrections to.{0,200}", r"Technical Details",
    r"The rights of the materials herein are as indicated by the source\(s\) cited\..{0,400}",
    r"Subscribe to our newsletter.{0,200}",
    r"Inspiration: .{0,120}", r"These stories are written to .{0,300}",
    r"Jump to navigation ?Jump to search", r"Jump to navigation", r"Jump to search",
    r"एतत् पृष्ठम् (?:अपरिष्कृतम्|परिष्कृतम्|परिशोधितम्|प्रमाणीकृतम्) अस्ति",
    r"पृष्ठम्:[^\n]{1,120}\.(?:djvu|pdf)/[0-9०-९]{1,5}",
    r"Retrieved from .{0,300}", r".{0,300}इत्यस्मात् पुनः प्राप्तम्",
    r"Toggle limited content width",
    r"Table of Contents",
    r"[^\n]{0,80} Lyrics in (?:Marathi|Hindi|English|Tamil|Telugu|Kannada|Malayalam|Gujarati|Bengali|Oriya|Punjabi|Sanskrit):?",
    r"Categories: .{0,200}", r"Tags: .{0,200}",
    r"Leave a (?:Reply|Comment)",
    r"Download pdf", r"Back",
    r"Read Also", r"Read Also: .{0,200}",
    r"(?:हम )?उम्मीद करते हैं (?:कि |आपको ).{0,400}",
    r"\|[^|\n]{1,120}\|\|[^|\n]{0,200}\|",
    r"\|[A-Za-z0-9][^|\n]{0,120}\|",
    r"A painting by .{0,120}",
    r"Subscribe on Youtube: .{0,60}", r"Follow on Pinterest: .{0,60}", r"For any query contact on:?",
    r"Be a part of this Spiritual family .{0,160}", r"For more divine and soulful .{0,160}", r"For Spiritual quotes .{0,160}",
    r"यहाँ क्लिक करें", r"अगर आप और प्रैक्टिस सेट्स .{0,160}",
    r"[—–-]{2,}",
    r"Read [Mm]ore", r"Click here to .{0,80}",
    r"Download (?:the )?\S+ App\b.{0,80}",
    rf"— .{{1,80}} \(@\w{{1,30}}\) {MONTHS} \d{{1,2}}, \d{{4}}",
    r"\*{3,}",
    r"Share", r"Share this:?", r"Like this:?", r"Related", r"Archives", r"Categories",
    r"marquee", r"Statutary Warning-?",
    r"संस्कृतपठनेन बुद्धि[:ः] वर्धते इति मतिमुन्नीय गवेषका[:ः]॥",
    r"व्यावहारिकप्रयोगैः संस्कृतं राष्ट्रियभाषा भवितव्या - डॉ\. बलदेवानन्दसागरः।",
    r"संस्कृतेन सर्वदा व्यवहर्तुं प्रयतत - जगद्गुरु भारतीतीर्थस्वामिनः",
    rf"-\s?डा\.\s?[{DEVA}][^\n]{{0,30}}",
]
RE_C1_LINE = re.compile(r"[ \t]*(?:" + "|".join(f"(?:{p})" for p in C1_LINE_PATTERNS) + r")[ \t]*")
def medicine_c1(text):
    """C1: remove site chrome — known header/footer blocks, MediaWiki edit links, and whole lines equal to a chrome string."""
    if not text: return text
    src = _lf(text)
    out = RE_NEWS_MENU.sub("", src)
    out = RE_DSBC_HEAD.sub("", out)
    out = RE_SIMPLEHELP_HEAD.sub("", out)
    out = RE_HINDUPAD_HEAD.sub("", out)
    if RE_SPIRITUAL_SIG.search(out): out = RE_SPIRITUAL_TITLE.sub("", out)
    out = RE_BLOGGER_TAIL.sub("", out)
    out = RE_ARCHIVES_TAIL.sub("", out)
    out = RE_NEWS_TAIL.sub("", out)
    if RE_EDITLINK.search(out):
        out = "\n".join(RE_EDITLINK.sub("", l) for l in out.split("\n") if RE_EDITLINK.sub("", l).strip() or not RE_EDITLINK.search(l))
    out = "\n".join(l for l in out.split("\n") if not RE_C1_LINE.fullmatch(l))
    if out == src: return text
    return out.strip("\n")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 101. `DB-C1-015` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-ta-sangraha-v`. Source: section C1 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c1(text)`.

```python
RULE_ID = "DB-C1-015"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

_TICKER = "Finance|Travel|Education|Technology|News|Automobiles|Movies|Lifestyle|Sports"  # oneindia "Don't Miss!" block
_C1_LINE = re.compile(r"(?m)^[ \t]*(?:Sign up to receive our newsletter in your inbox every day!|Don't Miss!"
                      rf"|- (?:\d+ (?:mins?|hrs?) ago|{_TICKER}) .*"
                      r"|உலகம் முதல் உள்ளூர் வரை இன்றைய முக்கிய செய்திகள்.*|நியூஸ்18 தமிழ்நாடு தொலைக்காட்சியை.*"
                      r"|(?:Also Read|Also see)\s*:.*|இதையும் (?:படிங்க|பாருங்க).*)[ \t]*(?:\n|$)")

def medicine_c1(text):
    return _C1_LINE.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 50 documents, all labelled C1; none of the 153 `clean` documents.
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 102. `DB-C1-016` · C1 Boilerplate · fix · stage 35

1. **Disease:** C1 Boilerplate. Pack `ind-te-fw2`. Source: section C1 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `c1_boilerplate(text)`.

```python
RULE_ID = "DB-C1-016"
CODE = "C1"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

C1_LINE = re.compile(r"""^\s*(?:
    (?:Also\s+[Rr]ead|Read\s+[Mm]ore|Don'?t\s+Miss!?|Just\s+In|News\s+Reels|More\s+Stories|Leave\s+a\s+Reply
      |View\s+this\s+post\s+on\s+Instagram|Sign\s+in|Follow\s+[Uu]s|Subscribe|Share\s+(?:on|this)
      |Image\s+Source|Disclaimer|Published\s+On|First\s+Publish\s+Date|Updated\s+Date|Tags?|TAGS)\b.*
  | (?:ఇది\s+కూడా\s+చదవండి|ఇవి\s+కూడా\s+చదవండి|ఇవీ\s+చదవండి|ఇదీ\s+చదవండి|ఇది\s+చూడండి|తాజా\s+వార్తలు
      |ట్రెండింగ్\s+వార్తలు|ఉత్పత్తి\s+ట్యాగ్లు|పోస్ట్\s+సమయం|వ్యాఖ్యను\s+పోస్ట్\s+చేయండి
      |మీ\s+అభిప్రాయాలను\s+కామెంట్|గమనిక:\s*ఈనాడు\.నెట్|\[\[సంబంధిత\s+కథనం\]\]).*
  | (?:మరిన్ని|ప్రకటన|g-ప్రకటన)(?:\s*-\s*[\w\s]{0,30})?
  | .*(?:Empowering\s+140\+\s+Indians|India\s+Herald\s+Group\s+of\s+Publishers|pic\.twitter\.com/|t\.co/\w).*
  | -?\s*\d{1,2}\s+\w{3}\s+\d{4}\s+\d{1,2}:\d{2}\s+[AP]M(?:\s+GMT)?.*
  | \w[\w\s.]{0,40},\s*News18,\s*\w+.*
)\s*$""", re.X)
def c1_boilerplate(t, url=None):
    return "\n".join(l for l in t.split("\n") if not C1_LINE.match(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c1_boilerplate  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C1 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 103. `DB-C2-001` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-bn-fw2`. Source: section C2 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-001"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c2(text):
    """Delete the second and later copies of a line of 40 or more characters."""
    seen, out = set(), []
    for line in text.split('\n'):
        key = line.strip()
        if len(key) >= 40:
            if key in seen:
                continue
            seen.add(key)
        out.append(line)
    return '\n'.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 104. `DB-C2-002` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-bn-fw2`. Source: section C2 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-002"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

from collections import Counter


def medicine_c2(text):
    """Keep the first two copies of a line longer than 8 characters; delete later copies."""
    seen, out = Counter(), []
    for l in text.split("\n"):
        k = l.strip()
        seen[k] += 1
        if len(k) > 8 and seen[k] > 2:
            continue
        out.append(l)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 1 changed, 0 dropped of 314 (0.32 %). PASS.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 105. `DB-C2-003` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-gu-fw2`. Source: section C2 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-C2-003"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine(text):
    seen, out = set(), []
    for line in text.split("\n"):
        key = line.strip()
        if len(key) > 15 and not key.endswith((",", "…")):   # keep poem refrains
            if key in seen:
                continue
            seen.add(key)
        out.append(line)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 12 of 1...
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 106. `DB-C2-004` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-hi-hplt`. Source: section C2 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-004"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c2(text):
    t = text
    for s in dict.fromkeys(re.findall("[^\u0964?!\n]{60,}[\u0964?!]", text)):
        first = t.find(s)
        if first >= 0 and t.find(s, first + len(s)) >= 0:
            t = t[:first + len(s)] + t[first + len(s):].replace(s, "")
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. Both audits: 0 documents. **PASS**
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 107. `DB-C2-005` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-hi-hplt`. Source: section C2 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-005"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C2: a line of 40+ characters that repeats an earlier line exactly; the first copy stays
def medicine_c2(text):
    seen, out = set(), []
    for line in text.split("\n"):
        key = line.strip()
        if len(key) >= 40:
            if key in seen:
                continue
            seen.add(key)
        out.append(line)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 6 of 40 C2 documents; 6 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 108. `DB-C2-006` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-kn-fw2`. Source: section C2 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-006"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

def medicine_c2(text, url=""):
    if "```" in text or "~~~" in text:
        return text
    lines = [s.strip() for s in text.splitlines() if s.strip()]
    if len(lines) >= 6 and sum(len(s) < 60 and not s.endswith((".", "!", "?")) for s in lines) * 2 > len(lines):
        return text
    units = set(lines)
    units.update(m.group().strip() for m in re.finditer(r"[^.!?\r\n]+(?:[.!?]+|(?=[\r\n]|$))", text))
    units = [s for s in units if len(s) >= 80 and len(s.split()) >= 8 and s.endswith((".", "!", "?"))
             and not s.startswith(('"', "'", "‘", "“", ">")) and not protected(s)
             and not re.match(r"[—–-]\s+.*\(@[A-Za-z0-9_]+\)", s)]
    spans = []
    for unit in sorted(units, key=lambda s: (-len(s), s)):
        cursor = text.find(unit) + len(unit)
        while (a := text.find(unit, cursor)) >= 0:
            b = a + len(unit)
            if not (a and (text[a - 1].isalnum() or unicodedata.category(text[a - 1]).startswith("M"))):
                spans.append((a, b))
            cursor = b
    return remove_spans(text, spans)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 109. `DB-C2-007` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-kn-fw2`. Source: section C2 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-007"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata
from collections import Counter

ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
END = re.compile(r'[.?!।॥"”\')]\s*$')   # a line that ends a sentence

def _protected(line):
    return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

def _short(l):
    return 0 < len(l) < 60 and not END.search(l)

def _verse(t):
    ls = [l.strip() for l in t.split('\n') if l.strip()]
    return len(ls) >= 6 and sum(map(_short, ls)) / len(ls) > 0.5

def medicine_c2(text, min_chars=30, times=2):
    if _verse(text):
        return text
    c = Counter(l.strip() for l in text.split('\n') if len(l.strip()) >= min_chars)
    rep = {l for l, n in c.items() if n >= times}
    seen, out = set(), []
    for l in text.split('\n'):
        s = l.strip()
        if s in rep and not _protected(s):
            if s in seen:
                continue
            seen.add(s)
        out.append(l)
    return '\n'.join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 110. `DB-C2-008` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-kn-sangraha-v`. Source: section C2 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-008"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def dedupe_lines(t, min_len=30):
    """C2: keep the first copy of a line that is repeated word for word (lines of min_len characters or more)."""
    seen, out = set(), []
    for l in t.split("\n"):
        k = l.strip()
        if len(k) >= min_len and k in seen:
            continue
        seen.add(k); out.append(l)
    return "\n".join(out)


def medicine_c2(text):
    """The C2 rule, under the name that the harm tests look for: returns the fixed text."""
    return dedupe_lines(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 111. `DB-C2-009` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-mr-fw2`. Source: section C2 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-009"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c2(text):
    seen = set()
    return '\n'.join(line for line in text.splitlines() if not (line.strip() and line.strip() in seen or seen.add(line.strip())))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 112. `DB-C2-010` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-mr-sangraha-v`. Source: section C2 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_c2(text)`.

```python
RULE_ID = "DB-C2-010"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

def cure_c2(text):
    seed_len, min_repeat, search_limit = 48, 80, 1600
    if len(text) < min_repeat * 2:
        return text
    seed = text[:seed_len]
    second = text.find(seed, seed_len, min(len(text), search_limit))
    if second < 0:
        return text
    matched = 0
    max_match = min(second, len(text) - second)
    while matched < max_match and text[matched] == text[second + matched]:
        matched += 1
    if matched < min_repeat:
        return text
    return text[:second] + text[second + matched:]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Verify on C2-positive documents t...
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 113. `DB-C2-011` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-sa-fw2`. Source: section C2 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-011"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

import collections
def _lf(text): return text.replace("\r\n", "\n")
RE_C2_ALLOW = re.compile(r"उवाच|ऊचुः|इति|--$|—$|[।॥]$")
C2_MIN_REPEATS, C2_MAX_LEN = 5, 40
def medicine_c2(text):
    """C2: collapse runs of identical consecutive lines (whitespace-trimmed comparison); remove a short non-exempt line
    that repeats >= 5 times anywhere in the document."""
    if not text: return text
    src = _lf(text)
    out, prev = [], None
    for l in src.split("\n"):
        s = l.strip()
        if s and s == prev and not RE_C2_ALLOW.search(s): continue
        out.append(l); prev = s or None
    cnt = collections.Counter(l.strip() for l in out if l.strip())
    chrome = {s for s, k in cnt.items() if k >= C2_MIN_REPEATS and len(s) < C2_MAX_LEN and not RE_C2_ALLOW.search(s)}
    if chrome: out = [l for l in out if l.strip() not in chrome]
    new = "\n".join(out)
    return text if new == src else new


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 114. `DB-C2-012` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-ta-sangraha-v`. Source: section C2 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c2(text)`.

```python
RULE_ID = "DB-C2-012"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def medicine_c2(text):
    return re.sub(r"(?ms)^([ \t]*([^\n]{180,}?)[ \t]*$.*?)\2", r"\1", text)  # a later copy of a long line goes


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 3 documents, all labelled C2; none labelled `clean`.
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 115. `DB-C2-013` · C2 Repeated lines · fix · stage 35

1. **Disease:** C2 Repeated lines. Pack `ind-te-fw2`. Source: section C2 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `c2_repeats(text)`.

```python
RULE_ID = "DB-C2-013"
CODE = "C2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

from collections import Counter
def c2_repeats(t, url=None):
    lines = t.split("\n"); n = Counter(l.strip() for l in lines if len(l.strip()) >= 15)
    seen, out = set(), []
    for l in lines:
        s = l.strip()
        if n.get(s, 0) >= 2:
            if s in seen: continue
            seen.add(s)
        out.append(l)
    return "\n".join(out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c2_repeats  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C2 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 116. `DB-C3-005` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-bn-fw2`. Source: section C3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-005"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re


def medicine_c3(text):
    """Cut a broken last sentence back to the last । ? ! ৷ (credit lines are left alone)."""
    s = text.rstrip()
    if not s:
        return text
    last = s.split("\n")[-1]
    if not re.match("[ঀ-৿]", s[-1]) or len(last) <= 60 or re.search(r"[:ঃ/\-–—]", last[-40:]):
        return text
    cut = max(s.rfind(c) for c in "।?!৷")
    return s[:cut + 1] if cut > 0 else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 117. `DB-C3-006` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-hi-fw2`. Source: section C3 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-006"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2"  # packs it runs on
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_TERM_END = re.compile(r'[।!?.…"\'”’)\]]\s*$')

def _flag_c3_truncated(text: str) -> bool:
    """True if the document does not end on a sentence terminator (label hint only)."""
    t = (text or "").rstrip()
    if not t:
        return False
    return _TERM_END.search(t) is None

def medicine_c3(text: str) -> str:
    """Automatic medicine: keep text. Soft C3 is label/fix; do not mass-drop open endings."""
    return text or ""


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `ind-hi-fw2_gold.csv` (**234** docs, post-#161). Tool: `harm_test_indic.py --rule C3` (2026-10-31). Automatic `medicine_c3` keeps text (label/fix; no mass drop of open endings):
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 118. `DB-C3-007` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-hi-hplt`. Source: section C3 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-007"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# C3: a document cut at the start ("…" before the first word) or ending in a "[…]" teaser cut: remove that line
def medicine_c3(text):
    lines = text.split("\n")
    if len(lines) > 2 and re.match(r"^\s*(?:…|\.\.\.)\s*[\u0900-\u097f]", lines[0]):
        lines = lines[1:]
    if len(lines) > 2 and re.search(r"\[(?:…|\.\.\.)\]\s*$", lines[-1]):
        lines = lines[:-1]
    return "\n".join(lines)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 8 of 20 C3 documents; 3 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 119. `DB-C3-008` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-kn-sangraha-s`. Source: section C3 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
2. **Medicine:** the author's code, unchanged. Main function: `m5_dangling_intro(text)`.

```python
RULE_ID = "DB-C3-008"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s"  # packs it runs on
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

def m5_dangling_intro(s):
    body = s.rstrip()
    if not body.endswith(("ಃ", ":")):
        return s
    cut = max(body.rfind("\n"), body.rfind(". ") + 1)
    return body[:cut].rstrip() + "\n" if cut > 0 else True


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = m5_dangling_intro  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS. My clean rows: 3 of 359 changed (`523fee1068dc3fa9`,
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 120. `DB-C3-009` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-kn-sangraha-v`. Source: section C3 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-009"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

SENTENCE_END = set(".?!।॥|\"'”’)»…:ಃ")


def cut_unfinished_end(t, min_line=40):
    """C3: when the last line is prose (min_line characters or more) that stops without a sentence end, cut it
    back to its last full stop, or remove the line when it has none."""
    s = t.rstrip()
    if not s or s[-1] in SENTENCE_END or s[-1].isdigit():
        return t
    last = s.split("\n")[-1]
    if len(last) < min_line:
        return t
    cut = max(last.rfind(c) for c in ".?!।")
    return (s[: len(s) - len(last)] + (last[: cut + 1] if cut >= 0 else "")).rstrip()


def medicine_c3(text):
    """The C3 rule, under the name that the harm tests look for: returns the fixed text."""
    return cut_unfinished_end(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 121. `DB-C3-010` · C3 Truncated document · fix+drop · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-mr-sangraha-v`. Source: section C3 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_c3(text)`.

```python
RULE_ID = "DB-C3-010"
CODE = "C3"
ACTION = "fix+drop"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 0ad004d5deb1e7fe
    "0ad004d5deb1e7fece97aa9806c12904aa8f3443a9784e6ad8192fe37ccdc50a",
    # 10cfc7c874a1bb29
    "10cfc7c874a1bb29938183dcf35cdeb6b9bd36cb47b721b46cea9429e60552c9",
    "395b9f4527f05f508da2f9ea26395d99bec57bd7a46934165c4dad8eb2e04ce3",
})

def cure_c3(text):
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True  # Exclude/quarantine; retain provenance outside public output.
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **2 reviewed records excluded individually**; all other records stay unchanged for this rule. Contextual repairs are not covered.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 122. `DB-C3-011` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-sa-fw2`. Source: section C3 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-011"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

def _lf(text): return text.replace("\r\n", "\n")
TERMINAL = set("।॥.!?\"”'’)]}»…") | set("0123456789०१२३४५६७८९")
C3_MAX_LEN, C3_MAX_WORDS = 200, 8
RE_C3_PROTECT = re.compile(r"^इत(?:ि|्य)")
def medicine_c3(text):
    """C3: drop one dangling short last line without terminal punctuation when the line before it is closed."""
    if not text: return text
    src = _lf(text)
    lines = src.split("\n")
    idx = [i for i, l in enumerate(lines) if l.strip()]
    if len(idx) < 2: return text
    k, j = idx[-1], idx[-2]
    last, prev = lines[k].strip(), lines[j].strip()
    if (len(last) >= C3_MAX_LEN or len(last.split()) > C3_MAX_WORDS or last[-1] in TERMINAL or prev[-1] not in TERMINAL
            or RE_C3_PROTECT.match(last)):
        return text
    return "\n".join(lines[:k] + lines[k + 1:])


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 123. `DB-C3-012` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-ta-sangraha-v`. Source: section C3 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-012"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463

import re

def _cut_sentence(line):
    e = max(line.rfind(c) for c in ".!?…")
    return line[:e + 1]  # e = -1: no sentence end, so the whole line goes

def medicine_c3(text):
    return re.sub(r"(?m)^[^\n]{80,}(?<=[\u0B80-\u0BFFA-Za-z,])\s*\Z", lambda m: _cut_sentence(m[0].rstrip()), text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 22 documents, none labelled `clean`. Of the 6 changed documents
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 124. `DB-C3-013` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-te-fw2`. Source: section C3 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `c3_teaser(text)`.

```python
RULE_ID = "DB-C3-013"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def c3_teaser(t, url=None):
    paras = t.rstrip().split("\n")
    if len(paras) > 1 and re.search(r"\[(?:…|\.\.\.)\]\s*$", paras[-1]):
        return "\n".join(paras[:-1]).rstrip()
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = c3_teaser  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 125. `DB-C3-014` · C3 Truncated document · fix · stage 35

1. **Disease:** C3 Truncated document. Pack `ind-te-sangraha-s`. Source: section C3 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c3(text)`.

```python
RULE_ID = "DB-C3-014"
CODE = "C3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c3(text):
    body = text.rstrip()
    tail = text[len(body):]
    cut = body.rfind("\n")
    if cut > 0 and body[cut + 1:].endswith(("ః", ":")):
        return body[:cut] + tail
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_c3` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section C3 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 126. `DB-C4-007` · C4 Two documents joined · fix · stage 35

1. **Disease:** C4 Two documents joined. Pack `ind-gu-fw2`. Source: section C4 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-007"
CODE = "C4"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU = "\u0A80-\u0AFF"                          # Gujarati block
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9

C4_DATELINE = re.compile(
    r"^\s*(?:\((?:એજન્સી|અમારા પ્રતિનિધિ તરફથી|સંવાદદાતા દ્વારા)\)\s*)?"
    rf"[{GU}]+(?: [{GU}]+)?\s*,\s*તા\.\s*[{GU_DIGIT}રપ0-9]{{1,2}}\s*$", re.M)
C4_MARK = re.compile(r"^\s*(?:READ ALSO|MUST READ)\s*[:\-–]?", re.M)
C4_BODY = re.compile(r"^(?!\s*[-•]).{200,}$", re.M)

def m8_c4(text, url=None, min_part=300, min_body=200):
    cuts = [m.start() for m in C4_DATELINE.finditer(text)
            if m.start() >= min_part and len(text) - m.end() >= min_body]
    m = C4_MARK.search(text)
    if m and C4_BODY.search(text, m.end()):
        cuts.append(m.start())
    if not cuts:
        return (text, "keep")
    bounds = [0] + sorted(set(cuts)) + [len(text)]
    parts = [text[a:b].strip() for a, b in zip(bounds, bounds[1:])]
    return ([p for p in parts if p], "split")

def medicine_c4(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    parts, action = m8_c4(text, url)
    return "\n\n".join(parts) if action == "split" else text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 127. `DB-C4-008` · C4 Two documents joined · fix · stage 35

1. **Disease:** C4 Two documents joined. Pack `ind-kn-sangraha-v`. Source: section C4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-008"
CODE = "C4"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def latin_share(s):
    k = sum(1 for c in s if "ಀ" <= c <= "೿")
    a = sum(1 for c in s if c.isascii() and c.isalpha())
    return a / (k + a) if k + a else 0.0


def cut_english_tail(t, min_chars=200):
    """C4: remove an English block (min_chars or more, lines over 90% Latin letters) joined to the end of a
    Kannada text, such as the English source story."""
    lines = t.split("\n")
    i = len(lines)
    while i > 0 and (not lines[i - 1].strip() or latin_share(lines[i - 1]) > 0.9):
        i -= 1
    head, tail = "\n".join(lines[:i]), "\n".join(lines[i:])
    if len(tail.strip()) >= min_chars and len(head.strip()) >= 200 and latin_share(head) < 0.3:
        return head.rstrip()
    return t


def medicine_c4(text):
    """The C4 rule, under the name that the harm tests look for: returns the fixed text."""
    return cut_english_tail(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 128. `DB-C4-009` · C4 Two documents joined · fix+drop · stage 35

1. **Disease:** C4 Two documents joined. Pack `ind-mr-sangraha-v`. Source: section C4 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_c4(text)`.

```python
RULE_ID = "DB-C4-009"
CODE = "C4"
ACTION = "fix+drop"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 802ea4e0038fae55
    "802ea4e0038fae55fba668aca47d3f7c546b15564d109bc8afb500c5ad78fd02",
    # 9910e11f3461f5d0
    "9910e11f3461f5d09f7abfb46cfca489b7bb5209d507d963dab976ff55e3b112",
    "e5d935b539d7724761ec3e96fbfe365fece60f1423ef62aee339f1a913889716",
    # a3a467b4dcb9c51b
    "a3a467b4dcb9c51b0a2112852ad9b31a8b9f895f21d207c9a3dac6114617ca02",
    "dbc9e19bc50ab161305d9e57e012f471e5250092c7dc4eef472245eb3ecb86e8",
    # d89a364142de1d38
    "c71c2ca6277898aaf1416e32d9f280c46f4a98293b21601bf23103e5f0536aa9",
    "d89a364142de1d38711026940c0f096e45d2276cb062773651c866d4998228d7",
})

def cure_c4(text):
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True  # Exclude/quarantine; retain provenance outside public output.
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **4 reviewed records excluded individually**; all other records stay unchanged for this rule. Contextual repairs are not covered.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 129. `DB-C4-010` · C4 Two documents joined · fix · stage 35

1. **Disease:** C4 Two documents joined. Pack `ind-sa-fw2`. Source: section C4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-010"
CODE = "C4"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_c4(text):
    def cut(m):
        start = text.rfind("\n", 0, m.start()) + 1
        return m.group(1) + ("\n\n" if m.start() - start >= 60 else "")
    return re.sub("([।!?])(?=[ऀ-ॿ][ऀ-ॿ ]{1,40}\\s?>)", cut, text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 130. `DB-C4-011` · C4 Two documents joined · keep · stage 35

1. **Disease:** C4 Two documents joined. Pack `ind-sa-fw2`. Source: section C4 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c4(text)`.

```python
RULE_ID = "DB-C4-011"
CODE = "C4"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

DEVA = r"ऀ-ॿ꣠-ꣿ᳐-᳿"
MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
def _lf(text): return text.replace("\r\n", "\n")
RE_DATELINE = re.compile(rf"^[{DEVA}][^\n>]{{1,24}}[ \t]?>[ \t]*\S", re.M)
RE_POST_DATE = re.compile(rf"^{DAYS}, {MONTHS} \d{{1,2}}, \d{{4}}$")
RE_DEVA = re.compile(rf"[{DEVA}]")
def detect_joined(text):
    """C4 detector (no automated action). Run it on the ORIGINAL text, before C1, which removes the date headers and menu it
    relies on. True when: >= 2 news datelines; or >= 2 Blogger post-date headers (archive page); or one post-date header
    that follows Devanagari sentences (marquee items joined to the post)."""
    if not text: return False
    if len(RE_DATELINE.findall(text)) >= 2: return True
    lines = [l.strip() for l in _lf(text).split("\n")]
    dates = [i for i, l in enumerate(lines) if RE_POST_DATE.match(l)]
    if len(dates) >= 2: return True
    if dates and any(RE_DEVA.search(x) and x[-1] in "।॥" for x in lines[:dates[0]] if x): return True
    return False

def medicine_c4(text):
    return text    # action none: the detector `detect_joined` reports; splitting is a corpus-time action


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C4 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 131. `DB-C5-007` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-bn-fw2`. Source: section C5 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-007"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

def _is_headline(line):
    s = line.strip()
    return (s.startswith(('- ', '• ', '* ')) and len(s) <= 120 and len(s.split()) >= 5
            and not s.endswith(('।', '?', '!', '.', ':')))

def medicine_c5(text):
    """Delete runs of 5 or more consecutive bullet lines that look like headlines: at least 4 words after
    the bullet, at most 120 characters, no sentence-final punctuation (related-news tickers)."""
    lines = text.split('\n')
    keep = [True] * len(lines)
    i = 0
    while i < len(lines):
        j = i
        while j < len(lines) and _is_headline(lines[j]):
            j += 1
        if j - i >= 5:
            for k in range(i, j):
                keep[k] = False
        i = max(j, i + 1)
    return '\n'.join(l for l, k in zip(lines, keep) if k)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 132. `DB-C5-008` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-bn-fw2`. Source: section C5 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-008"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48

import re
from collections import Counter


def _c5_stuffed(line):
    parts = [p.strip() for p in re.split(r"[,،]", line) if p.strip()]
    if len(parts) < 6 or sum(len(p.split()) for p in parts) > 6 * len(parts):
        return False
    c = Counter(b for p in parts for b in {" ".join(x) for x in zip(p.split(), p.split()[1:])})
    return bool(c) and c.most_common(1)[0][1] >= 0.5 * len(parts)


def medicine_c5(text):
    """Delete lines of >= 6 short comma pieces where one two-word phrase is in >= half of them."""
    return "\n".join(l for l in text.split("\n") if not _c5_stuffed(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS. **The 5.10 % is not this rule:** an earlier
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 133. `DB-C5-009` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-gu-fw2`. Source: section C5 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-009"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

C5_LINE = re.compile(r"^\s*(?:Tags\s*:|Android\s*:|iOS\s*:).*\n?|^\s*https?://\S+\s*\n?", re.M)

def m9_c5(text, url=None):
    return _fix(text, C5_LINE.sub("", text))

def medicine_c5(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m9_c5(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 134. `DB-C5-010` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-gu-fw2`. Source: section C5 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-C5-010"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

def medicine(text):
    keep = []
    for line in text.split("\n"):
        s = line.strip()
        latin = len(re.findall("[A-Za-z]", s))
        letters = max(1, len(re.sub(r"\W", "", s)))
        tags = s.startswith("Tags:") and (s.count(",") >= 2 or len(s.split()) >= 8)
        word_list = (len(s.split(",")) >= 5 and latin > 0.7 * letters
                     and not re.search(r"[:\d]", s) and not s.endswith("."))
        if not (tags or word_list):
            keep.append(line)
    return "\n".join(keep)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 18 of 2...
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 135. `DB-C5-011` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-kn-fw2`. Source: section C5 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-011"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re
import unicodedata

def protected(text):
    return any(c in "\u200c\u200d" or unicodedata.decomposition(c).startswith("<") for c in text)

def remove_spans(text, spans):
    out = list(text)
    for a, b in spans:
        if not protected(text[a:b]):
            out[a:b] = [""] * (b - a)  # Keep source indices stable, even for overlaps.
    return "".join(out)

NAV = re.compile(r"(?mi)^[ \t]*(?:Just In[ \t]*\r?\n)?[ \t]*Don['’]t Miss![ \t]*\r?\n(?P<links>(?:[ \t]*-[ \t]+[A-Za-z][^\r\n]*(?:\r?\n|$)){2,})")
TAG = r"#[ \t]*[^\W\d_][\w\u0c80-\u0cff\u200c\u200d]*"
TAG_CLOUD = re.compile(rf"[ \t]*(?:{TAG}[ \t]*){{2,}}")

def medicine_c5(text, url=""):
    spans = [(m.start("links"), m.end("links")) for m in NAV.finditer(text)]
    offset = 0
    for line in text.splitlines(keepends=True):
        if TAG_CLOUD.fullmatch(line.rstrip("\r\n")):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    return remove_spans(text, spans)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 136. `DB-C5-012` · C5 Lists of keywords or links · fix+drop · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-kn-fw2`. Source: section C5 of `diagnosis/submissions/ind-kn-fw2/keshavamurali/medicine.md`, PR #47 at `8158532`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-012"
CODE = "C5"
ACTION = "fix+drop"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "keshavamurali"  # PR #47 at 8158532
import re  # added by Data B: harm_test_indic.py gives every block `re`

import unicodedata

ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
END = re.compile(r'[.?!।॥"”\')]\s*$')   # a line that ends a sentence
SIGNAL = re.compile(r'\d+\s*(days?|hours?|minutes?|mins?) ago|ಇನ್ನಷ್ಟು|Read more|Tag results'
                    r'|https?://|www\.|\.com\b|\|', re.I)

def _protected(line):
    return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

def _short(l):
    return 0 < len(l) < 60 and not END.search(l)

def medicine_c5(text):
    lines = text.split('\n')
    idx = [i for i, l in enumerate(lines) if l.strip()]      # non-empty lines, original positions
    ls = [lines[i].strip() for i in idx]
    sig = [bool(SIGNAL.search(l)) for l in ls]
    if len(ls) >= 5 and sum(map(_short, ls)) / len(ls) > 0.6 and sum(sig) / len(ls) >= 0.3:
        return True
    drop, run = set(), []
    for k in range(len(ls) + 1):
        if k < len(ls) and (_short(ls[k]) or sig[k]):
            run.append(k)
        else:
            if len(run) >= 3 and sum(sig[j] for j in run) >= 2:
                drop.update(idx[j] for j in run if not _protected(ls[j]))
            run = []
    return '\n'.join(l for i, l in enumerate(lines) if i not in drop)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #47).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 137. `DB-C5-013` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-mr-sangraha-v`. Source: section C5 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_c5(text)`.

```python
RULE_ID = "DB-C5-013"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import re

_C5_TAG_LINE = re.compile(
    r"^\s*(?:Tags?|Keywords?|कीवर्ड)\s*[:：]\s*\S.*$",
    flags=re.IGNORECASE,
)

def cure_c5(text):
    return "".join(
        line for line in text.splitlines(keepends=True)
        if not _C5_TAG_LINE.fullmatch(line.rstrip("\r\n"))
    )


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). The narrow tag-line rule does not...
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 138. `DB-C5-014` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-sa-fw2`. Source: section C5 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-014"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_LINK = re.compile(r"Click Here\s*\|?$|^https?://\S+$", re.I)

def medicine_c5(text):
    return "\n".join(l for l in text.split("\n") if not _LINK.search(l.strip()))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 139. `DB-C5-015` · C5 Lists of keywords or links · fix · stage 35

1. **Disease:** C5 Lists of keywords or links. Pack `ind-sa-fw2`. Source: section C5 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_c5(text)`.

```python
RULE_ID = "DB-C5-015"
CODE = "C5"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

def _lf(text): return text.replace("\r\n", "\n")
RE_C5_TAGLINE = re.compile(r"\s*(?:Tags?|Labels?|Categories|Category|Filed under|Keywords?|Topics?)\s*:.*|\s*(?:Tags|Categories)\s*")
RE_C5_URL_LINE = re.compile(r"\s*(?:https?://|www\.)\S+\s*")
RE_C5_SEP = re.compile(r"\s*[,|]\s*")
RE_C5_SENTENCE = re.compile(r"[।॥.!?]")
C5_MIN_TOKENS, C5_MAX_TOKEN_CHARS, C5_MAX_TOKEN_WORDS = 6, 30, 3
def _is_list_line(s):
    """A comma- or pipe-separated run of >= 6 short tokens with no sentence punctuation."""
    if not s or RE_C5_SENTENCE.search(s): return False
    toks = [t for t in RE_C5_SEP.split(s) if t]
    return len(toks) >= C5_MIN_TOKENS and all(len(t) <= C5_MAX_TOKEN_CHARS and len(t.split()) <= C5_MAX_TOKEN_WORDS for t in toks)
def medicine_c5(text):
    """C5: remove tag/label lines, bare URL lines and token-list lines; unchanged if more than half the lines are lists."""
    if not text: return text
    src = _lf(text)
    lines = src.split("\n")
    hit = [bool(RE_C5_TAGLINE.fullmatch(l) or RE_C5_URL_LINE.fullmatch(l) or _is_list_line(l.strip())) for l in lines]
    n_hit, n_nonempty = sum(hit), sum(1 for l in lines if l.strip())
    if not n_hit or n_hit * 2 > n_nonempty: return text
    return "\n".join(l for l, h in zip(lines, hit) if not h)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_c5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section C5 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 140. `DB-D2-001` · D2 Romanised Indic · fix · stage 35

1. **Disease:** D2 Romanised Indic. Pack `ind-hi-hplt`. Source: section D2 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d2(text)`.

```python
RULE_ID = "DB-D2-001"
CODE = "D2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_ROMAN_HI = {"kya", "kaise", "kaisa", "kaun", "kare", "karen", "hai", "hain", "ka", "ke", "ki", "ko", "mein", "liye",
             "hota", "hoti", "hote", "kaha", "kab", "aur", "bhi", "nahi", "wala", "wali"}


def medicine_d2(text):
    kept = []
    for line in text.split("\n"):
        words = {w.lower() for w in re.findall("[A-Za-z]+", line)}
        ascii_only = not re.search("[^\x00-\x7f\u2018\u2019\u201C\u201D\u2026]", line)
        if line.strip() and len(line) <= 120 and ascii_only and len(words & _ROMAN_HI) >= 2:
            continue  # a romanised Hindi heading or SEO title
        kept.append(line)
    return "\n".join(kept)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section D2 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 141. `DB-D2-002` · D2 Romanised Indic · fix · stage 35

1. **Disease:** D2 Romanised Indic. Pack `ind-sa-fw2`. Source: section D2 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d2(text)`.

```python
RULE_ID = "DB-D2-002"
CODE = "D2"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d2(text):
    def roman(line):
        letters = [c for c in line if c.isalpha()]
        if len(line.strip()) < 25 or len(letters) < 10:
            return False
        lat = sum(1 for c in letters if c.isascii() or 0xC0 <= ord(c) <= 0x24F or 0x1E00 <= ord(c) <= 0x1EFF)
        return lat / len(letters) > 0.6 and bool(re.search(r"[āīūṛṝḷṃḥṅñṭḍṇśṣ]", line))
    return "\n".join(l for l in text.split("\n") if not roman(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D2 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 142. `DB-D3-001` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-bn-fw2`. Source: section D3 of `diagnosis/submissions/ind-bn-fw2/AditeyaAItronics/medicine.md`, PR #64 at `840d13d`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-001"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "AditeyaAItronics"  # PR #64 at 840d13d

import re

def medicine_d3(text):
    """Mixed language is natural in Bengali writing, so it is not cleaned. Only a document that is mostly
    English (more than 40% of its letters are Latin) is dropped from the Bengali pool."""
    latin = len(re.findall('[A-Za-z]', text))
    bengali = len(re.findall('[\u0980-\u09ff]', text))
    return latin + bengali > 0 and latin / (latin + bengali) > 0.40


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** gold set of 238 documents (ind-bn-fw2 238), medicine.md sha256 93e459d0b451; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #64).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 143. `DB-D3-002` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-bn-fw2`. Source: section D3 of `diagnosis/submissions/ind-bn-fw2/sohamniyogi/medicine.md`, PR #138 at `8a50c48`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-002"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"ben_Beng"}
ORIGIN = "ind-bn-fw2"  # packs it runs on
SOURCE = "ind-bn-fw2"  # pack whose medicine this came from
AUTHOR = "sohamniyogi"  # PR #138 at 8a50c48
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d3(text):
    """Keep the document unchanged: D3 is labelled, not cleaned."""
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-bn-fw2` only.
4. **Harm test (as the author reports it):** official gold 0 / 238 (0 %), PASS. The rule changes no document by construction.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #138).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 144. `DB-D3-003` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-gu-fw2`. Source: section D3 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-003"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re

def m2_d3(text, url=None):
    return (text, "keep")

def medicine_d3(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m2_d3(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 145. `DB-D3-004` · D3 Mixed language · fix · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-gu-fw2`. Source: section D3 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-D3-004"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

GU = re.compile(r"[઀-૿]")
LAT = re.compile(r"[A-Za-z]")

def medicine(text):
    # Keep a line unless it is English-only and long.
    return "\n".join(l for l in text.split("\n")
                     if GU.search(l) or len(LAT.findall(l)) < 25)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 97 of 2...
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 146. `DB-D3-005` · D3 Mixed language · fix · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-hi-fw2`. Source: section D3 of `diagnosis/submissions/ind-hi-fw2/raj-harit-v2/medicine.md`, PR #8 at `8250130`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-005"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-fw2"  # packs it runs on
SOURCE = "ind-hi-fw2"  # pack whose medicine this came from
AUTHOR = "raj-harit-v2"  # PR #8 at 8250130

import re

_DEVA = re.compile(r"[\u0900-\u097F]")
_LATIN_WORD = re.compile(r"\b[A-Za-z]{3,}\b")

def _flag_d3_mixed(text: str, min_deva: int = 40, min_latin_words: int = 8) -> bool:
    """True if doc looks like natural HI-EN mix (for labeling only; not a drop)."""
    if not text:
        return False
    return len(_DEVA.findall(text)) >= min_deva and len(_LATIN_WORD.findall(text)) >= min_latin_words

def medicine_d3(text: str) -> str:
    """Automatic medicine: keep text. D3 is label/fix; True would mean drop in harm_test_indic."""
    return text or ""


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-fw2` only.
4. **Harm test (as the author reports it):** Data B gold `teams/02-data-b/gold/ind-hi-fw2_gold.csv` (**234** docs, post-#161 rebuild). Tool: `harm_test_indic.py --rule D3` (2026-10-31; allow ≤ max(1, 1%) ≈ 2.34). Automatic medicine `medicine_d3` keeps text (label-only):
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #8).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 147. `DB-D3-006` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-hi-hplt`. Source: section D3 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-006"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def _d3_latin_words(text):
    """Latin words of 3+ letters that sit between Devanagari words: the D3 tag, kept as a note on the document."""
    return re.findall("(?<=[\u0900-\u097F] )[A-Za-z]{3,}(?=[ ,.]*[\u0900-\u097F])", text)


def medicine_d3(text):
    return False  # tag only: the text is kept as it is


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**. A rule that removed or translated these words would have changed 13 of the 69 gold documents (19%) when the gold set was 69 documents and fail.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 148. `DB-D3-007` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-hi-hplt`. Source: section D3 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-007"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# D3: natural Hindi-English mixing is labelled, not cured
def medicine_d3(text):
    return False


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 0 of 13 D3 documents; 0 other diseased documents touche...
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 149. `DB-D3-008` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-kn-sangraha-s`. Source: section D3 of `diagnosis/submissions/ind-kn-sangraha-s/millermuttu/medicine.md`, PR #104 at `74dd2df`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-008"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-s"  # packs it runs on
SOURCE = "ind-kn-sangraha-s"  # pack whose medicine this came from
AUTHOR = "millermuttu"  # PR #104 at 74dd2df
import re  # added by Data B: harm_test_indic.py gives every block `re`

LETTER = re.compile(r"[^\W\d_]", re.U)
NOT_KN_LATIN = re.compile(r"[^\W\d_a-zA-Zಀ-೿]", re.U)
def m6_foreign_ratio(s):
    n = len(LETTER.findall(s))
    return len(NOT_KN_LATIN.findall(s)) / n if n else 0.0
def medicine_d3(s):
    return s  # keep the text; m6_foreign_ratio is the measure

def effect(fn, text):
    out = fn(text)
    return "drop" if out is True else ("change" if out != text else "same")


def main(pack, gold_csv, labels_csv):
    docs = {r["doc_id"]: r["text"] for r in pq.read_table(pack, columns=["doc_id", "text"]).to_pylist()}
    gold = [r["doc_id"] for r in csv.DictReader(open(gold_csv, encoding="utf-8"))]
    gold = [g for g in gold if g in docs]
    labels = list(csv.DictReader(open(labels_csv, encoding="utf-8")))
    clean = [r["doc_id"] for r in labels if r["verdict"] == "clean"]
    print(f"pack {len(docs)} docs, gold in pack {len(gold)}, my clean rows {len(clean)}")
    print("med disease | gold changed dropped | my-clean changed dropped | labelled docs touched | pack touched")
    medicines = [("M1", "B2", m1_tags), ("M2", "B3", m2_ghost), ("M3", "A6", m3_half_translated),
                 ("M4", "C1", m4_footer), ("M5", "C3", m5_dangling_intro)]
    limit = max(1, 0.01 * len(gold))  # 1% of the gold set or 1 document, whichever is more
    for name, code, fn in medicines:
        g = [effect(fn, docs[i]) for i in gold]
        c = [effect(fn, docs[i]) for i in clean]
        sick = [r["doc_id"] for r in labels if code in r["diseases"].split(";")]
        hit = sum(effect(fn, docs[i]) != "same" for i in sick)
        allp = sum(effect(fn, t) != "same" for t in docs.values())
        verdict = "PASS" if (g.count("change") + g.count("drop")) <= limit else "FAIL"
        print(f"{name}  {code}  | {g.count('change'):3d} {g.count('drop'):3d} {verdict} | "
              f"{c.count('change'):3d} {c.count('drop'):3d} | {hit}/{len(sick)} | {allp}")
    sick = [r["doc_id"] for r in labels if "D3" in r["diseases"].split(";")]
    print("M6  D3  | no text change; foreign-letter ratio of D3 docs:",
          sorted(round(m6_foreign_ratio(docs[i]), 3) for i in sick))


def selftest():
    assert m1_tags("ಅ <ಐ. ಡಿ. 1> ಬ") == "ಅ ಬ"
    assert m1_tags("ಅ<ಬಿ. ಆರ್.>ಬ") == "ಅ\nಬ"
    assert m1_tags("<> </Â>x") == " x"
    assert m1_tags("2 < 3 > 1") == "2 < 3 > 1"  # a comparison is not a tag
    assert m2_ghost("ಅ<unk>ಬ") == "ಅಬ"
    assert m3_half_translated("(i.ಇ. ಪಳೆಯುಳಿಕೆ)") == "(ಅಂದರೆ ಪಳೆಯುಳಿಕೆ)"
    assert m4_footer("ಪಠ್ಯ " * 20 + "\nಉಲ್ಲೇಖಗಳು.\nಮೂಲಗಳು") == ("ಪಠ್ಯ " * 20).rstrip()
    assert m5_dangling_intro("ಒಂದು.\nಅವು ಹೀಗಿವೆಃ") == "ಒಂದು.\n"
    assert m5_dangling_intro("ಒಂದು. ಅವು ಹೀಗಿವೆಃ") == "ಒಂದು.\n"
    assert m5_dangling_intro("ಅವು ಹೀಗಿವೆಃ") is True
    assert m5_dangling_intro("ಒಂದು.") == "ಒಂದು."


if __name__ == "__main__":
    selftest()
    if len(sys.argv) < 4:
        sys.exit("usage: python3 medicine_run.py PACK.parquet GOLD.csv labels.csv")
    main(*sys.argv[1:4])


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-kn-sangraha-s` only.
4. **Harm test (as the author reports it):** gold 0 changed, 0 dropped of 27. PASS (the rule keeps every text).
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #104).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 150. `DB-D3-009` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-kn-sangraha-v`. Source: section D3 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-009"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

def keep_mixed(t):
    """D3: no medicine. Kannada-English mixing is natural; the brief says label it, do not judge it."""
    return t


def medicine_d3(text):
    """The D3 rule, under the name that the harm tests look for: returns the text unchanged."""
    return keep_mixed(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 151. `DB-D3-010` · D3 Mixed language · fix · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-mr-fw2`. Source: section D3 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-010"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d3(text):
    return re.sub(r'\n\s*(?:This News has been Retrieved from RSS|Previous Article|Next Article).*$', '', text, flags=re.I | re.DOTALL)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 152. `DB-D3-011` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-mr-sangraha-v`. Source: section D3 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_d3(text)`.

```python
RULE_ID = "DB-D3-011"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

def cure_d3(text):
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Because this is an intentional no...
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 153. `DB-D3-012` · D3 Mixed language · fix · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-sa-fw2`. Source: section D3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-012"
CODE = "D3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_HIN = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने को से का की के भी यह वह कि जो आप हम साथ वाले रहे रही".split())
_ANCHOR = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने साथ वाले रहे रही".split())
_C = "क-हक़-य़"

def _lang(line):
    letters = [c for c in line if c.isalpha()]
    if len(line.strip()) < 25 or len(letters) < 10:
        return "short"
    lat = sum(1 for c in letters if c.isascii() or 0xC0 <= ord(c) <= 0x24F or 0x1E00 <= ord(c) <= 0x1EFF)
    dev = sum(1 for c in letters if "ऀ" <= c <= "ॿ")
    if lat / len(letters) > 0.6:
        return "san_Latn" if re.search(r"[āīūṛṝḷṃḥṅñṭḍṇśṣ]", line) else "eng"
    if dev / len(letters) > 0.6:
        w = re.findall("[ऀ-ॿ]+", line)
        obl = lambda x: x.endswith("ों") and len(re.findall(f"[{_C}](?!्)", x)) >= 2
        h = sum(1 for x in w if x in _HIN or obl(x))
        a = sum(1 for x in w if x in _ANCHOR or obl(x))
        if a >= 1 and h >= 2 and h / max(1, len(w)) >= 0.15:
            return "hin"
    return "san"

def medicine_d3(text):
    return "\n".join(l for l in text.split("\n") if _lang(l) not in ("eng", "hin"))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 154. `DB-D3-013` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-sa-fw2`. Source: section D3 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-013"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

D3_MIN_IN_SENTENCE = 3
D3_MAX_LATIN_SHARE = 0.5
D3_DENSE_IN_SENTENCE = 10
D3_CONTEXT = 25
RE_DEVA_WORD = re.compile(
    r"[ऄ-हऽॐक़-ॡॲ-ॿ]"
    r"[ऀ-ॣॱ-ॿ‌‍]*"
    r"(?::(?![0-9A-Za-zऀ-ॿ]))?")
RE_LATIN_WORD = re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]+")
RE_DEVA_CHAR = re.compile(r"[ऀ-ॿ]")
RE_PAREN_ACRONYM = re.compile(r"\([A-Z]{2,8}\)")
def deva_words(text):
    """Devanagari words of `text` (see RE_DEVA_WORD); danda, digits and punctuation split, ZWJ/ZWNJ stay inside a word."""
    return RE_DEVA_WORD.findall(text)
def latin_in_sentences(text):
    """Latin-script words that sit inside a Devanagari sentence: Devanagari within D3_CONTEXT chars on both sides on the
    same line (adapted from prescreen.py's in_sentence rule; here the context window is cut at the nearest line break
    so it can never reach a neighbouring line). Latin-only lines — header, footer or mid-body chrome — therefore never
    qualify, however short. All-caps acronyms in parentheses such as (CPEC) are removed first. Single letters are
    ignored (list markers, variables)."""
    t = RE_PAREN_ACRONYM.sub(lambda m: " " * len(m.group()), text)
    hits = []
    for m in RE_LATIN_WORD.finditer(t):
        if len(m.group()) < 2:
            continue
        before = t[max(0, m.start() - D3_CONTEXT):m.start()].rsplit("\n", 1)[-1]
        after = t[m.end():m.end() + D3_CONTEXT].split("\n", 1)[0]
        if RE_DEVA_CHAR.search(before) and RE_DEVA_CHAR.search(after):
            hits.append(m.group())
    return hits
def latin_share(text):
    """Latin words / (Latin words + Devanagari words); 0.0 when there are no words."""
    latin = len(RE_LATIN_WORD.findall(text)); deva = len(deva_words(text))
    return latin / (latin + deva) if latin + deva else 0.0
def d3_mixed_language(text):
    """D3 detector: at least D3_MIN_IN_SENTENCE Latin words inside Devanagari sentences and Latin share below
    D3_MAX_LATIN_SHARE; the share clause is waived when at least D3_DENSE_IN_SENTENCE Latin words sit inside
    Devanagari sentences (word-by-word gloss pages). Detection only; the action is `none`."""
    n = len(latin_in_sentences(text))
    if n >= D3_DENSE_IN_SENTENCE:
        return True
    if latin_share(text) >= D3_MAX_LATIN_SHARE:
        return False
    return n >= D3_MIN_IN_SENTENCE

def medicine_d3(text):
    return text    # action none: the detector `d3_mixed_language` reports; the text is kept


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 155. `DB-D3-014` · D3 Mixed language · keep · stage 35

1. **Disease:** D3 Mixed language. Pack `ind-te-fw2`. Source: section D3 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d3(text)`.

```python
RULE_ID = "DB-D3-014"
CODE = "D3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d3(t, url=None):
    return t


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** own-pack real gold set (`ind-te-fw2_gold.csv`, 18 documents) and full Telugu real gold set (`telugu_gold.csv`, 50 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 27; 46 documents in the 31 Oct snapshot):
5. **Side effects:** in the author's `medicine.md`, section D3 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 156. `DB-D5-002` · D5 Translationese · keep · stage 35

1. **Disease:** D5 Translationese. Pack `ind-hi-hplt`. Source: section D5 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_d5(text)`.

```python
RULE_ID = "DB-D5-002"
CODE = "D5"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_d5(text):
    return False  # tag only: the text is kept as it is


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_d5  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** nothing to run, because the rule does nothing (changes 0 of 67 gold documents, drops 0). **PASS**
5. **Side effects:** in the author's `medicine.md`, section D5 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 157. `DB-G3-002` · G3 Indic dropped by an English rule · fix · stage 35

1. **Disease:** G3 Indic dropped by an English rule. Pack `ind-te-sangraha-s`. Source: section G3 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_g3(text)`.

```python
RULE_ID = "DB-G3-002"
CODE = "G3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_g3(text):
    return re.sub(r"[ \t]*\([ \t,;]*\)", "", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_g3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_g3` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section G3 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 158. `DB-H3-001` · H3 The same content in another source or language · fix · stage 35

1. **Disease:** H3 The same content in another source or language. Pack `ind-sa-fw2`. Source: section H3 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_h3(text)`.

```python
RULE_ID = "DB-H3-001"
CODE = "H3"
ACTION = "fix"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_HIN = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने को से का की के भी यह वह कि जो आप हम साथ वाले रहे रही".split())
_ANCHOR = set("है हैं था थे थी में और नहीं लिए गया गई हुआ होता होती करने किया करें ने साथ वाले रहे रही".split())

def _translation(line):
    letters = [c for c in line if c.isalpha()]
    if len(line.strip()) < 25 or len(letters) < 10:
        return False
    lat = sum(1 for c in letters if c.isascii() or 0xC0 <= ord(c) <= 0x24F or 0x1E00 <= ord(c) <= 0x1EFF)
    if lat / len(letters) > 0.6:
        return not re.search(r"[āīūṛṝḷṃḥṅñṭḍṇśṣ]", line)
    w = re.findall("[ऀ-ॿ]+", line)
    h = sum(1 for x in w if x in _HIN)
    a = sum(1 for x in w if x in _ANCHOR)
    return a >= 1 and h >= 2 and h / max(1, len(w)) >= 0.15

def medicine_h3(text):
    return "\n".join(l for l in text.split("\n") if not _translation(l))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_h3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section H3 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 159. `DB-H3-002` · H3 The same content in another source or language · keep · stage 35

1. **Disease:** H3 The same content in another source or language. Pack `ind-sa-fw2`. Source: section H3 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_h3(text)`.

```python
RULE_ID = "DB-H3-002"
CODE = "H3"
ACTION = "keep"
STAGE = "35"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

RE_ROMAN_VERSE_LINE = re.compile(r"^[Ⅰ-ⅿ]+ \S", re.M)                        # ebible.org: "Ⅰ यावन्तः …"
RE_GITA_REF = re.compile(r"।।[0-9]{1,2}(?:\.[0-9]{1,3}){1,2}।।")               # gitasupersite: ।।8.4।।
RE_GITA_HEADING_LINE = re.compile(r"^।।[^।\n0-9०-९]{1,60}।।[ \t\r]*$", re.M)  # ।।ब्रह्मसूत्रभाष्यम्।।
MIN_VERSE_LINES = 5; MIN_GITA_REFS = 2; MIN_GITA_HEADINGS = 3

def detect_h3(text):
    if not text: return False
    if len(RE_ROMAN_VERSE_LINE.findall(text)) >= MIN_VERSE_LINES: return True
    if len(RE_GITA_REF.findall(text)) >= MIN_GITA_REFS: return True
    if len(RE_GITA_HEADING_LINE.findall(text)) >= MIN_GITA_HEADINGS: return True
    return False
def medicine_h3(text):
    return text    # action none: the detector `detect_h3` reports; dedupe is a corpus-time action


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_h3  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section H3 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 160. `DB-B4-001` · B4 Template and code junk in prose · fix · stage 40

1. **Disease:** B4 Template and code junk in prose. Pack `ind-gu-fw2`. Source: section B4 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-B4-001"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

JUNK = re.compile(r"\[ઇમેઇલ સુરક્ષિત\]|email@example\.com|firstname\.lastname@example\.com"
                  r"|\[email\s*protected\]|\{\{.*?\}\}|\$\{.*?\}|\bundefined\b|\bNaN\b|\bnull\b")

def medicine(text):
    return JUNK.sub("", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 4 of 6.
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 161. `DB-B4-002` · B4 Template and code junk in prose · fix · stage 40

1. **Disease:** B4 Template and code junk in prose. Pack `ind-kn-sangraha-v`. Source: section B4 of `diagnosis/submissions/ind-kn-sangraha-v/pyru/medicine.md`, PR #25 at `5eaa16e`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-002"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-sangraha-v"  # packs it runs on
SOURCE = "ind-kn-sangraha-v"  # pack whose medicine this came from
AUTHOR = "pyru"  # PR #25 at 5eaa16e
import re  # added by Data B: harm_test_indic.py gives every block `re`

BS = chr(92)


def fix_literal_newline(t):
    """B4: a literal backslash-n (two characters) becomes a real newline."""
    return t.replace(BS + "n", "\n")


def medicine_b4(text):
    """The B4 rule, under the name that the harm tests look for: returns the fixed text."""
    return fix_literal_newline(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-sangraha-v` only.
4. **Harm test (as the author reports it):** on the gold set (103 documents) it changes 0 and drops 0: 0.0%. Pass (at most 1 document or 1%, whichever is larger).
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #25).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 162. `DB-B4-003` · B4 Template and code junk in prose · fix · stage 40

1. **Disease:** B4 Template and code junk in prose. Pack `ind-mr-sangraha-v`. Source: section B4 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_b4(text)`.

```python
RULE_ID = "DB-B4-003"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f
import re  # added by Data B: harm_test_indic.py gives every block `re`

def cure_b4(text):
    # Conservative gate for recurring escaped newlines in the Marathi prose pack.
    if text.count("\\n") < 3:
        return text
    return text.replace("\\n", "\n")


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** — **0 changed, 0 dropped / 88 gold documents (0.00%)**; gold limit: 1 changed/dropped document. **ZWJ/ZWNJ audit: PASS** (0 affected documents with changed joiner counts). **Normal-form audit: PASS** (0 affected documents left NFC or lost a compatibility character). Check B4-positive prose separatel...
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 163. `DB-B4-004` · B4 Template and code junk in prose · fix · stage 40

1. **Disease:** B4 Template and code junk in prose. Pack `ind-sa-fw2`. Source: section B4 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-004"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_JUNK = [r"\{\{[^{}\n]*\}\}", r"'''", r"\[Page\d+-[a-z]\+ ?\d+\]", "↩"]

def medicine_b4(text):
    t = re.sub(r"\[\[(?:[^|\]\n]*\|)?([^\]\n]*)\]\]", r"\1", text)
    for p in _JUNK:
        t = re.sub(p, "", t)
    t = re.sub(r"(?<=॥)\d{3,}(?=\s)", "", t)
    return re.sub(r"(?<=\s)\d{3,}(?=[क-ह])|(?<=[ा-्क-ह])\d{3,}(?=[क-ह])", "", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 164. `DB-B4-005` · B4 Template and code junk in prose · fix · stage 40

1. **Disease:** B4 Template and code junk in prose. Pack `ind-ta-sangraha-v`. Source: section B4 of `diagnosis/submissions/ind-ta-sangraha-v/abinesh1/medicine.md`, PR #101 at `3d69463`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-005"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"tam_Taml"}
ORIGIN = "ind-ta-sangraha-v"  # packs it runs on
SOURCE = "ind-ta-sangraha-v"  # pack whose medicine this came from
AUTHOR = "abinesh1"  # PR #101 at 3d69463
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b4(text):
    return text.replace("\\n", "\n")  # the two characters backslash and n become a line break


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-ta-sangraha-v` only.
4. **Harm test (as the author reports it):** gold set: 0 of 41 changed, 0 dropped, PASS. Pack check: changes 22 documents, all labelled B4.
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #101).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 165. `DB-B4-006` · B4 Template and code junk in prose · fix · stage 40

1. **Disease:** B4 Template and code junk in prose. Pack `ind-te-sangraha-s`. Source: section B4 of `diagnosis/submissions/ind-te-sangraha-s/shankarpandala/medicine.md`, PR #92 at `2e61b3b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_b4(text)`.

```python
RULE_ID = "DB-B4-006"
CODE = "B4"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-sangraha-s"  # packs it runs on
SOURCE = "ind-te-sangraha-s"  # pack whose medicine this came from
AUTHOR = "shankarpandala"  # PR #92 at 2e61b3b
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_b4(text):
    text = re.sub(r"[ \t]*<ఐ\.? ?డి\.? ?\d+>?%?", "", text)
    text = re.sub(r"[ \t]*(?<![\u0C00-\u0C7F])ఐడి\d+", "", text)
    text = re.sub(r"[ \t]*\(ID\d+\)", "", text)
    text = re.sub(r"(?m)^![^\n]*=[^\n]*\|[^\n]*\n?", "", text)
    return text


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_b4  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-sangraha-s` only.
4. **Harm test (as the author reports it):** gold set: the gold set of this pack, 5 documents (teams/02-data-b/gold/ind-te-sangraha-s_gold.csv on main, 2 Nov 2026); rule `medicine_b4` of this file (the code block in this section), run with harm_test_indic.py (PR #148); a rule passes if it changes or drops at most max(1 document, 1%) of the gol...
5. **Side effects:** in the author's `medicine.md`, section B4 (PR #92).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 166. `DB-F1-001` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-gu-fw2`. Source: section F1 of `diagnosis/submissions/ind-gu-fw2/Nisarg189/medicine.md`, PR #18 at `9184235`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python
RULE_ID = "DB-F1-001"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "Nisarg189"  # PR #18 at 9184235

import re
GU_DIGIT = "\u0AE6-\u0AEF"                    # Gujarati digits 0-9
def _fix(old, new):
    return (new, "keep" if new == old else "fix")

PHONE = re.compile(rf"(?<![0-9{GU_DIGIT}])(?:\+91[\s-]?)?[6-9૬-૯][0-9{GU_DIGIT}]{{4}}"
                   rf"[\s-]?[0-9{GU_DIGIT}]{{5}}(?![0-9{GU_DIGIT}])")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def m3_f1(text, url=None):
    return _fix(text, EMAIL.sub("[EMAIL]", PHONE.sub("[PHONE]", text)))

def medicine_f1(text, url=None):
    """Harm-test entry: return the new text, or True to drop."""
    return m3_f1(text, url)[0]


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** gold set of 19 documents (ind-gu-fw2 19), medicine.md sha256 3957269425fa; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #18).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 167. `DB-F1-002` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-gu-fw2`. Source: section F1 of `diagnosis/submissions/ind-gu-fw2/vedang-patel-10/medicine.md`, PR #91 at `b6bf183`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine(text)`.

```python
RULE_ID = "DB-F1-002"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"guj_Gujr"}
ORIGIN = "ind-gu-fw2"  # packs it runs on
SOURCE = "ind-gu-fw2"  # pack whose medicine this came from
AUTHOR = "vedang-patel-10"  # PR #91 at b6bf183

import re

EMAIL = re.compile(r"[\w.+-]+@(?!example\.com)[\w-]+\.[\w.]+")
PHONE = re.compile(
    r"(?<![\d.])(?:\+91[ -]?)?[6-9]\d{4}[ -]?\d{5}(?!\d)"   # mobile
    r"|(?<!\d)\d{3}\d{3}\d{4,}(?!\d)"                       # long digit run
    r"|\b0\d{2,4}[ -]\d{6,8}\b")                            # landline

def medicine(text):
    return EMAIL.sub("<EMAIL>", PHONE.sub("<PHONE>", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-gu-fw2` only.
4. **Harm test (as the author reports it):** **gold set** (`ind-gu-fw2_gold.csv`, 19 documents, all 19 are `clean` in labels.csv): changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). Proxy set (all `clean` rows of labels.csv), n=157: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 17 of 1...
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #91).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 168. `DB-F1-003` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-hi-hplt`. Source: section F1 of `diagnosis/submissions/ind-hi-hplt/narasimhatejav/medicine.md`, PR #170 at `4aaf84b`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python
RULE_ID = "DB-F1-003"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "narasimhatejav"  # PR #170 at 4aaf84b
import re  # added by Data B: harm_test_indic.py gives every block `re`

_MAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"(?<![\d,.])(?:\+91[ -]?|0)?[6-9]\d{9}(?![\d,.])")


def medicine_f1(text):
    t = _MAIL.sub("", text)
    return _PHONE.sub("", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** changed 0 of 67 gold documents, dropped 0. **PASS**
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #170).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 169. `DB-F1-004` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-hi-hplt`. Source: section F1 of `diagnosis/submissions/ind-hi-hplt/therahulbhati/medicine.md`, PR #24 at `37652bf`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python
RULE_ID = "DB-F1-004"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"hin_Deva"}
ORIGIN = "ind-hi-hplt"  # packs it runs on
SOURCE = "ind-hi-hplt"  # pack whose medicine this came from
AUTHOR = "therahulbhati"  # PR #24 at 37652bf

import re

# F1: personal e-mail addresses (free mail) and mobile numbers, not near helpline or office words
_MAIL = re.compile(r"[\w.+-]+@(?:gmail|yahoo|hotmail|outlook|rediffmail|ymail)\.[a-z.]+", re.I)
_MOB = re.compile(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)")
_ORG = re.compile(r"हेल्पलाइन|टोल|फ्री|व्हाट्सएप|whatsapp|helpline|toll|कार्यालय|office|कस्टमर|customer|support", re.I)


def medicine_f1(text):
    out = _MAIL.sub("", text)

    def mob(m):
        near = out[max(0, m.start() - 40):m.start()]
        return m.group(0) if _ORG.search(near) else ""
    return _MOB.sub(mob, out)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-hi-hplt` only.
4. **Harm test (as the author reports it):** gold set `ind-hi-hplt_gold.csv`, 67 documents, run with `harm_test_indic.py`. Changed 0 of 67, dropped 0 of 67 (0.00%): **PASS**. ZWJ/ZWNJ audit: **PASS**. Normal-form audit: **PASS**. Pack check (the 500 labelled documents of this pack): cures 10 of 16 F1 documents; 0 other diseased documents touch...
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #24).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 170. `DB-F1-005` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-kn-fw2`. Source: section F1 of `diagnosis/submissions/ind-kn-fw2/LokeshJatangi/medicine.md`, PR #63 at `aeb79b8`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python
RULE_ID = "DB-F1-005"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"kan_Knda"}
ORIGIN = "ind-kn-fw2"  # packs it runs on
SOURCE = "ind-kn-fw2"  # pack whose medicine this came from
AUTHOR = "LokeshJatangi"  # PR #63 at aeb79b8

import re

F1_EMAIL = r"(?<![\w.+-])[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}(?![\w-])"
F1_NUMBER = r"(?:[0-9]{10,11}|[0-9]{5}[ \t]+[0-9]{5}|[0-9]{3}[ \t]+[0-9]{8})"
F1_PHONE = rf"(?<!\w)(?:\+[0-9]{{1,3}}[ \t]+)?{F1_NUMBER}(?!\w)"
F1_CANDIDATE = re.compile(rf"(?:{F1_EMAIL})|(?:{F1_PHONE})")

def medicine_f1(text, url=""):
    return F1_CANDIDATE.sub("[REDACTED]", text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-kn-fw2` only.
4. **Harm test (as the author reports it):** **175-document** combined `kannada_gold.csv`, using the referenced Indic harness
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #63).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 171. `DB-F1-006` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-mr-fw2`. Source: section F1 of `diagnosis/submissions/ind-mr-fw2/thinktinkergreen/medicine.md`, PR #50 at `0d85486`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python
RULE_ID = "DB-F1-006"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-fw2"  # packs it runs on
SOURCE = "ind-mr-fw2"  # pack whose medicine this came from
AUTHOR = "thinktinkergreen"  # PR #50 at 0d85486
import re  # added by Data B: harm_test_indic.py gives every block `re`

def medicine_f1(text):
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '<EMAIL>', text)
    return re.sub(r'(?:\+91[\-\s]?)?[6-9]\d{9}', '<PHONE>', text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-mr-fw2` only.
4. **Harm test (as the author reports it):** gold set of 140 documents (ind-mr-fw2 140); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #50).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 172. `DB-F1-007` · F1 Personal data · fix+drop · stage 40

1. **Disease:** F1 Personal data. Pack `ind-mr-sangraha-v`. Source: section F1 of `diagnosis/submissions/ind-mr-sangraha-v/patilvijay23/medicine.md`, PR #19 at `07d884f`.
2. **Medicine:** the author's code, unchanged. Main function: `cure_f1(text)`.

```python
RULE_ID = "DB-F1-007"
CODE = "F1"
ACTION = "fix+drop"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"mar_Deva"}
ORIGIN = "ind-mr-sangraha-v"  # packs it runs on
SOURCE = "ind-mr-sangraha-v"  # pack whose medicine this came from
AUTHOR = "patilvijay23"  # PR #19 at 07d884f

import hashlib

# Reviewed Marathi pack records only: original and file-order pre-rule text.
# SHA-256 avoids embedding private values and supports the text-only harness.
_EXCLUDED_SHA256 = frozenset({
    # 001bc250879bd0f7
    "001bc250879bd0f702986535ee3252eee6e1a7c48cdee7f2890a890fd6d50583",
    # 404f212106f160c8
    "404f212106f160c83000ac10881284d088304b030173cbd48fbe99d83c42f743",
    # 50bf742434fe8393
    "50bf742434fe8393f951f369fee4030e82089b9f4ae1fc64cf130eaf3c7b8844",
    # 6402789257fa2f5a
    "011dd7d4bd18b4f776adc7618c36a81e30ae22fdcdde3a446d068968f1519296",
    "6402789257fa2f5a997646dca7c843b74d4dece07a4c7419fd92684c46b213cd",
    # 66ebbb3c7f89fc6e
    "66ebbb3c7f89fc6e9d0fd41720240f166e6a72ebe5fbca7e9d9c76ee8f47de44",
    # 727a8a3d9a6f4fd4
    "25a62eaac83c681739b5550c373f1f6fe1f8cf79ab5f63455d12b131659cc873",
    "727a8a3d9a6f4fd42343d464e0f3b36a153a29ef3c1a91bb9b3635aaf4b65be8",
    # 7d5867bf37cf6900
    "7d5867bf37cf6900af52d058752e3dfc761949319080591871e7c6bb5b0d3e2d",
    # 8924481cb3403322
    "8924481cb3403322ef651e1327e34417558683c9b6c7033dbc81111afd507873",
    # b5776aacf45b7cac
    "b5776aacf45b7cac904ffedd0da2f4fe8e5b08ea0732bc03684d66a93349ae1e",
    # d2dbdd1f87b6a3e1
    "d2dbdd1f87b6a3e1dda084663699ee354eca663094d25b6aa4ef48e373fa07af",
    # fab4928039a870ab
    "fab4928039a870ab3506e01b8a5a910ee799e3662c2a85cb8c3454c092364e50",
    # fedd23c56d6850a6
    "392115d2af134133091b7c8e672863133bea34461b3d8d352e3f6cdd5af5b0b3",
    "fedd23c56d6850a6fcdd4911a9b268d1f00d30a2b1c96e9b59bc8c05335e9936",
})

# Adapted from g1-specv1/tools/f1_rule.py: explicit private context,
# typed placeholders and organisation/role safeguards. Marathi prose only.
import re

_F1_ORG = re.compile(
    r"(?:महानगरपालिका|नगरपालिका|ग्रामपंचायत|शासकीय|सरकारी|कार्यालय|"
    r"विद्यापीठ|महाविद्यालय|विद्यालय|रुग्णालय|पोलीस|पोलिस|हेल्पलाइन|"
    r"कंपनी|बँक|बँकेचा|संस्था|सार्वजनिक|टोल[ -]?फ्री|"
    r"\b(?:government|office|university|hospital|company|helpline|bank)\b)", re.I)
_F1_PERSONAL = re.compile(
    r"(?:वैयक्तिक|खाजगी|खासगी|घरचा|घरचा संपर्क|घरचा पत्ता|घरचा फोन|"
    r"घरचा ईमेल|राहत्या घराचा|निवासी पत्ता|माझा|माझी|माझे|"
    r"\b(?:personal|private|home|residential|my)\b)", re.I)
_F1_EMAIL = re.compile(
    r"(?<![\w.+%-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w-])")
_F1_ROLE = re.compile(
    r"^(?:info|contact|support|help|admin|office|sales|press|media|"
    r"noreply|no-reply|editor|news|helpline|hr|jobs)$", re.I)
_F1_SAFE_DOMAIN = re.compile(
    r"(?:^|\.)(?:example\.(?:com|org|net)|invalid|test|localhost|"
    r"users\.noreply\.github\.com|gov\.in|nic\.in)$", re.I)
# Indian mobiles, ASCII or Devanagari digits; no digit normalization.
_F1_PHONE = re.compile(
    r"(?<![\w+])(?:\+[9९][1१][ -]?)?[6-9६-९][0-9०-९]{4}[ -]?[0-9०-९]{5}(?![\w-])")
# Only a labelled personal address field, never an inferred place/name span.
_F1_ADDRESS = re.compile(
    r"(?P<label>(?:(?:वैयक्तिक|खाजगी|खासगी|निवासी)\s+पत्ता|"
    r"(?:घरचा|राहत्या घराचा)\s+पत्ता|(?:home|private|residential)\s+address)"
    r"\s*[:：]\s*)(?P<value>[^\r\n]+)", re.I)

def _f1_private_context(text, start, end):
    # Stay within the line; the preceding line can identify an organisation.
    lo = text.rfind("\n", 0, start) + 1
    hi = text.find("\n", end)
    hi = len(text) if hi < 0 else hi
    previous = text.rfind("\n", 0, max(0, lo - 1)) + 1
    context = text[previous:hi]
    return not _F1_ORG.search(context) and bool(_F1_PERSONAL.search(text[lo:start]))

def _redact_f1_mr(text):
    """Bounded candidate, not proof of complete privacy removal.
    Unlabelled details, names, landlines and narrative addresses need review.
    """
    def email(match):
        local, domain = match.group().rsplit("@", 1)
        if _F1_ROLE.fullmatch(local) or _F1_SAFE_DOMAIN.search(domain):
            return match.group()
        return "<EMAIL>" if _f1_private_context(match.string, match.start(), match.end()) else match.group()

    def phone(match):
        return "<PHONE>" if _f1_private_context(match.string, match.start(), match.end()) else match.group()

    def address(match):
        if not _f1_private_context(match.string, match.start("value"), match.end("value")):
            return match.group()
        # Multi-field lines need separate span review; do not erase other fields.
        value = match.group("value")
        if "<ADDRESS>" in value or re.search(r"[;|]|<(?:PHONE|EMAIL)>", value):
            return match.group()
        return match.group("label") + "<ADDRESS>"

    out = _F1_EMAIL.sub(email, text)
    out = _F1_PHONE.sub(phone, out)
    return _F1_ADDRESS.sub(address, out)

def cure_f1(text):
    # Quarantine takes precedence: partial redaction never releases these records.
    if hashlib.sha256(text.encode("utf-8")).hexdigest() in _EXCLUDED_SHA256:
        return True
    return _redact_f1_mr(text)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = cure_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix+drop. **Runs on:** `ind-mr-sangraha-v` only.
4. **Harm test (as the author reports it):** See the fresh results above. Positive-case scope: **12 reviewed records excluded individually**; no other pack records changed. The redaction helper alone changed **0/12** reviewed F1 records, so it has no demonstrated repair coverage on those cases. Synthetic checks cover supported fields; they do ...
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #19).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 173. `DB-F1-008` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-sa-fw2`. Source: section F1 of `diagnosis/submissions/ind-sa-fw2/dattatreyamanjunath/medicine.md`, PR #45 at `b054835`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f1(text)`.

```python
RULE_ID = "DB-F1-008"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "dattatreyamanjunath"  # PR #45 at b054835
import re  # added by Data B: harm_test_indic.py gives every block `re`

_PHONE = re.compile(r"(?<!\d)(?:\+?91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}(?!\d)")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+\s*(?:@|\(at\)|\[at\]| at )\s*[A-Za-z0-9-]+\s*(?:\.|\(dot\)|\[dot\]| dot )\s*[A-Za-z]{2,}")

def medicine_f1(text):
    t = _EMAIL.sub(lambda m: m.group() if "example." in m.group() else "<EMAIL>", text)
    return _PHONE.sub("<PHONE>", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68); rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #45).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 174. `DB-F1-009` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-sa-fw2`. Source: section F1 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `fix_f1(text)`.

```python
RULE_ID = "DB-F1-009"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RE_PHONE = re.compile(r"(?<![0-9])(?:\+91[ \t-]{0,2})?"
                      r"(?:[6-9][0-9]{9}|[6-9][0-9]{4}[ -][0-9]{5}|[6-9][0-9]{2}[ -][0-9]{3}[ -][0-9]{4})(?![0-9])")

def fix_f1(text):
    """Replace every email with <email> and every Indian mobile number with <phone>. Idempotent."""
    return RE_PHONE.sub("<phone>", RE_EMAIL.sub("<email>", text))


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = fix_f1  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 175. `DB-F1-010` · F1 Personal data · fix · stage 40

1. **Disease:** F1 Personal data. Pack `ind-te-fw2`. Source: section F1 of `diagnosis/submissions/ind-te-fw2/sandeepkunkunuru/medicine.md`, PR #3 at `75e8f7b`.
2. **Medicine:** the author's code, unchanged. Main function: `f1_pii(text)`.

```python
RULE_ID = "DB-F1-010"
CODE = "F1"
ACTION = "fix"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"tel_Telu"}
ORIGIN = "ind-te-fw2"  # packs it runs on
SOURCE = "ind-te-fw2"  # pack whose medicine this came from
AUTHOR = "sandeepkunkunuru"  # PR #3 at 75e8f7b
import re  # added by Data B: harm_test_indic.py gives every block `re`

F1_RX = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|(?<!\d)(?:\+91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
def f1_pii(t, url=None):
    return F1_RX.sub("", t)


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = f1_pii  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** fix. **Runs on:** `ind-te-fw2` only.
4. **Harm test (as the author reports it):** real Telugu gold set (`telugu_gold.csv`, 46 documents across `ind-te-fw2` 18, `ind-te-sangraha-s` 5, `ind-te-sangraha-v` 23):
5. **Side effects:** in the author's `medicine.md`, section F1 (PR #3).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.

## 176. `DB-F2-002` · F2 Benchmark leak · keep · stage 40

1. **Disease:** F2 Benchmark leak. Pack `ind-sa-fw2`. Source: section F2 of `diagnosis/submissions/ind-sa-fw2/swatibansal/medicine.md`, PR #80 at `7af8541`.
2. **Medicine:** the author's code, unchanged. Main function: `medicine_f2(text)`.

```python
RULE_ID = "DB-F2-002"
CODE = "F2"
ACTION = "keep"
STAGE = "40"
STATUS = "CANDIDATE"
LANGS = {"san_Deva"}
ORIGIN = "ind-sa-fw2"  # packs it runs on
SOURCE = "ind-sa-fw2"  # pack whose medicine this came from
AUTHOR = "swatibansal"  # PR #80 at 7af8541
import re  # added by Data B: harm_test_indic.py gives every block `re`

import collections
import json, os, unicodedata
DEFAULT_BENCH = os.path.join("..", "bench")
WINDOW = 50
MAX_SENTENCE_CHARS = 2000
BENCH_DIRS = ("flores200_devtest", "itihasa_test", "in22_gen")
DROP_BENCH_PREFIXES = ("flores", "in22")
_DROP_CATS = ("P", "Z", "S")
_DROP_FULL = {"Nd", "Cf", "Cc"}
def _dropped(c):
    cat = unicodedata.category(c)
    return cat[0] in _DROP_CATS or cat in _DROP_FULL or c.isspace()
def normalise(text):
    """NFC per character, then drop punctuation, separators, symbols, digits of every script, format and control chars."""
    return "".join(c for ch in text for c in unicodedata.normalize("NFC", ch) if not _dropped(c))
class _Index:
    """hash(window) -> [(bench, sid, pos)] over every benchmark sentence; hits are verified against the real text."""
    def __init__(self, bench_dir):
        self.table = collections.defaultdict(list); self.norm = {}; self.n_sentences = 0
        if not bench_dir or not os.path.isdir(bench_dir): return
        for name in BENCH_DIRS:
            path = os.path.join(bench_dir, name, "sentences.jsonl")
            if not os.path.isfile(path): continue
            try:
                with open(path, encoding="utf-8", errors="replace") as f: lines = f.read().split("\n")
            except OSError: continue
            for ln, line in enumerate(lines, 1):
                line = line.strip()
                if not line: continue
                try: d = json.loads(line)
                except ValueError: continue
                if not isinstance(d, dict) or not isinstance(d.get("text"), str): continue
                sid = d.get("id", ln)
                if not isinstance(sid, (int, str)): sid = ln
                ns = normalise(d["text"][:MAX_SENTENCE_CHARS])
                if len(ns) < WINDOW: continue
                key = (name, sid); self.norm[key] = ns; self.n_sentences += 1
                for p in range(len(ns) - WINDOW + 1): self.table[hash(ns[p:p + WINDOW])].append((key, p))
    def __bool__(self): return bool(self.table)
    def hits(self, text, prefixes=None):
        """{(bench, sid): number of DISTINCT 50-char windows of that sentence found in text}."""
        found = collections.defaultdict(set)
        if not self.table: return {}
        ns = normalise(text)
        for i in range(len(ns) - WINDOW + 1):
            win = ns[i:i + WINDOW]
            for key, p in self.table.get(hash(win), ()):
                if prefixes and not key[0].lower().startswith(prefixes): continue
                if self.norm[key][p:p + WINDOW] == win: found[key].add(win)
        return {k: len(v) for k, v in found.items()}
_BENCH = {"dir": None, "cache": {}}
def _index(bench_dir=None):
    d = os.path.normpath(bench_dir or _BENCH["dir"] or DEFAULT_BENCH)
    if d not in _BENCH["cache"]: _BENCH["cache"][d] = _Index(d)
    return _BENCH["cache"][d]
def _strong(text, bench_dir=None, prefixes=None):
    return any(k >= 2 for k in _index(bench_dir).hits(text, prefixes).values())
def detect_f2(text, bench_dir=None):
    """True when some benchmark sentence (FLORES-200, IN22 or Itihāsa test split) shares >= 2 distinct 50-char
    normalised windows with the text. False when no benchmark file is available."""
    return _strong(text, bench_dir)
def drop_f2_flores(text, bench_dir=None):
    """Drop variant, not in MEDICINES: True only for FLORES-200 / IN22 hits (benchmark folder name starts with
    flores or in22). Itihāsa hits never drop (public canon)."""
    return _strong(text, bench_dir, DROP_BENCH_PREFIXES)

def medicine_f2(text):
    return text    # action none: the detector `detect_f2` reports (keep and record); `drop_f2_flores` is the drop variant


def _std(out, text):  # added by Data B, copied from Data A (medicine_english.md)
    # the author's result in the shared form: str -> fix/keep, None or True -> drop, False -> keep,
    # ("drop", _) -> drop. An empty result is a drop: nothing of the document is left.
    if out is None or out is True: return ("drop", text)
    if out is False: return ("keep", text)
    if isinstance(out, tuple):
        if out[0] == "drop": return ("drop", text)
        out = out[1]
    if not out.strip(): return ("drop", text)
    return ("fix" if out != text else "keep", out)

_AUTHOR_RULE = medicine_f2  # added by Data B
_PACKS = frozenset(ORIGIN.split(", "))  # added by Data B


def medicine(doc):  # added by Data B: runs only on the pack it was tested on
    if doc.get("pack_id") not in _PACKS:
        return ("keep", doc["text"])
    return _std(_AUTHOR_RULE(doc["text"]), doc["text"])
```

3. **Action:** keep. **Runs on:** `ind-sa-fw2` only.
4. **Harm test (as the author reports it):** gold set of 68 documents (ind-sa-fw2 68), medicine.md sha256 ff5e472b5ced; rule: changed or dropped at most 1% or 1 document, whichever is more.
5. **Side effects:** in the author's `medicine.md`, section F2 (PR #80).
6. **Spec v1:** status CANDIDATE, reviewer pending. Harm not re-run by Data B.
