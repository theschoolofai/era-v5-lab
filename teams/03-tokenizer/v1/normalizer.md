# v1 idea 2: Unicode normalizer (no retrain)

Owner: Harini Jasti · Date: 29 Oct 2026 · Base: BrahmicTokenizer-131K, commit `7dfcf398172c825c6689ad578e8b484ca5f57bc9`

## Summary

BrahmicTokenizer-131K has no normalizer (`"normalizer": null`), so the same word written in two Unicode forms is cut into different pieces. This change adds a normalizer only:

```
NFC  →  old-style Malayalam chillu → atomic chillu  →  re-join nukta letters (Bengali, Gurmukhi)
```

- Vocab, merges (content and rank) and all 356 special/added tokens are unchanged, so it can ship before any retrain and does not affect the v0 reserved ids.
- **Recommended variant: `nfc+chillu+nukta-BnPa`.** It meets both expectations of the spec and makes no language worse on clean text.

| Expectation | Result |
|---|---|
| About −5% tokens on Malayalam | **−6.6%** on Malayalam written with old-style chillus (3.7125 → 3.4672). −0.19% on clean FLORES, which is already mostly atomic. |
| Robustness on NFD Bn/Ta/Or | **Confirmed.** NFD text costs +2.93% mean today (Kn +10.8%, Bn +4.3%, Ml +3.9%, As +3.9%, Ta +2.9%, Or +1.3%). With the normalizer the penalty is 0. |
| No regression | Clean FLORES mean **−0.13%**; no language worse. English and code are unchanged (NFC is identity on ASCII). |

## The rules

1. **NFC**: canonical composition, so decomposed (NFD) input becomes the standard form.
2. **Chillu**: consonant + virama (U+0D4D) + ZWJ (U+200D) → atomic chillu, for ണ ന ര ല ള ക → ൺ ൻ ർ ൽ ൾ ൿ (U+0D7A–U+0D7F).
3. **Nukta re-join (Bengali, Gurmukhi only)**: NFC splits composition-excluded letters into letter + nukta (ড় ঢ় য়, ਲ਼ ਸ਼ ਖ਼ ਗ਼ ਜ਼ ਫ਼). The tokenizer learned the one-character forms, so they are joined back after NFC.

Why rule 3 is needed: plain NFC (the spec as written) makes clean Bengali **+0.87%**, Assamese **+0.38%** and Punjabi **+0.18%** worse. Re-joining for Devanagari and Odia as well was tested and rejected, because those scripts prefer the split form (Hi +0.16%, Or +0.04%).

## Method

- Data: FLORES-200 dev+devtest, 2,009 sentences per language, 12 languages, in three forms:
  - **A. clean**: as published
  - **B. NFD**: the same text decomposed
  - **C. old chillu**: Malayalam rewritten with old-style chillus
- Fertility = tokens / whitespace words of the clean text (the same word count for every form), no BOS/EOS. Mean Brahmic = mean of the 11 Indic languages.
- Round trip: `decode(encode(x)) == normalize(x)`.
- Script: `normalizer_experiment_v2.py` (in this folder), run from the BrahmicTokenizer-131K repo root:

```
python normalizer_experiment_v2.py --out C:/tmp/v1_norm_final --save nfc+chillu+nukta-BnPa
```

## Results

### A. Clean FLORES (fertility, % vs baseline)

| Lang | baseline | chillu | nfc+chillu | nfc+chillu+nukta | **nfc+chillu+nukta-BnPa** |
|---|---|---|---|---|---|
| En | 1.2352 | +0.00% | +0.00% | +0.00% | **+0.00%** |
| Hi | 1.6429 | +0.00% | −0.06% | +0.16% | **−0.06%** |
| Bn | 2.3295 | +0.00% | +0.87% | −1.01% | **−1.01%** |
| Ta | 3.1166 | +0.00% | −0.00% | −0.00% | **−0.00%** |
| Te | 3.0292 | +0.00% | −0.01% | −0.01% | **−0.01%** |
| Kn | 3.2734 | +0.00% | −0.03% | −0.03% | **−0.03%** |
| Ml | 3.4738 | −0.17% | −0.19% | −0.19% | **−0.19%** |
| Mr | 2.5723 | +0.00% | +0.00% | +0.00% | **+0.00%** |
| Gu | 2.2748 | +0.00% | +0.00% | +0.00% | **+0.00%** |
| Pa | 2.5955 | +0.00% | +0.18% | −0.11% | **−0.11%** |
| Or | 4.1287 | +0.00% | −0.10% | +0.04% | **−0.10%** |
| As | 2.7535 | +0.00% | +0.38% | −0.08% | **−0.08%** |
| **Mean Brahmic** | **2.8355** | −0.02% | +0.07% | −0.10% | **−0.13% (2.8317)** |

### B. NFD input (fertility, % vs baseline on clean text)

| Lang | no normalizer | **nfc+chillu+nukta-BnPa** |
|---|---|---|
| En | +0.07% | **+0.00%** |
| Hi | −0.06% | **−0.06%** |
| Bn | +4.25% | **−1.01%** |
| Ta | +2.93% | **−0.00%** |
| Te | +1.99% | **−0.01%** |
| Kn | +10.84% | **−0.03%** |
| Ml | +3.94% | **−0.19%** |
| Mr | +0.23% | **+0.00%** |
| Gu | +0.00% | **+0.00%** |
| Pa | +0.18% | **−0.11%** |
| Or | +1.26% | **−0.10%** |
| As | +3.94% | **−0.08%** |
| **Mean Brahmic** | **+2.93%** | **−0.13%** |

### C. Malayalam with old-style chillus

| | no normalizer | chillu (any variant) |
|---|---|---|
| Ml fertility | 3.7125 (+6.87% vs clean) | 3.4672 (**−6.6%**) |

### D. Round trip

0 failures in every language for every variant.

## Verify scripts on the recommended tokenizer

| Script | Result |
|---|---|
| verify_no_cross_script_merges | PASS (0 of 301,398) |
| verify_max_byte_length | PASS (131,072 vocab, longest 32 bytes) |
| verify_kronecker_constraints_unified | PASS |
| verify_sarvam_m_structural_identity (original vs normalized) | STRUCTURALLY IDENTICAL: vocab, merges (same rank) and 356 added tokens |

sha256 of the normalized `tokenizer.json` (built on the base tokenizer): `07c1441dc91a70e17a10846a690ca541fd6472b0b8a482011b31d26c385c8d01`

The file itself is not committed (over the 5 MB limit). To apply the same normalizer to the v0 tokenizer, run the script with `--tokenizer <path to v0 tokenizer.json>`. Ids, merges and reserved slots are untouched, so the result is v0 plus the normalizer.

## Notes and limits

- The normalizer changes text before tokenization, so decode returns the normalized text (for example, an old-style chillu comes back atomic). Data and training pipelines should tokenize through the same `tokenizer.json`, so the change applies consistently.
- Gains on real web text depend on how often it uses NFD or old-style chillus. A follow-up is to count these forms in the FineWeb-2 sample used by `train/fetch_corpus.py`.
