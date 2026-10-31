# Special tokens v0

Shared G10 special-token file (`teams/10-post-training/special-tokens/special_tokens_v0.md`). Due Wednesday 28 Oct, and sent to the Tokenizer team (**Team 3 / G3**) by **Saturday 31 Oct** so G3 reserves all 256 token IDs before tokenizer training starts on 1 Nov. Team 9 delivers fingerprints v1 on 28 Oct.

## Rule for ChatML `v0` markers (G10 -> G3 handoff)

- **ChatML style is used for `v0`.**
- **Instructor ruling, 27 Oct:** special tokens only for structure that the model must never confuse with normal text (role-turn start and end, tool call start and end, tool result start and end, thinking start and end). Values inside that structure are plain text: tool names, arguments, effort level, options and settings. Keep the list short; the lead owns the final list and TSAI reviews it at the Gate.
- **Every marker below must be one atomic special token** in the tokenizer, never split into subword pieces, and plain-text tags like `<think>` or `<tool_call>` are rejected.
- **256 reserved token IDs (`0..255`):** G3 reserves the full 256-ID block. Assigned IDs below are frozen; unassigned IDs in `0..255` are reserved (`<|reserved_003|>` .. `<|reserved_255|>`).

## Team workflow (Core Team · 12 members)

- Keep this **one shared file** (`teams/10-post-training/special-tokens/special_tokens_v0.md`).
- Each of the 12 G10 Core Team members has their own dataset section below (for example `StarCoder`, `Stack Exchange`, `Indic web`).
- Each member adds the markers of their own dataset in their own section by pull request to the lead's branch (`g10-week1-post-training`).
- The team lead (Sai Teja) merges the member PRs, removes duplicates in the consolidated 256-token table, and opens one PR to `theschoolofai/era-v5-lab` `main`.

---

## Consolidated 256-token block for Team 3 (G3)

TSAI reserves 256 token IDs (`0..255`). Every chat marker below is registered as **one special token** in the tokenizer, never plain text:

| Token ID | Name | Special token surface (atomic) | Role in ChatML `v0` |
| --- | --- | --- | --- |
| `000` | `endoftext` | `<\|endoftext\|>` | End of document / transcript |
| `001` | `im_start` | `<\|im_start\|>` | Start of a ChatML turn |
| `002` | `im_end` | `<\|im_end\|>` | End of a ChatML turn |
| `024` | `think` | `<\|think\|>` | Start of reasoning trace (1 special token, never plain `<think>`) |
| `025` | `think_end` | `<\|/think\|>` | End of reasoning trace (1 special token, never plain `</think>`) |
| `026` | `tool_call` | `<\|tool_call\|>` | Start of tool call JSON payload (1 special token) |
| `027` | `tool_call_end` | `<\|/tool_call\|>` | End of tool call JSON payload (1 special token) |
| `028` | `tool_result` | `<\|tool_result\|>` | Start of tool output span inside a tool turn (1 special token) |
| `029` | `tool_result_end` | `<\|/tool_result\|>` | End of tool output span inside a tool turn (1 special token) |

Machine-readable list of assigned markers for G3 (`ID Name Surface`):

```text
000 endoftext <|endoftext|>
001 im_start <|im_start|>
002 im_end <|im_end|>
024 think <|think|>
025 think_end <|/think|>
026 tool_call <|tool_call|>
027 tool_call_end <|/tool_call|>
028 tool_result <|tool_result|>
029 tool_result_end <|/tool_result|>
```

All remaining 247 IDs in `0..255` (`003..023`, `030..255`) are reserved by TSAI as `<|reserved_003|>` through `<|reserved_255|>`.

### Effort levels (plain text, not tokens)

Effort is a plain-text line at the top of the first system turn: `Reasoning effort: {level}`. IDs `016..019` are free again and stay reserved.

- `1k`: 1024 tokens
- `4k`: 4096 tokens
- `16k`: 16384 tokens
- `64k`: 65536 tokens

