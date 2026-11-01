# Medicine sheet: ind-gu-fw2 (Vedang)

Pack: 500 labelled documents (`labels-final.csv`): 158 labelled `clean`, 332 `fix`, 10 `drop`. Diseases found more than five times: C1 (174), D3 (284), A5 (24), F1 (19), C5 (19), A6 (18), C2 (13), D4 (12), B4 (6), G1 (6). Not above the threshold, so no medicine: C3 (5), G2 (4), C4 (3), D1 (2), A3 (2), B2 (2), F3 (1).

What changed since the last version: C4 dropped from 7 to 3 documents, so I removed its medicine. G1 went from 5 to 6, so it gets one now (Medicine 10). A5 went from 13 to 24 and its rule is fixed (the old one turned `અા` into `અ` instead of `આ`). C1 is 174 now and C2 is 13; their rules are the same. The other counts did not change.

I did not have the document texts, only the labels file, so I could not re-run anything. The harm-test results and the "acts on" numbers below are from the old run, or marked not run. They need to be run again on labels-final.csv before this sheet is final.

**Harm-test note (applies to all medicines).** I did not have the official Gujarati gold set. As a proxy I use the documents labelled `clean` in `labels-final.csv` (n=158). The old sheet had 178 clean rows and I removed 18 of them, because the medicines were changing them for a real defect the label had missed (a headline stored after the body, a view counter, a duplicated dateline, `ાે` for `ો`, a doubled vowel sign). The final file has 158 clean rows, so no one has to be removed now. The proxy is small. 1% of 158 is 1.6 documents, so one changed document (0.6%) passes and two (1.3%) fail. It also leaves out every document with a defect, so it is easier to pass than the real gold set. Re-run on the real gold set before this sheet is final. The code for C1, D3, C2, F1, C5, A6, D4 and B4 is the same as before. The A5 code is changed and the G1 code is new, and I have not run either on full documents.

## Medicine 1: C1 (Boilerplate)

1. **Disease:** C1, found in 174 of 500 labelled documents. Examples:
   - `9c013a675712ff90`: `Android: http://bit.ly/3ajxBk4` at offset 4017
   - `c829a1eb3044e514`: `Copyright © 2022-23 DB Corp ltd., All Ri` at offset 1390
   - `54525ab9a5efeb4b`: `સમગ્ર ઘટના CCTV આવ્યા સામે pic.twitter.c` at offset 93
