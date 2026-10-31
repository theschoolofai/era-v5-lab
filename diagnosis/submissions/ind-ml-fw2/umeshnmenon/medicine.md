# Medicine sheet: ind-ml-fw2 (umeshnmenon)

Pack: Malayalam FineWeb (`mal_Mlym`), 500 documents. Labels so far: 150 rows (75 `fix`, 68 `clean`, 7 `drop`).

| Code | Disease | Documents | Findings | Medicine |
|---|---|---:|---:|---|
| D3 | Mixed language | 43 | 70 | Medicine 2 |
| C1 | Boilerplate | 33 | 36 | Medicine 1 |
| C4 | Two documents joined | 11 | 12 | Medicine 3 |
| F3 | Harmful content | 5 | 5 | none (not more than five) |
| G1 | Cut at the vowel sign | 2 | 3 | none |
| C3 | Truncated document | 2 | 2 | none |
| H1 | Exact duplicate in the pack | 1 | 1 | none; method under Duplicates across the pack |
| H2 | Near duplicate in the pack | 1 | 1 | none; method under Duplicates across the pack |
| F1 | Personal data | 1 | 1 | none |
| C5 | Keyword or link list | 1 | 1 | none |
| C2 | Repeated text inside one document | 1 | 1 | none; method under Repeats inside one document |

A finding is one occurrence. A document with `D3;D3;D3` counts once under Documents and three times under Findings.

Every medicine below has two layers. Layer 1 is a regex for the patterns that recur in this pack. It is cheap, exact, and easy to harm-test. Layer 2 is the Laya decision model ([convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya), `laya-multilingual` checkpoint) for wordings the regex has not seen. Laya does not generate text, so it cannot invent a span, and the same input always gives the same answer.

The local harm proxy is the 68 documents marked `clean` in this sheet. One document is already more than 1% of 68, so a medicine passes the proxy only if it changes 0 of them. Final numbers must come from the official Malayalam gold set.

---

## Medicine 1 — C1 (boilerplate)

1. **Disease:** C1, 33 documents, 36 findings.
   - `e95ed7fc1706020c` — `Story high light: onion price` (English footer note)
   - `9162d14fb96c2741` — `Credits : Amma Secret Recipes`
   - `385533067bf3388b` — `Don't Miss!` link list before the article

2. **Medicine:**

   **Layer 1, regex.** Delete lines that match the site furniture seen in this pack: credit lines, English summary footers, `Just In` / `Don't Miss` / `Also Read` / `You may also like` rails, `Updated:` / `Published:` / `Last modified` stamps, `Screengrab` / `Photo:` lines, desk bylines such as `By സമകാലിക…`, copyright lines, and the Malayalam read-more tails `ഈ വാര്ത്ത കൂടി വായിക്കൂ`, `ദേശാഭിമാനി വാർത്തകൾ ഇപ്പോള്`, `ഏറ്റവും വിശ്വാസ്യതയുള്ള വാർത്തകള്`.

   **Layer 2, Laya.** For lines the regex did not match, ask Laya whether the line is article body or page furniture. Pass the line, its neighbours, and its position. Delete only unbroken runs of furniture at the start and at the end of the document. Never cut from the middle: C1 sat at the edges in this pack, and the middle is where names, glosses, and quotations live.

   Laya must be fine-tuned before use. The base checkpoints are close to chance without it. Training data comes from this sheet: lines inside the `offset` ranges of C1 rows are furniture, and lines of the `clean` documents are body. After fine-tuning, fit a temperature on held-out lines, because the model ships over-confident. The question is a two-option `choice`, not a yes/no `noul`, because the model card reports that `noul` can follow its option labels instead of the text.

