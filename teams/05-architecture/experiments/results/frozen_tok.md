# Week 3 frozen-tokenizer comparison

**Status: old baseline confirmed. Frozen C3 run and BPB delta pending.** Due Wed 18 Nov 2026.

## Reference and run plan

The lead selected the Gate 2 T2 Muon arm (`exp2_muon`). TSAI reported mean held-out BPB of **1.6607** across seeds 1234, 1235 and 1236 after 1,221 steps. TSAI confirmed seed 1235 as the match and reported old-tokenizer BPB of **1.6601** at that seed (1234: 1.6443, 1236: 1.6777). The manifests are on the Gate 2 evidence page. The three-seed mean is context for the matched comparison. [EXP-2 request](https://github.com/theschoolofai/era-v5-lab/pull/354)

TSAI will stage the same Gate 2 `train.jsonl` (SHA-256 starts `267c33bf`), `runtime_fast.yaml`, and the `t2m1` resolution. TSAI will apply the C3 scoring patch on top of the speed fixes at `71bc0fb` after reviewing [#474](https://github.com/theschoolofai/era-v5-lab/pull/474) on Mon 16 Nov. Match the seed's resolved settings, raw training text, holdout, and 1,221-step budget. Verify the full training digest and resolved settings from the manifest. Keep artifact validation enabled and pass the pinned C3 tokenizer identity in the run setup. [Gate 2 trainer diff discussion](https://github.com/theschoolofai/era-v5-lab/pull/441)

## Verified local inputs

| Artifact | SHA-256 |
| --- | --- |
| Old tokenizer v0 | `2de039f20d17afd17615095c406c43087359673b767ed0fe2c480b995f2af8e5` |
| Frozen C3 sample-v0 | `15468e66457b43af79f695cbe585c0d03e3cfe7a4a5d04d189dd3c6b9f02ddc3` |
| Locally rebuilt frozen raw P32 NPZ | `f775213c8b01602ca1179cd0b40a07340220e40cafa178e6315c87ab02da9c9b` |
| Frozen raw P32 content | `fc5e5f8ffacbe93ecdedc276661edfd43ed9a13621eb4a68166ef80e24e88f9b` |
| Original heldout_v1 JSONL | `21c6e4b2df8dae9d69e254f4a00fc934d2a3c70f0675065a03724299d94312bb` |

Built the raw P32 table with G4's `src/build_tables.py` at P=32. G5 accepted the verified C3 tokenizer and table when supplied the pinned C3 checksum. The table has 131,072 rows and zero truncated entries.

## Holdout preflight and scoring decision

Of 1,059 documents, C3's token bytes reconstructed the original text for 985. For the other 74, they reconstructed C3-normalized text exactly. For example, C3 maps Bengali U+09AF followed by U+09BC to U+09DF. Original holdout text totals 3,775,551 UTF-8 bytes. C3-normalized text totals 3,762,753 bytes. The current loader checks reconstruction against original bytes and rejects those 74 documents.

**Approved scoring policy:** TSAI directed us to use the original `heldout_v1` text and its original UTF-8 byte count for both tokenizers. C3 applies its normalizer internally. Its reconstructed bytes are checked against that normalized text, and BPB uses the original-byte denominator for the whole file and every slice. Keep all 1,059 documents and reuse the matched old Muon BPB from the original holdout. No old-model rescore on normalized text is needed.

Deepjyoti confirmed the holdout builder strips leading and trailing whitespace without applying Unicode normalization. All 1,059 documents are already NFC. The 74 differences are consistent with C3's additional Bengali-script and Gurmukhi nukta recomposition rules, which go beyond NFC.

The exact TSAI training file still needs a preflight. The local harness patch is based on `71bc0fb` and must be checked with TSAI's speed-fix diff and `runtime_fast.yaml` before the official run. The frozen comparison uses uncached windows because the current cache schema assumes that encoded byte lengths sum to original bytes.

## Result

| Run | Seed | Completed steps | Held-out BPB | Evidence |
| --- | --- | --- | --- | --- |
| Old tokenizer | 1235 | 1,221 | 1.6601 | TSAI confirmation. Manifest on the Gate 2 evidence page. |
| Frozen C3 | 1235 | Pending | Pending | TSAI manifest and metrics |

**BPB delta (frozen BPB minus 1.6601):** Pending. Record the scoring policy, held-out byte count, scored tokens, training bytes where available, trainer and runtime identity, and any differences in run settings.
 
## Local verification of the scoring path

The frozen C3 path loaded every original holdout document and all 15 slices. A targeted test checked whole-file and per-slice BPB using different original and encoded byte counts. A one-step CPU Muon smoke at seed 1235 with synthetic text containing decomposed Bengali nukta completed training, evaluation, and output writing in 51.40 seconds. The scorer used 72 original bytes and logged 60 encoded bytes. This is integration evidence. Full T2 quality and performance remain pending.
The local CUDA integration smoke also completed three steps in 5.98 seconds. See the [smoke command and output](../../jobs/evidence/2026-11-15-frozen-c3-muon/smoke.md).
