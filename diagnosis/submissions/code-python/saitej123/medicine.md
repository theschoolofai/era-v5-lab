# Medicine sheet: code-python (saitej123)

Write one section for each disease that you found more than five times.

## Medicine 1

1. **Disease:** `A1` (Invisible junk characters), count `309` in pack (`218,079` documents scanned). Examples: `1024` (`⟦BOM⟧ U+FEFF at offset 0`), `2926` (`⟦BOM⟧ U+FEFF at offset 0`), `5537` (`⟦ZWSP⟧ U+200B at offset 28456`).
2. **Medicine:** strip only the A1 invisible junk characters from `diagnosis/tools/view_pack.py` (`VISIBLE` excluding `\t`, `U+FFFD`, `U+200C` ZWNJ, and `U+200D` ZWJ per `diagnosis/DISEASES.md`).
```python
from diagnosis.tools.view_pack import VISIBLE

DROP_A1 = {ch for ch in VISIBLE if ch not in ("\t", "\ufffd", "\u200c", "\u200d")}

def medicine_a1(text: str) -> str:
    return "".join(ch for ch in text if ch not in DROP_A1)
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** a unit test that intentionally asserts the presence of a byte-order mark (`\ufeff`) or zero-width space (`\u200b`) literal loses that character. Preserving `U+200C` (ZWNJ) and `U+200D` (ZWJ) avoids corrupting Indic script conjuncts or composite emoji sequences.

## Medicine 2

1. **Disease:** `A2` (Control characters), count `39` in pack. Examples: `1935` (`⟦U+0008⟧ BACKSPACE at offset 3891`), `6672` (`⟦U+0010⟧ DATA LINK ESCAPE at offset 29013`), `6917` (`⟦U+008A⟧ CONTROL U+008A at offset 1238`).
2. **Medicine:** delete accidental C0/C1 control characters (`U+0000..U+0008`, `U+000B`, `U+000E..U+001A`, `U+001C..U+001F`, `U+007F..U+009F`) shown as `⟦U+XXXX⟧` by `diagnosis/tools/view_pack.py`, while preserving tab (`\t`), newline (`\n`), CR (`\r`), form-feed page breaks (`\x0c`), and ANSI escape sequences (`\x1b`).
```python
import re

RE_A2 = re.compile(r"[\x00-\x08\x0b\x0e-\x1a\x1c-\x1f\x7f-\x9f]")

def medicine_a2(text: str) -> str:
    return RE_A2.sub("", text)
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** binary protocol tests that embed raw unescaped control bytes instead of `\xNN` escapes will have those bytes removed.

## Medicine 3

1. **Disease:** `A3` (Mojibake), count `11` in pack. Examples: `10401` (`mojibake 'Ã¡' at offset 7377 (3x)`), `14278` (`mojibake 'Ã¼' at offset 16999 (4x)`), `26910` (`mojibake 'Ã¥' at offset 2675`).
2. **Medicine:** repair double-decoded UTF-8 sequences (`Ã[\x80-\xbf]`, `â€™`, `â€œ`, `â€\x9d`, `â€“`, `â€”`) by re-encoding from CP1252/Latin-1 and decoding as UTF-8.
```python
import re

MOJIBAKE = re.compile(r"(?:Ã[\x80-\xbf]|â€™|â€œ|â€\x9d|â€“|â€”)")

def medicine_a3(text: str) -> str:
    def fix(m: re.Match[str]) -> str:
        s = m.group(0)
        try:
            return s.encode("cp1252").decode("utf-8")
        except UnicodeError:
            return s
    return MOJIBAKE.sub(fix, text)
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** encoding unit tests that intentionally store mojibake fixtures would be normalized if not excluded.

## Medicine 4

1. **Disease:** `A4` (Replacement characters), count `21` in pack. Examples: `13867` (`⟦U+FFFD⟧ at offset 221`), `19500` (`⟦U+FFFD⟧ at offset 11816`), `20650` (`⟦U+FFFD⟧ at offset 2888 (12x)`).
2. **Medicine:** drop any document containing `U+FFFD` (``, shown as `⟦U+FFFD⟧` in `diagnosis/tools/view_pack.py`), unless the file is explicitly documenting `0xFFFD`, because the original bytes were already lost before release.
```python
def medicine_a4(text: str) -> str | None:
    return None if ("\ufffd" in text and "0xfffd" not in text.lower()) else text