```python
import re
from laya import Router

C1_LINE = re.compile(
    r"(?i)^(?:"
    r"Credits\s*:.*"
    r"|english summary\b.*"
    r"|Don't Miss!?\b.*"
    r"|Just In\b.*"
    r"|Also Read(?:-|:|\b).*"
    r"|You may also like:.*"
    r"|Read Also(?:-|:|\b).*"
    r"|Screengrab\b.*"
    r"|Updated:\s+.*"
    r"|Published:\s+.*"
    r"|Last (?:Modified|updated)\b.*"
    r"|Photo:\s*.*"
    r"|By\s+സമകാലിക.*"
    r"|©\s*\d{4}\b.*"
    r")$"
)
C1_TAIL = re.compile(
    r"(?m)(?:"
    r"ഈ വാര്ത്ത കൂടി വായിക്കൂ.*$"
    r"|ദേശാഭിമാനി വാർത്തകൾ ഇപ്പോള്.*$"
    r"|ഏറ്റവും വിശ്വാസ്യതയുള്ള വാർത്തകള്.*$"
    r")"
)

router = Router(preload=True)

FURNITURE = {"part": {
    "type": "choice",
    "instructions": "Is this line part of the article, or part of the web page around it?",
    "criteria": {
        "A": "article body: sentences of the news story, recipe or essay",
        "B": "page furniture: related links, credits, bylines, dates, share or read-more prompts, ads, copyright",
    },
}}

def is_furniture(lines: list[str], i: int, threshold: float = 0.9) -> bool:
    state = {
        "line": lines[i],
        "position": "start" if i < 3 else "end" if i > len(lines) - 4 else "middle",
        "previous": lines[i - 1] if i else "",
        "next": lines[i + 1] if i + 1 < len(lines) else "",
    }
    answer = router.predict(state, FURNITURE, model="multilingual")["answers"]["part"]
    return answer["choice"] == "B" and answer["confidence"] >= threshold

def medicine_c1(text: str) -> str:
    lines = [ln for ln in text.split("\n") if not C1_LINE.match(ln)]
    lines = C1_TAIL.sub("", "\n".join(lines)).split("\n")
    start, end = 0, len(lines)
    while start < end and (not lines[start].strip() or is_furniture(lines, start)):
        start += 1
    while end > start and (not lines[end - 1].strip() or is_furniture(lines, end - 1)):
        end -= 1
    return "\n".join(lines[start:end])
```

   The model card (`laya` 0.3.20) shows `answers[...]["choice"]` but does not name the field that holds the probability of that choice. `confidence` is assumed here; check it against the installed package.

3. **Action:** **fix** (delete the matched lines). Drop the document if fewer than about 200 characters of Malayalam prose remain after the cut.

4. **Harm test:**

   | Layer | Clean documents changed (of 68) | Dropped | C1 documents caught (of 33) |
   |---|---:|---:|---:|
   | Layer 1, regex | 0 | 0 | 20 |
   | Layer 2, Laya | not run yet | not run yet | not run yet |

   Laya runs only after fine-tuning. Raise its threshold until the clean set stays at 0 changes. Official gold-set numbers: to be filled.

5. **Side effects:** An article that discusses the phrase “Also Read” or quotes a `Credits:` line on its own line loses that line. A short article whose first line is a real headline could lose the headline if Laya reads it as furniture. The 200-character rule turns an over-cut into a drop instead of a hollow document. The regex list is incomplete by design: it holds the phrases from this pack, and Layer 2 exists for the rest.

---

## Medicine 2 — D3 (mixed language)

1. **Disease:** D3, 43 documents, 70 findings.
   - `67cfcddf399de1f3` — `aparna shaji`, `Last Modified`, `IST` (English article metadata)
   - `a627224d0ce02faf` — trailing `English Summary: Masai Mara Travel experience…`
   - `780e9cb21e997cd8` — English word in parentheses inside Malayalam prose (natural mix; must not be cut)

2. **Medicine:** D3 has two classes, and only one of them is cut.

   **Class A, English scrap: fix.** English lines that are page furniture: metadata, summaries, photo credits, hashtag stacks, stock tickers.

   **Class B, natural mix: keep.** A Malayalam sentence with a Latin name, a parenthetical original spelling, a URL, or a short English term. The medicine never rewrites it and never deletes it.

   **Layer 1, regex.** Run `medicine_c1`, which already removes English chrome lines. Then delete a trailing paragraph when at least 85% of its letters are Latin and it starts with a cue such as `English Summary`, `Story Highlights`, `Topic:`, `BSE:`, `NSE:` or `#`.

   **Layer 2, Laya.** A line in the middle of the document is a candidate only if at least 85% of its letters are Latin. A Class B sentence is mostly Malayalam, so it never becomes a candidate. Ask the same `FURNITURE` question for each candidate and delete it if Laya says furniture with high confidence.

```python
def latin_share(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    return sum(c.isascii() for c in letters) / len(letters) if letters else 0.0

TRAILING_CUES = re.compile(r"(?i)^(?:English Summary\b|Story Highlights\b|Topic:\s|BSE\s*:|NSE\s*:|#\w+)")

def medicine_d3(text: str, threshold: float = 0.9) -> str:
    lines = medicine_c1(text).split("\n")
    while lines and latin_share(lines[-1]) >= 0.85 and TRAILING_CUES.match(lines[-1]):
        lines.pop()
    return "\n".join(
        line for i, line in enumerate(lines)
        if not (latin_share(line) >= 0.85 and len(line) >= 20 and is_furniture(lines, i, threshold))
    )
```

