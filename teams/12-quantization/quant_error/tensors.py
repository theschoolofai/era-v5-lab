"""Per-tensor dequantization error between a quantized GGUF and its full-precision reference.

Streams one tensor (or one expert of a merged expert tensor) at a time, so a 7B model is never held in memory.
`check_pair` refuses two files that cannot be a llama-quantize output and its source; `tensor_errors` runs it first.
"""
import hashlib, math, re
from pathlib import Path

import numpy as np
import gguf

CHUNK = 1 << 22  # elements per float64 accumulation step
FULL_PRECISION = ('F32', 'F16', 'BF16')   # the only types a reference may hold (routers aside)
ROUTER_KINDS = ('router', 'router_bias')

_STEMS = {
    'attn_q': 'attn_q', 'attn_k': 'attn_k', 'attn_v': 'attn_v', 'attn_output': 'attn_output',
    'ffn_gate_inp': 'router', 'exp_probs_b': 'router_bias',
    'ffn_gate_exps': 'experts_gate', 'ffn_up_exps': 'experts_up', 'ffn_down_exps': 'experts_down',
    'ffn_gate_shexp': 'shared_gate', 'ffn_up_shexp': 'shared_up', 'ffn_down_shexp': 'shared_down',
}
_TOP = {'token_embd': 'token_embd', 'output': 'output'}


def classify(name: str) -> tuple[str, int | None]:
    """Return (kind, layer) for a GGUF tensor name; layer is None outside blk.N."""
    m = re.fullmatch(r'blk\.(\d+)\.(.+)', name)
    layer, rest = (int(m.group(1)), m.group(2)) if m else (None, name)
    stem = re.sub(r'\.(weight|bias)$', '', rest)
    if stem.endswith('_norm'):
        return 'norm', layer
    return (_STEMS if m else _TOP).get(stem, 'other'), layer


def _sums(w: np.ndarray, w_hat: np.ndarray) -> tuple[float, float, float]:
    """(sum w^2, sum (w_hat-w)^2, max |w_hat-w|), accumulated in float64 over bounded chunks."""
    w, w_hat = w.reshape(-1), w_hat.reshape(-1)
    if w.shape != w_hat.shape:
        raise ValueError(f'shape mismatch {w.shape} vs {w_hat.shape}')
    ww = dd = mx = 0.0
    for i in range(0, w.size, CHUNK):
        a = w[i:i + CHUNK].astype(np.float64)
        d = w_hat[i:i + CHUNK].astype(np.float64) - a
        ww += float(np.dot(a, a))
        dd += float(np.dot(d, d))
        mx = max(mx, float(np.abs(d).max()))
    return ww, dd, mx


def _rel(ww: float, dd: float) -> float:
    return math.sqrt(dd / ww) if ww else (0.0 if dd == 0 else math.inf)


def _sqnr(ww: float, dd: float) -> float:
    if dd == 0:
        return math.inf
    return 10 * math.log10(ww / dd) if ww else -math.inf


def rel_err(w: np.ndarray, w_hat: np.ndarray) -> float:
    """||w_hat - w||_F / ||w||_F."""
    ww, dd, _ = _sums(w, w_hat)
    return _rel(ww, dd)


def sqnr_db(w: np.ndarray, w_hat: np.ndarray) -> float:
    """10 log10(||w||^2 / ||w_hat - w||^2); inf when w_hat equals w."""
    ww, dd, _ = _sums(w, w_hat)
    return _sqnr(ww, dd)


def _dequant(tensor, index=None) -> np.ndarray:
    """float32 values of a tensor, or of expert `index` along axis 0 (quantized blocks run along the last axis)."""
    data = tensor.data if index is None else tensor.data[index]
    return gguf.quants.dequantize(data, tensor.tensor_type).astype(np.float32, copy=False)


def _tokens_sha256(reader) -> str | None:
    """sha256 of tokenizer.ggml.tokens (each token's bytes after its length), None if the file has no token list."""
    field = reader.get_field('tokenizer.ggml.tokens')
    if field is None:
        return None
    h = hashlib.sha256()
    for i in field.data:
        b = field.parts[i].tobytes()
        h.update(len(b).to_bytes(8, 'little') + b)
    return h.hexdigest()


