# Medicine sheet: ind-kn-sangraha-s (millermuttu)

Pack: 500 documents, Kannada, source sangraha-synthetic (Wikipedia pages machine-translated into Kannada).
Labels: 359 clean, 141 fix, 0 drop.

Diseases found more than five times: B2 (43), C3 (30), A6 (30), C1 (24), D3 (16), B3 (7). D4 and G1 (5 each) and
C2, C4, B4, A3 are at or below five, so they get no medicine.

All the code is in this file: the `python` blocks, read from top to bottom, make one script. The blocks are the
imports below, the six medicines, and the harm test at the end. To run the self-check and the harm test:

```
awk '/^ *```python/{f=1;next} /^ *```/{f=0;next} f{sub(/^   /,"");print}' medicine.md > medicine_run.py
python3 medicine_run.py ind-kn-sangraha-s.parquet teams/02-data-b/gold/kannada_gold.csv labels.csv
```

```python
import csv
import re
import sys

import pyarrow.parquet as pq
```

## The harm test, in one table

Gold set: `kannada_gold.csv` from the Data B interim gold sets (PR #149), 86 documents. 11 of them are in this
pack (two clean votes: millermuttu and subramanyanaik). The other 75 are in ind-kn-fw2 and ind-kn-sangraha-v, and I
do not have those packs, so I could test only the 11. With 11 documents, the 1% limit means that a medicine must
not touch any gold document.

As a second, wider check, I also ran each medicine on my own 359 clean rows. That set has one reader only, so it is a
proxy and not gold.

| Medicine | Disease | Gold changed | Gold dropped | Result | My clean rows changed | Labelled docs it fixes | Pack docs it touches |
|---|---|---|---|---|---|---|---|
| M1 | B2 | 0 / 11 | 0 | PASS | 0 / 359 | 43 / 43 | 46 |
| M2 | B3 | 0 / 11 | 0 | PASS | 0 / 359 | 3 / 7 | 3 |
| M3 | A6 | 0 / 11 | 0 | PASS | 0 / 359 | 9 / 30 | 9 |
| M4 | C1 | 0 / 11 | 0 | PASS | 5 / 359 | 7 / 24 | 22 |
| M5 | C3 | 0 / 11 | 0 | PASS | 3 / 359 | 18 / 30 | 26 |
| M6 | D3 | 0 / 11 | 0 | PASS (no text change) | 0 / 359 | n/a | 0 |

I read each of the 8 changes in my clean rows (see the side effects of M4 and M5). Each one removes text that I should
have labelled C1 or C3. They are misses in my label sheet, not harm.

## Medicine 1: translated HTML tags (B2)

1. **Disease:** B2, 43 documents. The translation step turned the tags into Kannada letters.
   - `ff6d56a4f0b67604`: `<ಐ. ಡಿ. 1>` at offset 626 (this was `<ID 1>`)
   - `3a69a945a1b7aeaa`: `<ಬಿ. ಆರ್.>` at offset 573 (this was `<br>`)
   - `5f6f044745aeb4f4`: `<>` and `</Â>` at offset 219 and 222 (7 times each)
   - Also without brackets: `2d9a373d2ef00c46`: `ಐ. ಡಿ. 1` at offset 5796.
2. **Medicine:** replace a translated or real `<br>` with a newline. Delete `<ID n>` in its Kannada form, with or
   without brackets, and the space before it. Delete any other tag that starts with a Latin letter, the translated
   `<ರಿಫರ್ ...>` reference tag, and `<>`.
   ```python
   TAG_ID = re.compile(r" ?<?ಐ\. ಡಿ\. \d+>?")
   TAG_BR = re.compile(r"<ಬಿ\.? ?ಆರ್\.?>|<br\s*/?>", re.I)
   TAG_ANY = re.compile(r"</?(?:[A-Za-zÀ-ÿ][^<>\n]{0,40}|ರಿಫರ್[^<>\n]{0,80})>|<>")
   def m1_tags(s):
       s = TAG_BR.sub("\n", s)
       return TAG_ANY.sub("", TAG_ID.sub("", s))
   ```
3. **Action:** fix the text.
4. **Harm test:** gold 0 changed, 0 dropped of 11. PASS. My clean rows: 0 of 359.
5. **Side effects:** `<ಐ. ಡಿ. 1>` stood for a name or a number that the source hid. Deleting it can leave a sentence
   with a gap ("... was born in ."). The medicine also deletes `<unk>` (that is M2's job too, so no harm). A real
   Kannada text that writes `ಐ. ಡಿ. 2` for "ID 2" (an ID card number) would lose it; I saw no such case.

## Medicine 2: ghost tokens (B3)

1. **Disease:** B3, 7 documents labelled. Only 3 have a real ghost token, `<unk>`:
   - `a84cbd8f664d1816`: `<unk>` 11 times, first at offset 753
   - `76ff156acd160ee4`: `<unk>` at offset 217 and 1074
   - `d5133441c9d74b4f`: `<unk>` at offset 37 and 58

   The other 4 rows (`f1161ea20322b1f3` `<`, `2b65959fd113626f` `?`, `652430783641cf74` `? =`, `145f7cfbe62c98c6` `!`)
   are stray punctuation, not chat markers. They are under the limit of five, so they get no medicine here.
2. **Medicine:** delete the unknown token and the usual chat-template markers.
   ```python
   GHOST = re.compile(r"<unk>|<\|[a-z_]+\|>|\[/?INST\]|</?s>|</?think>")
   def m2_ghost(s):
       return GHOST.sub("", s)
   ```
3. **Action:** fix the text. `<unk>` replaced a character that the tokenizer of the translation model did not know,
   so the word around it stays damaged.
4. **Harm test:** gold 0 changed, 0 dropped of 11. PASS. My clean rows: 0 of 359.
5. **Side effects:** a text about HTML or about language models that quotes `<s>` or `<|endoftext|>` loses the quote.

## Medicine 3: "i.e." and "e.g." half translated (A6)

1. **Disease:** A6, 30 documents. Latin letters glued to Kannada letters in one word. There are three kinds:
   - half-translated abbreviations: `54f770edbfb0f27e`: `(i.ಇ.ಪಳೆಯುಳಿಕೆ)` at offset 490; `7213ef84e617ab3c`:
     `(e.ಜಿ.` at offset 876; `4fde496efbb5da8b`: `(i.ಇ.,` at offset 316
   - Roman numerals or acronyms with a Kannada case ending: `0e72261397f357cd`: `xiiಗೆ` at offset 115;
     `572e66f3cdcbcedf`: `GMTಯಲ್ಲಿ` at offset 501
   - Latin technical names with a Kannada word: `bddb7db5986a353f`: `dbus-ಜಾವಾ` at offset 708
2. **Medicine:** only the first kind is damage. Replace the half-translated `i.e.` with `ಅಂದರೆ` and `e.g.` with `ಉದಾ.`.
   The second and third kinds are how Kannada writers add a case ending to a foreign name. Leave them.
   ```python
   HALF_IE = re.compile(r"\bi\.\s?ಇ\.")
   HALF_EG = re.compile(r"\be\.\s?ಜಿ\.")
   def m3_half_translated(s):
       return HALF_EG.sub("ಉದಾ.", HALF_IE.sub("ಅಂದರೆ", s))
   ```
3. **Action:** fix the text.
4. **Harm test:** gold 0 changed, 0 dropped of 11. PASS. My clean rows: 0 of 359. It fixes 9 of the 30 A6 documents.
5. **Side effects:** a list item `i.` followed by a sentence that begins with `ಇ.` would change; I saw none. Other
   half-translated initials (`f.ಸಿ.` for "F.C." in `b497ade9ed6f64c3`) are not fixed, because the right Kannada form
   depends on the name.

## Medicine 4: reference footer and advertisement lines (C1)

1. **Disease:** C1, 24 documents.
   - `248d753341105364`: `ಉಲ್ಲೇಖಗಳು.\nಉಲ್ಲೇಖಗಳು\nಮೂಲಗಳು` (References, References, Sources) at offset 565
   - `2237fbd5cc07cfb8`: `ಉಲ್ಲೇಖಗಳು.\nಉಲ್ಲೇಖಗಳು\nಗ್ರಂಥಸೂಚಿ` (References, Bibliography) at offset 6479
   - `795cf2909be9d1f6`: `ಜಾಹೀರಾತು` (Advertisement) as its own line at offset 4668, 4708, 4749
2. **Medicine:** find the first line that is only a footer heading: References, Sources, Notes, Bibliography,
   External links, See also. If it is in the second half of the document, cut the document there. Delete every line
   that is only `ಜಾಹೀರಾತು`.
   ```python
   FOOTER = re.compile(r"^(?:ಉಲ್ಲೇಖಗಳು|ಮೂಲಗಳು|ಟಿಪ್ಪಣಿಗಳು|ಗ್ರಂಥಸೂಚಿ|ಬಾಹ್ಯ ಸಂಪರ್ಕಗಳು|ಇದನ್ನೂ ನೋಡಿ)\.?[ \t]*$", re.M)
   AD_LINE = re.compile(r"^[ \t]*ಜಾಹೀರಾತು[ \t]*\n?", re.M)
   def m4_footer(s):
       m = FOOTER.search(s)
       if m and m.start() > len(s) // 2:
           s = s[: m.start()].rstrip()
       return AD_LINE.sub("", s)
   ```
3. **Action:** fix the text.
4. **Harm test:** gold 0 changed, 0 dropped of 11. PASS. My clean rows: 5 of 359 changed. I read all 5. Two
   (`7316a3d779366b1a`, `8772f7c961f3c48f`) end in an empty `ಉಲ್ಲೇಖಗಳು.` heading, `ed7cfe412cf5a9bb` ends in
   "translated from the German Wikipedia", `7696c91439e39dd0` and `ea7e1afd07060b11` end in a link or reference list.
   All 5 are footers that I missed when labelling.
5. **Side effects:** it fixes only 7 of the 24 C1 documents. The other 17 end in lists with a content heading
   (Honours `ಗೌರವಗಳು.`, track lists, cast lists). Those lists are content of the page, so the medicine keeps them. A
   footer in the first half of a short document stays; a "Notes" section that holds real text is cut.

## Medicine 5: dangling list intro at the end (C3)

1. **Disease:** C3, 30 documents. Most truncated documents end with a sentence that announces a list, and the list is
   missing. The translation wrote the colon as the visarga `ಃ`.
   - `1428f9e8314543c8`: `ಪುಸ್ತಕಗಳು ಮತ್ತು ಪ್ರಬಂಧಗಳು ಹೀಗಿವೆಃ` ("his books and essays are as follows:") at offset 560
   - `ee2758858961a338`: `ಜನರು ಅದರ ಮೇಯರ್ ಆಗಿದ್ದರುಃ` at offset 9312
   - `378c502cc7ad043b`: `ಈ ಕೆಳಗಿನವುಗಳನ್ನು ಒಳಗೊಂಡಿವೆಃ` at offset 406
2. **Medicine:** if the document ends with `ಃ` or `:`, cut its last sentence (back to the last newline or the last
   `. `). If nothing is left, drop the document.
   ```python
   def m5_dangling_intro(s):
       body = s.rstrip()
       if not body.endswith(("ಃ", ":")):
           return s
       cut = max(body.rfind("\n"), body.rfind(". ") + 1)
       return body[:cut].rstrip() + "\n" if cut > 0 else None
   ```
3. **Action:** fix the text (drop only a document that is one dangling sentence).
4. **Harm test:** gold 0 changed, 0 dropped of 11. PASS. My clean rows: 3 of 359 changed (`523fee1068dc3fa9`,
   `5182f57e468c0d70`, `db80897e2760a8ad`). All 3 end with a list intro and no list: C3 that I missed.
5. **Side effects:** it fixes 18 of the 30 C3 documents. The other 12 stop in the middle of a word or a list item
   (`2ffa1db3ff911b53`, `6a8a83b833862e25`); no safe rule finds the end of the text there. The visarga `ಃ` is also a
   real Kannada letter (`ದುಃಖ`, `ಅಂತಃ`). A document that really ends with such a word would lose its last sentence. In
   this pack no document does.

## Medicine 6: mixed language (D3)

1. **Disease:** D3, 16 documents. Foreign words inside Kannada text.
   - `cff540231e8e8ed1`: Russian `орлиное гнеzdо` at offset 51
   - `309c6300b2a22783`: Greek `αλεσιρεσι αρεσιρεσι` at offset 4207
   - `a0ee8f67d70aa82b`: Japanese romanisation `ōzeki` at offset 975
2. **Medicine:** no text change. DISEASES.md says: label mixed language, do not judge it. The foreign words are names
   and titles that the page quotes. The function measures the share of letters that are neither Kannada nor Latin,
   so the mixture team can see it.
   ```python
   LETTER = re.compile(r"[^\W\d_]", re.U)
   NOT_KN_LATIN = re.compile(r"[^\W\d_a-zA-Zಀ-೿]", re.U)
   def m6_foreign_ratio(s):
       n = len(LETTER.findall(s))
       return len(NOT_KN_LATIN.findall(s)) / n if n else 0.0
   ```
   In the 16 D3 documents the share is at most 0.054 (5.4%). No document is mostly foreign.
3. **Action:** keep the text. Record the ratio.
4. **Harm test:** gold 0 changed, 0 dropped. PASS by construction.
5. **Side effects:** none on the text. The ratio does not see Latin words (English, German) because Latin is normal in
   this pack (names, units, acronyms).

## The harm test code

`main` runs every medicine on the gold documents that are in the pack, and on my own clean rows. It also counts how
many of the labelled documents each medicine touches. `selftest` is the smallest check that each rule still works.

```python
MEDICINES = [("M1", "B2", m1_tags), ("M2", "B3", m2_ghost), ("M3", "A6", m3_half_translated),
             ("M4", "C1", m4_footer), ("M5", "C3", m5_dangling_intro)]


def effect(fn, text):
    out = fn(text)
    return "drop" if out is None else ("change" if out != text else "same")


def main(pack, gold_csv, labels_csv):
    docs = {r["doc_id"]: r["text"] for r in pq.read_table(pack, columns=["doc_id", "text"]).to_pylist()}
    gold = [r["doc_id"] for r in csv.DictReader(open(gold_csv, encoding="utf-8"))]
    gold = [g for g in gold if g in docs]
    labels = list(csv.DictReader(open(labels_csv, encoding="utf-8")))
    clean = [r["doc_id"] for r in labels if r["verdict"] == "clean"]
    print(f"pack {len(docs)} docs, gold in pack {len(gold)}, my clean rows {len(clean)}")
    print("med disease | gold changed dropped | my-clean changed dropped | labelled docs touched | pack touched")
    for name, code, fn in MEDICINES:
        g = [effect(fn, docs[i]) for i in gold]
        c = [effect(fn, docs[i]) for i in clean]
        sick = [r["doc_id"] for r in labels if code in r["diseases"].split(";")]
        hit = sum(effect(fn, docs[i]) != "same" for i in sick)
        allp = sum(effect(fn, t) != "same" for t in docs.values())
        verdict = "PASS" if (g.count("change") + g.count("drop")) <= 0.01 * len(gold) else "FAIL"
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
    assert m5_dangling_intro("ಅವು ಹೀಗಿವೆಃ") is None
    assert m5_dangling_intro("ಒಂದು.") == "ಒಂದು."


if __name__ == "__main__":
    selftest()
    if len(sys.argv) < 4:
        sys.exit("usage: python3 medicine_run.py PACK.parquet GOLD.csv labels.csv")
    main(*sys.argv[1:4])
```