2. **Medicine:** Delete whole lines that are site furniture: the Divya Bhaskar footer, the News18 promo, "read also" and `Tags:` lines, Instagram/tweet embeds, Saurashtra Kranti and GujjuRocks promo lines, source credits (`સૌજન્ય : દિવ્ય ભાસ્કર`), timestamps (`પોસ્ટનો સમય: …`), view counters (`57 , 1`), `Read More`, `જુઓ વિડીયો`, and the page promo `લેટેસ્ટ મનોરંજન, News અને Videos માટે પેજ લાઈક કરો`. In some newspaper pages the headline is stored after the body, followed by a final dateline (`(એજન્સી) તા.૬`); the headline line is deleted. The pattern must match the entire line.

   ```python
   import re

   LINE_PATTERNS = [
       r"Copyright © .*All Rights Reserved\.?",
       r"This website follows the DNPA Code of Ethics\.?",
       r"ગુજરાતી સમાચાર નો ખજાનો એટલે News18 ગુજરાતી\..*",
       r"View this post on Instagram",
       r"Tags:.*",
       r"(આ પણ વાંચો|તમે આ પણ વાંચી શકો છો)\s*[:\-–].*",
       r"આ પણ વાંચો\s*:?",
       r"(Subscribe|Visit) Saurashtra Kranti.*",
       r"Read (About Weather|National News|Saurashtra Kranti E-Paper).*",
       r"For any News, Event coverage.*",
       r"आपके किसी भी प्रकार.*",
       r"આપના કે આપની સંસ્થાના.*",
       r"You Can Find us on Google Play store too.*",
       r"Android: https?://\S+",
       r"— .{1,60}\(@\w+\).*\d{4}",
       r".*pic\.twitter\.com/\S+",
       r"(Article Source|Courtesy) : .*",
       r"[A-Z][a-z]{2} \d{1,2}, ?\d{4}, \d{1,2}:\d{2} [AP]M IST",
       r"Tap to Read ➤",
       r"[\d,]+ Views, \d+",
       r"વધુ વાંચો",
       r"અમારી (દર નવી|અન્ય) પોસ્ટ.*",
       r"તમે આ લેખ “ગુજ્જુ ગુજરાતી”.*",
       r"આવા વધુ સમાચારો માટે નીચેની લિન્ક.*",
       r"Author: GujjuRocks Team.*",
       r"\(નોંધ[ –-].*\)",
       r"નોંધ: આ વેબસાઇટ પર.*",
       r"ઉપરના આર્ટીકલના તમામ.*",
       r"ગુજરાતના તમામ સ્થળે પ્રેસ પ્રતિનિધિ.*",
       '\\"વંદે માતરમ ,ભારત માતાકી જય\\"',
       r"જંગ એ ગુજરાત ના વેબ ન્યૂઝ પોર્ટલ માટે",
       r"માનદ પ્રતિનિધિ નિમવાના છે.*",
       r"ચહેરો\d+ કલાક પહેલા",
       r"- લિંક કૉપિ કરો",
       r"🌺આરતીસોની🌺",
       r"-આરતીસોની ©",
   ]
   EXTRA = [
       r"\d{1,3} , \d{1,3}",
       r"લેટેસ્ટ મનોરંજન, News અને Videos માટે પેજ લાઈક કરો",
       r"Powered By .*",
       r"પોસ્ટનો સમય\s*:.*",
       r"સૌજન્ય\s*:?\s*(?:\n\s*)?દિવ્ય ભાસ્કર",
       r"ઇનપુટ્સ\s*:.*",
       r"જુઓ (?:આ )?વિડીયો",
       r"અમારી અન્ય પોસ્ટ પણ વાંચો\s*:?-?",
       r"સોશિયલ મીડિયા પ્લેટફોર્મ પર અમારી સાથે જોડાઓ",
       r"Visit Saurashtra Kranti Homepage here",
       r"Read About Weather here",
       r"(?:\.\.\. ?)?Read More",
       r"Team VTV.*",
   ]
   LINE = re.compile(r"^\s*(?:" + "|".join(LINE_PATTERNS + EXTRA) + r")\s*$\n?", flags=re.M)
   # headline line that is stored after the body, just before a final dateline such as "(એજન્સી) તા.૬"
   TRAIL = re.compile(r"\n[^\n]+\n(?=\(?[^\n]{0,30}\)?[ ,]*તા\.? ?[\d૦-૯]+\s*$)")

   def medicine(text):
       return TRAIL.sub("\n", LINE.sub("", text))
   ```

3. **Action:** fix. Only whole lines (and the trailing headline) are removed; a phrase inside a sentence is left alone.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 174 (old run: 132 of 164).
5. **Side effects:** Misses C1 that is not on its own line or comes from another site: `MUST READ:` and `READ ALSO` glued to text, a `ન્યૂઝ18 ગુજરાતી :` prefix glued to the first sentence, `જુઓ આગળની સ્લાઈડ્સ…`, source lines such as `શ્રોત: ગ્રામીણ ટુડે ન્યુઝ`, other wording of the English "This article is available in…" footer, and `- ` bullet lists of related links. The publisher lines (Divya Bhaskar, News18, Saurashtra Kranti, GujjuRocks) will not match other sites. A real one-line sentence equal to `વધુ વાંચો` would be deleted. If a real article ends with a headline-like line before a dateline, that line is deleted.

## Medicine 2: D3 (Mixed language)

1. **Disease:** D3, found in 284 of 500 labelled documents. Examples:
   - `9c013a675712ff90`: `vaishnav` at offset 114
   - `fb4348530cc01c8e`: `Copyright` at offset 1593
   - `b97cb6db98d14b11`: `Pathan` at offset 25
