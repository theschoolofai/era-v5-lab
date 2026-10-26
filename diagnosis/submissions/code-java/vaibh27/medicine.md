# Medicine sheet: code-java (vaibh27)

**Draft for the 27 Oct check-in.** The harm tests wait for the gold set and `harm_test.py` (Data A / Data B, due
Thu 29 Oct). The final version with all 500 rows comes on Sat 31 Oct.

Pack: `code-java`, 500 documents from `bigcode/starcoderdata:java`. Labelled so far: documents 1 to 150 (`labels.csv`).
Counts are given two ways: in my 150 labelled rows, and the number of documents that the medicine changes in the
whole pack of 500.

Run the medicines in this order: **M1, M3, M2, M4**. M4 expects the metadata line (M1) and the CR characters (M3)
to be gone already.

## Harm test status

The gold set for code-java is not in the repository yet, so **no gold harm test has been run**. As a stand-in, I ran
each medicine on the 39 documents that I marked `clean` in my labels. **All four medicines change 0 of 39.** I will
replace this with the real gold-set numbers when Data A / Data B publish the gold set.

One risk for the gold test: M1, M3 and M4 each fire on 9% to 50% of the raw pack. If the gold readers count
CRLF line endings or licence headers as clean, these medicines will fail the 1% rule even though they do not harm
the code. The gold-set owners need to decide whether A2 (CRLF) and E4 count as diseases in code.

C1 (IDE template comments) is also found more than five times (27 of 150 labelled). Its medicine comes with the
final version on 31 Oct.

---

## Medicine 1: StarCoder metadata header (B3)

1. **Disease:** B3, ghost dataset tokens `<reponame>`, `<filename>`, `<gh_stars>` on the first line.
   Count: 73 of 150 labelled; **250 of 500** in the pack. These tokens never appear after the first line in this pack.
   - `d0947d80d45f7ce3`: `<filename>src/test/java/problems/RangeSumOfBSTTest.java` at offset 0
   - `7590b32d671f36c9`: `<reponame>88t6/vwkit-matrix<gh_stars>1-10` at offset 0
   - `073b348caf645018`: `<reponame>DezByte/multiverse<filename>multiverse-core/...RetryError.java<gh_stars>0` at offset 0
2. **Medicine:** if the document starts with one or more of these tokens, delete that whole first line. Touch nothing
   after it.
   ```python
   import re
   META_HEAD = re.compile(r"\A(?:<reponame>[^<\n]*|<filename>[^<\n]*|<gh_stars>[^<\n]*)+\n")

   def m1_strip_meta_header(t: str) -> str:
       return META_HEAD.sub("", t, count=1)
   ```
3. **Action:** fix.
4. **Harm test:** gold set pending. Stand-in: changes 0 of my 10 `clean` documents, drops 0.
5. **Side effects:** the repo name and file path are lost. If we want them as metadata, copy them into a separate
   column before stripping. The rule is anchored at offset 0, so a `<filename>` string inside real code cannot match.
   After stripping, every one of the 250 documents starts with `package`, `import`, `public` or a comment. One
   document (`beae2c42d8a34ccc`) then starts with a BOM (A1), which needs its own fix.

## Medicine 2: PII redaction placeholders (B4)

1. **Disease:** B4 (ruling of 25 Oct: placeholders from earlier PII cleaning are B4, note `PII placeholder`; they
   are not personal data), the upstream PII-redaction placeholders `<NAME>`, `<EMAIL>`, `<PASSWORD>` and `<KEY>` left as
   plain text. A model trained on them learns to write these tokens. Count: 24 of 150 labelled; **82 of 500** in the
   pack (118 `<NAME>`, 54 `<EMAIL>`, 21 `<PASSWORD>`, 1 `<KEY>`).
   - `13a397d8bedc6210`: `@author <NAME> <<EMAIL>>`, `<NAME>` at offset 159
   - `8c9a9aa845f91a2c`: `String passWord = "<PASSWORD>";`, `<PASSWORD>` at offset 321
   - `4fce1af748c757ed`: `<NAME> (<EMAIL>)` 11 times (copyright line and `@author` tags), first `<NAME>` at offset 109
2. **Medicine:** replace each placeholder with a fixed, neutral surrogate. Do not delete it: in string literals,
   deleting it would leave `""` or broken code. Replace `<KEY>` only inside quotes, because a bare `<KEY>` is a legal
   Java generic type parameter (`class Cache<KEY>`).
   ```python
   SURROGATE = {"<EMAIL>": "user@example.com", "<NAME>": "Author Name",
                "<PASSWORD>": "password", '"<KEY>"': '"key"'}
   REDACT = re.compile("|".join(map(re.escape, SURROGATE)))

   def m2_surrogate_placeholders(t: str) -> str:
       return REDACT.sub(lambda m: SURROGATE[m.group()], t)
   ```
