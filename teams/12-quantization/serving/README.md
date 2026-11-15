# Serving: vLLM OpenAI endpoint with the G10 chat format

Week 3, task 4 (Member C). One checkpoint served by **vLLM 0.33.0** (the version in
[`gpu_path/results/environment.json`](../gpu_path/results/environment.json)) on the OpenAI-compatible endpoint, with
G10's chat template, a reasoning parser and a tool parser. 100 fixed prompts are sent and checked. The result goes
to [`results/serve_check.md`](../results/serve_check.md).

Gate 3 asks that the endpoint return reasoning and tool calls in the right fields: `message.reasoning` and
`message.tool_calls`, and not inside `message.content`.

| File | What |
|---|---|
| [`g10_parsers.py`](g10_parsers.py) | vLLM plugin with two parsers, both named `g10`. The reasoning parser maps `<\|think\|> … <\|/think\|>` to `reasoning`. The tool parser maps `<\|tool_call\|>{json}<\|/tool_call\|>` to `tool_calls`. Streaming and non-streaming. |
| [`serve_check.py`](serve_check.py) | starts `vllm serve` with the template and both parsers, sends the 100 prompts (plus 20 streamed), checks every field, and writes `serve_check.md`, `summary.json`, `serve_check.jsonl` and the server log to `--out` |
| [`prompts_v1.jsonl`](prompts_v1.jsonl), [`tools_v1.json`](tools_v1.json) | the 100 prompts and 6 tool schemas, written by [`make_prompts.py`](make_prompts.py) |
| [`test_g10_parsers.py`](test_g10_parsers.py) | template round trip, streaming in 1-char and random chunks, reasoning end on multi-turn prompts, and the parsers inside vLLM's own `DelegatingParser` (needs vllm) |
| [`test_serve_check.py`](test_serve_check.py) | the field and behaviour checks, the answer check on Indic digits, request building |

## Why our own parsers

No built-in vLLM parser reads the G10 markers. `deepseek_r1` and `qwen3` look for `<think>`. `hermes` looks for
`<tool_call>`, and its streaming expects `"name"` before `"arguments"`, while G10 writes `"arguments"` first.
Details that matter in vLLM 0.33:

- **Special tokens.** With the frozen tokenizer each marker is one special token, and vLLM drops special tokens
  from the text by default. Requests send `"skip_special_tokens": false` (serve_check.py does). The tool parser also
  sets it on any request that carries tools.
- **Earlier turns.** vLLM asks the reasoning parser whether reasoning has already ended *in the prompt*. A
  multi-turn prompt contains earlier `<|/think|>`. The parser reads only the open turn after the last
  `<|im_start|>`, or the new reasoning would come back as content (tested).
- **Answers with no reasoning.** An answer with no `<|think|>` ends the reasoning phase at its first token. That
  way a direct tool call is still parsed when streaming.
- **Stand-in tokenizers.** Markers are matched as text, so the parsers also work with a stand-in model whose
  tokenizer splits them into several tokens. Both tokenizer cases are tested.

## Run

**Tests (CPU, any machine):**
```bash
python -m pytest teams/12-quantization/serving -q          # vLLM adapter tests skip without vllm
```
With `vllm==0.33.0` installed, all 60 pass. On a Mac, `pip install --no-deps vllm==0.33.0` plus the modules
the parser imports is enough.

**Kaggle (GPU T4 x2, Internet on).** Stand-in model `Qwen/Qwen3-4B-Instruct-2507` (Apache-2.0). Each cell:
```bash
!git clone --depth 1 -b g12-week3-soma https://github.com/SomaKorada07/era-v5-lab.git
%cd era-v5-lab
!pip install -q "vllm==0.33.0"
!python -m pytest teams/12-quantization/serving -q
!python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-4B-Instruct-2507', local_dir='/kaggle/working/models/Qwen3-4B-Instruct-2507')"
# smoke: 10 prompts, 5 streamed
!python teams/12-quantization/serving/serve_check.py --model /kaggle/working/models/Qwen3-4B-Instruct-2507 \
    --label "Qwen3-4B-Instruct-2507 (stand-in)" --limit 10 --stream-check 5 --out /kaggle/working/smoke \
    --vllm-arg=--dtype=half --vllm-arg=--max-model-len=4096 --vllm-arg=--tensor-parallel-size=2 --n-gpus 2
# full: 100 prompts, 20 streamed
!python teams/12-quantization/serving/serve_check.py --model /kaggle/working/models/Qwen3-4B-Instruct-2507 \
    --label "Qwen3-4B-Instruct-2507 (stand-in)" --out /kaggle/working/out \
    --vllm-arg=--dtype=half --vllm-arg=--max-model-len=4096 --vllm-arg=--tensor-parallel-size=2 --n-gpus 2
```
A T4 has no bf16, so `--dtype half`. Copy `out/serve_check.md` to `results/serve_check.md`, and `summary.json` and
`serve_check.jsonl` to `results/serve_check/`. Keep `vllm_server.log` out of the repo; if needed, put it in a gist.

**Our checkpoint (job request).** Once `export_hf.py` (Member D) turns a dry-run-1 checkpoint into a Hugging Face
`GraniteMoeSharedForCausalLM` folder (`unsupported_parts.md` §8), run the same script on it with
`--format-hint off`. The script follows the JOB_REQUEST.md rules: localhost only, `HF_HUB_OFFLINE=1`, writes only
to `--out`.

## What the check measures

- **Fields (pass or fail, exit code 1 on failure).** No chat marker (`<|think|>`, `<|tool_call|>`, `<|im_end|>`, …)
  is left in `content`, `reasoning` or tool arguments, streamed or not, and every request returns HTTP 200. That is
  the serving check: a parser fault shows up here.
- **Behaviour (reported).** Reason prompts have reasoning, tool prompts call the expected tool with JSON arguments
  that have the schema's required keys, and no_tool / tool_result prompts call none. This measures the model. For
  a stand-in that never saw our format it is a lower bound. Answers in the stand-in's own format (`<think>`,
  `<tool_call>`) are counted separately.
- **Time and cost.** Server start, wall time for the 100 prompts, tokens/s, GPU-hours, and cost at
  `--usd-per-gpu-hour` (0 on Kaggle).

## Findings for G10 and the export

1. **The template drops the request's `tools`.** `chat_template.jinja` never renders `tools`, so a model served
   with it never sees the tool schemas. `chat_format_v0.md` mentions "injected tool schemas" (Tier 1) but fixes no
   format. Until G10 decides, serve_check writes the schemas into the system message (`--tools-in-system auto`).
2. **History tool calls in OpenAI form render in the wrong shape.** A client sends
   `{"id", "type", "function": {"name", "arguments"}}`, and the template's `call | tojson` writes it unchanged.
   Training data has `{"arguments", "name"}`. Proposed fix: render `call.function` when it is present. The parser
   reads both shapes.
3. **Reasoning from earlier turns** is rendered only from a `think` key. OpenAI clients send `reasoning`, so earlier
   reasoning is dropped. That is usually what we want; noted only.
4. **Export (`export_hf.py`).** `generation_config.json` must list `<|im_end|>` (130816) and `<|endoftext|>` (130822)
   as `eos_token_id`, or vLLM generates past the end of the turn.

## Status

- Parsers and checks: 60 tests pass on CPU with vLLM 0.33.0 (vLLM's parser composition, without a GPU).
- GPU run on the stand-in: to do (Kaggle). `results/serve_check.md` is written by that run, not by hand.
- Our checkpoint: waits for the dry-run-1 checkpoint (G7, D4) and `export_hf.py`.
