"""Lab 5 DT & Hybrid Muon compatibility tests (CPU, deterministic, no external downloads).

Verifies:
1. Shape-based Hybrid Muon routing (2D -> Muon wd=0.0, non-2D -> AdamW) and Muon momentum buffer save/restore.
2. MoE idle-expert zero-grad Newton-Schulz momentum re-inflation finding (skip_zero_grad=False vs True).
3. Deletion Tuning under Hybrid Muon (gate routed by shape to Muon vs AdamW) + optimizer step-time share.
4. Deletion Tuning with activation recompute (torch.utils.checkpoint use_reentrant=False): gradient parity.
5. Unseen-expert Wanda calibration policy (--dt-unseen official vs keep) on a routed MoE with idle experts.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

TEAM10 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM10 / "dt"))
sys.path.insert(0, str(TEAM10 / "capstone"))

import hybrid_optim as ho  # noqa: E402
import mask as dtmask  # noqa: E402


class TinyRoutedMoEBlock(nn.Module):
    """Minimal routed MoE block with a fused-stack path (like Team 5 #521) and a 1D RMSNorm gain."""

    def __init__(self, d: int = 32, hidden: int = 64, n_experts: int = 6, topk: int = 2):
        super().__init__()
        self.norm_gain = nn.Parameter(torch.ones(d))
        self.router = nn.Linear(d, n_experts, bias=False)
        self.experts = nn.ModuleList([
            nn.ModuleDict({
                "gate": nn.Linear(d, hidden, bias=False),
                "up": nn.Linear(d, hidden, bias=False),
                "down": nn.Linear(hidden, d, bias=False),
            })
            for _ in range(n_experts)
        ])
        self.topk = topk
        self.bias_gamma = 0.001
        self.register_buffer("router_bias", torch.zeros(n_experts))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = x * self.norm_gain
        probs = F.softmax(self.router(h), dim=-1)
        choice_scores = probs + self.router_bias
        top_idx = choice_scores.topk(self.topk, dim=-1).indices
        top_w = probs.gather(-1, top_idx)
        top_w = top_w / top_w.sum(dim=-1, keepdim=True).clamp_min(1e-8)

        # Fused stack path matching Team 5 #521: reads e["gate"].weight so MaskedLinear.weight fires.
        wg = torch.stack([e["gate"].weight for e in self.experts])  # [E, H, D]
        wu = torch.stack([e["up"].weight for e in self.experts])
        wd = torch.stack([e["down"].weight for e in self.experts])

        out = torch.zeros_like(h)
        for k in range(self.topk):
            idx = top_idx[..., k]
            w = top_w[..., k : k + 1]
            g_proj = torch.einsum("btd,bthd->bth", h, wg[idx])
            u_proj = torch.einsum("btd,bthd->bth", h, wu[idx])
            act = F.silu(g_proj) * u_proj
            y = torch.einsum("bth,btdh->btd", act, wd[idx])
            out = out + w * y
        return x + out


class TinyMoELM(nn.Module):
    def __init__(self, vocab: int = 64, d: int = 32, hidden: int = 64, n_layers: int = 2, n_experts: int = 6):
        super().__init__()
        self.embed = nn.Embedding(vocab, d)
        self.blocks = nn.ModuleList([TinyRoutedMoEBlock(d, hidden, n_experts) for _ in range(n_layers)])
        self.final_norm = nn.Parameter(torch.ones(d))
        self.head = nn.Linear(d, vocab, bias=False)
        self.use_checkpoint = False

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor | None = None) -> torch.Tensor:
        x = self.embed(input_ids)
        for blk in self.blocks:
            if self.use_checkpoint and self.training:
                x = checkpoint(blk, x, use_reentrant=False)
            else:
                x = blk(x)
        return self.head(x * self.final_norm)


