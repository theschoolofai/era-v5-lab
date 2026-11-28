"""Tiny random models for the quant_error tests: an OLMoE, our ERNIE export, and their GGUF files.

    tiny_olmoe(dir) -> HF folder    tiny_ernie(dir) -> HF folder    to_gguf(hf_dir, out, outtype) -> out

The weights are random (every tensor different from every other, so a swapped mapping cannot pass a test); only the
plumbing is tested. Inputs each fixture needs:
  tiny_olmoe  OLMoE's config and tokenizer files: the Hugging Face cache, or the Hub on first use
  tiny_ernie  the frozen p1536 tokenizer.json: $P1536_TOKENIZER, else teams/03-tokenizer/release/tokenizer.json (G3's
              release folder; the file is not committed, its sha256 is in that folder's SHA256SUMS)
  to_gguf     LLAMA_CPP_DIR, a llama.cpp b12359 checkout
A missing input raises `Unavailable`, a unittest.SkipTest: a test that builds the fixture is skipped with the message,
and any other caller can catch it. Anything else (a tokenizer with the wrong sha256, a failing script) is an error.
Tests build fixtures through a `Built` cache, inside the tests (never in setUpModule, where a skip skips the module).
"""
import hashlib, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from typing import Callable

import torch

HERE = Path(__file__).resolve().parent
TEAM = HERE.parent  # teams/12-quantization

OLMOE_REPO, OLMOE_REVISION = 'allenai/OLMoE-1B-7B-0924', '6d84c48581ece794365f2b8e9cfb043c68ade9c5'
OLMOE_TOKENIZER_FILES = ('tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json')
P1536 = Path(os.environ.get('P1536_TOKENIZER') or TEAM.parent / '03-tokenizer/release/tokenizer.json')
P1536_SHA256 = 'e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b'
ERNIE = 'Ernie4_5_MoeForCausalLM'


class Unavailable(unittest.SkipTest):
    """An input a fixture needs is not on this machine (see the module docstring)."""


class Built:
    """One test module's fixtures, each built once, on first use, in a temporary folder that close() removes.

        built = Built();  built('olmoe', tiny_olmoe)   # tiny_olmoe(<folder>/olmoe), cached under 'olmoe'

    A fixture that lacks an input skips every test that asks for it: its Unavailable is cached and raised again."""

    def __init__(self):
        self._tmp, self._cache = tempfile.TemporaryDirectory(), {}

    def __call__(self, key: str, make: Callable[[Path], Path]) -> Path:
        if key not in self._cache:
            try:
                self._cache[key] = make(Path(self._tmp.name) / key)
            except Unavailable as e:
                self._cache[key] = e
        if isinstance(self._cache[key], Unavailable):
            raise Unavailable(str(self._cache[key]))
        return self._cache[key]

    def close(self) -> None:
        self._tmp.cleanup()


def _run(cmd: list) -> None:
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f'{Path(str(cmd[1])).name} failed (exit {r.returncode}):\n{r.stderr[-3000:]}')


def _randomize(model: torch.nn.Module, std: float = 0.1, seed: int = 0) -> None:
    """As make_random_checkpoint.py: matrices N(0, std), vectors (norm weights) U(0.5, 1.5)."""
    g = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        for p in model.parameters():
            p.uniform_(0.5, 1.5, generator=g) if p.ndim == 1 else p.normal_(std=std, generator=g)


def tiny_olmoe(dir: Path) -> Path:
    """OLMoE-1B-7B's config at 2 layers, hidden 64, 4 experts (width 32), top-2, its own tokenizer and vocabulary; fp32."""
    from huggingface_hub import hf_hub_download
    from huggingface_hub.errors import LocalEntryNotFoundError
    from transformers import OlmoeConfig, OlmoeForCausalLM
    dir = Path(dir)
    try:   # all four files before any work: offline without a cache, nothing is written
        files = {f: Path(hf_hub_download(OLMOE_REPO, f, revision=OLMOE_REVISION))
                 for f in ('config.json', *OLMOE_TOKENIZER_FILES)}
    except LocalEntryNotFoundError as e:
        raise Unavailable(f'tiny_olmoe: {OLMOE_REPO}@{OLMOE_REVISION[:12]} files are not cached and the Hub cannot be '
                          f'reached ({type(e).__name__})') from e
    config = OlmoeConfig.from_json_file(files['config.json'])
    config.update(dict(num_hidden_layers=2, hidden_size=64, intermediate_size=32, num_attention_heads=4,
                       num_key_value_heads=4, num_experts=4, num_experts_per_tok=2, dtype='float32'))
    model = OlmoeForCausalLM(config)
    _randomize(model)
    model.save_pretrained(dir)
    for f in OLMOE_TOKENIZER_FILES:
        shutil.copyfile(files[f], dir / f)
    return dir


def tiny_ernie(dir: Path) -> Path:
    """Our path at 2 layers, d 64 (16 experts, KAS V2 head, active router bias): make_random_checkpoint.py, then
    export_hf.py --target ernie4_5_moe --dtype fp32 --drop-head-bias. Returns the HF folder, dir/hf (G5 run in dir/run)."""
    if not P1536.is_file():
        raise Unavailable(f'tiny_ernie: no p1536 tokenizer at {P1536}; set P1536_TOKENIZER to the frozen tokenizer.json')
    if hashlib.sha256(P1536.read_bytes()).hexdigest() != P1536_SHA256:
        raise ValueError(f'{P1536} is not the frozen p1536 tokenizer (sha256 {P1536_SHA256})')
    dir = Path(dir)
    run, hf = dir / 'run', dir / 'hf'
    _run([sys.executable, TEAM / 'scripts/make_random_checkpoint.py', '--tokenizer', P1536, '--out', run,
          '--n-layer', 2, '--d-model', 64, '--head-mode', 'kas_v2', '--bias-gamma', 0.001, '--router-bias-std', 0.01])
    _run([sys.executable, TEAM / 'scripts/export_hf.py', '--checkpoint', run, '--out', hf, '--target', 'ernie4_5_moe',
          '--dtype', 'fp32', '--drop-head-bias', '--tokenizer', P1536])
    return hf


def to_gguf(hf_dir: Path, out: Path, outtype: str) -> Path:
    """GGUF of an HF folder with llama.cpp's converter (LLAMA_CPP_DIR). Our ERNIE export goes through Team 12's
    convert_frozen() (frozen tokenizer, forced pre-tokenizer, BPE vocabulary step); anything else through the stock one."""
    llama = os.environ.get('LLAMA_CPP_DIR')
    if not llama:
        raise Unavailable('to_gguf: set LLAMA_CPP_DIR to a llama.cpp b12359 checkout')
    hf_dir, out = Path(hf_dir), Path(out)
    arch = json.loads((hf_dir / 'config.json').read_text(encoding='utf-8'))['architectures'][0]
    if arch == ERNIE:
        if str(TEAM / 'tokenizer') not in sys.path:
            sys.path.insert(0, str(TEAM / 'tokenizer'))
        import convert_frozen
        work = out.parent / f'{out.name}.work'
        convert_frozen.convert_frozen(hf_dir, hf_dir / 'tokenizer.json', P1536_SHA256, Path(llama), out, work,
                                      outtype=outtype, python=sys.executable)
        shutil.rmtree(work)
    else:
        _run([sys.executable, Path(llama) / 'convert_hf_to_gguf.py', hf_dir, '--outfile', out, '--outtype', outtype])
    return out
