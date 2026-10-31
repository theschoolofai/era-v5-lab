# Medicine sheet: ind-sa-fw2 (swatibansal)

Pack ind-sa-fw2 (Sanskrit web text), 500 rows, all labelled in labels.csv: fix 298, clean 184, drop 18. Labels and medicines as of 27 Oct 2026.
Thirteen codes occur more than five times and get one medicine each (sections below, ordered by the reader's row count).
Harm test: run on the Sanskrit gold set of PR #161 (`teams/02-data-b/gold/ind-sa-fw2_gold.csv`, PR head commit 74b28869, an interim set): 68 documents that two readers marked clean. Tool: `teams/02-data-b/tools/harm_test_indic.py` from the same PR (`--rule all`, pack ind-sa-fw2.parquet), run on this file with the gold results written in (sha256 8435caae686d; only prose changed after that, so the tool's own hash of the committed file differs but the code and results are identical).
Result: every rule and the all-in-order run change 0 and drop 0 of the 68 gold documents (0.00 %); the ZWJ/ZWNJ audit and the normal-form audit (NFC, compatibility characters) find nothing. Overall result: PASS.
DISEASES.md fails a medicine that changes or drops more than 1 % of the gold set; the tool's limit for a set under 200 rows is 1 document, so on 68 documents two or more fails.
Earlier proxy, kept as a secondary check: this pack's 184 rows labelled clean, run through Data A's `harm_test.py` (limit 1 document): also 0 changed and 0 dropped for every rule. The gold set is a subset of these 184 rows, so the two agree by construction. Pack and recall counts come from my medicine_report.py, unrounded.
Action `none` means there is no safe per-document fix; the section still gives the detection rule in code and the scale-time action.
Pipeline order for the fixes: C1, then C2, then C5, then C3 (C3 last, because a chrome tail is what usually leaves a document open).
The C4 detector runs on the original text before C1, which removes the date headers it relies on.
A6, G1 and G4 are order-independent on this pack; F1 can run anywhere. The pipeline changes 183 of the 500 documents and drops none.
Each section's python block is self-contained and is the code that produced the numbers (checked identical to diag-tools on all 500 rows): fix rules are `medicine_<code>` or the section's one public function; for action `none` the entry point `medicine_<code>` returns the text unchanged and the named detector is the rule that reports.
The Hindi-dominance drop detector `d1_wrong_language` (med_language.py in diag-tools, not in this file) fires on 0 of the 68 gold documents (1 of 500 in the pack).
Example texts are at most 60 characters; `⏎` stands for a line break. F1 examples give type and offset only.

## Medicine 1 — C1 Boilerplate

1. **Disease:** C1, 149 rows in the pack. Examples (characters removed):
   - `935e30775b66fab4` offset 49467: `⏎***` (upasanayoga.org separator line)
   - `6da72db6a95c25b8` offset 0: `Menu⏎Home⏎E- Journal⏎Sanskrit Literature⏎Online Video Educat…` (newssanskrit menu block)
   - `76073b33992af5b6` offset 620: `⏎Did you see any mistake/variation in the content above? Cli…` (stotranidhi report line)
2. **Medicine:** remove MediaWiki edit links and any whole line or known header/footer block that equals a chrome string read in the pack. Covered: Blogger menu, post-date, nav and Posted-by/Labels lines; stotranidhi, dsbcproject and dasarpai header-footer lines; the sanskritdocuments.org .itx metadata, "Please send corrections to", "BACK TO" and credit lines (the address line is dropped, never logged); wikisource page-name, navigation and proofread-status lines; "Retrieved from", "Categories:", "Tags:", embedded-tweet attributions, `***` and dash-only separators; and host-specific chrome: the three newssanskrit marquee slogan lines, "-डा." byline and trailing section names, the thesimplehelp Latin-title-plus-Hindi-intro leading block, "Read Also:" and Hindi sign-off lines, the hindupad English intro block, the-spiritualtalks pipe-separated title line (only with its footer present) and footer lines, sa.wikipedia infobox rows (|label||value| and Latin |cell|) and image caption, and the sarkariexpress "click here" tail. Devanagari body lines are never edited. Function `medicine_c1` (the full code, including every chrome pattern):
   ```python
   DEVA = r"ऀ-ॿ꣠-ꣿ᳐-᳿"
   MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
   DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
   def _lf(text): return text.replace("\r\n", "\n")
   RE_EDITLINK = re.compile(r"\[(?:सम्पादन|संपादन|edit|सम्पादयतु|सम्पाद्यताम्)\]")
   RE_BLOGGER_TAIL = re.compile(r"\nat\n\d{1,2}:\d{2} [AP]M\nNewer Post\nOlder Post\nHome\s*$")
   RE_ARCHIVES_TAIL = re.compile(r"\n\s*Archives\n(?:[A-Z][a-z]+ \d{4}\n)*Categories\s*$")
   RE_DSBC_HEAD = re.compile(r"^Technical Details\n[A-Za-z]\n", re.M)
   RE_NEWS_MENU = re.compile(r"\AMenu\nHome\n(?:[^\n]*\n){0,40}?marquee\n")
   RE_NEWS_TAIL = re.compile(r"(?:\n[ \t]*(?:सम्प्रति वार्ताः|इति वार्ताः|विश्वतोमुखम्)[ \t]*)+\s*$")
   RE_SIMPLEHELP_HEAD = re.compile(rf"\A[A-Za-z][^\n]{{0,120}}: नमस्कार दोस्तों,[^\n]*\n(?:[^\n{DEVA}]*\n)*")
   RE_HINDUPAD_HEAD = re.compile(rf"\A[^\n]{{1,80}} in (?:Hindi|Sanskrit|English|Tamil|Telugu|Kannada|Malayalam), Lyrics of [^\n]*\n(?:[^\n{DEVA}]*\n)*")
   RE_SPIRITUAL_SIG = re.compile(r"^Subscribe on Youtube: The Spiritual Talks[ \t]*$", re.M)
   RE_SPIRITUAL_TITLE = re.compile(r"\A[^\n]*\|[^\n]*\|[^\n]*\|[^\n]*\n")
   C1_LINE_PATTERNS = [
       rf"{DAYS}, {MONTHS} \d{{1,2}}, \d{{4}}",
       r"Posted by .{0,80}", r"Labels?: .{0,200}", r"at \d{1,2}:\d{2} [AP]M", r"\d{1,2}:\d{2} [AP]M",
       r"Newer Posts?", r"Older Posts?", r"Post a Comment", r"No comments?:?", r"Email This", r"BlogThis!",
       r"Share to (?:Twitter|Facebook|Pinterest)", r"Subscribe to:.{0,40}", r"Powered by Blogger\.?",
       r"Did you see any mistake/variation in the content above\?.{0,200}",
       r"इतर .{0,60}(?:स्तोत्राणि|स्तोत्रं|स्तोत्रम्|नामावलयः|सूक्तानि|कवचानि) पश्यतु ।",
       r"% (?:Text title|File name|itxtitle|engtitle|Category|Location|Sublocation|Texttype|Author|Language|Subject|"
       r"Transliterated by|Proofread by|Translated by|Description-comments|Indexextra|Latest update|Send corrections to|"
       r"Site access|Description|Acknowledge-Permission|Source|Notes|Date|Comment)\s*:.*",
       r"(?:From [^\n]{0,100} )?(?:Encoded|Proofread|Transliterated|Encoded and proofread) by .{0,120}",
       r"[A-Za-z][\w.-]{0,40} at [\w.-]+\.[a-z]{2,6}",
       r"(?i:back to(?: top)?)", r"Please send corrections to.{0,200}", r"Technical Details",
       r"The rights of the materials herein are as indicated by the source\(s\) cited\..{0,400}",
       r"Subscribe to our newsletter.{0,200}",
       r"Inspiration: .{0,120}", r"These stories are written to .{0,300}",
       r"Jump to navigation ?Jump to search", r"Jump to navigation", r"Jump to search",
       r"एतत् पृष्ठम् (?:अपरिष्कृतम्|परिष्कृतम्|परिशोधितम्|प्रमाणीकृतम्) अस्ति",
       r"पृष्ठम्:[^\n]{1,120}\.(?:djvu|pdf)/[0-9०-९]{1,5}",
       r"Retrieved from .{0,300}", r".{0,300}इत्यस्मात् पुनः प्राप्तम्",
       r"Toggle limited content width",
       r"Table of Contents",
       r"[^\n]{0,80} Lyrics in (?:Marathi|Hindi|English|Tamil|Telugu|Kannada|Malayalam|Gujarati|Bengali|Oriya|Punjabi|Sanskrit):?",
       r"Categories: .{0,200}", r"Tags: .{0,200}",
       r"Leave a (?:Reply|Comment)",
       r"Download pdf", r"Back",
       r"Read Also", r"Read Also: .{0,200}",
       r"(?:हम )?उम्मीद करते हैं (?:कि |आपको ).{0,400}",
       r"\|[^|\n]{1,120}\|\|[^|\n]{0,200}\|",
       r"\|[A-Za-z0-9][^|\n]{0,120}\|",
       r"A painting by .{0,120}",
       r"Subscribe on Youtube: .{0,60}", r"Follow on Pinterest: .{0,60}", r"For any query contact on:?",
       r"Be a part of this Spiritual family .{0,160}", r"For more divine and soulful .{0,160}", r"For Spiritual quotes .{0,160}",
       r"यहाँ क्लिक करें", r"अगर आप और प्रैक्टिस सेट्स .{0,160}",
       r"[—–-]{2,}",
       r"Read [Mm]ore", r"Click here to .{0,80}",
       r"Download (?:the )?\S+ App\b.{0,80}",
       rf"— .{{1,80}} \(@\w{{1,30}}\) {MONTHS} \d{{1,2}}, \d{{4}}",
       r"\*{3,}",
       r"Share", r"Share this:?", r"Like this:?", r"Related", r"Archives", r"Categories",
       r"marquee", r"Statutary Warning-?",
       r"संस्कृतपठनेन बुद्धि[:ः] वर्धते इति मतिमुन्नीय गवेषका[:ः]॥",
       r"व्यावहारिकप्रयोगैः संस्कृतं राष्ट्रियभाषा भवितव्या - डॉ\. बलदेवानन्दसागरः।",
       r"संस्कृतेन सर्वदा व्यवहर्तुं प्रयतत - जगद्गुरु भारतीतीर्थस्वामिनः",
       rf"-\s?डा\.\s?[{DEVA}][^\n]{{0,30}}",
   ]
   RE_C1_LINE = re.compile(r"[ \t]*(?:" + "|".join(f"(?:{p})" for p in C1_LINE_PATTERNS) + r")[ \t]*")
   def medicine_c1(text):
       """C1: remove site chrome — known header/footer blocks, MediaWiki edit links, and whole lines equal to a chrome string."""
       if not text: return text
       src = _lf(text)
       out = RE_NEWS_MENU.sub("", src)
       out = RE_DSBC_HEAD.sub("", out)
       out = RE_SIMPLEHELP_HEAD.sub("", out)
       out = RE_HINDUPAD_HEAD.sub("", out)
       if RE_SPIRITUAL_SIG.search(out): out = RE_SPIRITUAL_TITLE.sub("", out)
       out = RE_BLOGGER_TAIL.sub("", out)
       out = RE_ARCHIVES_TAIL.sub("", out)
       out = RE_NEWS_TAIL.sub("", out)
       if RE_EDITLINK.search(out):
           out = "\n".join(RE_EDITLINK.sub("", l) for l in out.split("\n") if RE_EDITLINK.sub("", l).strip() or not RE_EDITLINK.search(l))
       out = "\n".join(l for l in out.split("\n") if not RE_C1_LINE.fullmatch(l))
       if out == src: return text
       return out.strip("\n")
   ```
3. **Action:** fix. The matched lines and blocks are removed; nothing else changes.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 98 of the 149 rows labelled C1; 109 rows touched in the pack overall.
5. **Side effects:** a Sanskrit article about Blogger whose prose puts exactly these phrases on their own lines loses them, and the newssanskrit slogans would be lost if they were ever quoted on their own line in a news item. Chrome that is kept: Latin title lines (templesinindiainfo, advocatetanmoy, thesimplehelp section headings), Devanagari single-cell |…| infobox rows (same shape as the wikisource prev/next navigation row on seven clean rows), "Available at" and "Source:" reference lines, and author contact lines such as "E-mail id:", which are personal data (F1) and are left to the F1 medicine. Out of C1's scope, so still in the text: the learnsanskrit trilingual exercise rows (272; cutting the Hindi and English parts is an intra-line edit, not a line rule), the sanskritvarta embedded tweet bodies (37, 38, 114; only the attribution line is chrome), and the dr.du.ac.in alternating Sanskrit and English paragraphs (101; D3, label only). Nothing fuzzier than a full-line match is used, which is why 51 of the C1 rows are not touched; the 11 touched rows without a C1 label are mostly hosts whose chrome the reader filed under other codes.

## Medicine 2 — D3 Mixed language

1. **Disease:** D3, 91 rows in the pack. Examples (rows the detector fires on; what is there):
   - `adebf77350ddfac0` (ambuda.org): transliteration-scheme names ITRANS, OPTITRANS, "visarga", "Help" inside Devanagari lines; Latin share 47 %.
   - `aa8e369c2d562c48` (whatsappweb.fun): English phrases "wish", "to", "my", "wife" repeated eight times each between Sanskrit lines.
   - `5655024b4a855621` (sa.wikipedia.org): English glosses "Powder", "Flour", "Horse", "Gram" inside a Sanskrit list.
2. **Medicine:** detection only. At least three Latin-script words standing inside Devanagari sentences (Devanagari within 25 characters on both sides on the same line; the window never crosses a line break), ignoring all-caps acronyms in parentheses such as (CPEC) and Latin-only header, footer or mid-body lines, while Latin words stay below half of all words. Ten or more such in-sentence words waive the share clause (word-by-word gloss pages). Detector `d3_mixed_language`; `medicine_d3` returns the text unchanged:
   ```python
   D3_MIN_IN_SENTENCE = 3
   D3_MAX_LATIN_SHARE = 0.5
   D3_DENSE_IN_SENTENCE = 10
   D3_CONTEXT = 25
   RE_DEVA_WORD = re.compile(
       r"[ऄ-हऽॐक़-ॡॲ-ॿ]"
       r"[ऀ-ॣॱ-ॿ‌‍]*"
       r"(?::(?![0-9A-Za-zऀ-ॿ]))?")
   RE_LATIN_WORD = re.compile(r"[A-Za-zÀ-ɏḀ-ỿ]+")
   RE_DEVA_CHAR = re.compile(r"[ऀ-ॿ]")
   RE_PAREN_ACRONYM = re.compile(r"\([A-Z]{2,8}\)")
   def deva_words(text):
       """Devanagari words of `text` (see RE_DEVA_WORD); danda, digits and punctuation split, ZWJ/ZWNJ stay inside a word."""
       return RE_DEVA_WORD.findall(text)
   def latin_in_sentences(text):
       """Latin-script words that sit inside a Devanagari sentence: Devanagari within D3_CONTEXT chars on both sides on the
       same line (adapted from prescreen.py's in_sentence rule; here the context window is cut at the nearest line break
       so it can never reach a neighbouring line). Latin-only lines — header, footer or mid-body chrome — therefore never
       qualify, however short. All-caps acronyms in parentheses such as (CPEC) are removed first. Single letters are
       ignored (list markers, variables)."""
       t = RE_PAREN_ACRONYM.sub(lambda m: " " * len(m.group()), text)
       hits = []
       for m in RE_LATIN_WORD.finditer(t):
           if len(m.group()) < 2:
               continue
           before = t[max(0, m.start() - D3_CONTEXT):m.start()].rsplit("\n", 1)[-1]
           after = t[m.end():m.end() + D3_CONTEXT].split("\n", 1)[0]
           if RE_DEVA_CHAR.search(before) and RE_DEVA_CHAR.search(after):
               hits.append(m.group())
       return hits
   def latin_share(text):
       """Latin words / (Latin words + Devanagari words); 0.0 when there are no words."""
       latin = len(RE_LATIN_WORD.findall(text)); deva = len(deva_words(text))
       return latin / (latin + deva) if latin + deva else 0.0
   def d3_mixed_language(text):
       """D3 detector: at least D3_MIN_IN_SENTENCE Latin words inside Devanagari sentences and Latin share below
       D3_MAX_LATIN_SHARE; the share clause is waived when at least D3_DENSE_IN_SENTENCE Latin words sit inside
       Devanagari sentences (word-by-word gloss pages). Detection only; the action is `none`."""
       n = len(latin_in_sentences(text))
       if n >= D3_DENSE_IN_SENTENCE:
           return True
       if latin_share(text) >= D3_MAX_LATIN_SHARE:
           return False
       return n >= D3_MIN_IN_SENTENCE

   def medicine_d3(text):
       return text    # action none: the detector `d3_mixed_language` reports; the text is kept
   ```
3. **Action:** none. DISEASES.md says to label mixed language and not judge it. The scale-time action is keep-and-record: the detector's flag goes into the row's metadata, and the only text edit that is safe, removing Latin-only chrome lines, is already done by C1.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %): pass; the detector fires on 0 of 68 gold documents. No automated action. Proxy: detector fires on 1/184 clean rows (information only; pack row 457, sanskritvarta.in, the English words "Land for Job" in a news sentence). Recall: fires on 22 of the 91 rows labelled D3; 31 rows detected in the pack overall.
5. **Side effects:** none on the text. Two natural cases in this pack must stay as they are. sanskrit.today verse pages print the verse, its sandhi split, a word-by-word gloss (धीमताम् = of the wise) and an English meaning. sa.wikisource talk pages carry English wiki notices and user names between Sanskrit paragraphs. Both are legitimate bilingual data. The detector also fires on Sanskrit news that names people, places or hashtags in Latin script and on glossaries. That is why the result is reported, not acted on. A text rewrite (stripping the Latin words) would destroy glosses and names. The 91 include 17 rows with a Hindi introduction, gloss or commentary beside a dominant Sanskrit text; they carry little Latin, so the detector fires on 4 of them. The exported Hindi-dominance detector `d1_wrong_language` drops only the one Hindi-language menu page in this pack (row 66, sa.wikipedia.org, labelled drop) and none of the 184 clean rows; it is kept for the gold run.

