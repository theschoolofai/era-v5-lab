#!/usr/bin/env python3
"""Run the KE2 experiment for P = 32 and P = 64 and write one summary.

Steps (each can be skipped with ``--skip``):

``tables``           decode and raw byte tables, every P                         (build_tables.py)
``proofs``           Lemma 1, Lemma 2 and Theorem 1 on the real tokenizer          (proofs/proof_checks.py)
``decode_ref``       forward-encode a sample of IDs, decode with the reference
                     decoder, and repeat the hash in a fresh process              (decode_ref.py)
``cpu_determinism``  tokenizer decoding in three fresh CPU processes             (determinism/tokenizer_decode_cpu.py)
``mps``              forward codec on MPS vs CPU, three fresh processes, if MPS  (determinism/codec_v1_cpu_mps.py)

Then ``results/experiment/summary.json`` and ``experiment.md`` (team folder) are written from the
step outputs. Steps that start fresh processes run as subprocesses, so one step cannot leak state
into another.

Usage
-----
    python src/run_experiment.py [--tokenizer-dir DIR] [--pos-dims 32 64] [--sample 4096] [--skip mps ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import platform
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):  # run as a script: make ke2 and the upstream codec importable
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ke2.upstream import ensure_kronecker_embeddings

    ensure_kronecker_embeddings()

import numpy as np

import decode_ref
from ke2.codec import encode_ids
from ke2.config import POS_DIMS, SRC_DIR, TEAM_DIR, TOKENIZER_SHA256
from ke2.tables import KINDS, ByteTable, table_path
from ke2.tokenizer import load_tokenizer, resolve_tokenizer_path
from ke2.upstream import ensure_kronecker_embeddings

log = logging.getLogger("run_experiment")

STEPS = ("tables", "proofs", "decode_ref", "cpu_determinism", "mps")


@dataclass(frozen=True)
class Context:
    tokenizer_dir: Path
    pos_dims: tuple[int, ...]
    results: Path
    sample: int
    seed: int

    @property
    def tables_dir(self) -> Path:
        return self.results / "tables"


def _run(cmd: Sequence[str | Path]) -> subprocess.CompletedProcess:
    """Run a command (fails on a non-zero exit); log it with absolute paths shortened to file names."""
    args = [str(c) for c in cmd]
    log.info("$ %s", " ".join(Path(a).name if Path(a).is_absolute() else a for a in args[1:]))
    return subprocess.run(args, check=True, capture_output=True, text=True)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


# --------------------------------------------------------------------------- #
# Steps
# --------------------------------------------------------------------------- #
def step_tables(ctx: Context) -> None:
    _run([sys.executable, SRC_DIR / "build_tables.py", "--tokenizer", ctx.tokenizer_dir / "tokenizer.json",
          "--out", ctx.tables_dir, "--pos-dims", *map(str, ctx.pos_dims)])  # fmt: skip


def step_proofs(ctx: Context) -> None:
    _run([sys.executable, SRC_DIR / "proofs" / "proof_checks.py", ctx.tokenizer_dir, ctx.results / "proof_checks.json"])


def step_decode_ref(ctx: Context) -> None:
    """Round-trip a sample of IDs through the forward codec and the reference decoder."""
    import torch
    from kronecker_embeddings import codec as upstream_codec

    tb = load_tokenizer(str(ctx.tokenizer_dir / "tokenizer.json"), expected_sha256=TOKENIZER_SHA256)
    ids = decode_ref.sample_token_ids(tb.vocab_size, tb.special_ids, n=ctx.sample, seed=ctx.seed)
    runs: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for P in ctx.pos_dims:
            for kind in KINDS:
                path = table_path(ctx.tables_dir, kind, P)
                table = ByteTable.load(path, tokenizer=tb)
                vectors = encode_ids(ids, table).numpy()
                start = time.perf_counter()
                result = decode_ref.decode(vectors, decode_ref.CodeTable.from_byte_table(table))
                seconds = time.perf_counter() - start
                vectors_file = Path(tmp) / f"{kind}_P{P}.npy"
                np.save(vectors_file, vectors)
                fresh = _run([sys.executable, SRC_DIR / "decode_ref.py", "--table", path, "--vectors", vectors_file])
                expected_bytes = [table.row(int(i)) for i in ids]
                runs[f"{kind}_P{P}"] = {
                    "kind": kind,
                    "pos_dim": P,
                    "table_sha256": table.sha256(),
                    "vectors": len(ids),
                    "candidate_count": table.vocab_size,
                    "byte_comparison": "stored table-row bytes; original payloads only for raw tables",
                    "ids_recovered": int((result.token_ids == ids).sum()),
                    "bytes_recovered": int(
                        sum(a == b for a, b in zip(result.token_bytes, expected_bytes, strict=True))
                    ),
                    "ties": int((result.margins == 0).sum()),
                    "min_margin": float(result.margins.min()),
                    "median_margin": float(np.median(result.margins)),
                    "min_score": float(result.scores.min()),
                    "sha256": result.sha256(),
                    "fresh_process_sha256_equal": fresh.stdout.strip() == result.sha256(),
                    "seconds": round(seconds, 1),
                }
                log.info("decode_ref %-6s P=%d: %d/%d IDs, min margin %.4g, hash %s…", kind, P,
                         runs[f"{kind}_P{P}"]["ids_recovered"], len(ids), result.margins.min(),
                         result.sha256()[:12])  # fmt: skip
    _write_json(ctx.results / "decode_ref" / "summary.json", {
        "format": decode_ref.HASH_FORMAT,
        "encoder": "upstream kronecker_codec, float32, CPU",
        "decoder": "decode_ref.py, cosine similarity, float64, CPU, exhaustive over the vocabulary",
        "metric": "cosine similarity",
        "margin": "best cosine minus second-best cosine across all candidates",
        "determinism_scope": "same tested environment; repeats, query chunk sizes and a fresh process",
        "timing_scope": "seconds include code-table construction and decode; exclude forward encoding and fresh-process run",
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
                        "system": platform.system(), "machine": platform.machine(), "device": "cpu"},
        "source_sha256": {
            "decode_ref.py": hashlib.sha256(Path(decode_ref.__file__).read_bytes()).hexdigest(),
            "run_experiment.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "ke2/codec.py": hashlib.sha256((SRC_DIR / "ke2/codec.py").read_bytes()).hexdigest(),
            "ke2/tables.py": hashlib.sha256((SRC_DIR / "ke2/tables.py").read_bytes()).hexdigest(),
            "upstream_codec.py": hashlib.sha256(Path(upstream_codec.__file__).read_bytes()).hexdigest(),
        },
        "sample": {"n": len(ids), "seed": ctx.seed, "edges": "0, 77, 173, V-1, first 8 special IDs",
                   "query_token_ids": ids.tolist()},
        "runs": runs,
    })  # fmt: skip


def step_cpu_determinism(ctx: Context) -> None:
    _run([sys.executable, SRC_DIR / "determinism" / "tokenizer_decode_cpu.py", "--tokenizer",
          ctx.tokenizer_dir / "tokenizer.json", "--expected-sha256", TOKENIZER_SHA256, "--out", ctx.results])  # fmt: skip


def step_mps(ctx: Context) -> None:
    import torch

    if not torch.backends.mps.is_available():
        log.warning("mps: skipped (MPS not available on this machine)")
        return
    _run([sys.executable, SRC_DIR / "determinism" / "codec_v1_cpu_mps.py", "--tables", ctx.tables_dir,
          "--codec-src", ensure_kronecker_embeddings(), "--out", ctx.results])  # fmt: skip


STEP_FUNCS: dict[str, Callable[[Context], None]] = {
    "tables": step_tables,
    "proofs": step_proofs,
    "decode_ref": step_decode_ref,
    "cpu_determinism": step_cpu_determinism,
    "mps": step_mps,
}


# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
def summarize(ctx: Context) -> dict:
    """Collect the step outputs into one record per P."""
    manifest = _read_json(ctx.tables_dir / "manifest.json") or {}
    proofs = _read_json(ctx.results / "proof_checks.json") or {}
    decoded = (_read_json(ctx.results / "decode_ref" / "summary.json") or {}).get("runs", {})
    cpu = _read_json(ctx.results / "tokenizer_decode_cpu_metadata.json") or {}
    mps = (_read_json(ctx.results / "codec_v1_cpu_mps_results.json") or {}).get("summary", {})
    per_p = {}
    for P in ctx.pos_dims:
        entry: dict = {"D": 256 * P}
        for kind in KINDS:
            t = manifest.get("tables", {}).get(f"{kind}_table_P{P}.npz", {})
            pr = proofs.get(f"P{P}_{kind}", {})
            entry[kind] = {
                "table_sha256": t.get("sha256"),
                "unique_rows": t.get("n_unique_rows"),
                "colliding_tokens": t.get("n_colliding_tokens"),
                "fffd_rows": t.get("n_rows_containing_U+FFFD"),
                "truncated": t.get("n_truncated"),
                "theorem1_partitions_equal": all(pr.get(d, {}).get("partitions_equal") for d in ("float32", "bfloat16"))
                if pr
                else None,
                "distinct_codes_fp32": pr.get("float32", {}).get("distinct_codes"),
                "collision_groups": pr.get("groups"),
                "pair_causes": pr.get("pair_causes"),
                "decode_ref": decoded.get(f"{kind}_P{P}"),
            }
        entry["bf16_min_gap"] = proofs.get(f"P{P}_bf16_min_gap")
        entry["mps"] = mps.get(str(P))
        per_p[str(P)] = entry
    runs = cpu.get("runs", [])
    return {
        "tokenizer_sha256": manifest.get("tokenizer", {}).get("sha256"),
        "vocab_size": manifest.get("tokenizer", {}).get("vocab_size"),
        "max_raw_byte_length": manifest.get("max_raw_byte_length"),
        "cpu_decode_determinism": {
            "all_match": cpu.get("all_match"),
            "sha256": runs[0]["sha256"] if runs else None,
            "runs": len(runs),
        },
        "per_pos_dim": per_p,
    }


def _fmt(value) -> str:
    if value is None:
        return "–"
    if isinstance(value, bool):
        return "yes" if value else "**no**"
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def render_markdown(summary: dict, pos_dims: Sequence[int]) -> str:
    """The P = 32 vs P = 64 comparison as a Markdown page."""
    cols = [f"P={P} {kind}" for P in pos_dims for kind in KINDS]
    cells = [(str(P), kind) for P in pos_dims for kind in KINDS]

    def row(label: str, get) -> str:
        values = []
        for P, kind in cells:
            try:
                values.append(_fmt(get(summary["per_pos_dim"][P], kind)))
            except (KeyError, TypeError):
                values.append("–")
        return f"| {label} | " + " | ".join(values) + " |"

    def dr(field):
        return lambda e, k: (e[k]["decode_ref"] or {})[field]

    lines = [
        "# KE2 experiment: P = 32 vs P = 64",
        "",
        "Generated by `python src/run_experiment.py` from the files under `results/`. Do not edit by hand.",
        "",
        f"Tokenizer: BrahmicTokenizer-131K, `tokenizer.json` SHA-256 `{summary['tokenizer_sha256']}`, "
        f"V = {_fmt(summary['vocab_size'])}, longest token {summary['max_raw_byte_length']} bytes.",
        "",
        "## Tables, Theorem 1 and the reference decoder",
        "",
        "| | " + " | ".join(cols) + " |",
        "|---|" + "---|" * len(cols),
        row("code dimension D", lambda e, k: e["D"]),
        row("unique rows", lambda e, k: e[k]["unique_rows"]),
        row("colliding tokens (V − unique)", lambda e, k: e[k]["colliding_tokens"]),
        row("rows containing U+FFFD", lambda e, k: e[k]["fffd_rows"]),
        row("tokens truncated", lambda e, k: e[k]["truncated"]),
        row("distinct codes (fp32)", lambda e, k: e[k]["distinct_codes_fp32"]),
        row("collision groups", lambda e, k: e[k]["collision_groups"]),
        row("Theorem 1: code groups = cut-string groups (fp32, bf16)", lambda e, k: e[k]["theorem1_partitions_equal"]),
        row("decode_ref: IDs recovered", lambda e, k: f"{dr('ids_recovered')(e, k):,} / {dr('vectors')(e, k):,}"),
        row(
            "decode_ref: stored table bytes matched",
            lambda e, k: f"{dr('bytes_recovered')(e, k):,} / {dr('vectors')(e, k):,}",
        ),
        row("decode_ref: ties (margin 0)", dr("ties")),
        row("decode_ref: min margin (cosine)", dr("min_margin")),
        row("decode_ref: median margin", dr("median_margin")),
        row("decode_ref: same hash in a fresh process", dr("fresh_process_sha256_equal")),
        "",
        "The reference checks sampled query IDs against every vocabulary candidate; these are full-vocabulary cosine margins.",
        "Decode-table ties arise when partial-character tokens become U+FFFD and share rows; ties return the lowest ID.",
        "Stored decode-table byte agreement does not recover original token bytes lost during text decoding.",
        "Raw-table byte matches preserve original payloads. See [decode_ref.md](decode_ref.md) for scope and performance.",
        "",
        "## Determinism",
        "",
    ]
    cpu = summary["cpu_decode_determinism"]
    lines.append(
        f"- CPU tokenizer decoding, {cpu['runs']} fresh processes: all match = {_fmt(cpu['all_match'])}, "
        f"SHA-256 `{cpu['sha256']}`."
    )
    for P in pos_dims:
        m = summary["per_pos_dim"][str(P)].get("mps")
        if m:
            lines.append(
                f"- MPS forward codec, P={P}: three MPS hashes match = {_fmt(m['mps_three_hashes_match'])}, "
                f"CPU vs MPS within tolerance = {_fmt(m['cpu_mps_all_close'])}, "
                f"max abs difference {_fmt(m['max_absolute_difference'])} (bitwise equal: {'yes' if m['cpu_mps_bitwise_equal'] else 'no, as expected for float32 on MPS'})."
            )
        else:
            lines.append(f"- MPS forward codec, P={P}: not run.")
    for P in pos_dims:
        r = (summary["per_pos_dim"][str(P)]["raw"] or {}).get("decode_ref")
        if r:
            lines.append(f"- decode_ref hash, raw table, P={P}: `{r['sha256']}`.")
    lines.append("")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tokenizer-dir", type=Path, help="folder with tokenizer.json and special_tokens_map.json")
    ap.add_argument("--pos-dims", type=int, nargs="+", default=list(POS_DIMS))
    ap.add_argument("--sample", type=int, default=4096, help="token IDs in the decode_ref round trip")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--results", type=Path, default=TEAM_DIR / "results")
    ap.add_argument("--skip", nargs="*", default=[], choices=STEPS)
    ap.add_argument("--summary-md", type=Path, default=TEAM_DIR / "experiment.md")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    tokenizer_dir = (a.tokenizer_dir or resolve_tokenizer_path().parent).resolve()
    ctx = Context(tokenizer_dir, tuple(a.pos_dims), a.results.resolve(), a.sample, a.seed)
    for name in STEPS:
        if name in a.skip:
            log.info("== %s: skipped", name)
            continue
        log.info("== %s", name)
        start = time.perf_counter()
        try:
            STEP_FUNCS[name](ctx)
        except subprocess.CalledProcessError as e:
            log.error("step %s failed:\n%s", name, (e.stderr or e.stdout or "").strip())
            return 1
        log.info("== %s done in %.0fs", name, time.perf_counter() - start)

    summary = summarize(ctx)
    _write_json(ctx.results / "experiment" / "summary.json", summary)
    a.summary_md.write_text(render_markdown(summary, ctx.pos_dims), encoding="utf-8")
    log.info("wrote %s and %s", ctx.results / "experiment" / "summary.json", a.summary_md.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