2. **Medicine:** Delete whole lines that have no Gujarati letter and at least 25 Latin letters (embedded tweets, English footers and headings, transliterated verses). Words and acronyms inside a Gujarati sentence (`CBSE`, `Paytm`, `S10માં`) are natural mixing and are not touched.

   ```python
   import re

   GU = re.compile(r"[઀-૿]")
   LAT = re.compile(r"[A-Za-z]")

   def medicine(text):
       # Keep a line unless it is English-only and long.
       return "\n".join(l for l in text.split("\n")
                        if GU.search(l) or len(LAT.findall(l)) < 25)
   ```

3. **Action:** fix. Natural Gujarati-English mixing is not touched (label it, do not judge it); only English-only lines are removed.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 284 (old run: 96 of 284).
5. **Side effects:** In the old run it acted on 96 of 284 documents; the rest are natural mixing and need no medicine. Most of the changed documents are also changed by C1. It removes a real English quotation or English headline that is the point of the document, and a mostly-English document could lose most of its text, so run it after a language check. Romanised Hindi in Latin script is removed too, but that is really D2 and needs its own rule.

## Medicine 3: A5 (Wrong normal form (broken vowel signs))

1. **Disease:** A5, found in 24 of 500 labelled documents. Examples:
   - `8e517616dfb6854a`: `હતોે` at offset 251 (`0AB9 0AA4 0ACB 0AC7`)
   - `981bfe6e8a36077c`: `વાસ્ચવિક્તાઓ` at offset 1845 (`0AB5 0ABE 0AB8 0ACD 0A9A 0AB5 0ABF 0A95 `)
   - `3913921527d55e20`: `ચોથાા` at offset 1074 (`0A9A 0ACB 0AA5 0ABE 0ABE`)
2. **Medicine:** Repair the broken vowel-sign sequences left by legacy-font conversion: a doubled sign (`તાલુુકા`, `વગેેરે`), `ાે` → `ો` (`જાેકે` → `જોકે`), `ાૈ`/`ૈા` → `ૌ`, `અા` → `આ`, `અે` → `એ`, `અો` → `ઓ` (and `અૈ`, `અૌ`), a sign after an independent vowel (`આાસન`), a nukta after a sign (`જે઼`). `રૂા` (rupee shorthand) is correct and is protected.

   ```python
   import re

   SIGN = "\u0abe-\u0ac5\u0ac7-\u0ac9\u0acb\u0acc"      # Gujarati vowel signs

   def medicine(text):
       t = text.replace("રૂા", "\0")                      # rupee shorthand is correct, protect it
       t = (t.replace("\u0a85\u0abe", "\u0a86")           # અ + ા  ->  આ
             .replace("\u0a85\u0ac7", "\u0a8f")           # અ + ે  ->  એ
             .replace("\u0a85\u0ac8", "\u0a90")           # અ + ૈ  ->  ઐ
             .replace("\u0a85\u0acb", "\u0a93")           # અ + ો  ->  ઓ
             .replace("\u0a85\u0acc", "\u0a94"))          # અ + ૌ  ->  ઔ
       t = re.sub(f"([{SIGN}])\\1+", r"\1", t)           # the same sign twice
       t = (t.replace("\u0abe\u0ac7", "\u0acb")          # ાે -> ો
             .replace("\u0abe\u0ac8", "\u0acc")          # ાૈ -> ૌ
             .replace("\u0ac8\u0abe", "\u0acc"))         # ૈા -> ૌ
       t = re.sub(f"([\u0a85-\u0a94])[{SIGN}]", r"\1", t)  # sign after an independent vowel
       t = re.sub(f"([{SIGN}])[{SIGN}]", r"\1", t)         # any other two signs: keep the first
       t = re.sub(f"([{SIGN}\u0a82])\u0abc", r"\1", t)    # nukta after a sign
       return t.replace("\0", "રૂા")
   ```

