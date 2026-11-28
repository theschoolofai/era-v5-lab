# Staging Recipe for Dry Run 2 Post-Training Jobs (TSAI 28 Nov Unblock)

Prepared per TSAI's 28 Nov status note:

> "#861 is merged. The two Gate 4 jobs are blocked on inputs that are not on the job machine: the OCR-2 firewalled shards 0 to 3, `rl-code-v1-train.pool.jsonl` and `rl-code-v1-heldout.pool.jsonl`. Send TSAI a staging recipe or links for them by Wed 2 Dec, 7:00 AM IST. The Docker runner also needs a fix on the job machine; TSAI handles that. The dry run 2 weights (step 1,221) are ready."

Both rebuild pipelines are already merged on `main` (`#564` and `#565`), pin every input and output by SHA-256, and refuse any mismatch.

---

## 1. Stage `rl-code-v1-train.pool.jsonl`, `rl-code-v1-heldout.pool.jsonl`, and `out/v1/cc.jsonl` (`#564`)

**Source job request:** `teams/10-post-training/jobs/2026-11-18-rl-data-v1-pool.md` (CPU: 2 cores, 4 GB RAM, < 15 min, ~20 GB disk).

### Required raw inputs under `<RL_ROOT>`
- `deepmind/code_contests` @ `802411c3010cb00d1b05bad57ca77365a3c699d6` (39 train parquets, 7.5 GB) -> `<RL_ROOT>/code_contests/data/`
- `EleutherAI/hendrycks_math` @ `21a5633873b6a120296cce3e2df9d5550074f4a3` (7 train parquets, 3.0 MB) -> `<RL_ROOT>/hendrycks_math/`
- `HuggingFaceH4/MATH-500` `test.jsonl` (sha256 `35dc4108...`, overlap guard only) -> `<RL_ROOT>/math500/test.jsonl`
- Team 9 decontam tools + fingerprints v2 at commit `b470b4c0` (`set_sha256` `2826a3b883210c653979103c09ce1c79e40fc4f7034b54027f2836482370d22a`) -> `<RL_ROOT>/g9/teams/09-evaluation/decontam`
- Private firewall ID lists attached to `#564`:
  - `<RL_ROOT>/rl_heldout_v1_ids.txt` (255 IDs, sha256 `0e2c6f7835d98fdef72b76320604e020e3803ad650d88fcc64885843bdc09163`)
  - `<RL_ROOT>/sft_heldout_match_ids.txt` (82 IDs, sha256 `105103bebd0ba77f93d76536f7d8924e34edf16fd3121c60711199e82c0cf160`)

### Build command (`<POOL>` output root)
```bash
python teams/10-post-training/rl-data/rebuild_v1/rebuild_v1.py \
  --cc-dir <RL_ROOT>/code_contests/data \
  --math-dir <RL_ROOT>/hendrycks_math \
  --math500 <RL_ROOT>/math500/test.jsonl \
  --g9-tools <RL_ROOT>/g9/teams/09-evaluation/decontam \
  --rl-heldout-ids <RL_ROOT>/rl_heldout_v1_ids.txt \
  --sft-heldout-match-ids <RL_ROOT>/sft_heldout_match_ids.txt \
  --out <POOL>
```

### Expected staged files & SHA-256 pins (`rl-data/rebuild_v1/pins_v1.json`)
| Staged Path | Rows | Expected SHA-256 |
|---|---:|---|
| `<POOL>/out/v1/cc.jsonl` | 3,723 | `91ee99512f0411aea2de4ca5eaf10b87b2d8f785ca73747bf8deb45dd6ea9be0` |
| `<POOL>/pool/rl-code-v1-train.pool.jsonl` | 3,251 | `cd1aa76ef1216f6fc6fdcf63fc0b69c98fa6a5d58a510f28be9050fecbedcce1` |
| `<POOL>/pool/rl-code-v1-heldout.pool.jsonl` | 255 | `935857bb0246172aa0439445dd54ef9bbbe282ad2b5ea87ddd100429c9e31ae5` |

---

## 2. Stage `OCR-2` Firewalled Shards `0–3` (`#565`, subset `--shards 0:4` only)

**Source job request:** `teams/10-post-training/jobs/2026-11-17-ocr2-pack-v1-p1536.md`. Note: the dry run 2 SFT comparison job reads **only shards `0–3`** (`--shards 0:4`, ~2.4 GB output, ~15–25 min on 4–6 CPU cores — do not wait on all 70 shards).

### Required raw inputs under `<OCR_ROOT>`
- `nvidia/OpenCodeReasoning-2` @ `eadf535931451525f3e5621d0f960c240bc62fd9` (`train/python` shards `00000`–`00003`)
- `BAAI/TACO` @ `d593ed0a2becbbc952230bb89be09189bf1056dc`, `codeparrot/apps` @ `21e74ddf8de1a21436da12e3e653065c5213e9d1`, `deepmind/code_contests` @ `802411c3010cb00d1b05bad57ca77365a3c699d6`, `open-r1/codeforces` @ `fbe3f6e903ee854eec2e69e9d96d0306cde59baf` (test split only, protected-family index)
- Team 3 frozen `p1536` `tokenizer.json` (sha256 `e6b93a93a60520d7b1af2e9242485f443b5596a1e116b8f8798d83bbad25a64b`) -> `<OCR_ROOT>/tokenizer/p1536.json`
- Copy `teams/10-post-training/sft/manifests/ocr2_source_manifest_v1_p1536.json` -> `<OCR_ROOT>/source_manifest.json`
- Private firewall family list attached to `#565`: `<OCR_ROOT>/eval_firewall_families_v1.txt` (250 lines, sha256 `e8183f8ff236fc66064fcfef044ea5b9a4b6be330cdf67c0c5712315b3555cea`)

