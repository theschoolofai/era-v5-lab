#!/usr/bin/env python3
"""Tests for the checkpoint path of quantize_eval.py that need no llama.cpp:  python test_quantize_eval.py

The whole flow (export, convert, quantize, serve, score) is tested by running it on make_random_checkpoint.py output.
"""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import quantize_eval as q  # noqa: E402


def tokenizer(path: Path, n: int):
    path.write_text(json.dumps({'model': {'vocab': {f't{i}': i for i in range(n - 1)}},
                                'added_tokens': [{'id': n - 1, 'content': '<|endoftext|>'}]}), encoding='utf-8')
    return path


class CheckpointPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def hf_folder(self, vocab):
        d = self.dir / 'model'; d.mkdir()
        (d / 'config.json').write_text(json.dumps({'vocab_size': vocab}), encoding='utf-8')
        (d / 'model.safetensors').write_bytes(b'weights')
        (d / 'tokenizer.json').write_text('{"old": true}', encoding='utf-8')
        (d / 'vocab.json').write_text('{}', encoding='utf-8')
        return d

    def test_stage_replaces_the_tokenizer_and_keeps_the_weights(self):
        tok = tokenizer(self.dir / 'tokenizer.json', 10)
        out = q.stage_tokenizer(self.hf_folder(10), tok, self.dir / 'staged', '<|begin_of_text|>', '<|endoftext|>')
        self.assertEqual((out / 'tokenizer.json').read_bytes(), tok.read_bytes())
        self.assertEqual((out / 'model.safetensors').read_bytes(), b'weights')
        self.assertFalse((out / 'vocab.json').exists())      # the model's own tokenizer files are left out
        self.assertEqual(json.loads((out / 'tokenizer_config.json').read_text())['eos_token'], '<|endoftext|>')

    def test_stage_refuses_a_tokenizer_bigger_than_the_table(self):
        with self.assertRaises(SystemExit) as e:
            q.stage_tokenizer(self.hf_folder(9), tokenizer(self.dir / 'tokenizer.json', 10), self.dir / 'staged', 'b', 'e')
        self.assertIn('refusing', str(e.exception))

    def test_weights_file_of_a_checkpoint(self):
        run = self.dir / 'run'; run.mkdir()
        (run / 'checkpoint.pt').write_bytes(b'x')
        self.assertEqual(q.checkpoint_weights(run), run / 'checkpoint.pt')
        self.assertEqual(q.checkpoint_weights(run / 'checkpoint.pt'), run / 'checkpoint.pt')
        with self.assertRaises(SystemExit):
            q.checkpoint_weights(self.dir)

    def test_wrong_tokenizer_hash_stops_before_any_work(self):
        tok = tokenizer(self.dir / 'tokenizer.json', 10)
        r = subprocess.run([sys.executable, str(HERE / 'quantize_eval.py'), '--checkpoint', str(self.dir), '--tokenizer', str(tok),
                            '--work', str(self.dir / 'work'), '--llama-bin', str(self.dir / 'no-such-dir')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn('refusing', r.stderr)
        self.assertIn(q.FROZEN_TOKENIZER_SHA256, r.stderr)   # the default is the frozen tokenizer
        self.assertFalse((self.dir / 'work' / 'hf').exists())


class TargetTests(unittest.TestCase):
    """--target reaches export_hf.py, an ERNIE run has its own file names, and a resumed run never reuses the other export."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / 'run').mkdir(); (self.dir / 'run' / 'model.safetensors').write_bytes(b'w')
        self.real_run, self.cmds = q.run, []

    def tearDown(self):
        q.run = self.real_run
        self.tmp.cleanup()

    def args(self, target, **kw):
        return SimpleNamespace(**dict(dict(checkpoint=str(self.dir / 'run' / 'model.safetensors'), tokenizer='tok.json', bos='b',
                                           eos='e', verify=16, spec='manifest.json', drop_router_bias=False, drop_head_bias=True,
                                           target=target), **kw))

    def fake_export(self, cmd, **kw):   # stands in for export_hf.py: records the command and writes the report last
        self.cmds.append([str(c) for c in cmd])
        out = Path(cmd[cmd.index('--out') + 1]); out.mkdir(parents=True)
        (out / 'export_report.json').write_text(json.dumps({'target': cmd[cmd.index('--target') + 1]}), encoding='utf-8')

    def test_target_is_passed_to_export_hf(self):
        q.run = self.fake_export
        for target in (q.GRANITE, q.ERNIE):
            _, report = q.prepare_checkpoint(self.args(target), 'py', self.dir / 'work', q.run_name('m', 'f' * 64, target))
            cmd = self.cmds[-1]
            self.assertEqual(cmd[cmd.index('--target') + 1], target)
            self.assertEqual(report['target'], target)
        self.assertEqual(len(self.cmds), 2)   # two exports, two folders

    def test_ernie_files_have_their_own_name_and_granite_names_are_unchanged(self):
        self.assertEqual(q.run_name('dryrun2-1234', 'ab' * 32), 'dryrun2-1234-abababab')
        self.assertEqual(q.run_name('dryrun2-1234', 'ab' * 32, q.GRANITE), 'dryrun2-1234-abababab')
        self.assertEqual(q.run_name('dryrun2-1234', 'ab' * 32, q.ERNIE), 'dryrun2-1234-abababab-ernie')

    def test_a_resumed_run_refuses_an_export_of_the_other_target(self):
        q.run = self.fake_export
        q.prepare_checkpoint(self.args(q.GRANITE), 'py', self.dir / 'work', 'same')
        with self.assertRaises(SystemExit) as e:   # the -ernie suffix keeps quantize_eval's own runs apart, so this is
            q.prepare_checkpoint(self.args(q.ERNIE), 'py', self.dir / 'work', 'same')   # an export put there by hand
        self.assertIn('granite_moe_shared export', str(e.exception))
        self.assertEqual(len(self.cmds), 1)   # nothing was exported again
        _, report = q.prepare_checkpoint(self.args(q.GRANITE), 'py', self.dir / 'work', 'same')   # same target: reused
        self.assertEqual((len(self.cmds), report['target']), (1, q.GRANITE))

    def test_a_report_without_target_is_a_granite_export(self):   # export_report.json written before #838
        q.run = self.fake_export
        out = self.dir / 'work' / 'hf' / 'old'; out.mkdir(parents=True)
        (out / 'export_report.json').write_text('{"parameters": 1}', encoding='utf-8')
        _, report = q.prepare_checkpoint(self.args(q.GRANITE), 'py', self.dir / 'work', 'old')   # a Granite run reuses it
        self.assertEqual((self.cmds, report), ([], {'parameters': 1}))
        with self.assertRaises(SystemExit) as e:                                                # an ERNIE run refuses it
            q.prepare_checkpoint(self.args(q.ERNIE), 'py', self.dir / 'work', 'old')
        self.assertIn('granite_moe_shared export', str(e.exception))

    def test_runs_csv_note_comes_from_the_export_report(self):
        self.assertEqual([q.export_note(x) for x in (None, {}, {'target': q.GRANITE}, {'target': q.ERNIE})],
                         ['', '', '', 'export=ernie4_5_moe'])

    def refused(self, *extra, checkpoint=None):
        r = subprocess.run([sys.executable, str(HERE / 'quantize_eval.py'), '--checkpoint', str(checkpoint or self.dir / 'run'),
                            '--target', 'ernie4_5_moe', *extra, '--work', str(self.dir / 'work'), '--llama-bin', str(self.dir / 'no-such-dir')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertFalse((self.dir / 'work' / 'hf').exists())
        return r.stderr

    def test_ernie_with_drop_router_bias_stops_before_any_work(self):
        self.assertIn('ERNIE 4.5 MoE keeps the router bias', self.refused('--drop-router-bias', '--drop-head-bias'))

    def test_ernie_without_drop_head_bias_stops_before_any_work(self):   # llama.cpp cannot convert the use_bias=True folder
        self.assertIn('needs --drop-head-bias', self.refused())

    def test_ernie_on_a_hugging_face_folder_stops_before_any_work(self):   # nothing would be exported, so --target would be ignored
        hf = self.dir / 'hf-folder'; hf.mkdir(); (hf / 'config.json').write_text('{}', encoding='utf-8')
        self.assertIn('--target is for a G5 checkpoint', self.refused('--drop-head-bias', checkpoint=hf))


class OfflineTagTests(unittest.TestCase):
    """A prepared --work folder answers llama_tag without git ls-remote (a job has no network)."""
    def test_checkout_of_the_binaries_commit_gives_the_tag_without_the_network(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / 'llama.cpp-b123'; src.mkdir()
            git = lambda *a: subprocess.run(['git', '-C', str(src), *a], capture_output=True, text=True, check=True).stdout.strip()
            git('init', '-q'); git('-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '--allow-empty', '-m', 'x')
            commit = git('rev-parse', 'HEAD')
            real_run, calls = q.subprocess.run, []
            q.subprocess.run = lambda cmd, *a, **k: (calls.append(cmd), real_run(cmd, *a, **k))[1] if cmd[1] != 'ls-remote' else (_ for _ in ()).throw(AssertionError('network'))
            try:
                self.assertEqual(q.llama_tag(123, commit[:9], d), 'b123')
                with self.assertRaises(AssertionError):   # another commit: falls through to ls-remote
                    q.llama_tag(123, 'deadbeef', d)
            finally:
                q.subprocess.run = real_run


if __name__ == '__main__':
    unittest.main(verbosity=1)
