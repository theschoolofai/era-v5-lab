"""What users actually get from llama.cpp: KL divergence, same-top-1 and PPL ratio of each quantized GGUF against the
reference GGUF (bf16), separately for each held-out text slice.

Reuses Team 12's quality/kl_eval.py for the llama-perplexity call and the regexes of its summary lines, so the numbers
are in the team's format. Rows hold numbers only (no text, no token ids).

The llama.cpp version is not read here: a shallow checkout reports "build 1", so the caller records it from git.
"""
import importlib.util, re
from argparse import Namespace
from pathlib import Path

from tokenizers import Tokenizer

_spec = importlib.util.spec_from_file_location('kl_eval', Path(__file__).resolve().parents[1] / 'quality' / 'kl_eval.py')
kl_eval = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(kl_eval)

NGL = 99  # all layers on the GPU (Metal), as kl_eval's default


def plan_chunks(n_tokens: int, ctx: int, max_chunks: int) -> int:
    """Whole ctx-token chunks the text fills, at most max_chunks."""
    return min(max_chunks, n_tokens // ctx)


def _parse(log: str, where: str) -> dict:
    """The numbers of one llama-perplexity KL log, by kl_eval.PATTERNS ('<key>' and '<key>_unc')."""
    out = {}
    for key, pat in kl_eval.PATTERNS.items():
        m = re.search(pat, log)
        if not m:
            raise RuntimeError(f'{where}: no "{key}" in the llama-perplexity output')
        out[key] = float(m.group(1))
        if m.lastindex > 1:
            out[f'{key}_unc'] = float(m.group(2))
    return out


def run_kl_slices(ref: Path, quants: dict[str, Path], slice_files: dict[str, Path], tokenizer_json: Path,
                  llama_bin: Path, work: Path, ctx: int = 512, max_chunks: int = 8, runner=None) -> list[dict]:
    """One row per (slice, format): chunks, tokens_scored, ppl_ratio(+_unc), kld_mean(+_unc), kld_99, same_top_p, time_s.

    llama_bin is the directory with the llama.cpp binaries. A slice too short for one chunk gives one row with
    chunks = 0 and no numbers. runner(args, gguf, ngl, extra, log) -> (log text, seconds) defaults to
    kl_eval.perplexity. Each slice's base file (~260 KB per scored token at a 131k vocabulary) is deleted right
    after that slice's format passes."""
    runner = runner or kl_eval.perplexity
    tok = Tokenizer.from_file(str(tokenizer_json))
    work = Path(work)
    logs = work / 'kl-logs'
    logs.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, path in slice_files.items():
        n_tokens = len(tok.encode(Path(path).read_text(encoding='utf-8'), add_special_tokens=False).ids)
        chunks = plan_chunks(n_tokens, ctx, max_chunks)
        if chunks == 0:
            rows.append({'slice': name, 'format': None, 'chunks': 0})
            continue
        args = Namespace(llama_bin=str(llama_bin), ctx=ctx, chunks=chunks)
        base = work / f'{name}.kld'
        try:
            runner(args, ref, NGL, ['-f', str(path), '--kl-divergence-base', str(base)], logs / f'{name}-base.log')
            if not base.exists():
                raise RuntimeError(f'{name}: the base pass wrote no {base}')
            for fmt, gguf in quants.items():
                log, secs = runner(args, gguf, NGL, ['--kl-divergence-base', str(base), '--kl-divergence'],
                                   logs / f'{name}-{fmt}.log')
                p = _parse(log, f'{name} {fmt}')
                rows.append({'slice': name, 'format': fmt, 'chunks': chunks,
                             'tokens_scored': chunks * (ctx - 1 - ctx // 2),  # llama.cpp scores the 2nd half of each chunk
                             'ppl_ratio': p['ppl_ratio'], 'ppl_ratio_unc': p['ppl_ratio_unc'],
                             'kld_mean': p['kld_mean'], 'kld_mean_unc': p['kld_mean_unc'], 'kld_99': p['kld_99'],
                             'same_top_p': p['same_top_p'], 'time_s': round(secs, 1)})
        finally:
            base.unlink(missing_ok=True)
    return rows
