"""Router-balance test arms (#892, Lab 5 design task 4): each switch does what it says, and is off by default.

A3 fast start (moe.bias_gamma_start), A4 sampling window (moe.route_sample_steps), A5 small auxiliary loss
(moe.aux_loss_weight), A6 zero-gradient guard (optim.skip_zero_grad, from #919), A7 idle-row mask
(optim.mask_idle_rows, from Sourav Dhar's bb78dd5e).
"""
from pathlib import Path
import sys
import unittest

import torch

TEAM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM / "harness"))
from week2.config import load_runtime, validate
from week2.model import MoE
from week2.optim import MUON, Muon, zeropower_batched

D, E = 32, 8
ARMS = TEAM / "configs/arms/router_balance"


def moe(**extra):
    torch.manual_seed(0)
    cfg = {"n_embd": D, "moe": {"num_experts": E, "top_k": 2, "num_shared": 1, "ffn_hidden": 48,
                                "bias": False, "bias_gamma": 0.001, **extra}}
    return MoE(cfg).train()


def tokens(n=64, seed=0):
    return torch.randn(n, D, generator=torch.Generator().manual_seed(seed)), torch.ones(n, dtype=torch.bool)


class DefaultsOffTests(unittest.TestCase):
    def test_new_switches_absent_or_zero_give_the_same_output(self):
        x, v = tokens()
        plain = moe()(x, v)
        explicit = moe(bias_gamma_start=0.0, bias_gamma_start_steps=0, route_sample_steps=0, aux_loss_weight=0.0)(x, v)
        self.assertTrue(torch.equal(plain, explicit))

    def test_muon_with_guards_off_is_the_old_update(self):
        torch.manual_seed(1)
        a, b = torch.nn.Parameter(torch.randn(16, 24)), None
        b = torch.nn.Parameter(a.detach().clone())
        oa, ob = Muon([a], lr=0.02, **MUON), Muon([b], lr=0.02, **MUON, skip_zero_grad=False, mask_idle_rows=False)
        for g in (torch.randn(16, 24), torch.zeros(16, 24)):
            a.grad, b.grad = g.clone(), g.clone()
            oa.step(); ob.step()
        self.assertTrue(torch.equal(a, b))


class FastStartTests(unittest.TestCase):
    def bias_after(self, step):
        m = moe(bias_gamma_start=0.01, bias_gamma_start_steps=200)
        x, v = tokens()
        m(x, v)
        before = m.router_bias.clone()
        m.apply_balance_update(step)
        return (m.router_bias - before).abs().max().item()

    def test_start_step_size_until_the_given_step(self):
        self.assertAlmostEqual(self.bias_after(1), 0.01, places=6)
        self.assertAlmostEqual(self.bias_after(200), 0.01, places=6)
        self.assertAlmostEqual(self.bias_after(201), 0.001, places=6)

    def test_no_step_keeps_the_plain_step(self):
        self.assertAlmostEqual(self.bias_after(None), 0.001, places=6)


