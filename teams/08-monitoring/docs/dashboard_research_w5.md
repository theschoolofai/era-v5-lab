# Week 5 Training Dashboard Audit, Research Panel Table & BPB Loss Design

**Owner:** Team 08 (Monitoring & Records)  
**Deadline:** Wednesday 2 Dec 2026, 7:00 AM IST  
**Reference Run:** `dryrun2-1234` (`teams/05-architecture/results/dryrun2-1234/`, merged in `#869`: `1,221` steps, `1,222` JSONL lines, `wall_seconds = 4,788.17 s`, `val/bpb = 2.0561` at step 1,221)  
**Scope:** Covers Week 5 Items 1 (V4 Dashboard Audit), 2 (Online Research Panel Table & Missing V4 Panels), and 4 (Bits per Byte as Main Loss Line). Companion live dashboard & alarm replay log follow in the Item 3 PR.

---

## 1. Item 1 — Audit of ERA V4 Dashboard vs. Current V5 Dashboards

The ERA V4 dashboard provides per-chart zoom, fullscreen, CSV/PNG download, and `current / min / max / mean` legend stats across training, checkpoint, system, and MoE panels. The table below maps every V4 feature against our current V5 Grafana dashboards (`teams/08-monitoring/grafana/private_v1.json`, 33 panels; `public_v1.json`, 11 panels) and flags gaps to close before Wednesday 7:00 AM IST.

| V4 Feature / Chart | Current V5 Private (`private_v1.json`) | Current V5 Public (`public_v1.json`) | Gap / Action for Week 5 |
|---|---|---|---|
| Per-chart zoom, fullscreen, download, `current/min/max/mean` | Native Grafana zoom/inspect; add explicit `lastNotNull / min / max / mean` legend calcs on every trend panel | Same (read-only `editable: false`) | Add `calcs: ["lastNotNull", "min", "max", "mean"]` across all chart panels in Item 3 dashboard PR |
| Tokens per second | Present (`tokens_per_second`) | Present (`#779`, Training Pace) | Complete |
| Loss (total, NTP, MTP) | Present (`loss_ntp`, `loss_mtp`, `loss_total`) | Present (NTP + bucketed) | Promote **bits per byte (`train_bpb`, `val/bpb`)** to the primary loss panel (Item 4) |
| Learning rate | Present (`lr`, `muon_lr`) | Present (`Learning Rate Schedule`) | Complete |
| GPU memory allocated & peak reserved | Present (`gpu_alloc_gib`, `gpu_memory_used` Panel 26) | Held private (lab rule: no hardware specs) | Add `gpu_peak_reserved_gib` series if logged |
| Step time in ms | Present (`perf/step_ms`) | Present (`#779`, Training Pace) | Complete |
| Gradient norm | Present (`gradient_norm` Panel 17 + clipping Panel 19) | Held private | Complete |
| Checkpoint duration, size, loss, step | Partial (`run_events` checkpoint events in Panels 32–33, `#774`) | Planned (Open Infra Health) | Add checkpoint duration, size, and step-loss readout from `commits.jsonl` / `run_events` |
| System metrics (CPU %, freq, disk, per-GPU power/temp/util) | Partial (GPU temp/throttle Panel 22, GPU memory Panel 26, `node_health`) | Held private (lab rule: no hardware/machine specs) | Add CPU %/freq, disk free/used, GPU util/power panels on `private_v1.json` when host telemetry is streamed |
| Expert load distribution (per-expert over steps + dashed even-share line + `"even %"` readout) | Partial (`dead_experts_count` Panels 13–16, `router_max_vio` Panel 21, `expert_load_imbalance` Panel 27) | Present (`Mixture-of-Experts Load Balance`) | Add explicit **per-expert load over steps** panel with dashed `100 / N_experts` even-share threshold (`6.25%` for 16 routed experts) and `"even %"` stat |

---

## 2. Item 2 — Online Research Panel Table & Missing V4 Panels

Surveyed training monitoring setups across **Weights & Biases (W&B)**, **TensorBoard**, **Aim**, **MLflow**, **Grafana (Prometheus / DCGM)**, **OLMo 2 (AI2)**, **Megatron-LM**, and **DeepSeek-V3 / OLMoE** runs. Every panel below includes why it matters, the exact failure mode it catches, and explicitly covers all 9 gaps missing from ERA V4.

