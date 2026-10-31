# Medicine sheet: ind-ta-sangraha-s (truesrini)

Pack: 500 documents, all read in full (84 clean, 414 fix, 2 drop). The pack is English Wikipedia machine-translated
into Tamil, so most diseases come from the translation step.

Every medicine below is a Python function `medicine_<code>(text)`. It returns the new text (fix), the same text
(no change), or `True` (drop the document). This is the format of the lab's harm test,
`teams/02-data-b/tools/harm_test_indic.py` (PR #144, fixed in PR #148), so this file can be given to it directly.
The sections are in the order the medicines should run: A6 runs before G3, so the brackets that A6 empties are
then removed by G3.

**Harm test rules (PR #143 and PR #148 reviews).** A medicine passes when it changes or drops at most
max(1 document, 1%) of the Tamil gold set, it does not change the count of ZWJ/ZWNJ, and it keeps NFC and the
compatibility characters. The Tamil gold set is `teams/02-data-b/gold/tamil_gold.csv` (PR #149): **41 documents,
all from the pack `ind-ta-sangraha-v`**. My pack `ind-ta-sangraha-s` has no gold yet (one reader).

**Gold-set run: pending.** The test needs `ind-ta-sangraha-v.parquet` (the text of the 41 gold documents). The repo
has only their ids. When the file is here, run:

```
python teams/02-data-b/tools/harm_test_indic.py --medicine medicine_ind-ta-sangraha-s.md --pack ind-ta-sangraha-v.parquet --gold-dir teams/02-data-b/gold --show 10 --md-out harm_gold.md
```

**Stand-in run, done.** Until then, each harm test below also gives the result of the same tool on my own 84
`clean` documents (limit: max(1, 0.84) = 1 document). Every medicine changed 0 and dropped 0 of them.

A first stand-in run on 94 `clean` documents made G4 change 7, G3 change 2 and D4 change 2. I checked all ten
documents: each one really has that disease, and I had missed it when I labelled it `clean`. I relabelled those
ten documents (`fix`, with the code and the evidence; note "relabelled 31 Oct"), so the counts below include them.
The ten are named in the G3, G4 and D4 sections.

---

## Medicine 1

1. **Disease:** B2, HTML or XML tags. Count in my pack: 8.
   - `f1547c851d1156dd`: `<பிஆர்>` at 444 (`<br>` with its name translated)
   - `15a98014d11ac3eb`: `<கவிதை>` at 3986 (`<poem>` translated)
   - `473c4cce1e69e6f7`: `<பிரிவு தொடக்கம் = "2019 விஎன்எல் முதற்கட்டங்கள்"/>` at 2984 (`<section begin=.../>`)
2. **Medicine:** remove HTML and wiki tags, both the English ones (`<br>`, `<poem>`, `<ref>`, `<section>` ...) and
   the ones whose name the translator turned into Tamil (a `<` followed by Tamil letters, an optional `= value`,
   then `>`). A line-break tag (`<br>`, `<பிஆர்>`) becomes a newline; every other tag is removed.

   ```python
   import re

   _TA = "஀-௿"  # Tamil block
   _HTML = "br|p|div|span|poem|ref|references|section|small|big|center|sup|sub|nowiki|gallery|table|tr|td|th"
   _TAG = re.compile(rf"</?(?:(?:{_HTML})\b[^<>\n]{{0,120}}|[{_TA}][{_TA} ]{{0,30}}(?:\s*=[^<>\n]{{0,120}})?)/?>", re.I)
   _BREAK = re.compile(r"</?(?:br|பிஆர்)\b", re.I)


   def medicine_b2(text):
       """Remove HTML/wiki tags, also the ones whose names were translated into Tamil (<br> -> <பிஆர்>).
       A line-break tag becomes a newline; every other tag is removed."""
       return _TAG.sub(lambda m: "\n" if _BREAK.match(m.group(0)) else "", text)
   ```
3. **Action:** fix.
4. **Harm test:**
   - Gold set (41, `ind-ta-sangraha-v`): pending, see the top of this sheet.
   - Stand-in (my 84 clean): changed 0, dropped 0 (0.00%). ZWJ/ZWNJ ok, normal form ok. PASS.
   - My pack: treats all 8 B2 documents, and no document outside the label.
5. **Side effects:**
   - Text that writes about a tag as an example (`the <br> tag`) loses it. Not seen in this pack.
   - A Tamil phrase between `<` and `>` that is not a tag, for example a quote in angle brackets `<தமிழ்>`, is removed.
   - It does not bring back the content of `<poem>` or `<section>` blocks; it only removes the tags.

## Medicine 2

1. **Disease:** B4, template and code junk in prose. Count in my pack: 15.
   - `492dee62b8fa8976`: `ஐடி1` at 275 (an `ID1` number placeholder that the translator never filled back)
   - `83e3c9a41eecda14`: `ஐ. டி. 1` at 14924 (the same, spelled out, 3 times)
   - `5345840c80c5cb79`: `சூத்திரம் _ 1` at 146 ("formula _ 1", the placeholder of a removed formula)
2. **Medicine:** find a translator placeholder (`ஐடி1`, `ஐ. டி. 1`, `சூத்திரம் _ 1`), a URL whose host was
   translated (`HTTP:// பணிக்குழுக்கள்`), or `.html` translated letter by letter (`எச். டி. எம். எல்`). The number
   that belonged there is lost, so remove the whole sentence. If less than 150 characters are left, drop the document.

   ```python
   import re

   _PLACEHOLDER = re.compile(
       r"ஐ\. ?டி\.? ?\d>?"            # ஐ. டி. 1  (the "ID1" number placeholder, spelled out)
       r"|ஐடி\d"                      # ஐடி1
       r"|சூத்திரம் _ \d"              # சூத்திரம் _ 1  ("formula _ 1")
       r"|(?i:https?:// ?[஀-௿])"  # a URL whose host was translated
       r"|எச்\. ?டி\. ?எம்\. ?எல்"      # ".html" translated letter by letter
   )
   _SENTENCE = re.compile(r"[^.!?\n]*(?:[.!?]+|\n|$)")


   def medicine_b4(text):
       """Remove each sentence that holds a translator placeholder. Drop the document if less than 150 characters are left."""
       if not _PLACEHOLDER.search(text):
           return text
       kept = "".join(s for s in _SENTENCE.findall(text) if not _PLACEHOLDER.search(s))
       return kept if len(kept.strip()) >= 150 else True
   ```
3. **Action:** fix (drop when almost nothing is left).
4. **Harm test:**
   - Gold set (41): pending.
   - Stand-in (84 clean): changed 0, dropped 0 (0.00%). PASS.
   - My pack: treats 8 of the 15 B4 documents. It also fixes 2 documents I did not label B4, and both are real
     B4: `7010848fa88c9a00` (`சராசரியாக ஐடி1`) and `f468b1056b3f6c8d` (`சூத்திரம் _ 2`).
5. **Side effects:**
   - The whole sentence goes, so the facts in it that were correct are lost too.
   - A real use of `ஐடி` followed by a digit (an ID number written in Tamil, such as `ஐடி2 வகை`) would be removed.
   - It does not treat the other 7: wiki table code with translated names (`!கொல்ன் = 6 பாணி=/`) and translated file
     names (`வரைபடம்.கிடாமிமாக்கி-வில்.பி. என். ஜி.`, a `.png`) have too many forms for one safe rule.

## Medicine 3

1. **Disease:** A6, wrong or mixed script. Count in my pack: 27.
   - `ae1582f27fc4aeb8`: `க ored ரவிக்கப்பட்டார்` at 335 (கௌரவ, "honoured", split by the English piece `ored`)
   - `f1547c851d1156dd`: `Кучороо` at 25 (a Polish place name left in Cyrillic)
   - `6e563273545b8ca2`: `τατίανα αλMachova` at 63 (a Russian name in Greek and Latin letters)
2. **Medicine:** two parts. (a) Join the split word: `க o.. ரவ` becomes `கௌரவ`. (b) In a Tamil document, remove
   every word that has a Cyrillic letter, and every Greek word of 4 or more letters. These are names the translator
   left in a wrong script; the Tamil spelling is already next to them. Short Greek words (`α`, `β`, `δf`) are kept,
   because science text uses them.

   ```python
   import re

   _GAURAVA = re.compile(r"க o[a-z]{0,4} ரவ")  # கௌரவ split by an English piece: "க ored ரவி", "க or ரவ"
   _CYR = "Ѐ-ӿ"
   _GRK = "Ͱ-Ͽ"
   _FOREIGN = re.compile(
       rf"[A-Za-z{_CYR}{_GRK}]*[{_CYR}][A-Za-z{_CYR}{_GRK}]*"   # any word with a Cyrillic letter
       rf"|[A-Za-z{_GRK}]*[{_GRK}]{{4}}[A-Za-z{_GRK}]*"        # a Greek word of 4+ letters (keeps α, β, δf in formulas)
   )
   _TAMIL = re.compile(r"[஀-௿]")


   def medicine_a6(text):
       """Join the split word கௌரவ, and remove Cyrillic/Greek words from Tamil text
       (names the translator left in a wrong script, such as "Кучороо")."""
       text = _GAURAVA.sub("கௌரவ", text)
       if not _TAMIL.search(text):
           return text
       return re.sub(r"[ \t]{2,}", " ", _FOREIGN.sub("", text)) if _FOREIGN.search(text) else text
   ```
3. **Action:** fix.
4. **Harm test:**
   - Gold set (41): pending.
   - Stand-in (84 clean): changed 0, dropped 0 (0.00%). PASS.
   - My pack: treats 13 of the 27 A6 documents. It also fixes 2 that I did not label A6, and both are real:
     `b8eb9fe479192048` (`க ored ரவிக்கப்பட்டார்`) and `365f522e35ecd5c3` (`сеvket pamuk`, Cyrillic `с` and `е`).
5. **Side effects:**
   - A real Russian, Bulgarian or Greek quote in a Tamil article is removed. This pack has none; the gold set may.
   - When the name in Cyrillic was the only copy of the name (no Tamil spelling next to it), the name is lost.
   - A name in brackets leaves `()` behind. Medicine 4 (G3) runs next and removes it.
   - It does not treat the other 14: lowercased Latin (`exxv-TV`, `xk`) and Latin look-alike letters in a Latin
     word (`e.ஜி.`). Those need the English source.

## Medicine 4

1. **Disease:** G3, Indic dropped by an English rule. Count in my pack: 85.
   - `f16db9e6a9ceca9a`: `(, apsg)` at 65 (U+0028 + U+002C + U+0020: the native-script name after `(` is gone)
   - `365f522e35ecd5c3`: `()` at 94, twice (U+0028 + U+0029)
   - `d32d647301bdffd9`: `(;` at 40 (U+0028 + U+003B + U+0020)
2. **Medicine:** remove the empty brackets `()` with the space before them, and turn `(, ` or `(; ` into `(`.
   It does not act after a Latin letter, a digit or `_`, so code such as `main()` is safe.

   ```python
   import re

   _EMPTY = re.compile(r"(?<![A-Za-z0-9_])[ \t]*\([ \t]*\)")  # "பாலியடாங்கி () என்பது"; not after code such as main()
   _LEAD = re.compile(r"\([ \t]*[,;][ \t]*")                   # "(, 7 அக்டோபர்" and "(; "


   def medicine_g3(text):
       """Remove the empty brackets left when an English rule deleted a native-script name."""
       return _LEAD.sub("(", _EMPTY.sub("", text))
   ```
3. **Action:** fix.
4. **Harm test:**
   - Gold set (41): pending.
   - Stand-in (84 clean): changed 0, dropped 0 (0.00%). PASS. (On the first run it changed 2 documents I had
     labelled clean; both were real G3 and I relabelled them: `fbb2a14c319bec7e` `பாலியடாங்கி () என்பது`,
     `445abf59598bed4b` `மின்னெர்ட்ஸ்கா () என்பது`.)
   - My pack: treats 33 of the 85 G3 documents, and no document outside the label.
5. **Side effects:**
   - It cannot bring back the lost name; it only removes the hole.
   - A real `()` in prose (rare in Tamil Wikipedia) is removed.
   - It does not treat the other 52 G3 documents: missing sentences and sections ("content missing here") leave no
     mark that a rule can find. Those can only be fixed at the source, before the English filter.

## Medicine 5

1. **Disease:** G4, over-normalised. Count in my pack: 202.
   - `fd8bbd654c9a6da6`: `("ஆங்கிலம்ஃ உங்கள்` at 254 (U+0B83 TAMIL SIGN VISARGA, expected U+003A COLON)
   - `2807a96dde8c7ab5`: `"கிழக்கில் ஈடன்ஃ தென்கிழக்க` at 2253 (U+0B83, 5x)
   - `48c9c5090a86f641`: `பாணியில்ஃ துப்பறியும` at 1687 (U+0B83, 3x)
2. **Medicine:** in Tamil, aytham `ஃ` (U+0B83) always comes before a consonant (அஃது, எஃகு, and ஃப for "f").
   An aytham that is not followed by a Tamil consonant (U+0B95 to U+0BB9) was a colon before translation: put the
   colon back.

   ```python
   import re

   _AYTHAM_COLON = re.compile(r"ஃ(?![க-ஹ])")  # aytham not followed by a Tamil consonant


   def medicine_g4(text):
       """In Tamil, aytham (U+0B83) always comes before a consonant (அஃது, எஃகு, ஃப).
       Any other aytham was a colon before translation: put the colon back."""
       return _AYTHAM_COLON.sub(":", text)
   ```
3. **Action:** fix.
4. **Harm test:**
   - Gold set (41): pending.
   - Stand-in (84 clean): changed 0, dropped 0 (0.00%). PASS. (On the first run it changed 7 documents I had
     labelled clean; all 7 were this disease and I relabelled them: `(பிறப்புஃ` ("born:") in `03979be7415f6413`, `1323a4bb90f6d3d0`, `bcb80fddfc901bbd`,
     `be6c1a181533212a`, `fda48968696e39ef`; `(பிரெஞ்சுஃ` in `2852bade1f0fa60f`; `பிரிக்கப்பட்டுள்ளதுஃ` in
     `fbb2a14c319bec7e`.)
   - My pack: treats 188 of the 202 G4 documents, and 5 more that I did not label G4 (all `ஃ` used as a colon).
5. **Side effects:**
   - Old Tamil or poetry that ends a word on a bare `ஃ` (`அஃ`) gets a colon. Not seen in this pack.
   - `ஃ` before a Grantha or a vowel (`ஃஜ` is a consonant and is kept; `ஃஅ` is not) would become `:`.
   - It does not treat the other 14 G4 documents: lowercased Latin (`g` for `G`, `xiii` for `XIII`) and lost
     diacritics. Those need the source.

## Medicine 6

1. **Disease:** C2, repeated lines. Count in my pack: 6.
   - `c44e76d913272ece`: `தீர்க்க தீர்க்க தீர்க்க` at 3009 (one word 10 times)
   - `7ce341f95a5cdd35`: the line `இதில் அனைத்து போட்டி போட்டிகளும் அடங்கும்.` 4 times from 1063
   - `b9b2fb55f08f85eb`: the line `≤ பொதுத் தேர்தலுக்கான நியமனத்தில் வெற்றி பெற்றார்` 3 times from 3901
2. **Medicine:** keep the first copy of each line longer than 20 characters and remove the later copies; cut a run
   of 6 or more dots to `...`; cut a word repeated 3 or more times in a row to one copy.

   ```python
   import re

   _DOTS = re.compile(r"\.{6,}")
   _WORD_RUN = re.compile(r"(?<!\S)(\S{2,})(?:[ \t,]+\1){2,}(?!\S)")  # the same word 3 or more times in a row


   def medicine_c2(text):
       """Keep the first copy of each repeated line (longer than 20 characters), cut runs of dots to "...",
       and cut a word repeated 3+ times in a row to one copy."""
       seen, out = set(), []
       for line in text.split("\n"):
           key = line.strip()
           if len(key) > 20 and key in seen:
               continue
           seen.add(key)
           out.append(line)
       return _WORD_RUN.sub(r"\1", _DOTS.sub("...", "\n".join(out)))
   ```
3. **Action:** fix.
4. **Harm test:**
   - Gold set (41): pending.
   - Stand-in (84 clean): changed 0, dropped 0 (0.00%). PASS.
   - My pack: treats 4 of the 6 C2 documents, and 5 that I did not label C2 (for example `ஸ்லோசியோ,` 28 times in
     `3fa68b2c0ef958ff`, and a run of 200 dots in `e6e68c8fb70aa7a1`).
5. **Side effects:**
   - A song title or chant with a word 3 times (`யா யா யா` in `eb5ffd447eccfdf2`) is cut to one word. This one is wrong.
   - A table where two rows have the same long text loses the second row.
   - It does not treat a repeated phrase inside one line (`1916இல் அவர் 1916இல்` in `46c008a27d9c349b`).

## Medicine 7

1. **Disease:** C3, truncated document. Count in my pack: 47.
   - `d46cd7e81d574633`: ends at 660 with the heading `வெளி இணைப்புகள்.` ("External links.") and no links
   - `01d04458f50128e4`: ends at 2030 with `பின்வருவனவற்றை உள்ளடக்கியதுஃ` ("includes the following:") and no list
   - `1015e2e131199997`: ends at 1690 with `பின்வருமாறுஃ / குறிப்புகள். / மேற்கோள்கள் / ஆதாரங்கள்` (four empty headings)
2. **Medicine:** from the end of the document, remove lines while the last line is empty, a stray tag, a reference
   heading with nothing under it (குறிப்புகள், மேற்கோள்கள், ஆதாரங்கள், வெளி இணைப்புகள், மேலும் காண்க, நூலியல் ...),
   or a short line (60 characters or less) that ends in `ஃ` or `:` and whose list is gone. If less than 150
   characters are left, drop the document.

   ```python
   import re

   _REF_HEADINGS = {"குறிப்புகள்", "மேற்கோள்கள்", "ஆதாரங்கள்", "வெளி இணைப்புகள்", "மேலும் காண்க",
                    "நூலியல்", "நூல் பட்டியல்", "மேலும் படிக்க", "இவற்றையும் பார்க்கவும்"}


   def _is_dead_tail(line):
       s = line.strip()
       if not s or re.fullmatch(r"</?[^<>]+>", s):
           return True                                   # empty line or a stray tag
       if s.rstrip(".") in _REF_HEADINGS:
           return True                                   # "வெளி இணைப்புகள்." with nothing under it
       return s.endswith(("ஃ", ":")) and len(s) <= 60  # "வெற்றியாளர்கள் பின்வருமாறுஃ" whose list is gone


   def medicine_c3(text):
       """Remove the headings left at the end of a document after the list under them was cut.
       Drop the document if less than 150 characters are left."""
       lines = text.rstrip().split("\n")
       while len(lines) > 1 and _is_dead_tail(lines[-1]):
           lines.pop()
       out = "\n".join(lines)
       if out == text.rstrip():
           return text
       return out if len(out.strip()) >= 150 else True
   ```
3. **Action:** fix (drop when almost nothing is left).
4. **Harm test:**
   - Gold set (41): pending.
   - Stand-in (84 clean): changed 0, dropped 0 (0.00%). PASS.
   - My pack: treats 15 of the 47 C3 documents, and 3 that I did not label C3 (all end in `குறிப்புகள். <பிஆர்>` or
     a colon heading with no list).
5. **Side effects:**
   - Trailing whitespace at the end of a document is removed (any changed document also loses it).
   - A document that really ends on a one-line question or quote that ends in `:` loses that line.
   - It does not treat the other 32: a text cut in the middle of a sentence or a list has no heading to remove.
     Cutting back to the last full sentence would also change good documents, so I left it out.

## Medicine 8

1. **Disease:** D4, bad machine translation. Count in my pack: 284 (57% of the pack).
   - `9687c7aa0e255951`: `நகரம் ஆகும்.எஸ். மிச்சிகன் மாநிலம்` at 114 (the `.S.` of "U.S." moved after the next word)
   - `1af8a9c374c253e4`: `அவர் யு வென்றார்.எஸ். 1971` at 155 ("he won the U.S. 1971 ...")
   - `9c22a3084de95758`: `உதவினார்.எஸ். எடியூரப்பா` at 2109 (`B.S. Yediyurappa` split the same way)
2. **Medicine:** most D4 is wrong meaning (`கிரீடம் இளவரசர்` for "crown prince", `ஐந்து மற்றும் டைம்` for "five and
   dime"), and no text rule can fix meaning. This medicine treats the one D4 error that has a fixed form: the
   `.எஸ்.` of an abbreviation moved after the next word. If `யு` or `யூ` is right before that word, join them back
   (`யு வென்றார்.எஸ்.` becomes `யு.எஸ். வென்றார்`). Otherwise remove the stray `.எஸ்.` after a word of 4 or more
   Tamil letters (so initials like `கே.எஸ்.` are kept).

   ```python
   import re

   _US_SPLIT = re.compile(r"(யு|யூ) (\S+?)\.எஸ்\.")                  # "யு ஆதரவுடன்.எஸ். இராணுவம்"
   _US_TAIL = re.compile(r"(?<=[஀-௿]{4})\.எஸ்\.(?=\s)")   # "விரக்தியடைந்தார்.எஸ். போருக்கு"; 4 Tamil letters before keeps initials like கே.எஸ்.


   def medicine_d4(text):
       """Narrow fix for one machine-translation error: the ".S." of "U.S." moved after the next word.
       Join it back to யு/யூ when that is right before; otherwise remove the stray ".எஸ்."."""
       text = _US_SPLIT.sub(r"\1.எஸ். \2", text)
       return _US_TAIL.sub(".", text)
   ```
3. **Action:** fix. For the rest of D4 the action is at the source level: this pack is machine-translated as a
   whole, so its weight in the training mix should be set by the data team, not by a text rule.
4. **Harm test:**
   - Gold set (41): pending.
   - Stand-in (84 clean): changed 0, dropped 0 (0.00%). PASS. (On the first run it changed 2 documents I had
     labelled clean; both had this error and I relabelled them: `0eb3e17b78a07769` `பின்வருமாறு.எஸ். டெக்சாஸின்`,
     `47548b14a0cacfd3` `விரக்தியடைந்தார்.எஸ்.`, 6 times.)
   - My pack: treats 23 of the 284 D4 documents, and 7 that I did not label D4 (all the same `.எஸ்.` error).
5. **Side effects:**
   - When the lost letter was not `யு` (`B.S. Yediyurappa` becomes `உதவினார். எடியூரப்பா`), the initial is removed,
     not restored. The sentence reads better, but the name loses `பி.எஸ்.`.
   - A real abbreviation that ends in `.எஸ்.` after a long word (rare) loses it.
   - It treats only 23 of 284. The other 261 D4 documents stay as they are.

---

## Summary of the harm tests

Tool: `teams/02-data-b/tools/harm_test_indic.py` (lab `main`, after PR #148). Limit: max(1 document, 1%).

| Medicine | Gold set (41, ind-ta-sangraha-v) | Stand-in: my 84 clean, changed / dropped | Stand-in result |
|---|---|---|---|
| B2 | pending | 0 / 0 | PASS |
| B4 | pending | 0 / 0 | PASS |
| A6 | pending | 0 / 0 | PASS |
| G3 | pending | 0 / 0 | PASS |
| G4 | pending | 0 / 0 | PASS |
| C2 | pending | 0 / 0 | PASS |
| C3 | pending | 0 / 0 | PASS |
| D4 | pending | 0 / 0 | PASS |
| All in order | pending | 0 / 0 | PASS |

No medicine changed a ZWJ/ZWNJ count or broke NFC on the stand-in.
