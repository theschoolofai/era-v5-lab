"""D3 public initial-claim contract: actual filesystem CAS, no lifetime lock."""
import json
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

TEAM = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(TEAM))
from ckpt.ckpt import Checkpointer, CheckpointError, FencedError
from ckpt.store import Conflict

IDENTITY = 'a' * 64
parametrize = pytest.mark.parametrize


@pytest.fixture
def attempts(tmp_path):
    def new():
        return Checkpointer('run', str(tmp_path / 'local'), str(tmp_path / 'store'))
    return new


def test_fresh_then_explicit_recovery_and_stale_writer_fencing(attempts):
    old = attempts()
    assert old.claim_initial(IDENTITY) == 1
    before = old.store.get_json_ver('latest.json')
    new = attempts()
    with pytest.raises(CheckpointError):
        new.claim_initial(IDENTITY)
    assert old.store.get_json_ver('latest.json') == before
    assert new.claim_initial(IDENTITY, allow_takeover=True) == 2
    with pytest.raises(Conflict):
        old.store.put_json_if('latest.json', {'path': 'old-writer'}, old._ptr_ver)
    assert not (Path(old.store.root) / '.g5-owner.lock').exists()


@parametrize('history', ['', '{"step":0,"path":"main/step_0-e1"}\n', 'invalid-json\n'])
def test_committed_pointer_or_history_refused_without_fencing_owner(attempts, history):
    owner = attempts()
    owner.claim_initial(IDENTITY)
    if history:
        Path(owner.store.root, 'commits.jsonl').write_text(history)
    else:
        owner.store.put_json('latest.json', dict(owner.store.get_json('latest.json'),
                                               path='main/step_0-e1', step=0, branch='main'))
    before = owner.store.get_json_ver('latest.json')
    new = attempts()
    with pytest.raises(CheckpointError):
        new.claim_initial(IDENTITY, allow_takeover=True)
    assert owner.store.get_json_ver('latest.json') == before
    assert new.epoch is None


@parametrize('raw', ['{}', 'null', '[]', 'invalid-json',
    '{"epoch":true,"path":null,"step":null,"branch":null}',
    '{"epoch":1,"path":null,"step":null,"branch":null}'])
def test_invalid_or_identityless_claims_hold(attempts, raw):
    new = attempts()
    pointer = Path(new.store.root, 'latest.json')
    pointer.write_text(raw)
    with pytest.raises(CheckpointError):
        new.claim_initial(IDENTITY, allow_takeover=True)
    assert pointer.read_text() == raw
    assert new.epoch is None


def test_identity_mismatch_and_missing_claim_hold(attempts):
    new = attempts()
    with pytest.raises(CheckpointError):
        new.claim_initial(IDENTITY, allow_takeover=True)
    new.claim_initial(IDENTITY)
    other = attempts()
    before = new.store.get_json_ver('latest.json')
    with pytest.raises(CheckpointError):
        other.claim_initial('b' * 64, allow_takeover=True)
    assert new.store.get_json_ver('latest.json') == before


@parametrize('commit', [False, True])
def test_competing_claim_or_pointer_publication_wins_cas_race(attempts, commit):
    old = attempts()
    old.claim_initial(IDENTITY)
    new = attempts()
    store = new.store
    write = store.put_json_if
    calls = []
    def race(key, value, version):
        calls.append(value)
        winner = dict(value, epoch=3)
        if commit:
            winner.update(path='main/step_0-e1', step=0, branch='main')
        write(key, winner, version)
        return write(key, value, version)
    with patch.object(store, 'put_json_if', race), pytest.raises(FencedError):
        new.claim_initial(IDENTITY, allow_takeover=True)
    assert len(calls) == 1
    assert new.epoch is None
    assert store.get_json('latest.json')['epoch'] == 3
    if commit:
        assert store.get_json('latest.json')['path'] == 'main/step_0-e1'
        assert not Path(store.root, 'commits.jsonl').exists()


def test_legacy_d3_identity_is_accepted_without_preserving_lock_markers(attempts):
    new = attempts()
    new.store.put_json('latest.json', {'epoch': 2, 'path': None, 'step': None, 'branch': None,
        'g5_identity_sha256': IDENTITY, 'g5_owner_protocol': 'g5-local-owner-lock/1', 'g5_owner_epoch': 2})
    assert new.claim_initial(IDENTITY, allow_takeover=True) == 3
    claim = new.store.get_json('latest.json')
    assert claim['identity_sha256'] == IDENTITY
    assert not any(key.startswith('g5_owner') for key in claim)


def test_unavailable_metadata_and_object_store_hold(attempts):
    new = attempts()
    with patch('builtins.open', side_effect=PermissionError('unavailable')), pytest.raises(CheckpointError):
        new.claim_initial(IDENTITY)
    assert new.epoch is None
    with patch.object(new.store, 'kind', 's3'), pytest.raises(CheckpointError):
        new.claim_initial(IDENTITY)


@parametrize('operation', ['get_text', 'put_json_if'])
def test_history_read_or_claim_write_failure_preserves_existing_owner(attempts, operation):
    owner = attempts()
    owner.claim_initial(IDENTITY)
    before = owner.store.get_json_ver('latest.json')
    new = attempts()
    with patch.object(new.store, operation, side_effect=PermissionError('unavailable')):
        with pytest.raises(CheckpointError):
            new.claim_initial(IDENTITY, allow_takeover=True)
    assert new.epoch is None
    assert owner.store.get_json_ver('latest.json') == before
