"""Minimal D4: explicit-step restore through G7's existing checkpoint contract."""
import copy
import itertools
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

from test_week2_model import TEAM, fixture
import train_week2


class RollbackTests(unittest.TestCase):
    def test_invalid_options_fail_before_input_loading(self):
        common = ['trainer']
        for name in ('config', 'tokenizer', 'byte-table', 'train-data', 'heldout-data', 'out'):
            common.extend([f'--{name}', 'unused'])
        for flags in (
            ['--from-step', '1'], ['--resume', 'unused', '--from-step', '0'],
            ['--resume-committed', '--from-step', '-1'],
            ['--resume-committed', '--from-step', '0', '--checkpoint-at-start'],
            ['--resume-committed', '--from-step', '2', '--logger-factory', 'g5_adapter:make_writer'],
            ['--skip', '1'], ['--branch', 'fork'], ['--allow-env-change'], ['--recover-precommit'],
        ):
            with self.subTest(flags=flags), patch.object(sys, 'argv', common + flags), patch.object(train_week2, 'load_runtime') as load:
                with self.assertRaises(SystemExit) as failure:
                    train_week2.main()
                self.assertEqual(failure.exception.code, 2)
                load.assert_not_called()

    def test_real_explicit_step_adamw_and_muon(self):
        for optimizer in ('adamw', 'muon'):
            with self.subTest(optimizer=optimizer):
                self.check_rollback(optimizer)

    @unittest.skipUnless(hasattr(train_week2, 'claim_for_start'), 'Combined D3 initialization adapter required')
    def test_initialization_then_explicit_step_restore(self):
        for optimizer in ('adamw', 'muon'):
            with self.subTest(optimizer=optimizer):
                self.check_rollback(optimizer, initial_recovery=True)

    @unittest.skipUnless(torch.cuda.is_available(), 'CUDA unavailable')
    def test_real_explicit_step_cuda(self):
        self.check_rollback('adamw', device='cuda')

    @unittest.skipUnless(torch.cuda.is_available(), 'CUDA unavailable')
    def test_real_kas_bf16_cuda_explicit_step(self):
        from test_week2_kas_v2 import ModelIntegration
        helper = ModelIntegration()
        self.addCleanup(helper.doCleanups)
        cfg, rows, lengths, _ = helper.model()
        cfg['run']['dtype'] = 'bf16'
        for optimizer in ('adamw', 'muon'):
            with self.subTest(optimizer=optimizer), patch(
                __name__ + '.fixture', side_effect=lambda: (copy.deepcopy(cfg), rows, lengths)
            ):
                self.check_rollback(optimizer, device='cuda', initial_recovery=hasattr(train_week2, 'claim_for_start'))

    def check_rollback(self, optimizer, device='cpu', initial_recovery=False):
        cfg, byte_rows, _ = fixture()
        cfg['model'].update(ke_max_pos=byte_rows.shape[1], mtp_weight=0.0)
        cfg['optim'].update(name=optimizer, muon_lr=0.01 if optimizer == 'muon' else None)
        artifacts = SimpleNamespace(
            bytes=byte_rows, lengths=np.ones(len(byte_rows), dtype=np.int16),
            pos_dim=byte_rows.shape[1], bos_id=0, pad_id=1,
            encode=lambda text: [ord(c) - ord('a') + 2 for c in text],
            identity=lambda: {}, normalize_input=False,
        )
        with TemporaryDirectory() as temp:
            root = Path(temp)
            train, val = root/'train.jsonl', root/'val.jsonl'
            train.write_text('{"text":"aaaa"}\n{"text":"aaa"}\n')
            val.write_text('{"text":"bbbb"}\n')
            common = ['trainer', '--config', 'fixture.yaml', '--tokenizer', 'fixture.json',
                      '--byte-table', 'fixture.npz', '--train-data', str(train), '--heldout-data', str(val),
                      '--smoke', '--smoke-steps', '5', '--smoke-batch-size', '1', '--device', device]
            if device == 'cuda':
                common.extend(['--watchdog-s', '60'])
            committed = ['--checkpoint-store', str(root/'store'), '--run-id', 'rollback',
                         '--checkpoint-interval-s', '600']
            resume = [*committed, '--resume-committed']
            explicit = [*resume, '--from-step', '2']
            def run(name, *flags):
                out = root/name
                clock = itertools.count(0, 300)
                with patch.object(sys, 'argv', [*common, '--out', str(out), *flags]), patch.object(train_week2, 'checkpoint_clock', side_effect=lambda: next(clock)):
                    train_week2.main()
                return out
            def summary(out):
                return json.loads((out/'summary.json').read_text())
            def entries():
                return [json.loads(line) for line in (root/'store'/'rollback'/'commits.jsonl').read_text().splitlines()]
            def refuse(name, flags, cause=None):
                with patch.object(train_week2, 'set_lr_scale') as update, patch.object(Checkpointer, 'save') as save, self.assertRaises(SystemExit) as failure:
                    run(name, *flags)
                self.assertEqual(failure.exception.code, 78)
                update.assert_not_called()
                save.assert_not_called()
                self.assertFalse((root/name/'checkpoint.pt').exists())
                self.assertFalse((root/name/'summary.json').exists())
                if cause:
                    self.assertIn(cause, (root/name/'manifest.json').read_text())
            with (
                patch.object(train_week2, 'load_runtime', return_value=cfg),
                patch.object(train_week2, 'Artifacts', return_value=artifacts),
                patch.object(sys, 'path', [str(TEAM.parent/'07-infrastructure'), *sys.path]),
                patch.dict(os.environ, {'V5_RUNS_DIR': str(root/'notes')}),
            ):
                from ckpt.ckpt import Checkpointer, FencedError
                baseline = run('baseline')
                if initial_recovery:
                    def interrupted_save(checkpointer, *args, **kwargs):
                        checkpointer.claim()
                        raise SystemExit(9)
                    with patch.object(Checkpointer, 'save', interrupted_save), self.assertRaises(SystemExit) as interrupted:
                        run('interrupted', *committed)
                    self.assertEqual(interrupted.exception.code, 9)
                first = run('first', *committed, '--checkpoint-at-start', '--stop-after', '2')
                run('later', *resume)
                store = root/'store'/'rollback'
                source = next(entry for entry in entries() if entry['step'] == 2)
                source_manifest = (store/source['path']/'MANIFEST.json').read_bytes()
                previous = entries()
                # Restoring an already committed state does not publish another copy.
                with patch.object(Checkpointer, 'save') as save, patch.object(train_week2, 'set_lr_scale') as update:
                    stopped = run('no-update', *explicit, '--stop-after', '2')
                save.assert_not_called()
                update.assert_not_called()
                self.assertEqual(entries(), previous)
                self.assertEqual(summary(stopped)['team7_checkpoint_path'], source['path'])
                checkpoint = torch.load(stopped/'checkpoint.pt', map_location='cpu', weights_only=False)
                first_checkpoint = torch.load(first/'checkpoint.pt', map_location='cpu', weights_only=False)
                self.assertEqual(checkpoint['step'], 2)
                self.assertEqual(checkpoint['trace'], first_checkpoint['trace'])
                record = summary(stopped)['rollback_events'][-1]
                self.assertEqual(record['from_path'], source['path'])
                self.assertEqual(record['tokens'], sum(row.get('train/scored_tokens', 0) for row in checkpoint['rows']))
                self.assertEqual(record['branch'], source['branch'])
                self.assertFalse(record['replay_guaranteed'])
                self.assertNotIn('skip_batches', record)
                # Restore an older step despite newer commits; losses/model match uninterrupted training.
                rolled = run('rolled', *explicit)
                self.assertEqual((rolled/'losses.txt').read_bytes(), (baseline/'losses.txt').read_bytes())
                self.assertEqual(summary(rolled)['final_model_sha256'], summary(baseline)['final_model_sha256'])
                self.assertFalse(summary(rolled)['eligible_for_quality_comparison'])
                self.assertEqual((store/source['path']/'MANIFEST.json').read_bytes(), source_manifest)
                self.assertEqual(summary(rolled)['run_id'], 'rollback')
                self.assertEqual({entry['branch'] for entry in entries()}, {'main'})
                manifest = json.loads((rolled/'manifest.json').read_text())
                self.assertEqual(manifest['status'], 'DRAFT_ROLLBACK_NOT_A_QUALITY_RESULT')
                self.assertEqual(manifest['team7_checkpoint']['restore']['from_path'], source['path'])
                rows = [json.loads(line) for line in (rolled/'metrics.jsonl').read_text().splitlines()]
                self.assertEqual([row['step'] for row in rows], list(range(6)))
                self.assertEqual(len((rolled/'losses.txt').read_text().splitlines()), 5)
                inherited = run('inherited', *resume)
                self.assertEqual(summary(inherited)['rollback_events'], summary(rolled)['rollback_events'])
                native = run('native', '--resume', str(rolled/'checkpoint.pt'))
                self.assertEqual(summary(native)['rollback_events'], summary(rolled)['rollback_events'])
                for name, flags in (('committed-logger', resume), ('native-logger', ['--resume', str(rolled/'checkpoint.pt')])):
                    with self.assertRaises(SystemExit) as failure:
                        run(name, *flags, '--logger-factory', 'g5_adapter:make_writer')
                    self.assertEqual(failure.exception.code, 2)
                zero = run('zero', *resume, '--from-step', '0')
                self.assertEqual(summary(zero)['final_model_sha256'], summary(baseline)['final_model_sha256'])
                self.assertEqual((zero/'losses.txt').read_bytes(), (baseline/'losses.txt').read_bytes())
                refuse('missing', [*resume, '--from-step', '999'])
                with patch.object(Checkpointer, 'restore', side_effect=FencedError('new owner')):
                    refuse('fenced', explicit)
                with patch.object(artifacts, 'identity', return_value={'changed': True}):
                    refuse('identity', explicit)
                import ckpt.ckpt as ckpt_module
                original_env = ckpt_module.env_manifest
                def changed_env(*args, **kwargs):
                    result = original_env(*args, **kwargs)
                    result['image_digest'] = 'changed-image'
                    return result
                with patch.object(ckpt_module, 'env_manifest', changed_env):
                    refuse('environment', explicit)
                # A corrupt explicitly selected step must not fall back to another intact commit.
                selected = [entry for entry in entries() if entry['step'] == 2][-1]
                extra = store/selected['path']/'extra_rank0.json'
                extra.write_bytes(extra.read_bytes() + b'corrupt')
                refuse('corrupt', explicit)