## Medicine 3 — C3 Truncated document

1. **Disease:** C3, 81 rows in the pack. Examples (dangling last line removed):
   - `70ca517813a00c74` offset 6744: `⏎श्रीः` (sarit.indology.info, lone invocation after the closing ॥)
   - `85b9f023199490ad` offset 4827: `⏎श्रीः` (sarit.indology.info, same ending)
   - `14ee406c9fcc5df9` offset 957: `⏎प्रविष्टां संख्यां एकेन वर्धयित्वा न्यूनीकरोतु,` (oratlas.com, line ends in a comma)
2. **Medicine:** the last non-empty line is dropped when four conditions hold. It has no terminal punctuation (। ॥ . ! ? closing quote or bracket, or a digit). It is shorter than 200 characters and at most eight words. It is not a colophon (starts with इति or इत्य). The line before it ends with terminal punctuation. Never more than one line. A longer open last line is real truncation and is left alone. Function `medicine_c3`:
   ```python
   def _lf(text): return text.replace("\r\n", "\n")
   TERMINAL = set("।॥.!?\"”'’)]}»…") | set("0123456789०१२३४५६७८९")
   C3_MAX_LEN, C3_MAX_WORDS = 200, 8
   RE_C3_PROTECT = re.compile(r"^इत(?:ि|्य)")
   def medicine_c3(text):
       """C3: drop one dangling short last line without terminal punctuation when the line before it is closed."""
       if not text: return text
       src = _lf(text)
       lines = src.split("\n")
       idx = [i for i, l in enumerate(lines) if l.strip()]
       if len(idx) < 2: return text
       k, j = idx[-1], idx[-2]
       last, prev = lines[k].strip(), lines[j].strip()
       if (len(last) >= C3_MAX_LEN or len(last.split()) > C3_MAX_WORDS or last[-1] in TERMINAL or prev[-1] not in TERMINAL
               or RE_C3_PROTECT.match(last)):
           return text
       return "\n".join(lines[:k] + lines[k + 1:])
   ```
