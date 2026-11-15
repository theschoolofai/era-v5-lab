#!/usr/bin/env python3
"""The flow on one checkpoint, then 100 fixed prompts (G12 week 3, core task 5). No network, no keys, writes only to --out.

    python scripts/flow_fixed_prompts.py --checkpoint <hf dir> --tokenizer <tokenizer.json> --tokenizer-sha256 <64 hex> \\
        --llama-cpp <b11669 checkout> --llama-quantize <bin> [--formats Q4_K_M,Q8_0] [--out out] [--eos "<|endoftext|>"]

1. checks prompts/fixed_100.jsonl against prompts/fixed_100.sha256 (100 prompts, fixed ids and order);
2. tokenizer/convert_frozen.py: checkpoint + frozen tokenizer -> bf16 GGUF (refuses a tokenizer with another sha256);
3. llama-quantize each format (output layer Q8_0, as quantize_eval.py);
4. runs every prompt on bf16 and on each format: greedy (temperature 0), seed 0, same max tokens, token ids kept.

Writes out/prompts_<format>.jsonl (per prompt: id, output token ids, sha256 of the text, the text, finish reason, tokens/s)
and out/summary.json (finish reasons, mean tokens/s, agreement with bf16: identical outputs and mean shared prefix, GGUF
sha256s, versions, wall time). The prompts are our own, not from a benchmark. The GGUF files go to out/_work and are removed
at the end (--keep to keep them), so out/ stays small. The tokenizer round trip on held-out text needs the network and is
tokenizer/convert_frozen.py's own run (#467); it is not repeated here.
"""
from __future__ import annotations

import argparse, hashlib, json, platform, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tokenizer"))
import convert_frozen as cf  # noqa: E402
import gguf_roundtrip as rt  # noqa: E402


def load_prompts(path: Path) -> list[dict]:
    want = path.with_suffix(".sha256").read_text().split()[0]
    if rt.sha256(path) != want:
        sys.exit(f"refusing: {path} does not have the sha256 in {path.with_suffix('.sha256').name}")
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 100 and len({r["id"] for r in rows}) == 100, "expected 100 prompts with unique ids"
    return rows


def generate(gguf: Path, prompts: list[dict], max_tokens: int, n_ctx: int, ngl: int, out: Path) -> dict:
    from llama_cpp import Llama
    m = Llama(model_path=str(gguf), n_ctx=n_ctx, n_gpu_layers=ngl, seed=0, verbose=False)
    eos, rows, t_all = m.token_eos(), [], time.time()
    for p in prompts:
        ids_in = m.tokenize(p["prompt"].encode("utf-8"), add_bos=True, special=True)
        ids, finish, t0 = [], "length", time.time()
        for t in m.generate(ids_in, top_k=1, top_p=1.0, temp=0.0, repeat_penalty=1.0, reset=True):
            if t == eos:
                finish = "stop"; break
            ids.append(t)
            if len(ids) >= max_tokens or len(ids_in) + len(ids) >= n_ctx:
                break
        dt = time.time() - t0
        text = m.detokenize(ids).decode("utf-8", errors="replace")
        rows.append({"id": p["id"], "n_prompt_tokens": len(ids_in), "output_ids": ids, "n_output_tokens": len(ids),
                     "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], "text": text,
                     "finish_reason": finish, "tokens_per_s": round(len(ids) / dt, 2) if dt > 0 else None})
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    del m
    fin = {k: sum(r["finish_reason"] == k for r in rows) for k in ("stop", "length")}
    return {"rows": rows, "finish": fin, "wall_s": round(time.time() - t_all, 1),
            "mean_tokens_per_s": round(sum(r["tokens_per_s"] or 0 for r in rows) / len(rows), 2)}