3. **Action:** **fix** Class A. Leave Class B as written. Do not drop a document because it mixes languages.

4. **Harm test:**

   | Layer | Clean documents changed (of 68) | Dropped |
   |---|---:|---:|
   | Layer 1, regex (through `medicine_c1`) | 0 | 0 |
   | Trailing English cue rule | not run yet | not run yet |
   | Layer 2, Laya | not run yet | not run yet |

5. **Side effects:** An English quotation that is the subject of the article could be cut if it sits on its own line and Laya calls it furniture. A Latin-script line under 20 characters is never a candidate, so a short English heading in the middle stays. A full English article labelled `mal_Mlym` is D1, not this medicine.

---

## Medicine 3 — C4 (two documents joined)

1. **Disease:** C4, 11 documents, 12 findings.
   - `b61e9a6fc72f518e` — `Just In` headline rail joined in front of the pilot article
   - `435fdd72e5a6455b` — `Read Also:- …` promotion joined after the article
   - `396ca17551d6e885` — three separate news items run together

   C4 is two unrelated texts in one document. It is not a duplicate: text repeated inside one document is C2, and copies across documents are H1 and H2 (see the two sections after this one).

2. **Medicine:**

   **Layer 1, regex.** Run `medicine_c1`. Most joins in this pack were a rail or a promotion glued to the article, and the C1 patterns cut them.

   **Layer 2, Laya.** For a document that still has three or more paragraphs, ask Laya whether each later paragraph continues the opening. Cut from the first paragraph it confidently calls a different article. If less than about 200 characters remain, drop the document instead of keeping a stub.

```python
SAME_STORY = {"story": {
    "type": "choice",
    "instructions": "Does this paragraph continue the same article as the opening?",
    "criteria": {
        "A": "same article: the same event, people or subject",
        "B": "a different article, an advertisement or a promotion",
    },
}}

def medicine_c4(text: str, threshold: float = 0.9) -> str | None:
    paras = [p for p in medicine_c1(text).split("\n") if p.strip()]
    if len(paras) >= 3:
        opening = "\n".join(paras[:2])[:1000]
        for i in range(2, len(paras)):
            state = {"opening": opening, "paragraph": paras[i]}
            answer = router.predict(state, SAME_STORY, model="multilingual")["answers"]["story"]
            if answer["choice"] == "B" and answer["confidence"] >= threshold:
                paras = paras[:i]
                break
    kept = "\n".join(paras)
    return kept if len(kept) >= 200 else None
```

3. **Action:** **fix** when one coherent article of about 200 characters or more remains. **drop** (`None`) otherwise.

4. **Harm test:**

   | Layer | Clean documents changed (of 68) | Dropped |
   |---|---:|---:|
   | Layer 1, regex (through `medicine_c1`) | 0 | 0 |
   | Layer 2, Laya | not run yet | not run yet |

5. **Side effects:** A long feature that moves to a new subtopic can look like a second article to Laya; a high threshold limits this. Laya reads about 768 tokens of state by default, so the opening is cut to 1,000 characters.

---

## Repeats inside one document (C2)

C2 is text repeated inside one document. It was found in fewer than five documents, so it does not need a medicine; this is the method and what it measured.

- `2307d0c6733e5ce6` — a 350-character passage at offset 401 appears again, unchanged, at offset 1809. Nothing like it exists in another document (the closest document shares 8% of its character 5-grams), so it is C2, not H1.
- `0f33ec6172258c08` — two passages of about 210 and 260 characters repeated.
- `f70a3757c962344d` — the news header repeated in the body.

The copies do not start and end at line or sentence breaks, so hashing lines or sentences misses them. Exact sentence hashing also changed 5 of the 130 `clean` documents. The method below finds any exact passage of at least `min_chars` characters that appears twice and deletes the later copy.

```python
def drop_repeated_passages(text: str, min_chars: int = 300) -> str:
    while True:
        first, hit = {}, None
        for i in range(len(text) - min_chars + 1):
            j = first.setdefault(text[i:i + min_chars], i)
            if j + min_chars <= i:
                hit = (j, i)
                break
        if hit is None:
            return text
        j, i = hit
        n = min_chars
        while i + n < len(text) and j + n < i and text[j + n] == text[i + n]:
            n += 1
        text = text[:i] + text[i + n:]
```

