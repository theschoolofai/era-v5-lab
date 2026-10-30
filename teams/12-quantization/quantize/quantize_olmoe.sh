#!/usr/bin/env bash
#
# Build llama.cpp, download OLMoE, create a BF16 GGUF baseline, then make
# selective 8/6/5/4/3-bit GGUFs. Router gates and output.weight stay BF16.
#
# Usage:
#   ./quantize_olmoe.sh
#   MODEL_ID=allenai/OLMoE-1B-7B-0924 OUTPUT_DIR="$PWD/artifacts" ./quantize_olmoe.sh
#
# This script did NOT produce the team's results. Every measured GGUF has output.weight Q8_0 and goes from Q8_0
# down to Q2_K: runs/runs.csv and quality/ use scripts/quantize_eval.py, eval_mini/ its notebook, perplexity/
# llama-quantize --output-tensor-type q8_0. This script keeps output.weight BF16 and stops at Q3_K_M.
#
set -Eeuo pipefail

MODEL_ID="${MODEL_ID:-allenai/OLMoE-1B-7B-0924}"
OUTPUT_DIR="${OUTPUT_DIR:-$PWD/artifacts}"
WORK_DIR="${WORK_DIR:-$PWD/.quantize-work}"
LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$WORK_DIR/llama.cpp}"
HF_DIR="$WORK_DIR/hf/$(basename "$MODEL_ID")"
VENV_DIR="$WORK_DIR/.venv"
LLAMA_CPP_TAG="${LLAMA_CPP_TAG:-b11669}"   # = v0.7.0, the build eval_mini and perplexity/ used
BASE_NAME="$(basename "$MODEL_ID")"
BF16_GGUF="$OUTPUT_DIR/${BASE_NAME}-BF16.gguf"

# GGUF tensor names for the output projection and OLMoE/Mixtral-style routers.
# llama-quantize never quantizes ffn_gate_inp.weight, so routers keep the
# converter's F32; output.weight is pinned with --output-tensor-type.
PRESERVED_TENSOR_PATTERNS=(
  '^output\.weight$'
  '^blk\.[0-9]+\.ffn_gate_inp\.weight$'
)
QUANT_TYPES=(Q8_0 Q6_K Q5_K_M Q4_K_M Q3_K_M)

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

find_quantizer() {
  local candidate
  for candidate in \
    "$LLAMA_CPP_DIR/build/bin/llama-quantize" \
    "$LLAMA_CPP_DIR/build/bin/Release/llama-quantize" \
    "$LLAMA_CPP_DIR/llama-quantize"; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

verify_preserved_tensors() {
  local gguf_file="$1"
  PYTHONPATH="$LLAMA_CPP_DIR/gguf-py${PYTHONPATH:+:$PYTHONPATH}" \
    "$PYTHON" - "$gguf_file" "${PRESERVED_TENSOR_PATTERNS[@]}" <<'PY'
import re
import sys
from collections import Counter

from gguf import GGMLQuantizationType, GGUFReader

# 8-bit or wider. The converter stores router gates as F32.
ALLOWED_TYPES = {"F32", "F16", "BF16", "Q8_0"}

path, *patterns = sys.argv[1:]
reader = GGUFReader(path, "r")
matches = {pattern: [] for pattern in patterns}

for tensor in reader.tensors:
    for pattern in patterns:
        if re.fullmatch(pattern, tensor.name):
            type_name = GGMLQuantizationType(int(tensor.tensor_type)).name
            matches[pattern].append((tensor.name, type_name))

missing = [pattern for pattern, tensors in matches.items() if not tensors]
wrong_type = [
    f"{name} ({type_name})"
    for tensors in matches.values()
    for name, type_name in tensors
    if type_name not in ALLOWED_TYPES
]

if missing or wrong_type:
    if missing:
        print("Missing protected tensor pattern(s): " + ", ".join(missing), file=sys.stderr)
    if wrong_type:
        print("Protected tensors below 8-bit: " + ", ".join(wrong_type), file=sys.stderr)
    sys.exit(1)

for pattern, tensors in matches.items():
    counts = Counter(type_name for _, type_name in tensors)
    summary = ", ".join(f"{n} x {t}" for t, n in sorted(counts.items()))
    print(f"  protected {pattern}: {summary}")
PY
}

require_command git
require_command cmake
require_command python3

mkdir -p "$OUTPUT_DIR" "$WORK_DIR/hf"

if [[ ! -d "$LLAMA_CPP_DIR/.git" ]]; then
  printf 'Cloning llama.cpp into %s\n' "$LLAMA_CPP_DIR"
  git clone --depth 1 --branch "$LLAMA_CPP_TAG" https://github.com/ggml-org/llama.cpp.git "$LLAMA_CPP_DIR"
else
  printf 'Checking out llama.cpp %s in %s\n' "$LLAMA_CPP_TAG" "$LLAMA_CPP_DIR"
  git -C "$LLAMA_CPP_DIR" fetch --depth 1 origin tag "$LLAMA_CPP_TAG"
  git -C "$LLAMA_CPP_DIR" checkout -q "$LLAMA_CPP_TAG"
fi

python3 -m venv "$VENV_DIR"
PYTHON="$VENV_DIR/bin/python"
"$PYTHON" -m pip install pip==26.2.2
"$PYTHON" -m pip install -r "$LLAMA_CPP_DIR/requirements/requirements-convert_hf_to_gguf.txt" huggingface_hub==0.36.2

cmake -S "$LLAMA_CPP_DIR" -B "$LLAMA_CPP_DIR/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$LLAMA_CPP_DIR/build" --config Release --parallel
QUANTIZER="$(find_quantizer)" || die "llama-quantize was not built"

# llama-quantize prints usage and exits 1 for --help, so don't pipe it under pipefail.
QUANTIZER_HELP="$("$QUANTIZER" --help 2>&1 || true)"
if ! grep -q -- '--output-tensor-type' <<<"$QUANTIZER_HELP"; then
  die "This llama-quantize build lacks --output-tensor-type; update llama.cpp."
fi

if [[ ! -f "$HF_DIR/config.json" ]]; then
  printf 'Downloading %s\n' "$MODEL_ID"
  MODEL_ID="$MODEL_ID" HF_DIR="$HF_DIR" "$PYTHON" - <<'PY'
import os
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id=os.environ["MODEL_ID"],
    local_dir=os.environ["HF_DIR"],
    token=os.environ.get("HF_TOKEN"),
)
PY
fi

if [[ ! -f "$BF16_GGUF" ]]; then
  printf 'Converting checkpoint to BF16 GGUF: %s\n' "$BF16_GGUF"
  "$PYTHON" "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" \
    "$HF_DIR" --outfile "$BF16_GGUF" --outtype bf16
fi
verify_preserved_tensors "$BF16_GGUF"

for quant_type in "${QUANT_TYPES[@]}"; do
  output_gguf="$OUTPUT_DIR/${BASE_NAME}-${quant_type}.gguf"
  if [[ -f "$output_gguf" ]]; then
    printf 'Keeping existing %s\n' "$output_gguf"
  else
    printf 'Quantizing %s -> %s\n' "$quant_type" "$output_gguf"
    "$QUANTIZER" \
      --output-tensor-type bf16 \
      "$BF16_GGUF" "$output_gguf" "$quant_type"
  fi
  verify_preserved_tensors "$output_gguf"
done

printf '\nFinished. Files written to %s\n' "$OUTPUT_DIR"