3. **Action:** fix. The sign sequences are repaired in place; the rest of the text stays. NFC alone does not fix these.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: **NOT RUN** for the new rule. The old rule gave changed 0, dropped 0 → PASS. The new `અ` lines only touch `અ` followed by a vowel sign, which should not appear in correct text, but that needs checking. On my labelled documents with this disease it acts on ? of 24 (old run: 9 of 13).
5. **Side effects:** Some repairs are a guess: when two different signs are stacked (`સાથૂી`) the rule keeps the first, which may be the wrong one, so the word is still wrong. A wrong or doubled consonant is not found (`શરરૂઆત`, `રિઝર્લ`, `મહીઅલાઓ`). The old version of this rule turned `અા` and `અો` into `અ`, so `અાજે` became `અજે`. The new `અ` lines fix that. I only tried the new code on sample strings from the CSV. Wrong letters that are valid Gujarati are invisible to it. Do not run it on text that is already NFC and correct: it changes nothing there, but it is not a spell checker.

## Medicine 4: C2 (Repeated lines)

1. **Disease:** C2, found in 13 of 500 labelled documents. Examples:
   - `98b9ca997dc64e33`: `અંબાજી મંદિરના મુખ્ય શિખરને સુવર્ણમય બનાવવા` at offset 998
   - `8a8d9a6ffd1d7271`: `જ્યારે યુ.એસ. માં શ્રેષ્ઠ રાષ્ટ્રી…` at offset 0
   - `b85dd656e0a0f691`: `રાખી સાવંતની માતાનું નિધન,બ્રે` at offset 8340
2. **Medicine:** Keep the first copy of a line longer than 15 characters and delete later identical copies. Lines ending in `,` or `…` are kept, because poems repeat refrains.

   ```python
   def medicine(text):
       seen, out = set(), []
       for line in text.split("\n"):
           key = line.strip()
           if len(key) > 15 and not key.endswith((",", "…")):   # keep poem refrains
               if key in seen:
                   continue
               seen.add(key)
           out.append(line)
       return "\n".join(out)
   ```

3. **Action:** fix. Keep the first copy, delete the later copies.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 13 (old run: 6 of 7).
5. **Side effects:** Misses repeats that are short (a dateline under 16 characters such as `અમદાવાદ, તા.ર`), differ in a number (`59300 રૂપિયા`), or were cut at a different place. A deliberate repeated slogan or chorus that does not end in `,` or `…` would be deleted.

## Medicine 5: F1 (Personal data)

1. **Disease:** F1, found in 19 of 500 labelled documents. Examples (type and offset only, no values):
   - `79e1f2d27c8fda29`: phone at offset 1924
   - `272bab66c491c858`: phone at offset 2043
   - `5a8e7392dd213881`: phone at offset 1651
2. **Medicine:** Replace email addresses and phone numbers (10-digit mobiles, `+91` numbers, landlines with area code, in Latin or Gujarati digits) with `<EMAIL>` and `<PHONE>`. example.com placeholder addresses are left for B4.

   ```python
   import re

   EMAIL = re.compile(r"[\w.+-]+@(?!example\.com)[\w-]+\.[\w.]+")
   PHONE = re.compile(
       r"(?<![\d.])(?:\+91[ -]?)?[6-9]\d{4}[ -]?\d{5}(?!\d)"   # mobile
       r"|(?<!\d)\d{3}\d{3}\d{4,}(?!\d)"                       # long digit run
       r"|\b0\d{2,4}[ -]\d{6,8}\b")                            # landline

   def medicine(text):
       return EMAIL.sub("<EMAIL>", PHONE.sub("<PHONE>", text))
   ```

3. **Action:** fix. The values are masked and the rest of the document stays.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 19 (old run: 17 of 19).
5. **Side effects:** Does not find the private-name-plus-locality case, because a regex cannot find names. It masks public helpline numbers (a government employment helpline) that are not private data. A Latin digit run of 10 or more digits that is an order or ID number is masked as a phone number.

## Medicine 6: C5 (Lists of keywords or links)

1. **Disease:** C5, found in 19 of 500 labelled documents. Examples:
   - `cf008373747082a4`: `Tags: અંડર વર્લ્ડ ડોન` at offset 1242
   - `8fb11ce7723f2e80`: `Tags:` at offset 2150
   - `111b541c64c8d29b`: `Tags:` at offset 1943
