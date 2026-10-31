# Medicine sheet: ind-bn-fw2 (sohamniyogi)

Pack: 500 documents, `HuggingFaceFW/fineweb-2 | ben_Beng`, 1.34 M characters. Labels: 314 clean, 148 fix, 38 drop.

## What this pack has and does not have

- **No** ZWSP, BOM, bidi marks, soft hyphens (A1), control characters (A2), U+FFFD (A4), HTML entities or tags (B1, B2),
  or ghost chat markers (B3) anywhere in the pack. I checked all 1.34 M characters, not only the documents I read.
- **The pack is fully NFC.** All 22,571 য় and 3,601 ড় are in decomposed form (base + nukta U+09BC), which is
  the NFC form, because U+09DC/U+09DD/U+09DF are composition exclusions. So A5 is not about NFC here. It is only
  about two-part vowels written in reverse order (Medicine 9).
- **ZWJ and ZWNJ count: 0 in the whole pack.** Real Bengali web text always has some, so they were stripped before
  release. The visible damage from this is G2 (Medicine 2).
- Emails are already masked by FineWeb-2 (`email@example.com`, `firstname.lastname@example.org`). Phone numbers are
  not masked. F1 occurs only 2 times, so it gets no medicine, but both rows are labelled with type and offset.

## About the harm tests below