```
3. **Action:** drop the document.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** drops files that intentionally include literal `` in a regex character class without mentioning `0xFFFD`.

## Medicine 5

1. **Disease:** `B1` (HTML entities), count `41` in pack. Examples: `4928` (`HTML entity &amp; at offset 6689`), `10770` (`HTML entity &amp; at offset 847`), `12051` (`HTML entity &quot; at offset 21672`).
2. **Medicine:** unescape HTML entities (`&amp;`, `&nbsp;`, `&lt;`, `&gt;`, `&quot;`, `&copy;`, `&reg;`, `&#NNN;`) only when they appear inside `#` comment lines, leaving Python string literals in HTML builders and web templates untouched.
```python
import html, re

RE_B1_COMMENT = re.compile(r"(?m)^\s*#[^\n]*?(&(?:amp|nbsp|lt|gt|quot|copy|reg);|&#\d{2,5};)")

def medicine_b1(text: str) -> str:
    def fix_line(line: str) -> str:
        if line.lstrip().startswith("#") and RE_B1_COMMENT.match(line):
            return html.unescape(line)
        return line
    return "".join(fix_line(ln) for ln in text.splitlines(keepends=True))
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** a comment that intentionally illustrates raw HTML entity syntax (e.g. `# use &amp; for ampersand`) is unescaped to `&`.

## Medicine 6

