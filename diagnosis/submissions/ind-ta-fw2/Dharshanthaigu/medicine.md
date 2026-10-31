# Medicine sheet: ind-ta-fw2 (Dharshanthaigu)

Pack: fineweb-2, tam_Taml, 500 documents (1,452,201 characters). Counts are from `labels.csv`: clean 287, fix 201, drop 12. Every document was scanned by code, word by word; the middle of every `clean` document and all suspected machine translation were also read. All rows are `partial`, and the D4 calls were not checked by a native Tamil reader.

**Harm tests.** The gold set was not available to me, so no harm test was run on gold. Each section gives a proxy: the share of this pack that the medicine changes or drops (an upper bound). On gold, a medicine that changes or drops more than 1% fails; re-run these on gold before use. On this pack all edits together change 3.38% of characters (49,060) and the 12 drops remove 9.55% (138,744).

## Medicine 1

1. **Disease:** C1 boilerplate, 115 documents. Examples: `cb5361ef4ea1c696`: `Sign up to receive our newsletter in your inbox ev`; `a6207a923fd8ca22`: `காலவரிசையைப் பகிரவும்`; `568bd0de84bbbe5b`: `இதையும் பாருங்க : மீராதா கொழப்பிடா.! என்ன நடிப்புட`.
2. **Medicine:** delete (a) lines under 150 characters that occur in 4 or more documents, (b) lines matching `C1_RE=re.compile(r'Share on|Sign up to receive|Related posts|Next Story|t\.me/|டெலிகிராம்|காலவரிசையைப் பகிரவும்|Copy and paste this code|cannot reply to topics|Advertisement|மேலும் படிக்க\.\.|இதையும் (பாருங்க|படிங்க|படியுங்கள்)')`, (c) the line that starts at each `C1:` offset in `labels.csv` (credit lines, timestamps, related headlines, contact footers). The regex reaches only about 35 of the 115 documents, so rule (c) is what makes the result reproducible.
3. **Action:** fix the text (delete the lines).
4. **Harm test:** gold not run. Proxy on this pack: changes 115 of 500 documents (23.0%), 5,011 characters (0.35%), drops 0 documents for C1.
5. **Side effects:** a news line that really mentions Telegram or Facebook is deleted; `மேலும் படிக்க..` followed by a headline is a link, not news text; unrelated headline lines inside a body have no pattern and are found only by rule (c).

## Medicine 2

1. **Disease:** G1 damaged Tamil letter sequences, 22 documents (290 damaged signs). Examples: `d63996e2a9a8b732`: `வேலூா்: கரோனா`; `4f80863664c176ca`: `கள் வௌியாகியுள்`; `48dd3be00c5aab82`: ` இன்னி்ங்சில் ஆ`.
2. **Medicine:** a legacy-text bug turned `ர` into `ா` and `ூ` into `ுா`, and left `ெ ே ை` before the consonant. Apply in order, then NFC:
```python
import re, unicodedata
def g1fix(t):
    t=t.replace('ா்','ர்').replace('ோ்','ேர்').replace('ொ்','ெர்')
    for a,b in [('ாி','ரி'),('ாீ','ரீ'),('ாு','ரு'),('ாூ','ரூ'),('ுா','ூ')]: t=t.replace(a,b)
    t=re.sub('ௌ(?=[\u0bbf\u0bc0])','ெள',t)
    t=re.sub('([\u0bbf\u0bc0\u0bc1\u0bc2\u0bc8])்',r'\1',t)
    t=re.sub(r'(?<![\u0b95-\u0bb9])([\u0bc6\u0bc7\u0bc8])([\u0b95-\u0bb9])',r'\2\1',t)
    return unicodedata.normalize('NFC',t)
```
Detection: `(?<![\u0b95-\u0bb9])[\u0bbe-\u0bcd\u0bd7]` (a vowel sign or virama not preceded by a consonant), except `ெ/ே` followed by `ா/ௗ`. It finds all 22 documents and no other.
3. **Action:** fix the text. No G1 document is dropped, because the rules leave 0 of the 290 damaged signs (the old two-step rule left 25 in 16 documents).
4. **Harm test:** gold not run. Proxy: changes 22 of 500 documents (4.4%), 17,796 characters (1.23%, above the 1% limit), drops 0.
5. **Side effects:** not checked against a Tamil dictionary; step 6 can mis-order a vowel sign in rare consonant clusters; a legitimate word that happens to match steps 2 or 3 would be changed (no such case was found outside the 22 documents).

