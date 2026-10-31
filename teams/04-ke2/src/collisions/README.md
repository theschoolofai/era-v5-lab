# KE2 collisions — BrahmicTokenizer-131K

Week-1 question: does every token get a unique Kronecker code, and if not, why?

## Result

| Table | P | Groups | Tokens in groups | Excess tokens | Largest group | Cause |
|---|---|---|---|---|---|---|
| **raw** (KE2) | 32 | **0** | 0 | 0 | — | — |
| **raw** (KE2) | 64 | **0** | 0 | 0 | — | — |
| decode (library baseline) | 32 | 10 | 1,151 | 1,141 | 658 | all `decode_collapse` |
| decode (library baseline) | 64 | 10 | 1,151 | 1,141 | 658 | all `decode_collapse` |

- **With exact byte extraction (raw), all 131,072 tokens have distinct bytes at P=32 and P=64.**
  Since the codec is injective on distinct byte strings of length ≤ P (see the proof),
  every token gets a unique code.
- With the library's current extraction (`decode([id])`), 1,151 tokens share codes.
  Every group has one cause: partial-character tokens decode to U+FFFD.
- P=32 and P=64 are identical because no token is longer than 32 bytes
  (no truncation happens).

Tokenizer: `theschoolofai/BrahmicTokenizer-131K`,
`tokenizer.json` sha256 `01d968a7970b029c071b29f060abf6104b66168dedf2ff3b1a0290a545739fff`.

## Definitions

- **Collision:** two token IDs whose table rows (bytes after truncation to P) are identical.
  Identical rows give identical codes, so the model cannot tell the tokens apart.
- **Extraction** — how a token ID is turned into bytes (tables built by `src/build_tables.py` (the `ke2` package)):
  - `raw` — exact bytes, by inverting the 256-symbol ByteLevel alphabet the tokenizer
    stores tokens in. Special tokens use their literal text. **This is the KE2 table.**
  - `decode` — what `kronecker-embeddings` 0.1.1 does today:
    `tokenizer.decode([id]).encode("utf-8")`. Reported as a baseline.
- **Truncation rule:** raw `bytes[:P]`; decode UTF-8-safe (upstream behaviour). Moot here.

## Causes

| Cause | Meaning |
|---|---|
| `empty` | a member has zero bytes (every empty row encodes to the zero vector) |
| `duplicate_vocab` | members have identical true bytes (two vocabulary entries, same bytes) |
| `special_literal` | a special token's literal text equals a normal token's bytes |
| `decode_collapse` | true bytes differ, but the extraction already made them equal, via U+FFFD |
| `truncation` | bytes differ, but are equal after cutting to P |
| `other` | none of the above — **must be zero** (it is) |

## Example (decode table, group 3)

Tokens 26588 and 54680 have true bytes `a1 e0 a6 bc` and `af e0 a6 bc`:
a stray byte (part of some other character) followed by the Bengali nukta `়` (U+09BC).
The stray byte is not a valid character on its own, so `decode([id])` replaces it with
`�` (`ef bf bd`). Both tokens become `�়` (`ef bf bd e0 a6 bc`) — one code for two tokens.
The raw table keeps them distinct.

## Files

`teams/04-ke2/results/collisions.csv` — one row per collision group.

| Column | Meaning |
|---|---|
| `extraction` | `raw` or `decode` |
| `P` | `pos_dim` (32 or 64) |
| `group_id` | index within (extraction, P), ordered by smallest token ID |
| `cause` | see Causes |
| `script_class` | members' class if all the same, else `multiple(k)` |
| `member_classes` | `class:count;…` for the members |
| `n_tokens` | members in the group |
| `token_ids` | member IDs, `;`-separated |
| `bytes_hex` | the shared table row, hex |
| `byte_len` | its length |
| `true_bytes_hex_examples` | exact bytes of the first 5 members, hex |

`teams/04-ke2/results/collisions_summary.csv` — one row per (extraction, P, script class); every class
appears, including those with zero collisions.

| Column | Meaning |
|---|---|
| `n_tokens` | tokens in this class |
| `n_colliding_tokens` | of these, tokens in any collision group |
| `n_excess_tokens` | colliding tokens beyond the first of each group (= codes lost) |
| `rate_colliding` | `n_colliding_tokens / n_tokens` |

So 1,151 colliding tokens fall into 10 groups; only 10 distinct codes remain for them,
i.e. 1,141 codes are lost. Both numbers are reported; they answer different questions.

`teams/04-ke2/results/collisions_meta.json` — tokenizer path and sha256, package versions, totals per
table, and the gate (`gate_zero_other`).

`teams/04-ke2/results/inspect_BrahmicTokenizer-131K.json` — step-1 census of the vocabulary
(lengths, specials, fragments, single-byte coverage, codec smoke test).

## Caveats

1. **Script classes come from `build_tables.script_class`.** Classes are chosen from the
   decoded characters' Unicode blocks.
2. **`Partial-UTF8[...]` sub-labels are guesses from lead bytes.** Brahmic sub-labels are
   reliable (the lead bytes select the block). Others are approximate — e.g.
   `E0: Sinhala/Thai/Tibetan remnant` also covers Samaritan, Arabic-extended and Lao.
   `continuation-only` fragments have no lead byte and cannot be attributed.
3. **`Mixed` means two or more character classes** (e.g. Latin + digits, `2nd`), not two
   writing systems. Tokens with letters from two scripts: **0**
   (`tests/test_collisions.py::test_no_cross_script_tokens_brahmic`), consistent with the
   model card.
4. Of the 1,151 colliding tokens in the decode table, 4 genuinely contain `�`;
   the other 1,147 are fragments (1,306 fragments exist; 159 stay unique by chance).
   748 of the colliding fragments are CJK or Hangul remnants; 52 are Brahmic.

## Reproduce

Requires `kronecker-embeddings==0.1.1`, `tokenizers`, `transformers`, `torch`, `numpy`,
and `src/build_tables.py` (the `ke2` package) (Tables task).

```bash
cd teams/04-ke2
python src/collisions/inspect_tokenizer.py      # step-1 census
python src/collisions/build_collisions.py       # writes teams/04-ke2/results/, exit code 1 if any 'other'
cd ../..
python -m pytest teams/04-ke2/tests -q      # includes a check that results/ is current
```

Other tokenizer: `KE2_TOKENIZER=<path or HF id>` for the tests, `--tokenizer` for the scripts.
