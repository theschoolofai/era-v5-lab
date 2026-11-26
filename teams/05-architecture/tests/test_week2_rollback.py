"""Draft rollback through G7's real local checkpoint store."""
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
from week2.data import BatchStream
from week2.team7_checkpoints import CheckpointProgress


class RollbackTests(unittest.TestCase):
    def test_skip_matches_discarded_batches_across_epochs_without_materializing(self):
        dataset = SimpleNamespace(windows=list(range(7)))
        dataset.batch = lambda ids, device: ids
        for count in (0, 1, 5, 20):
            reference = BatchStream(dataset, 3, 42)
            skipped = BatchStream(dataset, 3, 42)
            reference.next('cpu')
            skipped.next('cpu')
            for _ in range(count):
                reference.next('cpu')
            CheckpointProgress(skipped, 'identity', 'run').add_skip(count)
            self.assertEqual(reference.next('cpu'), skipped.next('cpu'))
            self.assertTrue(torch.equal(reference.generator.get_state(), skipped.generator.get_state()))
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                skipped.advance_batches(bad)

    def test_g5_identity_cannot_be_overridden(self):
        progress = CheckpointProgress(None, 'current', 'run')
        with self.assertRaisesRegex(ValueError, 'identity changed'):
            progress.load_state_dict({'identity_sha256': 'old', 'run_id': 'run'})

    def test_invalid_options_fail_before_input_loading(self):
        common = ['trainer']
        for name in ('config', 'tokenizer', 'byte-table', 'train-data', 'heldout-data', 'out'):
            common.extend([f'--{name}', 'unused'])
        for flags in (
            ['--from-step', '1'], ['--skip', '-1'], ['--from-step', '-1'],
            ['--resume-committed', '--skip', '1'],
            ['--resume-committed', '--branch', '../escape'],
            ['--resume-committed', '--branch', 'fork', '--logger-factory', 'g5_adapter:make_writer'],
        ):
            with self.subTest(flags=flags), patch.object(sys, 'argv', common + flags), patch.object(train_week2, 'load_runtime') as load:
                with self.assertRaises(SystemExit) as failure:
                    train_week2.main()
                self.assertEqual(failure.exception.code, 2)
                load.assert_not_called()

    def test_real_rollback_adamw_and_muon(self):
        for optimizer in ('adamw', 'muon'):
            with self.subTest(optimizer=optimizer):
                self.check_rollback(optimizer)

    @unittest.skipUnless(torch.cuda.is_available(), 'CUDA unavailable')
    def test_real_rollback_cuda(self):
        self.check_rollback('adamw', device='cuda')

    @unittest.skipUnless(torch.cuda.is_available(), 'CUDA unavailable')
    def test_real_kas_bf16_cuda_rollback(self):
        from test_week2_kas_v2 import ModelIntegration
        helper = ModelIntegration()
        self.addCleanup(helper.doCleanups)
        cfg, rows, lengths, _ = helper.model()
        cfg['run']['dtype'] = 'bf16'
        for optimizer in ('adamw', 'muon'):
            with self.subTest(optimizer=optimizer), patch(
                __name__ + '.fixture', side_effect=lambda: (copy.deepcopy(cfg), rows, lengths)
            ):
                self.check_rollback(optimizer, device='cuda')

    def check_rollback(self, optimizer, device='cpu'):
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
            committed = ['--checkpoint-store', str(root/'store'), '--run-id', 'rollback',
                         '--checkpoint-interval-s', '600']
            resume = [*committed, '--resume-committed']
            def run(name, *flags):
                out = root/name
                clock = itertools.count(0, 300)
                with patch.object(sys, 'argv', [*common, '--out', str(out), *flags]), patch.object(train_week2, 'checkpoint_clock', side_effect=lambda: next(clock)):
                    train_week2.main()
                return out
            def summary(out):
                return json.loads((out/'summary.json').read_text())
            with (
                patch.object(train_week2, 'load_runtime', return_value=cfg),
                patch.object(train_week2, 'Artifacts', return_value=artifacts),
                patch.object(sys, 'path', [str(TEAM.parent/'07-infrastructure'), *sys.path]),
                patch.dict(os.environ, {'V5_RUNS_DIR': str(root/'notes')}),
            ):
                from ckpt.ckpt import Checkpointer
                baseline = run('baseline')
                first = run('first', *committed, '--checkpoint-at-start', '--stop-after', '2')
                # Add a later checkpoint, then explicitly roll back without rewriting history.
                run('later', *resume)
                store = root/'store'/'rollback'
                source = next(json.loads(line) for line in (store/'commits.jsonl').read_text().splitlines() if json.loads(line)['step'] == 2)
                rolled = run('rolled', *resume, '--from-step', '2', '--branch', 'rollback2')
                self.assertEqual((rolled/'losses.txt').read_bytes(), (baseline/'losses.txt').read_bytes())
                self.assertEqual(summary(rolled)['final_model_sha256'], summary(baseline)['final_model_sha256'])
                self.assertFalse(summary(rolled)['eligible_for_quality_comparison'])
                events = summary(rolled)['rollback_events']
                self.assertEqual(events[0]['from_path'], source['path'])
                self.assertEqual(events[0]['skip_batches'], 0)
                rows = [json.loads(line) for line in (rolled/'metrics.jsonl').read_text().splitlines()]
                self.assertEqual([r['step'] for r in rows], list(range(6)))
                self.assertEqual(len((rolled/'losses.txt').read_text().splitlines()), 5)
                # Zero-update forks must still publish a checkpoint on the requested branch.
                fork = run('no-update', *resume, '--from-step', '2', '--branch', 'fork2', '--skip', '3', '--stop-after', '2')
                latest = json.loads((store/'latest.json').read_text())
                self.assertEqual(latest['branch'], 'fork2')
                self.assertEqual(latest['step'], 2)
                self.assertEqual(summary(fork)['team7_checkpoint_path'], latest['path'])
                source_manifest = json.loads((store/source['path']/'MANIFEST.json').read_text())
                fork_manifest = json.loads((store/latest['path']/'MANIFEST.json').read_text())
                self.assertEqual(fork_manifest['tokens'], source_manifest['tokens'])
                # Compare skipping against native restore with the same sampler-only advance.
                original_load = BatchStream.load_state_dict
                def load_and_skip(stream, state):
                    original_load(stream, state)
                    stream.advance_batches(3)
                with patch.object(BatchStream, 'load_state_dict', load_and_skip):
                    reference = run('skip-reference', '--resume', str(first/'checkpoint.pt'))
                skipped = run('skipped', *resume)
                self.assertEqual(summary(skipped)['final_model_sha256'], summary(reference)['final_model_sha256'])
                self.assertEqual((skipped/'losses.txt').read_bytes(), (reference/'losses.txt').read_bytes())
                self.assertEqual(summary(skipped)['rollback_events'], summary(fork)['rollback_events'])
                self.assertEqual(json.loads((skipped/'manifest.json').read_text())['status'], 'DRAFT_ROLLBACK_NOT_A_QUALITY_RESULT')
                with patch.object(Checkpointer, 'save') as save, self.assertRaises(SystemExit) as failure:
                    run('lineage-logger-denied', *resume, '--logger-factory', 'g5_adapter:make_writer')
                self.assertEqual(failure.exception.code, 2)
                save.assert_not_called()
                # Step-zero rollback preserves lazy optimizer state and exact unskipped replay.
                zero = run('zero', *resume, '--from-step', '0', '--branch', 'zero')
                self.assertEqual(summary(zero)['final_model_sha256'], summary(baseline)['final_model_sha256'])
                for flags in (['--from-step', '999', '--branch', 'missing'], ['--from-step', '2', '--branch', 'fork2']):
                    with patch.object(Checkpointer, 'save') as save, self.assertRaises(SystemExit) as failure:
                        run(flags[-1]+'-failure', *resume, *flags)
                    self.assertEqual(failure.exception.code, 78)
                    save.assert_not_called()
                # G7 environment override is usable, but never bypasses G5 identity.
                import ckpt.ckpt as ckpt_module
                original_env = ckpt_module.env_manifest
                def changed_env(*args, **kwargs):
                    result = original_env(*args, **kwargs)
                    result['image_digest'] = 'changed-image'
                    return result
                with patch.object(ckpt_module, 'env_manifest', changed_env):
                    with self.assertRaises(SystemExit) as failure:
                        run('env-denied', *resume, '--from-step', '2', '--branch', 'env-denied')
                    self.assertEqual(failure.exception.code, 78)
                    allowed = run('env-allowed', *resume, '--from-step', '2', '--branch', 'env-allowed', '--allow-env-change', '--stop-after', '2')
                self.assertIn('image_digest', summary(allowed)['rollback_events'][-1]['env_override'])
                with patch.object(artifacts, 'identity', return_value={'changed': True}), self.assertRaises(SystemExit) as failure:
                    run('identity-denied', *resume, '--from-step', '2', '--branch', 'identity-denied', '--allow-env-change')
                self.assertEqual(failure.exception.code, 78)
                # Explicit selection must not fall back to a different intact checkpoint.
                selected = [json.loads(line) for line in (store/'commits.jsonl').read_text().splitlines() if json.loads(line)['step'] == 2][-1]
                extra = store/selected['path']/'extra_rank0.json'
                extra.write_bytes(extra.read_bytes() + b'corrupt')
                with patch.object(Checkpointer, 'save') as save, self.assertRaises(SystemExit) as failure:
                    run('corrupt', *resume, '--from-step', '2', '--branch', 'corrupt')
                self.assertEqual(failure.exception.code, 78)
                save.assert_not_called()