def _architecture(reader) -> str | None:
    field = reader.get_field('general.architecture')
    return None if field is None else field.contents()


def _same_bytes(a: np.ndarray, b: np.ndarray, chunk: int = 1 << 26) -> bool:
    """Byte equality of two tensors' stored data, compared in bounded chunks of the memory maps."""
    a, b = np.asarray(a).reshape(-1).view(np.uint8), np.asarray(b).reshape(-1).view(np.uint8)
    return a.size == b.size and all(np.array_equal(a[i:i + chunk], b[i:i + chunk]) for i in range(0, a.size, chunk))


def _check(q_reader, r_reader, quant: Path, ref: Path) -> None:
    for key, get in (('general.architecture', _architecture), ('tokenizer.ggml.tokens', _tokens_sha256)):
        if get(q_reader) != get(r_reader):
            raise ValueError(f'{key} differs between {quant} and {ref}: not the same model export')
    for r in r_reader.tensors:
        if classify(r.name)[0] not in ROUTER_KINDS and r.tensor_type.name not in FULL_PRECISION:
            raise ValueError(f'tensor {r.name} is {r.tensor_type.name} in the reference {ref}; a reference holds '
                             f'F32, F16 or BF16 only')
    r_by_name = {x.name: x for x in r_reader.tensors}
    q_names = {x.name for x in q_reader.tensors}
    if q_names != set(r_by_name):
        name = min(q_names ^ set(r_by_name))
        raise ValueError(f'tensor {name} is only in {quant if name in q_names else ref}')
    for q in q_reader.tensors:
        r = r_by_name[q.name]
        if [n for n in q.shape.tolist() if n != 1] != [n for n in r.shape.tolist() if n != 1]:  # llama-quantize drops size-1 axes
            raise ValueError(f'tensor {q.name} has shape {q.shape.tolist()} in {quant} but {r.shape.tolist()} in {ref}')
        if q.tensor_type == r.tensor_type and not _same_bytes(q.data, r.data):
            raise ValueError(f'tensor {q.name} is {q.tensor_type.name} in both files but its bytes differ '
                             f'(llama-quantize copies such a tensor unchanged): {quant} is not quantized from {ref}')


def check_pair(quant: Path, ref: Path) -> None:
    """Raise ValueError, naming the tensor or metadata key, unless `quant` can be a llama-quantize output of `ref`:
    the same general.architecture and tokenizer.ggml.tokens; a reference of F32, F16 or BF16 tensors only (router
    tensors aside); the same tensor names and shapes (size-1 axes aside); and every tensor whose ggml type is the same
    in both files byte for byte the same (llama-quantize copies the tensors it does not quantize)."""
    _check(gguf.GGUFReader(str(quant)), gguf.GGUFReader(str(ref)), quant, ref)


def tensor_errors(quant: Path, ref: Path) -> list[dict]:
    """One row per tensor of `quant` (one per expert for 3-D *_exps tensors) comparing it with `ref`.

    Runs check_pair's checks first: ValueError, naming the tensor or key, for a pair that is not a quantized file and
    its reference.
    """
    q_reader, r_reader = gguf.GGUFReader(str(quant)), gguf.GGUFReader(str(ref))
    _check(q_reader, r_reader, quant, ref)
    r_by_name = {x.name: x for x in r_reader.tensors}
    rows = []
    for q in q_reader.tensors:
        r = r_by_name[q.name]
        kind, layer = classify(q.name)
        split = kind.startswith('experts_') and len(q.shape) == 3  # GGUFReader numpy axis 0 is the expert axis
        experts = range(q.data.shape[0]) if split else [None]
        numel = q.n_elements // len(experts)
        for e in experts:
            ww, dd, mx = _sums(_dequant(r, e), _dequant(q, e))
            rows.append({
                'tensor': q.name, 'layer': layer, 'kind': kind, 'expert': e, 'ggml_type': q.tensor_type.name,
                'bits_per_weight': q.n_bytes * 8 / q.n_elements, 'numel': numel,
                'rel_err': _rel(ww, dd), 'sqnr_db': _sqnr(ww, dd), 'max_abs_err': mx,
            })
    return rows
