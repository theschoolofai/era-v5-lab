# English reading audit (task 7): en-nemotroncc-synth

Kunal Sinha (`kunal2016`). 50 cleaned docs: the en-nemotroncc-synth half of row 7 (Harini Jasti's assignment), taken
over for the spec v1.1 deadline. Log: [`reading_en-nemotroncc-synth_kunal.csv`](reading_en-nemotroncc-synth_kunal.csv).

## How it was read

- Data: "Week 2: cleaned tokenizer sample v0-clean", Train `en-nemotroncc-synth/part-00000.parquet` (Part 1) and
  `part-00001.parquet` (Part 2). Heldout not used.
- Docs: rows **1-50** of `pick_docs.py` over Part 1 then Part 2 (196,907 docs), seed **20261101**. These are the 50
  IDs listed under en-nemotroncc-synth in the team's reading doc.
- Cleaner: spec v1 `clean.py` of PR #244, as shipped in v0-clean. Checked: the cleaned text of all 50 docs is
  identical to the output of `clean.py` at `c0b29d1` (patilvijay23/g1-specv1). On these 50, cleaning changed 1 doc
  (`DA-B4-007`), kept 49, dropped none.
- The full cleaned text of every doc was read. Offsets are character start-end (0-based, end exclusive) in the cleaned
  text.
- AI used: yes. Claude read the 50 docs and suggested 21 candidate findings with offsets; I read each against the
  cleaned text, kept 16 and dropped 5 (two closing advert lines, an opinion rather than a factual error, a possible
  author spelling, a footnote list that starts at 2). All rows are `source=ai`.
- `missed` = spec v1 has a rule for the disease on this pack; `new` = no rule covers it on this pack (`C4` has no rule
  in spec v1, so it is logged as `new` with its existing code).

## Findings table

4 missed findings in 4 docs, 12 new in 10 docs, 0 harm. 37 of 50 docs had no finding.

| code | kind | docs affected | % of docs read |
|---|---|---|---|
| `B4` | missed | 3 | 6% |
| `C1` | missed | 1 | 2% |
| `C4` | new | 4 | 8% |
| `NEW-factual-error` | new | 4 | 8% |
| `NEW-appended-qa` | new | 3 | 6% |
| `NEW-missing-code` | new | 1 | 2% |

## Where the existing rules miss

- **`B4`, rewrites that refer to their source (3 docs).** `DA-B4-007` deletes the synthetic meta phrases "not … in the
  given/provided text" and "the given/provided text". These docs use other wording and are kept as they are:
  "The user expresses disdain …" (every line of `82aa41d29e468a85`), "The speaker attended …" (`0407920ed49eb6af`),
  "The text discusses carbon taxes …" (`55eb060ae2bc2600`). Widening `META` to sentence-initial "The user / The
  speaker / The text discusses" would catch them; it needs a harm check, since "the speaker" is ordinary English.
- **`C1`, an image credit line (1 doc).** `c3d88009d8a459e9` keeps "Paul Tong / Op Art" as its own line between
  paragraphs. `DA-C1-006` targets menus, share bars and footer links, not caption credits.
- **`C4` has no rule in spec v1 (4 docs).** Joined documents pass through: `ffaad5c6d3dde332` (a press release ends
  with `###` and a credit line, then an unrelated stem-cell article), `b4281ea0782a6671`, `52bd1da881ee0592`,
  `bf1cefdecf84bf1a`.
- **Appended Q&A (3 docs).** `DA-B4-007` removes a Q&A pair only when it carries a meta phrase; a plain trailing
  `Question: … Answer: …` stays (`5aeafd200220c080`, `ffaad5c6d3dde332`, `c3d88009d8a459e9`).

## New diseases

| name | description | docs |
|---|---|---|
| `C4` (no rule in spec v1) | two or more unrelated texts joined with no boundary: a press release then an unrelated science article; a book list then a company profile; biblical covenant notes then the Scottish Covenant; five unrelated topics in one doc | 4 |
| `NEW-factual-error` | a checkable error introduced by the synthetic rewrite: Victoria called "the Virgin Queen"; "battles of Artemisia" for Artemisium; "Exodus 9" for Joshua 9; a camera comparison reversed (the fixed-lens model is the XC10, not the 1Ds) | 4 |
| `NEW-appended-qa` | a synthetic `Question: … Answer: …` pair appended after the passage; in 2 of 3 the answer is wrong or unsupported (Leven called the Duke of Lauderdale; "The Institute" for the Albert Shanker Institute) | 3 |
| `NEW-missing-code` | the text announces a code example ("consider the following compact, yet complex, example") that is not in the document | 1 |

`C4`, `NEW-factual-error` and `NEW-appended-qa` are each in 2 or more docs, so each is above the 1% bar for the
English domain (2+ of 200).

## Harm

None. The only doc cleaning changed, `390b9ed0ffbd7fb6`, lost the line "Release Year: Not specified in the given
text": a correct `DA-B4-007` fix.

## Open questions for the lead

- `C4`, `NEW-appended-qa` and `NEW-factual-error` are each in 2+ docs. Should they go to Smita and Aneesha for spec
  v1.1? `NEW-appended-qa` looks rule-able (a trailing `Question: … Answer: …` block); `C4` and factual errors probably
  need a model or a classifier rather than a regex.
- `B4`: should `DA-B4-007` be widened to the "The user / The speaker / The text discusses" meta-references, or stay
  narrow for v1.1?
- Is a factual error introduced by a synthetic rewrite a disease for this audit, or out of scope?
- The en-nemotroncc half of row 7 (50 docs) may still need a reader.

## Doc IDs read (reading order = shuffle order)

1. `878f9d48ad498922` — clean
2. `5aeafd200220c080` — NEW-appended-qa
3. `f0a4a58b7f9a01e3` — clean
4. `8e8d8d665724ee0e` — clean
5. `482459b361873245` — clean
6. `5ffd22882ba35f3e` — clean
7. `7264a177c61434df` — clean
8. `0f7b90400c1362df` — NEW-factual-error
9. `d8dcee236fef69c3` — clean
10. `ccabc5a234934fd0` — clean
11. `66059039c4d0cd16` — clean
12. `488b525016dbab19` — clean
13. `cb69e3410c5bc9df` — clean
14. `70ab4763836d77e3` — clean
15. `390b9ed0ffbd7fb6` — clean
16. `0407920ed49eb6af` — B4
17. `82aa41d29e468a85` — B4
18. `6ab044802b5ccaed` — clean
19. `280503e96a840313` — clean
20. `23b10d26ac886d57` — clean
21. `51a0b4027f575f76` — clean
22. `58f93564f62c3f74` — clean
23. `638aac23790e95ea` — clean
24. `c4aadf93ec2178b1` — clean
25. `9d81ac9b8c93267a` — clean
26. `7d820d691c590509` — clean
27. `ea84635879759482` — NEW-missing-code
28. `bea84f90415a5b5d` — clean
29. `92575d2502926a56` — clean
30. `40d51909df47f1e0` — clean
31. `0f7240ba1fdd3411` — NEW-factual-error
32. `94c2efea7c6ce4f6` — clean
33. `2c33678d82db9ffa` — clean
34. `55eb060ae2bc2600` — B4
35. `18fa47308d9fe79e` — clean
36. `ffaad5c6d3dde332` — C4, NEW-appended-qa
37. `c3d88009d8a459e9` — C1, NEW-appended-qa
38. `f417dd85463514c8` — clean
39. `b4281ea0782a6671` — C4
40. `52bd1da881ee0592` — C4, NEW-factual-error
41. `6d46a2f7ae209851` — clean
42. `b36e53dbb443169d` — clean
43. `ff4162ecf3f8c204` — clean
44. `1877686d8ee63f8c` — clean
45. `c9cc0b7d991bbf9f` — clean
46. `afec255188660355` — clean
47. `f2a8b2cc25bb5c7a` — NEW-factual-error
48. `420d6e3cde0965e4` — clean
49. `bf1cefdecf84bf1a` — C4
50. `af5340cf280d1651` — clean