### Build commands (`<PACK>` output root)
```bash
# Step 1: build admission packs for shards 0..3 only
python teams/10-post-training/sft/run_ocr2.py \
  --manifest <OCR_ROOT>/source_manifest.json \
  --policy teams/10-post-training/sft/ocr2_policy.json \
  --shards 0:4 --workers 4 --out-dir <OCR_WORK>/run --mode admission

# Step 2: apply evaluation firewall to shards 0..3
for N in 00000 00001 00002 00003; do
  python teams/10-post-training/sft/eval_firewall.py apply \
    --pack <OCR_WORK>/run/shards/shard-${N}/pack/pack.jsonl \
    --sidecar <OCR_WORK>/run/shards/shard-${N}/join/joined.sidecar.jsonl \
    --families <OCR_ROOT>/eval_firewall_families_v1.txt \
    --families-sha256 e8183f8ff236fc66064fcfef044ea5b9a4b6be330cdf67c0c5712315b3555cea \
    --out <PACK>/shard-${N}/pack.firewalled.jsonl \
    --report <PACK>/shard-${N}/firewall_report.json
done
```

### Expected staged files & SHA-256 pins (`sft/results/ocr2_eval_firewall_v1.json`)
| Staged Path | Kept Rows | Bytes | Expected SHA-256 |
|---|---:|---:|---|
| `<PACK>/shard-00000/pack.firewalled.jsonl` | 7,687 | 608,603,588 | `227d97e37ede3b203b8f07a4d5e247c83ab1f1f202b1376ba755d435f2a25c06` |
| `<PACK>/shard-00001/pack.firewalled.jsonl` | 7,640 | 604,823,777 | `8a5c19ac8c6793ee701c983ff76a93b14d75073267d6ce8269d2ffe398aa312f` |
| `<PACK>/shard-00002/pack.firewalled.jsonl` | 7,607 | 594,146,724 | `0143f11095ac75a103f2c5d752baf758dcdcee7f275eaecc6e845dca086b698b` |
| `<PACK>/shard-00003/pack.firewalled.jsonl` | 7,681 | 605,885,024 | `c2b530f12a166cc28f35e45ddb30c36c3bf14f56d35f413ab02850dd5f738e2c` |

---

## 3. Pre-Launch Verification & Launch Order

Verify all 7 staged files before starting GPU time:
```bash
sha256sum -c <<'EOF'
91ee99512f0411aea2de4ca5eaf10b87b2d8f785ca73747bf8deb45dd6ea9be0  <POOL>/out/v1/cc.jsonl
cd1aa76ef1216f6fc6fdcf63fc0b69c98fa6a5d58a510f28be9050fecbedcce1  <POOL>/pool/rl-code-v1-train.pool.jsonl
935857bb0246172aa0439445dd54ef9bbbe282ad2b5ea87ddd100429c9e31ae5  <POOL>/pool/rl-code-v1-heldout.pool.jsonl
227d97e37ede3b203b8f07a4d5e247c83ab1f1f202b1376ba755d435f2a25c06  <PACK>/shard-00000/pack.firewalled.jsonl
8a5c19ac8c6793ee701c983ff76a93b14d75073267d6ce8269d2ffe398aa312f  <PACK>/shard-00001/pack.firewalled.jsonl
0143f11095ac75a103f2c5d752baf758dcdcee7f275eaecc6e845dca086b698b  <PACK>/shard-00002/pack.firewalled.jsonl
c2b530f12a166cc28f35e45ddb30c36c3bf14f56d35f413ab02850dd5f738e2c  <PACK>/shard-00003/pack.firewalled.jsonl
EOF
```

Then run in order against `dryrun2-1234` (step `1,221`, sha256 `8d1600b278a3d8e15c3d7af408a86e7c47acd987a899bf5eeee6b2c72192eb47`):
1. `teams/10-post-training/jobs/2026-11-26-g10-dryrun2-dt-vs-fft.md` (`125 min`, exports `keep_canary/dt/` and `keep_t7/g10-dr2-{full,lora,dt}/`, plus `out/forget/forget_*.json`).
2. `teams/10-post-training/jobs/2026-11-17-dt-then-rl-code.md` (`30 min`, consumes `keep_canary/dt/`, exports `keep_t7/g10-rl-final/`).
3. Team 9 watcher scores `/shared/ckpt/dryrun2-1234` (step `1,221`) + `keep_t7/{g10-dr2-full,g10-dr2-lora,g10-dr2-dt,g10-rl-final}` in `bfloat16`.
