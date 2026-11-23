"""Loss-free balancer: bias changes the choice only, then moves toward under-used experts."""

import sys
import unittest
from pathlib import Path

import torch

TEAM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM / "harness"))
from week2.config import load, load_runtime, merge, validate
from week2.model import MoE


def moe_cfg(gamma, experts=2, top_k=1):
    return {
        "n_embd": 4,
        "moe": {
            "ffn_hidden": 4,
            "top_k": top_k,
            "num_experts": experts,
            "num_shared": 0,
            "bias": False,
            "bias_gamma": gamma,
        },
    }


class RouterBiasTests(unittest.TestCase):
    def test_gamma_zero_leaves_the_bias_buffer_at_zero(self):
        moe = MoE(moe_cfg(0.0))
        moe.train()
        x = torch.ones(1, 2, 4)
        valid = torch.ones(1, 2, dtype=torch.bool)
        moe(x, valid)
        moe.apply_balance_update()
        self.assertTrue(torch.equal(moe.router_bias, torch.zeros(2)))
        self.assertIsNone(moe.experts[0].gate.bias)

    def test_bias_changes_the_choice_and_not_the_gate(self):
        moe = MoE(moe_cfg(0.001, experts=3, top_k=2))
        moe.eval()
        with torch.no_grad():
            moe.router.weight.zero_()
            moe.router.weight[0].fill_(3.0)
            moe.router.weight[1].fill_(1.0)
            moe.router_bias.copy_(torch.tensor([0.0, 0.0, 2.0]))
        flat = torch.ones(1, 4)
        valid = torch.ones(1, 1, dtype=torch.bool)
        scores = torch.softmax(moe.router(flat).detach().float(), dim=-1)
        unbiased = scores.topk(2).indices[0].tolist()
        chosen = (scores + moe.router_bias).topk(2).indices[0].tolist()
        self.assertNotEqual(sorted(chosen), sorted(unbiased))
        y = moe(flat.reshape(1, 1, 4), valid)
        weights = scores[0, chosen]
        weights = weights / weights.sum()
        expected = sum(moe.experts[i](flat) * float(weights[k]) for k, i in enumerate(chosen))
        torch.testing.assert_close(y.reshape(1, 4), expected.detach())

    def test_update_raises_the_starved_expert(self):
        moe = MoE(moe_cfg(0.001))
        moe.train()
        with torch.no_grad():
            moe.router.weight.zero_()
            moe.router.weight[0].fill_(4.0)
            moe.router_bias.zero_()
        x = torch.ones(2, 3, 4)
        valid = torch.ones(2, 3, dtype=torch.bool)
        moe(x, valid)
        before = moe.router_bias.detach().clone()
        moe.apply_balance_update()
        # Every token chose expert 0, so expert 1 is under the mean and its bias rises.
        self.assertGreater(float(moe.router_bias[1]), float(before[1]))
        self.assertLess(float(moe.router_bias[0]), float(before[0]))
        self.assertAlmostEqual(float(moe.router_bias[1] - before[1]), 0.001)

    def test_expert_linear_bias_stays_rejected(self):
        c = merge(
            load_runtime(TEAM / "configs/arms/t1.yaml"),
            load(TEAM / "configs/small/smoke_resolution.yaml"),
        )
        c["model"]["moe"]["bias"] = True
        self.assertTrue(any("bias-free" in err for err in validate(c)))


if __name__ == "__main__":
    unittest.main()
