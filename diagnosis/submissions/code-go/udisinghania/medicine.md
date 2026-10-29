# Medicine sheet: code-go

Working sheet based on labels_code-go_500_WORKING_v1.xlsx (500 rows). No cleaning has been applied to the pack. These counts are labels in that workbook; they are not confirmed prevalence. Manual review and the gold-set harm test remain open.

The five codes above the five-record threshold are B3 (247), B4 (43), E1 (42), E2 (8) and E4 (44). The E1 count includes disputed record 13. The workbook marks 422 rows full, 69 partial and 9 check; check is not a permitted read value in the instructor CSV template. 

NOTE: We are further checking on the files.

## Shared patch helper

B4 and E4 use exact reviewed patches. A mismatch stops the change. The patch list is not an automatic classifier. All evidence and patch offsets refer to the original text. On a retained document, apply approved B4 and E4 patches before removing the B3 first line; otherwise B3 shifts every later offset. For a document dropped under E1 or E2, do not apply text patches. Recalculate offsets if any approved patches change text length before another patch stage.

```python
def apply_reviewed_patches(text,patches):
    # Each patch is (start,end,expected_original,approved_replacement).
    patches=sorted(patches);previous=0
    for start,end,expected,replacement in patches:
        if not (previous<=start<end<=len(text)) or text[start:end]!=expected:
            raise ValueError('Patch mismatch or overlapping spans')
        previous=end
    for start,end,expected,replacement in reversed(patches):
        text=text[:start]+replacement+text[end:]
    return text
```

## B3: Dataset markers

**Disease:** 247 currently labelled records.

**Examples:**
- Record 3; doc_id `2f6d4b8c8e3fcbd5`; offset 0; `<reponame>`.
- Record 6; doc_id `2bdf36ae14fd90fa`; offset 0; `<gh_stars>`.
- Record 8; doc_id `b0eed26ac2f6a1a7`; offset 0; `<filename>`.

**Medicine:** In this pack, each B3 case begins with a separate StarCoder metadata line. Remove that whole first line, including its newline. The marker value may be any text; no star-bucket whitelist or metadata-value match is needed. Apply this only to a leading line that starts with one of the three observed markers.

```python
import re

MARKER_LINE = re.compile(r'\A<(?:reponame|filename|gh_stars)>[^\r\n]*\r?\n')

def fix_b3(text):
    match = MARKER_LINE.match(text)
    return text[match.end():] if match else text
```

**Action:** Fix by removing the complete leading metadata line. The original repository, path and star values remain available in source metadata.

**Harm test:** NOT RUN. Clean Go gold set not available locally. Gold documents changed: not measured. Gold documents dropped: not measured. Affected means changed or dropped; more than 1% fails. No zero or pass result is claimed.

**Side effects:** A genuine document whose first line begins with one of these literal markers would lose that line. A document with code on the same first line would lose that code too. Review new source formats before applying this rule outside this pack; issue and jupyter markers are not yet covered.

## B4: PII placeholders

**Disease:** 43 currently labelled records.

**Examples:**
- Record 1; doc_id `f08e1abfa9c2ebdc`; offset 138; `<EMAIL>`.
- Record 27; doc_id `c05ecf8c28dd8d51`; offset 20; `<NAME>`.
- Record 96; doc_id `3bfbdf84356326dc`; offset 150; `<KEY>`.

**Medicine:** Find the old PII placeholders. Review the affected comment, literal or test before approving a replacement. Do not guess the original name or secret.

```python
import re

PLACEHOLDER = re.compile(r'<(?:NAME|EMAIL|KEY|PASSWORD)>')

def fix_b4(text,approved_patches):
    for start,end,expected,replacement in approved_patches:
        if not PLACEHOLDER.search(expected):raise ValueError('Not a B4 placeholder patch')
    return apply_reviewed_patches(text,approved_patches)
```

**Action:** Fix using reviewed patches. If a safe repair is unavailable, review exclusion of that example/file.

**Harm test:** NOT RUN. Clean Go gold set not available locally. Gold documents changed: not measured. Gold documents dropped: not measured. Affected means changed or dropped; more than 1% fails. No zero or pass result is claimed.

**Side effects:** Deleting placeholders blindly can break syntax or test expectations. In record97 a placeholder affects an expression, not just a comment. The approved patch list is still to be written.

