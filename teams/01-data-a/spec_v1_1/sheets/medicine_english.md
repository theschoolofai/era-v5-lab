# medicine_english: English medicines for the Spec v1.1 new diseases

**Draft, 13 Nov.** This sheet has the rules for the new English diseases in `NEW_DISEASES.md`. These are diseases that aren't in `DISEASES.md` and that turn up in 1% or more of the 200 English docs read, which is 2 docs. Four readers read 50 docs each:
- narasimhatejav, en-fineweb-edu (mittalutkarsh/era-v5-lab#7)
- kunal, en-nemotroncc-synth (mittalutkarsh/era-v5-lab#8)
- aneesha, en-nemotroncc (mittalutkarsh/era-v5-lab#9)
- Smita, en-dclm (patilvijay23/era-v5-lab#36)

Reasons and choices are in `decisions_english.md`.

- **Packs.** en-nemotroncc-synth has 326 gold docs and en-nemotroncc 129 (Data A gold). The limit is `max(1, floor(1% of gold))`: 3 docs on en-nemotroncc-synth and 1 on en-nemotroncc.
- **Rule form.** As the v1 rules: `doc = {doc_id, text, url, lang_label, pack_id}`, and `medicine(doc)` returns `(action, text)`. Each rule checks `pack_id` against its `ORIGIN`, the pack where its disease was found. A doc with no `pack_id` passes unchanged.
- **Codes and IDs.** They come from `NEW_DISEASES.md`. Every code here is a proposed new code.
- **Run order.** These rules run after the English family's v1 rules, because the readers found the diseases in v1-cleaned text. Within this sheet they run in section order: stage 10 (characters), then stage 30 (source).
- **Two documents joined (C4).** kunal found it in 4 docs, but it is in `DISEASES.md`, so it isn't new and has no section here. Spec v1 has no English C4 rule.

The last column counts the reading docs with the rule's code that it changes or drops, on the cleaned sample the readers read (`scripts/reading_recall.py`).

| # | ID | disease | action | stage | en-nemotroncc-synth | en-nemotroncc | reading docs treated |
|---|---|---|---|---|---|---|---|
| 1 | `DA-A8-003` | A8 words run together: no space after a full stop (NEW-missing-spaces) | fix | 10 | off | 0.78% (1/129) PASS | 1 / 2 |
| 2 | `DA-D7-001` | D7 facts the rewrite got wrong (NEW-factual-error, and 2 wrong answers from NEW-appended-qa) | drop | 30 | 0.00% (0/326) PASS | off | 4 / 4, and the 2 wrong answers |
| | all in order | sections 1–2 | | | **0.00% (0/326) PASS** | **0.78% (1/129) PASS** | |

en-dclm (62 gold docs) and en-fineweb-edu (158) were run too: both rules are off there, so 0 gold docs are touched (PASS).

**Harm runs, 13 Nov.**
- **First run:** the sheet had a third rule, `DA-D6-002`, for appended questions and answers (NEW-appended-qa, 3 docs, kunal). It caught all 3 reading docs but changed **32 of 326** gold docs on en-nemotroncc-synth, against a limit of 3.
- **What the gold docs showed:** each of the 32 ends in ordinary `Question: … Answer: …` pairs, 1 to 4 of them, with sensible answers. Appended Q&A is a normal part of this synthetic pack, in about 10% of its gold set, and the gold readers marked it clean.
- **No narrower rule works:** nothing in the text separates kunal's docs from the gold ones. A score for how much of the answer appears in the passage gives 0.67, 1.00 and 1.00 for his 3, and 0.50 to 1.00 for the gold docs.
- **What was done (aneeshads, 13 Nov):**
  - `DA-D6-002` is **withdrawn**, and the ID is not reused.
  - The 2 docs with wrong answers (`5aeafd200220c080`, `c3d88009d8a459e9`) were facts the rewrite got wrong, so they are in `DA-D7-001`.
  - The third (`ffaad5c6d3dde332`) has a correct answer.
  - Whether appended Q&A is a disease at all is for the team to rule.
- **`DA-A8-003`'s one gold doc:** `056cc9bc44c927e2` has a real missing space (`tantrum.To the sociopath`), so it is a gold contradiction, within the limit.

Each section below follows the spec v1 card:
1. **Disease:** code, count and examples by doc_id.
2. **Medicine:** in words, then the python block.
3. **Action** and the packs it runs on.
4. **Harm test.**
5. **Side effects.**
6. **Spec v1.1:** status, author, source.

## 1. `DA-A8-003` · A8 words run together: no space after a full stop · fix · stage 10

1. **Disease:** NEW-missing-spaces, 2 docs, aneesha (en-nemotroncc). Examples:
   - `2feb05980d7d894a`: `as you choose.Compose a 500-750-word paper`
   - `502ee3da08920d31`: `Every once in awhile`

   Math has 13 more and science 3, each with its own rule: `DA-A8-001` and `DA-A8-002`.
2. **Medicine:** put the space back where a sentence ends with a lowercase word and the next one starts with a capital, with no space between them: `choose.Compose` becomes `choose. Compose`. It leaves these alone:
   - **URLs, file names and abbreviations:** the word after the dot must be followed by a space, punctuation or the end of the text (`www.Google.com` stays), and the word before it must start a token (`e.g.The`, `Mr.Smith` and `Node.Js` stay);
   - **code:** lines that look like code, and lines inside code fences.

   `awhile` is an English word, so it is left as it is.

```python
RULE_ID = "DA-A8-003"
CODE = "A8"  # proposed new code: words run together (NEW_DISEASES.md)
ACTION = "fix"
STAGE = "10"
STATUS = "CANDIDATE"
ORIGIN = "en-nemotroncc"  # packs it runs on
PACKS = set(ORIGIN.split(", "))
SOURCE = "en-nemotroncc"  # pack whose reading found it (aneesha, Week 2 reading audit)
AUTHOR = "aneeshads"
import re

A8E_GLUED = re.compile(r"(?<![\w./@:\-])([a-z]{2,})\.([A-Z][a-z]+)(?=[\s,;:!?)\"']|$)")
A8E_CODE = re.compile(r"[{};]|==|=>|->|::|//|\bdef |\bfunction\b|\breturn\b")


def medicine_a8e(text):
    out, fence = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append(line)
            continue
        if fence or A8E_CODE.search(line):
            out.append(line)
            continue
        out.append(A8E_GLUED.sub(lambda m: m.group(1) + ". " + m.group(2), line))
    return "\n".join(out)


def medicine(doc):
    if doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    new = medicine_a8e(doc["text"])
    return ("fix" if new != doc["text"] else "keep", new)
```

3. **Action:** fix. **Runs on:** en-nemotroncc. **Reading docs it treats:** 1 of 2 (`2feb05980d7d894a`). `awhile` is kept on purpose.
4. **Harm test:** en-nemotroncc 0.78% (1/129) PASS. The gold doc it changes, `056cc9bc44c927e2`, has the disease itself (`tantrum.To`).
5. **Side effects:**
   - A name written with a dot and a capital, followed by a space (`site.Com today`), gets a space.
   - Words run together with no dot (`twowords`) are missed, because they need a word list.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: aneesha's en-nemotroncc reading, mittalutkarsh/era-v5-lab#9.

## 2. `DA-D7-001` · D7 facts the rewrite got wrong · drop · stage 30

1. **Disease:** NEW-factual-error, 4 docs, kunal (en-nemotroncc-synth). The synthetic rewrite brought in an error that can be checked. Examples:
   - `0f7b90400c1362df`: Victoria called "the Virgin Queen" (that is Elizabeth I)
   - `0f7240ba1fdd3411`: "the battles of Artemisia and Salamis" (Artemisium)
   - `52bd1da881ee0592`: "In Exodus 9" (Joshua 9)
   - `f2a8b2cc25bb5c7a`: a camera comparison reversed

   2 more docs from kunal's NEW-appended-qa have a wrong answer in their appended Q&A:
   - `5aeafd200220c080`: the answer names the Duke of Lauderdale, whom the passage doesn't mention
   - `c3d88009d8a459e9`: "The Institute" for the Albert Shanker Institute

   **Proposed new code D7:** none of D1–D5 covers wrong facts; D4 is about translation.
2. **Medicine:** quarantine the 6 confirmed docs by doc_id, the way spec v1 quarantines confirmed records (`DA-D1-001`, `DA-F1-006`). Nothing in the text marks a wrong fact, so a rule can't find other cases. That needs a fact check or a model. **Chosen by aneeshads, 13 Nov.**

```python
RULE_ID = "DA-D7-001"
CODE = "D7"  # proposed new code: facts the rewrite got wrong (NEW_DISEASES.md)
ACTION = "drop"
STAGE = "30"
STATUS = "CANDIDATE"
ORIGIN = "en-nemotroncc-synth"  # packs it runs on
PACKS = set(ORIGIN.split(", "))
SOURCE = "en-nemotroncc-synth"  # pack whose reading found it (kunal, Week 2 reading audit)
AUTHOR = "aneeshads"

D7_CONFIRMED = frozenset({
    "0f7b90400c1362df", "0f7240ba1fdd3411", "52bd1da881ee0592", "f2a8b2cc25bb5c7a",  # NEW-factual-error
    "5aeafd200220c080", "c3d88009d8a459e9",  # a wrong answer in an appended Q&A (NEW-appended-qa)
})


def medicine(doc):
    if doc.get("pack_id") not in PACKS:
        return ("keep", doc["text"])
    return ("drop", doc["text"]) if doc.get("doc_id") in D7_CONFIRMED else ("keep", doc["text"])
```

3. **Action:** drop. **Runs on:** en-nemotroncc-synth. **Reading docs it treats:** all 4 NEW-factual-error docs and the 2 wrong-answer docs, all dropped.
4. **Harm test:** en-nemotroncc-synth 0.00% (0/326) PASS. The pass proves little: the rule acts only on the 6 listed docs, and none is a gold doc.
5. **Side effects:**
   - Every other doc with a wrong fact is missed; the rule finds only what a reader confirmed.
   - The rest of each of the 6 docs, which may be fine, is dropped with them.
6. **Spec v1.1:** status CANDIDATE, reviewer pending. Source: kunal's en-nemotroncc-synth reading, mittalutkarsh/era-v5-lab#8.
