#!/usr/bin/env python3
"""Tests for layer-wise weights from Hugging Face folders and GGUF files:  python test_weights.py

The GGUF round trips need llama.cpp's converter:  LLAMA_CPP_DIR=<llama.cpp b12359 checkout> python test_weights.py
"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

import torch
import gguf
from safetensors.torch import load_file, save_file
from transformers import AutoModelForCausalLM

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures  # noqa: E402
import weights as w  # noqa: E402

LLAMA = os.environ.get('LLAMA_CPP_DIR')
needs_llama = unittest.skipUnless(LLAMA, 'set LLAMA_CPP_DIR to a llama.cpp b12359 checkout to run the GGUF round trips')
TMP, HF, GG = None, {}, {}


def setUpModule():
    global TMP
    TMP = tempfile.TemporaryDirectory()
    d = Path(TMP.name)
    HF.update(olmoe=fixtures.tiny_olmoe(d / 'olmoe'), ernie=fixtures.tiny_ernie(d / 'ernie'))
    if LLAMA:
        GG.update({k: fixtures.to_gguf(v, d / f'{k}-f32.gguf', 'f32') for k, v in HF.items()})


def tearDownModule():
    TMP.cleanup()


def stages(src) -> dict[str, dict[str, torch.Tensor]]:
    """{'embed': ..., 'layer 0': ..., 'layer 1': ..., 'head': ...} of a WeightSource."""
    return {'embed': src.embed(), **{f'layer {i}': src.layer(i) for i in range(src.n_layers)}, 'head': src.head()}


def tied_copy(hf: Path, out: Path) -> Path:
    """`hf` with tie_word_embeddings = true and no lm_head.weight in its safetensors."""
    out.mkdir()
    cfg = json.loads((hf / 'config.json').read_text(encoding='utf-8'))
    (out / 'config.json').write_text(json.dumps(dict(cfg, tie_word_embeddings=True)), encoding='utf-8')
    state = load_file(hf / 'model.safetensors')
    del state['lm_head.weight']
    save_file(state, out / 'model.safetensors', metadata={'format': 'pt'})
    return out


def rewrite_gguf(src: Path, out: Path, arch: str, drop: str | None = None) -> Path:
    """Copy of `src`'s tensors (minus `drop`) in a GGUF whose general.architecture is `arch`."""
    writer = gguf.GGUFWriter(str(out), arch)
    for t in gguf.GGUFReader(str(src)).tensors:
        if t.name != drop:
            writer.add_tensor(t.name, t.data, raw_dtype=t.tensor_type)
    writer.write_header_to_file()
    writer.write_kv_data_to_file()
    writer.write_tensors_to_file()
    writer.close()
    return out


class SafetensorsTests(unittest.TestCase):
    def test_matches_transformers(self):
        for arch, hf in HF.items():
            with self.subTest(arch=arch):
                state = AutoModelForCausalLM.from_pretrained(hf, dtype=torch.float32).state_dict()
                src = w.SafetensorsWeights(hf)
                self.assertEqual(src.n_layers, 2)
                got = stages(src)
                self.assertEqual(set(got['embed']), {'model.embed_tokens.weight'})
                self.assertEqual(set(got['head']), {'model.norm.weight', 'lm_head.weight'})
                for i in range(2):
                    self.assertTrue(all(k.startswith(f'model.layers.{i}.') for k in got[f'layer {i}']))
                merged = {k: v for part in got.values() for k, v in part.items()}
                self.assertEqual(len(merged), sum(len(part) for part in got.values()))  # stages do not overlap
                self.assertEqual(set(merged), set(state))
                for k, v in merged.items():
                    self.assertEqual(v.dtype, torch.float32, k)
                    self.assertTrue(torch.equal(v, state[k]), k)

    def test_tied_head(self):
        with tempfile.TemporaryDirectory() as t:
            src = w.SafetensorsWeights(tied_copy(HF['ernie'], Path(t) / 'tied'))
            self.assertTrue(torch.equal(src.head()['lm_head.weight'], src.embed()['model.embed_tokens.weight']))


