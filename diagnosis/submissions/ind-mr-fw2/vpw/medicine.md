# medicine.md — ind-mr-fw2 (handle: vpw)

Prescriptions for every disease found **> 5×** across the 500-doc pack. Counts are
from `labels.csv` (500 rows: **230 clean, 240 fix, 30 drop**).

## Harm-test protocol

No official Data-A/B gold set ships locally, so harm is measured against a
**single-reader proxy gold set**: my own **230 clean docs** (verdict=`clean`,
read end-to-end). This is weaker than a two-reader official gold set — it shares
my blind spots — so treat each PASS as "does not disturb text one careful reader
judged clean," not as a guarantee.

A medicine **FAILS** if it changes or drops **> 1%** of the proxy gold set
= **> 2.3 docs** (i.e. **3 or more**). Each rule below reports docs touched / 230,
re-measured against the final clean set.

All figures below are reproduced by a harm-test harness (`harm_test.py`, kept with
the capstone tooling alongside the pack — not in this submission repo) that reads
this `labels.csv` + the pack, runs every naive and narrow rule, and builds the real
cross-document shingle index.

Rules are the exact regex/predicate the fixer would run. For F1/E3, evidence is
type + offset only — the value is never copied, hex left empty.

---

## C1 — boilerplate / chrome contamination — **161**

Site furniture welded onto article text: inline teasers (`हेही वाचा`, `हे ही वाचा`,
`आणखी वाचा`, `नक्की वाचा`), share CTAs (`Whatsapp स्टेटस, Facebook, Instagram`),
CMS leaks (`Web Title`, `This News has been`), footers (`Copyright`,
`आपल्या शहरातील ताज्या बातम्या … डाउनलोड करा`, `Read the latest Marathi news …
Saam TV`, `Read Goa news in Marathi`), `View this post on Instagram`.

Examples: `9c9cb2366bc14d88` ('This News has been'), `d40a6e0c632b3dd0` (e-paper
footer @0 + Copyright), `a84ec9a0a34a3f12` (city-news chunk + Copyright tail).

**Medicine (two-stage, action = fix / strip):**
1. **Cross-document shingle index** (primary, high precision): drop any text chunk
   that recurs verbatim across **≥ 4 documents** — this is how pass-1 found C1 and
   is self-calibrating: unique article prose never repeats, so it is untouched.
2. **Pure-boilerplate line anchors** (supplement): strip whole lines matching the
   fixed teaser/CTA/footer marker set above, **only when the line is a document
   head/tail** (first/last ~3 lines).

**Harm test:** the line-anchored marker strip applied doc-wide touches **6/230
(2.6%) → FAILS**. The 6 are real clean articles whose *body* contains a phrase like
`महत्वाच्या बातम्या` as a sub-heading, not as chrome — the marker can't tell a
heading from a footer. The stage-1 shingle index (measured, not asserted) touches
**1/230 (0.4%) → PASS**: the single hit, `51b91de49faf6839`, carries a
`View this post on Instagram` line that recurs across ≥4 docs — genuine boilerplate,
so stripping it is arguably correct, and it is well under the bar. Unique article
prose does not recur ≥4×, so it is untouched.

**Prescription:** ship **stage 1** as the automatic fix; apply stage-2 markers only
when the line is also a head/tail line or confirmed by a second reader. The
doc-wide marker strip is too aggressive — documented side-effect, do not run it
unscoped.

**Side effects:** stage-2 unscoped removes legitimate in-body sub-headings (6 docs).

---

## D3 — foreign-language content (label, don't judge) — **107**

English/Hindi titles and full sentences sitting in a Marathi doc. Per the field
guide this is **natural** — labelled, never dropped or "fixed." Conservative
tagging: English **title prefix** or a **full** English/Hindi sentence only; bare
loanwords and parenthetical glosses skipped.

Examples: `00eed90bde196e9c` ('How To Find Sweet Watermelon:'),
`45099f1718f10018` ('Lioness And leopard Fight Viral Video'), `924d41c82dfe4138`
('Viral Video').

**Medicine:** action = **none (label only)**. Detector = script-run test: a
contiguous run of ≥ 4 Latin tokens forming a title or sentence → tag D3. No text
is altered.

**Harm test:** rule writes **0** bytes → **0/230 → PASS** trivially. (A D3 tag on
a clean doc is metadata, not harm.)

**Side effects:** none — non-destructive.

---

## C2 — intra-document duplication — **18**

Same line/paragraph repeated inside one doc beyond natural refrain.