## Medicine 3

1. **Disease:** C3 truncated document, 37 documents. Examples (the unfinished end): `c231d36f72281264`: `்கில மொழிபெயர்ப்பின் வெளியீடு சென்னையில் நடைப`; `aebffbe78a715708`: `் கொழித்தது. அதிலும் மடத்து நிலங்கள். எல்லாம்`; `5562334dc209bf2e`: `லக்கணம் கூறும் அகத்தியமாகும். இது அகத்தியரால்`.
2. **Medicine:** `flag = len(last)>40 and not last.endswith(tuple('.?!"\'”’)]।:;…'))` on the last non-empty line. Most flags are boilerplate tails (embed text, tag lists, promos); only a few are real mid-word cuts. No `clean` document triggers it.
3. **Action:** fix = delete the last line. One document (`86a594a2`) is `drop`, for A6, not for C3. Do not use C3 as a drop rule.
4. **Harm test:** gold not run. Proxy: changes 37 of 500 documents (7.4%, fails 1% as a drop rule), 7,956 characters (0.55%).
5. **Side effects:** a real last sentence without a full stop (headlines, quotes without punctuation) is deleted.

## Medicine 4

1. **Disease:** D4 bad machine translation and spam, 21 documents. Examples: `054cb6cead3ddfb3`: `NooCube தற்போது ஒரு உண்மையான ரகசிய NooCube கருதப்ப`; `54ae0344bd23097f`: `ProExtender இந்த தலைப்பு இணைக்கப்பட்டுள்ளது - ஏன் `; `0f77ea53fd801c91`: `கிழக்கு லடாக் மற்றும் சீனாவுடன் கார்கில் மற்றும் ச`.
2. **Medicine:** `top=Counter(re.findall(r'\b[A-Za-z]{4,}\b',t)).most_common(1)[0]; flag = top[1]>=8 and len(t)<20000` finds brand-stuffed spam. Machine translation without spam (word order from English, auto-translated sites) was found by reading only.
3. **Action:** drop the 7 spam or machine-translated documents (`054cb6`, `54ae03`, `c92e79`, `655882`, `e3d686`, `128625`, `5bd09956`). The other 14 are `fix` rows meaning "send to a Tamil reader"; they receive no automatic edit.
4. **Harm test:** gold not run. Proxy: flags 21 of 500 documents (4.2%); drops 7 documents (1.4%).
5. **Side effects:** news with repeated names or dates triggers the code (one false hit was removed); `Google` x10 in `1f696c02148459c7` may be a false hit; the reading-only calls were not checked by a native reader.

## Medicine 5

1. **Disease:** C5 keyword and link lists, 19 documents. Examples: `054cb6cead3ddfb3`: `NooCube தற்போது ஒரு உண்மையான ரகசிய NooCube கருதப்ப`; `c9590b0e18378df3`: `Kepa சிறுவயது கதை மற்றும் வாழ்க்கை வரலாறு உண்மைகள்`; `54ae0344bd23097f`: `ProExtender இந்த தலைப்பு இணைக்கப்பட்டுள்ளது - ஏன் `.
2. **Medicine:** flag documents with 3 or more URLs, or the phrase "in Tamil" 2 or more times, or one Latin brand repeated 8 or more times.
3. **Action:** drop if the document is mainly such a list (5 of them, all D4); otherwise strip the tail from the `C5:` offset.
4. **Harm test:** gold not run. Proxy: flags 19 of 500 documents (3.8%).
5. **Side effects:** a real article that quotes several links, or a recipe site that repeats a brand name, is flagged.