class GGUFTests(unittest.TestCase):
    def assert_same(self, got, ref):
        """Same stages, same key sets, every tensor fp32 and exactly equal."""
        self.assertEqual(got.n_layers, ref.n_layers)
        got, ref = stages(got), stages(ref)
        self.assertEqual(list(got), list(ref))
        for stage in ref:
            self.assertEqual(sorted(got[stage]), sorted(ref[stage]), stage)
            for k, v in ref[stage].items():
                self.assertEqual(got[stage][k].dtype, torch.float32, k)
                self.assertTrue(torch.equal(got[stage][k], v), k)

    def assert_all_distinct(self, src):
        """No two tensors of the fixture are equal, so a swapped mapping could not pass assert_same."""
        tensors = [(k, v) for part in stages(src).values() for k, v in part.items()]
        for i, (a, x) in enumerate(tensors):
            for b, y in tensors[i + 1:]:
                self.assertFalse(x.shape == y.shape and torch.equal(x, y), f'{a} equals {b}')

    @needs_llama
    def test_roundtrip_olmoe(self):
        ref = w.SafetensorsWeights(HF['olmoe'])
        self.assert_all_distinct(ref)
        self.assert_same(w.GGUFWeights(GG['olmoe'], HF['olmoe']), ref)

    @needs_llama
    def test_roundtrip_ernie(self):
        ref = w.SafetensorsWeights(HF['ernie'])
        self.assert_all_distinct(ref)
        for i in range(ref.n_layers):
            bias = ref.layer(i)[f'model.layers.{i}.mlp.moe_statics.e_score_correction_bias']
            self.assertGreater(bias.abs().max().item(), 0)  # the fixture's router bias is active
        self.assert_same(w.GGUFWeights(GG['ernie'], HF['ernie']), ref)

    @needs_llama
    def test_quantized_ernie(self):
        """A llama-quantize Q8_0 file: HF names and shapes, router and norms exact (llama-quantize keeps them F32)."""
        with tempfile.TemporaryDirectory() as t:
            q8 = Path(t) / 'ernie-q8_0.gguf'
            subprocess.run([str(Path(LLAMA) / 'build/bin/llama-quantize'), str(GG['ernie']), str(q8), 'Q8_0'],
                           capture_output=True, check=True)
            got, ref = stages(w.GGUFWeights(q8, HF['ernie'])), stages(w.SafetensorsWeights(HF['ernie']))
        exact = ('layernorm.weight', 'model.norm.weight', 'mlp.gate.weight', 'e_score_correction_bias')
        for stage in ref:
            self.assertEqual(sorted(got[stage]), sorted(ref[stage]), stage)
            for k, v in ref[stage].items():
                g = got[stage][k]
                self.assertEqual((g.dtype, g.shape), (torch.float32, v.shape), k)
                if k.endswith(exact):
                    self.assertTrue(torch.equal(g, v), k)
                else:
                    rel = ((g - v).norm() / v.norm()).item()
                    self.assertTrue(0 < rel < 0.01, f'{k}: relative error {rel}')

    @needs_llama
    def test_tied_head(self):
        with tempfile.TemporaryDirectory() as t:
            tied = tied_copy(HF['ernie'], Path(t) / 'tied')
            no_output = rewrite_gguf(GG['ernie'], Path(t) / 'no-output.gguf', 'ernie4_5-moe', drop='output.weight')
            src = w.GGUFWeights(no_output, tied)
            self.assertTrue(torch.equal(src.head()['lm_head.weight'], src.embed()['model.embed_tokens.weight']))
            self.assertTrue(torch.equal(src.head()['lm_head.weight'],
                                        w.SafetensorsWeights(HF['ernie']).embed()['model.embed_tokens.weight']))
            with self.assertRaisesRegex(ValueError, r'output\.weight'):
                w.GGUFWeights(no_output, HF['ernie'])  # untied config: a missing head is an error, not the embedding

    @needs_llama
    def test_refuses_other_model(self):
        with self.assertRaisesRegex(ValueError, 'olmoe'):
            w.GGUFWeights(GG['olmoe'], HF['ernie'])

    def test_unsupported_arch(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'llama.gguf'
            writer = gguf.GGUFWriter(str(p), 'llama')
            writer.add_tensor('token_embd.weight', torch.zeros(8, 4).numpy())
            writer.write_header_to_file()
            writer.write_kv_data_to_file()
            writer.write_tensors_to_file()
            writer.close()
            with self.assertRaisesRegex(NotImplementedError, r'^llama: add a mapping and its round-trip test$'):
                w.GGUFWeights(p, Path(t))


if __name__ == '__main__':
    unittest.main()
