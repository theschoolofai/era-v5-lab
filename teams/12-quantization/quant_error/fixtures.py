"""Tiny random models for the quant_error tests: an OLMoE, our ERNIE export, and their GGUF files.

    tiny_olmoe(dir) -> HF folder    tiny_ernie(dir) -> HF folder    to_gguf(hf_dir, out, outtype) -> out

The weights are random (every tensor different from every other, so a swapped mapping cannot pass a test); only the
plumbing is tested. tiny_olmoe downloads OLMoE's config and tokenizer files once (Hugging Face cache); tiny_ernie needs
the frozen p1536 tokenizer; to_gguf needs LLAMA_CPP_DIR (a llama.cpp b12359 checkout).
"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
TEAM = HERE.parent  # teams/12-quantization

OLMOE_REPO, OLMOE_REVISION = 'allenai/OLMoE-1B-7B-0924', '6d84c48581ece794365f2b8e9cfb043c68ade9c5'
OLMOE_TOKENIZER_FILES = ('tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json')
P1536 = Path.home() / 'Workspace/era-v5-data/tokenizers/p1536-sample-v0/tokenizer.json'
P1536_SHA256 = 'e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b'
ERNIE = 'Ernie4_5_MoeForCausalLM'


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
    from transformers import OlmoeConfig, OlmoeForCausalLM
    dir = Path(dir)
    get = lambda f: Path(hf_hub_download(OLMOE_REPO, f, revision=OLMOE_REVISION))  # noqa: E731
    config = OlmoeConfig.from_json_file(get('config.json'))
    config.update(dict(num_hidden_layers=2, hidden_size=64, intermediate_size=32, num_attention_heads=4,
                       num_key_value_heads=4, num_experts=4, num_experts_per_tok=2, dtype='float32'))
    model = OlmoeForCausalLM(config)
    _randomize(model)
    model.save_pretrained(dir)
    for f in OLMOE_TOKENIZER_FILES:
        shutil.copyfile(get(f), dir / f)
    return dir


def tiny_ernie(dir: Path) -> Path:
    """Our path at 2 layers, d 64 (16 experts, KAS V2 head, active router bias): make_random_checkpoint.py, then
    export_hf.py --target ernie4_5_moe --dtype fp32 --drop-head-bias. Returns the HF folder, dir/hf (G5 run in dir/run)."""
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
        raise RuntimeError('to_gguf needs LLAMA_CPP_DIR=<llama.cpp b12359 checkout>')
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