The budget covers the think span and the tool trace. It does not cover the visible reply.

---

## Dataset sections by G10 Core Team member (12)

### 1. Sai Teja (Lead) — StarCoder (`code-python` · `bigcode/starcoderdata`)

- **Core team:** 10. Post-training and Agentic (Lead) · **Week 2:** 9. Evaluation · **Week 3:** 12. Quantization and Serving
- **Pack:** `code-python`
- **Language:** `Code`
- **Source:** `bigcode/starcoderdata`
- **Licence decision:** `TSAI reserves` (commercial-use data only)
- **Chat & ghost markers found in dataset (`B3`):** `<|endoftext|>`, `<|im_start|>`, `<|im_end|>`, `[INST]`, `[/INST]`, `### Assistant:`, `<think>`, `</think>`
- **Dataset-specific markers in `bigcode/starcoderdata`:**
  - Repository & file headers: `<reponame>`, `<filename>`, `<gh_stars>`
  - Notebook markers: `<jupyter_start>`, `<jupyter_text>`, `<jupyter_code>`, `<jupyter_output>`, `<empty_output>`
  - Commit & issue markers: `<commit_before>`, `<commit_msg>`, `<commit_after>`, `<issue_start>`, `<issue_comment>`
  - Redaction placeholders: `<NAME>`, `<EMAIL>`, `<KEY>`, `<PASSWORD>`
- **Action:** Strip `B3` ghost chat markers from pre-training text so the model never learns to emit control markers as plain text; register every ChatML `v0` marker above as **one special token** in G3's tokenizer.

### 1b. Sai Teja (Lead) — Chandassu (`BodduSriPavan111/chandassu`)

- **Core team:** 10. Post-training and Agentic (Lead) · **Week 2:** 9. Evaluation · **Week 3:** 12. Quantization and Serving
- **Pack:** `chandassu`
- **Language:** Telugu (`te`)
- **Source:** `BodduSriPavan111/chandassu`
- **Licence decision:** `TSAI reserves` (MIT on the dataset card; commercial use allowed)
- **Chat markers found:** none. No `<|im_start|>`, `<|im_end|>`, `<|endoftext|>`, `[INST]`, `<think>`, or `<tool_call>` in the 4,651 poems.
- **Not a special token:** `_x000D_` (1,134 Vemana poems). It is an exported carriage return left as plain letters. Strip it in cleaning. Do not give it a token id.
- **Not markers:** the hyphen in Andhranaayaka and the danda `।` in Laavanya are the yati pause, plain text. `U+200C` ZWNJ and `U+200D` ZWJ are part of Telugu writing (1,014 poems). Do not reserve them.
- **New token request:** none. The ChatML `v0` block above already covers this dataset. No assigned id is added or renumbered.

### 2. Ajay Kumar — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Ajay Kumar via PR)*
- **Dataset markers:** *(to be added by Ajay Kumar via PR; deduplicated into consolidated list on merge)*

### 3. Amit T — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Amit T via PR)*
- **Dataset markers:** *(to be added by Amit T via PR; deduplicated into consolidated list on merge)*

### 4. Anirudh Narla — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Anirudh Narla via PR)*
- **Dataset markers:** *(to be added by Anirudh Narla via PR; deduplicated into consolidated list on merge)*

### 5. Ashish Kamble — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Ashish Kamble via PR)*
- **Dataset markers:** *(to be added by Ashish Kamble via PR; deduplicated into consolidated list on merge)*

### 6. Hema Varshini Palpandian — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Hema Varshini Palpandian via PR)*
- **Dataset markers:** *(to be added by Hema Varshini Palpandian via PR; deduplicated into consolidated list on merge)*

### 7. Lokesh Arundathi — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Lokesh Arundathi via PR)*
- **Dataset markers:** *(to be added by Lokesh Arundathi via PR; deduplicated into consolidated list on merge)*

### 8. Rammohan Madhusudan — Indic web (`ind-hi-hplt` · HPLT 3.0 `hin_Deva`)