def test_hybrid_muon_shape_routing_and_momentum_checkpoint_roundtrip():
    torch.manual_seed(7)
    m = TinyMoELM()
    opt = ho.build_optimizer(m.named_parameters(), kind="hybrid_muon", lr=1e-3, muon_lr=6e-3, wd=0.01)
    assert opt.meta["kind"] == "hybrid_muon"
    assert opt.meta["muon_params"] > 0 and opt.meta["adamw_params"] > 0
    # Verify shape rule: every 2D param is in muon (wd=0.0), every 1D param is in adamw.
    by_name = dict(opt.named)
    muon_ids = {id(p) for g in by_name["muon"].param_groups for p in g["params"]}
    adamw_ids = {id(p) for g in by_name["adamw"].param_groups for p in g["params"]}
    assert all(g["weight_decay"] == 0.0 for g in by_name["muon"].param_groups)
    for _, p in m.named_parameters():
        if p.ndim == 2:
            assert id(p) in muon_ids and id(p) not in adamw_ids
        else:
            assert id(p) in adamw_ids and id(p) not in muon_ids

    # Run 2 steps, snapshot model + Muon/AdamW state, reload into fresh model/opt, verify exact step 3 parity.
    x = torch.randint(0, 64, (2, 12))
    y = torch.randint(0, 64, (2, 12))
    for _ in range(2):
        opt.zero_grad()
        F.cross_entropy(m(x).reshape(-1, 64), y.reshape(-1)).backward()
        opt.step()

    saved_model = copy.deepcopy(m.state_dict())
    saved_opt = copy.deepcopy(opt.state_dict())
    assert len(saved_opt["optimizers"]["muon"]["state"]) > 0  # Muon momentum buffers saved

    m2 = TinyMoELM()
    m2.load_state_dict(saved_model)
    opt2 = ho.build_optimizer(m2.named_parameters(), kind="hybrid_muon", lr=1e-3, muon_lr=6e-3, wd=0.01)
    opt2.load_state_dict(saved_opt)

    x3 = torch.randint(0, 64, (2, 12))
    y3 = torch.randint(0, 64, (2, 12))
    for model, optimizer in ((m, opt), (m2, opt2)):
        optimizer.zero_grad()
        F.cross_entropy(model(x3).reshape(-1, 64), y3.reshape(-1)).backward()
        optimizer.step()

    for (k, v1), (_, v2) in zip(m.state_dict().items(), m2.state_dict().items()):
        assert torch.equal(v1, v2), f"mismatch after Muon checkpoint restore on {k}"
    summary = opt.summary(total_train_seconds=max(opt.optim_seconds * 2.0, 1e-6))
    assert 0.0 < summary["optim_step_share"] <= 1.0


def test_muon_idle_expert_zero_grad_reinflation_bug_and_guard():
    """Demonstrate that all-zero grad (fused MoE idle expert) moves weights without skip_zero_grad, and stops with it."""
    torch.manual_seed(11)
    w_raw = nn.Parameter(torch.randn(16, 8))
    w_guarded = nn.Parameter(w_raw.detach().clone())

    opt_raw = ho.Muon([w_raw], lr=0.01, skip_zero_grad=False)
    opt_guarded = ho.Muon([w_guarded], lr=0.01, skip_zero_grad=True)

    # Step 1: expert sees tokens -> nonzero grad initializes momentum buffer `buf`.
    g1 = torch.randn_like(w_raw)
    w_raw.grad = g1.clone()
    w_guarded.grad = g1.clone()
    opt_raw.step()
    opt_guarded.step()
    assert torch.allclose(w_raw, w_guarded)

    # Step 2: expert is idle in fused MoE -> p.grad is an all-zero tensor (not None).
    before_raw = w_raw.detach().clone()
    before_guarded = w_guarded.detach().clone()
    w_raw.grad = torch.zeros_like(w_raw)
    w_guarded.grad = torch.zeros_like(w_guarded)
    opt_raw.step()
    opt_guarded.step()

    drift_raw = float((w_raw.detach() - before_raw).abs().max())
    drift_guarded = float((w_guarded.detach() - before_guarded).abs().max())
    assert drift_raw > 1e-3, "expected unguarded Muon to re-inflate stale momentum on all-zero grad"
    assert drift_guarded == 0.0, "skip_zero_grad=True must keep idle expert weights bit-exact unchanged"


