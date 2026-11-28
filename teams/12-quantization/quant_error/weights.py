"""Model weights one stage at a time (embedding, one decoder layer, head) as fp32 tensors under the parameter names of
the transformers model, read from a Hugging Face folder or from a GGUF file.

The names and shapes are those of the transformers model's state_dict(), built from the folder's config on the meta
device. A GGUF name is found the way llama.cpp's converter (b12359, conversion/olmo.py and conversion/ernie.py) made it:
the HF name through gguf-py's TensorNameMap for the architecture, with the per-expert matrices of a layer stacked on
axis 0 into one `*_exps` tensor (GGUFReader's numpy axis 0), and ERNIE's `e_score_correction_bias` renamed to
`e_score_correction.bias` first (ModelBase.filter_tensors). Neither architecture's q/k rows are permuted by that
converter (OlmoeModel and Ernie4_5MoeModel do not call LlamaModel.permute), so there is nothing to undo. Only the tensors
of the requested stage are read (GGUFReader memory-maps the file) and dequantized.
"""
import json, re
from pathlib import Path
from typing import Protocol

import torch
import gguf
from safetensors import safe_open

# GGUF general.architecture -> transformers model_type, for the architectures whose mapping has a round-trip test
ARCHS = {'olmoe': 'olmoe', 'ernie4_5-moe': 'ernie4_5_moe'}
NEW_ARCH = ('A new architecture needs three things to pass: (1) the weights round trip (test_weights.py), (2) '
            'test_streamed_matches_full_model and test_values_match_whole_models in test_forward.py on a tiny model of it, '
            'and (3) one matched-positions check against llama.cpp (results/olmoe_pilot/matched_positions.py). Model-level '
            "glue outside the decoder layers (e.g. Granite's embedding_multiplier and logits_scaling), experts that are "
            "not nn.Linear modules (Granite's GraniteMoeParallelExperts) and a router other than mlp.gate also need "
            'changes in forward.py. See README.md, "A new architecture".')
EMBED, HEAD = 'model.embed_tokens.weight', 'lm_head.weight'
_LAYER = re.compile(r'model\.layers\.(\d+)\.')
_EXPERT = re.compile(r'(model\.layers\.\d+\.mlp\.experts)\.(\d+)\.(\w+\.weight)')


class WeightSource(Protocol):
    """fp32 tensors with full HF names; key sets equal the matching parts of the transformers model's state_dict()."""
    n_layers: int

    def embed(self) -> dict[str, torch.Tensor]: ...

    def layer(self, i: int) -> dict[str, torch.Tensor]: ...

    def head(self) -> dict[str, torch.Tensor]: ...   # final norm and lm_head


def _squeezed(shape) -> tuple[int, ...]:
    return tuple(int(n) for n in shape if n != 1)


class _Stages:
    """Splits the transformers model's state_dict() names into embed / layer i / head; subclasses implement _read."""

    def __init__(self, config_dir: Path):
        from transformers import AutoConfig, AutoModelForCausalLM
        self.config = AutoConfig.from_pretrained(config_dir)
        with torch.device('meta'):
            model = AutoModelForCausalLM.from_config(self.config)
        self.shapes: dict[str, torch.Size] = {k: v.shape for k, v in model.state_dict().items()}
        self.tied = bool(getattr(self.config, 'tie_word_embeddings', False))
        self.n_layers: int = self.config.num_hidden_layers
        self._keys: dict = {'embed': [], 'head': [], **{i: [] for i in range(self.n_layers)}}
        for k in self.shapes:
            m = _LAYER.match(k)
            stage = int(m.group(1)) if m else ('embed' if k.startswith('model.embed_tokens.') else 'head')
            self._keys[stage].append(k)

    def embed(self) -> dict[str, torch.Tensor]:
        return {k: self._read(k) for k in self._keys['embed']}

    def layer(self, i: int) -> dict[str, torch.Tensor]:
        if not 0 <= i < self.n_layers:
            raise IndexError(f'layer {i} of a {self.n_layers}-layer model')
        return {k: self._read(k) for k in self._keys[i]}

    def head(self) -> dict[str, torch.Tensor]:
        return {k: self._read(k) for k in self._keys['head']}

    def _read(self, key: str) -> torch.Tensor:
        raise NotImplementedError