3. **Action:** fix. One dangling last line is removed; mid-sentence truncation is not repaired.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 31 of the 81 rows labelled C3; 38 rows touched in the pack overall.
5. **Side effects:** a document whose last line is a title or an unpunctuated verse-number line loses it. Real mid-sentence truncation (most wikisource rows) is not repaired, so most C3 rows keep their damage. The lone sarit invocation श्रीः after the closing ॥ is cut: by the reader's policy all 16 sarit rows that end that way are C3 (24, 25, 50, 72, 73, 92, 131, 135, 402, 422, 427, 435, 439, 478, 493, 496), and they are 16 of the 31 rows repaired. A श्रीः closed by its own danda is terminal and stays. Of the 7 touched rows without a C3 label, six are C1 rows whose open last line is a chrome tail (C1 removes most of them first in the pipeline), and one is row 109 (sarkariexpress, D3), whose Hindi "click here" tail C1 also removes first. Interaction: on advocatetanmoy rows 305 and 323, C1 removes a "Categories:" line and C3 then drops the Latin title line above it.

## Medicine 4 — G4 Over-normalised

1. **Disease:** G4, 70 rows in the pack. Examples (ASCII digits rewritten as Devanagari):
   - `2d181da484a0d781` offset 8: `अध्यायः 064` becomes `अध्यायः ०६४` (sarit.indology.info)
   - `61cdf0be9f009325` offset 8: `अध्यायः 066` becomes `अध्यायः ०६६` (sarit.indology.info)
   - `70ca517813a00c74` offset 8: `अध्यायः 030` becomes `अध्यायः ०३०` (sarit.indology.info)
