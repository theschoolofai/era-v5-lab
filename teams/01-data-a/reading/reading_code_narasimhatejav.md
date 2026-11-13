# Code reading audit (task 8): code-cpp, code-go, code-java

**STATUS: all 100 docs read; every finding manually reviewed by the reader.**

Reader: narasimhatejav. Row 8 of the Week 2 assignments. The findings are in `reading_code_narasimhatejav.csv`: one row per finding, 9 rows, with a `pack` column added.

## How it was read

- **Pack files:** tokenizer sample v0-clean, Train. For each pack, `part-00000 (2).parquet` is Part 1 and `part-00001.parquet` is Part 2 (the `(2)` is a browser duplicate suffix). Parts were concatenated Part 1 then Part 2. The files do not say Train or Heldout inside; the reader should confirm they came from the Train links (the README says not to use Heldout).
- **Rows per pack:** code-cpp 54,588 (40,418 + 14,170); code-go 76,955 (56,702 + 20,253); code-java 84,679 (62,443 + 22,236). `doc_id` is unique within each pack.
- **Seed and pick:** 20261101, with the repo's `pick_docs.py` (`random.Random(20261101).shuffle` on the doc_id list), `--rows 1-N` with N = 34 (cpp), 33 (go), 33 (java). The doc_ids read are listed at the end of this file.
- **Docs read:** 100 (34 cpp + 33 go + 33 java). 8 of them have at least one finding; the other 92 are clean and have no rows.
- **Cleaner:** spec v1 `clean.py` as run on PR #244 (the README's v0-clean sample). **Exact commit to confirm with the lead:** it is not in my clone. The only `clean.py` I could check is the one on `g1-reading` (last changed in `555f2d8`, 1 Nov, sha256 `d3464bda...`), which may differ from the job that made the sample. Another reader's file for the same job cites `8da2ac4`; I could not verify that.
- Every finding was then **manually reviewed** by the reader against the cleaned text, and all 9 were confirmed. `source` is `manual` for every row.
- **Offsets:** code points in the cleaned text, end exclusive. A whole-doc finding is `0-<length>`.
- **quote:** short snippet showing the problem. For E3 (secrets) the quote is empty and only the type and offset are given.
- **Not re-reported (already decided in `decisions_code.md`):** 2 to 4 line licence notes (`DA-E4-003`, blocked); author names (`DA-F1-003`, blocked); "leetcode" alone as F2; vendored copies as H3; language tags assumed correct (D1). `AUTHOR`, `EXAMPLE_PASSWORD` and similar words are the cleaner's own replacements and are not logged.

## Findings table

9 findings in 8 of 100 docs. Kinds: missed 9, new 0, harm 0.

| code | kind | docs affected | % of docs read |
|---|---|---|---|
| E4 | missed | 3 | 3.0% |
| E1 | missed | 2 | 2.0% |
| C1 | missed | 1 | 1.0% |
| E2 | missed | 1 | 1.0% |
| E3 | missed | 1 | 1.0% |

Per pack: cpp 4 of 34 docs with findings, go 2 of 33 docs with findings, java 2 of 33 docs with findings.

What the `missed` rows show:

- **E4 (3 docs, all cpp):** full licence headers (BSD 3-clause, GPL v2, and a **German-language** Apache 2.0 header) were left in. The German one suggests the E4 rules match English text only.
- **E1 (2 docs: 1 cpp, 1 java):** generated code was kept. The java one says `This is an auto-generated file: do not edit` in its own text; the cpp one is an IDL-generated GObject binding with six identical get/set blocks.
- **C1 (1 doc, java):** an empty IDE file-template header (`@Program/@ClassName/@Author/@Description:`). `DA-C1-005` targets IDE templates on java, but see open question 2.
- **E3 (1 doc, go):** a test file holds a hardcoded API key and secret key in one string. Offsets only, no quote.
- **E2 (1 doc, go):** a vendored Blowfish file where a 1,024-entry hex constant table is about 77% of the text. These are real cipher constants, so this is a judgement call (see open questions).

## New diseases

None found. Every problem I saw fits an existing spec v1 disease.

## Harm

None found. No doc showed code removed or damaged by a rule. This is not proof of zero harm: with 100 docs it only bounds the harm rate loosely, and I cannot see what was removed, only what remains.

## Doc IDs read

**code-cpp** (34 docs, rows 1-34 of the shuffle):

`6455ab7982d0ccb2 1247e834aaf22251 ec7bea7f056139ab 02ce72e94ce12a49 5e727153d4bb2e51 b4e5ad0d21ad61ed 625f45b727dca30b 55b3366d1acb0f97 305227a41ae66f58 29115cda8e60e532 650e623a5ad4b041 ea721946403098db 23e1455fb6c04416 260f5c22d6abe2e8 eda80e7310b7374e 1efc6f95927da24f 958484dcc2f83498 174e9812ca825ed8 b5824602734d5fc6 1f5f066d9264e212 9d9d1422b2261d6c 1ea6aa6f099ce221 b8ed8942251e219f c87f7ce6ca0da382 4a0b6bb025c448d0 4b92a879b7283d96 af9a4f86884eb472 500cedd644b2f41a 7eeb7a04fa94004f 4be50a580ff9a88c 28147ee9df526d52 faa1e89964f89845 91893ae4570da459 4d39458e42f9ef3e`

**code-go** (33 docs, rows 1-33 of the shuffle):

`93754e7443259cac 5239c1da96e97637 99a12963f17dbcb9 04f3e63924f06b52 7b383f4c84665082 dfd9696501ea0c82 29f34c47ed9e6844 25b1dcc85bd7f763 85ecce4a38e6449d 872ae75c172d7962 4c52560d44c2dadf 31d217362a0031c9 e8fa31db616c560b 1e20a90bd09e39e6 adf2ffa73955c935 b4887285a1d3eb2b 25ed08f4f55b7c5c 379f4d4f5855ae40 85156d78fee179b8 f46dbd415257e9e4 b96b2acadc46a8de f601aec6443fd5f3 b685e726cc2b2ffb e9ef001c1808dbe9 06e9af001dba77fa 1dee37b0b44de359 7750585553675585 b2539619cec53fc0 fd214f25fdb2a960 9bcb98b956475308 6c01c794f2e066eb 25391370a5827545 0511c858ef7a8e4e`

**code-java** (33 docs, rows 1-33 of the shuffle):

`1f4ba2571794161c 141926c5b12699e9 88f34503c00aba80 292a6dc6825ec921 794598e53e372e80 edf80bfd3cb8bc6c 4eed97e472bb15c4 413de6c9e6a07e40 d8e6491b59ad100a 2b1eb1fbcadcd293 c347430edfae2bbe 55e854d2b8607eae 32257481fbb5dafe bb064da6014aac8a 28d05c7bc35fc6c5 36e11e75c2c2fd3d 25ea90f898359174 25dd7c3571810066 3997e21e2a8d0f7f efc45cc424a1b657 47ac595a19042773 43de7e6958f10c11 d5602d6a28a2c508 daeec37ff36f59a0 56de81ab66a03469 3043e8b9e6d30d87 14beec47b700a27a 5eda8b1014543f7b 3a216fcd59cdb6bc d37cf443f5ef0f39 fda747add93ddacb 2b6aca3c694426ee ef8b2a1ff79a2cf8`