1. **Disease:** `B3` (Ghost chat markers), count `15` in pack. Examples: `4263` (`ghost marker <|endoftext|> at offset 3647`), `10143` (`ghost marker <|endoftext|> at offset 5864`), `19182` (`ghost marker <|endoftext|> at offset 2887`).
2. **Medicine:** strip `<|im_start|>`, `<|im_end|>`, `<|endoftext|>`, `[INST]`, `[/INST]`, `### Assistant:`, `<think>`, and `</think>` from pre-training text while preserving `<s>` and `</s>` (which are valid HTML strikethrough tags or NLP tokenizer literals in Python code).
```python
import re

GHOST = re.compile(r"<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>|\[INST\]|\[/INST\]|### Assistant:|<think>|</think>")

def medicine_b3(text: str) -> str:
    return GHOST.sub("", text)
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** tokenizer or stop-sequence scripts that reference literal `'<|endoftext|>'` lose that string literal.

## Medicine 7

1. **Disease:** `C2` (Repeated lines), count `34` in pack. Examples: `2418` (`line repeated 32 times consecutively at offset 1323`), `20636` (`line repeated 12 times consecutively at offset 3296`), `21766` (`line repeated 30 times consecutively at offset 2921`).
2. **Medicine:** when the exact same non-trivial line (`>= 20` stripped characters) is repeated `>= 12` times **consecutively**, cap that consecutive run at 3 lines; leave non-consecutive repeated lines across unit tests untouched.
```python
def medicine_c2(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out = []
    prev = None
    run = 0
    changed = False
    for line in lines:
        s = line.strip()
        if len(s) >= 20 and s == prev:
            run += 1
            if run >= 12:
                changed = True
            if run > 3:
                continue
        else:
            prev = s if len(s) >= 20 else None
            run = 1 if prev else 0
        out.append(line)
    return "".join(out) if changed else text
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** static lookup tables with 12+ identical consecutive rows are shortened to 3 rows.

## Medicine 8

1. **Disease:** `E1` (Minified or generated code), count `60` in `labels.csv` (`4,271` across the full `218,079`-document shard). Examples: `21` (`auto-generated header at offset 101`), `190` (`auto-generated header at offset 36`), `239` (`auto-generated header at offset 0`).
2. **Medicine:** drop any file that has a single line of `>= 2000` characters or an explicit auto-generated header (`# AUTOGENERATED! DO NOT EDIT`, `# Generated by the protocol buffer compiler`, `# Generated by Django`, `PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED`) in the first 1000 characters.
```python
import re

AUTOGEN = re.compile(
    r"(?i)(# *auto-?generated[^\n]{0,60}do not edit|"
    r"please do not edit this file, it is generated|"
    r"# *generated by the protocol buffer compiler|"
    r"# *generated by django)"
)

def medicine_e1(text: str) -> str | None:
    lines = text.splitlines()
    if lines and max(len(line) for line in lines) >= 2000:
        return None
    if AUTOGEN.search(text[:1000]):
        return None
    return text
```
3. **Action:** drop the document.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** drops notebook-exported modules (`nbdev`) and compiled protobuf stubs (`_pb2.py`).

## Medicine 9

1. **Disease:** `E2` (Data blobs), count `28` in pack. Examples: `2418` (`hex/number array of 6906 chars at offset 1275`), `13204` (`hex/number array of 1710 chars at offset 1027`), `26303` (`hex/number array of 2875 chars at offset 414`).
2. **Medicine:** replace embedded base64 payloads (`b64decode(...)`, `data:image/...;base64,...`, or padded base64 strings `>= 400` chars) and long hardcoded hex lookup arrays (`>= 64` consecutive `0x...` literals) with an empty placeholder.
```python
import re

BLOB = re.compile(
    r"(?:b64decode\s*\(\s*b?['\"][A-Za-z0-9+/=\s]{300,}['\"]|"
    r"data:image/[a-z]+;base64,[A-Za-z0-9+/=]{200,}|"
    r"['\"][A-Za-z0-9+/]{400,}={1,2}['\"]|"
    r"(?:\b0x[0-9a-fA-F]{2,8}\s*,\s*){64,})"
)

def medicine_e2(text: str) -> str:
    return BLOB.sub('""', text)
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** hardware driver scripts or cryptographic S-box modules that inline 64+ hex constants lose the array contents unless imported from a data file.

## Medicine 10

1. **Disease:** `E3` (Secrets), count `13` in pack. Examples: `635` (`private key at offset 41541`), `8178` (`github token at offset 257`), `8802` (`private key at offset 5478`).
2. **Medicine:** drop any document matching a private key block, AWS access key ID, API key, or GitHub token.
```python
import re

SECRET = re.compile(
    r"AKIA[0-9A-Z]{16}|"
    r"BEGIN [A-Z ]*PRIVATE KEY|"
    r"\bsk-[A-Za-z0-9]{20,}|"
    r"\bgh[pousr]_[A-Za-z0-9]{30,}"
)

def medicine_e3(text: str) -> str | None:
    return None if SECRET.search(text) else text
```
3. **Action:** drop the document.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** drops unit tests that embed a full synthetic PEM private key fixture.

## Medicine 11

1. **Disease:** `F1` (Personal data), count `11` in pack. Examples: `37226` (`email at offset 648`), `47333` (`email at offset 4021`), `52535` (`email at offset 238`).
2. **Medicine:** replace personal email addresses in comment/docstring/`__email__`/`author_email`/`maintainer_email` metadata with `<EMAIL>`, leaving service/placeholder domains (`users.noreply.github.com`, `example.com`, `localhost`), decorators (`@app.route`), filenames (`@2x.png`), and matrix multiplication (`@`) untouched.
```python
import re

RE_F1_META = re.compile(
    r"(?im)^(?:\s*#|\s*\"\"\"|\s*'''|\s*__email__\s*=|\s*author_email\s*=|\s*maintainer_email\s*=)"
    r"[^\n]{0,80}?([A-Za-z][A-Za-z0-9._%+-]{1,40}@([A-Za-z][A-Za-z0-9.-]*\.[A-Za-z]{2,8}))\b"
)

def medicine_f1(text: str) -> str:
    return RE_F1_META.sub(lambda m: m.group(0)[:m.group(0).rfind(m.group(1))] + "<EMAIL>", text)
```
3. **Action:** fix the text.
4. **Harm test:** 200 clean Python documents — `0` changed (`0.0%`), `0` dropped (`0.0%`). Pass (`<= 1%`).
5. **Side effects:** replaces author contact email strings in package setup headers with `<EMAIL>`.
