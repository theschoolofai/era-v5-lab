# Quantization and serving tools (G12, week 1)

Checked on 25 Oct 2026. Licences come from each repository's LICENSE file (GitHub API). "MoE model file" means the
repository ships a model definition for that architecture at its default branch on that date.

"MoE support" means the project can load or transform mixture-of-experts (MoE) checkpoints; it does not mean every MoE
architecture is automatically supported. Always run a small generation and routing smoke test with the target model.

Test models: `allenai/OLMoE-1B-7B-0924` (`OlmoeForCausalLM`, 64 experts, top-8, Apache-2.0) and
`Qwen/Qwen3-30B-A3B` (`Qwen3MoeForCausalLM`, Apache-2.0).

## Quantization tools

| Tool | Licence | Methods / bit widths | OLMoE | Qwen3-MoE | Router and output layer | Hardware | Status |
|---|---|---|---|---|---|---|---|
| **llama.cpp** (`ggml-org/llama.cpp`) | MIT | GGUF: Q8_0, Q6_K, Q5_K, Q4_K, Q3_K, Q2_K, IQ4…IQ1 (imatrix), MXFP4_MOE, TQ1/TQ2 | yes: converter `OlmoeForCausalLM`, `LLM_ARCH_OLMOE` | yes: converter `Qwen3MoeForCausalLM` | `ffn_gate_inp` (router) is **never quantized** (`src/llama-quant.cpp`). Output set with `--output-tensor-type`, per tensor with `--tensor-type` | CPU, Metal, CUDA, Vulkan | active. **Our week-1 tool** |
| **llm-compressor** (`vllm-project/llm-compressor`) | Apache-2.0 | GPTQ, AWQ, SmoothQuant, W8A8 INT8/FP8, W4A16, NVFP4 → compressed-tensors | no OLMoE example found (1 code hit for "olmoe") | yes: example `examples/quantization_w4a4_fp4/qwen_30b_a3b.py` | `ignore=["lm_head", "re:.*mlp.gate$"]` keeps output + router in bf16 | CUDA GPU for calibration | active. Path for vLLM serving (week 2+) |
| **GPTQModel** (`ModelCloud/GPTQModel`) | Apache-2.0 (SPDX header, GitHub shows NOASSERTION) | GPTQ, QQQ, EoRA, 2–8 bit | yes: `definitions/olmoe.py` | yes: `definitions/qwen3_moe.py` | not checked | CUDA (also ROCm, XPU, CPU) | active. Successor of AutoGPTQ |
| **AutoRound** (`intel/auto-round`) | Apache-2.0 | sign-gradient rounding, 2–8 bit; exports GPTQ, AWQ and GGUF formats | 3 code hits for "olmoe", not checked further | not checked | not checked | CUDA, XPU, CPU | active |
| **Intel Neural Compressor** (`intel/neural-compressor`) | Apache-2.0 | PTQ, GPTQ, AWQ, SmoothQuant | architecture-dependent; test the OLMoE model path | not checked | not checked | CPU, XPU focused | active |
| **mlx-lm** (`ml-explore/mlx-lm`) | MIT | MLX affine 2/3/4/6/8 bit, group size 32/64, mixed recipes | yes: `models/olmoe.py` | yes: `models/qwen3_moe.py` | not checked | Apple silicon only | active. Mac alternative to GGUF |
| **bitsandbytes** | MIT | load-time NF4/FP4, LLM.int8() inside transformers; no saved low-bit file for fast serving | via transformers (any Linear) | via transformers | router `gate` is a Linear and **is quantized** unless listed in `llm_int8_skip_modules` | CUDA mainly | active. Quick experiments only |
| **HQQ** (`dropbox/hqq`, was `mobiusml/hqq`) | Apache-2.0 | calibration-free 1–8 bit | via generic Linear patching, not checked | not checked | not checked | CUDA | maintained |
| **torchao** (`pytorch/ao`) | BSD-3-Clause | int4/int8 weight-only, float8, MX formats | not checked | not checked | not checked | CUDA, CPU | active. MoE work is in `prototype/moe_training` (training side) |
| **optimum-quanto** | Apache-2.0 | int2/int4/int8, float8 weights | generic Linear | generic Linear | not checked | CUDA, MPS, CPU | low activity |
| **ExLlamaV3** (`turboderp-org/exllamav3`) | MIT | EXL3 (QTIP-based) 1–8 bpw | **no** OLMoE arch file (has `olmo3`, `olmohybrid`) | yes: `architecture/qwen3_moe.py` | not checked | CUDA only | active |
| **NVIDIA Model Optimizer** (`NVIDIA/Model-Optimizer`, was TensorRT-Model-Optimizer) | Apache-2.0 (NVIDIA runtime components have their own terms) | FP8, NVFP4, INT4-AWQ, INT8-SQ, pruning, for TensorRT-LLM, vLLM, SGLang | not checked | not checked | not checked | NVIDIA GPU | active |
| AutoAWQ (`casper-hansen/AutoAWQ`) | MIT | AWQ 4-bit | n/a | n/a | n/a | CUDA | **archived May 2025**: do not use (AWQ now in llm-compressor) |
| AutoGPTQ (`AutoGPTQ/AutoGPTQ`) | MIT | GPTQ | n/a | n/a | n/a | CUDA | **archived Apr 2025**: do not use (use GPTQModel) |

