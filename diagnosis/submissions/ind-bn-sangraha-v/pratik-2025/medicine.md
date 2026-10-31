# Medicine sheet: ind-bn-sangraha-v (pratik-2025)

Harm test status for every medicine below: the Bengali gold set
teams/02-data-b/gold/ind-bn-sangraha-v_gold.csv (about 50 documents) is available.
Harm tests were not run before Gate 1; results will be added in a follow-up commit.

## D4 — Bad machine translation
- Count: 189. Examples: 0ca18aa03db2ef77, 54442e06493e7751, 87c77e18093a596b
- Medicine: no regex can detect this. Score each document with a Bengali language-model fluency score (perplexity); flag documents above a threshold set on the gold set.
- Action: drop (only above the threshold)
- Harm test: not run before Gate 1 (see top).
- Side effects: formal, technical or old-style Bengali can score badly and be dropped wrongly.

## D3 — Mixed language
- Count: 109. Examples: 0ca18aa03db2ef77, 54442e06493e7751, 87c77e18093a596b
- Medicine: measure the share of Latin letters: `len(re.findall(r'[A-Za-z]', t)) / max(1, len(re.findall(r'[A-Za-z\u0980-\u09FF]', t)))`
- Action: keep (natural code-mixing); drop only if Latin share > 0.5
- Harm test: not run before Gate 1 (see top).
- Side effects: news with many English names or terms may cross the threshold.

## C5 — Lists of keywords or links
- Count: 46. Examples: 017b4f09daad47e4, 0f79a07b7f39f669, 14c39215a007bbe9
- Medicine: drop if more than 60% of lines are short (< 4 words) and contain no sentence end (`।` `.` `?` `!`).
- Action: drop
- Harm test: not run before Gate 1 (see top).
- Side effects: poems and real lists (recipes, ingredients) may be dropped.

## C3 — Truncated document
- Count: 41. Examples: f4b1f41a0f6d3a9e, b3f021daf03eebe5, eb3dc547426a3951
- Medicine: flag if the text does not end with `।` `.` `?` `!` `"` or `)`: `not re.search(r'[।.?!"\)]\s*$', t)`
- Action: fix (remove the last incomplete sentence)
- Harm test: not run before Gate 1 (see top).
- Side effects: headings, list items and poems that end without punctuation.

## C1 — Boilerplate
- Count: 39. Examples: 7035900113f62f27, 017b4f09daad47e4, 5c35ce7401e2ddd5
- Medicine: remove whole lines matching share/menu phrases, e.g. `^(শেয়ার করুন|Share|আরও পড়ুন|Read more|Follow us).*$`
- Action: fix
- Harm test: not run before Gate 1 (see top).
- Side effects: a real sentence that starts with one of these phrases.

## G2 — Lost ZWJ or ZWNJ
- Count: 31. Examples: 4620e19b5836f03f, 8a252dfddf006bf5, f83b0bf24e9d2963
- Medicine: restore ZWJ in known forms, e.g. `র্য` → `র‍্য` (র + ZWJ + ্ + য) for words such as র‍্যাব.
- Action: fix
- Harm test: not run before Gate 1 (see top).
- Side effects: words where র্য is the correct spelling would be changed.

## C4 — Two documents joined
- Count: 15. Examples: f0e9d668c4268ff2, 7160f28b914f8629, f4b1f41a0f6d3a9e
- Medicine: no reliable rule; flag documents with a sharp topic change (low similarity between halves) for review.
- Action: drop (flagged only)
- Harm test: not run before Gate 1 (see top).
- Side effects: long articles that change topic naturally.

## A3 — Mojibake
- Count: 14. Examples: 5584556a2ea2dcfd, 975e9170d8259094, 1530194906022e0e
- Medicine: detect `à¦|à§|Ã|â€`; try `t.encode('latin-1').decode('utf-8')` on the broken span.
- Action: fix if the repair succeeds, else drop
- Harm test: not run before Gate 1 (see top).
- Side effects: real text containing accented Latin letters.

## C2 — Repeated lines
- Count: 10. Examples: 44f51067574b2556, b0d8affd2329469d, 1da19ac48860fb47
- Medicine: keep only the first copy of any line (longer than 20 characters) that appears 3 or more times.
- Action: fix
- Harm test: not run before Gate 1 (see top).
- Side effects: songs and poems with a repeated chorus.

## G1 — Cut at the vowel sign
- Count: 9. Examples: 251870ed41c8f19c, 32029c674c355e1b, 53ad1531ea630e8c
- Medicine: remove a space before a Bengali vowel sign or virama: `re.sub(r' ([\u09BE-\u09CD\u09D7])', r'\1', t)`
- Action: fix
- Harm test: not run before Gate 1 (see top).
- Side effects: very rare; a deliberately spaced sign in teaching text.

## D5 — Translationese
- Count: 8. Examples: b0c095487dd72b87, 22a785c77561bc0e, 63a1a908974b93be
- Medicine: no rule; same fluency score as D4.
- Action: keep (low harm)
- Harm test: not run before Gate 1 (see top).
- Side effects: same as D4.

## A2 — Control characters
- Count: 8. Examples: f4b1f41a0f6d3a9e, 2d21cfd2fc5a133f, 4620e19b5836f03f
- Medicine: `re.sub(r'[\x00-\x08\x0B-\x1F\x7F-\x9F]', '', t)` (carriage return \r replaced by nothing)
- Action: fix
- Harm test: not run before Gate 1 (see top).
- Side