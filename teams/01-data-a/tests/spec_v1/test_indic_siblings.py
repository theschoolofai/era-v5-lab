"""Receiving-pack scope and build contracts for Indic sibling reuse. Synthetic text only."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

SPEC = Path(__file__).resolve().parents[2] / "spec_v1"
sys.path.insert(0, str(SPEC))
import clean as c


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


extension = module('sibling_extension_test', SPEC / 'build/extend_indic_siblings.py')
review = module('sibling_source_test', SPEC / 'build/integrate_indic.py')
ROWS = {row['id']: row for row in review.read_source()}
REPORT = json.loads((SPEC.parent / 'results/spec_v1/cleaner/indic_sibling_scopes.json').read_text(encoding='utf-8'))
BORROWED = [(pack, rid) for pack, result in REPORT['targets'].items() for rid in result['accepted']]


def test_policy_is_declared_in_source_and_native_ids_are_preserved():
    assert extension.policy_from_source() == REPORT['policy']
    assert len(ROWS) == 176
    for rid, packs in REPORT['rule_scopes'].items():
        assert c.SCOPE[rid] == frozenset(packs)
        assert ROWS[rid]['pack'] in packs
    assert {'ind-bn-sangraha-v', 'ind-hi-indiccorp', 'ind-te-sangraha-v'} <= c._FAMILY.keys()
    indic = {pack for pack, family in c._FAMILY.items() if family == 'indic'}
    assert REPORT['privacy_missing_packs'] == []
    assert set(REPORT['shared_f1_packs']) == indic


def test_one_selected_rule_per_receiving_pack_and_disease():
    selected = [(pack, rid.split('-')[1]) for rid, packs in c.SCOPE.items() if rid.startswith('DB-') for pack in packs]
    assert len(selected) == len(set(selected))
    for pack, entry in REPORT['targets'].items():
        native_codes = {rid.split('-')[1] for rid in entry['native_rules']}
        assert not native_codes & {rid.split('-')[1] for rid in entry['accepted']}


@pytest.mark.parametrize('pack,rid', BORROWED, ids=[pack + '-' + rid for pack, rid in BORROWED])
def test_borrowed_callable_has_the_tested_scope_and_source_behavior(pack, rid):
    row = ROWS[rid]
    assert pack.split('-')[1] == row['pack'].split('-')[1]
    entry = REPORT['targets'][pack]
    attempt = next(a for a in entry['attempts'] if a['rule_id'] == rid and a['result'] == 'ACCEPTED')
    assert attempt['gold']['result'] == attempt['combined_gold']['result'] == 'PASS'
    assert entry['gold_n'] > 0
    fn = c._RULE[rid]()
    original = extension.target_rule(row, pack)
    for text in list(review.probes(pack).values()) + ['<p>' + review.SENTENCES[pack.split('-')[1]] + '</p>']:
        doc = dict(doc_id='synthetic', text=text, url='', lang_label=pack.split('-')[1], pack_id=pack)
        assert fn(doc) == original(doc)
        assert fn(dict(doc, pack_id='ind-unknown')) == ('keep', text)


def test_empty_or_missing_gold_never_creates_a_pipeline():
    for pack in ('ind-hi-sangraha-s', 'ind-hi-sangraha-v', 'ind-ta-fw2', 'ind-ta-sangraha-s'):
        assert REPORT['targets'][pack]['result'] == 'NOT TESTABLE'
        assert pack not in c._FAMILY
    for pack in ('ind-ml-fw2', 'ind-or-fw2'):
        assert REPORT['targets'][pack]['result'] == 'NO SAME-LANGUAGE DONOR'
        assert pack not in c._FAMILY


def test_sibling_rule_factory_refuses_a_cross_language_target():
    with pytest.raises(ValueError, match='cross-language'):
        extension.target_rule(ROWS['DB-A5-001'], 'ind-hi-fw2')


def test_bengali_sibling_receives_the_real_normalization_fix():
    doc = dict(doc_id='synthetic', text='ত্ ', url='', lang_label='bn', pack_id='ind-bn-sangraha-v')
    assert c.a5(doc) == ('fix', 'ৎ ')
    assert 'ind-bn-sangraha-v' in c.SCOPE['f1_rule.py']  # every Indic pack gets the shared F1


def test_receiving_pipeline_checks_include_shared_f1_and_keep_pack_guards():
    pipeline = extension.compose([], set(), {}, review.shared_f1_rule(), 'ind-hi-fw2')
    doc = dict(doc_id='synthetic', text='संपर्क करें: 9876543210', url='',
               lang_label='hin_Deva', pack_id='ind-hi-fw2')
    assert pipeline(doc) == ('fix', 'संपर्क करें: <PHONE>')
    assert pipeline(dict(doc, pack_id='ind-unknown')) == ('keep', doc['text'])
    assert pipeline(dict(doc, text='संपर्क करें: <PHONE>')) == ('keep', 'संपर्क करें: <PHONE>')