| `min_chars` | Clean documents changed (of 130) | `2307d0c6733e5ce6` | `0f33ec6172258c08` | `f70a3757c962344d` |
|---:|---:|---|---|---|
| 100 | 6 | caught | caught | missed |
| 200 | 2 | caught | caught | missed |
| 300 | 0 | caught | missed | missed |

At 300 it passes the harm rule but only catches long repeats. The clean set here is the 130 `clean` rows of the current 300-row sheet, not the 68 used above.

---

## Duplicates across the pack (H1, H2, H3)

The H codes compare one document with the other documents of the pack: an exact copy (H1), a copy with small changes (H2), or the same content in another language (H3). A repeat inside one document is C2, above. H1 and H2 were found once each, so neither gets a medicine section. The method for running them at corpus scale:

1. **Normalise** each document into a comparison key: NFC, whitespace collapsed, URLs replaced by `<url>`, Latin case folded. The key is used only for comparing; the kept text is the original. Use NFC only, because NFKC would itself cause G4.
2. **Exact duplicates (H1):** hash the key of each document. Keep the first `doc_id` for each hash and drop the later ones.
3. **Near duplicates (H2):** character 5-gram shingles, MinHash with 128 permutations, and LSH at a Jaccard threshold of about 0.8. Character n-grams fit Malayalam better than word n-grams, because one Malayalam word carries suffixes that a word tokenizer splits poorly.
4. **Another language (H3):** a translation shares almost no character n-grams with its source, so MinHash cannot find it. That needs a multilingual sentence encoder trained to match translations, such as LaBSE. H3 was not found in this pack.

```python
import hashlib
import unicodedata
from datasketch import MinHash, MinHashLSH

URL = re.compile(r"https?://\S+|www\.\S+")

def norm_key(text: str) -> str:
    key = unicodedata.normalize("NFC", text)
    key = URL.sub("<url>", key)
    return re.sub(r"\s+", " ", key).strip().casefold()

def exact_key(text: str) -> str:
    return hashlib.sha1(norm_key(text).encode("utf-8")).hexdigest()

def minhash(text: str, k: int = 5, num_perm: int = 128) -> MinHash:
    key = norm_key(text)
    m = MinHash(num_perm=num_perm)
    for i in range(max(len(key) - k + 1, 1)):
        m.update(key[i:i + k].encode("utf-8"))
    return m

def dedupe(corpus: list[tuple[str, str]], threshold: float = 0.8) -> list[str]:
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    kept = []
    for doc_id, text in corpus:
        m = minhash(text)
        if lsh.query(m):
            continue
        lsh.insert(doc_id, m)
        kept.append(doc_id)
    return kept
```

Side effect: two short news briefs that share a wire-agency template can pass 0.8 without being the same story. Check a sample of the pairs before dropping.

---

## Rejected options

| Option | Why it was not chosen |
|---|---|
| Delete by the `offset` ranges in `labels.csv` | Works for these 150 rows only. The course runs the medicine on documents nobody labelled. The offsets are used instead as Laya training data. NOTE: Just to clean this pack up, we can use the offset range from the annotation to remove the texts.|
| A generative LLM that returns the span to delete | The span can change between runs and can be invented, so the 1% harm test is not repeatable. |
| Split paragraphs into sentences, translate to English, then classify | Translation is a generative step with the same risk. It also erases the signal: English inside a Malayalam page is often the very sign of furniture. Malayalam sentence splitting is unreliable, and furniture sits on whole lines, not inside sentences. Laya reads Malayalam directly. |
| Strip every Latin letter from Malayalam documents | Deletes names, original spellings, and the Class B mix that must stay. |

## Next steps

1. Extend the C1 regex from the 13 C1 documents it misses, and re-run the clean-set check after each addition.
2. Build Laya training lines from the `offset` ranges and the `clean` documents, fine-tune `laya-multilingual`, fit the temperature, and fill in the Laya rows above.
3. Confirm that `laya-multilingual` reads Malayalam well. The model card lists 45 of 51 tested languages as usable but does not say whether Malayalam is one of them.
4. Run all three medicines on the official Malayalam gold set and fill in the changed and dropped counts.
5. Re-check the five `clean` documents that repeat a whole sentence (`764508e37990daf8`, `8a2dfc6d228cb4d2`, `6b5a5422907ce088`, `cedfc5d0810b3b19`, `0b189250cabc1253`). If the repeat is a page summary shown twice, they are C2, not `clean`.
