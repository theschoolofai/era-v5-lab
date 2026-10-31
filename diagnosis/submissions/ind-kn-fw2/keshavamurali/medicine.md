# Medicine sheet: ind-kn-fw2 (keshavamurali)

Pack: `ind-kn-fw2` (Kannada, 500 documents). Counts come from `labels.csv` (500 labelled rows).

**Gold set used for the harm test:** TBD

Until the two-reader gold set exists, the harm numbers below come from `teams/02-data-b/tools/harm_test_indic.py`
run on a stand-in: the 118 documents of this pack that are labelled `clean` in `labels.csv` (one reader).
1% of 118 is 1.18 documents, so a medicine passes only if it changes or drops at most 1 of them.

**How the code is laid out:**
- Each section's code runs on its own, as the harm tool runs it. Shared helpers are repeated in each section.
- Each rule takes the document text and returns the new text, or `True` to drop the document.
- The sections are in the order the medicines run: C2, C5, C1, G1. C5 runs before C1 because C1 removes the
  `N days ago` / `Read more` lines that C5 uses as signals.
- **Never removed:** a line with a ZWJ or ZWNJ, or with a compatibility character (`…`, `½`, full-width letters).
  The harm tool counts such a removal as damage.
- **Built for a larger corpus too:** C2, C5 and G1 look at one document at a time. C1's site templates are counted
  per website with an 8-byte hash per line (Medicine 3).
- `medicines.py` holds the same rule functions and runs them on a whole pack.

## Medicine 1

1. **Disease:** C2 (repeated lines), 28 documents.
   - `17e5d6b10dc06231` (row 111): the dateline and lead `ಕಲಬುರಗಿ,ಏ.5:ಈಶಾನ್ಯ ಕರ್ನಾಟಕದ ಪ್ರವಾಸೋದ್ಯಮದ ಅಭಿವೃದ್ಧಿಗೆ …` (188 characters) twice, as the title and again as the first line of the body
   - `76fdbcb28c49fc27` (row 51): `ಸುದ್ದಿದಿನ.ಕಾಂ|ವಾಟ್ಸಾಪ್|<phone>` four times (site contact line; number not copied)
   - `0bc105464a1dbdf3` (row 369): `ಫೋಟೋ: ಪೋಲಿನಾ ಇನೊಜೆಮ್ಟ್ಸೆವಾ, ಚಾಂಪಿಯನ್ಶಿಪ್` eight times
2. **Medicine:** if a line of **30 or more characters** appears **2 or more times** in one document, keep only its
   first copy.
   - Short lines are never touched, so repeated words, answers (`ಹೌದು`), dialogue tags and quiz options stay.
   - Documents that look like verse are skipped entirely: 6 or more lines, more than half of them short (under 60 characters) and without a sentence end. Refrains are the writing style there, and a refrain can be longer than 30 characters (`ಇವನಾರವ ಇವನಾರವ ಇವನಾರವನೆಂದೆನಿಸದಿರಯ್ಯಾ` is 40).
   ```python
   import unicodedata
   from collections import Counter

   ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
   END = re.compile(r'[.?!।॥"”\')]\s*$')   # a line that ends a sentence

   def _protected(line):
       return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

   def _short(l):
       return 0 < len(l) < 60 and not END.search(l)

   def _verse(t):
       ls = [l.strip() for l in t.split('\n') if l.strip()]
       return len(ls) >= 6 and sum(map(_short, ls)) / len(ls) > 0.5

   def medicine_c2(text, min_chars=30, times=2):
       if _verse(text):
           return text
       c = Counter(l.strip() for l in text.split('\n') if len(l.strip()) >= min_chars)
       rep = {l for l, n in c.items() if n >= times}
       seen, out = set(), []
       for l in text.split('\n'):
           s = l.strip()
           if s in rep and not _protected(s):
               if s in seen:
                   continue
               seen.add(s)
           out.append(l)
       return '\n'.join(out)
   ```
3. **Action:** fix the text.
4. **Harm test:** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
   - Changed 0 of 45 (0.00%). Dropped 0 of 45 (0.00%). **PASS**
   - ZWJ/ZWNJ audit: 0 changed documents with a different count. **PASS**
   - Normal-form audit: 0 changed documents left NFC or lost a compatibility character. **PASS**
