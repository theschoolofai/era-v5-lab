# Medicine sheet: ind-gu-fw2 (Vedang)

Pack: 152 labelled documents, 45 labelled `clean`. Diseases found more than five times: C1 (63), D3 (94), F1 (11), A6 (9). C2 (5) and D4 (5) are not above the threshold, so they have no medicine.

**Harm-test note (applies to all four medicines).** The official Gujarati gold set was not available to me. As a proxy I used the 45 documents I labelled `clean` in my label sheet (n=45). The proxy is small: 1% of 45 is less than one document, so any change counts as a fail. The numbers must be re-run on the real gold set before this sheet is final.

## Medicine 1: C1 (Boilerplate)

1. **Disease:** C1, found in 63 of 152 labelled documents. Examples:
   - `bfbddfa37a31c087`: Copyright © 2022-23 DB Corp ltd., All Rights Reserved at offset 1308
   - `f8b8774484d54393`: ગુજરાતી સમાચાર નો ખજાનો એટલે News18 ગુજરાતી. at offset 1934
   - `e67f381e4b67937d`: View this post on Instagram at offset 286
2. **Medicine:** Delete whole lines that are site furniture, not article text:
   - the Divya Bhaskar footer (`Copyright © … All Rights Reserved`, `This website follows the DNPA Code of Ethics.`) and the News18 promo line;
   - "read also" lines (`આ પણ વાંચો`, `તમે આ પણ વાંચી શકો છો`), `Tags:` lines, `વધુ વાંચો`, and `View this post on Instagram`;
   - Saurashtra Kranti link lines, news-desk contact promos in Gujarati, English and Hindi, and `Android:` app links;
   - tweet credit lines (`— Name (@handle) Month D, YYYY`) and lines with `pic.twitter.com/…`;
   - source credits (`Article Source :`, `Courtesy :`), page timestamps (`Oct 18,2021, 20:36 PM IST`), `Tap to Read ➤`, view counters, press-representative recruiting lines, and a few GujjuRocks and Aarti Soni credit lines.

   The pattern must match the entire line.

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
       r"— .{1,60}\(@\w+\).*\d{4}",              # tweet credit line
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
       r"\"વંદે માતરમ ,ભારત માતાકી જય\"",
       r"જંગ એ ગુજરાત ના વેબ ન્યૂઝ પોર્ટલ માટે",
       r"માનદ પ્રતિનિધિ નિમવાના છે.*",
       r"ચહેરો\d+ કલાક પહેલા",
       r"- લિંક કૉપિ કરો",
       r"🌺આરતીસોની🌺",
       r"-આરતીસોની ©",
   ]
   PAT = re.compile(r"^\s*(?:" + "|".join(LINE_PATTERNS) + r")\s*$\n?", flags=re.M)

   def medicine(text):
       return PAT.sub("", text)
   ```

3. **Action:** fix. Only whole lines are removed; a phrase inside a sentence is left alone.
4. **Harm test:** proxy gold set (my own documents labelled clean; the official Gujarati gold set was not available to me), n=45: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 50 of 63.
5. **Side effects:** Misses C1 that is not on its own line (for example `ન્યૂઝ18 ગુજરાતી :` glued to the first sentence, `Author: GujjuRocks Team` glued to the promo text, and promo lines in the middle of a sentence). Related-link bullet lists that start with `- ` are not covered. The publisher-specific lines (Divya Bhaskar, News18, Saurashtra Kranti, GujjuRocks) will not match other sites. A real one-line sentence that is only `વધુ વાંચો` or `Tags: …` would be deleted.

## Medicine 2: D3 (Mixed language)

1. **Disease:** D3, found in 94 of 152 labelled documents. Examples:
   - `676aea07ba8ddf25`: Shameful gesture by @MStoinis regarding bowling action… at offset 1344
   - `0bb02359d03a32e7`: Mumbai Police arrest Republic TV CEO … at offset 351
   - `3ed1c081935c62ce`: anāśritaḥ karmaphalaṃ kāryaṃ karma karōti yaḥ at offset 126
2. **Medicine:** Delete whole lines that have no Gujarati letter at all and at least 25 Latin letters: embedded tweet text, English footers and headings, and transliterated verses. Words and acronyms inside a Gujarati sentence (`CBSE`, `Paytm`, `S10માં`) are natural mixing and are not touched.

   ```python
   import re

   GU = re.compile(r"[઀-૿]")
   LAT = re.compile(r"[A-Za-z]")

   def medicine(text):
       # Keep a line unless it is English-only and long.
       return "\n".join(l for l in text.split("\n")
                        if GU.search(l) or len(LAT.findall(l)) < 25)
   ```

3. **Action:** fix. Natural Gujarati-English mixing is not touched (DISEASES.md: label it, do not judge it); only English-only lines are removed.
4. **Harm test:** proxy gold set (my own documents labelled clean; the official Gujarati gold set was not available to me), n=45: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 31 of 94. Most of the 94 are natural mixing and need no medicine.
5. **Side effects:** Most of the 31 documents it changes are already fixed by Medicine 1. It also removes a real English quotation or an English headline that is the point of the document. A document that is mostly English could lose most of its text, so run this after a language check. Romanised Hindi lines in Latin script (`Gharwalon par bane memes…`) are removed, but those are really D2 and need their own rule.

## Medicine 3: F1 (Personal data)

1. **Disease:** F1, found in 11 of 152 labelled documents. Examples (type and offset only, no values):
   - `79e1f2d27c8fda29`: phone number at offset 1924
   - `600f00a985c89202`: phone number at offset 7544 and email at offset 7847
   - `ba50fb1f69975aea`: phone number at offset 4010
2. **Medicine:** Replace email addresses and phone numbers (10-digit mobile numbers, numbers with `+91`, and landlines with an area code) with `<EMAIL>` and `<PHONE>`.

   ```python
   import re

   EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
   PHONE = re.compile(
       r"(?<![\d.])(?:\+91[ -]?)?[6-9]\d{4}[ -]?\d{5}(?!\d)"   # mobile
       r"|(?<!\d)\d{3}\d{3}\d{4,}(?!\d)"                       # long digit run
       r"|\b0\d{2,4}[ -]\d{6,8}\b")                            # landline

   def medicine(text):
       return EMAIL.sub("<EMAIL>", PHONE.sub("<PHONE>", text))
   ```

3. **Action:** fix. The values are masked and the rest of the document stays.
4. **Harm test:** proxy gold set (my own documents labelled clean; the official Gujarati gold set was not available to me), n=45: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 10 of 11.
5. **Side effects:** Misses the one F1 document where the problem is a private person's full name next to a home locality (a regex cannot find names). It misses phone numbers written in Gujarati digits. A Latin digit run of 10 or more digits that is not a phone number (an ID or order number) would be masked.

## Medicine 4: A6 (Wrong or mixed script)

1. **Disease:** A6, found in 9 of 152 labelled documents (5 with Latin letters inside Gujarati words, 4 with Devanagari). Examples:
   - `0992299d9580a5a2`: તેcણે at offset 465 (`0AA4 0AC7 0063 0AA3 0AC7`)
   - `8a8d9a6ffd1d7271`: વletલેટ at offset 558 (`0AB5 006C 0065 0074 0AB2`)
   - `953dc7a7731c47d7`: પે ofીનું at offset 1255 (`0AAA 0AC7 0020 006F 0066`)
2. **Medicine:** Two rules.
   - **A6a:** if any lowercase Latin run of 1 to 8 letters has a Gujarati letter on both sides, drop the document. The correct word cannot be recovered.
   - **A6b:** otherwise delete lines that contain Devanagari. If more than 30% of the lines are deleted, drop the document.

   ```python
   import re

   SANDWICH = re.compile(r"[઀-૿][a-z]{1,8}[઀-૿]")
   DEV = re.compile(r"[ऀ-ॿ]")

   def medicine(text):
       if SANDWICH.search(text):
           return None                      # drop
       lines = text.split("\n")
       keep = [l for l in lines if not DEV.search(l)]
       if len(keep) < 0.7 * len(lines):
           return None                      # drop
       return "\n".join(keep)
   ```

3. **Action:** A6a drops the document, because a corrupted word means the translation around it is unreliable. A6b fixes the text, and drops it when most of it is Devanagari.
4. **Harm test:** proxy gold set (my own documents labelled clean; the official Gujarati gold set was not available to me), n=45: changed 0, dropped 0 (0.0%) → **PASS** (limit 1%). On my labelled documents with this disease it acts on 9 of 9.
5. **Side effects:** The 30% threshold is a proposal and has not been tuned. Real Hindi or Sanskrit quotations in a Gujarati article (a Gita verse, a quoted footer) are removed even though they are correct text. Gujarati suffixes after Latin words (`S10માં`) have Latin on one side only, so they are not matched. A lowercase brand glued between two Gujarati letters would be dropped. Dropping a whole document for one corrupted word loses a lot of good text; if the drop rate on the real gold set is above 1%, change A6a to remove only the affected sentence.
6. 
