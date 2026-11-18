"""Input coverage and train/heldout contract checks using real synthetic Parquets."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

pa = pytest.importorskip('pyarrow')
import pyarrow.parquet as pq

JOB = Path(__file__).resolve().parents[1]
REPO = JOB.parents[3]
spec = importlib.util.spec_from_file_location('first_training_inputs', JOB / 'build_inventory.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
sys.path.insert(0, str(REPO / 'teams/01-data-a/pipeline'))
import inventory_check


@pytest.fixture
def scope():
    return json.loads((JOB / 'approved_inputs.json').read_bytes())


@pytest.fixture
def raw(tmp_path, scope):
    root = tmp_path / 'raw'
    for pack in scope['packs']:
        for split in ('train', 'heldout'):
            folder = root / split / pack['pack_id']
            folder.mkdir(parents=True)
            n = 2 if split == 'train' else 1
            table = pa.table({'doc_id': [f'{split}-{i}' for i in range(n)],
                              'text': ['synthetic input'] * n,
                              'pack_id': [pack['pack_id']] * n,
                              'lang_label': [pack['lang_label']] * n})
            pq.write_table(table, folder / 'part-00000.parquet')
    return root


def run(raw, out, scope_file=None):
    return builder.build(raw, out, scope_file or JOB / 'approved_inputs.json')


def test_scope_matches_the_actual_dedup_allowlist_and_source_policy(scope):
    config = json.loads((REPO / scope['dedup_policy']['file']).read_bytes())
    sample = json.loads((REPO / scope['sample_reference']['file']).read_bytes())
    assert len(scope['allowed_train_packs']) == 38
    assert set(scope['allowed_train_packs']) == set(config['pack_order']) == set(config['licence_usable'])
    assert all(config['licence_usable'].values()) and config['default_licence_usable'] is False
    assert set(scope['allowed_train_packs']) == {p['pack_id'] for p in sample['packs']}
    assert all(scope['source_policy']['commit'] in p['license_source'] for p in scope['packs'])
    assert 'chandassu' not in scope['allowed_train_packs']


def test_expanded_inputs_preserve_both_splits_but_only_train_expects_shards(raw, tmp_path):
    original = raw / 'train/code-go/part-00000.parquet'
    for index in range(1, 21):
        original.with_name(f'part-{index:05d}.parquet').write_bytes(original.read_bytes())
    out = tmp_path / 'frozen'
    summary = run(raw, out)
    inventory = inventory_check.load(out / 'expected_inventory.json')
    manifest_bytes = (out / 'input_manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    assert summary['parts'] == len(inventory['parts']) == 96  # production is not limited to 86
    assert inventory['input_manifest_sha256'] == hashlib.sha256(manifest_bytes).hexdigest()
    assert manifest['total_docs'] == 154
    for name, entry in inventory['parts'].items():
        assert entry['raw_sha256'] == hashlib.sha256((raw / name).read_bytes()).hexdigest()
        assert entry['raw_rows'] == pq.ParquetFile(raw / name).metadata.num_rows
        assert entry['expected'] == (['written'] if entry['split'] == 'train' else ['not_sharded'])
    assert all(p['license_source'] and p['license'] for p in manifest['packs'])
    assert len([p for p in inventory['parts'].values() if p['split'] == 'heldout']) == 38
    shards = tmp_path / 'shards'
    shards.mkdir()
    entries = {name: {'pack_id': p['pack_id'], 'status': p['expected'][0]}
               for name, p in inventory['parts'].items()}
    (shards / 'shards_summary.json').write_text(json.dumps({'parts': entries}))
    assert inventory_check.check(inventory, shards=shards)['ok']
    entries['heldout/code-go/part-00000.parquet']['status'] = 'written'
    (shards / 'shards_summary.json').write_text(json.dumps({'parts': entries}))
    assert not inventory_check.check(inventory, shards=shards)['ok']


def test_identical_staging_produces_identical_frozen_files(raw, tmp_path):
    first, second = tmp_path / 'first', tmp_path / 'second'
    run(raw, first)
    run(raw, second)
    for name in ('input_manifest.json', 'expected_inventory.json'):
        assert (first / name).read_bytes() == (second / name).read_bytes()


@pytest.mark.parametrize('name,message', [
    ('train/not-approved/part-00000.parquet', 'unapproved pack or split'),
    ('validation/code-go/part-00000.parquet', 'unapproved pack or split'),
    ('train/code-go/notes.parquet', 'incompatible with the sharder'),
    ('train/code-go/part-0.parquet', 'duplicate numeric part index'),
    ('train/code-go/nested/part-00001.parquet', 'expected regular'),
])
def test_incompatible_inputs_are_rejected_before_publication(raw, tmp_path, name, message):
    extra = raw / name
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_bytes((raw / 'train/code-go/part-00000.parquet').read_bytes())
    out = tmp_path / 'bad'
    with pytest.raises(ValueError, match=message):
        run(raw, out)
    assert not out.exists()


def test_missing_required_heldout_pack_is_rejected(raw, tmp_path):
    (raw / 'heldout/code-go/part-00000.parquet').unlink()
    with pytest.raises(ValueError, match='missing required pack/split'):
        run(raw, tmp_path / 'missing')


def test_missing_columns_are_rejected(raw, tmp_path):
    pq.write_table(pa.table({'text': ['missing identifiers']}), raw / 'train/code-go/part-00000.parquet')
    with pytest.raises(ValueError, match='missing columns'):
        run(raw, tmp_path / 'schema')


def test_mismatched_dedup_policy_pin_is_rejected(raw, tmp_path, scope):
    scope['dedup_policy']['sha256'] = '0' * 64
    file = tmp_path / 'altered_scope.json'
    file.write_text(json.dumps(scope))
    with pytest.raises(ValueError, match='dedup.json changed'):
        run(raw, tmp_path / 'pins', file)


def test_frozen_output_cannot_be_overwritten(raw, tmp_path):
    out = tmp_path / 'frozen'
    run(raw, out)
    before = (out / 'expected_inventory.json').read_bytes()
    with pytest.raises(ValueError, match='already exists'):
        run(raw, out)
    assert (out / 'expected_inventory.json').read_bytes() == before


def test_scope_cannot_enable_heldout_sharding(raw, tmp_path, scope):
    scope['split_policy']['shard_splits'].append('heldout')
    file = tmp_path / 'wrong_scope.json'
    file.write_text(json.dumps(scope))
    with pytest.raises(ValueError, match='only train may be sharded'):
        run(raw, tmp_path / 'wrong_split', file)