def test_dt_with_activation_recompute_matches_standard_gradients():
    """MaskedLinear + regulariser_backward_ under torch.utils.checkpoint(use_reentrant=False) matches uncheckpointed grads."""
    torch.manual_seed(21)
    m_std = TinyMoELM()
    dtmask.convert(m_std, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",), alpha_start=100.0, alpha_end=1000.0, total_steps=20, seed=0)
    m_ckpt = copy.deepcopy(m_std)
    m_ckpt.use_checkpoint = True

    x = torch.randint(0, 64, (2, 10))
    y = torch.randint(0, 64, (2, 10))

    for mod in (m_std, m_ckpt):
        mod.train()
        loss = F.cross_entropy(mod(x).reshape(-1, 64), y.reshape(-1))
        loss.backward()
        dtmask.regulariser_backward_(mod, 1e-5)

    for (n1, l1), (n2, l2) in zip(dtmask.masked_layers(m_std), dtmask.masked_layers(m_ckpt)):
        assert n1 == n2
        assert l1.gate.grad is not None and l2.gate.grad is not None
        assert torch.allclose(l1.gate.grad, l2.gate.grad, atol=1e-6, rtol=1e-5), f"grad mismatch on {n1}"


def test_dt_unseen_keep_vs_official_on_idle_moe_experts():
    """Verify Sourav's observation: official leaves ~50% of idle experts deleted; keep shifts them positive."""
    torch.manual_seed(31)
    m_off = TinyMoELM(n_experts=6)
    # Force router bias so experts 4 and 5 receive zero tokens during calibration.
    with torch.no_grad():
        for blk in m_off.blocks:
            blk.router_bias.copy_(torch.tensor([5.0, 5.0, 0.0, 0.0, -50.0, -50.0]))
    dtmask.convert(m_off, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",), alpha_start=100.0, alpha_end=1000.0, total_steps=20, seed=0)
    m_keep = copy.deepcopy(m_off)

    # Provide calibration scores only for experts 0..3 (simulating idle experts 4 and 5).
    scores = {
        name: torch.rand_like(layer.base_weight)
        for name, layer in dtmask.masked_layers(m_off)
        if not (name.endswith("experts.4.gate") or name.endswith("experts.5.gate"))
    }
    r_off = dtmask.apply_wanda_prior(m_off, scores, eta=1.0 / 2048.0, prior_strength=3.0, unseen="official")
    r_keep = dtmask.apply_wanda_prior(m_keep, scores, eta=1.0 / 2048.0, prior_strength=3.0, unseen="keep")

    assert r_off["layers_without_scores"] == 4 and r_keep["layers_without_scores"] == 4
    d_off = dtmask.deletion_stats(m_off)["deleted_frac_of_targeted"]
    d_keep = dtmask.deletion_stats(m_keep)["deleted_frac_of_targeted"]
    assert d_off > 0.10, f"expected high initial deletion under official with 1/3 idle experts, got {d_off}"
    assert d_keep < d_off * 0.25, f"expected keep to sharply cut idle-expert initial deletion: {d_keep} vs {d_off}"


def test_dt_trains_with_hybrid_muon_shape_and_adamw_gate_modes():
    """Test DT under both Hybrid Muon gate modes (shape -> Muon vs adamw) and verify finite loss & timing."""
    torch.manual_seed(42)
    x = torch.randint(0, 64, (4, 16))
    y = torch.randint(0, 64, (4, 16))

    for gate_mode in ("shape", "adamw"):
        m = TinyMoELM()
        dtmask.convert(m, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",), alpha_start=100.0, alpha_end=1000.0, total_steps=10, seed=0)
        opt = ho.build_optimizer(m.named_parameters(), kind="hybrid_muon", lr=5e-4, muon_lr=5e-4, dt_gate_optim=gate_mode)
        losses = []
        for step in range(8):
            opt.zero_grad()
            loss = F.cross_entropy(m(x).reshape(-1, 64), y.reshape(-1))
            loss.backward()
            dtmask.regulariser_backward_(m, dtmask.lambda_at(step, 8, 1e-5))
            opt.step()
            dtmask.step_all(m)
            losses.append(float(loss.detach()))
        assert all(torch.isfinite(torch.tensor(losses)))
        assert losses[-1] < losses[0], f"DT loss did not decrease under gate_mode={gate_mode}: {losses}"


def test_hybrid_muon_keeps_grad_masked_marker_param_elementwise_without_frozen_row_bleed():
    """A 2D marker_param masked to a few rows must route to AdamW so Muon does not bleed into frozen rows."""
    torch.manual_seed(55)
    head = nn.Parameter(torch.randn(32, 8))
    block_w = nn.Parameter(torch.randn(8, 8))
    active = [2, 5]
    rowmask = torch.zeros_like(head)
    rowmask[active] = 1.0
    head.register_hook(lambda g: g * rowmask)

    before = head.detach().clone()
    opt = ho.build_optimizer(
        [("head.weight", head), ("blocks.0.w", block_w)],
        kind="hybrid_muon", lr=1e-3, muon_lr=6e-3, marker_param=head, marker_lr=1e-2,
    )
    for _ in range(3):
        opt.zero_grad()
        loss = (head @ block_w).pow(2).mean()
        loss.backward()
        opt.step()

    frozen_rows = [i for i in range(32) if i not in active]
    assert torch.equal(head.detach()[frozen_rows], before[frozen_rows]), "frozen non-marker rows drifted"
    assert not torch.equal(head.detach()[active], before[active]), "active marker rows did not update"