- **Pack / Language / Source:** `ind-hi-hplt` / `Hindi` / HPLT 3.0 (`data.hplt-project.org/three/sorted/hin_Deva`)
- **Chat & ghost markers found in dataset (`B3`):** none in all 500 documents. Checked by known patterns and by open-ended catalogues, all 0 hits:
  - known formats: ChatML / Llama-3 style `<|...|>` (also fullwidth `<｜...｜>`), `[INST]` / `[/INST]`, `<<SYS>>`, `<s>` / `</s>`, `<think>`, `<tool_call>`, `<tool_result>`, `<unk>` / `<pad>` / `<mask>` / `<bos>` / `<eos>`, `[CLS]` / `[SEP]` / `[MASK]`, SentencePiece `▁`, StarCoder-style `<reponame>`, `<jupyter_*>`, `<commit_*>`, `<issue_*>`;
  - catalogues: every `<...>` token without spaces (none exist), every `[UPPERCASE]` tag (none), HTML-escaped `&lt;...&gt;` (none), line-initial role prefixes in English and Hindi (`User:`, `Assistant:`, `System:`, `Human:`, `### Instruction:`, `उपयोगकर्ता:`, `सहायक:` ...), and every invisible or private-use code point (none).
  - Only 3 documents contain `<` at all: a chemistry equation, a `<3` emoticon, and legacy-font garbage.
- **Dataset-specific markers:** none. `प्रश्न 1:` / `उत्तर:` lines (3 documents) are FAQ sections written by the site, natural Q&A text, not chat markers. Stray HTML tag endings (`/>` in 3 documents, `B2`) are web residue cleaned as text, not reserved as tokens.
- **Not markers:** `U+200D` ZWJ and `U+200C` ZWNJ are part of Indic script (they control conjunct shaping), not special tokens or diseases. They do not occur in this pack (0 of 500 documents), but other Hindi sources will have them and the tokenizer must keep them.
- **New token request:** none. The ChatML `v0` block above covers everything needed for this dataset.
- **Action:** keep `B3` stripping in pre-training cleaning (nothing to strip in this pack); keep ZWJ/ZWNJ untouched.

### 9. Ranjani Chandrasekaran — Indic web (`ind-hi-indiccorp`)

- **Pack / Language / Source:** `ind-hi-indiccorp` — Hindi (`hi`) — `ai4bharat/IndicCorpV2` (`data/hi-{1,2,3}.txt`)
- **Dataset markers:** No ChatML-style ghost markers (`<|im_start|>`, `<|endoftext|>`, `<think>`, `<|tool_call|>`) found in the 500-document diagnosis sample. The pack is news/web prose, not chat data.
  - `U+200D` ZWJ and `U+200C` ZWNJ appear as legitimate Devanagari script joiners — per `diagnosis/DISEASES.md` these are valid text characters, **not** special tokens or diseases. Keep as plain text in the tokenizer.
  - Mojibake residue found in some documents: `ज़्` (ja + nukta + virama) where `र्` or `ड़` is expected — corpus damage (G1), not a marker.
  - Latin-script spans in otherwise-Hindi text (`Reverse osmosis`, `COVID19`, `WWE`, `USIBC`) and URLs — normal text, no special-token need.
  - **Action:** none required to strip ghost markers from this pack. Confirmed clean for ChatML v0.


### 10. Ravi Naik — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Ravi Naik via PR)*
- **Dataset markers:** *(to be added by Ravi Naik via PR; deduplicated into consolidated list on merge)*

### 11. Syed Abdul — Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Syed Abdul via PR)*
- **Dataset markers:** *(to be added by Syed Abdul via PR; deduplicated into consolidated list on merge)*

### 12. Vikash Ranjan — Stack Exchange / Dataset section *(placeholder for PR to `g10-week1-post-training`)*

- **Pack / Language / Source:** *(to be added by Vikash Ranjan via PR)*
- **Dataset markers:** *(to be added by Vikash Ranjan via PR; deduplicated into consolidated list on merge)*
