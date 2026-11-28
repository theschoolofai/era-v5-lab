#!/usr/bin/env python3
"""Fewer positions per text, fewer decode steps: what it buys at inference (G12 with G6, lead item 7, third part).

    python tokens_per_text.py count   --texts DIR --tokenizer p1536=PATH --tokenizer sarvam-1=sarvamai/sarvam-1@REV ... --out counts.json
    python tokens_per_text.py speed   --gguf model.gguf [--gguf other.gguf] --out speed.json
    python tokens_per_text.py combine --counts counts.json --speed speed.json --base p1536 --out tokens_per_text.md

count    (needs `tokenizers`) cuts each <lang>.txt into excerpts of about --chunk-chars characters (whole lines), and counts
         tokens per excerpt for every tokenizer, with no special tokens added. A tokenizer given as PATH or as a Hugging
         Face repo (optionally @revision). Reports tokens per 1,000 characters and per word, per language.
speed    (needs llama-cpp-python) measures the real decode time per token of a GGUF at several context lengths (a prefix of
         fixed ids, then greedy decoding that ignores EOS), median of --repeats, and reads the KV-cache size per token
         from the GGUF metadata (K and V in f16: 2 x layers x kv heads x head dim x 2 bytes).
combine  turns both into, per language and tokenizer: decode steps per 1,000 characters (= tokens), projected decode seconds
         per 1,000 characters (steps x the measured step time, which grows linearly with context: a + b x context), and KV-cache
         bytes per 1,000 characters; each next to the base tokenizer's value.

Limits that go with every number: the model is the same GGUF for every tokenizer (the dry-run-2-shaped stand-in, random
weights: step time does not depend on the weight values), so a tokenizer with another vocabulary size would change the
embedding and head cost a little; that is not modelled. Texts are excerpts of Wikipedia articles (CC BY-SA, not committed);
only aggregate counts are written. Speed is one machine, labelled in the output, and is not a 16 GB or 32 GB laptop.
"""
from __future__ import annotations

import argparse, json, platform, statistics, sys, time
from pathlib import Path


# ---------------------------------------------------------------------------------------------- counting
def make_chunks(lines: list[str], chunk_chars: int, max_chunks: int) -> list[str]:
    """Whole lines joined until a chunk has at least chunk_chars characters; the first max_chunks full chunks."""
    chunks, cur, n = [], [], 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        cur.append(line); n += len(line) + 1
        if n >= chunk_chars:
            chunks.append("\n".join(cur)); cur, n = [], 0
            if len(chunks) >= max_chunks:
                break
    return chunks


def load_tokenizer(spec: str):
    from tokenizers import Tokenizer
    name, _, src = spec.partition("=")
    if Path(src).is_file():
        return name, Tokenizer.from_file(src)
    repo, _, rev = src.partition("@")
    return name, Tokenizer.from_pretrained(repo, revision=rev or None)


