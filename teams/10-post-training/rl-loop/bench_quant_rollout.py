"""Measure quantized rollouts: speed and mismatch per scheme (`speed`), and GRPO learning on them (`learn`).

    python rl-loop/bench_quant_rollout.py speed --schemes copy int8_dynamic --out out/quant_speed.json
    python rl-loop/bench_quant_rollout.py learn --seeds 1 2 3 --out out/quant_learn.json
    python rl-loop/bench_quant_rollout.py coverage --out out/quant_coverage.json
    python rl-loop/bench_quant_rollout.py export --out out/rollout_check_export.json

`speed`: every scheme samples the same prompts with the same seeds through quant_rollout.QuantRolloutSampler. Without
--model-path the model is a randomly initialised Llama of the size given (speed is real for that shape; its mismatch
numbers say nothing about a trained model). One untimed warm-up call per scheme; schemes are interleaved across repeats
so that drift of the machine falls on all of them. Throughput counts generated tokens over the whole sample() call, the
copy's refresh included; `decode_tok_s` leaves the refresh out. Other load on the machine changes the numbers: the JSON
keeps the 1-minute load average before and after, and each scheme's slowest and fastest repeat.

`learn`: the trainer's tiny OLMoE smoke run (toy task), objective_v1 or grpo, once with the exact sampler and once per
scheme, per seed: held-out reward on the learner, and the logged mismatch.

`coverage`: TSAI's rule for speed claims. One forward and backward of the learner on the tokens each scheme sampled,
against the tokens of the exact copy: the trainable parameters whose gradient is None or all zero, on the speed model and
on the tiny OLMoE (router frozen).

`export`: what one train.rollout_check step costs the trainer: building the rollout copy, and writing and hashing both
weights files, on the model shape of --manifest (untrained weights, random byte table), with the file sizes.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import sys
import tempfile
import time
from pathlib import Path

import torch
import yaml

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "dt")]

import quant_rollout as qr  # noqa: E402
import rollout_check  # noqa: E402
import router  # noqa: E402
import train  # noqa: E402
from check_grad_coverage import audit_grads  # noqa: E402
from policy import completion_logprobs, hf_policy  # noqa: E402


def build(args):
    import transformers  # noqa: PLC0415
    torch.manual_seed(args.model_seed)
    if args.model_path:
        model = transformers.AutoModelForCausalLM.from_pretrained(args.model_path, local_files_only=True,
                                                                  torch_dtype=getattr(torch, args.dtype))
        desc = {"path": str(args.model_path)}
    else:
        cfg = transformers.LlamaConfig(vocab_size=args.vocab, hidden_size=args.hidden, intermediate_size=4 * args.hidden,
                                       num_hidden_layers=args.layers, num_attention_heads=args.heads,
                                       num_key_value_heads=args.heads, tie_word_embeddings=False, bos_token_id=None,
                                       eos_token_id=None, pad_token_id=None,
                                       max_position_embeddings=args.prompt_len + args.max_new + 8)
        model = transformers.LlamaForCausalLM(cfg).to(getattr(torch, args.dtype))
        desc = {"random_llama": {"vocab": args.vocab, "hidden": args.hidden, "layers": args.layers, "heads": args.heads}}
    desc["parameters"] = sum(p.numel() for p in model.parameters())
    return hf_policy(model.eval(), None, args.device), desc


def gap(policy, rolls, prompts) -> dict:
    """Sampler against learner on the sampled tokens: r = log pi_learner - log pi_sampler."""
    parts = []
    with torch.no_grad():
        for p, r in zip(prompts, rolls):
            parts.append((completion_logprobs(policy, r.seq, len(p)) - r.rollout_lp)[r.cmask])
    r = torch.cat(parts).double()
    out = ((r < math.log(0.8)) | (r > math.log(1.2))).double().mean()
    return {"tokens": int(r.numel()), "k3": float((r.exp() - 1 - r).mean()), "abs_logratio": float(r.abs().mean()),
            "outside_0.8_1.2": float(out)}


def load_average() -> float | None:
    return round(os.getloadavg()[0], 2) if hasattr(os, "getloadavg") else None


def speed(args) -> dict:
    if args.threads:
        torch.set_num_threads(args.threads)
    load_before = load_average()
    policy, desc = build(args)
    vocab = policy.model.config.vocab_size
    g = torch.Generator().manual_seed(args.model_seed)
    prompts = [torch.randint(0, vocab, (args.prompt_len,), generator=g).tolist() for _ in range(args.prompts)]
    samplers = {s: qr.QuantRolloutSampler(policy, s) for s in args.schemes}

    def call(name, seed):
        if args.device.startswith("cuda"):
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()
        rolls = samplers[name].sample(prompts, args.k, args.max_new, 1.0, torch.Generator().manual_seed(seed))
        if args.device.startswith("cuda"):
            torch.cuda.synchronize()
            peak_gb = round(torch.cuda.max_memory_allocated() / (1024 ** 3), 4)
        else:
            peak_gb = None
        total = time.perf_counter() - t0
        return rolls, total, samplers[name].last["refresh_s"], peak_gb

    for name in args.schemes:  # warm-up at the measured shape
        call(name, 0)
    runs = {s: [] for s in args.schemes}
    for rep in range(args.repeats):
        for name in args.schemes:
            rolls, total, refresh, peak_gb = call(name, 100 + rep)
            tokens = int(sum(int(r.cmask.sum()) for r in rolls))
            rec = {"seconds": total, "refresh_s": refresh, "tokens": tokens, "tok_s": tokens / total,
                   "decode_tok_s": tokens / (total - refresh), **gap(policy, rolls, prompts)}
            if peak_gb is not None:
                rec["peak_vram_gb"] = peak_gb
            runs[name].append(rec)
            row = {k: round(v, 5) for k, v in runs[name][-1].items()}
            print(json.dumps({"scheme": name, "repeat": rep, **row}), flush=True)
    table = {}
    for name, rs in runs.items():
        med = {k: statistics.median(r[k] for r in rs) for k in rs[0]}
        med.update(tok_s_min=min(r["tok_s"] for r in rs), tok_s_max=max(r["tok_s"] for r in rs),
                   simulated=name in qr.SIMULATED)
        table[name] = med
    base = table.get("copy")
    if base:
        for name, m in table.items():
            m["speed_up_vs_copy"] = m["tok_s"] / base["tok_s"]
    out_doc = {"mode": "speed", "load_average_1m": {"before": load_before, "after": load_average()}, "model": desc,
               "device": args.device, "dtype": args.dtype, "threads": torch.get_num_threads(),
               "cpu": platform.processor() or platform.machine(), "torch": torch.__version__,
               "prompts": args.prompts, "k": args.k, "prompt_len": args.prompt_len, "max_new": args.max_new,
               "repeats": args.repeats, "median": table, "runs": runs}
    if args.device.startswith("cuda") and torch.cuda.is_available():
        out_doc["gpu_name"] = torch.cuda.get_device_name(0)
    return out_doc


def learn(args) -> dict:
    base = yaml.safe_load((HERE / "config" / "smoke_tiny_olmoe.yaml").read_text())
    arms = ["exact", *args.schemes]
    results = []
    for seed in args.seeds:
        for arm in arms:
            cfg = json.loads(json.dumps(base))
            cfg.update(seed=seed, verbose=False)
            cfg["train"].update(algo=args.algo, steps=args.steps, eval_every=args.steps, ppo_epochs=args.ppo_epochs)
            if args.algo == "grpo" and arm != "exact":
                cfg["train"]["tis_clip"] = args.tis_clip
            if arm != "exact":
                cfg["train"].update(sampler="quant", quant={"scheme": arm, "guard": True})
            with tempfile.TemporaryDirectory() as tmp:
                cfg["out_dir"] = tmp
                s = train.train(cfg)
                rows = [json.loads(x) for x in (Path(tmp) / "metrics.jsonl").read_text().splitlines()]
                evals = [json.loads(x) for x in (Path(tmp) / "evals.jsonl").read_text().splitlines()]
            quant_end = [e["pass"] for e in evals if e["name"] == "heldout_quant"]
            rec = {"seed": seed, "arm": arm, "steps": s["steps"], "heldout_start": s["heldout_reward_start"],
                   "heldout_end": s["heldout_reward_end"], "heldout_end_quant_copy": quant_end[-1] if quant_end else None,
                   "mean_mismatch_k3": s.get("mean_mismatch_k3"),
                   "max_mismatch_k3": max((r["mismatch_k3"] for r in rows if "mismatch_k3" in r), default=None),
                   "mean_masked_frac": (statistics.mean(r["masked_frac"] for r in rows if "masked_frac" in r)
                                        if any("masked_frac" in r for r in rows) else None),
                   "router_unchanged": s["router_unchanged"], "seconds": s["seconds"]}
            print(json.dumps(rec), flush=True)
            results.append(rec)
    return {"mode": "learn", "config": "rl-loop/config/smoke_tiny_olmoe.yaml", "algo": args.algo, "steps": args.steps,
            "ppo_epochs": args.ppo_epochs, "tis_clip": args.tis_clip if args.algo == "grpo" else None,
            "torch": torch.__version__, "runs": results}


def coverage(args) -> dict:
    base = yaml.safe_load((HERE / "config" / "smoke_tiny_olmoe.yaml").read_text())
    torch.manual_seed(base["seed"])
    olmoe_device = "cpu" if "int8_dynamic" in args.olmoe_schemes else args.device
    tiny, _ = train.build_model(base["model"], olmoe_device)
    router.freeze_router(tiny.model, router.ROUTER_PATTERNS)
    task = train.build_task(base["task"], None, base["seed"])
    llama, desc = build(args)
    g = torch.Generator().manual_seed(args.model_seed)
    random_prompts = [torch.randint(0, llama.model.config.vocab_size, (args.prompt_len,), generator=g).tolist()
                      for _ in range(args.prompts)]
    cases = [("speed_model", llama, random_prompts, args.k, args.max_new, args.schemes),
             ("tiny_olmoe", tiny, task.train[:base["train"]["prompts_per_step"]], base["train"]["k"],
              base["train"]["max_new"], args.olmoe_schemes)]
    checks = []
    for name, policy, prompts, k, max_new, schemes in cases:
        reference = None
        for scheme in ["copy", *[x for x in schemes if x != "copy"]]:
            sampler = qr.QuantRolloutSampler(policy, scheme)
            rolls = sampler.sample(prompts, k, max_new, 1.0, torch.Generator().manual_seed(0))
            policy.model.zero_grad(set_to_none=True)
            for p, r in zip(prompts, rolls):
                (-completion_logprobs(policy, r.seq, len(p))[r.cmask].sum()).backward()
            a = audit_grads(policy.model)
            lists = [sorted(x["name"] for x in a[key]) for key in ("none_grads", "zero_grads")]
            reference = reference or lists
            checks.append({"model": name, "device": policy.device, "scheme": scheme,
                           "trainable_tensors": a["trainable_tensors"],
                           "none_grads": lists[0], "zero_grads": lists[1], "lists_identical_to_copy": lists == reference})
            print(json.dumps({"model": name, "device": policy.device, "scheme": scheme,
                              "trainable": a["trainable_tensors"],
                              "none": len(lists[0]), "zero": len(lists[1]), "identical": lists == reference}), flush=True)
        policy.model.zero_grad(set_to_none=True)
    out_doc = {"mode": "coverage", "device": args.device, "speed_model": desc, "torch": torch.__version__, "checks": checks}
    if args.device.startswith("cuda") and torch.cuda.is_available():
        out_doc["gpu_name"] = torch.cuda.get_device_name(0)
    return out_doc


def export(args) -> dict:
    sys.path.append(str(HERE.parents[1] / "05-architecture" / "harness"))  # after rl-loop: it has its own train.py
    from week2.model import LanguageModel  # noqa: PLC0415
    if args.threads:
        torch.set_num_threads(args.threads)
    m = json.loads(args.manifest.read_text(encoding="utf-8"))["config"]["model"]
    g = torch.Generator().manual_seed(0)
    rows = torch.randint(0, 256, (m["vocab_size"], m["ke_max_pos"]), generator=g, dtype=torch.uint8)
    lengths = torch.randint(1, 5, (m["vocab_size"],), generator=g)
    torch.manual_seed(1234)
    model = LanguageModel(m, rows, lengths).eval()
    runs, load_before = [], load_average()
    with tempfile.TemporaryDirectory(dir=args.work_dir) as tmp:
        for rep in range(1, args.repeats + 1):
            for scheme in args.schemes:
                t0 = time.perf_counter()
                copy_ = qr.quantized_copy(model, scheme)[0]
                t1 = time.perf_counter()
                d = rollout_check.export(Path(tmp), rep, model, copy_, scheme, m)
                t2 = time.perf_counter()
                sizes = {r: (d / f"{r}.safetensors").stat().st_size for r in rollout_check.ROLES}
                runs.append({"scheme": scheme, "repeat": rep, "copy_s": round(t1 - t0, 3), "write_hash_s": round(t2 - t1, 3),
                             "bytes": sizes})
                print(json.dumps(runs[-1]), flush=True)
                for r in rollout_check.ROLES:  # keep the disk use to one export at a time
                    (d / f"{r}.safetensors").unlink()
    median = {s_: {k: statistics.median([r[k] for r in runs if r["scheme"] == s_]) for k in ("copy_s", "write_hash_s")}
              for s_ in args.schemes}
    return {"mode": "export", "parameters": sum(p.numel() for p in model.parameters()), "threads": torch.get_num_threads(),
            "torch": torch.__version__, "load_average_1m": {"before": load_before, "after": load_average()}, "runs": runs,
            "median": median}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    s = sub.add_parser("speed")
    cov = sub.add_parser("coverage")
    for p, schemes in ((s, ["copy", "int8_dynamic", "w8a8_sim", "w4a16_sim"]), (cov, ["copy", "int8_dynamic", "bf16"])):
        p.add_argument("--model-path", type=Path, help="local Hugging Face folder; default: a random Llama")
        p.add_argument("--schemes", nargs="+", default=schemes, choices=qr.SCHEMES)
        p.add_argument("--vocab", type=int, default=32000)
        p.add_argument("--hidden", type=int, default=768)
        p.add_argument("--layers", type=int, default=8)
        p.add_argument("--heads", type=int, default=12)
        p.add_argument("--prompts", type=int, default=4)
        p.add_argument("--k", type=int, default=8)
        p.add_argument("--prompt-len", type=int, default=128)
        p.add_argument("--max-new", type=int, default=128)
        p.add_argument("--dtype", default="float32", choices=("float32", "bfloat16", "float16"))
        p.add_argument("--device", default="cpu")
        p.add_argument("--model-seed", type=int, default=0)
    s.add_argument("--repeats", type=int, default=3)
    s.add_argument("--threads", type=int, default=0, help="torch CPU threads (0 = torch's default)")
    cov.add_argument("--olmoe-schemes", nargs="+", default=["int8_dynamic", "w8a8_sim", "w4a16_sim", "bf16"],
                     choices=qr.SCHEMES)
    le = sub.add_parser("learn")
    le.add_argument("--schemes", nargs="+", default=["copy", "int8_dynamic", "w8a8_sim", "w4a16_sim"], choices=qr.SCHEMES)
    le.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    le.add_argument("--algo", default="objective_v1", choices=("objective_v1", "grpo"))
    le.add_argument("--steps", type=int, default=80)
    le.add_argument("--ppo-epochs", type=int, default=1)
    le.add_argument("--tis-clip", type=float, default=2.0)
    ex = sub.add_parser("export")
    ex.add_argument("--manifest", type=Path,
                    default=HERE.parents[1] / "05-architecture" / "results" / "dryrun2-1234" / "manifest.json")
    ex.add_argument("--schemes", nargs="+", default=["bf16", "w4a16_sim"],
                    choices=[x for x in qr.SCHEMES if x != "int8_dynamic"])
    ex.add_argument("--repeats", type=int, default=3)
    ex.add_argument("--threads", type=int, default=0)
    ex.add_argument("--work-dir", type=Path, help="where the files are written for timing (default: the temp folder)")
    for p in (s, le, cov, ex):
        p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    result = {"speed": speed, "learn": learn, "coverage": coverage, "export": export}[a.mode](a)
    result["command"] = "bench_quant_rollout.py " + " ".join(map(str, argv if argv is not None else sys.argv[1:]))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    summary = result.get("median") or {k: len(result[k]) for k in ("runs", "checks") if k in result}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
