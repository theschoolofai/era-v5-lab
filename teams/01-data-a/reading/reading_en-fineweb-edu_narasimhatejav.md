# English reading audit (task 7): en-fineweb-edu

**STATUS: all 50 docs read; every finding manually reviewed by the reader.**

Reader: narasimhatejav. The findings are in `reading_en-fineweb-edu_narasimhatejav.csv`: one row per finding, 14 rows, positions and short snippets only.

## How it was read

- **Pack files:** tokenizer sample v0-clean, Train, `en-fineweb-edu`: `part-00000 (2).parquet` is Part 1 (54,004 rows) and `part-00001.parquet` is Part 2 (17,929 rows); 71,933 docs, `doc_id` unique. The `(2)` is a browser duplicate suffix. The files do not say Train or Heldout inside; the reader should confirm they came from the Train links.
- **Docs read:** 50. 10 of them have at least one finding; the other 40 are clean and have no rows.
- **Seed:** 20261101 (the group's seed, used by `pick_docs.py`). The 50 docs read were supplied by the reader and were not chosen by that seed; see the next bullet.
- **Which docs (please read):** the 50 doc IDs were supplied by the reader and are listed at the end. **They are not the output of `pick_docs.py`.** Running `pick_docs.py` (seed 20261101, Part 1 then Part 2, rows 1-50) gives a different list (first ID `33324b7387762547`) with 0 of 50 IDs in common; a pandas `sample(frac=1, random_state=20261101)` gives a third list (first ID `405f9a63f0336440`), also with 0 in common. All 50 supplied IDs do exist in this pack (36 in Part 1, 14 in Part 2). Where the supplied list came from is not recorded here (open question 1).
- **Read against:** `specv1.md`, `medicine_english.md` and `decisions_english.md` (the English sheets, not the code sheets).
- **Cleaner:** spec v1 `clean.py` (PR #244). The exact commit is not verified from my clone (open question 4).
- **Labelling rule:** `missed` = spec v1 has a rule for that disease and the cleaned text still has it (here C1 and D3). C1 was counted as menus, cookie banners, share buttons and footer links only.
- **Method: manual.** The reader manually read and reviewed every finding against the cleaned text and confirmed all 14. `source` is `manual` for every row.
- **Offsets:** code points in the cleaned text, end exclusive. A whole-doc finding is `0-<length>`. `quote` is a short snippet; no phone numbers, emails or other personal data are quoted.
- **Not logged (already decided in `decisions_english.md`):** an organisation's phone numbers and emails (the 31 Oct F1 ruling leaves them), names and bylines (names are not in the F1 ruling), and `<EMAIL>`, `<PHONE>`, `<ADDRESS>` tags (that is F1's own redaction).

## Findings table

14 findings in 10 of 50 docs. Kinds: missed 14, new 0, harm 0.

| code | kind | docs affected | % of docs read |
|---|---|---|---|
| C1 | missed | 9 | 18% |
| D3 | missed | 2 | 4% |

What the `missed` rows show:

- **C1 (9 docs):** website furniture kept in the text: a cookie banner (`Your consent to our cookies…`), page navigation and footer links (`« Previous / Next »`, a cite-this-page and `More on…` block, `Latest posts by…`, an app promo, related-story links), tab and button text (`Navigate through the tabs…`, `Access this Article`, `Go to this verse :: Verse pop-up`, `Read the full story:`), and the slideplayer header line. C1 was counted as menus, cookie banners, share buttons and footer links only.
- **D3 (2 docs):** a Japanese title and a journal citation line written only in Japanese letters (doc `dbcb78a28f12027d`), and a Russian date glued to an English sentence (doc `fd566045d10b5f73`), left in English documents.

## New diseases

None logged. Only problems that a spec v1 rule is meant to treat are in the findings.

## Harm

None found. No doc showed text that a rule had visibly removed or damaged. This is not proof of zero harm: the reader sees only what is left, and with 50 docs a zero only bounds the harm rate loosely.



## Doc IDs 

`10f60963e48a9ddf 14bc06c6ac5fe815 1d03189599fe659f 395db5a13fa8bd27 1226dfbd3262945f 660f785d72c4f743 fd566045d10b5f73 0a710c3b70f90ea6 27460298db342bcb 2f50ea982f698219 6b3e869b7576ba25 8ab065232be7266c dfea851dab5364e6 db44efda56b304c3 01eb3742a898cd17 38acc2def894aa6b 079e456eccfc6cbf 6f2323af43471531 e3b95766b8aadcc2 d5b548bc0f39f117 f1a2fd4c1859abf0 807ef2ed55b5870c bb9c0b88020d73b6 da51218a0a3b148c 9aecc434a5319f1f a65e044d8a662efe 89dad1346f35100c 5e7ec8f9deba2878 a3c4142a27497797 1cb7689294d65dd3 52bcd2c41abe39c2 dbcb78a28f12027d 42c2c25f5241601e b4c7d5c0c575b555 5226ae351d82a4aa c28901fc82203af6 51b1c9916f997a55 55571715fdbd630d 7aecfc945a0434db f1571683226b09dc 0ff2aa6733f2db17 c16c6ed1ea3b91d7 db076cce5f4c8096 66464920e7393bd9 d7a6fec2f8c5d0ed 86e8b9ce026393b4 81d21bee74c3adbf 41fa080a582c488e 37bfda386fa30d6e 5bf467e083a214fa`
