"""Synthetic tests for recursive G1 parent-medicine generation.

Run: uv run -m pytest -q teams/01-data-a/spec/test_build_spec_v1.py
"""
import csv
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name('build_spec_v1.py')
spec = importlib.util.spec_from_file_location('g1_spec_builder', SCRIPT)
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def put(base, pack, user, contents):
    path = base / pack / user / 'medicine.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding='utf-8')
    return path


def standard(pack, code, treatment, name='1'):
    return f'''# Medicine sheet: {pack} (person)
## Medicine {name}: {code} example
1. **Disease:** {code}, 20 examples.
2. **Medicine:** {treatment}

```python
def cure(t):
    return t
```

3. **Action:** fix.
4. **Harm test:** source reported 0/100 changed, PASS on proxy gold.
5. **Side effects:** Might change a valid document.
'''


def test_recursive_all_packs_conflicts_and_templates(tmp_path):
    base = tmp_path / 'medicines' / 'submissions'
    put(base, 'code-java', 'a', standard('code-java', 'B3', 'Strip header'))
    put(base, 'code-java', 'b', standard('code-java', 'B3', 'Delete all metadata'))
    put(base, 'en-dclm', 'c', standard('en-dclm', 'B3', 'Strip header'))
    put(base, 'math-finemath', 'd', standard('math-finemath', 'C1', 'Remove site chrome'))
    put(base, 'cadj-commits', 'template', '# Medicine sheet: <pack_id>\n## Medicine 1\n1. **Disease:** code, count in your pack, three examples (`doc_id` and the exact characters).\n')
    out = tmp_path / 'spec_v1.md'
    result = mod.build(base, out)
    assert result == {'files': 5, 'sections': 4, 'groups': 3,
                      'multi_proposal_groups': 1, 'blocked': 1}
    doc = out.read_text()
    assert 'code-java / B3 · a' in doc
    assert 'code-java / B3 · b' in doc
    assert 'en-dclm / B3 · c' in doc  # same disease in other pack is not a clash
    assert 'NOT_EVALUATED on regenerated gold' in doc
    assert '```text' in doc and '```python' not in doc
    assert 'G2 Indic' in doc and 'PENDING' in doc
    assert 'source reported 0/100 changed, PASS on proxy gold' in doc
    assert 'all medicine.md submissions' not in doc.lower()  # not approved claim
    with out.with_name('spec_v1_sources.csv').open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5
    assert next(x for x in rows if x['handle']=='template')['status']=='TEMPLATE'
    with out.with_name('spec_v1_conflicts.csv').open() as f:
        conflicts = list(csv.DictReader(f))
    assert len(conflicts) == 1
    assert (conflicts[0]['pack'], conflicts[0]['disease'], conflicts[0]['status']) == ('code-java', 'B3', 'BLOCKED')


def test_equivalent_duplicates_not_automatically_approved(tmp_path):
    base = tmp_path / 's'
    put(base,'code-go','a',standard('code-go','B3','Trim leading marker'))
    put(base,'code-go','b',standard('code-go','B3','Trim leading marker'))
    output = tmp_path / 'spec.md'
    result = mod.build(base, output)
    assert result['blocked'] == 0
    assert 'DUPLICATE' in output.read_text()
    assert 'NOT APPROVED' in output.read_text()


def test_unnumbered_first_medicine_and_3_hash_fields():
    source = '''# Medicine sheet: cadj-stackexchange
1. **Disease:** B3, markers.
2. **Medicine:** remove marker
3. **Action:** fix.
4. **Harm test:** pending
5. **Side effects:** may remove valid markers
## Medicine 2
### 1. Disease
**Code:** B4
### 2. Medicine
Normalize placeholder.
### 3. Action
fix.
### 4. Harm test
Pending
### 5. Side effects
Could change source.
'''
    parsed = mod.sections(source)
    assert len(parsed) == 2
    first = mod.read_fields(parsed[0][1]); second = mod.read_fields(parsed[1][1])
    assert mod.disease_of(parsed[0][0], first) == 'B3'
    assert mod.disease_of(parsed[1][0], second) == 'B4'
    assert len(first) == len(second) == 5


def test_sci_finepdfs_the_disease_and_unstructured_rows(tmp_path):
    src = '''## Medicine 1: F1 private data
1. **The disease:** `F1`, identified examples.
2. **The medicine:** Review.
3. **The action:** fix.
4. **The harm test:** pending.
5. **The side effects:** unknown.
'''
    sections = mod.sections(src)
    fields = mod.read_fields(sections[0][1])
    assert set(fields) == {1,2,3,4,5}
    assert mod.disease_of(sections[0][0],fields) == 'F1'
    base = tmp_path/'s'
    put(base,'en-synth','alice','# Notes\n## Row 16: manual C4 medicine\nManual change\n## Row 34: manual C4 medicine\nAnother')
    target = tmp_path/'spec.md'
    result = mod.build(base,target)
    assert result['sections'] == 2
    assert result['blocked'] == 1
    assert 'No automatic executable decision' in target.read_text()


def test_redaction_and_reproducibility(tmp_path):
    src = standard('code-go','F1', 'Replace foo@example.com and +1 212-555-1212 and ghp_0123456789abcdefghij.')
    base = tmp_path / 's'
    put(base,'code-go','first',src)
    target=tmp_path/'spec.md'
    mod.build(base,target)
    one = target.read_bytes()
    mod.build(base,target)
    assert target.read_bytes()==one
    doc=one.decode()
    assert 'foo@example.com' not in doc
    assert 'ghp_0123456789abcdefghij' not in doc
    assert '[REDACTED_EMAIL]' in doc
    assert '[REDACTED_SECRET]' in doc
    assert '[REDACTED_PHONE]' in doc


def test_no_silent_empty_inputs(tmp_path):
    with pytest.raises(FileNotFoundError):
        mod.build(tmp_path/'missing',tmp_path/'spec.md')
    empty=tmp_path/'empty';empty.mkdir()
    with pytest.raises(ValueError,match='No medicine.md'):
        mod.build(empty,tmp_path/'spec.md')


def test_default_checkout_fails_when_verified_source_missing(tmp_path, monkeypatch):
    team = tmp_path / 'teams' / '01-data-a'
    base = team / 'medicines' / 'submissions'
    put(base,'code-go','someone',standard('code-go','B3','Strip header'))
    monkeypatch.setattr(mod, 'TEAM', team)
    monkeypatch.setattr(mod, 'SUBMISSIONS', base)
    with pytest.raises(FileNotFoundError, match='Incomplete local g1-harm-test'):
        mod.build(base, tmp_path / 'spec.md')


def test_empty_or_unstructured_contributor_still_accounted(tmp_path):
    base = tmp_path/'submissions'
    put(base,'sci-finepdfs','notes', '''# Notes only\n## Preliminary findings\nThere are no completed medicine sections.\n''')
    put(base,'cadj-commits','empty','')
    output=tmp_path/'spec.md'
    result=mod.build(base,output)
    assert result['files'] == 2 and result['sections'] == 0
    with output.with_name('spec_v1_sources.csv').open() as f:
        status={r['handle']:r['status'] for r in csv.DictReader(f)}
    assert status == {'empty':'EMPTY','notes':'UNSTRUCTURED'}
