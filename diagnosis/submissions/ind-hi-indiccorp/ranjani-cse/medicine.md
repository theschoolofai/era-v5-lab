# Medicine sheet: ind-hi-indiccorp (ranjani-cse)

Three diseases found more than five times in the 500-document pack.

## Medicine 1

1. **Disease:** C3 (truncated document), 11 cases.
   Examples:
   - c1204f56ddf72d2e ends with ... at offset ~370
   - 6404b661ab7d5119 ends at ...शिक्षक बलराम कौशिक ने बताया कि offset ~480
   - 88f8b9b04f3c44eb ends at ...करीब छह offset ~280

2. **Medicine:** drop any document whose last non-whitespace character is not a sentence terminator.

```python
import re
TERM = re.compile(r'[।!?."\'”’)\]]\s*$')
def medicine_c3(text):
    return not TERM.search(text.strip())
```

3. **Action:** drop the document.

4. **Harm test:** TBD, Hindi gold set pending (Data B, due 29 Oct).

5. **Side effects:** may drop documents ending on a URL, code block, or abbreviation; may miss truncations ending on a period.

## Medicine 2

1. **Disease:** G1 (cut at the vowel sign / word-boundary damage), 17 cases.
   Examples:
   - 7ee85435bb1db370 बच्चो missing anusvara
   - 45faba24d7143976 स्वास्थ्य ा split matra at offset ~340
   - 019e76df805db9e7 वषज़् mojibake where वर्ष expected
   - d26dca6be8d4af25 जनसं्यस्रया matra corruption at offset ~5

2. **Medicine:** flag a document if a Devanagari consonant is separated from its matra/virama by whitespace, or the corrupt sequence ज़् appears.

```python
import re
SPLIT_MATRA = re.compile(r'[\u0915-\u0939]\s+[\u093E-\u094D\u200C\u200D]')
MOJI        = re.compile(r'ज़्')
def medicine_g1(text):
    return bool(SPLIT_MATRA.search(text) or MOJI.search(text))
```

3. **Action:** fix the text (rejoin split matra); drop if mojibake is extensive.

4. **Harm test:** TBD, Hindi gold set pending (Data B, due 29 Oct).

5. **Side effects:** may flag legitimate ज़् in loanwords; may miss missing-anusvara cases; may flag intentional spacing in poetry.

## Medicine 3

1. **Disease:** G3 (damage from earlier cleaning, machine-translated or generated text), 6 cases.
   Examples:
   - 89a31fc1bec0f40d repeated के कारण, unnatural MT syntax
   - 7a354dffcf84e4d4 Italian sailing-school text machine-translated into Hindi
   - 2484b09e2a68fe66 keyword-stuffed product listing, no sentences
   - 4724780d3ef785bc machine-translated real-estate copy

2. **Medicine:** flag documents that look machine-translated or generated, high ratio of Latin tokens, no sentence terminator across a long text, or repeated function-word trigrams.

```python
import re
LATIN = re.compile(r'[A-Za-z]')
TERM  = re.compile(r'[।!?]')
def medicine_g3(text):
    if len(text) < 200:
        return False
    latin_ratio = len(LATIN.findall(text)) / len(text)
    no_sentence = not TERM.search(text)
    repeated = text.count('के कारण') > 2
    return latin_ratio > 0.05 or (no_sentence and latin_ratio > 0.02) or repeated
```

3. **Action:** drop the document.

4. **Harm test:** TBD, Hindi gold set pending (Data B, due 29 Oct).

5. **Side effects:** may drop legitimate Hindi news that quotes English terms heavily; the के कारण heuristic may misfire on legal or explanatory text.