## Medicine 6

1. **Disease:** D3 mixed language, 16 documents. Examples: `264798d24ec2bd8a`: `Ingredients for ரசகுல்லா`; `05c9a6ea438df166`: `" Thank you for registering with Dinamalar.com"`; `f8b030fd03e1a987`: `Here we go, the official trailer of #Kaithi ! We s`.
2. **Medicine:** delete lines of at least 8 characters in which more than 50% of the letters are Latin: `sum(c.isascii() and c.isalpha() for c in x)/len(x.strip())>0.5`. Keep the Tamil body.
3. **Action:** fix the text. All 16 documents are `fix`.
4. **Harm test:** gold not run. Proxy: changes 16 of 500 documents (3.2%), 4,779 characters (0.33%), drops 0.
5. **Side effects:** a Tamil document that quotes an English sentence in full loses that sentence.

## Medicine 7

1. **Disease:** C2 repeated lines, 13 documents. Examples (the second copy): `1764f27a3eea3f9f`: `படையப்பா படத்தில் முதலில் நடிக்கவிருந்தது இந்த பிர`; `a30ed1434333cc5c`: `தேசியவாத காங்கிரஸ், திரிணமூல் காங்கிரஸ், சி.பி.ஐ ஆ`; `22f92acc659c4d2e`: `கழுத்தை வெட்டி விட்டு தப்பியோட்டம்`.
2. **Medicine:** for lines of more than 25 characters, delete every copy after the first inside the same document.
3. **Action:** fix the text.
4. **Harm test:** gold not run. Proxy: changes 13 of 500 documents (2.6%), 947 characters (0.07%), drops 0.
5. **Side effects:** a refrain that is repeated on purpose (song or poem lines) loses its repeats.

## Medicine 8

1. **Disease:** A6 wrong or mixed script, 11 documents. Examples: `c9590b0e18378df3`: `Aஅவர் வளர்ந்தபின், கேபாவின் பிரதிபலிப்புகள் மற்றும`; `24d1f3221d4b6703`: `்Tvக்கு எதிரான போராட்டம், DTHக்கு எதிரான போராட்டம்`; `315294ec820a9d4e`: `த்pல் கிடந்து ஐயோ ஜெகன் என்னைக் குத்திப்போட்டான் எ`.
2. **Medicine:** `drop = len(re.findall(r'[\u0b80-\u0bff][A-Za-z]|[A-Za-z][\u0b80-\u0bff]',t))>=5 or len(FOREIGN.findall(t))>=5`, where `FOREIGN` matches Devanagari and other non-Tamil scripts.
3. **Action:** drop where the rule fires (4 documents); fix the other 7 (a single Latin letter inside a Tamil word, such as `வெள்ளத்த்pல்` or `அடைப்புd`) by deleting the stray letter and checking the word.
4. **Harm test:** gold not run. Proxy: flags 11 of 500 documents (2.2%); drops 4 documents (0.8%).
5. **Side effects:** a Tamil sentence that legitimately glues an English acronym to a Tamil suffix (for example `NIMHANSஐ`) reaches the threshold only if it happens 5 times.

## Other findings (five or fewer, no medicine)

D2 romanised or English tail (5 documents, cut at the `D2:` offset), C4 joined documents (3), B2 `{youtube}` tags (1), F1 phone numbers and e-mails (6; type and offset only, no value in this repository), F3 adult content (2, dropped), E3 secrets (0). Seen but not labelled as a disease and recorded in `note`: words split by a space (7 documents), a letter-spaced word (`d60ae580`), stray `;;;;` (`81726322`), Tamil-script digits (`b7266ade`, `e61c833d`). Do not apply NFKC to this data: 38 documents change under it, mostly because of `…`, and four contain `½ ℃ ℉ ″`.
