import sys
import unittest
from pathlib import Path

import torch
from torch import nn

TEAM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM / "lab5" / "gradient_coverage"))
import grad_coverage as gc


class Toy(nn.Module):
    def __init__(self):
        super().__init__()
        self.a = nn.Linear(3, 3)
        self.unused = nn.Linear(3, 3)
        self.dead = nn.Linear(3, 3, bias=False)

    def forward(self, x, skip_a=False):
        h = x if skip_a else self.a(x)
        return h + 0.0 * self.dead(x).sum()      # zero gradient, not None


class ScanTests(unittest.TestCase):
    def test_none_zero_ok_are_told_apart(self):
        m = Toy()
        r = gc.scan(m, lambda: m(torch.ones(2, 3)).sum().backward())
        self.assertEqual(r["a.weight"]["state"], gc.OK)
        self.assertEqual(r["unused.weight"]["state"], gc.NONE)
        self.assertEqual(r["dead.weight"]["state"], gc.ZERO)

    def test_a_fast_path_that_skips_a_gradient_shows_in_compare(self):
        m = Toy()
        off = gc.scan(m, lambda: m(torch.ones(2, 3)).sum().backward())
        on = gc.scan(m, lambda: m(torch.ones(2, 3), skip_a=True).sum().backward())
        names = [d["name"] for d in gc.compare(off, on)]
        self.assertEqual(names, ["a.bias", "a.weight"])

    def test_scan_does_not_reuse_old_gradients(self):
        m = Toy()
        gc.scan(m, lambda: m(torch.ones(2, 3)).sum().backward())
        r = gc.scan(m, lambda: m(torch.ones(2, 3), skip_a=True).sum().backward())
        self.assertEqual(r["a.weight"]["state"], gc.NONE)

    def test_frozen_parameters_are_not_counted(self):
        m = Toy()
        m.a.weight.requires_grad_(False)
        r = gc.scan(m, lambda: m(torch.ones(2, 3)).sum().backward())
        self.assertNotIn("a.weight", r)

    def test_reason_required(self):
        m = Toy()
        r = gc.scan(m, lambda: m(torch.ones(2, 3)).sum().backward())
        rows = gc.report(r, allow=[(r"^unused\.", "kept for a later stage")])
        by = {x["name"]: x["reason"] for x in rows}
        self.assertEqual(by["unused.weight"], "kept for a later stage")
        self.assertIsNone(by["dead.weight"])


class Team5ModelTests(unittest.TestCase):
    def test_eager_and_sdpa_cover_the_same_parameters(self):
        res = gc.run(["model.attn_impl=sdpa"], [])
        self.assertEqual(res["differences"], [])
        self.assertEqual(res["off"], res["on"])

    def test_expert_with_no_tokens_is_explained_by_its_load(self):
        # Loss-free balancer on, one expert's selection bias very negative: it gets 0 tokens, so its gradient is all zero.
        model, ids, targets = gc.build(["model.moe.bias_gamma=0.001"])
        model.blocks[0].moe.router_bias[3] = -1e9
        r = gc.scan(model, gc.team5_step(model, ids, targets))
        load = gc.expert_loads(model)
        self.assertEqual(load[0][3], 0)
        rows = {x["name"]: x for x in gc.report(r, expert_load=load)}
        e3 = [n for n in rows if n.startswith("blocks.0.moe.experts.3.")]
        self.assertTrue(e3)
        for n in e3:
            self.assertEqual(rows[n]["state"], gc.ZERO)
            self.assertIn("received 0 tokens", rows[n]["reason"])
        self.assertFalse([n for n in rows if n.startswith("blocks.0.moe.experts.0.")])

    def test_cli_exit_codes(self):
        self.assertEqual(gc.main(["--fast", "model.attn_impl=sdpa"]), 0)


if __name__ == "__main__":
    unittest.main()
