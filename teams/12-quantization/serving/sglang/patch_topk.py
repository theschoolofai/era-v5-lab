"""The spike's 4-line patch: make SGLang 0.5.23's fused_topk honour an ERNIE-style selection bias on the softmax path.

    python patch_topk.py      # edits the installed sglang in place (modal_sgl.py runs it inside the image)

A diagnostic only, not a fix to use. In 0.5.23, fused_topk()'s softmax branch on CUDA calls
_jit_moe_fused_gate(gating_output, None, ...), so a correction_bias (Ernie4_5_Moe's e_score_correction_bias) is
dropped. This patch routes softmax + correction_bias to SGLang's own fused_topk_torch_native, which ranks experts by
softmax probability + bias and gates with the unbiased probabilities, as ERNIE does. It is right for our random model
(bias ~ N(0, 0.01)), but 0.5.23 stores the bias in bf16 and this route adds it in the model dtype. Baidu's
ERNIE-4.5 biases (a common offset of about 22 to 63, a per-layer spread of 0.003 to 0.028) collapse in bf16, and in
one layer of ERNIE-4.5-21B the patch then routes worse than no patch (47% of tokens against 21.5% differ from
transformers, on synthetic router logits). The upstream fix is the SGLang PR linked in README.md.
"""
import pathlib, sglang
p = pathlib.Path(sglang.__file__).parent / 'srt/layers/moe/topk.py'
src = p.read_text()
start = src.index('def fused_topk(')
anchor = src.index('    if scoring_func == "softmax":\n', start)
patch = ('    if scoring_func == "softmax" and correction_bias is not None:  # SPIKE PATCH\n'
         '        w, i = fused_topk_torch_native(hidden_states, gating_output, topk, renormalize,\n'
         '                                       correction_bias.reshape(-1), "softmax")\n'
         '        return w.float(), i.to(torch.int32)\n')
p.write_text(src[:anchor] + patch + src[anchor:])
print('patched', p)