2. **Medicine:** an ASCII digit run (digits, with . or , inside allowed) is rewritten with Devanagari digits ०-९ when a Devanagari letter sits within 10 characters on both sides and no Latin letter within 10 characters on either side. The document must have at least three such runs. It need not contain a Devanagari digit already: sarit ASCII verse numbers are G4 by the reader's policy. Runs joined by : / or - (times, dates, hyphenated references), runs near Latin letters or URLs, and runs with a month name, a currency word (रूप्यक, रुपय, ₹, करोड, लाख, डॉलर), a percent sign or दिनाङ्क/दिनांक within 12 characters (dates and amounts in news prose) stay ASCII; a guarded run does not count towards the three-run gate. Function `fix_g4_all_ascii`, entry point `medicine_g4`; the stricter `fix_g4_mixed_only` (only documents that already have a Devanagari digit) is exported for comparison:
   ```python
   RE_G4_RUN = re.compile(r"[0-9]+(?:[.,:/\-][0-9]+)*")
   DEVA_CTX = r"\u0904-\u0939\u0958-\u0961\u0972-\u097F"   # Devanagari letters only
   RE_DEVA_CTX = re.compile(rf"[{DEVA_CTX}]")
   RE_LATIN = re.compile(r"[A-Za-z]"); RE_DEVA_DIGIT = re.compile(r"[०-९]")
   TO_DEVA_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९"); CTX = 10; MIN_RUNS = 3
   # news-prose guard: month names (Hindi/Sanskrit/Marathi stems), currency words, %, दिनाङ्क within NEWS_CTX chars
   NEWS_WORDS = (r"जनवर|फरवर|फेब्रु|मार्च|अप्रैल|एप्रिल|मई|जून|जुलाई|जुलै|अगस्त|आगस्ट|सितम्बर|सितंबर|सप्टेम्बर|सेप्टेम्बर|"
                 r"अक्टूबर|अक्तूबर|ऑक्टोबर|नवम्बर|नवंबर|नोव्हेम्बर|दिसम्बर|दिसंबर|डिसेम्बर|"
                 r"रूप्यक|रुपय|रूपय|रु\.|₹|करोड|लाख|डॉलर|डालर|%|दिनाङ्क|दिनांक")
   RE_G4_NEWS = re.compile(NEWS_WORDS); NEWS_CTX = 12

   def _g4_convert_run(m):
       run = m.group()
       if ":" in run or "/" in run or "-" in run: return run
       s = m.string; left = s[max(0, m.start() - CTX):m.start()]; right = s[m.end():m.end() + CTX]
       if not (RE_DEVA_CTX.search(left) and RE_DEVA_CTX.search(right)): return run
       if RE_LATIN.search(left) or RE_LATIN.search(right): return run
       nleft = s[max(0, m.start() - NEWS_CTX):m.start()]; nright = s[m.end():m.end() + NEWS_CTX]
       if RE_G4_NEWS.search(nleft) or RE_G4_NEWS.search(nright): return run   # date or amount in news prose
       return run.translate(TO_DEVA_DIGITS)

   def fix_g4_all_ascii(text):            # the G4 medicine
       convertible = sum(1 for m in RE_G4_RUN.finditer(text) if _g4_convert_run(m) != m.group())
       if convertible < MIN_RUNS: return text
       return RE_G4_RUN.sub(_g4_convert_run, text)

   def fix_g4_mixed_only(text):           # exported variant, not in MEDICINES
       if not RE_DEVA_DIGIT.search(text): return text
       return fix_g4_all_ascii(text)

   def medicine_g4(text):                 # the G4 medicine = fix_g4_all_ascii
       return fix_g4_all_ascii(text)
   ```
3. **Action:** fix. Every document with three or more convertible runs is rewritten, whether or not it already mixes the two digit systems.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 55 of the 70 rows labelled G4; 56 rows touched in the pack overall (the 55 and row 235, sa.m.wikisource, labelled D3;H3). The exported mixed-only variant touches 9 of 70 G4 rows and 0 clean rows.
5. **Side effects:** digits next to a month name, a currency word, a percent sign or दिनाङ्क stay ASCII. That keeps the medicine off clean row 8 (`5448b7f64d6a2e8f`, newssanskrit.blogspot.com: three ASCII dates and an amount in Devanagari prose). It also leaves the two year runs on one essay unconverted: on G4 row 334 (`cc0e23e9c96354ae`, thesimplehelp.com) the date `4 जुलाई 1902` is guarded, so only `1863 तमे` and `1893 तमे` remain convertible, below the three-run gate. A date run inside an otherwise converted document (`30 दिनांके` in row 429) stays ASCII. Alternatives measured and not applied: skipping four-digit years 1800-2099 not next to ॥ touches clean row 8 (53/70); requiring ॥ । or a line boundary within 3 characters reaches 0 clean rows but only 47/70. The 15 G4 rows the medicine misses (11 sarit, 2 sa.m.wikisource, row 334, and row 471 `36f68c1b4189e521` with two dotted references) have fewer than three convertible runs: their numbers are hyphenated references (9-66-66), sit next to Latin letters, are guarded, or are too few. Hyphenated verse references stay ASCII, so a converted document can still mix systems. A document with only one or two stray ASCII numbers (।। 57 ।। in a 200-digit Devanagari text) is left alone because the same rule without the three-run gate touches 17 of the 184 clean rows (one or two converted runs each). Footnote numbers glued inside words (पूर्वोत्त772र) are converted like any other run, which neither repairs nor worsens them.

## Medicine 5 — G2 Lost ZWJ or ZWNJ

1. **Disease:** G2, 51 rows in the pack. Examples (word that carried ZWJ in the crawl-date source, from source_compare.py):
   - `2d33ec2d9fc4e9db` (sanskritvarta.in): `उल्लेखनीयम्` at offset 708; source has 3 ZWJ, pack text has none.
   - `a54696edce4482b2` (sanskritvarta.in): `इस्लामाबाद` at offset 0 and `स्थितम्` at offset 265; source has 12 ZWJ.
   - `55d085f09d929665` (sanskritvarta.in): `राष्ट्रपति` at offset 28; source has 1 ZWJ.
2. **Medicine:** detection needs the crawl-date source. source_compare.py fetches the page, counts U+200C/U+200D there and in the pack text, and flags the document when the page has them and the pack has none. 50 rows were confirmed that way, mostly sanskritvarta.in and newssanskrit.blogspot.com. The pack itself contains zero ZWJ/ZWNJ (asserted in test_med_script.py), so no in-text rule can find the disease. Function `detect_g2`:
   ```python
   def detect_g2(text):
       """Always False: G2 cannot be detected from the text alone. The pack contains zero U+200C/U+200D,
       so there is no in-text signal; detection is source_compare.py's comparison with the crawl-date page."""
       return False
   def medicine_g2(text):
       return text    # action none: no in-text signal; detection is source_compare.py
   # source_compare.py, in words: zw_source = count(U+200C, U+200D) in fetched page text;
   # zw_pack = same count in the pack text; flag G2 when zw_source > 0 and zw_pack == 0,
   # evidence = the source words that carried the joiner, located in the pack text by offset.
   ```