## E1: Generated code

**Disease:** 42 currently labelled records.

**Examples:**
- Record 20; doc_id `3c4db0c3d41b7673`; offset 1018; `m.ctrl.Call`.
- Record 145; doc_id `91bf17319ac11223`; offset 922; `protoimpl.MessageState`.
- Record 321; doc_id `fe2c1445611e0cfc`; offset 416; `MarshalJSONBuf`.

**Medicine:** Check the code below the header. Exclude mechanical expansions selected by the code-corpus policy; keep useful fixtures separately.

```python
def select_e1(text,generated_body_confirmed,retain_useful_fixture=False):
    # None means drop. A header regex alone never sets body_confirmed.
    return None if generated_body_confirmed and not retain_useful_fixture else text
```

**Action:** Drop selected generated expansions. Keep useful generated tests/schema examples when approved.

**Harm test:** NOT RUN. Clean Go gold set not available locally. Gold documents changed: not measured. Gold documents dropped: not measured. Affected means changed or dropped; more than 1% fails. No zero or pass result is claimed.

**Side effects:** A header alone is not enough. Record13 is labelled E1 in the submitted150 but our earlier body review disputed it. Current500 labels contain42 E1 rows;41 have supporting generated-body findings. Reconcile record13 before the final count.

## E2: Embedded data

**Disease:** 8 currently labelled records.

**Examples:**
- Record 34; doc_id `637118880fa53f2f`; offset 5772; `0x1f, 0x8b, 0x08, 0x00, 0x00, 0x`.
- Record 145; doc_id `91bf17319ac11223`; offset 23994; `0x0a, 0x23, 0x64, 0x69, 0x63, 0x`.
- Record 377; doc_id `023d4d7c1524277f`; offset 1495; `0x1f, 0x8b, 0x08, 0x00, 0x00, 0x`.

**Medicine:** Identify the payload and its use. Drop a selected generated descriptor file as a whole; do not remove required bytes from a retained file.

```python
def select_e2(text,generated_body_confirmed,opaque_descriptor_confirmed,retain_required_data=True):
    if generated_body_confirmed and opaque_descriptor_confirmed and not retain_required_data:
        return None
    return text
```

**Action:** Drop only approved generated descriptor files. Keep required fixture data, including record360 if the test is retained.

**Harm test:** NOT RUN. Clean Go gold set not available locally. Gold documents changed: not measured. Gold documents dropped: not measured. Affected means changed or dropped; more than 1% fails. No zero or pass result is claimed.

**Side effects:** Seven records contain protobuf descriptor data. Record360 is a transaction fixture. Long arrays are not automatically useless.

## E4: Repeated licence text

**Disease:** 44 currently labelled records.

**Examples:**
- Record 13; doc_id `83381a2f882bdce3`; offset 95; `Permission is hereby granted`.
- Record 27; doc_id `c05ecf8c28dd8d51`; offset 43; `Licensed under the Apache License`.
- Record 58; doc_id `312d930b2b41cf89`; offset 79; `Licensed under the Apache License`.

**Medicine:** Compare actual shared licence wording. Remove only reviewed repeated boilerplate from the training view and keep full legal provenance separately.

```python
def fix_e4(text,reviewed_licence_patches):
    # Review must preserve holders, SPDX, build tags and comment syntax.
    # Save the original licence and source association outside training text.
    return apply_reviewed_patches(text,reviewed_licence_patches)
```

**Action:** Fix reviewed spans while keeping holders, notices, source association and valid Go comment syntax.

**Harm test:** NOT RUN. Clean Go gold set not available locally. Gold documents changed: not measured. Gold documents dropped: not measured. Affected means changed or dropped; more than 1% fails. No zero or pass result is claimed.

**Side effects:** A short SPDX notice or the words licence declaration are not enough. A clean Go gold set may contain valid licences; if this rule changes more than 1%, it fails.

## What remains

1. Review the 69 partial and 9 check rows. The instructor CSV accepts only full or partial; five partial rows and five check rows currently have clean verdicts, which require a full read.
2. Resolve the E1 body-evidence dispute in record 13 before finalizing its count.
3. Approve the B4/E4 patch lists and generated-file selections.
4. Please Note: We are still refining the medicines and identified diseases in the template file.