5. **Side effects:**
   - Short repeated junk is not removed: `ಖರೀದಿಸಿ.` six times (row 369) and `ಚಿತ್ರಕೃಪೆ: rajkumar1220` five
     times (row 476). Medicine 3 catches such lines only when they repeat across a site's pages.
   - A long line that is repeated on purpose in prose, such as a quoted sentence or a question restated in an FAQ, loses its second copy.
   - Verse with long lines (6 or more lines that are mostly 60 characters or longer) is not seen as verse, so a long refrain there is thinned.
   - The 30-character limit counts code points, which suits Kannada (about 3 to 4 words). It is a parameter, to be set again for other scripts.

## Medicine 2

1. **Disease:** C5 (lists of keywords or links, teaser pages), 80 documents.
   - `dbbd14b33cfb0729` (row 37): `Display85`, `CPU43`, `GPU28` (spec widget and shop links)
   - `c472a3db00395ba6` (row 33): `ದಿನದ ಸುದ್ದಿ5 days ago` (related-headline teasers)
   - `bf21eb9f2a9511b6` (row 58): `Title`, `ಚಿತ್ರದುರ್ಗ | ನೀರಾವರಿ ಸಮಿತಿ ಅಧ್ಯಕ್ಷರ ಆಯ್ಕೆ ಪ್ರಕ್ರಿಯೆ ಸರಿಯಿಲ್ಲ : …` (headline list)
2. **Medicine:** short lines on their own are not a disease; poems, news highlights and credit blocks are short too.
   - **Block:** 3 or more consecutive short lines (under 60 characters, no sentence end), of which at least 2 carry a link or teaser signal: `N days ago`, `ಇನ್ನಷ್ಟು`, `Read more`, `Tag results`, a URL or `.com`, or `|`.
   - **Drop:** the whole document is dropped when more than 60% of its lines are short and at least 30% carry a signal.
   ```python
   import unicodedata

   ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
   END = re.compile(r'[.?!।॥"”\')]\s*$')   # a line that ends a sentence
   SIGNAL = re.compile(r'\d+\s*(days?|hours?|minutes?|mins?) ago|ಇನ್ನಷ್ಟು|Read more|Tag results'
                       r'|https?://|www\.|\.com\b|\|', re.I)

   def _protected(line):
       return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

   def _short(l):
       return 0 < len(l) < 60 and not END.search(l)

   def medicine_c5(text):
       lines = text.split('\n')
       idx = [i for i, l in enumerate(lines) if l.strip()]      # non-empty lines, original positions
       ls = [lines[i].strip() for i in idx]
       sig = [bool(SIGNAL.search(l)) for l in ls]
       if len(ls) >= 5 and sum(map(_short, ls)) / len(ls) > 0.6 and sum(sig) / len(ls) >= 0.3:
           return True
       drop, run = set(), []
       for k in range(len(ls) + 1):
           if k < len(ls) and (_short(ls[k]) or sig[k]):
               run.append(k)
           else:
               if len(run) >= 3 and sum(sig[j] for j in run) >= 2:
                   drop.update(idx[j] for j in run if not _protected(ls[j]))
               run = []
       return '\n'.join(l for i, l in enumerate(lines) if i not in drop)
   ```
3. **Action:** fix the text (remove the block); drop the document when it is mostly a list.
4. **Harm test:** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
   - Changed 0 of 45 (0.00%). Dropped 0 of 45 (0.00%). **PASS**
   - ZWJ/ZWNJ audit: 0 changed documents with a different count. **PASS**
   - Normal-form audit: 0 changed documents left NFC or lost a compatibility character. **PASS**
5. **Side effects:**
   - `|` is a signal, and Kannada verse uses `|` and `||` as line ends. Song lines in `634f9d4743893171` (row 31), such as `ಯಾರೇನೆಂದರು ನಿನಗೆ ಸದ್ಗುರು ದೇವ ||`, are removed with the headline block next to them.
   - A real list of links, for example a reference list at the end of an article, is removed.
   - Teaser lines that hold `…` stay, because of the never-removed rule (2 documents in this pack).
   - Most C5 pages without these signals are not caught.

## Medicine 3