**Official gold set (31 Oct): every medicine PASSES, 0 of 238 gold documents changed or dropped.** The gold set is
`teams/02-data-b/gold/ind-bn-fw2_gold.csv` (rebuilt in #161, unchanged from the interim set): 238 documents of this pack
that both readers (aditeyaaitronics and I) labelled clean, with 0 disputed. It lists ids only, so I joined the text from
the pack by `doc_id` and ran the command below on it. Because I am one of the two readers, the gold set is a subset of my
own 314 clean rows. A second, independent reader agreed on each of these documents, so the circularity is smaller than
with the proxy, but it is not gone. This matters most for M2 (see its warning).

The proxy result is kept for comparison: **the 314 documents of this pack that I labelled `clean`**. For the
character medicines (M2, M4, M7, M9) I used the same detector to label, so 0 % on the proxy is true by construction.
The proxy still found real problems. A first version of M5 changed 5 % of it (FAIL), so I tightened M5. M1 first
changed 8 proxy documents (2.5 %). All 8 were real boilerplate that I had missed, so I relabelled them as C1.

**Ready for the official gold set.** The code at the end of this sheet runs the full harm test with one command and
prints the result as a Markdown table (the "Gold" column below):

```
awk '/^```python$/{f=1;next} /^```$/{f=0} f' medicine.md > medicine.py
python medicine.py <bn-gold>
```

`<bn-gold>` can be a `.parquet`, `.jsonl`, `.json` or `.csv` file, or a folder of them. The script reads the text from
a `text`, `content` or `document` column and the URL from `url`, `source_url` or `meta.url`. If there is a language
column, it keeps only Bengali rows (`--all-langs` turns this off). If the gold set has no URL, M3 is reported as
"not tested", not as PASS. For each medicine that fails, the script lists the gold `doc_id`s it hit, so each one can be
checked. I tested the script on all four input formats, and on the whole pack as a deliberately dirty "gold" set, where
it reports FAIL for M1, M2, M3, M4, M7, M8 and M9, as expected.

| Medicine | Disease | Docs in pack | Action | Fires on pack (agrees with my labels) | Proxy gold changed / dropped (of 314) | Gold changed / dropped (of 238) | Result |
|---|---|---|---|---|---|---|---|
| M1 | C1 boilerplate lines | 95 | fix | 44 (42) | 0 / 0 | 0 / 0 | PASS |
| M2 | G2 lost ZWJ in র‍্যা | 50 | fix | 50 (50) | 0 / 0 | 0 / 0 | PASS, see the warning |
| M3 | D4 MT spam sites | 36 | drop | 26 (26) | 0 / 0 | 0 / 0 | PASS |
| M4 | A6 look-alike danda U+09F7 | 17 | fix | 11 (11) | 0 / 0 | 0 / 0 | PASS |
| M5 | C5 keyword-stuffed lines | 11 | fix | 1 (1) | 0 / 0 | 0 / 0 | PASS, low recall |
| M6 | F3 porn / gambling promotion | 8 | drop | 5 (5) | 0 / 0 | 0 / 0 | PASS |
| M7 | A3 legacy-font leftovers | 7 | fix | 7 (7) | 0 / 0 | 0 / 0 | PASS |
| M8 | C2 repeated lines | 9 | fix | 8 (7) | 1 / 0 | 0 / 0 | PASS (0.32 %) |
| M9 | A5 two-part vowel reversed | 7 | fix | 7 (7) | 0 / 0 | 0 / 0 | PASS |
| M10 | C3 truncated tail | 7 | fix | 5 (3) | 0 / 0 | 0 / 0 | PASS |
| M11 | G1 detached virama | 6 | fix | 2 (2) | 0 / 0 | 0 / 0 | PASS, low recall |

D3 (10 rows, plus 2 rows that are only an Arabic Qur'an or hadith quotation, labelled clean with a note) gets
**no medicine**. The mixing is
natural, and DISEASES.md says to label it, not judge it. D5 (5) and B4 (5) are not more than five, so they get no
medicine.

---

## Medicine 1: C1 boilerplate lines

1. **Disease:** C1, 95 documents. Examples: `6ffbbf510a981e67` "এ বিভাগের সর্বাধিক পঠিত" and "প্রিন্ট" at the end;
   `25ce3d7ca0f24773` "For all the latest Sports News Click Here"; `a04341dee190908a` (and all bn.topwar.ru pages)
   "সাবস্ক্রাইব করুন এবং সর্বশেষ খবর এবং দিনের সবচেয়ে গুরুত্বপূর্ণ ইভেন্টগুলির সাথে আপ টু ডেট থাকুন।";
   `ab306b59d8e205f6` "…'হোয়াটসঅ্যাপে ফলো করুন এই সময়কে।"
2. **Medicine:** delete a line only if the *whole line* matches a known furniture pattern (`C1_LINE` in the code:
   "আরও পড়ুন: …", "শেয়ার করুন", "মন্তব্য করুন", "বিজ্ঞাপন", "প্রিন্ট সংস্করণ", "সর্বশেষ", "সর্বাধিক পঠিত",
   "View this post on Instagram", "Read More", "N total views, M views today", "[hupso]", a lone "#", …) **and** the
   line is among the first 3 or last 6 lines of the document.
3. **Action:** fix (delete the line).
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy gold 0 changed, 0 dropped of 314 (0 %). PASS.
5. **Side effects:** a real headline that is exactly "সর্বশেষ" or "বিজ্ঞাপন" in the last 6 lines is deleted. The
   medicine does not catch furniture glued to prose ("শিরোনামOther", "সিলেট সদর Read More"), desk/initials lines
   ("জিএমএম/এএটি"), related-headline lists, or share requests written as a full sentence. Those need a list model. It
   fires on 44 of the 95 C1 documents.

## Medicine 2: G2 lost ZWJ in the loanword form র‍্যা

1. **Disease:** G2, 50 documents, 136 occurrences. The pack has 0 ZWJ, so every র‍্যা (RAB, rally, brand, track)
   became র্যা, which renders as ya-phala with reph (r-ya), not as ra with ya-phala. Examples: `3024066d06a72875` "র্যাব"
   at 105 (hex `E0 A6 B0 E0 A7 8D E0 A6 AF E0 A6 BE`); `cce9dc39b1581ffb` "ব্র্যান্ডিং" x40 from offset 25;
   `61e81566d086ef88` "র্যালী" at 36.
2. **Medicine:** `র্যা` at a word start or right after a virama becomes `র + ZWJ + ্যা`:
   `re.sub("(?:^|(?<=[^ঀ-৿])|(?<=্))র্যা", "র‍্যা", t)`.
   The rule needs the following া. Without it, native words like দারিদ্র্য and বৈচিত্র্য would also match, and they
   must not change. Words like কার্যালয় do not match because the র follows া, not a word start or a virama.
3. **Action:** fix.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314 (circular, see above). **Warning:** a gold set built from the same FineWeb-2 dump
   will have the same ZWJ loss. In this pack, 10 % of documents contain the pattern. A medicine that *correctly* changes
   10 % of the gold set fails the 1 % rule as written. I recommend restoring ZWJ/ZWNJ upstream (re-extracting from the
   source HTML) and not patching documents. If it must be a medicine, the gold set must be checked for the same loss
   first. The official gold set confirms this: it has 0 ZWJ too. Its 0 % only shows that no gold document has the
   loanword form M2 targets (র্যা at a word start or after a virama). 55 gold documents have র্যা inside native words
   such as কার্যালয়, and M2 correctly leaves them alone. Every document with the loanword form was labelled G2, so it
   could not be in the gold set.
5. **Side effects:** a transliterated name that really is written র্যা without ZWJ (rare) gets a ZWJ. The medicine does
   not fix lost ZWNJ, which has no reliable surface pattern.

## Medicine 3: D4 machine-translated spam sites (drop)

1. **Disease:** D4, 36 documents. Examples: `6a18f8751bb83059` bn.horoskopdnevni.com "বৃহস্পতি বিপরীতমুখীটি যখন
   অষ্টাদশীতে"; `3092e9bd6566d7fc` bn.utaheconomicandenergysummit.com "মানুষ এটি লাঠি" (English "stick it");
   `a04341dee190908a` and 8 other bn.topwar.ru pages (machine-translated Russian news).
2. **Medicine:** drop the document if the URL host starts with `bn.` and is not in a short allow-list of real Bengali
   editions (`bn.mtnews24.com`, `bn.globalvoices.org`, `bn.wikipedia.org`, `bn.m.wikipedia.org`,
   `bn.ekusherbangladesh.com.bd`, …). These `bn.` subdomains of foreign sites are auto-translation farms.
3. **Action:** drop.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** a new real Bengali edition on a `bn.` host is dropped until it is added to the allow-list. It does
   not catch MT on normal hosts (enigmasoftware.com, actualidadgadget.com, drcockatiel.com). It fires on 26 of 36.

## Medicine 4: A6 look-alike danda U+09F7

1. **Disease:** A6, 17 documents: 13 with U+09F7, 3 with Assamese ৰ U+09F0 (one also has U+09F7), 1 with
   U+2019 inside words ("ঘনি’ষ্ঠ", clickbait filter evasion), 1 with a Devanagari headline. U+09F7 BENGALI CURRENCY NUMERATOR FOUR
   looks exactly like the danda but is a different code point, so the tokenizer splits sentences wrong. Examples:
   `fb97c8e54faa6ea5` "গ্রামে৷" at 176 (hex `E0 A7 B7`); `740b87d9773606f0` x27; `8d8e16b8a976243b` "উত্তর।৷" at 130.
2. **Medicine:** `re.sub("(?<=[ঀ-৿\s])৷", "।", t)`.
3. **Action:** fix.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** a real currency numerator in old-style money notation (I found none in the pack) becomes a danda.
   U+09F7 after a digit, Latin letter or । ("BDT৷", "উত্তর।৷") is not changed. That is why it fires on 11 of
   the 13 U+09F7 documents. Assamese ৰ inside Bengali words ("গ্ৰন্থ", "চাইৰে") is
   not fixed: ৰ→র is safe in "গ্ৰন্থ" but wrong in "চাইৰে" (a typo for চাইবে), so I leave those 3 to a human.

## Medicine 5: C5 keyword-stuffed lines

1. **Disease:** C5, 11 documents. Examples: `01d455bebba21ef1` "Tag: সূরা লাহাবের শানে নুজুল, সুরা লাহাব এর শানে নুযুল,
   …"; `e4aa2126d8505b14` a keyword list at the end; `a315585629ebfd19` a name-meaning SEO page.
2. **Medicine:** delete a line with 6 or more comma pieces, an average of 6 words or fewer per piece, and one two-word
   phrase in at least half of the pieces (`_stuffed` in the code).
3. **Action:** fix (delete the line).
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS. A first version (single shared word, 60 %) changed 16 / 314 = 5 % (FAIL). It hit
   lists of names ("মোঃ …, মোঃ …") and enumerations, so I tightened it.
5. **Side effects:** recall is low (1 of 11). Whole SEO pages and spec tables are not caught. Use M3 or a classifier
   for those.

## Medicine 6: F3 porn and gambling promotion (drop)

1. **Disease:** F3, 8 documents. Examples: `43804ba72410d8ff` and `f043584d6c27e3d7` porn-tube pages;
   `80d6bada82e5ff0b` bn.bettingonlinebd.net 888starz review; `95261ddc152835cc` betting promo with "Mostbet BD"
   injected into the middle of the word অনলাইন.
2. **Medicine:** drop if the text has at least 4 matches of
   `পর্ন|চোদা|ক্যাসিনো|বেটিং|বাজি ধর|জুয়া খেল|casino|betting|porn|xxx|sex video` **and** at least 1 match per 600
   characters.
3. **Action:** drop.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS. The density rule keeps news about casino raids: `ce8a91b51a89e51a` has 2 hits in
   2,641 chars and is kept.
5. **Side effects:** a long news feature about the casino crackdown with many mentions could be dropped. It does not
   catch spam appended in English to a clean article (`a041c47c2735d3f0`, cialis) or sexual-health product spam.
   Those are caught by M3 or not at all.

## Medicine 7: A3 legacy-font (Bijoy/ANSI) leftovers

1. **Disease:** A3, 7 documents. Text typed in the old Bijoy font and badly converted to Unicode. Examples:
   `874ac01ed8db4951` "দ্রæত" at 571 (æ for ু, hex `C3 A6`); `0cc55d56de34d944` "স¦াক্ষর" at 457 (¦ for ্ব, hex
   `C2 A6`); `4daaf2d1c7aea69f` "বøুপ" at 1232 (ø for ্ল); `71bb93238817a1c8` "সহÑসভাপতি" (Ñ for a dash).
2. **Medicine:** only when the character touches a Bengali letter: æ→ু, ø→্ল, ¦→্ব, Ñ→–, Í→-.
3. **Action:** fix.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** a real Latin-1 letter right next to Bengali text (a Danish or Spanish name with no space) would be
   changed. None in the pack. Other Bijoy damage (reph in the wrong place "র্ধষণ", "রির্পোটার") is not fixed.

## Medicine 8: C2 repeated lines

1. **Disease:** C2, 9 documents. Examples: `0ca0ac43cc9f2526` "Department of Textile Engineering" x3;
   `7bbe5a23532255c3` "— ANI (@ANI) July 8, 2023" x3; `bd59fdf51e29e37b` a question heading x5.
2. **Medicine:** keep the first two copies of a line longer than 8 characters and delete the third and later copies.
3. **Action:** fix.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 1 changed, 0 dropped of 314 (0.32 %). PASS.
5. **Side effects:** the one proxy change is `fb25628d14ed717a`, a poem whose refrain "পিতার আশীর্বাদ।" repeats 3
   times. The medicine cuts a real refrain. Song lyrics and poems are at risk.

## Medicine 9: A5 two-part vowel written in reverse order

1. **Disease:** A5, 7 documents. The vowel ো must be stored as ে + া (or U+09CB). These documents store া + ে, which
   NFC does not fix, so the same word exists in two byte forms. Examples: `1c748f4d41f5cb07` "ভালাে" x16 from 594 (hex
   `E0 A6 BE E0 A7 87`); `4c3a514616f31a33` "চৈাধুরী" (ৈ + া for ৌ) at 57; `bfb033a731f20dc9` "বিক্ষােভ" at 593.
2. **Medicine:** `t.replace("াে", "ো").replace("ৈা", "ৌ")`.
3. **Action:** fix.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** none found. The sequence া + ে has no correct use in Bengali.

## Medicine 10: C3 truncated tail

1. **Disease:** C3, 7 documents. Examples: `a03da238fe5d7dcd` ends "…সহযোগী সংগঠনের সভা"; `39feeae74731a5f8` ends
   "…অপহরন করে নিয়ে যায়" with no danda; `740b87d9773606f0` ends "…মিল রয়েছে, কখনও কখনও".
2. **Medicine:** if the text ends in a Bengali letter, the last line is longer than 60 characters, and the last 40
   characters contain no `: ঃ / - – —` (credit lines such as "সূত্র: বিবিসি" or "শিশির/এনাম/আকাশ"), cut the text after the
   last `। ? ! ৷`.
3. **Action:** fix (trim the broken sentence; keep the document).
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** a last sentence that is complete but has no danda is cut (all 3 labelled cases it fires on are real
   cuts, but the same shape could be complete). It misses "[…]" endings and lists that stop without "প্রমুখ". It also trims keyword lists at the end (`7b65bbecd0338588`, `e4aa2126d8505b14`),
   which is a useful side effect.

## Medicine 11: G1 detached virama

1. **Disease:** G1, 6 documents. Examples: `bb4a327ce2e54290` "সম ্প্রদায়" at 5977 (hex `20 E0 A7 8D`);
   `ce8a91b51a89e51a` "মু্িক্তযোদ্ধা" at 30; `f31201dc061fecbc` "\nিশক্ষা" at 265 (pre-base ি placed before the
   consonant, Bijoy conversion).
2. **Medicine:** remove a space between a consonant and a following virama + consonant:
   `re.sub("(?<=[ক-হ]) (?=্[ক-হ])", "", t)`.
3. **Action:** fix.
4. **Harm test:** official gold 0 / 238 (0 %), PASS. Proxy 0 / 314. PASS.
5. **Side effects:** low recall (2 of 6). Virama + vowel ("্ি") and ি moved before its consonant need reordering, not
   joining, and a wrong join makes it worse ("ধর্মের ্র" would become "ধর্মের্র"), so those cases stay for a human.

---

## The code (medicine.py)

Save the block as `medicine.py` (the `awk` line above does this) and run `python medicine.py <gold>` (needs `pyarrow`).
With the pack and `labels.csv` as the two arguments, it compares the medicines with the labels and uses the clean rows as
a proxy gold set.

```python
"""Medicines for ind-bn-fw2 and their harm test.

Each medicine takes (text, url) and returns the new text, or None to drop the document.

Usage:
    python medicine.py <gold>                      # harm test; <gold> is .parquet/.jsonl/.json/.csv or a folder of them
    python medicine.py <gold> --all-langs          # same, without keeping only Bengali rows
    python medicine.py <pack.parquet> <labels.csv> # hits vs. my labels; proxy gold = rows labelled clean
"""
import sys, re, csv, collections
from urllib.parse import urlparse
import pyarrow.parquet as pq

BN = "ঀ-৿"

# M1 C1 boilerplate: whole lines that are site furniture, only in the first 3 or last 6 lines.
C1_LINE = re.compile(
    r"^\s*(?:"
    r"(?:আরও|আরো) (?:পড়ুন|পড়তে পারেন)\s*[:ঃ]?.{0,80}|শেয়ার করুন\s*[:ঃ]?|মন্তব্য করুন|বিজ্ঞাপন|"
    r"(?:প্রতিনিধি )?প্রিন্ট সংস্করণ|সর্বশেষ|সর্বাধিক পঠিত|শীর্ষ সংবাদ\s*[:ঃ]?|সম্পর্কিত (?:নিউজ|খবর)|"
    r"সাবস্ক্রাইব করুন এবং সর্বশেষ খবর.*|আমাদের নিউজ চ্যানেল|.*ইউটিউব চ্যানেলে সাবস্ক্রাইব করুন|"
    r".*হোয়াটসঅ্যাপে ফলো করুন.*|এ বিভাগের সর্বাধিক পঠিত|বিস্তারিত (?:ভিডিওতে দেখুন|আরোও জানতে ক্লিক করুন)\s*[:ঃ]?|"
    r"View this post on Instagram|Read (?:More|Entire Article).{0,3}|Continue Reading.{0,3}|Highlights|"
    r"Powered by Froala Editor|For all the latest .* Click Here|[\d,]+ total views, \d+ views today|"
    r"- More Stories On :|\[hupso\]|#"
    r")\s*$", re.I)

def m_c1(t, url):
    lines = t.split("\n")
    n = len(lines)
    keep = [l for k, l in enumerate(lines) if not ((k < 3 or k >= n - 6) and C1_LINE.match(l))]
    return "\n".join(keep)

# M2 G2 lost ZWJ: reph-ya before aa at word start or after virama is the loanword form র‍্যা (র + ZWJ + ্ + য + া).
G2_RX = re.compile(f"(?:^|(?<=[^{BN}])|(?<=্))র্যা", re.M)

def m_g2(t, url):
    return G2_RX.sub("র‍্যা", t)

# M3 D4 machine-translated spam sites: bn.* subdomain of a non-Bengali site (topwar.ru, *.pt, insterne.com, ...)
BN_OK = {"bn.mtnews24.com", "bn.globalvoices.org", "bn.m.wikipedia.org", "bn.wikipedia.org", "bn.ekusherbangladesh.com.bd",
         "bn.jwtrubber.com", "bn.bettingonlinebd.net"}

def m_d4(t, url):
    host = urlparse(url).netloc.lower()
    if host.startswith("bn.") and host not in BN_OK:
        return None
    return t

# M4 A6 look-alike danda: U+09F7 (currency numerator four) after a Bengali char -> U+0964 danda.
def m_a6(t, url):
    return re.sub(f"(?<=[{BN}\\s])৷", "।", t)

# M5 C5 keyword-stuffed lines: >= 6 short comma pieces (<= 6 words) and one two-word phrase in >= 50% of them.
def _stuffed(line):
    parts = [p.strip() for p in re.split(r"[,،]", line) if p.strip()]
    if len(parts) < 6 or sum(len(p.split()) for p in parts) > 6 * len(parts):
        return False
    c = collections.Counter(b for p in parts for b in {" ".join(x) for x in zip(p.split(), p.split()[1:])})
    return bool(c) and c.most_common(1)[0][1] >= 0.5 * len(parts)

def m_c5(t, url):
    return "\n".join(l for l in t.split("\n") if not _stuffed(l))

# M6 F3 porn / gambling promotion: drop if >= 4 hits and >= 1 hit per 600 chars.
F3_RX = re.compile(r"পর্ন|চোদা|ক্যাসিনো|বেটিং|বাজি ধর|জুয়া খেল|casino|betting|porn|xxx|sex video", re.I)

def m_f3(t, url):
    n = len(F3_RX.findall(t))
    return None if n >= 4 and n * 600 >= len(t) else t

# M7 A3 legacy (Bijoy) font leftovers inside Bengali words.
A3_MAP = {"æ": "ু", "ø": "্ল", "¦": "্ব", "Ñ": "–", "Í": "-"}

def m_a3(t, url):
    return re.sub(f"(?<=[{BN}])[æø¦ÑÍ]|[æø¦ÑÍ](?=[{BN}])", lambda m: A3_MAP[m.group()], t)

# M8 C2 repeated lines: keep the first two copies of a line (len > 8) and remove the rest.
def m_c2(t, url):
    seen, out = collections.Counter(), []
    for l in t.split("\n"):
        k = l.strip()
        seen[k] += 1
        if len(k) > 8 and seen[k] > 2:
            continue
        out.append(l)
    return "\n".join(out)

# M9 A5 two-part vowel in reverse order: া+ে -> ো, ৈ+া -> ৌ.
def m_a5(t, url):
    return t.replace("াে", "ো").replace("ৈা", "ৌ")

# M10 C3 truncated tail: if the text ends in a Bengali letter, the last line is prose (> 60 chars, no ':' '/' '-'),
# cut back to the last sentence end.
END = "।?!৷"

def m_c3(t, url):
    s = t.rstrip()
    last = s.split("\n")[-1]
    if not s or not re.match(f"[{BN}]", s[-1]) or len(last) <= 60 or re.search(r"[:ঃ/\-–—]", last[-40:]):
        return t
    cut = max(s.rfind(c) for c in END)
    return s[:cut + 1] if cut > 0 else t

# M11 G1 detached virama: "সম ্প্রদায়" -> "সম্প্রদায়" (space between a consonant and a virama that starts a conjunct).
def m_g1(t, url):
    return re.sub("(?<=[ক-হ]) (?=্[ক-হ])", "", t)

MEDICINES = [("M1 C1", m_c1), ("M2 G2", m_g2), ("M3 D4", m_d4), ("M4 A6", m_a6), ("M5 C5", m_c5), ("M6 F3", m_f3),
             ("M7 A3", m_a3), ("M8 C2", m_c2), ("M9 A5", m_a5), ("M10 C3", m_c3), ("M11 G1", m_g1)]

def harm(docs):
    """Print the harm-test table as Markdown, ready to paste into medicine.md."""
    has_url = any(d.get("url") for d in docs)
    print("| Medicine | Gold docs | Changed | Dropped | Changed or dropped | Result |")
    print("|---|---|---|---|---|---|")
    failed = []
    for name, f in MEDICINES:
        if name.startswith("M3") and not has_url:
            print(f"| {name} | {len(docs)} | - | - | - | not tested: the gold set has no url column |")
            continue
        hit = []
        ch = dr = 0
        for d in docs:
            r = f(d["text"], d.get("url") or "")
            if r is None:
                dr += 1
            elif r != d["text"]:
                ch += 1
            else:
                continue
            hit.append(d.get("doc_id", "?"))
        pct = 100 * (ch + dr) / max(1, len(docs))
        ok = pct <= 1
        print(f"| {name} | {len(docs)} | {ch} | {dr} | {pct:.2f} % | {'PASS' if ok else 'FAIL'} |")
        if not ok:
            failed.append((name, hit))
    for name, hit in failed:
        print(f"\n{name} FAIL, gold docs hit ({len(hit)}): {', '.join(hit[:20])}")

def _rows(path):
    """Read a gold set: a .parquet/.jsonl/.json/.csv file, or a directory of them."""
    import os, json, glob
    if os.path.isdir(path):
        out = []
        for p in sorted(glob.glob(os.path.join(path, "**", "*"), recursive=True)):
            if p.endswith((".parquet", ".jsonl", ".json", ".csv")):
                out += _rows(p)
        return out
    if path.endswith(".parquet"):
        return pq.read_table(path).to_pylist()
    if path.endswith(".csv"):
        csv.field_size_limit(sys.maxsize)
        return list(csv.DictReader(open(path, encoding="utf-8")))
    with open(path, encoding="utf-8") as fh:
        if path.endswith(".jsonl"):
            return [json.loads(l) for l in fh if l.strip()]
        data = json.load(fh)
        return data if isinstance(data, list) else data.get("rows", data.get("data", []))

def load_gold(path, all_langs=False):
    """Normalise gold rows to {doc_id, text, url}; keep only Bengali rows when a language column exists."""
    import json
    docs = []
    for r in _rows(path):
        text = r.get("text") or r.get("content") or r.get("document")
        if not text:
            continue
        lang = str(r.get("lang_label") or r.get("lang") or r.get("language") or "")
        if lang and not all_langs and not re.search(r"ben|^bn\b|bengali|bangla", lang, re.I):
            continue
        url = r.get("url") or r.get("source_url") or ""
        if not url and r.get("meta"):
            try:
                url = json.loads(r["meta"]).get("url", "") if isinstance(r["meta"], str) else r["meta"].get("url", "")
            except (ValueError, AttributeError):
                url = ""
        docs.append({"doc_id": str(r.get("doc_id") or r.get("id") or "?"), "text": text, "url": url})
    return docs

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        docs = load_gold(args[0], "--all-langs" in sys.argv)
        if not docs:
            sys.exit("no Bengali rows with a text column found (use --all-langs to skip the language filter)")
        print(f"Harm test on {len(docs)} gold documents from {args[0]}\n")
        harm(docs)
        return
    docs = pq.read_table(args[0]).to_pylist()
    lab = {r["doc_id"]: r for r in csv.DictReader(open(args[1], encoding="utf-8"))}
    print("== hits on the whole pack vs. my labels (code in labels / medicine fires)")
    for name, f in MEDICINES:
        code = name.split()[1]
        fire = {d["doc_id"] for d in docs if f(d["text"], d["url"]) != d["text"]}
        have = {k for k, r in lab.items() if code in r["diseases"].split(";")}
        print(f"{name:8} fires={len(fire):3} labelled={len(have):3} both={len(fire & have):3} "
              f"fires-not-labelled={sorted(fire - have)[:4]}")
    gold = [d for d in docs if lab[d["doc_id"]]["verdict"] == "clean"]
    print(f"\n== harm test on proxy gold: {len(gold)} docs of this pack labelled clean")
    harm(gold)

if __name__ == "__main__":
    main()
```