### 2.1 Core Training, Loss & Stability Panels

| Panel | Reference Ecosystem | Why It Matters | Which Failure It Catches | V5 Status |
|---|---|---|---|---|
| **Training & Held-Out Bits per Byte (Main Loss Line)** | OLMo 2, ERA V5 (`bpb_policy`) | Tokenizer- and script-invariant compression quality across variable-length tokens and multilingual UTF-8 bytes (Section 3) | Silent quality regression, bad LR schedule, or tokenizer/data-mix shifts hidden by per-token CE loss | `val/bpb` live; add per-step `train_bpb` as primary loss line |
| **Loss (NTP, MTP, Total) + Bucketed Mean** | W&B, TensorBoard, DeepSeek-V3 | Separates next-token vs. multi-token prediction head convergence and smooths micro-batch variance | MTP head collapse, objective weighting bugs, or sudden divergence | Live (`private_v1.json`, `public_v1.json`) |
| **Loss Spikes Counter & $7\sigma$ Envelope** *(missing in V4)* | OLMo 2 (`spike_score` $7\sigma$ / 1,000 steps), W&B | Tracks acute upward loss jumps without letting spiked steps pollute the trailing baseline | Corrupted/repeated n-gram batches, bad data shards, LR instability before full divergence | `alarms.py` live (`alarms_dryrun1.md`); add dedicated spike counter & envelope panel |
| **Gradient $L_2$ Norm & Clipping Rate** | OLMo 2, Megatron-LM, W&B | Gradient spikes typically precede loss spikes by several steps; clipping fraction shows if the optimizer is saturated | Exploding gradients, bad initialization, or LR too high for Muon/AdamW | Live (`private_v1.json` Panels 17 & 19) |
| **Gradient & Activation Outlier Counters** *(missing in V4)* | Megatron-LM, OLMo 2 (QK-norm/Z-loss), Aim | Tracks max hidden-state magnitude per block, `update_weight_ratio` ($\|\Delta W\|/\|W\|$), and non-finite/outlier counts | BF16/FP8 overflow precursors, attention logit growth, silent layer-wise numerical drift before `NaN` | `update_weight_ratio` live (Panel 24); add activation-outlier / non-finite counter panel |
| **Learning Rate Schedule (Muon & AdamW)** | W&B, TensorBoard, MLflow | Verifies WSD warmup (`5%`), stable plateau, and decay (`10%`) match the frozen config | Misconfigured schedule, broken resume step counter, or frozen LR after restart | Live (`private_v1.json`, `public_v1.json`) |

### 2.2 Data Composition, Position & Evaluation Panels *(Missing in V4)*

| Panel | Reference Ecosystem | Why It Matters | Which Failure It Catches | V5 Status |
|---|---|---|---|---|
| **Data Composition Table (Indic Share & Lane Shares in Tokens, Bytes, and Words)** *(missing in V4)* | OLMo 2, ERA V5 Team 01/02 (`shard_composition`) | Shows what the model is actually trained on (`pack_id × domain × stage × token_count × byte_count × word_count × drop_rate_pct`) | Accidental English-only skew, missing Indic packs, unexpected drop-rate blowup, or stale rehearsal mix | Live (`#732`, `#817`); extend `shard_composition` display with bytes/words & Indic/lane share summary |
| **Data Position (Tokens Seen / Shard Cursor / Epoch)** *(missing in V4)* | Megatron-LM, MLflow, Aim | Tracks exact position in the shuffled shard stream across restarts | Duplicate shard replay after SIGKILL restore, skipped data, or premature epoch wrap | Add panel from `train/scored_tokens` cumulative sum + checkpoint `commits.jsonl` step/shard cursor |
| **Evaluation Lines per Slice (15 Held-Out Slices + `eval_mini` Tiers)** *(missing in V4)* | OLMo 2, W&B, ERA V5 Team 09 (`eval_mini`) | Ties internal loss curves to per-language (`en`, `hi`, `te`, `ta`, `kn`, `ml`, `bn`, `mr`, `gu`, `pa`, `or`, `as`, `code`, `math`, `sci`) and benchmark progress | Weakest-language regression hidden by aggregate loss (e.g., Indic degradation while English improves) | `eval_mini` Panel 28 live; add 15-slice `val/slices/*/bpb` + 3-group (`english`, `indic_mean`, `code`) panel |