1. **Disease:** C1 (boilerplate), 211 documents.
   - `5eaafa2efe204fb3` (row 8): `- Tag results for Subramanian Swamy`
   - `95fcd3a60a26a368` (row 19): `- Just In`, `- Don't Miss!`, `- News ಕರ್ನಾಟಕದಲ್ಲಿ 573 ಕೊರೊನಾ ಸೋಂಕಿತರು ಪತ್ತೆ`
   - `bfe4d0c9f43dc03b` (row 14): `‘ವಾರ್ತಾ ಭಾರತಿ’ ನಿಮಗೆ ಆಪ್ತವೇ ? …` and `ಬೆಂಬಲಿಸಲು ಇಲ್ಲಿ ಕ್ಲಿಕ್ ಮಾಡಿ` (the site's donation appeal, on all 7 of its pages)
2. **Medicine:** remove a line in any of these four cases:
   - (a) **site template:** the line is on 5 or more pages of the same website (host of the `url` column), and on
     at least 10% of that site's pages. A line that many different sites share, such as `ಧನ್ಯವಾದಗಳು` or a
     proverb, is never a template by this count.
   - (b) it matches a short list of boilerplate phrases;
   - (c) it starts with a dash or bullet followed by an English word. Tag pages, related-news links and ads use this format: `- Tag results for …`, `- Education …`, `- News …`;
   - (d) it is a bare dash followed by a `<category> N days ago` line, a teaser card.

   Finding the templates needs the URLs and the whole pack, but the harm tool passes the rule only the text. So the
   templates are found first (`python medicines.py <pack> --templates`), and the rule below carries the 15 template
   lines of this pack as 8-byte hashes. A hash also keeps the site's phone number out of this file. Examples of
   template lines: `Don't Miss!` (all 34 `kannada.filmibeat.com` pages), `Source link` (all 8 `savikannada.in`
   pages), `ಟಾಪ್ ನ್ಯೂಸ್` (11 of 25 `udayavani.com` pages). On a whole pack, `medicines.py` applies each site's own
   templates to that site only.
   ```python
   import hashlib
   import unicodedata

   ZWJ, ZWNJ = chr(0x200D), chr(0x200C)
   BOILER = re.compile(r'Share on WhatsApp|Copyright|©|Leave a Reply|Team Udayavani|ಟಾಪ್ ನ್ಯೂಸ್'
                       r'|\d+\s*(days?|hours?|minutes?) ago|Read more|ಇನ್ನಷ್ಟು (ಓದಿ|ಸುದ್ದಿ)', re.I)
   DASH_EN = re.compile(r'^[ \t]*[-–•][ \t]+[A-Za-z].*$', re.M)
   DASH_BARE = re.compile(r'^[ \t]*[-–•][ \t]*\n[^\n]*\d+\s*days? ago[^\n]*$', re.M)
   TEMPLATES = frozenset({          # site-template lines of ind-kn-fw2, found by medicines.py --templates
       '0c61b19cfb72c68a', '1523d8487cd4c792', '33f8a3e8d468bc8a', '4c304be013888589',
       '54181b210567e69b', '714f62bb0822152b', '86796ef8093339d7', '9236d07688fe64f6',
       '9c5d9390e0604341', 'b3f8b6881e5db8b7', 'bbce4efb0877577a', 'be298df70325f3f8',
       'cd54a6b665b3a745', 'e73bc5bae38473b3', 'ff2cc858983d961c',
   })

   def _protected(line):
       return ZWJ in line or ZWNJ in line or any(unicodedata.decomposition(c).startswith('<') for c in line)

   def _key(line):
       return hashlib.blake2b(line.encode('utf-8'), digest_size=8).hexdigest()

   def medicine_c1(text, templates=TEMPLATES):
       def cut(m):
           return m.group() if _protected(m.group()) else ''
       t = DASH_BARE.sub(cut, text)
       t = DASH_EN.sub(cut, t)

       def boiler(l):
           s = l.strip()
           return not _protected(s) and ((len(s) >= 3 and _key(s) in templates) or BOILER.search(s))
       return '\n'.join(l for l in t.split('\n') if not boiler(l))
   ```
3. **Action:** fix the text (remove the lines).
4.  **Harm test:** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
   - Changed 0 of 45 (0.00%). Dropped 0 of 45 (0.00%). **PASS**
   - ZWJ/ZWNJ audit: 0 changed documents with a different count. **PASS**
   - Normal-form audit: 0 changed documents left NFC or lost a compatibility character. **PASS**
5. **Side effects:**
   - A real Kannada bullet list that starts with an English word, such as `- WhatsApp ಮೂಲಕ…`, loses those lines.
   - A sentence that one site puts in many of its articles on purpose, such as a standard disclaimer, is removed.
   - Template lines on a site with fewer than 5 pages in the corpus are not found. A small pack finds less boilerplate than a large corpus.
   - Template lines that change from day to day, such as a "trending" headline box, can stay under the 10% share on a large site.
   - The hash list in this file belongs to this pack. For another pack or a larger corpus, find the templates again.
   - It catches only about half of the C1 documents. Menus and footers that are not repeated across a site's pages remain.

## Medicine 4

1. **Disease:** G1 (word cut at the vowel sign), 27 documents.
   - Only 2 documents in the pack have the exact pattern that this medicine fixes, so there are 2 examples:
     - `634f9d4743893171` (row 31): `ವಣ ್ಸುವಾಗ` (space before the virama)
     - `2914f93d5aa778b8` (row 253): `ವಸಡಿನ ೊಂದನ್ನು` (space before a vowel sign)
   - Most G1 damage in this pack is another kind:
     - a split between two full letters (`ಕರ್ನಾ ಟಕದ`, `e427affbdf302a39`, row 48);
     - legacy-font damage (`ಸಾಂಸ್ಕøತಿಕ`).
   - This regex cannot fix those.
2. **Medicine:** a Kannada dependent sign (vowel sign, virama, anusvara, visarga) can never start a word. Remove the
   space in front of it. Then normalise to NFC: a two-part vowel that was split (`ೆ` + space + `ೂ`) is not NFC once
   joined, and NFC composes it (`ೊ`).
   ```python
   import unicodedata

   G1 = re.compile(r'([\u0C80-\u0CFF]) ([\u0CBE-\u0CCD\u0CD5\u0CD6\u0C82\u0C83])')

   def medicine_g1(text):
       out = G1.sub(r'\1\2', text)
       return unicodedata.normalize('NFC', out) if out != text else text
   ```
3. **Action:** fix the text.
4. **Harm test:** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
   - Changed 0 of 45 (0.00%). Dropped 0 of 45 (0.00%). **PASS**
   - ZWJ/ZWNJ audit: 0 changed documents with a different count. **PASS**
   - Normal-form audit: 0 changed documents left NFC or lost a compatibility character. **PASS**
5. **Side effects:**
   - The join restores valid bytes but not lost letters. If a letter was dropped together with the space, the joined word is still wrong.
   - Text that shows a sign on its own on purpose, such as a grammar lesson that writes `ಾ`, is joined to the word before it.
   - A changed document is also normalised to NFC as a whole.

## All four in order

4. **Harm test:** gold set of 45 documents (ind-kn-fw2 45), medicine.md sha256 583a1eab3b18; rule: changed or dropped at most 1%.
   - Changed 0 of 45 (0.00%). Dropped 0 of 45 (0.00%). **PASS**
   - ZWJ/ZWNJ audit: 0 changed documents with a different count. **PASS**
   - Normal-form audit: 0 changed documents left NFC or lost a compatibility character. **PASS**



## Medicines rejected

- **A6 (wrong or mixed script), 31 documents. Fails.**
  - **Rule:** flag Latin or legacy-font letters joined to a Kannada letter. A single `s` that ends a Kannada word is allowed, because it is valid dialect: `ಒಂದs`, `ತಾನs` in `92305d5a724c194a` (row 73).
  - **Failure:** it still marks the gold document `41932ab38a6fafb6` (row 172), where `ka.gov.inಗೆ` is a URL with a normal Kannada case suffix.
  - Scripts cannot be fixed without a font map, so this is at most a flag, not a medicine.
- **C3 (truncated document), 14 documents. Left out.**
  - **Rule:** "the last line has no sentence end."
  - **Failure:** it changed 7 gold documents (5.9%), even after skipping credit lines (`ಚಿತ್ರ ಕೃಪೆ:`, `ವರದಿ:`). The cases:
    - a closing `,` (row 1);
    - an author name (row 462);
    - a narrator credit block (row 373);
    - a poem (row 9);
    - complete sentences with no full stop (rows 45, 144, 289).
  - A regex cannot tell these from a real cut. C3 is labelled by hand only.
- **G2 (lost ZWJ or ZWNJ), 270 documents. No medicine.**
  - The pack has no ZWNJ at all, so this is a pack-wide loss from upstream cleaning.
  - Restoring it needs a word list, so it is reported upstream instead.
- **D3, D4, D5 (92, 34, 7 documents). No medicine.**
  - D3 is labelled, not judged.
  - D4 and D5 need a reader or a model, not a regex.
- **F3 (harmful content), 9 documents.**
  - A keyword rule (`dating`, `ಡೇಟಿಂಗ್`, `HGH`, `sex stor…`) touched 0 gold documents, but it caught only 4 of the 9.
  - It is kept as a flag for review, not as an automatic drop.
