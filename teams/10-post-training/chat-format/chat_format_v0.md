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

## Hindi application — `ind-hi-hplt`

The format and `render.py` apply to Hindi (Devanagari) unchanged, with no language-specific tokens. The examples are newly authored, not extracted from HPLT documents.

- Hindi text, the danda `।` and `॥`, nukta letters, ZWJ/ZWNJ and Hindi-English mixing (`Python में bug ठीक करें`) are plain content. They go in message content and tool JSON string values. `render.py` keeps Devanagari readable in tool JSON (no `\u` escapes).
- `render.py` itself does not normalize. The pre-tokenization step must not change Hindi either:
  - **Keep ZWJ (`U+200D`) and ZWNJ (`U+200C`).** They choose between a half form and a conjunct (`क्‍ष` vs `क्ष`). Removing them changes the written word.
  - **Do not apply NFKC to content.** It splits precomposed nukta letters (`ज़` `U+095B` becomes `ज` + `़`) and folds compatibility characters in mixed text (`10²` becomes `102`).
  - **Remove only `U+200B` and `U+FEFF`.** `render.py` alone does not reject a marker with a zero-width space inside (`<|th` + `U+200B` + `ink|>`), so this removal must run before rendering. After it, the hidden marker is rejected.
- The `ind-hi-hplt` pack has no precomposed nukta letters and no ZWJ/ZWNJ (0 of 500 documents), so it is not affected. Other Hindi sources will have them.
- `special_tokens_v1.md` (on the team branch `saitej123:g10-week1-post-training`, not yet in this repository) asks for NFKC and removal of `U+200B..U+200D` (Pre-tokenization line). For Indic text this conflicts with the same file's per-pack note that ZWJ/ZWNJ are kept. The Hindi SWE task below tests the narrower rule.

Example input to the shared Python module (effort `16k`, with a think span):

```python
messages = [
    {"role": "system", "content": "हिंदी में उत्तर दें।"},
    {"role": "user", "content": "फ़ाइल में \"क्\u200dष\" सहेजें।"},
    {"role": "assistant", "think": "ZWJ को नहीं हटाना है।", "tool_calls": [
        {"name": "write_text", "arguments": {"path": "शब्द.txt", "text": "क्\u200dष"}}]},
    {"role": "tool", "content": "UTF-8 में लिखा गया: 4 code points।"},
    {"role": "assistant", "content": "सहेज दिया।"},
]
text = render(messages, effort="16k")
assert parse(text) == {"effort": "16k", "messages": messages}
```

Rendered (ZWJ shown as `\u200d`; the actual string holds the character):

```text
<|im_start|>system
Reasoning effort: 16k

हिंदी में उत्तर दें।<|im_end|>
<|im_start|>user
फ़ाइल में "क्\u200dष" सहेजें।<|im_end|>
<|im_start|>assistant
<|think|>
ZWJ को नहीं हटाना है।
<|/think|>
<|tool_call|>
{"arguments":{"path":"शब्द.txt","text":"क्\u200dष"},"name":"write_text"}
<|/tool_call|>
<|im_end|>
<|im_start|>tool
<|tool_result|>
UTF-8 में लिखा गया: 4 code points।
<|/tool_result|><|im_end|>
<|im_start|>assistant
सहेज दिया।<|im_end|>
<|endoftext|>
```

### Executed Hindi SWE task (Docker)

See `results/hindi_swe_e2e.md`, `swe-task/run_hindi_e2e.py` and `swe-task/Dockerfile.hindi`. A `prepare_text()` written to the v1 pre-tokenization rule fails 4 of 6 Hindi tests. The repair keeps ZWJ/ZWNJ, drops NFKC and still removes `U+200B`, so all 6 pass. The trajectory has think spans and round-trips exactly at all four effort levels. It ran in Docker with no network. This is an authored smoke task, not a SWE-bench score or a model-generated trajectory.