3. **Action:** none. Scale-time action: re-crawl these hosts with a fetcher that keeps format characters. Never insert joiners heuristically: the glyph a ZWJ/ZWNJ selects depends on the font and the conjunct, and a wrong guess changes how the word renders.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %): pass; the detector fires on 0 of 68 gold documents. No automated action. Proxy: detector fires on 0/184 clean rows (information only, by construction). Recall: touches 0 of the 51 rows labelled G2; 0 rows detected in the pack overall. The real detection count is source_compare.py's 50 confirmed rows.
5. **Side effects:** none at text level. Nothing is changed, so the pack count here is 0 by construction. A re-crawl can only restore joiners that the live page still has; the reader accepted all 50 candidates as G2 by policy (ZWJ after virama changes glyph shape only, but it is the source's spelling).

## Medicine 6 — A6 Wrong or mixed script

1. **Disease:** A6, 34 rows in the pack. Examples (Latin look-alike replaced):
   - `cfd726ed027be926` offset 150: `‘सोSहम्’` becomes `‘सोऽहम्’` (sahityapedia.com)
   - `a5c8f34aa49a0681` offset 51: `सुविधायतेI⏎` becomes `सुविधायते।⏎` (newssanskrit.blogspot.com)
   - `94138fa4fcc9e3ac` offset 480: `सन्दर्भेsस्मिन्` becomes `सन्दर्भेऽस्मिन्` (srimukha.srisamsthana.org)
2. **Medicine:** a Latin capital I or small l (one or two) becomes a danda । (two become ॥). It must stand right after a Devanagari letter or sign and before a space, tab, no-break space, newline, danda or the end of text. A Latin S or s becomes avagraha ऽ in one position only. A Devanagari e/o vowel (े ो ए ओ and the short ॆ ॊ ऎ ऒ) must be on its left and a Devanagari letter on its right. Function `fix_a6`:
   ```python
   # character classes use \u escapes on purpose: a literal nukta letter is stored decomposed and would break the range
   DEVA_LETTER = r"\u0904-\u0939\u093D\u0950\u0958-\u0961\u0972-\u097F"    # letters incl. avagraha and OM
   DEVA_MARK = r"\u0900-\u0903\u093A-\u093C\u093E-\u094F\u0951-\u0957\u0962\u0963"    # matras, virama, nukta, bindus, visarga, accents
   BOUNDARY = r"[ \t\u00A0\r\n।॥]"    # space, tab, nbsp, newline, danda
   E_O_VOWELS = r"\u0946\u0947\u094A\u094B\u090E\u090F\u0912\u0913"    # matras ॆ े ॊ ो and letters ऎ ए ऒ ओ
   RE_A6_DANDA = re.compile(rf"(?<=[{DEVA_LETTER}{DEVA_MARK}])(I{{1,2}}|l{{1,2}})(?={BOUNDARY}|$)")
   RE_A6_AVAGRAHA = re.compile(rf"(?<=[{E_O_VOWELS}])[Ss](?=[{DEVA_LETTER}])")

   def fix_a6(text):
       text = RE_A6_DANDA.sub(lambda m: "॥" if len(m.group(1)) == 2 else "।", text)
       return RE_A6_AVAGRAHA.sub("ऽ", text)
   ```
3. **Action:** fix. Each replacement needs Devanagari on the left and a boundary or Devanagari letter on the right; no neighbouring character is consumed.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 18 of the 34 rows labelled A6; 18 rows touched in the pack overall.
5. **Side effects:** two rules the plan suggested are measured and not applied. ASCII ':' standing for visarga (colon right after a Devanagari letter, before a boundary, in a document that also has ः) occurs in 21 clean rows; the reader does not call it A6. ASCII '|' or '||' standing for a danda after a Devanagari word occurs in 7 clean rows. Left as they are: Latin o as a variant-reading mark (sarit झo पाठः), OCR letters inside words (मूfत), whole Latin words glued to Devanagari (Navashaktiनामिकाम्), and quotations in other Indic scripts, which are D3 not A6. A Sanskrit text that uses a Latin l as a list marker directly after a Devanagari word would gain a danda.

## Medicine 7 — H3 The same content in another source or language

1. **Disease:** H3, 34 rows in the pack: 24 cross-site copies with three or more shared 40-character windows (both sides labelled), 8 pages from the translated-source hosts ebible.org and gitasupersite.iitk.ac.in, and 2 sa.wikipedia pages the reader judged translations of their English counterpart (rows 227, 233). Examples:
   - `66a9c2d6e2a78709` (advocatetanmoy.com) and `64e263170df29e32` (vedas site, punycode host): Rudra adhyāya of the Śukla Yajurveda; the second shares 12 windows with a sa.wikisource copy as well.
   - `b1bb7f2f7db80183` (anantjivan.com) and `b41dc0d17e090cdd` (dnaofhinduism.com): Devī Māhātmya, Śakrādaya stuti; 203 shared windows.
   - `18f91690f821fc5c` (ebible.org): Bible book with every verse line numbered `Ⅰ Ⅱ Ⅲ …`; the same content exists in English and other languages.
2. **Medicine:** detection proper is h3_check.py: cross-host 40-character windows inside the pack (three or more shared windows make a copy; one or two are a quotation, not H3), a list of known translated-source hosts (ebible.org, gitasupersite.iitk.ac.in), and Wikipedia langlinks for sa.wikipedia pages (H3 only when the reader judges the page a translation). Per document, the fn can only recognise the house style of the two translated sources: five or more lines numbered with Unicode Roman numerals (ebible.org), or two ।।8.4।।-style references or three ।।heading।। lines (gitasupersite.iitk.ac.in). Function `detect_h3`:
   ```python
   RE_ROMAN_VERSE_LINE = re.compile(r"^[Ⅰ-ⅿ]+ \S", re.M)                        # ebible.org: "Ⅰ यावन्तः …"
   RE_GITA_REF = re.compile(r"।।[0-9]{1,2}(?:\.[0-9]{1,3}){1,2}।।")               # gitasupersite: ।।8.4।।
   RE_GITA_HEADING_LINE = re.compile(r"^।।[^।\n0-9०-९]{1,60}।।[ \t\r]*$", re.M)  # ।।ब्रह्मसूत्रभाष्यम्।।
   MIN_VERSE_LINES = 5; MIN_GITA_REFS = 2; MIN_GITA_HEADINGS = 3

   def detect_h3(text):
       if not text: return False
       if len(RE_ROMAN_VERSE_LINE.findall(text)) >= MIN_VERSE_LINES: return True
       if len(RE_GITA_REF.findall(text)) >= MIN_GITA_REFS: return True
       if len(RE_GITA_HEADING_LINE.findall(text)) >= MIN_GITA_HEADINGS: return True
       return False
   def medicine_h3(text):
       return text    # action none: the detector `detect_h3` reports; dedupe is a corpus-time action
   ```
3. **Action:** none. Scale-time action: corpus-level dedupe that keeps one copy per text, preferring the copy with the fewest other diseases; for translated canon (Bible, Gītā, Brahmasūtra), keep the Sanskrit side and record that parallel versions exist. A per-document drop would remove good Sanskrit.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %): pass; the detector fires on 0 of 68 gold documents. No automated action. Proxy: detector fires on 0/184 clean rows (information only). Recall: fires on 9 of the 34 rows labelled H3; 9 rows detected in the pack overall, all from ebible.org (6) or gitasupersite.iitk.ac.in (3), and all 9 carry the H3 label.
5. **Side effects:** misses every cross-site copy and every translation that does not use these two layouts, so the 24 copies and the 2 Wikipedia translations among the 34 H3 rows are invisible per document. Fires on any Bible or Gītā-site page whatever its text quality. Any Sanskrit text that numbers verses with Roman numerals or wraps references in ।।…।। would be flagged as well. The detector sees the layout, not the host, so a copy of an ebible page on another site is flagged too.

