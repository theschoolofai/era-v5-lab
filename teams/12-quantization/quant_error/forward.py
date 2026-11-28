"""Twin forward: a reference and a quantized copy of one model pass through the same transformers layer stack in fp32,
one stage resident at a time, and the error is measured where it arises.

    select_experts(arch, gate_logits, k, bias) -> LongTensor [tokens, k]
    twin_forward(hf_config_dir, ref, quant, batches, device='cpu', x_rows=256) -> TwinResult

The model is built on `meta` from the folder's config. Each stage (embedding, decoder layer 0..L-1, head) is
materialized on `device`, loaded strictly with the reference weights, run on the reference track's hidden states of
every batch, loaded with the quantized weights, run on the quantized track's own hidden states, and returned to `meta`:
one decoder layer is resident at a time, plus the other track's weights of that layer while they are read. A layer is
called as the transformers model calls it: rotary (cos, sin) from the model's rotary embedding (rebuilt on `device`,
since its inv_freq buffer is not in the state dict), the mask from `create_causal_mask` with no padding and no cache
(None under sdpa, which then attends causally), position ids 0..T-1 per sequence.

Measured, per held-out slice unless noted:
  layers   hidden_rel_err  ‖h_q - h_r‖ / ‖h_r‖ of the layer's output over the slice's tokens
           router_agree    share of tokens whose top-k expert set is the same in both tracks (None: dense MLP layer)
  linears  act_rel_err     ‖X(W - Ŵ)ᵀ‖ / ‖XWᵀ‖ per nn.Linear (every layer's, and lm_head with layer None); X is a
                           uniform sample of up to x_rows of its reference-track inputs over all slices (an expert's:
                           the tokens routed to it); `rows` = len(X); None when no input reached it
  tokens   kl_mean, kl_p99 KL(ref ‖ quant) of the next-token softmax, in nats, per scored position
           same_top1       share of positions whose argmax agrees
Router logits come from a forward hook on the MoE block's `gate` (nn.Linear in both architectures); an MoE layer
(one whose MLP has `experts`) without that router, or whose router gave no logits, is an error naming the layer.
twin_forward first pins full fp32 matmuls (precision 'highest', TF32 off for CUDA matmuls and cuDNN) and leaves them
so; fp32_settings() reports them. The activation sample's generator is seeded with SEED.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import torch
from torch import nn

from weights import ARCHS, WeightSource

_EXPERT = re.compile(r'\.experts\.(\d+)\.')
SEED = 0   # of the generator that samples each nn.Linear's inputs


def pin_fp32() -> None:
    """Full fp32 matmuls on every device: TF32 (CUDA's default for cuDNN) or a lower precision would add an error of
    its own to both tracks."""
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def fp32_settings() -> dict:
    return {'float32_matmul_precision': torch.get_float32_matmul_precision(),
            'cuda_matmul_allow_tf32': torch.backends.cuda.matmul.allow_tf32,
            'cudnn_allow_tf32': torch.backends.cudnn.allow_tf32}


def select_experts(arch: str, gate_logits: torch.Tensor, k: int, bias: torch.Tensor | None) -> torch.Tensor:
    """The k experts each row of router logits picks, as transformers 4.57.6 picks them, in fp32.

    olmoe: top-k of the logits (the softmax it ranks is monotonic). ernie4_5-moe: top-k of softmax(logits) + bias, the
    selection bias (e_score_correction_bias, [1, E]) flattened and used only for the choice. The bias must stay fp32:
    Baidu's biases sit at offsets of 22-63 with a per-expert range of at most 0.028, which bf16 rounds away."""
    logits = gate_logits.float()
    if arch == 'olmoe':
        if bias is not None:
            raise ValueError('olmoe has no router selection bias')
        scores = logits
    elif arch == 'ernie4_5-moe':
        scores = torch.softmax(logits, dim=-1)
        if bias is not None:
            scores = scores + bias.float().reshape(-1)
    else:
        raise NotImplementedError(f'{arch}: no expert selection rule')
    return scores.topk(k, dim=-1).indices


@dataclass
class TwinResult:
    layers: list[dict] = field(default_factory=list)    # slice, layer, hidden_rel_err, router_agree
    linears: list[dict] = field(default_factory=list)   # layer, tensor, expert, rows, act_rel_err
    tokens: list[dict] = field(default_factory=list)    # slice, n_tokens, kl_mean, kl_p99, same_top1


class _Sample:
    """A uniform sample, without replacement, of up to n of the rows passed to add(): the rows with the n smallest
    random keys."""

    def __init__(self, n: int, gen: torch.Generator):
        self.n, self.gen, self.rows, self.keys = n, gen, None, None

    def add(self, x: torch.Tensor) -> None:
        x = x.detach().reshape(-1, x.shape[-1])
        keys = torch.rand(x.shape[0], generator=self.gen)
        if self.rows is not None:
            x, keys = torch.cat([self.rows, x]), torch.cat([self.keys, keys])
        if x.shape[0] > self.n:
            keep = keys.topk(self.n, largest=False).indices
            x, keys = x[keep.to(x.device)], keys[keep]
        self.rows, self.keys = x, keys


def _materialize(parts: dict[str, nn.Module], device: str) -> None:
    for module in parts.values():
        module.to_empty(device=device)
        if lost := sorted({n for n, _ in module.named_buffers()} - set(module.state_dict())):
            raise RuntimeError(f'{type(module).__name__}: buffers {lost} are not in the state dict and would stay '
                               'uninitialized')


def _load(parts: dict[str, nn.Module], state: dict[str, torch.Tensor]) -> None:
    """Each module takes the tensors under its prefix (prefix stripped), strictly; every tensor must be taken."""
    left = dict(state)
    for prefix, module in parts.items():
        module.load_state_dict({k[len(prefix):]: left.pop(k) for k in list(left) if k.startswith(prefix)},
                               strict=True)
    if left:
        raise ValueError(f'tensors with no module in this stage: {sorted(left)[:5]}')


def _unload(parts: dict[str, nn.Module]) -> None:
    for module in parts.values():
        module.to_empty(device='meta')


def _act_rel_err(x: torch.Tensor | None, w: torch.Tensor, w_hat: torch.Tensor) -> tuple[int, float | None]:
    if x is None or not len(x):
        return 0, None
    den = torch.linalg.vector_norm(x @ w.T).item()
    return len(x), (torch.linalg.vector_norm(x @ (w - w_hat).T).item() / den if den else None)


def twin_forward(hf_config_dir: Path, ref: WeightSource, quant: WeightSource, batches: dict[str, list[torch.Tensor]],
                 device: str = 'cpu', x_rows: int = 256, *,
                 on_logits: Callable[[str, int, torch.Tensor, torch.Tensor], None] | None = None) -> TwinResult:
    """Both tracks over every batch (token ids [B, T] or [T], one dict entry per slice); see the module docstring.

    on_logits(slice, batch index, reference logits, quantized logits) is called per batch, if given; logits are not
    kept."""
    from transformers import AutoConfig, AutoModelForCausalLM
    from transformers.masking_utils import create_causal_mask

    pin_fp32()   # not restored: the caller records fp32_settings()
    config = AutoConfig.from_pretrained(hf_config_dir)
    arch = {v: k for k, v in ARCHS.items()}.get(config.model_type)
    if arch is None:
        raise NotImplementedError(f'{config.model_type}: no expert selection rule')
    if not ref.n_layers == quant.n_layers == config.num_hidden_layers:
        raise ValueError(f'layers: ref {ref.n_layers}, quant {quant.n_layers}, config {config.num_hidden_layers}')
    if not batches or not all(batches.values()):
        raise ValueError(f'every slice needs at least one batch: {[s for s, b in batches.items() if not b]}')
    with torch.device('meta'):
        model = AutoModelForCausalLM.from_config(config, dtype=torch.float32)
    model.eval()
    ids = {(s, j): torch.atleast_2d(b).to(device) for s, bs in batches.items() for j, b in enumerate(bs)}
    gen = torch.Generator().manual_seed(SEED)
    out = TwinResult()

    with torch.no_grad():
        # embedding: both tracks' hidden states of every batch stay on `device` from here on
        embed = {'model.embed_tokens.': model.model.embed_tokens}
        _materialize(embed, device)
        h = {}
        for track, src in (('ref', ref), ('quant', quant)):
            _load(embed, src.embed())
            h[track] = {key: embed['model.embed_tokens.'](x) for key, x in ids.items()}
        _unload(embed)

        rotary = type(model.model.rotary_emb)(config=model.config, device=device)
        call = {}   # per batch: what the transformers model passes each decoder layer, cache off
        for key, x in h['ref'].items():
            pos = torch.arange(x.shape[1], device=device)
            call[key] = dict(position_embeddings=rotary(x, pos[None]), position_ids=pos[None], cache_position=pos,
                             attention_mask=create_causal_mask(config=model.config, input_embeds=x, attention_mask=None,
                                                               cache_position=pos, past_key_values=None,
                                                               position_ids=pos[None]))

        for i, layer in enumerate(model.model.layers):
            out.layers += _layer(arch, i, layer, ref, quant, h, call, x_rows, gen, out.linears, device)

        out.tokens += _head(model, ref, quant, h, x_rows, gen, out.linears, device, on_logits)
    return out


def _layer(arch, i, layer, ref, quant, h, call, x_rows, gen, linears, device) -> list[dict]:
    parts = {f'model.layers.{i}.': layer}
    router = getattr(layer.mlp, 'gate', None)   # an MoE block's router; a dense MLP has none
    if hasattr(layer.mlp, 'experts') and not isinstance(router, nn.Module):
        raise NotImplementedError(f'layer {i}: an MoE block whose router is not mlp.gate; forward.py reads router '
                                  'logits from mlp.gate only')
    linear = {f'model.layers.{i}.{name}.weight': m for name, m in layer.named_modules() if isinstance(m, nn.Linear)}
    gate_logits = []
    hooks = [router.register_forward_hook(lambda m, a, o: gate_logits.append(o))] if router is not None else []

    def run(track: str, key) -> torch.Tensor | None:
        y = layer(h[track][key], **call[key])
        h[track][key] = y[0] if isinstance(y, tuple) else y
        if router is None:
            return None
        if len(gate_logits) != 1:
            raise RuntimeError(f'layer {i}: the MoE router (mlp.gate) gave {len(gate_logits)} sets of logits in one '
                               'layer call, expected 1; this block routes some other way')
        bias = getattr(getattr(layer.mlp, 'moe_statics', None), 'e_score_correction_bias', None)
        return select_experts(arch, gate_logits.pop(), layer.mlp.top_k, bias)

    _materialize(parts, device)
    _load(parts, ref.layer(i))
    samples = {t: _Sample(x_rows, gen) for t in linear}
    capture = [m.register_forward_pre_hook(lambda m, a, s=samples[t]: s.add(a[0])) for t, m in linear.items()]
    chosen = {key: run('ref', key) for key in h['ref']}
    for hook in capture:
        hook.remove()

    w_hat = quant.layer(i)
    for t, m in linear.items():   # the module still holds the reference weights
        rows, err = _act_rel_err(samples[t].rows, m.weight, w_hat[t].to(device))
        e = _EXPERT.search(t)
        linears.append(dict(layer=i, tensor=t, expert=int(e.group(1)) if e else None, rows=rows, act_rel_err=err))
    del samples
    _load(parts, w_hat)
    del w_hat

    acc = {}   # slice -> [Σ‖h_q - h_r‖², Σ‖h_r‖², tokens with the same expert set, tokens]
    for key in h['quant']:
        sel = run('quant', key)
        d, r = h['quant'][key] - h['ref'][key], h['ref'][key]
        a = acc.setdefault(key[0], [0.0, 0.0, 0, 0])
        a[0] += torch.linalg.vector_norm(d).item() ** 2
        a[1] += torch.linalg.vector_norm(r).item() ** 2
        if sel is not None:
            a[2] += int((sel.sort(-1).values == chosen[key].sort(-1).values).all(-1).sum())
            a[3] += len(sel)
    for hook in hooks:
        hook.remove()
    _unload(parts)
    return [dict(slice=s, layer=i, hidden_rel_err=(dd / rr) ** 0.5 if rr else None,
                 router_agree=same / n if router is not None else None) for s, (dd, rr, same, n) in acc.items()]


def _head(model, ref, quant, h, x_rows, gen, linears, device, on_logits) -> list[dict]:
    """Final norm and lm_head, reloaded per batch so that only one batch's logits per track exist at a time."""
    parts = {'model.norm.': model.model.norm, 'lm_head.': model.lm_head}
    w, w_hat = ref.head(), quant.head()
    _materialize(parts, device)
    sample, kl, top1 = _Sample(x_rows, gen), {}, {}
    for key in h['ref']:
        _load(parts, w)
        x = model.model.norm(h['ref'][key])
        sample.add(x)
        logits = model.lm_head(x)
        _load(parts, w_hat)
        logits_q = model.lm_head(model.model.norm(h['quant'][key]))
        if on_logits is not None:
            on_logits(key[0], key[1], logits, logits_q)
        lp, lq = torch.log_softmax(logits.float(), -1), torch.log_softmax(logits_q.float(), -1)
        kl.setdefault(key[0], []).append((lp.exp() * (lp - lq)).sum(-1).flatten().cpu())
        top1.setdefault(key[0], []).append((logits.argmax(-1) == logits_q.argmax(-1)).flatten().cpu())
        del logits, logits_q, lp, lq
    _unload(parts)
    rows, err = _act_rel_err(sample.rows, w['lm_head.weight'].to(device), w_hat['lm_head.weight'].to(device))
    linears.append(dict(layer=None, tensor='lm_head.weight', expert=None, rows=rows, act_rel_err=err))
    out = []
    for s in kl:
        k, t = torch.cat(kl[s]), torch.cat(top1[s])
        out.append(dict(slice=s, n_tokens=len(k), kl_mean=k.mean().item(), kl_p99=torch.quantile(k, 0.99).item(),
                        same_top1=int(t.sum()) / len(t)))
    return out
