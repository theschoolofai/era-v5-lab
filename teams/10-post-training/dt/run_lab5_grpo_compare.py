"""Reproducible Lab 5 GRPO 3-arm comparison (Full FT vs LoRA vs DT) with shared base weights & rollout cache.

CPU stand-in routed MoE (2 layers, d=48, h=96, 6 experts top-2, 2 seeds). Compares:
  - full_hybrid_muon (Hybrid Muon, shape-based)
  - lora_adamw (LoRA r=8 on expert gate projections)
  - dt_adamw (Deletion Tuning on expert gate projections, AdamW)

Uses a single shared base checkpoint per seed and caches initial-step rollouts in `rl-loop/rollout_cache.py`
across arms (Design Task 6: Waste). Reports held-out verifiable toy reward, held-out forgetting delta-bpb,
step time, optimizer step-time share, delta storage, and rollout-cache reuse stats.

Scope label: CPU stand-in, mechanics and relative comparison only, not a quality or scale claim.

Usage:
    python teams/10-post-training/dt/run_lab5_grpo_compare.py --steps 12 --seeds 1 2 \
        --out teams/10-post-training/results/lab5_grpo_dt_vs_fft.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
import tempfile
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

TEAM10 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEAM10 / "dt"))
sys.path.insert(0, str(TEAM10 / "capstone"))
sys.path.insert(0, str(TEAM10 / "rl-loop"))

import grpo  # noqa: E402
import hybrid_optim as ho  # noqa: E402
import mask as dtmask  # noqa: E402
import rollout_cache as rc  # noqa: E402
from run_lab5_dt_checks import _add_lora  # noqa: E402
from test_lab5_dt_compat import TinyMoELM  # noqa: E402

VOCAB = 64
TARGET_TOKEN = 7  # verifiable toy rule: reward = 1.0 iff completion contains TARGET_TOKEN at least once


def _state_sha256(state: dict) -> str:
    h = hashlib.sha256()
    for k in sorted(state):
        v = state[k]
        if isinstance(v, torch.Tensor):
            h.update(k.encode("utf-8"))
            h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


@torch.no_grad()
def _heldout_bpb(model: nn.Module, seqs: torch.Tensor) -> float:
    model.eval()
    logits = model(seqs[:, :-1])
    nll = F.cross_entropy(logits.reshape(-1, VOCAB), seqs[:, 1:].reshape(-1), reduction="mean")
    return float(nll.item() / math.log(2.0))  # 1 byte per synthetic token


def _seq_logprobs(model: nn.Module, seq: torch.Tensor, prompt_len: int) -> torch.Tensor:
    logits = model(seq[:, :-1])
    logp = F.log_softmax(logits, dim=-1)
    tok_lp = logp.gather(-1, seq[:, 1:].unsqueeze(-1)).squeeze(-1)
    return tok_lp[:, prompt_len - 1 :]  # completion tokens only


@torch.no_grad()
def _sample_group(model: nn.Module, prompts: torch.Tensor, k: int, max_new: int, gen: torch.Generator) -> dict:
    model.eval()
    B, P = prompts.shape
    seq = prompts.repeat_interleave(k, dim=0)
    lps = []
    for _ in range(max_new):
        logits = model(seq)[:, -1, :]
        probs = F.softmax(logits, dim=-1)
        nxt = torch.multinomial(probs, num_samples=1, generator=gen)
        lp = torch.log(probs.gather(-1, nxt).clamp_min(1e-12))
        seq = torch.cat([seq, nxt], dim=1)
        lps.append(lp)
    rollout_lp = torch.cat(lps, dim=1)  # [B*k, max_new]
    comp = seq[:, P:]
    rewards = (comp == TARGET_TOKEN).any(dim=1).float()
    cmask = torch.ones_like(rollout_lp)
    return {"seq": seq, "rollout_lp": rollout_lp, "cmask": cmask, "rewards": rewards, "prompt_len": P}


def _eval_reward(model: nn.Module, prompts: torch.Tensor, k: int, max_new: int, seed: int) -> float:
    gen = torch.Generator().manual_seed(seed)
    out = _sample_group(model, prompts, k, max_new, gen)
    return float(out["rewards"].mean().item())


def run_grpo_arm(
    arm: str,
    base_state: dict,
    base_sha: str,
    train_prompts: torch.Tensor,
    heldout_prompts: torch.Tensor,
    heldout_text: torch.Tensor,
    base_bpb: float,
    base_reward: float,
    cache: rc.RolloutCache,
    steps: int,
    seed: int,
) -> dict:
    torch.manual_seed(seed)
    m = TinyMoELM(vocab=VOCAB, d=48, hidden=96, n_layers=2, n_experts=6)
    m.load_state_dict(copy.deepcopy(base_state))

    is_dt = arm == "dt_adamw"
    if arm == "full_hybrid_muon":
        opt = ho.build_optimizer(m.named_parameters(), kind="hybrid_muon", lr=1e-3, muon_lr=3e-3)
    elif arm == "lora_adamw":
        _add_lora(m, r=8, alpha=16.0)
        opt = ho.build_optimizer(m.named_parameters(), kind="adamw", lr=2e-3)
    elif arm == "dt_adamw":
        dtmask.convert(
            m, ("re:blocks\\.[0-9]+\\.experts\\.[0-9]+\\.gate",),
            alpha_start=100.0, alpha_end=1000.0, total_steps=steps, seed=seed,
        )
        opt = ho.build_optimizer(m.named_parameters(), kind="adamw", lr=1e-3)
    else:
        raise ValueError(arm)

    trainable_params = sum(p.numel() for p in m.parameters() if p.requires_grad)
    k, max_new = 8, 6
    gen = torch.Generator().manual_seed(500 + seed)
    t0 = time.perf_counter()
    rollout_s = 0.0
    updates = 0
    step0_key = rc.cache_key(
        checkpoint_sha256=base_sha,
        prompt_ids=[f"p{i}" for i in range(train_prompts.shape[0])],
        sampler_cfg={"k": k, "max_new": max_new, "seed": 500 + seed, "temp": 1.0},
    )

    for step in range(steps):
        ts = time.perf_counter()
        batch = None
        if step == 0:
            batch = cache.get(step0_key)
        if batch is None:
            batch = _sample_group(m, train_prompts, k=k, max_new=max_new, gen=gen)
            if step == 0:
                cache.put(step0_key, batch, meta={"seed": seed, "arm_writer": arm})
        rollout_s += time.perf_counter() - ts

        # objective_v1 update: centered advantages per group, drop equal-reward groups, closed trust-region mask
        m.train()
        opt.zero_grad()
        B = train_prompts.shape[0]
        seq, old_lp, cmask, rew, P = batch["seq"], batch["rollout_lp"], batch["cmask"], batch["rewards"], batch["prompt_len"]
        new_lp = _seq_logprobs(m, seq, P)
        loss_terms = []
        total_tok = 0
        for b in range(B):
            sl = slice(b * k, (b + 1) * k)
            adv = grpo.advantages(rew[sl], "objective_v1")
            if adv is None:
                continue
            num, st = grpo.objective_v1_terms(new_lp[sl], old_lp[sl], adv, cmask[sl], eps=grpo.TR_EPSILON)
            loss_terms.append(num)
            total_tok += int(st["tokens"])
        if loss_terms and total_tok > 0:
            loss = torch.stack(loss_terms).sum() / total_tok
            loss.backward()
            if is_dt:
                dtmask.regulariser_backward_(m, dtmask.lambda_at(step, steps, 1e-5))
            torch.nn.utils.clip_grad_norm_([p for p in m.parameters() if p.requires_grad], 1.0)
            opt.step()
            if is_dt:
                dtmask.step_all(m)
            updates += 1

    wall_s = time.perf_counter() - t0
    after_reward = _eval_reward(m, heldout_prompts, k=8, max_new=max_new, seed=900 + seed)
    after_bpb = _heldout_bpb(m, heldout_text)
    opt_sum = opt.summary(wall_s)
    del_frac = dtmask.deletion_stats(m)["deleted_frac_of_targeted"] if is_dt else 0.0
    storage_bytes = (trainable_params // 8) if is_dt else (trainable_params * 2)
    return {
        "arm": arm,
        "seed": seed,
        "steps": steps,
        "updates": updates,
        "trainable_params": trainable_params,
        "heldout_reward_before": round(base_reward, 4),
        "heldout_reward_after": round(after_reward, 4),
        "heldout_reward_delta": round(after_reward - base_reward, 4),
        "heldout_bpb_before": round(base_bpb, 4),
        "heldout_bpb_after": round(after_bpb, 4),
        "forgetting_delta_bpb": round(after_bpb - base_bpb, 4),
        "wall_seconds": round(wall_s, 4),
        "rollout_seconds": round(rollout_s, 4),
        "optim_seconds": opt_sum["optim_seconds"],
        "optim_step_share": opt_sum["optim_step_share"],
        "deleted_frac_targeted": round(del_frac, 4),
        "delta_storage_bytes": storage_bytes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=12)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    arms = ["full_hybrid_muon", "lora_adamw", "dt_adamw"]
    runs = []
    cache_stats = []
    with tempfile.TemporaryDirectory(prefix="g10-grpo-cache-") as tmp:
        for seed in args.seeds:
            torch.manual_seed(200 + seed)
            base = TinyMoELM(vocab=VOCAB, d=48, hidden=96, n_layers=2, n_experts=6)
            base_state = copy.deepcopy(base.state_dict())
            base_sha = _state_sha256(base_state)
            train_prompts = torch.randint(0, VOCAB, (6, 6))
            heldout_prompts = torch.randint(0, VOCAB, (8, 6))
            heldout_text = torch.randint(0, VOCAB, (8, 12))
            base_bpb = _heldout_bpb(base, heldout_text)
            base_reward = _eval_reward(base, heldout_prompts, k=8, max_new=6, seed=900 + seed)
            cache = rc.RolloutCache(Path(tmp) / f"seed_{seed}")
            for arm in arms:
                runs.append(run_grpo_arm(
                    arm, base_state, base_sha, train_prompts, heldout_prompts, heldout_text,
                    base_bpb, base_reward, cache, args.steps, seed,
                ))
            cache_stats.append({"seed": seed, **cache.stats()})

    payload = {
        "scope": "CPU stand-in routed MoE (2 layers, d=48, h=96, 6 experts top-2); mechanics and relative comparison only, not a scale claim",
        "seeds": args.seeds,
        "steps": args.steps,
        "arms": runs,
        "rollout_cache": cache_stats,
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