2. **Medicine:** Delete `Tags:` lines that have two or more commas or eight or more words, and lines that are a comma list of five or more mostly-Latin items with no digit, colon or full stop.

   ```python
   import re

   def medicine(text):
       keep = []
       for line in text.split("\n"):
           s = line.strip()
           latin = len(re.findall("[A-Za-z]", s))
           letters = max(1, len(re.sub(r"\W", "", s)))
           tags = s.startswith("Tags:") and (s.count(",") >= 2 or len(s.split()) >= 8)
           word_list = (len(s.split(",")) >= 5 and latin > 0.7 * letters
                        and not re.search(r"[:\d]", s) and not s.endswith("."))
           if not (tags or word_list):
               keep.append(line)
       return "\n".join(keep)
   ```

3. **Action:** fix. Delete the tag or keyword line only.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 19 (old run: 17 of 19).
5. **Side effects:** Misses keyword lists written in Gujarati (`ugvcl બિલ ઑનલાઇન કેવી રીતે જોવું, …`) and `- ` bullet lists of links. A real `Tags:` line with a few words is deleted, which is intended, but it is also boilerplate (C1).

## Medicine 7: A6 (Wrong or mixed script)

1. **Disease:** A6, found in 18 of 500 labelled documents. Examples:
   - `79e1f2d27c8fda29`: `आ` at offset 2039 (`0906 092A 0915`)
   - `f5b5303747485fca`: `अ` at offset 3872 (`0905 `)
   - `194f2b945bfbeb1f`: `क` at offset 670 (`0915`)
2. **Medicine:** Two rules. **A6a:** if a lowercase Latin run of 1 to 8 letters has a Gujarati letter on both sides, drop the document. **A6b:** otherwise delete lines that contain Devanagari letters; if more than 30% of the lines are deleted, drop the document. The Devanagari danda `।` is not counted.

   ```python
   import re

   SANDWICH = re.compile(r"[઀-૿][a-z]{1,8}[઀-૿]")
   DEVANAGARI = re.compile(r"[\u0900-\u0963\u0966-\u097f]")      # letters, not the danda

   def medicine(text):
       if SANDWICH.search(text):
           return None                       # drop the document
       lines = text.split("\n")
       keep = [l for l in lines if not DEVANAGARI.search(l)]
       if len(keep) < 0.7 * len(lines):
           return None                       # drop the document
       return "\n".join(keep)
   ```

3. **Action:** A6a drops the document (a corrupted word makes the text around it unreliable). A6b deletes Hindi lines and drops the document if more than 30% of lines go.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 18 (old run: 15 of 18).
5. **Side effects:** In the old run it acted on only 15 of 18 documents. It does not cover Gujarati letters used as digits (`ર01ર`, `ર૯પ`), a U+201A comma-like character in place of `ૂ`, candra signs (`અપૅણ`, `નેતાઑ`), long ઊ for ઉ, wrong letters (`વિઘુત`), or a lone Latin letter between spaces (`બનાવવી l હોમમેઇડ`). The digit-letter case can be repaired by a rule but only inside numbers, which I did not write; the others need a spelling model. The 30% threshold is a proposal and has not been tuned. Real Hindi or Sanskrit quotations in a Gujarati article are removed even though they are correct text. A lowercase brand glued between two Gujarati letters is dropped. Dropping a whole document for one corrupted word loses a lot of good text; if the drop rate on the real gold set is above 1%, change A6a to remove only the affected sentence.

## Medicine 8: D4 (Bad machine translation)

1. **Disease:** D4, found in 12 of 500 labelled documents. Examples:
   - `014f6b1dc9a324be`: `ક્રીપ પ્રતિરોધક, પર્યાવરણીય તણાવ ક…` at offset 339
   - `0ec81e67b8a18c56`: `આઇએમએમ breakingપલ વ Watchચને` at offset 7409
   - `0f3d75a890fadfcb`: `તારીખ સાથે પ્રદેશ⏎સમ` at offset 0
2. **Medicine:** Drop the document if a lowercase Latin run of 1 to 8 letters sits between Gujarati letters (the same sign as A6a). This is the only part of D4 that a rule can see; the rest needs a quality model (see side effects).

   ```python
   import re

   SANDWICH = re.compile(r"[઀-૿][a-z]{1,8}[઀-૿]")

   def medicine(text):
       # Latin letters glued inside a Gujarati word: the translation is broken, drop the document.
       return None if SANDWICH.search(text) else text
   ```

