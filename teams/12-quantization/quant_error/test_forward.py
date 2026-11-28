#!/usr/bin/env python3
"""Tests for the layer-streamed twin forward:  python test_forward.py

Both tracks read Hugging Face folders (SafetensorsWeights), so no llama.cpp is needed. A test whose fixture lacks an
input (the p1536 tokenizer, OLMoE's files offline) is skipped with a message.
"""
import json, sys, unittest
from pathlib import Path
from unittest import mock

import torch
from torch import nn
from transformers import AutoConfig, AutoModelForCausalLM, Ernie4_5_MoeConfig, Ernie4_5_MoeForCausalLM

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fixtures  # noqa: E402
import forward as f  # noqa: E402
from weights import SafetensorsWeights  # noqa: E402

BUILT = None   # fixtures.Built, for this module's tests
SCALED = 'model.layers.1.mlp.experts.2.down_proj.weight'


def setUpModule():
    global BUILT
    BUILT = fixtures.Built()


def tearDownModule():
    BUILT.close()


def hf(arch: str) -> Path:
    make = {'olmoe': fixtures.tiny_olmoe, 'ernie': fixtures.tiny_ernie, 'ernie-dense0': dense_first_ernie}[arch]
    return BUILT(arch, make)


def dense_first_ernie(dir: Path) -> Path:
    """A tiny ERNIE whose layer 0 is a dense MLP (as ERNIE-4.5-21B's, moe_layer_start_index 1), no shared experts."""
    config = Ernie4_5_MoeConfig(vocab_size=512, hidden_size=64, intermediate_size=96, num_hidden_layers=2,
                                num_attention_heads=4, num_key_value_heads=2, moe_num_experts=8, moe_k=2,
                                moe_intermediate_size=32, moe_layer_start_index=1, moe_num_shared_experts=0,
                                use_bias=False, tie_word_embeddings=False, dtype='float32')
    model = Ernie4_5_MoeForCausalLM(config)
    fixtures._randomize(model, seed=1)
    model.save_pretrained(dir)
    return dir


def batches(hf_dir: Path, seed: int = 0) -> dict[str, list[torch.Tensor]]:
    """Two slices of random token ids; batches of different shapes."""
    vocab = json.loads((hf_dir / 'config.json').read_text(encoding='utf-8'))['vocab_size']
    g = torch.Generator().manual_seed(seed)
    ids = lambda *shape: torch.randint(0, vocab, shape, generator=g)
    return {'a': [ids(2, 24)], 'b': [ids(1, 40), ids(1, 16)]}


def linear_weights(hf_dir: Path) -> set[str]:
    """The weight name of every nn.Linear in the transformers model."""
    with torch.device('meta'):
        model = AutoModelForCausalLM.from_config(AutoConfig.from_pretrained(hf_dir))
    return {f'{name}.weight' for name, m in model.named_modules() if isinstance(m, nn.Linear)}


class Edited:
    """A WeightSource: `src` with each tensor named in `edits` replaced by edits[name](tensor)."""

    def __init__(self, src, edits: dict):
        self.src, self.edits, self.n_layers = src, edits, src.n_layers

    def _edited(self, part: dict) -> dict:
        return {k: self.edits[k](v) if k in self.edits else v for k, v in part.items()}

    def embed(self):
        return self._edited(self.src.embed())

    def layer(self, i):
        return self._edited(self.src.layer(i))

    def head(self):
        return self._edited(self.src.head())


def noise(v: torch.Tensor) -> torch.Tensor:
    return v + 0.05 * torch.randn(v.shape, generator=torch.Generator().manual_seed(v.numel()))


def whole(hf_dir: Path, src, data: dict, inputs_of: list[str]) -> dict:
    """The whole transformers model with `src`'s weights on `data`: per slice, each layer's outputs, the experts each
    MoE layer picked (transformers' own rule), the inputs of the Linears named in `inputs_of`, and the logits."""
    model = AutoModelForCausalLM.from_pretrained(hf_dir, dtype=torch.float32).eval()
    model.load_state_dict({k: v for part in (src.embed(), *map(src.layer, range(src.n_layers)), src.head())
                           for k, v in part.items()}, strict=True)
    rec = {s: {'h': {}, 'picked': {}, 'x': {}, 'logits': []} for s in data}
    cur = {}

    def keep(kind, key, value):
        rec[cur['s']][kind].setdefault(key, []).append(value.reshape(-1, value.shape[-1]))

    for i, layer in enumerate(model.model.layers):
        layer.register_forward_hook(lambda m, a, o, i=i: keep('h', i, o[0] if isinstance(o, tuple) else o))
        if hasattr(layer.mlp, 'gate'):
            mlp = layer.mlp
            def pick(m, a, o, i=i, mlp=mlp):
                p = torch.softmax(o, dim=1, dtype=torch.float)
                keep('picked', i, torch.topk(mlp.moe_statics(p) if hasattr(mlp, 'moe_statics') else p, mlp.top_k,
                                             dim=-1).indices.sort(-1).values)
            mlp.gate.register_forward_hook(pick)
    for t in inputs_of:
        model.get_submodule(t.removesuffix('.weight')).register_forward_pre_hook(lambda m, a, t=t: keep('x', t, a[0]))
    with torch.no_grad():
        for s, bs in data.items():
            cur['s'] = s
            rec[s]['logits'] = [model(b).logits.reshape(-1, model.config.vocab_size) for b in bs]
    return rec


