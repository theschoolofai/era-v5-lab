"""Indic integration contracts. Every text is synthetic; no pack data is published."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

SPEC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPEC))
import clean as c

spec = importlib.util.spec_from_file_location('indic_review', SPEC / 'tools/integrate_indic.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
SOURCE = review.read_source()
SELECTED = [row for row in SOURCE if row['id'] in c._RULE]
DECISIONS = json.loads((SPEC / 'results/cleaner/indic_integration.json').read_text())


def document(row, text):
    return dict(doc_id='synthetic-review', text=text, url='', pack_id=row['pack'], lang_label=row['lang'])


def test_inventory_and_overlap_decisions_are_explicit():
    assert len(SOURCE) == 176
    assert len(DECISIONS['overlaps']) == 43
    for row in SOURCE:
        decision = DECISIONS['rules'][row['id']]
        assert (row['id'] in c._RULE) == (decision['status'] == 'CANDIDATE')
        if decision['status'] == 'DEFERRED':
            assert c.DEFERRED_RULES[row['id']] == decision['reason']
    groups = [(row['pack'], row['code']) for row in SELECTED]
    assert len(groups) == len(set(groups))
    assert list(c.RULES)[-1] == 'F1'
    assert {'D2', 'D5', 'F3', 'G1', 'G2', 'G4', 'H3'} <= c.RULES.keys()


@pytest.mark.parametrize('row', SELECTED, ids=lambda row: row['id'])
def test_factory_preserves_source_behavior_and_inputs(row):
    medicine = c._RULE[row['id']]()
    for text in review.probes(row['pack']).values():
        doc = document(row, text)
        original = dict(doc)
        actual = medicine(doc)
        assert actual == row['rule'](doc)
        assert actual[0] in {'keep', 'fix', 'drop'} and isinstance(actual[1], str)
        assert doc == original
        assert actual[0] != 'drop'
        assert all(actual[1].count(ch) >= text.count(ch) for ch in ('\u200c', '\u200d'))
        assert medicine(dict(doc, text=actual[1])) == ('keep', actual[1])
        for pack in ('code-cpp', 'math-finemath', 'sci-finepdfs', 'en-dclm', 'ind-unknown', None):
            assert medicine(dict(doc, pack_id=pack)) == ('keep', text)


@pytest.mark.parametrize('pack', sorted({row['pack'] for row in SELECTED}))
def test_combined_pipeline_unicode_and_idempotence(pack):
    row = next(row for row in SELECTED if row['pack'] == pack)
    assert c._FAMILY[pack] == 'indic'
    assert pack in c.SCOPE['f1_rule.py']  # the shared F1's Indic path replaces the source F1 rules
    for text in review.probes(pack).values():
        doc = document(row, text)
        action, new = c.clean(doc)
        assert action != 'drop'
        assert all(new.count(ch) >= text.count(ch) for ch in ('\u200c', '\u200d'))
        assert c.clean(dict(doc, text=new)) == ('keep', new)


def test_known_failure_and_benchmark_candidates_are_excluded(monkeypatch):
    monkeypatch.delenv('ITIHASA_TEST_SN', raising=False)
    for rid in ('DB-F2-001', 'DB-F2-002', 'DB-C3-003', 'DB-C3-005', 'DB-C3-009', 'DB-C3-012'):
        assert rid in c.DEFERRED_RULES
        assert rid not in c.SCOPE and rid not in c._RULE
    assert 'F2' not in c.RULES  # no keep-only detector masquerades as benchmark remediation


def test_indic_normalization_and_tag_independent_dispatch():
    row = dict(doc_id='synthetic', text='नदीचे पाणी\r\nशेतीसाठी वापरतात।\n', url='',
               pack_id='ind-mr-sangraha-v', lang_label='mr')
    tagged = dict(row, lang_label='mar_Deva')
    assert c.clean(row) == c.clean(tagged)


def test_unsupported_indic_pack_passes_through_but_is_not_registered():
    doc = dict(doc_id='synthetic', text='সাধারণ লেখা।', url='', pack_id='ind-ml-fw2', lang_label='ml')
    assert doc['pack_id'] not in c._FAMILY
    assert c.clean(doc) == ('keep', doc['text'])


def test_builder_does_not_silently_skip_a_bad_heading(tmp_path):
    source = (SPEC / 'sheets/specv1.md').read_text()
    source = source.replace('— indic / A3 / `DB-A3-001`', '— indic / A3 / `XX-A3-001`', 1)
    sheet = tmp_path / 'specv1.md'
    sheet.write_text(source)
    dest = tmp_path / 'clean.py'
    result = subprocess.run([sys.executable, '-I', str(SPEC / 'tools/build_clean.py'), '--sheet', str(sheet), '--out', str(dest)], capture_output=True)
    assert result.returncode != 0 and b'unsupported medicine heading' in result.stderr
    assert not dest.exists()


def test_real_normalization_trigger_and_joiner_exception():
    row = dict(doc_id='synthetic', text='ত্ ', url='', pack_id='ind-bn-fw2', lang_label='bn')
    assert c.a5(row) == ('fix', 'ৎ ')
    for joiner in ('\u200c', '\u200d'):
        text = 'ত্' + joiner
        assert c.a5(dict(row, text=text)) == ('keep', text)


def test_review_falls_back_after_an_ineligible_overlap_candidate():
    rows = [{'id': 'first', 'pack': 'pack', 'code': 'C3'}, {'id': 'second', 'pack': 'pack', 'code': 'C3'}]
    decisions = {'first': {'review_issues': ['not idempotent']}, 'second': {'review_issues': []}}
    review.choose(rows, decisions)
    assert decisions['first']['status'] == 'DEFERRED'
    assert decisions['second']['status'] == 'CANDIDATE'


def test_review_detects_a_cross_rule_second_pass_action():
    def first(doc):
        text = doc['text'].replace('second', 'finished')
        return ('fix' if text != doc['text'] else 'keep', text)

    def second(doc):
        text = doc['text'].replace('start', 'second')
        return ('fix' if text != doc['text'] else 'keep', text)

    doc = dict(doc_id='synthetic', text='start', url='', pack_id='pack', lang_label='en')
    assert review.interaction_check([('first', first), ('second', second)], {'synthetic': doc}) == {'first': ['synthetic']}