Examples: `052f2791183c599c` (`आधी रोटी खाएंगे…` ×5), `2542e8ad88e5f64e`
(birthday-wishes block), `0e8893761b8a7317`.

**Medicine (action = fix / dedupe):** collapse a line to one copy only when it
repeats **≥ 5×** *and* is **≥ 20 chars** (guards poem refrains, quiz-answer
labels, section headers — all deliberately declined during labelling).

**Harm test:** **0/230 → PASS**. The ≥5×/≥20-char gate skips benign structural
repeats (quiz `उत्तर:`, verse refrains) a naive "any repeated line" rule flattens.

**Side effects:** a genuine 5× rhetorical refrain ≥20 chars would be clipped —
rare; accept.

---

## G2 — legacy-font (Shree-Lipi / ISCII) damage — **15**

Virama/nukta/colon corruption from legacy-font→Unicode conversion, four sub-forms:
1. `ऱ+य` with dropped virama (U+0931 U+092F), e.g. `मोठय़ा`=मोठ्या;
2. stray nukta `य़` (U+092F U+093C), e.g. `झेंडय़ाखाली`=झेंड्याखाली;
3. `रु/रू → ऊ` glyph substitution, e.g. `तऊणाच्या`=तरुणाच्या;
4. **standalone visarga `ः` (U+0903) used as the dateline colon**, e.g.
   `नवी मुंबई ः` — the old dateline-colon glyph survives on the visarga codepoint.

Examples: `db98ccd3357dd806` (`मोठय़ा`), `dd4c7834eff01ca4` (`रु/रू→ऊ`, systematic),
`506a604b057244e5` (visarga-as-colon `ता. १९ ः`).

**Medicine (action = fix / recompose):** `U+0931 U+092F` → `ऱ्य`; strip stray
`U+093C` after `य`/`र` where it yields a non-word; `ऊ→रू` **only inside a flagged
legacy-font doc** (context gate); a lone `U+0903` bounded by spaces → `:` (dateline
colon). The conjunct-gibberish variant (fully garbled `डअध छज …`) is unrecoverable
→ `drop` or flag, not auto-fix.

**Harm test:** legacy patterns (`ऱय`, stray `य़`, standalone visarga-colon) occur in
**0/230** clean docs → PASS. The visarga-colon rule is gated to a space-bounded lone
U+0903 so it never touches a legitimate word-final visarga (`स्वतःच`, `यशः`).

**Side effects:** `ऊ→रू` is context-gated to legacy docs to avoid corrupting the
legitimate vowel ऊ; outside that gate, leave alone.

---

## A5 — अॅ dual-encoding — **13**

Same vowel sign encoded two ways: `अ + ॅ` (U+0905 U+0945) vs `ऍ` (U+090D). NFC does
**not** unify them. Examples: `1afac20e086d5472` (U+0905+U+0945+प),
`8207d3c24ce05878` (अॅलोवेरा, अॅसिड), `8be5674f271d5ed9` (अॅप ×6).

**Medicine (action = fix / normalize):** normalize to a single form **only in docs
where both encodings co-occur** (the coexist gate). Do **not** normalize everywhere.

**Harm test:** the naive "normalize every अॅ" rule touches **8/230 (3.5%) → FAILS**
— because अॅप / अॅक्शन / अॅलोवेरा are *normal* Marathi loanword spellings. The
**coexist-only** rule touches **0/230 → PASS**: a clean doc uses one consistent
encoding, never both.

**Side effects:** none under the coexist gate; unscoped normalization mangles
everyday loanwords (documented — do not ship unscoped).

---

## D4 — broken machine translation — **12** · (drop)

Ungrammatical word-salad Marathi from MT of foreign-site content; word order
destroyed. Examples: `48fa412a505a1e68` (Spanish grooming site, `hombresconestilo.com/mr/`),
`fc9290beea94f4df`, `fef7b755c76715d1`.

**Medicine:** action = **drop** (unsalvageable). Detector: source URL carries an
MT marker (`/mr/`, `/mt/`, translate param) **and** a Marathi grammaticality score
below threshold → drop. **Both gates are required.**

**Harm test:** the URL marker **alone** touches **3/230 (1.3%) → FAILS**:
`526f8907` (inheritanceneeds.com/mr/), `38326254` (happiesthealth.com/mr/),
`089a742f` (thefreemedia.in/mr/) are all `/mr/` localized URLs whose Marathi is
**fluent** and was read clean. So the grammaticality gate is doing real work — it
is what keeps these three out of the drop set. With no local grammaticality scorer,
D4 ships as **review-assisted** (URL marker shortlists candidates; a reader
confirms the word-salad before drop), not fully automatic.

