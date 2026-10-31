# Structural identity: Sarvam-m vs Tekken (#130)

Task (#130): in #72, `verify_sarvam_m_structural_identity.py` ran BrahmicTokenizer-131K against itself. Here it runs on the pair it was written for, Sarvam-m against Tekken.

**Result: Sarvam-m has the same BPE table as Tekken, merge for merge and in the same rank order. The two differ only in special-token names and in ten special-token ids, 10 to 19. Every id from 20 up is identical.**

## Inputs (pinned)

| Name | HF repo | Revision | `tokenizer.json` sha256 |
|---|---|---|---|
| Sarvam-m | `sarvamai/sarvam-m` | `01534a53c46f2788e392dbb3d994e0fa8f04d3fd` (same pin as `REGISTRY` in `run_harness.py`) | `86150969e5647911369bbf28086fdad5fa5134f887e1a03a4e94030ad8e5468a` |
| Tekken | `mistralai/Mistral-Nemo-Base-2407` | `a4477a2f977929a969745b69bbd62e03043551a5` | `e11c71726323d33da7b8d6f6f269f1988931c0a52b7122bcdd8c05042974e0db` |

`Mistral-Nemo-Base-2407` is the repo the paper's reference script uses for "Tekken/Sarvam-m" (`evaluate_fertility_flores.py`). Verify scripts: BrahmicTokenizer-131K commit `7dfcf398172c825c6689ad578e8b484ca5f57bc9`.

## Commands

```bash
git clone https://github.com/theschoolofai/BrahmicTokenizer-131K.git && cd BrahmicTokenizer-131K
SARVAM=01534a53c46f2788e392dbb3d994e0fa8f04d3fd
TEKKEN=a4477a2f977929a969745b69bbd62e03043551a5
mkdir -p tok/sarvam_m tok/tekken
curl -sSL -o tok/sarvam_m/tokenizer.json https://huggingface.co/sarvamai/sarvam-m/resolve/$SARVAM/tokenizer.json
curl -sSL -o tok/tekken/tokenizer.json   https://huggingface.co/mistralai/Mistral-Nemo-Base-2407/resolve/$TEKKEN/tokenizer.json
shasum -a 256 tok/*/tokenizer.json                      # must match the table above

# 1. the repo's own script (sets: vocab strings, merge pairs, added-token strings)
python verify_sarvam_m_structural_identity.py tok/sarvam_m/tokenizer.json tok/tekken/tokenizer.json

# 2. the id-level check added in this PR
python <era-v5-lab>/teams/03-tokenizer/harness/structural_identity_ids.py tok/sarvam_m/tokenizer.json tok/tekken/tokenizer.json
```

Python 3.12.1, `tokenizers` 0.22.2. Both commands exit 0, and neither needs a Hugging Face login. If `huggingface_hub` fails with an SSL certificate error behind a corporate proxy, `curl` as above worked.

## 1. `verify_sarvam_m_structural_identity.py` (A = Sarvam-m, B = Tekken)

| | Sarvam-m (A) | Tekken (B) | identical | only in A | only in B |
|---|---|---|---|---|---|
| Normal vocab strings | 131,072 | 131,072 | 131,066 | 6 | 6 |
| BPE merges | 269,443 | 269,443 | 269,443 | 0 | 0 |
| Merge rank order same | | | **True** | | |
| Added / special tokens | 1,000 | 1,000 | 994 | 6 | 6 |

- Only in Sarvam-m: `[IMG]`, `[IMG_BREAK]`, `[IMG_END]`, `[SYSTEM_PROMPT]`, `[/SYSTEM_PROMPT]`, `[TOOL_CONTENT]`.
- Only in Tekken: `<SPECIAL_14>` to `<SPECIAL_19>`.
- Verdict printed by the script: `RESULT: BPE-TABLE IDENTICAL`, divergence confined to added/special tokens.
- Control (the #72 call, BrahmicTokenizer-131K against itself): `RESULT: STRUCTURALLY IDENTICAL`.

## 2. `structural_identity_ids.py`: what the set comparison does not show

| | Count |
|---|---|
| Same string in both | 131,066 |
| Same string **and** same id | 131,062 |
| Same string, **different id** | 4 |
| Ids whose string differs | 10 (ids 10 to 19) |

The script above compares strings only, so it hides the 4 tokens with the same name at a different id:

| id | Sarvam-m | Tekken |
|---|---|---|
| 10 | `[IMG]` | `<pad>` |
| 11 | `<pad>` | `[PREFIX]` |
| 12 | `[IMG_BREAK]` | `[MIDDLE]` |
| 13 | `[IMG_END]` | `[SUFFIX]` |
| 14 | `[PREFIX]` | `<SPECIAL_14>` |
| 15 | `[MIDDLE]` | `<SPECIAL_15>` |
| 16 | `[SUFFIX]` | `<SPECIAL_16>` |
| 17 | `[SYSTEM_PROMPT]` | `<SPECIAL_17>` |
| 18 | `[/SYSTEM_PROMPT]` | `<SPECIAL_18>` |
| 19 | `[TOOL_CONTENT]` | `<SPECIAL_19>` |

So Sarvam-m is not a pure rename. It inserted `[IMG]`, `[IMG_BREAK]`, `[IMG_END]` at ids 10 to 12 and shifted `<pad>`, `[PREFIX]`, `[MIDDLE]` and `[SUFFIX]` up by 1 to 3. Ids 0 to 9 and 20 and above are unchanged.

Other parts of the pipeline:

| Part | Identical |
|---|---|
| normalizer | True |
| pre_tokenizer | True |
| decoder | True |
| post_processor | False, but only because Tekken's `special_tokens` table also lists `</s>` (id 2). The single and pair templates are the same, so encoding is unaffected. |

Encode check on 8 fixed samples (English, Hindi, Bengali, Tamil, Telugu, Odia, Java code, mixed text with an emoji): **8 of 8 give identical ids** (11, 17, 17, 19, 15, 88, 18 and 13 tokens). The Odia sentence has 6 words and costs 88 tokens (about 14.7 per word), in line with the high Sarvam-m Odia fertility in `COMPARE.md` (18.18).

## What this means

- **Fertility.** Any text that does not use the renamed specials gets the same ids from both tokenizers. So Sarvam-m's FLORES and code numbers should equal Tekken's, which is the paper's claim. Run `run_harness.py` on a Tekken row to confirm the numbers if needed. The repo has no Tekken row yet.
- **Models.** A model trained on Tekken ids cannot use Sarvam-m's special tokens as they are. Ids 10 to 19 mean different things, so `<pad>`, `[PREFIX]`, `[MIDDLE]` and `[SUFFIX]` move. This matters for G3 and G4 only when a Tekken-trained or Sarvam-m-trained checkpoint is reused. It does not matter for v0, which keeps its own ids (`v0/special_slots.md`).
- **Limits.** This checks tokenizer files, not model behaviour. It covers one Tekken revision. The encode check uses 8 sentences, not a corpus.