class TwinForwardTests(unittest.TestCase):
    def test_identical_weights(self):
        for arch in ('olmoe', 'ernie', 'ernie-dense0'):
            with self.subTest(arch=arch):
                d = hf(arch)
                src, data = SafetensorsWeights(d), batches(d)
                r = f.twin_forward(d, src, SafetensorsWeights(d), data)
                self.assertEqual([(row['slice'], row['layer']) for row in r.layers],
                                 [(s, i) for i in range(2) for s in data])
                for row in r.layers:
                    self.assertEqual(row['hidden_rel_err'], 0, row)
                    if arch == 'ernie-dense0' and row['layer'] == 0:
                        self.assertIsNone(row['router_agree'], row)  # a dense MLP has no router
                    else:
                        self.assertEqual(row['router_agree'], 1.0, row)
                self.assertEqual({row['tensor'] for row in r.linears}, linear_weights(d))
                for row in r.linears:   # an expert no token was routed to has no inputs and no error
                    self.assertEqual(row['act_rel_err'], 0 if row['rows'] else None, row)
                self.assertEqual([row['slice'] for row in r.tokens], list(data))
                for row in r.tokens:
                    self.assertEqual(row['n_tokens'], sum(b.numel() for b in data[row['slice']]))
                    self.assertLessEqual(row['kl_mean'], 1e-7, row)
                    self.assertEqual(row['same_top1'], 1.0, row)

    def test_streamed_matches_full_model(self):
        for arch in ('olmoe', 'ernie'):
            with self.subTest(arch=arch):
                d = hf(arch)
                data, got = batches(d, seed=1), {}
                f.twin_forward(d, SafetensorsWeights(d), SafetensorsWeights(d), data,
                               on_logits=lambda s, j, ref, quant: got.__setitem__((s, j), ref.cpu()))
                model = AutoModelForCausalLM.from_pretrained(d, dtype=torch.float32).eval()
                self.assertEqual(sorted(got), sorted((s, j) for s in data for j in range(len(data[s]))))
                with torch.no_grad():
                    for (s, j), logits in got.items():
                        want = model(data[s][j]).logits
                        self.assertEqual(logits.shape, want.shape)
                        self.assertLessEqual((logits - want).abs().max().item(), 1e-4, (s, j))

    def test_error_localised(self):
        for arch in ('olmoe', 'ernie'):
            with self.subTest(arch=arch):
                d = hf(arch)
                ref = SafetensorsWeights(d)
                r = f.twin_forward(d, ref, Edited(SafetensorsWeights(d), {SCALED: lambda v: v * 1.1}), batches(d, seed=2))
                for row in r.layers:
                    if row['layer'] == 0:
                        self.assertEqual(row['hidden_rel_err'], 0, row)
                    else:
                        self.assertGreater(row['hidden_rel_err'], 0, row)
                hit = [row for row in r.linears if row['act_rel_err']]
                self.assertEqual([row['tensor'] for row in hit], [SCALED])
                self.assertEqual((hit[0]['layer'], hit[0]['expert']), (1, 2))
                self.assertGreater(hit[0]['rows'], 0)
                self.assertAlmostEqual(hit[0]['act_rel_err'], 0.1, places=5)  # ‖X(W - 1.1W)ᵀ‖ / ‖XWᵀ‖
                for row in r.tokens:
                    self.assertGreater(row['kl_mean'], 0, row)

    def test_values_match_whole_models(self):
        """Every number against whole transformers models run with each track's weights: a perturbation upstream
        (layer 0) makes layer 1's inputs and routing differ between the tracks, so a measure that took the quantized
        track's inputs, or one track's routing twice, would not match."""
        for arch in ('olmoe', 'ernie'):
            with self.subTest(arch=arch):
                d = hf(arch)
                edited = ('model.layers.0.self_attn.o_proj.weight', 'model.layers.0.mlp.gate.weight',
                          'model.layers.1.self_attn.q_proj.weight', 'model.layers.1.mlp.experts.2.gate_proj.weight')
                ref, quant = SafetensorsWeights(d), Edited(SafetensorsWeights(d), dict.fromkeys(edited, noise))
                data = batches(d, seed=3)
                r = f.twin_forward(d, ref, quant, data, x_rows=10_000)   # every input row, no sampling
                wr, wq = whole(d, ref, data, edited), whole(d, quant, data, [])
                close = lambda got, want, tol=1e-4: self.assertLessEqual(abs(got - want), tol * abs(want) + 1e-7)
                cat = lambda rec, s, kind, key: torch.cat(rec[s][kind][key]).double()
                agree = []
                for row in r.layers:
                    s, i = row['slice'], row['layer']
                    hr, hq = cat(wr, s, 'h', i), cat(wq, s, 'h', i)
                    close(row['hidden_rel_err'], ((hq - hr).norm() / hr.norm()).item())
                    pr, pq = cat(wr, s, 'picked', i), cat(wq, s, 'picked', i)
                    self.assertEqual(row['router_agree'], (pr == pq).all(-1).double().mean().item(), row)
                    agree.append(row['router_agree'])
                self.assertLess(min(agree), 1.0)   # the routing does differ somewhere
                linears = {row['tensor']: row for row in r.linears}
                for t in edited:
                    x = torch.cat([cat(wr, s, 'x', t) for s in data])
                    w = ref.layer(int(t.split('.')[2]))[t].double()
                    w_hat = quant.layer(int(t.split('.')[2]))[t].double()
                    self.assertEqual(linears[t]['rows'], len(x), t)
                    close(linears[t]['act_rel_err'], ((x @ (w - w_hat).T).norm() / (x @ w.T).norm()).item())
                for row in r.tokens:
                    lp = torch.log_softmax(torch.cat(wr[row['slice']]['logits']).double(), -1)
                    lq = torch.log_softmax(torch.cat(wq[row['slice']]['logits']).double(), -1)
                    kl = (lp.exp() * (lp - lq)).sum(-1)
                    self.assertEqual(row['n_tokens'], len(kl))
                    close(row['kl_mean'], kl.mean().item(), 1e-3)
                    close(row['kl_p99'], torch.quantile(kl, 0.99).item(), 1e-3)
                    self.assertEqual(row['same_top1'], (lp.argmax(-1) == lq.argmax(-1)).double().mean().item())

    def test_fp32_matmul_precision_is_pinned(self):
        """TF32 (CUDA) or a lower matmul precision would add an error of its own to both tracks; twin_forward pins
        full fp32 and leaves it so, and fp32_settings reports it."""
        d = hf('olmoe')
        torch.set_float32_matmul_precision('medium')
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        f.twin_forward(d, SafetensorsWeights(d), SafetensorsWeights(d), batches(d))
        self.assertEqual(f.fp32_settings(), {'float32_matmul_precision': 'highest', 'cuda_matmul_allow_tf32': False,
                                             'cudnn_allow_tf32': False})

    def test_a_moe_layer_whose_router_gave_no_logits_is_an_error(self):
        """An MoE block that routes without calling mlp.gate would leave router_agree unmeasured; it must raise,
        naming the layer, not pass a stale or missing router output on."""
        from transformers.models.olmoe.modeling_olmoe import OlmoeSparseMoeBlock
        d = hf('olmoe')
        with mock.patch.object(OlmoeSparseMoeBlock, 'forward', lambda self, h: (h, None)):
            with self.assertRaisesRegex(RuntimeError, r'layer 0\b.*mlp\.gate'):
                f.twin_forward(d, SafetensorsWeights(d), SafetensorsWeights(d), batches(d))

    def test_x_rows_caps_the_sample(self):
        d = hf('olmoe')
        r = f.twin_forward(d, SafetensorsWeights(d), SafetensorsWeights(d), batches(d), x_rows=8)
        full = f.twin_forward(d, SafetensorsWeights(d), SafetensorsWeights(d), batches(d))
        self.assertEqual([row['rows'] for row in r.linears], [min(8, row['rows']) for row in full.linears])