class SamplingWindowTests(unittest.TestCase):
    def test_sampled_choices_differ_from_top_k_and_gates_are_probabilities(self):
        m = moe(route_sample_steps=200)
        x, v = tokens(512)
        m.expert_load = torch.zeros(E, dtype=torch.long)
        m.route_sample = False
        m(x, v)
        topk_load = m.expert_load.clone()
        m.expert_load.zero_()
        m.route_sample = True
        torch.manual_seed(3)
        out = m(x, v)
        self.assertTrue(torch.isfinite(out).all())
        self.assertEqual(int(m.expert_load.sum()), 2 * 512)       # still two experts per token
        self.assertFalse(torch.equal(m.expert_load, topk_load))  # but not the same ones
        # Sampling spreads the load: the busiest expert gets no more than with the top 2.
        self.assertLessEqual(int(m.expert_load.max()), int(topk_load.max()))

    def test_sampling_is_training_only(self):
        m = moe()
        x, v = tokens()
        m.route_sample = True
        m.eval()
        a = m(x, v)
        m.route_sample = False
        self.assertTrue(torch.equal(a, m(x, v)))

    def test_window_for_growth(self):
        from week2.model import LanguageModel
        lm = LanguageModel.__new__(LanguageModel)
        self.assertTrue(lm.route_sampling_active(10, configured_steps=200))
        self.assertFalse(lm.route_sampling_active(201, configured_steps=200))
        lm.start_route_sampling(50, from_step=600)      # Udit's growth step at 600
        self.assertFalse(lm.route_sampling_active(600))
        self.assertTrue(lm.route_sampling_active(601))
        self.assertTrue(lm.route_sampling_active(650))
        self.assertFalse(lm.route_sampling_active(651))

    def test_sampling_with_bias_follows_the_bias(self):
        # A4b: a large negative bias on expert 0 keeps it almost never sampled; without the switch it is sampled.
        x, v = tokens(512)
        counts = {}
        for with_bias in (False, True):
            m = moe(route_sample_steps=200, route_sample_bias=with_bias)
            m.router_bias[0] = -1.0
            m.expert_load = torch.zeros(E, dtype=torch.long)
            m.route_sample = True
            torch.manual_seed(5)
            out = m(x, v)
            self.assertTrue(torch.isfinite(out).all())
            self.assertEqual(int(m.expert_load.sum()), 2 * 512)
            counts[with_bias] = int(m.expert_load[0])
        self.assertGreater(counts[False], 0)
        self.assertLess(counts[True], counts[False] // 10)

    def test_sampling_with_bias_keeps_gates_as_probabilities(self):
        m = moe(route_sample_steps=200, route_sample_bias=True)
        m.router_bias.uniform_(-0.2, 0.2)
        x, v = tokens(64)
        m.route_sample = True
        torch.manual_seed(1)
        m(x, v)                                          # runs with mixed-sign bias, no invalid weights
        m.route_sample = False
        m.eval()
        a = m(x, v)
        m.route_sample_bias = False
        self.assertTrue(torch.equal(a, m(x, v)))         # outside training the switch changes nothing


class AuxLossTests(unittest.TestCase):
    def test_even_routing_gives_one(self):
        # With every probability equal, f_i = P_i = 1/E, so E * sum f_i P_i = 1.
        m = moe(aux_loss_weight=0.001)
        with torch.no_grad():
            m.router.weight.zero_()
        x, v = tokens()
        m(x, v)
        self.assertAlmostEqual(m.aux_loss.item(), 1.0, places=5)

    def test_skewed_routing_gives_more_and_reaches_the_router(self):
        m = moe(aux_loss_weight=0.001)
        with torch.no_grad():
            m.router.weight.zero_()
            m.router.weight[0] += 2.0          # expert 0 favoured for positive inputs
        x, v = tokens()
        m(x.abs(), v)
        self.assertGreater(m.aux_loss.item(), 1.0)
        m.aux_loss.backward()
        self.assertGreater(m.router.weight.grad.abs().sum().item(), 0.0)

    def test_off_computes_nothing(self):
        m = moe()
        x, v = tokens()
        m(x, v)
        self.assertIsNone(m.aux_loss)


class ZeroGuardTests(unittest.TestCase):
    """A6, Udit Singhania's #919 guard."""

    def test_all_zero_gradient_keeps_weights_and_momentum(self):
        p = torch.nn.Parameter(torch.randn(16, 24))
        opt = Muon([p], lr=0.02, **MUON, skip_zero_grad=True)
        p.grad = torch.randn(16, 24)
        opt.step()
        w, buf = p.detach().clone(), opt.state[p]["buf"].clone()
        for _ in range(5):
            p.grad = torch.zeros(16, 24)
            opt.step()
        self.assertTrue(torch.equal(p, w))
        self.assertTrue(torch.equal(opt.state[p]["buf"], buf))

    def test_without_the_guard_the_idle_weight_drifts(self):
        p = torch.nn.Parameter(torch.randn(16, 24))
        opt = Muon([p], lr=0.02, **MUON)
        p.grad = torch.randn(16, 24)
        opt.step()
        w = p.detach().clone()
        p.grad = torch.zeros(16, 24)
        opt.step()
        self.assertFalse(torch.equal(p, w))

    def test_tiny_gradient_still_updates(self):
        p = torch.nn.Parameter(torch.randn(16, 24))
        opt = Muon([p], lr=0.02, **MUON, skip_zero_grad=True)
        w = p.detach().clone()
        p.grad = torch.full((16, 24), 1e-12)
        opt.step()
        self.assertFalse(torch.equal(p, w))


class IdleRowMaskTests(unittest.TestCase):
    """A7, Sourav Dhar's bb78dd5e row mask, with Udit's two checks."""

    def test_idle_row_keeps_weight_and_momentum(self):
        p = torch.nn.Parameter(torch.randn(8, 32))
        opt = Muon([p], lr=0.02, **MUON, skip_zero_grad=True, mask_idle_rows=True)
        p.grad = torch.randn(8, 32)
        opt.step()
        w, buf = p.detach().clone(), opt.state[p]["buf"].clone()
        g = torch.randn(8, 32)
        g[5] = 1e-10                       # row 5: an idle expert's router row (rounding-level gradient)
        p.grad = g
        opt.step()
        self.assertTrue(torch.equal(p[5], w[5]))
        self.assertTrue(torch.equal(opt.state[p]["buf"][5], buf[5]))
        self.assertFalse(torch.equal(p[0], w[0]))

    def test_active_rows_match_the_reference_with_the_idle_row_zeroed(self):
        # Udit's check 1: when another row is masked, active rows get exactly the update the old step gives
        # a matrix whose idle row has no gradient and no momentum.
        torch.manual_seed(2)
        g, w0 = torch.randn(8, 32), torch.randn(8, 32)
        g[3] = 0.0
        p = torch.nn.Parameter(w0.clone())
        opt = Muon([p], lr=0.02, **MUON, mask_idle_rows=True)
        p.grad = g.clone()
        opt.step()
        # Reference: the plain update on the same gradient (row 3 zero, fresh momentum, so its momentum is zero too).
        q = torch.nn.Parameter(w0.clone())
        ref = Muon([q], lr=0.02, **MUON)
        q.grad = g.clone()
        ref.step()
        live = torch.ones(8, dtype=torch.bool)
        live[3] = False
        torch.testing.assert_close(p[live], q[live], rtol=0, atol=1e-6)
        self.assertTrue(torch.equal(p[3], w0[3]))

    def test_real_small_gradient_rows_are_not_suppressed(self):
        # Udit's check 2: a row with a small but real gradient (1e-3 of the largest) still updates.
        p = torch.nn.Parameter(torch.randn(8, 32))
        opt = Muon([p], lr=0.02, **MUON, mask_idle_rows=True)
        w = p.detach().clone()
        g = torch.randn(8, 32)
        g[6] = g[6] / g[6].norm() * g.norm(dim=1).max() * 1e-3
        p.grad = g
        opt.step()
        self.assertFalse(torch.equal(p[6], w[6]))


class ArmFileTests(unittest.TestCase):
    def test_every_arm_file_is_valid_and_changes_one_thing(self):
        base = load_runtime(ARMS / "base.yaml")
        changes = {
            "gamma_low": ("model", "moe", "bias_gamma", 0.0001),
            "gamma_high": ("model", "moe", "bias_gamma", 0.01),
            "fast_start": ("model", "moe", "bias_gamma_start", 0.01),
            "sample_window": ("model", "moe", "route_sample_steps", 200),
            "aux_loss": ("model", "moe", "aux_loss_weight", 0.001),
            "zero_guard": ("optim", None, "skip_zero_grad", True),
            "guard_row_mask": ("optim", None, "mask_idle_rows", True),
            # Second screen (29 Nov): A2b, A5b, A4b.
            "gamma_mid": ("model", "moe", "bias_gamma", 0.003),
            "aux_loss_strong": ("model", "moe", "aux_loss_weight", 0.01),
            "sample_window_bias": ("model", "moe", "route_sample_bias", True),
        }
        self.assertEqual(validate(base), [])
        for arm, (part, sub, key, value) in changes.items():
            c = load_runtime(ARMS / f"{arm}.yaml")
            self.assertEqual(validate(c), [], arm)
            node = c[part][sub] if sub else c[part]
            self.assertEqual(node[key], value, arm)
            self.assertEqual(c["model"]["n_layer"], base["model"]["n_layer"], arm)
            self.assertEqual(c["run"]["dtype"], base["run"]["dtype"], arm)

    def test_bad_values_are_refused(self):
        c = load_runtime(ARMS / "base.yaml")
        c["model"]["moe"]["bias_gamma_start"] = 0.01      # without its step count
        self.assertTrue(any("bias_gamma_start" in e for e in validate(c)))
        c = load_runtime(ARMS / "base.yaml")
        c["model"]["moe"]["route_sample_steps"] = -1
        self.assertTrue(any("route_sample_steps" in e for e in validate(c)))
        c = load_runtime(ARMS / "base.yaml")
        c["optim"]["mask_idle_rows"] = "yes"
        self.assertTrue(any("mask_idle_rows" in e for e in validate(c)))
        c = load_runtime(ARMS / "base.yaml")
        c["model"]["moe"]["route_sample_bias"] = True        # without a sampling window
        self.assertTrue(any("route_sample_bias" in e for e in validate(c)))
        c = load_runtime(ARMS / "base.yaml")
        c["model"]["moe"]["route_sample_bias"] = "yes"
        self.assertTrue(any("route_sample_bias" in e for e in validate(c)))


if __name__ == "__main__":
    unittest.main()
