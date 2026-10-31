# Chat format v0

Team G10. ChatML-style template for Team 3 (G3 Tokenizer) and Team 12 (G12 Quantization and Serving) by Saturday 31 Oct.

## Core rule: special tokens for structure, plain text for values

Instructor ruling, 27 Oct (reply to the special-tokens discussion in the G10 chat):

- **Special tokens** only for structure that the model must never confuse with normal text: the start and end of each role turn, tool call start and end, tool result start and end, and thinking start and end.
- **Plain text** for values inside that structure: tool names, arguments, effort level, options and settings. A tool call is special tokens around plain-text JSON.
- Keep the special-token list short. Sai Teja owns the final list, and TSAI reviews it at the Gate.

Markers in `v0` (each is one atomic special token in the tokenizer, never split into pieces):

- Turn & document markers: `<|endoftext|>` (`000`), `<|im_start|>` (`001`), `<|im_end|>` (`002`)
- Reasoning & tool markers: `<|think|>` (`024`), `<|/think|>` (`025`), `<|tool_call|>` (`026`), `<|/tool_call|>` (`027`), `<|tool_result|>` (`028`), `<|/tool_result|>` (`029`)

Effort is **not** a token. It is a plain-text line, `Reasoning effort: {level}`, at the top of the first system turn. Levels are `1k`, `4k`, `16k` and `64k` (budgets of `1024`, `4096`, `16384` and `65536` tokens covering think + tool trace, excluding the final visible reply).

- Plain-text XML look-alikes (`<think>`, `</think>`, `<tool_call>`, `</tool_call>`, `<tool_result>`, `</tool_result>`) are rejected by `render.py`.
- All 9 assigned markers and 247 reserved slots (`0..255`) are listed in `teams/10-post-training/special-tokens/special_tokens_v0.md` for Team 3 (G3) to reserve by Saturday 31 Oct.

## Turn structure

Roles are `system`, `user`, `assistant`, and `tool`.

1. **First turn is always `system`:**
   `<|im_start|>system\nReasoning effort: {level}\n\n{system content}<|im_end|>\n`
   If the transcript has no system message, the turn holds only the effort line. Other `system` and `user` turns are `<|im_start|>{role}\n{content}<|im_end|>\n`.
2. **`assistant` turn:**
   `<|im_start|>assistant\n`, then, in order and omitting empty optional sections:
   - Optional reasoning span wrapped in atomic special tokens: `<|think|>\n{think}\n<|/think|>\n`
   - Zero or more tool calls, each wrapped in atomic special tokens around plain-text JSON: `<|tool_call|>\n{"arguments":{...},"name":"..."}\n<|/tool_call|>\n`
   - Optional visible reply text: `{content}`
   Closed by `<|im_end|>\n`.
3. **`tool` turn:**
   `<|im_start|>tool\n<|tool_result|>\n{content}\n<|/tool_result|><|im_end|>\n` (tool output `content` is required).
4. **End of transcript:**
   `<|endoftext|>`

`render.py` renders messages to a string, `parse()` reconstructs the messages and effort level, and `tokenize_markers()` splits a rendered transcript into atomic special-token IDs (`0..255`) and text spans to verify that no marker is ever left as plain text.

One edge case: a first system message with empty content renders as the effort line only, so `parse()` returns no system message for it.

## Example

Effort `4k`.

```text
<|im_start|>system
Reasoning effort: 4k

You edit code and you report only what a tool returned.<|im_end|>
<|im_start|>user
test_add fails in calc.py. Fix add.<|im_end|>
<|im_start|>assistant
<|think|>
The return adds one too many.
<|/think|>
<|tool_call|>
{"arguments":{"path":"calc.py"},"name":"read_file"}
<|/tool_call|>
I am reading calc.py before editing it.<|im_end|>
<|im_start|>tool
<|tool_result|>
def add(a, b):
    return a + b + 1

<|/tool_result|><|im_end|>
<|im_start|>assistant
<|tool_call|>
{"arguments":{"patch":"return a + b","path":"calc.py"},"name":"apply_patch"}
<|/tool_call|>
Removed the extra increment.<|im_end|>
<|endoftext|>
```