class SelectionTests(unittest.TestCase):
    def test_ernie_selection_large_offset(self):
        """Baidu's ERNIE biases sit at large offsets with a tiny per-expert spread; the choice must keep them."""
        g = torch.Generator().manual_seed(0)
        logits = torch.randn(1000, 16, generator=g)
        bias = (50 + 1e-3 * torch.randn(1, 16, generator=g)).float()   # the [1, E] parameter
        want = torch.topk(torch.softmax(logits.double(), -1) + bias.double().reshape(-1), 2, dim=-1).indices
        got = f.select_experts('ernie4_5-moe', logits, 2, bias)
        self.assertEqual(got.shape, (1000, 2))
        self.assertTrue(torch.equal(got.sort(-1).values, want.sort(-1).values))
        unbiased = f.select_experts('ernie4_5-moe', logits, 2, None)
        self.assertFalse(torch.equal(unbiased.sort(-1).values, want.sort(-1).values))

    def test_olmoe_selection(self):
        logits = torch.tensor([[0.1, 2.0, -1.0, 1.5], [3.0, 0.0, 2.9, -5.0]])
        self.assertEqual(f.select_experts('olmoe', logits, 2, None).sort(-1).values.tolist(), [[1, 3], [0, 2]])
        with self.assertRaises(NotImplementedError):
            f.select_experts('llama', logits, 2, None)


if __name__ == '__main__':
    unittest.main()
