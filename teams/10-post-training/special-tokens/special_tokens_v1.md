# Special tokens v1 (Final Tokenizer ID Allocation)

Shared G10 special-token allocation file (`teams/10-post-training/special-tokens/special_tokens_v1.md`).  
Prepared for **Team 3 (G3 Tokenizer)**, **Team 4 (G4 KE2)**, **Team 9 (G9 Evaluation)**, and **Team 12 (G12 Quantization and Serving)** for [Issue #132](https://github.com/theschoolofai/era-v5-lab/issues/132) and the Week 2 tokenizer freeze (`teams/03-tokenizer/v0/special_slots.md`, [PR #173](https://github.com/theschoolofai/era-v5-lab/pull/173)).

---

## 1. Core Architecture, Tokenizer ID Mapping & Pre-Tokenization Rules

- **One Exact Tokenizer ID per Marker**:
  - In `special_tokens_v0.md`, G10 used `000..255` as logical slot numbers. Tokenizer IDs `0..255` in `BrahmicTokenizer-131K` are byte tokens and cannot hold control markers.
  - **Existing Base Tokenizer Specials Kept As-Is**: Any marker that already exists with the same ASCII `<|name|>` surface in the base tokenizer (`129994` and `130725..130821`) keeps its exact existing tokenizer ID: `<|im_start|>` (`129994`), `<|tool_call|>` (`130773`), `<|tool_result|>` (`130774`), `<|fim_prefix|>` (`130801`), `<|fim_middle|>` (`130802`), `<|fim_suffix|>` (`130803`), `<|fim_pad|>` (`130804`), `<|im_end|>` (`130816`), `<|file_sep|>` (`130817`), and `<|repo_name|>` (`130818`).
  - **New Markers in Team 3 Slots (`g10_slot_00..63`, IDs `130822..130885`)**: Each new G10 marker takes exactly one slot in `130822..130885` by renaming the string in place while keeping `special: true` and the vocab size (`131,072`) unchanged: `<|endoftext|>` (`130822`, `g10_slot_00`), `<|think|>` (`130823`, `g10_slot_01`), `<|/think|>` (`130824`, `g10_slot_02`), `<|/tool_call|>` (`130825`, `g10_slot_03`), `<|/tool_result|>` (`130826`, `g10_slot_04`), `<|subagent_call|>` (`130827`, `g10_slot_05`), and `<|subagent_return|>` (`130828`, `g10_slot_06`).
- **One Pipe-Delimited ASCII Form Only (`<|name|>`)**:
  - The chat format **does not use** the base tokenizer's bare XML tokens `<think>` (`128512`), `</think>` (`128601`), `<tool_call>` (`130174`), `</tool_call>` (`130226`), `<tool_response>` (`130819`), or `</tool_response>` (`130820`).
  - Every G10 control marker uses the single ASCII form `<|name|>`. Plain `<think>` and fullwidth look-alikes (`<｜think｜>`, `＜tool_call＞`) are rejected at the input boundary by `render.py`.
- **Structural vs. Value Plane Separation (27 Oct Ruling)**:
  - Special tokens are strictly reserved for structural boundaries.
  - Variable values (reasoning effort, tool names, arguments, options) remain plain text inside the structure.
  - Reasoning effort is conditioned via the plain-text system line: `Reasoning effort: {1k|4k|16k|64k}`.
- **Pre-Tokenization & Script Integrity Rule (No NFKC; Keep ZWJ and ZWNJ)**:
  - **Do not apply NFKC to content.** Special tokens in the tokenizer match exact raw ASCII text (`<|...|>`), so a fullwidth `<｜think｜>` is tokenized as ordinary text and can never trigger a special marker ID.
  - **Keep `ZWJ` (`U+200D`) and `ZWNJ` (`U+200C`) untouched.** As demonstrated across G10's Indic datasets (`ind-hi-hplt` in [PR #157](https://github.com/theschoolofai/era-v5-lab/pull/157), `ind-mr-fw2`, `ind-kn-fw2`, `ind-ta-sangraha-v`, and `chandassu`), `U+200D` and `U+200C` are essential Indic script joiners governing conjuncts, eyelash-ra (`ऱ्या`), and half-consonant forms, while NFKC corrupts mathematical/superscript symbols (`²` -> `2`, `½` -> `1/2`). Strip only true `A1` invisible junk (`U+200B` ZWSP and `U+FEFF` BOM) during text preparation.
- **No `<|eval_fp_*|>` Special Tokens (TSAI v0 Decision)**:
  - Do not add `<|eval_fp_*|>` special tokens. Evaluation fingerprints are plain-text canary strings placed by Team 9 (G9) in benchmark data so decontamination filters and logit probes can detect them in ordinary text. Former v0 slot numbers `021..023` (and unallocated Team 3 slots `g10_slot_07..63`, IDs `130829..130885`) remain **reserved and unused**.

---

## 2. Final G10 Marker Table — Exact Team 3 Tokenizer IDs

Every marker below maps to **exactly one** atomic special token ID (`special: true`) in Team 3's `BrahmicTokenizer-131K` (`vocab_size = 131,072`, 256-slot special architecture):

### A. Active Chat Format `v0` Markers (9 Markers — Active in `v0.1`, PR #173)

| Tokenizer ID | Source / Slot in Team 3 Tokenizer | Name | Special Token Surface (Atomic) | Role in ChatML `v0` |
| :--- | :--- | :--- | :--- | :--- |
| `129994` | Existing base special (kept as-is) | `im_start` | `<\|im_start\|>` | Start of a ChatML turn (`system`, `user`, `assistant`, `tool`) |
| `130816` | Existing base special (kept as-is) | `im_end` | `<\|im_end\|>` | End of a ChatML turn |
| `130822` | `g10_slot_00` (renamed in v0.1) | `endoftext` | `<\|endoftext\|>` | End of document / transcript boundary (distinct from base `<\|end_of_text\|>` at ID `36`) |
| `130823` | `g10_slot_01` (renamed in v0.1) | `think` | `<\|think\|>` | Start of reasoning trace (never bare `<think>` at ID `128512`) |
| `130824` | `g10_slot_02` (renamed in v0.1) | `think_end` | `<\|/think\|>` | End of reasoning trace (never bare `</think>` at ID `128601`) |
| `130773` | Existing base special (kept as-is) | `tool_call` | `<\|tool_call\|>` | Start of structured JSON tool call payload (never bare `<tool_call>` at ID `130174`) |
| `130825` | `g10_slot_03` (renamed in v0.1) | `tool_call_end` | `<\|/tool_call\|>` | End of structured JSON tool call payload (never bare `</tool_call>` at ID `130226`) |
| `130774` | Existing base special (kept as-is) | `tool_result` | `<\|tool_result\|>` | Start of tool execution output inside a `tool` turn |
| `130826` | `g10_slot_04` (renamed in v0.1) | `tool_result_end` | `<\|/tool_result\|>` | End of tool execution output inside a `tool` turn |

### B. Code Infilling (FIM), Repository Context & Sub-Agent Markers (8 Markers)

| Tokenizer ID | Source / Slot in Team 3 Tokenizer | Name | Special Token Surface (Atomic) | Role in Code & Agentic Workflows |
| :--- | :--- | :--- | :--- | :--- |
| `130801` | Existing base special (kept as-is) | `fim_prefix` | `<\|fim_prefix\|>` | Fill-In-The-Middle prefix anchor for code infilling |
| `130802` | Existing base special (kept as-is) | `fim_middle` | `<\|fim_middle\|>` | Fill-In-The-Middle middle target slot for code infilling |
| `130803` | Existing base special (kept as-is) | `fim_suffix` | `<\|fim_suffix\|>` | Fill-In-The-Middle suffix context anchor |
| `130804` | Existing base special (kept as-is) | `fim_pad` | `<\|fim_pad\|>` | Fill-In-The-Middle padding token for batched infilling sequences |
| `130817` | Existing base special (kept as-is) | `file_sep` | `<\|file_sep\|>` | Multi-file boundary delimiter in workspace repository map |
| `130818` | Existing base special (kept as-is) | `repo_name` | `<\|repo_name\|>` | Repository / package identifier anchor in multi-file context |
| `130827` | `g10_slot_05` (`130822 + 5`) | `subagent_call` | `<\|subagent_call\|>` | Sub-agent / delegation invocation boundary |
| `130828` | `g10_slot_06` (`130822 + 6`) | `subagent_return` | `<\|subagent_return\|>` | Sub-agent / delegation return boundary |

### C. Reserved & Unused G10 Slots (`g10_slot_07` .. `g10_slot_63`)

- **IDs `130829..130885` (`<|g10_slot_07|>` .. `<|g10_slot_63|>`, 57 slots)**: Reserved and unused.
- Former v0 slot numbers `021..023` (and all remaining slots in `g10_slot_07..63`) stay **reserved and unused** (no `<|eval_fp_*|>` tokens).

---

## 3. Machine-Readable Mapping for Team 3 (`ID Name Surface Source`)

```text
129994 im_start <|im_start|> existing_base
130773 tool_call <|tool_call|> existing_base
130774 tool_result <|tool_result|> existing_base
130801 fim_prefix <|fim_prefix|> existing_base
130802 fim_middle <|fim_middle|> existing_base
130803 fim_suffix <|fim_suffix|> existing_base
130804 fim_pad <|fim_pad|> existing_base
130816 im_end <|im_end|> existing_base
130817 file_sep <|file_sep|> existing_base
130818 repo_name <|repo_name|> existing_base
130822 endoftext <|endoftext|> g10_slot_00
130823 think <|think|> g10_slot_01
130824 think_end <|/think|> g10_slot_02
130825 tool_call_end <|/tool_call|> g10_slot_03
130826 tool_result_end <|/tool_result|> g10_slot_04
130827 subagent_call <|subagent_call|> g10_slot_05
130828 subagent_return <|subagent_return|> g10_slot_06
```

Remaining G10 slots `130829..130885` stay reserved as `<|g10_slot_07|>` .. `<|g10_slot_63|>`.

---

## 4. Dataset Pre-Training Sanity & Script Joiner Rules

1. **StarCoder (`code-python` · Sai Teja & `f20201351h-maker`, `code-go` · Ravi Naik, `code-rust` · Vikash Ranjan)**: Strip upstream `B3` ghost tokens (`[INST]`, `[/INST]`, `<think>`, `### Assistant:`) and StarCoder metadata prefixes (`<reponame>`, `<filename>`, `<gh_stars>`) during pre-processing so raw control markers are never learned from pre-training code. Keep PII redaction placeholders (`<NAME>`, `<EMAIL>`, `<PASSWORD>`, `<KEY>`) as ordinary text, never special tokens.
2. **Chandassu (`chandassu` · Sai Teja)**: Strip exported `_x000D_` carriage-return literals as plain text; preserve Telugu `ZWNJ` (`U+200C`) and `ZWJ` (`U+200D`) in all 1,014 poems where they occur.
3. **HPLT 3.0 Hindi (`ind-hi-hplt` · `gmrammohan15`, PR #157) & IndicCorpV2 Hindi (`ind-hi-indiccorp` · Ranjani)**: Keep `ZWJ` (`U+200D`) and `ZWNJ` (`U+200C`); do not apply NFKC to content; strip only `U+200B` (ZWSP) and `U+FEFF` (BOM) before the marker check.
4. **FineWeb-2 Marathi (`ind-mr-fw2` · Amit T), Tamil Sangraha (`ind-ta-sangraha-v` · Hema Varshini Palpandian), & FineWeb-2 Kannada (`ind-kn-fw2` · Lokesh Arundathi)**: Zero ghost chat tokens found. Preserve `ZWJ` (`U+200D`), `ZWNJ` (`U+200C`), and native vowel/virama sequences as standard text without NFKC normalization.
