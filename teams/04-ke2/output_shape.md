# KE2 output shape (for G5)

**Status:** draft v0, 27 Oct. Both P = 32 and P = 64 are supported; P = 32 is recommended.
Final after the re-check on G3 tokenizer v0 (28 Oct).

## Shape

KE2 replaces the token-embedding table. Each token ID becomes a fixed vector (no learned
weights), followed by one learned linear layer.

| Step | Shape | dtype |
|---|---|---|
| Input: token IDs | `(B, T)` | int64 |
| KE2 code | `(B, T, D)`, with `D = 256 · P` | float32 |
| Projection `Linear(D, d_model, bias=False)` | `(B, T, d_model)` | float32 |

`B` = batch size, `T` = sequence length, `d_model` = model width (open; set by G5 / TSAI).
The final shape is the same as a standard `nn.Embedding`. KE2 does not change tokenization,
so `T` for a given text is the same as with a standard embedding.

| P | D |
|---|---|
| **32 (recommended)** | **8,192** |
| 64 | 16,384 |

## Settings

| Setting | Value | Source |
|---|---|---|
| `pos_dim` (P) | 32; 64 supported | Longest token is 32 bytes, so P = 32 cuts nothing off and gives 0 collisions (`results/collisions.csv`, `results/inspect_BrahmicTokenizer-131K.json`) |
| `char_dim` | 256 | One slot per possible byte value (fixed) |
| `D` | `256 · P` | Codec definition |

`pos_dim` is the byte position **inside a token** (slot 0 = first byte). It is unrelated to the
token's position in the sequence; sequence positions (e.g. RoPE) are handled as usual.

### P = 32 vs P = 64

| | P = 32 | P = 64 |
|---|---|---|
| `D` (numbers per token) | 8,192 | 16,384 |
| Projection parameters at `d_model = 768` | 6.29 M | 12.58 M |
| Code memory per token (float32) | 32 KB | 64 KB |
| Code memory for 8,192 tokens (e.g. `B = 8`, `T = 1,024`) | 256 MB | 512 MB |
| Tokens longer than P (cut off) | 0 | 0 |
| Collisions | 0 | 0 |
| Slots used on average (mean token = 6.56 bytes) | 20.5 % | 10.3 % |

On this tokenizer both give identical codes for every token's bytes; P = 64 costs twice the size
with no gain. The longest token is exactly 32 bytes, so P = 32 has no spare room: any longer
token in a future tokenizer would be cut off.

## Properties of the code

- Index layout: byte value `b` at position `p` maps to index `b · P + p`.
- Normalised per token: mean ≈ 0, std ≈ 0.9999 (library epsilon 1e-6).
- Before normalisation, a token of `L` bytes has exactly `L` non-zero entries (`L ≤ 32`).
- Deterministic: the same token ID always gives the same vector.
- Special tokens (BOS, EOS, PAD, UNK, …) are encoded from their literal text, so each has
  its own non-zero vector, including PAD.

## Parameter count (input side)

| | Formula | Example at `d_model = 768` |
|---|---|---|
| Standard embedding | `V · d_model` (V = 131,072) | 100.66 M |
| KE2, P = 32 | `8,192 · d_model` | 6.29 M |
| KE2, P = 64 | `16,384 · d_model` | 12.58 M |

KE2's size does not depend on V, so adding special-token slots does not change it.

## Not covered

The output side (the model's next-token layer) is not decided. KE2 decision: 14 Nov.

## Pending

- 28 Oct: re-run the KE2 checks on G3 tokenizer v0. If its longest token is still ≤ 32 bytes
  with 0 collisions, P = 32 is final. Otherwise this doc is updated.
- 31 Oct: same check with G10's special-token list.

Based on: BrahmicTokenizer-131K (`tokenizer.json` sha256
`01d968a7970b029c071b29f060abf6104b66168dedf2ff3b1a0290a545739fff`), kronecker-embeddings 0.1.1 (commit d07cb54, as pinned in `src/ke2/config.py`).
