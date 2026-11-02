# OLMoE perplexity at 6 bit widths (Kaggle T4)

A second measurement next to the stand-in eval in `runs/runs.csv`: WikiText-2 perplexity for the bf16 baseline and
6 llama.cpp formats. Perplexity is not the eval-mini score, but it is sensitive enough to separate every step of the
ladder, which 200 stand-in items cannot (their noise is about ±3 points).

Run on 25 Oct 2026 by therahulbhati. Results: [`runs_ppl.csv`](runs_ppl.csv). Lower perplexity is better.

## Setup

- Model: `allenai/OLMoE-1B-7B-0924`
- Runtime: llama.cpp `v0.7.0`, built from source with CUDA
- Machine: Kaggle notebook, 2x Tesla T4 (compute capability 7.5), 4 CPUs
- Eval: `llama-perplexity` on the full WikiText-2 test set (`scripts/get-wikitext-2.sh` in llama.cpp), n_ctx 512, `-ngl 99`
- Quantization: `llama-quantize --output-tensor-type q8_0`; the router (`ffn_gate_inp`) is left F32 by llama-quantize

## How perplexity is calculated

What `llama-perplexity` does (`tools/perplexity/perplexity.cpp` in llama.cpp v0.7.0):

1. The test text is tokenized and cut into chunks of 512 tokens (`n_ctx`). Each chunk is run on its own, starting from
   an empty context, 4 chunks per batch (`n_seq=4`).
2. Only the second half of each chunk is scored (`const int first = n_ctx/2;`), so every scored token has at least 256
   tokens of context before it.
3. For each scored token, NLL = -ln p(correct next token). PPL = exp(mean NLL over all scored tokens).
   For example, Q4_K_M has mean NLL ln(8.1785) = 2.1015 against 2.0785 for bf16: 0.023 nats more per token.
4. The ± is the standard error: the standard deviation of the per-token NLL divided by √(number of tokens), times PPL.

Every format is scored on the same text with the same chunks, so the values compare directly. A different `n_ctx`
gives different values, which is why `run_perplexity.py` adds `_ctxN` to the metric name when it is not 512.

## Results

| Format | Bits/weight | Size | PPL | vs bf16 | Eval time |
|---|---|---|---|---|---|
| bf16 | 16.00 | 13.84 GB | 7.993 ± 0.052 | | 468 s |
| Q8_0 | 8.51 | 7.36 GB | 7.994 ± 0.052 | +0.02% | 141 s |
| Q6_K | 6.60 | 5.71 GB | 8.012 ± 0.053 | +0.24% | 139 s |
| Q5_K_M | 5.72 | 4.95 GB | 8.039 ± 0.053 | +0.58% | 132 s |
| Q4_K_M | 4.90 | 4.24 GB | 8.179 ± 0.054 | +2.32% | 125 s |
| Q3_K_M | 3.89 | 3.37 GB | 8.516 ± 0.056 | +6.55% | 130 s |
| Q2_K | 2.99 | 2.59 GB | 10.500 ± 0.071 | +31.4% | 130 s |

- 8 to 5 bits is close to lossless (under 0.6%).
- Q4_K_M is 3.3x smaller for +2.3%.
- The knee is between 4 and 3 bits; 2 bits loses 31%.
- Bits per weight and sizes match the M3 Max run in `runs/runs.csv` exactly, so both runs quantized the same way.
- bf16 is 3-4x slower than the quantized files because the T4 has no native bf16 support. The quantized files all
  take about the same time: perplexity runs large batches, so these times say nothing about generation speed.
- The ± is the uncertainty of each value on its own. All runs use the same text, so the differences between formats
  are more certain than the ± suggests.

Quantize time per format on 4 CPUs: Q8_0 78 s, Q6_K 192 s, Q5_K_M 301 s, Q4_K_M 340 s, Q3_K_M 160 s, Q2_K 208 s.

## Screenshots

1. [`01-quantize-times.png`](screenshots/01-quantize-times.png): `llama-quantize` times
2. [`02-file-sizes.png`](screenshots/02-file-sizes.png): file sizes
3. [`03-router-output-check.png`](screenshots/03-router-output-check.png): `gguf_dump.py` shows `ffn_gate_inp` F32 and `output.weight` Q8_0 in the Q2_K file
4. [`04-smoke-test.png`](screenshots/04-smoke-test.png): bf16, Q8_0, Q4_K_M and Q2_K each complete a prompt
5. [`05-perplexity.png`](screenshots/05-perplexity.png): perplexity for all 7 files

## Files

- [`run_perplexity.py`](run_perplexity.py): runs perplexity on every GGUF in a folder and appends to `runs_ppl.csv`.
  Works on the GGUFs from `scripts/quantize_eval.py` or `quantize/quantize_olmoe.sh`:
  ```bash
  pip install gguf==0.19.0
  python teams/12-quantization/perplexity/run_perplexity.py --models-dir <folder with *.gguf> --llama-bin <llama.cpp bin folder>
  ```
  `--chunks N` gives a quick run on part of the text. Tested on a Mac M1 with two small GGUFs
  (`ggml-org/models` `tinyllamas/stories15M` q8_0 and q4_0).
- [`kaggle_run.ipynb`](kaggle_run.ipynb): the Kaggle notebook of this run, with all outputs. The cell that set
  `$MODELS` is missing from it, so the quantize cell wrote the GGUFs to `/`; cell 12 moves them to `/kaggle/tmp/models`.
- [`runs_ppl.csv`](runs_ppl.csv): the results above.

## Reproduce on Kaggle

Notebook settings: GPU T4 x2, Internet on. Keep models outside `/kaggle/working` (20 GB limit).

```bash
git clone --depth 1 --branch v0.7.0 https://github.com/ggml-org/llama.cpp
# GGML_CUDA_NO_VMM: Kaggle's build image has no libcuda for CMake to link (CUDA::cuda_driver not found)
cmake -S llama.cpp -B llama.cpp/build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=75 -DGGML_CUDA_NO_VMM=ON -DLLAMA_BUILD_TESTS=OFF
cmake --build llama.cpp/build --config Release -j4 --target llama-quantize llama-completion llama-perplexity
pip install -r llama.cpp/requirements/requirements-convert_hf_to_gguf.txt   # do not upgrade huggingface_hub after this

M=/kaggle/tmp/models; mkdir -p $M
hf download allenai/OLMoE-1B-7B-0924 --local-dir $M/olmoe-hf
python llama.cpp/convert_hf_to_gguf.py $M/olmoe-hf --outtype bf16 --outfile $M/olmoe-bf16.gguf
for q in Q8_0 Q6_K Q5_K_M Q4_K_M Q3_K_M Q2_K; do
  llama.cpp/build/bin/llama-quantize --output-tensor-type q8_0 $M/olmoe-bf16.gguf $M/olmoe-$q.gguf $q
done

(cd llama.cpp && sh scripts/get-wikitext-2.sh)
for q in bf16 Q8_0 Q6_K Q5_K_M Q4_K_M Q3_K_M Q2_K; do   # or: python run_perplexity.py --models-dir $M --llama-bin llama.cpp/build/bin
  llama.cpp/build/bin/llama-perplexity -m $M/olmoe-$q.gguf -f llama.cpp/wikitext-2-raw/wiki.test.raw -ngl 99 2>&1 | grep "Final estimate"
done
```

Kaggle notes: in a notebook, each `!` line is a new shell, so set `M` in every cell (or use full paths). `%%bash`
cells only show output when the whole cell ends; use `!` lines for long steps to see progress.