def count_command(a) -> int:
    texts = {p.stem: p for p in sorted(Path(a.texts).glob("*.txt"))}
    tokenizers = dict(load_tokenizer(s) for s in a.tokenizer)
    out = {"chunk_chars": a.chunk_chars, "tokenizers": list(tokenizers), "languages": {}}
    for lang, path in texts.items():
        chunks = make_chunks(path.read_text(encoding="utf-8").splitlines(), a.chunk_chars, a.max_chunks)
        if not chunks:
            continue
        chars = sum(len(c) for c in chunks)
        row = {"chunks": len(chunks), "chars": chars, "bytes": sum(len(c.encode()) for c in chunks),
               "words": sum(len(c.split()) for c in chunks), "tokens": {}, "tokens_per_chunk": {}}
        for name, tok in tokenizers.items():
            per = [len(tok.encode(c, add_special_tokens=False).ids) for c in chunks]
            row["tokens"][name] = sum(per)
            row["tokens_per_chunk"][name] = per
        out["languages"][lang] = row
        print(lang, {n: round(1000 * t / chars, 1) for n, t in row["tokens"].items()}, "tokens per 1000 chars", flush=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    return 0


# ---------------------------------------------------------------------------------------------- speed
def fit_line(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Least squares y = a + b x."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return my - b * mx, b


def kv_bytes_per_token(n_layer: int, n_kv_head: int, head_dim: int, bytes_per_value: int = 2) -> int:
    return 2 * n_layer * n_kv_head * head_dim * bytes_per_value


def speed_command(a) -> int:
    from llama_cpp import Llama
    out = {"machine": f"{platform.machine()} {platform.system()} {platform.processor() or ''}".strip(), "decode_tokens": a.decode,
           "context_points": a.ctx, "models": {}}
    for path in a.gguf:
        llm = Llama(model_path=path, n_ctx=max(a.ctx) + a.decode + 8, n_gpu_layers=a.n_gpu_layers, seed=1, verbose=False)
        md = llm.metadata
        arch = md["general.architecture"]
        n_layer, n_head, n_kv = int(md[f"{arch}.block_count"]), int(md[f"{arch}.attention.head_count"]), int(md[f"{arch}.attention.head_count_kv"])
        head_dim = int(md.get(f"{arch}.attention.key_length", int(md[f"{arch}.embedding_length"]) // n_head))
        points = []
        for c in a.ctx:
            times = []
            for _ in range(a.repeats):
                llm.reset()
                prefix = [(7 * i + 13) % 1000 + 100 for i in range(max(c, 1))]
                llm.eval(prefix)
                t0 = time.perf_counter(); n = 0
                for tok in llm.generate(prefix[-1:], temp=0.0, reset=False):   # greedy, EOS ignored: always a - full - decode
                    n += 1
                    if n >= a.decode:
                        break
                times.append((time.perf_counter() - t0) / n * 1000)
            points.append({"context": c, "ms_per_token": round(statistics.median(times), 3), "all_ms": [round(x, 3) for x in times]})
            print(Path(path).name, "context", c, points[-1]["ms_per_token"], "ms/token", flush=True)
        out["models"][Path(path).name] = {"points": points, "n_layer": n_layer, "n_kv_head": n_kv, "head_dim": head_dim,
                                         "kv_bytes_per_token": kv_bytes_per_token(n_layer, n_kv, head_dim)}
        del llm
    Path(a.out).write_text(json.dumps(out, indent=1))
    return 0


# ---------------------------------------------------------------------------------------------- combine
def decode_seconds(n_tokens: float, a_ms: float, b_ms_per_ctx: float) -> float:
    """Time to decode n_tokens one by one from an empty context: sum over steps of a + b x position."""
    return (n_tokens * a_ms + b_ms_per_ctx * n_tokens * (n_tokens - 1) / 2) / 1000


def project(counts: dict, model: dict, base: str) -> dict:
    a_ms, b_ms = fit_line([p["context"] for p in model["points"]], [p["ms_per_token"] for p in model["points"]])
    kv = model["kv_bytes_per_token"]
    rows = {}
    for lang, row in counts["languages"].items():
        per_k = 1000 / row["chars"]
        res = {}
        for name, per_chunk in row["tokens_per_chunk"].items():
            n_chunk = sum(per_chunk) / len(per_chunk)
            chars_chunk = row["chars"] / row["chunks"]
            steps = row["tokens"][name] * per_k
            secs = decode_seconds(n_chunk, a_ms, b_ms) * (1000 / chars_chunk)       # time of an average excerpt, per 1,000 chars
            res[name] = {"steps_per_1000_chars": steps, "seconds_per_1000_chars": secs, "kv_bytes_per_1000_chars": steps * kv,
                         "tokens_per_word": row["tokens"][name] / row["words"]}
        for name, r in res.items():
            r["steps_vs_base"] = r["steps_per_1000_chars"] / res[base]["steps_per_1000_chars"]
            r["seconds_vs_base"] = r["seconds_per_1000_chars"] / res[base]["seconds_per_1000_chars"]
        rows[lang] = res
    return {"a_ms": a_ms, "b_ms_per_context_token": b_ms, "kv_bytes_per_token": kv, "languages": rows}


def render(counts: dict, speed: dict, base: str) -> str:
    names = counts["tokenizers"]
    lines = ["# Decode steps, time and KV memory per 1,000 characters, by tokenizer", "",
             f"Excerpts of about {counts['chunk_chars']} characters per language; machine: {speed['machine']}; "
             f"decode of {speed['decode_tokens']} tokens per timing point. Base tokenizer: `{base}`. Model: the same GGUF for every tokenizer.", ""]
    for mname, model in speed["models"].items():
        pr = project(counts, model, base)
        lines += [f"## {mname}", "",
                  f"Step time fit: {pr['a_ms']:.2f} ms + {pr['b_ms_per_context_token'] * 1000:.3f} microseconds per context token; "
                  f"KV cache {pr['kv_bytes_per_token']} bytes per token (f16). Measured points: "
                  + ", ".join(f"{p['context']}: {p['ms_per_token']} ms" for p in model["points"]) + ".", ""]
        for title, key, fmt in (("Decode steps per 1,000 characters (tokens)", "steps_per_1000_chars", "{:.0f}"),
                                ("Projected decode seconds per 1,000 characters", "seconds_per_1000_chars", "{:.2f}"),
                                ("KV-cache KB per 1,000 characters", "kv_bytes_per_1000_chars", "{:.0f}")):
            lines += [f"### {title}", "", "| Language | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
            for lang, res in pr["languages"].items():
                cells = []
                for n in names:
                    v = res[n][key] / (1000 if key == "kv_bytes_per_1000_chars" else 1)
                    ratio = res[n]["steps_vs_base" if key != "seconds_per_1000_chars" else "seconds_vs_base"]
                    cells.append(fmt.format(v) + ("" if n == base else f" ({ratio:.2f}x)"))
                lines.append(f"| {lang} | " + " | ".join(cells) + " |")
            lines.append("")
    return "\n".join(lines) + "\n"


def combine_command(a) -> int:
    counts, speed = json.loads(Path(a.counts).read_text()), json.loads(Path(a.speed).read_text())
    if a.base not in counts["tokenizers"]:
        sys.exit(f"base tokenizer {a.base!r} is not in {counts['tokenizers']}")
    Path(a.out).write_text(render(counts, speed, a.base))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("count"); c.add_argument("--texts", required=True); c.add_argument("--tokenizer", action="append", required=True, metavar="NAME=PATH|REPO[@REV]")
    c.add_argument("--chunk-chars", type=int, default=1000); c.add_argument("--max-chunks", type=int, default=30); c.add_argument("--out", required=True)
    s = sub.add_parser("speed"); s.add_argument("--gguf", action="append", required=True); s.add_argument("--out", required=True)
    s.add_argument("--ctx", type=lambda v: [int(x) for x in v.split(",")], default=[0, 1024, 2048, 4096]); s.add_argument("--decode", type=int, default=64)
    s.add_argument("--repeats", type=int, default=3); s.add_argument("--n-gpu-layers", type=int, default=0)
    k = sub.add_parser("combine"); k.add_argument("--counts", required=True); k.add_argument("--speed", required=True)
    k.add_argument("--base", required=True); k.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"count": count_command, "speed": speed_command, "combine": combine_command}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
