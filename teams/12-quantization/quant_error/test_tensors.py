#!/usr/bin/env python3
"""Tests for per-tensor dequantization error:  python test_tensors.py"""
import re, sys, tempfile, unittest
from pathlib import Path

import numpy as np
import gguf
from gguf import GGMLQuantizationType as QT

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tensors as t  # noqa: E402


def write_gguf(path: Path, items, arch: str = 'llama', tokens: list[str] | None = None):
    """items: [(name, float32 array, GGML type)]; quantizes each array to its type and writes a tiny GGUF with that
    general.architecture and, if given, that tokenizer.ggml.tokens list."""
    w = gguf.GGUFWriter(str(path), arch)
    if tokens is not None:
        w.add_token_list(tokens)
    for name, arr, qtype in items:
        if qtype in (QT.F32, QT.F16):
            w.add_tensor(name, gguf.quants.quantize(arr, qtype))
        else:
            w.add_tensor(name, gguf.quants.quantize(arr, qtype), raw_dtype=qtype)
    w.write_header_to_file()
    w.write_kv_data_to_file()
    w.write_tensors_to_file()
    w.close()


RNG = np.random.default_rng(0)
A, B, C = (RNG.standard_normal((4, 64)).astype(np.float32) for _ in range(3))


class TensorErrorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_identical(self):
        p = self.dir / 'a.gguf'
        write_gguf(p, [('blk.0.attn_q.weight', A, QT.F32), ('blk.0.attn_norm.weight', B[0], QT.F32)])
        rows = t.tensor_errors(p, p)
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertEqual(r['rel_err'], 0.0)
            self.assertEqual(r['sqnr_db'], float('inf'))
            self.assertEqual(r['max_abs_err'], 0.0)

    def test_mixed_types(self):
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        names = ['blk.0.attn_q.weight', 'blk.0.attn_k.weight', 'blk.0.attn_v.weight']
        write_gguf(ref, [(n, x, QT.F32) for n, x in zip(names, (A, B, C))])
        write_gguf(q, [(names[0], A, QT.Q8_0), (names[1], B, QT.Q4_0), (names[2], C, QT.F32)])
        rows = {r['tensor']: r for r in t.tensor_errors(q, ref)}
        self.assertEqual([rows[n]['ggml_type'] for n in names], ['Q8_0', 'Q4_0', 'F32'])
        self.assertEqual([rows[n]['bits_per_weight'] for n in names], [8.5, 4.5, 32.0])
        self.assertEqual(rows[names[2]]['rel_err'], 0.0)
        self.assertEqual(rows[names[0]]['numel'], A.size)
        self.assertEqual(rows[names[0]]['layer'], 0)
        self.assertEqual(rows[names[0]]['kind'], 'attn_q')
        self.assertIsNone(rows[names[0]]['expert'])
        # Q4_0 loses more than Q8_0, and the reported numbers match a direct computation
        self.assertGreater(rows[names[0]]['rel_err'], 0)
        self.assertGreater(rows[names[1]]['rel_err'], rows[names[0]]['rel_err'])
        a_hat = gguf.quants.dequantize(gguf.quants.quantize(A, QT.Q8_0), QT.Q8_0)
        self.assertAlmostEqual(rows[names[0]]['rel_err'], t.rel_err(A, a_hat), places=9)
        self.assertAlmostEqual(rows[names[0]]['max_abs_err'], float(np.abs(a_hat - A).max()), places=6)
        self.assertAlmostEqual(rows[names[0]]['sqnr_db'], t.sqnr_db(A, a_hat), places=6)

    def test_expert_split_axis(self):
        """Only expert 2 differs. The quantized file holds F16 (a type change, as llama-quantize makes) of values that F16
        stores exactly, so experts 0, 1 and 3 have no error at all."""
        ref_w = RNG.standard_normal((4, 8, 32)).astype(np.float16).astype(np.float32)
        q_w = ref_w.copy()
        q_w[2] += 0.1
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        write_gguf(ref, [('blk.0.ffn_down_exps.weight', ref_w, QT.F32)])
        write_gguf(q, [('blk.0.ffn_down_exps.weight', q_w, QT.F16)])
        rows = t.tensor_errors(q, ref)
        self.assertEqual([r['expert'] for r in rows], [0, 1, 2, 3])
        self.assertEqual([r['kind'] for r in rows], ['experts_down'] * 4)
        self.assertEqual([r['numel'] for r in rows], [8 * 32] * 4)
        self.assertEqual([r['rel_err'] == 0 for r in rows], [True, True, False, True])
        self.assertAlmostEqual(rows[2]['rel_err'], t.rel_err(ref_w[2], q_w[2].astype(np.float16).astype(np.float32)),
                               places=6)

    def test_expert_split_quantized(self):
        w = RNG.standard_normal((3, 4, 64)).astype(np.float32)
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        write_gguf(ref, [('blk.1.ffn_up_exps.weight', w, QT.F32)])
        write_gguf(q, [('blk.1.ffn_up_exps.weight', w, QT.Q8_0)])
        rows = t.tensor_errors(q, ref)
        self.assertEqual([r['expert'] for r in rows], [0, 1, 2])
        self.assertTrue(all(r['ggml_type'] == 'Q8_0' and r['bits_per_weight'] == 8.5 for r in rows))
        w_hat = gguf.quants.dequantize(gguf.quants.quantize(w, QT.Q8_0), QT.Q8_0)
        for e, r in enumerate(rows):
            self.assertAlmostEqual(r['rel_err'], t.rel_err(w[e], w_hat[e]), places=9)

    def test_refuses_mismatch(self):
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        write_gguf(ref, [('blk.0.attn_q.weight', A, QT.F32)])
        write_gguf(q, [('blk.0.attn_k.weight', A, QT.F32)])
        with self.assertRaisesRegex(ValueError, r'blk\.0\.attn_[qk]\.weight'):
            t.tensor_errors(q, ref)
        write_gguf(q, [('blk.0.attn_q.weight', A[:2], QT.F32)])
        with self.assertRaisesRegex(ValueError, r'blk\.0\.attn_q\.weight'):
            t.tensor_errors(q, ref)

    def test_refuses_a_same_type_tensor_with_other_bytes(self):
        """Two exports of the same shape: llama-quantize copies a tensor it does not quantize byte for byte, so a tensor
        of the same type in both files must be identical, whatever the other tensors are."""
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        write_gguf(ref, [('blk.0.attn_q.weight', A, QT.F32), ('blk.0.attn_norm.weight', B[0], QT.F32)])
        write_gguf(q, [('blk.0.attn_q.weight', A, QT.Q8_0), ('blk.0.attn_norm.weight', B[0] + np.float32(1e-3), QT.F32)])
        for check in (t.check_pair, t.tensor_errors):
            with self.subTest(check=check.__name__):
                with self.assertRaisesRegex(ValueError, r'blk\.0\.attn_norm\.weight.*F32.*bytes'):
                    check(q, ref)

    def test_refuses_another_vocabulary_or_architecture(self):
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        items = [('blk.0.attn_q.weight', A, QT.F32)]
        write_gguf(ref, items, arch='olmoe', tokens=['a', 'b', 'c'])
        for arch, tokens, key in (('olmoe', ['a', 'b', 'd'], 'tokenizer.ggml.tokens'),
                                  ('olmoe', None, 'tokenizer.ggml.tokens'),
                                  ('llama', ['a', 'b', 'c'], 'general.architecture')):
            with self.subTest(key=key, tokens=tokens):
                write_gguf(q, items, arch=arch, tokens=tokens)
                with self.assertRaisesRegex(ValueError, re.escape(key)):
                    t.check_pair(q, ref)
                with self.assertRaisesRegex(ValueError, re.escape(key)):
                    t.tensor_errors(q, ref)

    def test_refuses_a_quantized_reference(self):
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        write_gguf(ref, [('blk.0.attn_q.weight', A, QT.Q8_0)])
        write_gguf(q, [('blk.0.attn_q.weight', A, QT.Q4_0)])
        with self.assertRaisesRegex(ValueError, r'blk\.0\.attn_q\.weight.*Q8_0.*F32, F16 or BF16'):
            t.check_pair(q, ref)
        with self.assertRaisesRegex(ValueError, r'blk\.0\.attn_q\.weight.*Q8_0.*F32, F16 or BF16'):
            t.tensor_errors(q, ref)

    def test_accepts_a_llama_quantize_pair(self):
        """Same architecture and tokens; quantized matrices, F16 and BF16 copies and F32 norms identical; [1, E] vs [E]."""
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        tokens = ['a', 'b', '\u00e9']
        write_gguf(ref, [('blk.0.attn_q.weight', A, QT.BF16), ('blk.0.attn_k.weight', B, QT.F16),
                         ('blk.0.attn_norm.weight', C[0], QT.F32), ('blk.0.exp_probs_b.bias', C[1:2], QT.F32)],
                   arch='olmoe', tokens=tokens)
        write_gguf(q, [('blk.0.attn_q.weight', A, QT.Q8_0), ('blk.0.attn_k.weight', B, QT.F16),
                       ('blk.0.attn_norm.weight', C[0], QT.F32), ('blk.0.exp_probs_b.bias', C[1], QT.F32)],
                   arch='olmoe', tokens=tokens)
        t.check_pair(q, ref)   # no error
        rows = {r['tensor']: r for r in t.tensor_errors(q, ref)}
        self.assertGreater(rows['blk.0.attn_q.weight']['rel_err'], 0)
        self.assertEqual(rows['blk.0.attn_k.weight']['rel_err'], 0.0)

    def test_size_one_axes_are_ignored(self):
        """The converter writes ERNIE's selection bias as [1, E]; llama-quantize rewrites it as [E]."""
        ref, q = self.dir / 'ref.gguf', self.dir / 'q.gguf'
        write_gguf(ref, [('blk.0.exp_probs_b.bias', B[:1], QT.F32)])      # shape [1, 64]
        write_gguf(q, [('blk.0.exp_probs_b.bias', B[0], QT.F32)])         # shape [64]
        rows = t.tensor_errors(q, ref)
        self.assertEqual((rows[0]['rel_err'], rows[0]['numel']), (0.0, 64))

    def test_kinds(self):
        cases = {
            'token_embd.weight': ('token_embd', None), 'output.weight': ('output', None),
            'output_norm.weight': ('norm', None), 'blk.3.attn_norm.weight': ('norm', 3),
            'blk.3.attn_q_norm.weight': ('norm', 3), 'blk.3.attn_output.weight': ('attn_output', 3),
            'blk.3.ffn_gate_inp.weight': ('router', 3), 'blk.3.exp_probs_b.bias': ('router_bias', 3),
            'blk.3.ffn_gate_exps.weight': ('experts_gate', 3), 'blk.3.ffn_up_exps.weight': ('experts_up', 3),
            'blk.3.ffn_gate_shexp.weight': ('shared_gate', 3), 'blk.3.ffn_up_shexp.weight': ('shared_up', 3),
            'blk.3.ffn_down_shexp.weight': ('shared_down', 3), 'blk.3.ffn_down.weight': ('other', 3),
            'rope_freqs.weight': ('other', None),
        }
        for name, expected in cases.items():
            self.assertEqual(t.classify(name), expected, name)

    def test_error_metrics(self):
        w = np.array([3.0, 4.0], dtype=np.float32)
        self.assertEqual(t.rel_err(w, w + np.float32(0)), 0.0)
        self.assertAlmostEqual(t.rel_err(w, np.zeros_like(w)), 1.0)
        self.assertAlmostEqual(t.sqnr_db(w, w * np.float32(0.9)), 20.0, places=4)
        self.assertEqual(t.sqnr_db(w, w), float('inf'))


if __name__ == '__main__':
    unittest.main()
