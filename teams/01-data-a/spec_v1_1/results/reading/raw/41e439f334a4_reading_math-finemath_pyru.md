# Math reading audit (task 9): math-finemath

Reader: pyru. Row 9 of the Week 2 assignments (math-megamath is read by the partner). 199 docs: the 100 picked with
`pick_docs.py`, plus 99 extra docs from my earlier read (PR #27), kept as the lead asked.
The findings are in `reading_math-finemath_pyru.csv`: one row per finding, 332 rows, positions only.
Rows 1-184 are the 100, rows 185-332 the extra 99.

## How it was read

- **Pack file:** tokenizer sample v0-clean, `train/math-finemath/part-00000.parquet` (Part 1; math-finemath has no Part 2).
  28,522 docs, sha256 `7b3366baf9b8b756…`, as listed in `cleaned_manifest.json`.
- **Cleaner:** spec v1 as run by TSAI on #244: `clean.py` sha256 `97c1a55b…` at `8da2ac4`. Rule IDs in this file
  are the ones that ran in that job (for example `DA-C2-001`, `DA-D3-005`), not the v1.1 sheet numbers.
- **Offsets:** code points in the cleaned text of that job, end exclusive. A whole-doc finding is `0-<length>`. A harm
  row gives the point in the cleaned text where the rule removed the text (`p-p`).
- **quote:** left empty in every row. The sample holds personal data, so no document text goes into the repo;
  `why` is written in my own words.

**The 100 (pick_docs.py)**

- **Seed and pick:** 20261101, the `pick_docs.py` method, rows 1-100: the doc_ids in file order, shuffled with
  `random.Random(20261101)`, first 100. The list is at the end of this file.
- **Changed by the cleaner:** 33 of the 100: `DA-C2-001` 17, `DA-C1-001` 14, `DA-A1-005` 3, and
  `DA-A3-001`, `DA-A5-002`, `DA-A6-003`, `DA-B2-001`, `DA-D3-005` 1 each. These come from a rule-by-rule trace with the
  same math rules, and the trace output matches the job output on all 100 docs.
- **Method: AI-assisted.** Claude (Anthropic) made a first pass over all 100 docs and suggested 184 findings. In a
  local reading page I accepted all 184; I rejected none and added none. Every row therefore has `source` = `ai`.
  The 9 docs with no suggestion have no rows.

**The extra 99 (earlier read)**

- **Pick:** the 100 docs read for PR #27 (now closed), picked with `random.Random(20261101).sample()` over the sorted
  doc_ids of the same 28,522 cleaned docs. `2842cc032aca51f3` is also in the 100, so it is counted there only.
  The list is at the end of this file.
- **Text:** read on 1 Nov on my own spec v1 run (`clean.py` at `67e6187`), before the job output was out. The job output
  has the same docs, and 98 of the 99 texts are identical. In `e1d06f4e49257cfe` the job's F1 rule replaced an email,
  so its C1 span is 12 characters shorter. The offsets here are in the job's text.
- **Changed by the cleaner:** 26 of the 99. 25 by the math rules: `DA-C1-001` 12, `DA-C2-001` 11, `DA-A3-001` 3,
  `DA-A5-002` 2, `DA-D3-005` 2, and `DA-A1-005`, `DA-A6-003`, `DA-B2-001`, `DA-B5-001` 1 each. 1 by the shared F1 rule
  only (`e1d06f4e49257cfe`).
- **Method: AI-assisted,** as for the 100. Claude suggested 148 findings on that sample of 100 on 1 Nov. I accepted
  all 148; I rejected none and added none. 147 of them are on these 99 docs, all with `source` = `ai`. The 10 docs with
  no suggestion have no rows.
- **Decontam scan:** one more row comes from Team 9's scan (#342), not from the reading: F2 in `5a93d530d9026175`,
  with `source` = `manual`. Of the 35 math-finemath docs in that scan, it is the only one in these 199 docs.
- **Kinds:** as in this README. NEW codes, and diseases with no math rule (B1, C4, E1, E2), are `new` (PR #27 had them
  as `missed`). 13 rows were marked unsure in the page. This README has no unsure kind, so they keep the closest kind
  and their `why` starts with `unsure:` (B5 5, C5 4, NEW-ai-generated-text 3, NEW-unattributed-copy 1).

## Findings table

332 findings in 180 of the 199 docs; the other 19 docs have no finding. Kinds: missed 221, new 104, harm 7.
The last two columns split the docs affected between the 100 and the extra 99.

| code | kind | docs affected | % of docs read | the 100 | extra 99 |
|---|---|---|---|---|---|
| C1 | missed | 136 | 68.3% | 68 | 68 |
| NEW-missing-formulas | new | 26 | 13.1% | 15 | 11 |
| NEW-flattened-formulas | new | 20 | 10.1% | 14 | 6 |
| B5 | missed | 18 | 9.0% | 8 | 10 |
| C2 | missed | 18 | 9.0% | 8 | 10 |
| C5 | missed | 10 | 5.0% | 5 | 5 |
| NEW-merged-table-cells | new | 10 | 5.0% | 7 | 3 |
| NEW-seo-filler | new | 10 | 5.0% | 7 | 3 |
| NEW-ai-generated-text | new | 8 | 4.0% | 4 | 4 |
| NEW-template-pages | new | 8 | 4.0% | 5 | 3 |
| DA-C2-001 | harm | 6 | 3.0% | 2 | 4 |
| A3 | missed | 5 | 2.5% | 5 | 0 |
| NEW-missing-spaces | new | 5 | 2.5% | 3 | 2 |
| B4 | missed | 4 | 2.0% | 0 | 4 |
| B1 | new | 3 | 1.5% | 1 | 2 |
| B2 | missed | 3 | 1.5% | 2 | 1 |
| C3 | missed | 3 | 1.5% | 2 | 1 |
| D4 | new | 2 | 1.0% | 2 | 0 |
| E2 | new | 2 | 1.0% | 1 | 1 |
| A4 | new | 1 | 0.5% | 1 | 0 |
| C4 | new | 1 | 0.5% | 0 | 1 |
| D2 | new | 1 | 0.5% | 1 | 0 |
| D3 | missed | 1 | 0.5% | 0 | 1 |
| DA-D3-005 | harm | 1 | 0.5% | 1 | 0 |
| E1 | new | 1 | 0.5% | 0 | 1 |
| F2 | missed | 1 | 0.5% | 0 | 1 |
| NEW-dropped-ligatures | new | 1 | 0.5% | 0 | 1 |
| NEW-hyphen-split-words | new | 1 | 0.5% | 1 | 0 |
| NEW-interleaved-columns | new | 1 | 0.5% | 1 | 0 |
| NEW-missing-code-lines | new | 1 | 0.5% | 0 | 1 |
| NEW-orphan-figure-labels | new | 1 | 0.5% | 1 | 0 |
| NEW-unattributed-copy | new | 1 | 0.5% | 0 | 1 |

Where the existing rules miss (from the `missed` rows):

- **C1 (136 docs):** forum post headers and user-info blocks, Q&A comment signatures and timestamps, related-question
  and related-document blocks, search-page chrome, breadcrumbs, adverts and sign-up widgets.
  - The C1 line rule needs a whole-line match, so it misses chrome lines that carry a markdown heading prefix (a
    similar-questions heading, tag toggles) in `4ffb288e0df06071` and `885bc9229d4bb0bf`.
  - In `c63a6dd114e246eb` and `91bf5e3b4ad423ee` its line filter removes the reply/view labels before its own
    reply-view block pattern runs, so bare counts are left.
- **C2 (18 docs):** mostly quoted forum posts that repeat earlier posts. The quote is joined to the reply text or split
  into short blocks, so neither the line rule nor the passage rule sees it. Also a repeated answer, a repeated bot
  message, and widget or metadata lines repeated on every item.
  - Also, the keep-first copy of a repeated line stays: a UI button line (`053c7e6dfbdb4e46`, `fcc79d8f03cf663e`) and
    the stage and difficulty lines of search listings (`50963f2a333bf053`, `f27d1907594e1111`), counted as C1.
- **B5 (18 docs):** units and exponents broken by a site's math converter (3 docs), site-specific math delimiter tags
  and markup, currency dollars that clash with math delimiters (2 docs), dollars escaped with a backslash inside code
  and math (2 docs), code fences doubled to six backticks (2 docs), prose wrapped whole in a code fence (2 docs), and a
  broken LaTeX command. Marked unsure: currency written with escaped dollars (4 docs) and a macro that exists only on
  the source site.
- **C5 (10 docs):** listing and search-result pages, keyword lists, and a see-more link in the middle of a line. The C5
  rule needs Title-Case phrases at the start of a line. In the extra 99, 3 whole-doc search listings and a
  resource catalogue are marked unsure.
- **A3 (5 docs):** mojibake from other code pages: Cyrillic cp1251, Greek cp1253, Thai cp874 and Central
  European cp1250. The rule repairs only cp1252 and cp866. In `6647e054e451c4dc` about 20 emojis became a lone pi
  sign, which reads as maths.
- **B4 (4 docs):** notebook export leftovers, unfilled template code, slide placeholder text and an empty template
  value.
- **F2 (1 doc):** `5a93d530d9026175` holds a past exam question that is in the MILU test set (Team 9 scan, #342). The
  job ran without F2, and the reading did not catch it.

## New diseases

The README bar is 2 or more docs in a domain (1% of 200). The first ten rows here are at or above it, so they go to
spec v1.1.

| name | what it is | docs |
|---|---|---|
| NEW-missing-formulas | formula or number images and symbols dropped by the scraper; the text points to a formula that is not there | 26 |
| NEW-flattened-formulas | superscripts, subscripts and fractions flattened to plain digits, or split one token per line | 20 |
| NEW-merged-table-cells | tables run into one line or broken one cell per line, so values lose their row and column | 10 |
| NEW-seo-filler | SEO pages and paragraphs: question headings with pasted answers, site-wide filler text, spun articles | 10 |
| NEW-ai-generated-text | machine-written articles or AI summaries and FAQs, some with false statements (3 of the 8 marked unsure) | 8 |
| NEW-template-pages | pages generated from a template for one number or unit value | 8 |
| NEW-missing-spaces | words and sentences run together where line breaks were lost | 5 |
| B1 (no math rule) | HTML entities left in the text | 3 |
| D4 (no math rule) | spun text: a rewriter swapped words for odd synonyms | 2 |
| E2 (no math rule) | data blobs: hash values, a JSON copy of a worksheet's questions | 2 |
| A4 (no math rule) | symbols replaced by question marks | 1 |
| C4 (no math rule) | an unrelated discussion thread from a site widget appended after the lesson | 1 |
| D2 (no math rule) | romanised Hindi comments | 1 |
| E1 (no math rule) | a machine-generated test report of a computer-algebra rule set | 1 |
| NEW-dropped-ligatures | fi, ff and ffi ligatures dropped by a PDF text layer, so words lose letters | 1 |
| NEW-hyphen-split-words | print line-end hyphens left inside words | 1 |
| NEW-interleaved-columns | two-column PDF pages read across both columns, so sentences of two exercises alternate | 1 |
| NEW-missing-code-lines | programs with lines already missing on the source page, so the code cannot run | 1 |
| NEW-orphan-figure-labels | bullet lists of figure labels left from an interactive scene | 1 |
| NEW-unattributed-copy | marked unsure: a CC BY-SA encyclopedia article copied by a mirror site with no attribution | 1 |

## Harm

| rule | what it deleted | docs |
|---|---|---|
| `DA-C2-001` | real lines that repeat by design. In `f85486e0d9ad0a50`, 30 survey trial lines, leaving 8 trials empty. In `3bc7339b3365a201`, 7 of 8 copies of a curve equation, including a working step and the line a later reply points to. In `404146d814b03d07`, 4 print statements of Python examples. In `1b1a0d909bc9c515`, 44 program-output and translation-note lines, so several outputs no longer match their programs. In `bf617118c1ef6d8b`, 8 column headers of R matrix printouts. In `f8993128de3e2a07`, the instruction line of problems 2 to 14. | 6 |
| `DA-D3-005` | 98 formula and number lines (hypotheses, test statistics, data values) in `1eadf4cf278db7e6`. The PDF text is cp1251 mojibake, so its Greek letters and signs count as Cyrillic. | 1 |

## Open questions for the lead

1. **A3 and D3:** extend the A3 repair to cp1251, cp1253, cp874 and cp1250? A3 already runs before D3. While A3
   cannot repair cp1251, D3 deletes those lines as Cyrillic, and that is where the harm in `1eadf4cf278db7e6` comes
   from.
2. **C2 line rule:** limit it (for example skip lines with digits or `$`, lines inside numbered items, or lines inside
   code and its output)? It harms 6 of the 199 docs.
3. **C1:** allow an optional markdown heading prefix in the whole-line phrases, and run the reply-view block pattern
   before the line filter?
4. **Listing, template, SEO and AI-written pages:** drop them by rule, or leave them to the quality filter?
5. **Escaped currency dollars:** 4 docs write every amount with a backslash before the dollar sign. Is that fine as
   the FineMath convention, or is it B5? Marked unsure.
6. **Unattributed CC BY-SA copy** (`c9cc04b4cece5d95`): drop it under the licence rule, or keep it? Marked unsure.
7. **quote column:** left empty because of the personal-data rule. Is that fine for the consolidation?

## Doc IDs read

The 100, `pick_docs.py` rows 1-100 (reading order = shuffle order):

```
f85486e0d9ad0a50 02265dbc8fa20259 7aa25f450cbc9b70 1ab888d9366a43fd fe843a72092064cd
0610be9612d18bc6 ee9ac5fd44a100b7 56aadb5db0327910 9e9292036542a1b0 9373e806c8ee0ac8
54656567cb9c8e38 32b1f031d8c464e4 0815e685a1a74bda f19cd0cc87cb399a a48d37861a2ab782
8f098ccbede3a46d 920808a906ef229b dcd6058ecb2cfc18 743e8c255952e983 4ffb288e0df06071
8d724d02426ad3ff 7872171b9bf54929 2334d216e03d1058 789dfcb4222e401e 767037306d97bc86
42c81cfd52a5849d d72a2a98549b9142 c63a6dd114e246eb 9453359091e63dfc a77ec4895195a433
facfd603bc865298 afa476465dcc2169 25e224253f9a5c0a 26bf10df32e94547 d805befbd984308c
9dd2fc49a23b7e73 10d547035dd610e2 053c7e6dfbdb4e46 fd804060f7a299ac 4ac56ea0cf68007b
6647e054e451c4dc b1925e5c2908520f e7211e16ef44de51 4e9a082228b0c45e 885bc9229d4bb0bf
e492f103e239bec0 f09378316ce939e1 a8004bba3cd5bbfb dc76a8ad4d35952e ec20a4ca6692ddb7
63783f04778f7000 8d53fca95d65362b 26fc94c2c763ffaf 291cff41d0672085 2fb9464195bf2edc
cb9a946cd4eba389 322fa2d2c8fd6470 3567192e9fc75b00 90d9ff5ef9c45a37 6712725af9da5453
a91801046f79b716 4783c724f8fbfa52 31a477d3965aebee a345d577da510a26 d68e2a6365d972da
d3c81797986b7e17 473eccb431e6029a 0499a6d6c38ef86f 8d88bdd73268baaa b47ab81de0a41d92
02b5f8e058694237 06f2d75b8c5610f1 fdb1238e2b5a4d0c 9c393ad230dc838b a919c1b20d1178f0
e71f555ad2f37d57 28f56e454b2ade39 1eadf4cf278db7e6 1f2abff491b96656 3bc7339b3365a201
3825a12534054bb3 0a34dcef3fe6b07a 6aea632beaa6aacf 9b89f0605fe52eea f3a2d01395300022
fcc79d8f03cf663e 379ab92860d593f5 d0693c18056bae02 4f2da70883d8d65f ec4ea0009df33e1a
0614bc6ecf034495 c7e8da53587e0e2a 6f08675347237529 74b959b3e8c2b31b 2842cc032aca51f3
033ab42a96110ff9 cc0bf2c48f0be1a8 ec7ecf0ffc763747 5073e2edc460a575 cdccda71cb0f4ff3
```

Docs with no finding (no rows): `56aadb5db0327910`, `b1925e5c2908520f`, `e7211e16ef44de51`, `26fc94c2c763ffaf`, `322fa2d2c8fd6470`, `31a477d3965aebee`, `0499a6d6c38ef86f`, `02b5f8e058694237`, `fdb1238e2b5a4d0c`.

The extra 99, in the order of the earlier read:

```
d8cdfe9d696affee 1b1c42eddd14c8e7 2206a4b3f2fa1c98 74081137bc07599a 11ece04d6039799d
cc98b78d56e7d12a 0d5843ac84b81432 0f2f052fd95da6d4 bfb1450cc0baabcd 404146d814b03d07
50963f2a333bf053 611df2fbc4c0e699 251134e031c49770 29e09f00864fb729 83efffa29c3912fb
a4e9be8e5651af40 f54f128a54a43837 f799043f1ea9cf26 f69cc8bbc85d948a 8f88eda8c99d74b2
1b1a0d909bc9c515 b7a39f13e9256ff5 006ffef8ad023034 684104b74a06267b 085f9f7987b7cf56
908532d474dd5b6b 726a52bba345c3bc 1e7fad525310d310 91bf5e3b4ad423ee 02184129b68ce0ae
36c3e8b4b4457083 c91ec668b0457861 e6b99ccca7c2ddc9 2030d68728594df9 b9174a22f4a5f9aa
61515ee94cba4c0c fc3df208c596140d 487be44b6ec97e28 35e1acff2d77be17 5a93d530d9026175
5ff99d750078fcc5 e1d06f4e49257cfe 0930f3267a518a19 2e13692256fe1603 e10da4c47ad873bd
45d9549b8abddacd 7a022b5b6866075b 5788f0b66f0d48e2 647d9713533c5664 48f9583ca4f5f6d7
8758fc16164dd1b6 fe988ef1a6257c35 78a24d025dbbec07 97998a6e3228aef8 0e89fda818263262
b0db84c6cc4bfa1d 125fe0fb9ea9baf6 841c670703589d6f 8368193ce67a8aed 2efabdcf89a1b7fd
627f7669b7376fb5 bf617118c1ef6d8b 8f07e29a799ad0cc eb991e7190deb462 362f33b15513ca3f
91fddbdb172ba0b0 d2994cf7f9224a43 86bde6e4d785cc63 1fecb45d0ff3dce1 6f02ef48c5a546c4
fa0a090b409130f7 2a0b42a85dad4b55 c4f8ad82ea97fd64 a2bb043ed2daf997 f285339020e1209a
e9bdb26928ae1153 8f1f8a9c194e88f2 909260e5184ccd7f ac3b6e69316582a1 bb610211dc626e72
d420078066dbe0e3 d10ec0084ee609b0 f8993128de3e2a07 0156e747a3f842b7 cb0c11649966e8e2
21a4cd70d938f919 c9cc04b4cece5d95 2c28686b0e067a28 f27d1907594e1111 ddb33aaa60f363c7
9dd8f31bc427673c 2c170d176eb7921c fd9c962e0eed27f4 add901f9b4e42472 8a65dd95beda74c4
3de57c8832f9a452 8df3b2b6e4aa72b7 88ccc6ac7603665c 349089a95c833a09
```

Docs with no finding (no rows): `251134e031c49770`, `908532d474dd5b6b`, `02184129b68ce0ae`, `b9174a22f4a5f9aa`, `5ff99d750078fcc5`, `45d9549b8abddacd`, `7a022b5b6866075b`, `909260e5184ccd7f`, `9dd8f31bc427673c`, `fd9c962e0eed27f4`.