### 2.3 MoE Routing & Architecture Health Panels

| Panel | Reference Ecosystem | Why It Matters | Which Failure It Catches | V5 Status |
|---|---|---|---|---|
| **Router Balance per Layer & Expert Load Distribution** *(partially missing in V4)* | DeepSeek-V3, OLMoE, W&B | Per-layer `router_max_vio`, `expert_load_imbalance`, `dead_experts_count`, and per-expert share over steps with dashed even-share line (`100 / 16 = 6.25%`) + `"even %"` readout | Expert collapse (few experts taking all tokens), dead experts, or layer-specific routing instability | Aggregate Panels 13–16, 21, 27 live; add per-layer router balance + V4-style even-share curve |
| **Dynamic Router Bias & Dropped Token Rate** | DeepSeek-V3 (aux-loss-free balancing) | Tracks router bias drift and capacity-cap token drops | Oscillating router biases or silent token dropping under capacity limits | Track when `router_bias` / dropped-token telemetry is emitted |

### 2.4 Throughput, Idle Time, Restarts & Alarm State Panels *(Missing in V4)*

| Panel | Reference Ecosystem | Why It Matters | Which Failure It Catches | V5 Status |
|---|---|---|---|---|
| **Throughput & Step Time (`tokens_per_second`, `perf/step_ms`)** | TensorBoard, Megatron-LM, Grafana | Core compute efficiency rate required by Week 5 compute rule ("measure the rate before you scale") | Kernel regression, straggler ranks, thermal throttling, or comms slowdown | Live (`private_v1.json`, `public_v1.json` `#779`) |
| **Idle Time & Loader Wait (`loader_wait_time`, Pipeline/Comm Bubble)** *(missing in V4)* | Megatron-LM, Grafana/DCGM | Directly reports wasted GPU/CPU time and *why* it waited (dataloader starvation, checkpoint sync, NCCL stall) | Dataloader I/O bottlenecks, blocking checkpoint saves, or collective hangs | `loader_wait_time` Panel 18 live; add explicit Idle Time % / wait-reason breakdown |
| **Restart & Checkpoint Events (`run_events`)** *(missing in V4)* | Grafana, Xiaomi MiMo public dashboard, Team 07 | Shows restarts, checkpoint durations/sizes, and kill-drill recovery openly | Silent crash-loops, lost steps on restore, slow checkpoint flushes | Private Panels 32–33 live (`#774`); promote to public once live Dry Run 2 events are loaded |
| **Alarms & Live State Table (`alarms.py` + `eval_lag_checks`)** *(missing in V4)* | Grafana Alerting, W&B Alerts, Team 08/09 | Single glance at every alarm's current state (`OK / WARN / PAGE / STOP`), last fired step, and eval-watcher lag (`eval_lag.py`) | Missed pages, stalled `eval_watcher.py` (`> 1,200 s` lag), or unacknowledged `non_finite` / `spike_score` events | `eval_lag` Panels 29–31 live (`#769`, `#822`); add unified Alarm State summary table |
| **System & GPU Telemetry (Memory, Temp, Power, CPU, Disk)** | Grafana + Prometheus / DCGM | Operational hardware health on `private_v1.json` (never exposed on `public_v1.json`) | OOM risk, thermal throttling, ECC/XID errors, disk exhaustion | GPU memory/temp/throttle & `node_health` live; keep strictly private |

---

## 3. Item 4 — Why Bits per Byte (BPB) Must Be the Main Loss Line

### 3.1 Definition

For any batch or held-out slice with total negative log-likelihood $\text{NLL}_{\text{nats}} = \sum_{t=1}^{T} (-\ln p(x_t \mid x_{<t}))$ over $T$ scored positions representing $B$ raw UTF-8 bytes of text:

$$\text{BPB} = \frac{\text{NLL}_{\text{nats}}}{B \cdot \ln 2} = \frac{\overline{\text{CE}}_{\text{nats/pos}} \cdot T}{B \cdot \ln 2} = \frac{\overline{\text{CE}}_{\text{nats/pos}}}{\ln 2} \cdot \left(\frac{T}{B}\right)$$

where $\overline{\text{CE}}_{\text{nats/pos}} = \text{NLL}_{\text{nats}} / T$ is the standard cross-entropy **loss per position**, and $B / T$ is the average **UTF-8 bytes per position**.

