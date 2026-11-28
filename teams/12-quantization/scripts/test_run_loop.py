#!/usr/bin/env python3
"""Tests for run_loop.py with a fake quantize_eval.py (no llama.cpp, no torch):  python test_run_loop.py"""
import contextlib, io, json, subprocess, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_loop  # noqa: E402

SCORES = {'bf16': 0.80, 'Q8_0': 0.80, 'Q4_K_M': 0.65}
MINI = {'bf16': dict(mmlu=30.0, arc_challenge=26.0), 'Q8_0': dict(mmlu=30.5, arc_challenge=25.0), 'Q4_K_M': dict(mmlu=28.0, arc_challenge=24.5)}


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); d = Path(self.tmp.name); self.d = d
        for n in ('model.safetensors', 'manifest.json', 'tok.json', 'eval.json'): (d / n).write_text(n)
        self.calls, self.minis = [], []
        self.keep_run = subprocess.run
        subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 0, '', '')   # the guard test of eval_mini
        self.keep = run_loop.sh
        run_loop.sh = self.fake_sh

    def tearDown(self):
        run_loop.sh = self.keep; subprocess.run = self.keep_run; self.tmp.cleanup()

    def fake_sh(self, cmd, **kw):
        cmd = [str(c) for c in cmd]
        if 'run_mini_gguf.py' in cmd[1]:
            fmt = cmd[cmd.index('--format') + 1]; self.minis.append(fmt)
            v = MINI[fmt]; d = Path(cmd[cmd.index('--out') + 1]) / fmt; d.mkdir(parents=True, exist_ok=True)
            recs = [dict(task=k, metric='acc', filter='none', primary=True, value=v[k], stderr=1.5, n_items=100) for k in cmd[cmd.index('--tasks') + 1:cmd.index('--n-gpu-layers')]]
            (d / 'summary.json').write_text(json.dumps(dict(records=recs)))
            return ' '.join(cmd)
        fmt = cmd[cmd.index('--formats') + 1]; self.calls.append(fmt)
        gg = self.d / f'{fmt}.gguf'; gg.write_text(fmt)
        row = dict(file=str(gg), score=SCORES[fmt], score_by_kind=dict(mcq=SCORES[fmt]), size_gb=1.0, bpw=8.0, gen_tok_s=5.0, n_items=20, sha256=fmt + 'sha', format=fmt)
        Path(cmd[cmd.index('--scores-out') + 1]).write_text(json.dumps(dict(formats=[row], export_a1=dict(passed=True), gguf_a3=dict(passed=True))))
        return ' '.join(cmd)

    def loop(self, *extra):
        d = self.d
        argv = ['--weights', str(d / 'model.safetensors'), '--manifest', str(d / 'manifest.json'), '--tokenizer', str(d / 'tok.json'),
                '--eval', str(d / 'eval.json'), '--out', str(d / 'out'), '--formats', 'bf16,Q8_0,Q4_K_M', '--drop-head-bias', '--mini-python', 'py', '--model-note', 'a weak model', *extra]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_loop.main(argv), 0)

    def test_rerun_skips_and_a_changed_stage_reruns_only_what_it_must(self):
        self.loop(); self.assertEqual(self.calls, ['bf16', 'Q8_0', 'Q4_K_M'])
        self.loop(); self.assertEqual(len(self.calls), 3, 'a finished loop reruns nothing')
        run_loop.STAGES['quantize'] += 1
        try:
            self.loop(); self.assertEqual(len(self.calls), 6, 'a new quantize version reruns the format stages')
        finally:
            run_loop.STAGES['quantize'] -= 1
        log = [json.loads(x) for x in (self.d / 'out/loop_log.jsonl').read_text().splitlines()]
        self.assertEqual([x['event'] for x in log if x.get('stage') == 'strip'], ['start', 'done', 'skip', 'skip'])   # strip never reran

    def test_killed_stage_leaves_no_marker_and_the_rerun_resumes_there(self):
        real = self.fake_sh
        def die(cmd, **kw):
            if 'Q8_0' in [str(c) for c in cmd]: raise KeyboardInterrupt
            return real(cmd, **kw)
        run_loop.sh = die
        with self.assertRaises(KeyboardInterrupt): self.loop()
        self.assertTrue((self.d / 'out/stages/q_bf16.json').exists()); self.assertFalse((self.d / 'out/stages/q_Q8_0.json').exists())
        run_loop.sh = real; self.calls.clear(); self.loop()
        self.assertEqual(self.calls, ['Q8_0', 'Q4_K_M'])

    def test_killed_mini_stage_resumes_there_and_keeps_its_gguf(self):
        real = self.fake_sh
        def die(cmd, **kw):
            if 'run_mini_gguf.py' in str(cmd[1]) and 'Q8_0' in [str(c) for c in cmd]: raise KeyboardInterrupt
            return real(cmd, **kw)
        run_loop.sh = die
        with self.assertRaises(KeyboardInterrupt): self.loop()
        self.assertTrue((self.d / 'Q8_0.gguf').exists()); self.assertFalse((self.d / 'out/stages/mini_Q8_0.json').exists())
        run_loop.sh = real; self.calls.clear(); self.minis.clear(); self.loop()
        self.assertEqual((self.calls, self.minis), (['Q4_K_M'], ['Q8_0', 'Q4_K_M']))   # bf16 and both q stages of Q8_0 / bf16 skipped

    def test_gap_and_label(self):
        self.loop()
        g = json.loads((self.d / 'out/gap.json').read_text())
        self.assertEqual([r['gap'] for r in g['formats']], [0.0, 0.0, -0.15])
        self.assertIn('RELAXED: --drop-head-bias', g['guards']); self.assertIn('no watcher score given', g['watcher']['status'])

    def test_mini_stage_per_format_gap_label_keep_then_delete_and_restart(self):
        self.loop()
        self.assertEqual(self.minis, ['bf16', 'Q8_0', 'Q4_K_M'])
        self.assertTrue((self.d / 'bf16.gguf').exists()); self.assertFalse((self.d / 'Q8_0.gguf').exists())   # bf16 stays, a quantized GGUF goes after its mini stage
        g = json.loads((self.d / 'out/gap.json').read_text())
        q = g['eval_mini']['mmlu']['Q4_K_M']
        self.assertEqual((q['gap'], q['gap_se_unpaired']), (-2.0, 2.1213)); self.assertIsNone(g['eval_mini']['mmlu']['bf16']['gap'])
        md = (self.d / 'out/gap.md').read_text()
        self.assertIn('> a weak model', md); self.assertIn('NOT eval-mini', md); self.assertIn('| arc_challenge | acc | Q8_0 |', md)
        self.loop(); self.assertEqual(len(self.minis), 3, 'a finished loop reruns no mini stage')
        self.loop('--mini-tasks', 'mmlu'); self.assertEqual(len(self.minis), 6, 'new tasks rerun the mini stages only')
        self.assertEqual(self.calls, ['bf16', 'Q8_0', 'Q4_K_M', 'Q8_0', 'Q4_K_M'])   # the deleted GGUFs are rebuilt from bf16, which is not re-made

    def test_no_note_without_the_option(self):
        self.loop('--model-note', ''); self.assertNotIn('> ', (self.d / 'out/gap.md').read_text().split('# Gap table')[1][:10])

    def test_changed_checkpoint_reruns_everything(self):
        self.loop(); (self.d / 'model.safetensors').write_text('new weights'); self.loop()
        self.assertEqual(len(self.calls), 6)


if __name__ == '__main__':
    unittest.main(verbosity=1)