## Medicine 8 — C5 Lists of keywords or links

1. **Disease:** C5, 21 rows in the pack. Examples (line removed):
   - `6da72db6a95c25b8` offset 319: `⏎https://twitter.com/samprativartah` (newssanskrit.blogspot.com, bare URL line)
   - `cf161644b0475f04` offset 319: `⏎https://twitter.com/samprativartah` (same host)
   - `ce0f08033f2453d9` offset 313: `⏎https://twitter.com/samprativartah` (same host)
2. **Medicine:** remove lines that are "Tags:", "Labels:" or "Categories" lines, lines that are only a URL, and lines made of six or more comma- or pipe-separated short tokens with no sentence punctuation. If more than half of the non-empty lines match, the document is returned unchanged. Function `medicine_c5`:
   ```python
   def _lf(text): return text.replace("\r\n", "\n")
   RE_C5_TAGLINE = re.compile(r"\s*(?:Tags?|Labels?|Categories|Category|Filed under|Keywords?|Topics?)\s*:.*|\s*(?:Tags|Categories)\s*")
   RE_C5_URL_LINE = re.compile(r"\s*(?:https?://|www\.)\S+\s*")
   RE_C5_SEP = re.compile(r"\s*[,|]\s*")
   RE_C5_SENTENCE = re.compile(r"[।॥.!?]")
   C5_MIN_TOKENS, C5_MAX_TOKEN_CHARS, C5_MAX_TOKEN_WORDS = 6, 30, 3
   def _is_list_line(s):
       """A comma- or pipe-separated run of >= 6 short tokens with no sentence punctuation."""
       if not s or RE_C5_SENTENCE.search(s): return False
       toks = [t for t in RE_C5_SEP.split(s) if t]
       return len(toks) >= C5_MIN_TOKENS and all(len(t) <= C5_MAX_TOKEN_CHARS and len(t.split()) <= C5_MAX_TOKEN_WORDS for t in toks)
   def medicine_c5(text):
       """C5: remove tag/label lines, bare URL lines and token-list lines; unchanged if more than half the lines are lists."""
       if not text: return text
       src = _lf(text)
       lines = src.split("\n")
       hit = [bool(RE_C5_TAGLINE.fullmatch(l) or RE_C5_URL_LINE.fullmatch(l) or _is_list_line(l.strip())) for l in lines]
       n_hit, n_nonempty = sum(hit), sum(1 for l in lines if l.strip())
       if not n_hit or n_hit * 2 > n_nonempty: return text
       return "\n".join(l for l, h in zip(lines, hit) if not h)
   ```
3. **Action:** fix for pages with a few list lines; a page that is mostly lists is left unchanged for the reader to drop.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 12 of the 21 rows labelled C5; 17 rows touched in the pack overall.
5. **Side effects:** a C5-heavy page (tag cloud, link list, menu dump) is not fixed and must be dropped by the reader; that drop is not automated. A list of names or epithets written without dandas is removed although it may be content. A reference line that is only a URL is lost together with the spam URLs.

## Medicine 9 — G1 Cut at the vowel sign

1. **Disease:** G1, 19 rows in the pack. Examples (whitespace or extra virama removed):
   - `61cdf0be9f009325` offset 4195: `षट््षष्टितमो` becomes `षट्षष्टितमो` (sarit.indology.info, double virama)
   - `dfab2a81a8c6cfc6` offset 70483: `लक्ष्मीसहित ः` becomes `लक्ष्मीसहितः` (anandamakaranda.in, space before visarga)
   - `cb50958b8cdd3fca` offset 170: `विद््ध्वा` becomes `विद्ध्वा` (sarit.indology.info, double virama)
2. **Medicine:** whitespace, or a line break, between a consonant (क-ह, क़-य़) and a following dependent sign is removed so the sign re-attaches. Dependent signs are matra, virama, anusvara, candrabindu, visarga and nukta. The gap is left when the sign is followed by a second vowel sign (ोि is corruption, not a cut). Two viramas in a row collapse to one. Function `fix_g1`:
   ```python
   CONS = r"\u0915-\u0939\u0958-\u095F"    # consonants क-ह and nukta consonants
   DEP = r"\u0901-\u0903\u093C\u093E-\u094D"    # candrabindu, anusvara, visarga, nukta, matras, virama
   MATRA = r"\u093E-\u094C"    # vowel signs only
   RE_G1_WS = re.compile(rf"([{CONS}])[ \t\u00A0]+([{DEP}])(?![{MATRA}])")
   RE_G1_NL = re.compile(rf"([{CONS}])[ \t\u00A0]*\r?\n[ \t\u00A0]*([{DEP}])(?![{MATRA}])")
   RE_G1_DOUBLE_VIRAMA = re.compile(r"्{2,}")

   def fix_g1(text):
       text = RE_G1_WS.sub(r"\1\2", text)
       text = RE_G1_NL.sub(r"\1\2", text)
       return RE_G1_DOUBLE_VIRAMA.sub("्", text)
   ```
3. **Action:** fix. The gap is closed; both characters are kept.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 6 of the 19 rows labelled G1; 6 rows touched in the pack overall.
5. **Side effects:** a dependent sign with no bare consonant immediately before the gap is left alone (।⏎्रणयी, क् िशुनि, धे ु, [या]ः, --ाखा): that damage cannot be repaired from the text, so 13 of the 19 G1 rows stay as they are. Of the 6 repaired, 4 are repaired by the double-virama collapse alone. A word-final virama followed by a space and a consonant (ब्रह्मन् कथ) is normal Sanskrit and is never joined. Vedic accent marks after a dash are not touched. A deliberate space before a visarga in a grammar text that discusses the sign itself would be closed.

## Medicine 10 — C4 Two documents joined

1. **Disease:** C4, 16 rows in the pack. Examples (rows the detector fires on; what is there):
   - `6da72db6a95c25b8` (newssanskrit.blogspot.com): marquee headlines ending in danda, then a Blogger post-date header, then the post with a dateline `कोच्ची >`.
   - `596acf94f5ae92b4` (newssanskrit.blogspot.com): same layout; dateline `नवदहली >`.
   - `d571365a691a7aa1` (newssanskrit.blogspot.com): same layout; dateline `नवदिल्ली>`.
