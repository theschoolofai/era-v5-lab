# Gate 3: the Indic shards (Data B summary)

Week 3, task 6 of the Data B work order. Draft of Tue 17 Nov 2026; the final version is due Fri 20 Nov, 11:59 PM IST.
Sections 3 and 4 are filled in when the readers' day files (task 3), the rotation files (R1, R2) and the language
label check (task 5) are in.

Gate 3 asks: "Indic shards keep ZWJ and ZWNJ, pass the reader audit and stay inside approved drop rates."

**Inputs.** TSAI's 18 Indic token shards of 16 Nov (sample v0 train parts, after `clean.py` and F2, frozen tokenizer
p1536, sha256 `e6b93a93...`). The 22 raw sample v0 Indic train parts they were made from (from Data A; sha256 in
`audit/raw_parts_SHA256SUMS`). Every shard document is in its raw part.

## 1. ZWJ and ZWNJ

Measured with `audit/indic_audit.py` (#523): the counts of every kept document, in the raw text and in the shard text
decoded with the frozen tokenizer. The tokenizer's own chillu fold (Malayalam) is the one allowed change.

| | Raw | Shard | Documents changed | Changed in kept text |
|---|---:|---:|---:|---:|
| ZWNJ (U+200C) | 619 | 619 | 0 | 0 |
| ZWJ (U+200D) | 11,179 | 11,139 | 26 | **0** |

- **ZWNJ: no change in any pack.**
- **ZWJ: no joiner was lost from text that cleaning kept.** The 40 missing ZWJ are in 26 `ind-hi-indiccorp` documents.
  In each of them, cleaning cut a trailing "Also Read" link line, and the ZWJ were in that line (38 of the 40 in half
  forms, virama + ZWJ + consonant). The shard text of each of these documents is one unbroken piece of the raw text.
- Task 4 (`audit/zwj_counts.csv`, a second count made independently): [to add, Thu 19].

### Visarga

Data A's #566 found the visarga turned into an ASCII colon in the v0-clean sample (ః U+0C03 to `:` in
`ind-te-sangraha-s`, and in the Hindi packs). `indic_audit.py` checks the shards for it (#576): it counts the
visarga of each script in every kept document, and the words in kept text whose visarga cleaning turned into `:` or
deleted. Tamil uses the aytham ஃ (U+0B83).

| Language | Visarga raw | Visarga shard | Documents with fewer | Words edited in kept text |
|---|---:|---:|---:|---:|
| hi | 26,535 | 26,352 | 109 | 0 |
| bn | 23,681 | 23,400 | 172 | 0 |
| te | 28,352 | 28,308 | 7 | 0 |
| kn | 21,520 | 20,620 | 650 | 0 |
| ta | 7,369 | 7,369 | 0 | 0 |
| mr | 14,444 | 14,342 | 89 | 0 |
| gu | 6,441 | 6,238 | 105 | 0 |
| sa | 404,275 | 402,911 | 422 | 0 |
| **all** | 532,617 | 529,540 | 1,554 | **0** |

- **No visarga in text that cleaning kept was turned into a colon or deleted.** In the 1,554 documents with fewer
  visargas, they went out with text that cleaning removed: whole lines, short phrases such as a Marathi "हे ही वाचाः"
  ("Also read:") tail, and Sanskrit wiki markup.
- The damage #566 found is in the v0-clean sample only. The same check on raw vs v0-clean finds 3,490 edited words in
  `ind-te-sangraha-s`, 4,540 in `ind-ta-sangraha-v` (ஃ to `:`, not in #566) and 73 in the Hindi packs. The shards come
  from a later cleaning run without the visarga-to-colon step (TSAI, #240 review, 5 Nov). Indic audits should read the
  shards, not v0-clean.

## 2. Drop rate per language

Documents in the raw part with no row in the shard. The work order flags a filter that drops over 20%: no pack drops
over 20% in total, so no single filter does.

| Language | Packs with a shard | Raw | Kept | Dropped | Drop rate | Highest pack | ZWJ raw / shard | ZWNJ raw / shard |
|---|---|---:|---:|---:|---:|---|---:|---:|
| hi | fw2, hplt, indiccorp, sangraha-s, sangraha-v | 156,831 | 153,777 | 3,054 | 1.95% | ind-hi-sangraha-s 9.82% | 11,178 / 11,138 | 564 / 564 |
| bn | fw2, sangraha-v | 21,533 | 20,816 | 717 | 3.33% | ind-bn-fw2 4.47% | 0 / 0 | 0 / 0 |
| te | fw2, sangraha-s, sangraha-v | 19,388 | 18,682 | 706 | 3.64% | ind-te-sangraha-s 7.59% | 0 / 0 | 42 / 42 |
| kn | fw2, sangraha-s, sangraha-v | 21,576 | 21,274 | 302 | 1.40% | ind-kn-sangraha-v 2.30% | 0 / 0 | 13 / 13 |
| ta | sangraha-v | 6,796 | 6,795 | 1 | 0.01% | ind-ta-sangraha-v 0.01% | 0 / 0 | 0 / 0 |
| mr | fw2, sangraha-v | 23,632 | 23,414 | 218 | 0.92% | ind-mr-fw2 1.83% | 1 / 1 | 0 / 0 |
| gu | fw2 | 23,118 | 22,689 | 429 | 1.86% | ind-gu-fw2 1.86% | 0 / 0 | 0 / 0 |
| sa | fw2 | 5,908 | 5,667 | 241 | 4.08% | ind-sa-fw2 4.08% | 0 / 0 | 0 / 0 |
| **all** | 18 packs | **278,782** | **273,114** | **5,668** | **2.03%** | | 11,179 / 11,139 | 619 / 619 |

No shard yet (no cleaner rules; task 1): `ind-ml-fw2`, `ind-or-fw2`, `ind-ta-fw2`, `ind-ta-sangraha-s`. Malayalam and
Odia therefore have no shard at all, and Tamil has only `sangraha-v`.

The `sangraha-s` shards (hi, kn, te) are machine-translated text. They are counted here, but they are not part of the
native Indic share of the mix (`mix/indic_share_v1.md`, #522).

## 3. Reader audit

Task 3: each reader reads 50 cleaned documents of their language each day, Wed 18 to Fri 20 (`audit/day_D4.md` to
`audit/day_D6.md`). R1 and R2: rotation members check one shard each for script damage and lost joiners
(`audit/rotation_<handle>.md`).

| Language | Reader (task 3) | Documents read | Findings | Rotation check (R1, R2) |
|---|---|---:|---|---|
| te | #527 | [to add] | [to add] | `ind-te-sangraha-v` (#533) [to add] |
| kn | #528, and a second reader on the same documents (#569) | [to add] | [to add] | `ind-kn-sangraha-v` (#550): 100 documents, G1 4 in 3, A6 5 in 4, 0 ZWJ/ZWNJ |
| ta | #529 | [to add] | [to add] | |
| bn | #568 | [to add] | [to add] | |
| hi | none in the core team | | | `ind-hi-fw2` (#560): 50 documents, G1 2 in 1, A5 4 in 2 (source spelling), 0 ZWJ/ZWNJ |
| gu | none in Data B | | | `ind-gu-fw2` by code point (#570) [to add] |
| mr, sa | none in Data B | | | |

The two rotation checks so far find no damage from `clean.py` or p1536. The G1 and A5 cases are spellings in the
source, and the Kannada A6 and G1 cases (Latin letters inside Kannada words) wait for a Kannada reader. Both reports
were checked against the shards: every finding is at its offset, and a recount on the same documents gives the same
numbers.

Languages with no reader are reported as not read, not as passed.

## 4. Language labels of script-sharing pairs

Task 5 (`audit/lang_label_check.md`): Hindi, Marathi and Sanskrit in Devanagari, and Assamese in the Bengali packs.
[to add, Thu 19]

## 5. Result

| Gate 3 condition | Result |
|---|---|
| Indic shards keep ZWJ and ZWNJ | **Yes** for the 18 shards: 0 documents with a joiner changed in kept text (section 1) |
| (and the visarga, #566) | **Yes** for the 18 shards: 0 words with a visarga turned into `:` or deleted in kept text (section 1) |
| Pass the reader audit | [to add, Fri 20] |
| Inside approved drop rates | No pack drops over 20%; highest 9.82% (`ind-hi-sangraha-s`); all packs 2.03% (section 2) |

Not covered: Malayalam, Odia and two Tamil packs have no shard; Bengali, Marathi, Gujarati and Sanskrit have no Data B
reader.