**Side effects:** URL-marker-alone would wrongly drop fluent localized content
(the 3 docs above) — never ship it without the second gate.

---

## C3 — truncation — **9** · (fix/drop)

Doc cut mid-sentence or carrying an explicit truncation marker. Examples:
`c5c7f7feea32245d` (ends `[…]` @445), `a84ec9a0a34a3f12` (copyright cut-off),
`23d8d35ab252e3c4` (incomplete Wikipedia para).

**Medicine (action = drop if body lost, else fix/trim):** flag only on **explicit
truncation markers** — `[…]`, `Continue Reading`, `Read More`, trailing `...` at
EOF — not on "no terminal punctuation."

**Harm test:** the naive "ends without sentence punctuation" rule touches **19/230
(8.3%) → FAILS** (clean docs legitimately end on a heading, list item, or quote).
The explicit-marker rule touches **1/230 (0.4%) → PASS** — the single hit,
`c85acdaeebe64599`, ends `…स्लाईड्सवर क्लिक करा...` (a "click next slide" CTA whose
trailing `...` is rhetorical, not truncation). Under the bar, documented.

**Side effects:** rare clean docs ending in a rhetorical `...` CTA (1 above) would
be mis-flagged; the explicit-`[…]`/`Continue Reading` subset avoids even that.

---

## B4 — template / code junk / filter-evasion — **8** · (fix)

`:-`/`-`/`'` inserted inside words to dodge filters; unrendered WP shortcodes
(`[sc_fs_faq …]`, `[ad_1]`); placeholder PII (`firstname.lastname@example.org`);
stray markup glyphs (orphaned superscript `⁵`). Examples: `f21b3178cb113107`
(`ध:- म:- का:- वू:- न`), `05045fec2475fdb9` (shortcode @8232), `a17a859aa9af0546`
(placeholder email `firstname.lastname@example.org`).

**Medicine (action = fix):** (a) strip known shortcode tokens by literal list;
(b) remove intra-word `:-` only when a doc has **≥ 3** intra-word `:-` occurrences
(filter-evasion signature), re-joining the splinters; (c) delete a lone orphaned
superscript/markup glyph on its own line.

**Harm test:** the naive "remove any `:-`" rule touches **11/230 (4.8%) → FAILS** —
`:-` is a normal dateline/time separator (`मुंबई :-`, `10:-30`). The **tokens +
intra-word-`:-` ≥ 3** rule touches **0/230 → PASS**: no clean doc splinters 3+ words.

**Side effects:** none under the ≥3 gate; the blunt `:-` strip mangles datelines
(documented — do not ship).

---

## C4 — two/more documents joined — **8** · (fix/drop)

Unrelated texts concatenated with no boundary, or a shared boilerplate block welded
across docs. Examples: `654e623661c0b8c6`, `0cd78c6d499c4cb5`, `1686935b1034083d`
(unrelated company share-price paragraphs joined → drop).

**Medicine:** two paths. (a) Shared-block removal: the same **cross-document shingle
index as C1 stage-1** (chunk recurs across ≥ 4 docs → strip). (b) True two-doc
splices (topic A then unrelated topic B) have no automatic cut point → **drop**.

**Harm test:** the shingle index touches **1/230 (0.4%) → PASS** (the same single
Instagram-caption doc as C1 stage-1; it shares one implementation). The splice-drop
path is review-flagged (no safe automatic boundary detector).

**Side effects:** none beyond C1 stage-1's; the splice case is human-confirmed.

---

## D5 — translationese — **8** · (drop)