2. **Medicine:** detected on the original text, before C1, by any of three signals. Two or more lines start with a Devanagari dateline `<place>>`. The page carries two or more Blogger post-date headers (an archive page). One post-date header follows Devanagari sentences (marquee items joined to the post). Detector `detect_joined`; `medicine_c4` returns the text unchanged:
   ```python
   DEVA = r"ऀ-ॿ꣠-ꣿ᳐-᳿"
   MONTHS = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
   DAYS = r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
   def _lf(text): return text.replace("\r\n", "\n")
   RE_DATELINE = re.compile(rf"^[{DEVA}][^\n>]{{1,24}}[ \t]?>[ \t]*\S", re.M)
   RE_POST_DATE = re.compile(rf"^{DAYS}, {MONTHS} \d{{1,2}}, \d{{4}}$")
   RE_DEVA = re.compile(rf"[{DEVA}]")
   def detect_joined(text):
       """C4 detector (no automated action). Run it on the ORIGINAL text, before C1, which removes the date headers and menu it
       relies on. True when: >= 2 news datelines; or >= 2 Blogger post-date headers (archive page); or one post-date header
       that follows Devanagari sentences (marquee items joined to the post)."""
       if not text: return False
       if len(RE_DATELINE.findall(text)) >= 2: return True
       lines = [l.strip() for l in _lf(text).split("\n")]
       dates = [i for i, l in enumerate(lines) if RE_POST_DATE.match(l)]
       if len(dates) >= 2: return True
       if dates and any(RE_DEVA.search(x) and x[-1] in "।॥" for x in lines[:dates[0]] if x): return True
       return False

   def medicine_c4(text):
       return text    # action none: the detector `detect_joined` reports; splitting is a corpus-time action
   ```
3. **Action:** none. Splitting is a corpus-time action: segment at the datelines or date headers and re-emit the pieces as separate documents. No text is changed per document.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %): pass; the detector fires on 0 of 68 gold documents. No automated action. Proxy: detector fires on 0/184 clean rows (information only). Recall: fires on 7 of the 16 rows labelled C4; 9 rows detected in the pack overall (8 newssanskrit, 1 simplesanskrit archive page). After C1 runs the detector finds 0 rows, which is why it must run first.
5. **Side effects:** a news digest that is meant to be one page is flagged. Wiki pages whose sections are glued by `[सम्पादयतु]` headings (rows 162, 171) are not detected: a heading-plus-paragraph rule fires on nine clean rows (28, 29, 59, 255, 297, 368, 450, 457, 466) and is not used. The sanskritdocuments.org multi-text files and other joined pages without datelines are missed.

## Medicine 11 — F2 Benchmark leak

1. **Disease:** F2, 12 rows in the pack, all Itihāsa test-split hits; 0 FLORES-200 or IN22 hits. Examples (rows the detector fires on; what is there):
   - `935e30775b66fab4` (upasanayoga.org): Mahābhārata quotation sharing 24 windows with Itihāsa test sentence 5826.
   - `1871b6a4ca1aaec1` (sarit.indology.info): Mahābhārata chapter sharing 184 windows with sentence 6870, 25 benchmark sentences hit.
   - `91abf9d2eaed3776` (sarit.indology.info): Mahābhārata chapter sharing 172 windows with sentence 6541, 22 benchmark sentences hit.
2. **Medicine:** normalise both sides (NFC; drop punctuation, symbols, separators, digits, format characters) and flag the document when one benchmark sentence from FLORES-200, IN22 or the Itihāsa test split shares at least two distinct 50-character windows with it. Same rule as leak_check.py. Detectors `detect_f2` and `drop_f2_flores` (full code; `medicine_f2` returns the text unchanged):
   ```python
   import collections
   import json, os, unicodedata
   DEFAULT_BENCH = os.path.join("..", "bench")
   WINDOW = 50
   MAX_SENTENCE_CHARS = 2000
   BENCH_DIRS = ("flores200_devtest", "itihasa_test", "in22_gen")
   DROP_BENCH_PREFIXES = ("flores", "in22")
   _DROP_CATS = ("P", "Z", "S")
   _DROP_FULL = {"Nd", "Cf", "Cc"}
   def _dropped(c):
       cat = unicodedata.category(c)
       return cat[0] in _DROP_CATS or cat in _DROP_FULL or c.isspace()
   def normalise(text):
       """NFC per character, then drop punctuation, separators, symbols, digits of every script, format and control chars."""
       return "".join(c for ch in text for c in unicodedata.normalize("NFC", ch) if not _dropped(c))
   class _Index:
       """hash(window) -> [(bench, sid, pos)] over every benchmark sentence; hits are verified against the real text."""
       def __init__(self, bench_dir):
           self.table = collections.defaultdict(list); self.norm = {}; self.n_sentences = 0
           if not bench_dir or not os.path.isdir(bench_dir): return
           for name in BENCH_DIRS:
               path = os.path.join(bench_dir, name, "sentences.jsonl")
               if not os.path.isfile(path): continue
               try:
                   with open(path, encoding="utf-8", errors="replace") as f: lines = f.read().split("\n")
               except OSError: continue
               for ln, line in enumerate(lines, 1):
                   line = line.strip()
                   if not line: continue
                   try: d = json.loads(line)
                   except ValueError: continue
                   if not isinstance(d, dict) or not isinstance(d.get("text"), str): continue
                   sid = d.get("id", ln)
                   if not isinstance(sid, (int, str)): sid = ln
                   ns = normalise(d["text"][:MAX_SENTENCE_CHARS])
                   if len(ns) < WINDOW: continue
                   key = (name, sid); self.norm[key] = ns; self.n_sentences += 1
                   for p in range(len(ns) - WINDOW + 1): self.table[hash(ns[p:p + WINDOW])].append((key, p))
       def __bool__(self): return bool(self.table)
       def hits(self, text, prefixes=None):
           """{(bench, sid): number of DISTINCT 50-char windows of that sentence found in text}."""
           found = collections.defaultdict(set)
           if not self.table: return {}
           ns = normalise(text)
           for i in range(len(ns) - WINDOW + 1):
               win = ns[i:i + WINDOW]
               for key, p in self.table.get(hash(win), ()):
                   if prefixes and not key[0].lower().startswith(prefixes): continue
                   if self.norm[key][p:p + WINDOW] == win: found[key].add(win)
           return {k: len(v) for k, v in found.items()}
   _BENCH = {"dir": None, "cache": {}}
   def _index(bench_dir=None):
       d = os.path.normpath(bench_dir or _BENCH["dir"] or DEFAULT_BENCH)
       if d not in _BENCH["cache"]: _BENCH["cache"][d] = _Index(d)
       return _BENCH["cache"][d]
   def _strong(text, bench_dir=None, prefixes=None):
       return any(k >= 2 for k in _index(bench_dir).hits(text, prefixes).values())
   def detect_f2(text, bench_dir=None):
       """True when some benchmark sentence (FLORES-200, IN22 or Itihāsa test split) shares >= 2 distinct 50-char
       normalised windows with the text. False when no benchmark file is available."""
       return _strong(text, bench_dir)
   def drop_f2_flores(text, bench_dir=None):
       """Drop variant, not in MEDICINES: True only for FLORES-200 / IN22 hits (benchmark folder name starts with
       flores or in22). Itihāsa hits never drop (public canon)."""
       return _strong(text, bench_dir, DROP_BENCH_PREFIXES)

   def medicine_f2(text):
       return text    # action none: the detector `detect_f2` reports (keep and record); `drop_f2_flores` is the drop variant
   ```