class SafetensorsWeights(_Stages):
    """An HF folder (model.safetensors, or shards listed in model.safetensors.index.json)."""

    def __init__(self, hf_dir: Path):
        hf_dir = Path(hf_dir)
        super().__init__(hf_dir)
        index = hf_dir / 'model.safetensors.index.json'
        files = (sorted(set(json.loads(index.read_text(encoding='utf-8'))['weight_map'].values())) if index.exists()
                 else ['model.safetensors'])
        self._files = {f: safe_open(hf_dir / f, framework='pt') for f in files}
        stored = {k: (f, k) for f, h in self._files.items() for k in h.keys()}
        if self.tied and HEAD not in stored and EMBED in stored:
            stored[HEAD] = stored[EMBED]
        if extra := sorted(set(stored) - set(self.shapes)):
            raise ValueError(f'{hf_dir}: tensors the transformers model does not have: {extra[:5]}')
        if missing := sorted(set(self.shapes) - set(stored)):
            raise ValueError(f'{hf_dir}: no tensor for {missing[:5]}')
        self._src = stored
        for k, (f, name) in stored.items():
            got = list(self._files[f].get_slice(name).get_shape())
            if got != list(self.shapes[k]):
                raise ValueError(f'{hf_dir}: {name} has shape {got}, the transformers model wants {list(self.shapes[k])}')

    def _read(self, key: str) -> torch.Tensor:
        f, name = self._src[key]
        return self._files[f].get_tensor(name).float()


class GGUFWeights(_Stages):
    """A GGUF made by llama.cpp's converter from the HF folder `hf_config_dir` (or quantized from such a file; any
    tensor type that gguf-py can dequantize)."""

    def __init__(self, gguf_path: Path, hf_config_dir: Path):
        reader = gguf.GGUFReader(str(gguf_path))
        arch = reader.fields['general.architecture'].contents()
        if arch not in ARCHS:
            raise NotImplementedError(f'{arch}: not supported (supported: {", ".join(ARCHS)}). {NEW_ARCH}')
        super().__init__(Path(hf_config_dir))
        if self.config.model_type != ARCHS[arch]:
            raise ValueError(f'{gguf_path} is {arch}, but {hf_config_dir} is a {self.config.model_type} model')
        self._tensors = {t.name: t for t in reader.tensors}
        names = gguf.get_tensor_name_map({v: k for k, v in gguf.MODEL_ARCH_NAMES.items()}[arch], self.n_layers)
        self._src: dict[str, tuple[str, int | None]] = {}
        for k in self.shapes:
            m = _EXPERT.fullmatch(k)
            hf, expert = (f'{m.group(1)}.{m.group(3)}', int(m.group(2))) if m else (k, None)
            name = names.get_name(hf.replace('e_score_correction_bias', 'e_score_correction.bias'),
                                  try_suffixes=('.weight', '.bias'))
            if name is None:
                raise ValueError(f"{k}: gguf-py's {arch} tensor map has no name for it")
            if k == HEAD and name not in self._tensors and self.tied:   # the converter writes no output.weight
                name = names.get_name(EMBED, try_suffixes=('.weight',))
            if name not in self._tensors:
                raise ValueError(f'{gguf_path}: no tensor {name} for {k}')
            self._src[k] = (name, expert)
        if extra := sorted(set(self._tensors) - {name for name, _ in self._src.values()}):
            raise ValueError(f'{gguf_path}: tensors with no transformers parameter: {extra[:5]}')
        self._check_shapes(gguf_path)

    def _check_shapes(self, gguf_path) -> None:
        """Each GGUF tensor has the shape its HF parameters ask for, experts stacked on axis 0; size-1 axes aside
        (llama-quantize writes ERNIE's [1, E] selection bias as [E])."""
        want, experts = {}, {}
        for k, (name, expert) in self._src.items():
            want[name] = tuple(self.shapes[k])
            if expert is not None:
                experts[name] = max(experts.get(name, 0), expert + 1)
        for name, shape in want.items():
            got = tuple(int(n) for n in reversed(self._tensors[name].shape.tolist()))   # numpy order
            n = experts.get(name)
            expected = shape if n is None else (n, *shape)
            if _squeezed(got) != _squeezed(expected) or (n is not None and got[0] != n):
                raise ValueError(f'{gguf_path}: {name} has shape {list(got)}, the HF parameters want {list(expected)}')

    def _read(self, key: str) -> torch.Tensor:
        name, expert = self._src[key]
        t = self._tensors[name]
        arr = gguf.quants.dequantize(t.data if expert is None else t.data[expert], t.tensor_type)
        if not arr.flags.writeable:   # F32 data is a view of the read-only memory map
            arr = arr.copy()
        return torch.from_numpy(arr).reshape(self.shapes[key])