3. **Action:** fix.
4. **Harm test:** gold set pending. Stand-in: changes 0 of my 10 `clean` documents, drops 0.
5. **Side effects:**
   - A real XML/HTML tag `<NAME>` inside a string would be changed. There are no `</NAME>`, `</EMAIL>` or
     `</PASSWORD>` closing tags in the pack, so I found no such case.
   - Every author becomes the same "Author Name". This is a small bias, but it is better than the special token.
   - The redaction was not complete. `1a1a1d7ab0bf9188` still has a real phone number (F1, offsets 40 and 1499) and a
     garbled `<EMAIL>H<EMAIL>`. M2 does not find unredacted PII. F1 needs its own rule.

## Medicine 3: CRLF line endings (A2)

1. **Disease:** A2, control character U+000D (CR) as Windows line endings (`0D 0A`). Count: 21 of 150 labelled;
   **44 of 500** in the pack. No lone CR and no other control characters in the pack.
   - `e0ebe203093970dc`: U+000D x38, first at offset 17
   - `7fc99d2b6e1e3d08`: U+000D x330, first at offset 2
   - `b584f0fe9264ce70`: U+000D x24, first at offset 47
2. **Medicine:** turn every CRLF into LF, then any lone CR into LF.
   ```python
   def m3_normalise_newlines(t: str) -> str:
       return t.replace("\r\n", "\n").replace("\r", "\n")
   ```
3. **Action:** fix.
4. **Harm test:** gold set pending. Stand-in: changes 0 of my 10 `clean` documents, drops 0.
5. **Side effects:** Java treats CR and LF the same, so the program does not change. The escaped text `"\r\n"`
   inside a string is two ASCII characters, not U+000D, so it is not touched. A raw CR inside a Java text block
   (`"""`) would change the string value. I found none in the pack.

## Medicine 4: Licence headers (E4)

1. **Disease:** E4, the same licence text at the top of many files (Apache-2.0 ASF, Apache-2.0 short form, MIT,
   BSD). Count: 24 of 150 labelled; **87 of 500** in the pack.
   - `5655154f71365c63`: 18-line ASF Apache-2.0 header, offsets 0 to 825
   - `4fce1af748c757ed`: 23-line MIT header, offsets 0 to 1205
   - `86534a30f79557fb`: 13-line Apache-2.0 short-form header, offsets 0 to 562; the same text is in 35 other documents
2. **Medicine:** if the document starts with a block comment that contains "license"/"licence" or "Permission is
   hereby granted", and the next code is `package` or `import`, delete that comment.
   ```python
   LIC_HEAD = re.compile(r"\A(\s*)/\*.*?\*/[ \t]*\n", re.S)
   LIC_WORDS = re.compile(r"licen[cs]e|permission is hereby granted", re.I)

   def m4_strip_licence_header(t: str) -> str:
       m = LIC_HEAD.match(t)
       if not m or not LIC_WORDS.search(m.group()):
           return t
       if not re.match(r"\s*(package|import)\b", t[m.end():]):
           return t  # may be a class Javadoc, not a file header
       return t[m.end():].lstrip("\n")
   ```
3. **Action:** fix.
4. **Harm test:** gold set pending. Stand-in: changes 0 of my 10 `clean` documents, drops 0. On my 50 labelled rows
   On my 150 labelled rows it does not match my E4 labels yet (to fix by 31 Oct):
   - it fires on 2 NetBeans "To change this license header" templates (`50e06974390e57ea`, `6e3090899a74fa03`).
     They say "license" but hold no licence; I label them C1. M4 needs a guard for this template.
   - it misses 5 E4 headers: 4 written as `//` line comments (`2b64b0726c469c39`, `d1e50dcbfa47a388`,
     `f8d11746cccf1c17`, `73e175e90e6e37da`) and a BSD header without the word "license" (`fea61dd1f1c92f61`).
5. **Side effects:**
   - Short copyright-only headers without the word "license" (for example `7fc99d2b6e1e3d08`,
     "Copyright (c) 2010, tamacat.org. All rights reserved.") are kept. I did not label them E4 either.
   - A file in the default package (no `package` line) keeps its header. This is a miss, not harm.
   - The licence notice is removed from the training text. If the release team needs licence information, keep the
     header in a metadata column. Another option is to keep it once per repository instead of once per file. I need
     a decision from the lead on this.
   - A header that also holds real documentation (a file description inside the licence block) loses it.