### 3.2 Why Loss per Position Is Not Enough When Positions Differ in Length

Loss per position ($\overline{\text{CE}}_{\text{nats/pos}}$) only measures uncertainty **per emitted unit**, not per unit of underlying text. Whenever two slices, languages, or tokenizers encode the same text into different numbers of positions ($T_1 \ne T_2$ for the same $B$ bytes):

1. **Longer positions look artificially worse on per-position loss:** Packing more bytes into a single token (higher $B / T$) forces each position to predict more information at once, raising $\overline{\text{CE}}_{\text{nats/pos}}$ even when total compression ($\text{NLL}_{\text{nats}} / B$) is *better*.
2. **Shorter positions look artificially better on per-position loss:** Splitting text into many short tokens (lower $B / T$, e.g., code punctuation/indentation or byte-fallback tokens) lowers $\overline{\text{CE}}_{\text{nats/pos}}$ because each position predicts fewer bytes, hiding poor compression.
3. **Multilingual Indic vs. English UTF-8 bias:** Indic scripts (`hi`, `te`, `ta`, `kn`, `ml`, `bn`, `mr`, `gu`, `pa`, `or`, `as`) use 3 UTF-8 bytes per Unicode code point vs. 1 byte for ASCII English/code. Comparing raw nats/token across languages or across tokenizer revisions (e.g., dense BPE vs. `frozen-p1536` / KE2 variable-length units) is invalid without normalizing by UTF-8 bytes.

### 3.3 Empirical Proof on Real Dry Run 2 (`dryrun2-1234`, `#869`, Step 1,221)

Every number below is computed directly from `teams/05-architecture/results/dryrun2-1234/metrics.jsonl` (step `1221`) using the reproducible command below:

```bash
python3 -c '
import json, math
from pathlib import Path
row = [json.loads(l) for l in Path("teams/05-architecture/results/dryrun2-1234/metrics.jsonl").read_text().splitlines() if l.strip()][-1]
for s in ["en", "te", "ta", "hi", "code", "math"]:
    nll = row[f"val/slices/{s}/nll_nats"]
    tok = row[f"val/slices/{s}/scored_tokens"]
    byt = row[f"val/slices/{s}/utf8_bytes"]
    bpb = row[f"val/slices/{s}/bpb"]
    print(f"{s:4s} | bytes/tok={byt/tok:5.2f} | ce_per_pos={nll/tok:6.3f} nats | bpb={bpb:.4f}")
'
```

| Slice (`dryrun2-1234`, step 1,221) | UTF-8 Bytes / Position ($B/T$) | Loss per Position ($\overline{\text{CE}}$, nats) | True Compression (`val/bpb`) | Why Per-Position Loss Misleads |
|---|---:|---:|---:|---|
| `en` (English) | `4.67` | `5.729` | **`1.7687`** | Baseline 1-byte ASCII tokens |
| `ta` (Tamil) | `10.53` | `13.022` | **`1.7834`** | Per-position loss is **2.27x higher** than `en`, yet true BPB is almost identical (`+0.015` bpb)! |
| `te` (Telugu) | `8.98` | `11.766` | **`1.8892`** | Per-position loss is **2.05x higher** than `en`, yet BPB is within `0.12` bpb |
| `hi` (Hindi) | `8.68` | `11.414` | **`1.8982`** | Same 3-byte Devanagari UTF-8 effect |
| `math` (Math) | `3.63` | `6.249` | **`2.4825`** | Looks nearly as good as `en` on per-position loss (`6.25` vs `5.73`), but is **`+0.71` bpb worse** |
| `code` (Code) | `3.88` | `9.172` | **`3.4073`** | Looks **22% better** than `te` on per-position loss (`9.17` vs `11.77`), yet is actually **1.80x worse** in true BPB (`3.41` vs `1.89`)! |

**Dashboard decision:**
- Make **Bits per Byte** (`train_bpb = (train/ce_loss * train/scored_tokens) / (train/utf8_bytes * ln(2))` alongside `val/bpb`, `val/three_group_bpb`, and the 15 per-slice `val/slices/*/bpb` lines) the **primary loss panel** on both `private_v1.json` and `public_v1.json`.
- Keep raw per-position `loss_ntp` / `loss_mtp` as secondary diagnostic panels for optimizer stability (`spike_score` $7\sigma$ alarm).