## Serving runtimes (needed in weeks 2–4)

| Runtime | Licence | Reads | OLMoE | Qwen3-MoE |
|---|---|---|---|---|
| llama.cpp `llama-server` | MIT | GGUF | yes | yes |
| Ollama (`ollama/ollama`) | MIT | GGUF (Modelfile) | runs llama.cpp GGUF; the converter is a week-4 task | yes |
| vLLM | Apache-2.0 | bf16, FP8, GPTQ, AWQ, compressed-tensors, GGUF (experimental) | yes: `models/olmoe.py` | yes: `models/qwen3_moe.py` |
| SGLang | Apache-2.0 | bf16, FP8, GPTQ, AWQ, compressed-tensors | not checked | not checked |

## Choice for week 1

- **llama.cpp GGUF** for the bit-width ladder. Reasons: MIT licence; OLMoE and Qwen3-MoE both convert; it runs on Mac (Metal), Colab and Kaggle; a single runtime serves bf16 and every quantized format, so score differences come from the quantization, not from the runtime; the router is never quantized, and the output layer is pinned to 8-bit or BF16 with one flag.
- **Week 2+:** add one GPU path, llm-compressor (GPTQ/AWQ, FP8) served by vLLM. It needs a CUDA GPU.
- Do not use AutoAWQ or AutoGPTQ (archived).

## Workflows in this folder

Both use llama.cpp on `allenai/OLMoE-1B-7B-0924`. Both keep the 16 OLMoE router tensors (`blk.<n>.ffn_gate_inp.weight`)
in **F32**, the precision the converter writes. They differ in the output layer and in whether they evaluate.

**No results table in this folder comes from workflow A.** Every measured GGUF has `output.weight` at Q8_0 and the
ladder `Q8_0 … Q2_K`: `runs/runs.csv` and `quality/` use workflow B, `eval_mini/` its notebook, and `perplexity/` the
same `llama-quantize --output-tensor-type q8_0` commands run by hand on Kaggle.

### A. `quantize/quantize_olmoe.sh`: build + quantize

Downloads the model, builds `llama.cpp` at the pinned tag `b11669` (= v0.7.0; override with `LLAMA_CPP_TAG`), converts
a BF16 GGUF baseline, and creates `Q8_0`, `Q6_K`, `Q5_K_M`, `Q4_K_M` and `Q3_K_M`. It does not make `Q2_K`. Every variant keeps `output.weight` in **BF16** (`llama-quantize --output-tensor-type bf16`).
The script checks each GGUF and exits with an error if a router or output tensor is missing or stored below 8-bit.

```bash
./quantize/quantize_olmoe.sh
MODEL_ID=allenai/OLMoE-1B-7B-0924 OUTPUT_DIR="$PWD/artifacts" ./quantize/quantize_olmoe.sh
```

Requirements: `git`, `cmake`, a C/C++ compiler, Python 3.10+, and disk space for the checkpoint, the BF16 GGUF and five
quantized GGUFs. Set `HF_TOKEN` for a gated model.

### B. `scripts/quantize_eval.py`: quantize + evaluate + record

One command from a clean clone: pinned download, BF16 GGUF with the converter at the same build as the installed
llama.cpp, the ladder `Q8_0 … Q2_K` (down to 3 bits), output layer forced to **Q8_0**, router/output types checked in
every GGUF, then each format is served with `llama-server`, scored, and written to `runs/runs.csv` with time and machine.

```bash
python teams/12-quantization/scripts/quantize_eval.py --delete-hf            # stand-in eval
python teams/12-quantization/scripts/quantize_eval.py --eval eval_mini_v0.json
```

Requirements: llama.cpp binaries on PATH (`brew install llama.cpp`) or `--llama-bin`, and `uv` or Python 3.12.

## Open checks

- AutoRound, HQQ, torchao, Intel Neural Compressor, Model Optimizer: confirm OLMoE support by running them, not by reading the code.
- llm-compressor on OLMoE: the router module name for OLMoE is `mlp.gate`. Confirm that the `ignore` regex matches it.
- Output layer: workflow A keeps BF16, workflow B uses Q8_0. Both meet the "8-bit or bf16" rule. All tables use Q8_0, so their rows are comparable; GGUFs from A are not comparable with them.