def agreement(base: list[dict], other: list[dict]) -> dict:
    same, prefix = 0, 0.0
    for a, b in zip(base, other):
        x, y = a["output_ids"], b["output_ids"]
        k = next((i for i, (u, v) in enumerate(zip(x, y)) if u != v), min(len(x), len(y)))
        same += x == y
        prefix += k / max(len(x), len(y), 1)
    return {"identical_outputs": same, "of": len(base), "mean_shared_prefix_fraction": round(prefix / len(base), 4)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--tokenizer", type=Path, required=True)
    ap.add_argument("--tokenizer-sha256", required=True)
    ap.add_argument("--llama-cpp", type=Path, required=True, help="llama.cpp b11669 checkout (converter + gguf-py)")
    ap.add_argument("--llama-quantize", type=Path, required=True)
    ap.add_argument("--convert-python", type=Path, help="python of the converter's venv (default: this one)")
    ap.add_argument("--formats", default="Q4_K_M", help="comma list of llama-quantize types; bf16 is always run")
    ap.add_argument("--prompts", type=Path, default=HERE.parent / "prompts" / "fixed_100.jsonl")
    ap.add_argument("--out", type=Path, default=Path("out"))
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--n-ctx", type=int, default=2048)
    ap.add_argument("--ngl", type=int, default=99, help="layers on the GPU (ignored by a CPU build)")
    ap.add_argument("--bos", default="<|begin_of_text|>")
    ap.add_argument("--eos", default="<|end_of_text|>", help='the frozen tokenizer\'s is "<|endoftext|>"')
    ap.add_argument("--keep", action="store_true", help="keep the GGUF files in out/_work")
    a = ap.parse_args()

    t0, prompts = time.time(), load_prompts(a.prompts)
    work = a.out / "_work"; work.mkdir(parents=True, exist_ok=True)
    bf16 = work / "model-bf16.gguf"
    t = time.time()
    cf.convert_frozen(a.checkpoint, a.tokenizer, a.tokenizer_sha256, a.llama_cpp, bf16, work, "bf16", a.bos, a.eos, a.convert_python)
    summary = {"prompts_sha256": rt.sha256(a.prompts), "tokenizer_sha256": rt.sha256(a.tokenizer), "pre_tokenizer": cf.PRE,
               "max_tokens": a.max_tokens, "n_ctx": a.n_ctx, "decoding": "greedy (temperature 0, top_k 1), seed 0",
               "convert_s": round(time.time() - t, 1), "formats": {}}
    ggufs = {"bf16": bf16}
    for fmt in [f for f in a.formats.split(",") if f and f != "bf16"]:
        t = time.time(); ggufs[fmt] = work / f"model-{fmt}.gguf"
        subprocess.run([str(a.llama_quantize), *([] if fmt == "Q8_0" else ["--output-tensor-type", "q8_0"]),
                        str(bf16), str(ggufs[fmt]), fmt], check=True, capture_output=True)
        summary["formats"][fmt] = {"quantize_s": round(time.time() - t, 1)}
    summary["formats"]["bf16"] = {}
    runs = {}
    for fmt, g in ggufs.items():
        runs[fmt] = generate(g, prompts, a.max_tokens, a.n_ctx, a.ngl, a.out / f"prompts_{fmt}.jsonl")
        summary["formats"][fmt] |= {"gguf_sha256": rt.sha256(g), "size_bytes": g.stat().st_size,
                                    **{k: runs[fmt][k] for k in ("finish", "mean_tokens_per_s", "wall_s")}}
        if fmt != "bf16":
            summary["formats"][fmt]["agreement_with_bf16"] = agreement(runs["bf16"]["rows"], runs[fmt]["rows"])
    import llama_cpp
    summary |= {"total_s": round(time.time() - t0, 1), "machine": f"{platform.machine()} {platform.system()}",
                "versions": {"Python": platform.python_version(), "llama-cpp-python": llama_cpp.__version__},
                "llama_convert_sha256": rt.sha256(a.llama_cpp / "convert_hf_to_gguf.py")}
    (a.out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    if not a.keep:
        shutil.rmtree(work)
    print(json.dumps({k: v for k, v in summary.items() if k != "versions"}, indent=1))


if __name__ == "__main__":
    main()