3. **Action:** none for Itihāsa hits (keep and record): the benchmark quotes the public Mahābhārata and Rāmāyaṇa canon, and dropping would remove the canon itself. A FLORES-200 or IN22 hit would be drop, via `drop_f2_flores`; it fires on 0 rows of this pack, so it is not in the medicine list.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %): pass; the detector fires on 0 of 68 gold documents. No automated action. Proxy: detector fires on 0/184 clean rows (information only). Recall: fires on 12 of the 12 rows labelled F2; 12 rows detected in the pack overall. The drop variant fires on 0 of 500 rows.
5. **Side effects:** needs the benchmark sentence files under ../bench; without them nothing is detected. Any page quoting a canon verse that Itihāsa happens to test on is flagged, which is why the action is keep. A benchmark sentence shorter than 51 normalised characters can never be detected. All 12 Itihāsa hits carry the F2 label; the sarit Mahābhārata rows are good data and must stay in the corpus.

## Medicine 12 — C2 Repeated lines

1. **Disease:** C2, 10 rows in the pack. Examples (line removed; only the first row carries the C2 label):
   - `da1ff98edc2a471c` offset 0: `- - - -⏎` (simplesanskrit.blogspot.com, repeated separator)
   - `c3452b55fcd4bede` offset 1642: `Text Unavailable. If you can help fixing this issue by prov…` (ashtadhyayi.com, repeated notice; labelled D3;C4;G4)
   - `3f95aea95623583e` offset 0: `सामरहस्योपनिषत्⏎` (sa.m.wikisource.org, title printed twice; labelled G4)
2. **Medicine:** identical consecutive lines are collapsed to one. A line under 40 characters that occurs 5 or more times in the document is removed everywhere. Exempt from both steps: speaker tags and lemma markers (contains उवाच, ऊचुः or इति, ends with `--` or `—`) and lines ending with a danda (verse refrain, pratika). Lines of 40 characters or more are only collapsed when consecutive; comparison is whitespace-trimmed. Function `medicine_c2`:
   ```python
   import collections
   def _lf(text): return text.replace("\r\n", "\n")
   RE_C2_ALLOW = re.compile(r"उवाच|ऊचुः|इति|--$|—$|[।॥]$")
   C2_MIN_REPEATS, C2_MAX_LEN = 5, 40
   def medicine_c2(text):
       """C2: collapse runs of identical consecutive lines (whitespace-trimmed comparison); remove a short non-exempt line
       that repeats >= 5 times anywhere in the document."""
       if not text: return text
       src = _lf(text)
       out, prev = [], None
       for l in src.split("\n"):
           s = l.strip()
           if s and s == prev and not RE_C2_ALLOW.search(s): continue
           out.append(l); prev = s or None
       cnt = collections.Counter(l.strip() for l in out if l.strip())
       chrome = {s for s, k in cnt.items() if k >= C2_MIN_REPEATS and len(s) < C2_MAX_LEN and not RE_C2_ALLOW.search(s)}
       if chrome: out = [l for l in out if l.strip() not in chrome]
       new = "\n".join(out)
       return text if new == src else new
   ```
3. **Action:** fix. Duplicate lines are removed; the first copy stays.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 1 of the 10 rows labelled C2; 6 rows touched in the pack overall.
5. **Side effects:** a legitimately repeated short heading or list marker without a danda is removed. Repeated tweet attributions over 40 characters are left to C1, and a chrome line repeated fewer than five times ("Read Also" three times) stays; that is why 9 of the 10 C2 rows are not touched. Reader policy encoded as-is: recurring speaker tags and lemma markers (सूत उवाच, वैशम्पायन उवाच ॥, यथावा--, कात्यायनः--) on rows 208, 297, 412 and 474 are not C2, and the medicine leaves all four rows unchanged. The danda exemption also protects clean rows 386 (lone । lines) and 418 (a headline ending in । repeated twice).

## Medicine 13 — F1 Personal data

1. **Disease:** F1, 9 rows in the pack. Examples (type and offset only; values are never copied):
   - `eb2b252468aea92c` (the-spiritualtalks.com): email at offset 3861.
   - `788a3d1d099f2017` (sanskritdocuments.org): email at offsets 16610 and 17015.
   - `aafd2d8a6d638218` (hitaya.org): phone at offset 148.
2. **Medicine:** replace every email address with `<email>` and every Indian mobile number with `<phone>`. A mobile number is an optional +91 and ten ASCII digits starting 6-9, contiguous or grouped 5+5 or 3+3+4 with one space or hyphen, not inside a longer digit run. ASCII digits only, so Devanagari digits are never touched. Function `fix_f1`:
   ```python
   RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
   RE_PHONE = re.compile(r"(?<![0-9])(?:\+91[ \t-]{0,2})?"
                         r"(?:[6-9][0-9]{9}|[6-9][0-9]{4}[ -][0-9]{5}|[6-9][0-9]{2}[ -][0-9]{3}[ -][0-9]{4})(?![0-9])")

   def fix_f1(text):
       """Replace every email with <email> and every Indian mobile number with <phone>. Idempotent."""
       return RE_PHONE.sub("<phone>", RE_EMAIL.sub("<email>", text))
   ```
3. **Action:** fix. The value is replaced by a type token; the surrounding line stays.
4. **Harm test:** Gold (PR #161, 68 documents, `harm_test_indic.py`): changes 0, drops 0 (0.00 %); ZWJ/ZWNJ and normal-form audits clean: pass. Proxy (184 clean rows): changes 0, drops 0. Recall: touches 9 of the 9 rows labelled F1; 9 rows touched in the pack overall.
5. **Side effects:** the nine pack rows are site-contact lines in footers and credits (sanskritdocuments.org proofreader credits, hitaya.org and the-spiritualtalks.com contact lines), which DISEASES.md does not count as F1 for private people. They are redacted anyway because the cost is one footer token and a missed private address costs a person. Misses: Devanagari-digit numbers, landlines, phone groupings other than contiguous, 5+5 and 3+3+4, postal addresses and ID numbers (prescreen flags Aadhaar and PAN patterns; no pack row has one). A ten-digit catalogue number starting 6-9 would be redacted. Addresses quoted inside a story are redacted too.

## Policy decisions recorded in labels.csv

- Recurring speaker tags and lemma markers (सूत उवाच, यथावा--, कात्यायनः--) are not C2: rows 208, 297, 412 and 474 carry a C2 candidate and no C2 label.
- Emoji and decorative symbols are valid text, not C1.
- ASCII verse numbers in a Devanagari text (sarit) are G4.
- A lone श्रीः after the closing ॥ is a dangling last line, C3.
- Hindi beside a Sanskrit text is D3 (label, not judge); Hindi-dominant text is D1 (one row in this pack, 66).
- F2 marks Itihāsa benchmark overlap and the row is kept; a FLORES-200 or IN22 hit would drop (none in this pack).
- H3: cross-site copies with three or more shared windows are H3 on both sides; one or two shared windows are a quotation; ebible.org and gitasupersite pages are H3 as translated sources; a sa.wikipedia page with an English counterpart is H3 only when the reader judges it a translation (rows 227, 233).
- 22 rows whose note carries "drop→fix" name cleanup that needs rules not in this sheet: learnsanskrit trilingual rows (272), sanskritvarta tweet bodies (37, 38, 114), dr.du.ac.in alternating English paragraphs (101).
- The 18 drop verdicts (menu-only pages, OCR noise, English-dominant pages with Sanskrit quotes, machine-translated prose) are reading judgements; no medicine executes them, and they would need a scale-time quality filter that is not part of this sheet.