Literal MT that is grammatical but unnatural — calqued English idioms. Examples:
`8201070a548d3e9d` ('एक लहान बाटली खूप लांब जाईल' = "a little bottle goes a long
way"), `d9abc0a9e976cd2f` (codegym auto-translation), `235af31f6022ea73`.

**Medicine:** action = **drop**. No reliable automatic detector — flagged by reader
judgement on calque idioms + foreign source domain. **Do not auto-run**; this is a
human-review disease.

**Harm test:** no automatic rule to run → not applicable (review-only). Any
automated proxy for translationese would over-reach; left as review-only.

**Side effects:** none automatic; manual drop risks subjectivity — keep the
foreign-domain corroboration requirement.

---

## F1 — PII leak — **8** · (fix)

Phone numbers (Latin or Devanagari digits), emails leaked into body. **Never copy
the value** — evidence is type + offset only, hex empty. Examples:
`26dda2c33506f1ff` (phone @2435), `dac55ea8bc131eb1` (phone @10), `6169b09fe7801904`
(email @1171).

**Medicine (action = fix / redact):** redact matches of a phone regex
(`(?<!\d)[6-9]\d{9}(?!\d)` + Devanagari-digit and delimited variants) and an email
regex, replacing with a `[redacted]` token. Offsets logged, values never stored.

**Harm test:** **0/230 → PASS** — the phone/email regexes match nothing in the
clean set. (Placeholder `example.org` emails are the B4 cases, which are `fix`
docs, not clean.)

**Side effects:** a 10-digit non-phone (e.g. a long ID) could be redacted — low
rate; the `[6-9]` leading-digit gate limits it to plausible Indian mobiles.

---

## C5 — keyword / link lists, SEO spam — **6** · (fix)

Tag clouds, SEO keyword-slugs, and product keyword lists dumped into article text.
Examples: `626fc9159542b61c` (`Tags: Diabetes`), `4ab66b3a5d21bfe7` (SEO slug
`(odi world cup 2023 hardik pandya fitness update)`), `bc8ad309586730d2`
(`बांबू पलंग / बांबू खुर्ची / बांबू टेबल …` repeated-head product list).

**Medicine (action = fix / strip the list block):** strip a line/segment matching
any of (a) an explicit tag label `^(Tags?|टॅग|कीवर्ड)\s*:`; (b) an English SEO slug
— ≥ 5 consecutive all-lowercase-ascii/digit tokens; (c) a `/`- or `|`-separated run
of ≥ 4 items sharing a repeated head word (Devanagari keyword list).

**Harm test:** the naive "any line with ≥6 comma/pipe tokens" rule touches **28/230
(12.2%) → FAILS** (normal Marathi comma lists). The tight rule (a)+(b)+(c) touches
**1/230 (0.4%) → PASS**. (The three C5 docs it does not catch —
`5c05e18231a55839`, `ea74237e4114182f` — are news-site chrome labels that overlap
C1 and are handled by the C1 shingle index.)

**Side effects:** rare clean doc carrying a genuine lowercase English slug (1 above)
— under the bar; the tag-label clause alone is near-zero risk.

---

## Summary table

| Disease | Count | Action | Naive rule (harm/230) | Shipped rule (harm/230) |
|---|---|---|---|---|
| C1 | 161 | fix/strip | markers 6 (2.6%) FAIL | shingle ≥4 docs → 1 (0.4%) PASS (stage-2 scoped) |
| D3 | 107 | label only | — | 0 PASS (non-destructive) |
| C2 | 18 | fix/dedupe | — | ≥5× & ≥20ch → 0 PASS |
| G2 | 15 | fix/recompose | — | legacy patterns → 0 PASS |
| A5 | 13 | fix/normalize | all-अॅ 8 (3.5%) FAIL | coexist-only → 0 PASS |
| D4 | 12 | drop | URL-marker 3 (1.3%) FAIL | URL + gram gate → review-assisted |
| C3 | 9 | fix/drop | no-punct 19 (8.3%) FAIL | explicit markers → 1 (0.4%) PASS |
| B4 | 8 | fix | any `:-` 11 (4.8%) FAIL | tokens + `:-`≥3 → 0 PASS |
| C4 | 8 | fix/drop | — | shingle ≥4 docs → 1 (0.4%) PASS (splice=drop) |
| D5 | 8 | drop | — | review-only (no auto rule) |
| F1 | 8 | fix/redact | — | phone+email regex → 0 PASS |
| C5 | 6 | fix/strip | token-list 28 (12.2%) FAIL | tag+slug+head-list → 1 (0.4%) PASS |

**Headline finding:** every naive first-pass medicine that looked obvious (strip all
boilerplate markers, normalize all अॅ, drop any unpunctuated tail, remove any `:-`,
strip any comma-list) **FAILS** the 1% harm bar — each over-reaches into normal
Marathi. The shipped rules are the *narrowed* versions (co-occurrence gate,
cross-document recurrence, explicit markers, count thresholds, tag/slug shapes),
all **≤ 1/230 → PASS**. Two diseases cannot be fully automated to the bar and ship
**review-assisted**: **D4** (URL marker alone wrongly drops 3 fluent localized docs
— needs a grammaticality gate) and **D5** (no reliable automatic detector).

**Caveat:** the proxy gold set is one reader (me). A real two-reader gold set would
likely expose further C1/D3/C5 edge cases; the PASS results are necessary, not
sufficient.