3. **Action:** drop. A broken translation cannot be repaired by a rule.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 12 (old run: 4 of 12).
5. **Side effects:** In the old run it acted on only 4 of 12 documents. It misses translations that are wrong but have no Latin letters: repeated or untranslated phrases (`મિક્સ કરો અને મિક્સ કરો`), incoherent spam text, and unnatural wording. Those need a language-model quality score, which I did not run. D4 labels are my judgement, not a measurement, so the acts-on number is only a lower bound for how bad the disease is. Dropping documents costs data.

## Medicine 9: B4 (Template and code junk)

1. **Disease:** B4, found in 6 of 500 labelled documents. Examples:
   - `b67a6cca719bf1d7`: `#IndiaWantsCrypto` at offset 3353
   - `a4ab5516e2836afa`: `[ઇમેઇલ સુરક્ષિત]` at offset 11188
2. **Medicine:** Delete template and placeholder junk: `[ઇમેઇલ સુરક્ષિત]` and `[email protected]` (email obfuscation placeholders), example.com placeholder addresses, `{{ … }}`, `${ … }`, and the whole words `undefined`, `NaN`, `null`.

   ```python
   import re

   JUNK = re.compile(r"\[ઇમેઇલ સુરક્ષિત\]|email@example\.com|firstname\.lastname@example\.com"
                     r"|\[email\s*protected\]|\{\{.*?\}\}|\$\{.*?\}|\bundefined\b|\bNaN\b|\bnull\b")

   def medicine(text):
       return JUNK.sub("", text)
   ```

3. **Action:** fix. Delete the junk token; the sentence stays.
4. **Harm test:** proxy gold set (`clean` rows in labels-final.csv), n=158: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). This is the old result and has not been re-run. On my labelled documents with this disease it acts on ? of 6 (old run: 4 of 6).
5. **Side effects:** Misses hashtags such as `#IndiaWantsCrypto` (it is part of the post). The word `null` or `undefined` inside a real English quotation is deleted. Email-obfuscation placeholders in other languages or spellings will not match.

## Medicine 10: G1 (Detached or orphaned marks)

1. **Disease:** G1, found in 6 of 500 labelled documents. I made up the name from the evidence, so swap in the official one. Examples:
   - `774bfbc8ab7805ba`: `ા ં` at offset 677 (`0ABE 0020 0A82`)
   - `674c953262045ec3`: `જ િ` at offset 818 (`0A9C 0020 0ABF`)
   - `be329b1fecf270e9`: `ૂંટણીને` at offset 32 (`0AC2 0A82 0A9F 0AA3 0AC0 0AA8 0AC7`)
2. **Medicine:** Delete a space that sits between a Gujarati consonant, virama or vowel sign and a following vowel sign or anusvara (`જ િ` → `જિ`, `ા ં` → `ાં`). A word cannot start with a vowel sign, so that space is not a real word break.

   ```python
   import re

   # space before a vowel sign / anusvara, after a consonant, virama or vowel sign
   DETACHED = re.compile("(?<=[\u0a95-\u0ab9\u0acd\u0abe-\u0acc]) +(?=[\u0abe-\u0acc\u0a82])")

   def medicine(text):
       return DETACHED.sub("", text)
   ```

3. **Action:** fix. Only the stray space is removed; the rest of the text stays.
4. **Harm test:** **NOT RUN.** I had no document texts. On the six evidence strings from the CSV it fixes `જ િ` and `ા ં`, turns `કરતા ંચું` into `કરતાંચું`, and leaves `ૂંટણીને`, `અર્ધગ્ધ` and `જ્ .ા` as they are. Run it on the 158 clean documents first.
5. **Side effects:** It cannot bring back a lost letter (`ૂંટણીને` lost its consonant, `અર્ધગ્ધ` lost a letter), so those words stay wrong. If the space was a real word break and the next word lost its first letter (`કરતા ંચું`), the join glues two words into a non-word. A stray full stop between the pieces (`જ્ .ા`) is not handled. Two of the six documents are already labelled `drop`, so this rule gains little.
