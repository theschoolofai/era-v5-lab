# Per-batch composition, data position and the native Indic share alarm (Week 5)

Capstone Lab 5, Team 08 tasks:

1. Log per-batch composition (Indic share, lane shares) and the data position next to loss.
2. Alarm if native Indic share leaves 8% plus or minus a tolerance we propose.

Evidence: [`alarms/replay_dryrun2_indic_share.log`](../alarms/replay_dryrun2_indic_share.log) (the replay below), private
Grafana panels 35 to 37, and the tests listed at the end.

## 1. What is logged (`metrics_logger/composition.py`)

| Metric | Meaning |
|---|---|
| `indic_share` | Native-script Indic share of the batch's **tokens**. Team 02's rule ([`indic_share_v1.md`](../../02-data-b/mix/indic_share_v1.md)): native Indic is a fixed 8% of every batch. Translated packs (`ind-<lang>-sangraha-s`, #212) and romanised Indic documents are not native. |
| `lane_share_tokens`, `lane_share_bytes`, `lane_share_words` | {lane: share} of the batch by tokens, UTF-8 bytes and words; each adds up to 1. Words only when every document gives a word count. |
| `data_tokens_seen`, `data_bytes_seen`, `data_words_seen`, `data_docs_seen` | Running totals of what the run has trained on: the data position. |
| `data_epoch` | `data_tokens_seen` / corpus tokens, when the caller gives the corpus size. |

Lanes come from Team 01's pack ids: `en-*` english, `code-*` code, `math-*` math, `sci-*` science, `ind-<lang>-*` indic
(native), `ind-<lang>-sangraha-s` or a document marked translated → `indic_translated`, a document marked romanised →
`indic_romanised`, anything else `other`.

In the training loop, once per optimizer step, with the documents (or document pieces) packed into the batch:

```python
from composition import DataPosition, batch_composition, composition_metrics
position = DataPosition(corpus_tokens=CORPUS_TOKENS)           # save position.state_dict() with each checkpoint
comp = batch_composition(docs)  # docs: [{"pack": "ind-hi-fw2", "tokens": 812, "bytes": 2203, "words": 390}, ...]
writer.write(step, loss_ntp=..., **composition_metrics(comp), **position.update(comp))
```

`MetricsWriter` now accepts these names. The ClickHouse loader stores the dicts as `lane_share_tokens.<lane>` rows.

## 2. The alarm: `indic_share` (`alarms/alarms.py` rule 8)

**Rule.** Page once when the mean `indic_share` of the last **50** logged batches leaves **8% ± 1 point** (7% to 9%),
and re-arm when the mean is back inside. Rows without `indic_share` are ignored, so a run that does not log composition
never fires it. Its rolling window and latch are saved in `AlarmMonitor.state_dict()`, so a restored run continues it.

```bash
python -I teams/08-monitoring/alarms/alarms.py --jsonl metrics.jsonl                    # defaults: 0.08, 0.01, 50
python -I teams/08-monitoring/alarms/alarms.py --jsonl metrics.jsonl --indic-target 0.08 --indic-tolerance 0.01 --indic-window 50
```

**Why a rolling mean, not each batch.** The 8% is held per batch, but a batch is made of whole documents (or pieces of
them). At 16,384 positions per step (dry run 2: 8 sequences of 2,048), 8% is about 1,311 tokens, so one document more or
less moves a single batch's share by several points. An alarm on each batch would page all the time; the mean of 50
batches keeps a real drift visible and lets the document-sized wobble cancel out.

**Why ±1 point over 50 batches (our proposal).** If one batch's share varies by σ around 8% (document rounding), the
50-batch mean varies by σ/√50. With σ ≈ 2.1 points (about one 350-token document swing in 16,384 tokens), the mean's
σ is 0.3 points, so ±1 point is about 3σ: no false pages from rounding, while a real fault shows within a few dozen
batches. A lost Indic lane (share 0) crosses 7% after **7** batches of a full window (43 × 8% / 50 = 6.88%); a lane at
12% crosses 9% after 13 batches (9.04%) (`test_indic_share.py`).

**What would change it.** σ above is an assumption: no run has logged per-batch composition yet. Once a run does
(dry run 3 or the first 1,000 batches of the main run), set the tolerance to 3 × (standard deviation of the per-batch
share) / √50 from that log, and keep the window at 50 unless the batch size changes a lot.

**Severity `page`.** A wrong mix wastes the compute spent on it and is not fixed by waiting, so the lead should look
the same day.

## 3. Dry run 2: replay (finding)

dryrun2-1234 (#869) did not log composition. Its record says: *"Training text of this run was one English web shard of
25M tokens, not the sample-v0 mix"*. So every batch is 100% english and the native Indic share is **0%**, from the
record, not measured per batch. [`metrics_logger/dryrun2_composition.py`](../metrics_logger/dryrun2_composition.py) adds
that composition and the data position (running sums of `train/input_positions` and `train/utf8_bytes`) to the run's
own `metrics.jsonl`; the run's fields are unchanged.

Replay ([`alarms/replay_dryrun2_indic_share.log`](../alarms/replay_dryrun2_indic_share.log), input sha256 `2b764501…`):

| Step | Rule | Severity | Detail |
|---:|---|---|---|
| 50 | `indic_share` | page | native Indic share 0.00% over the last 50 batches is outside 8% +/- 1 points |
| 226 | `throughput_drop` | warn | tokens_per_second 38.8% below baseline for 100 steps (already in the run's own alarms) |
| 1184 | `spike_score` | page | gradient_norm 8.1 sigma above the trailing mean (already in the run's own alarms) |

`indic_share` fires **once**, at step 50, the first step with a full 50-batch window, and stays latched: the share never
returns to the band. **Finding:** dry run 2 is not a test of the 8% Indic rule; its training text had no Indic at all.
A run meant to follow the mix would have paged at step 50.

Data position at the last step (1,221): 20,004,864 tokens and 39,818,093 bytes seen, 0.80 of the 25M-token shard
(`data_epoch`). Training bits per byte at that step: 1.667 (`train/ce_loss × train/scored_tokens / (train/utf8_bytes × ln 2)`).

## 4. Panels (`grafana/private_v1.json`, row "Data composition and position")

| Panel | Shows | Dry run 2 (checked on ClickHouse) |
|---|---|---|
| 35 Native Indic share per batch | per-batch `indic_share` and its 50-batch mean, the alarm's band 7% to 9% in green | 1,221 points, 0% throughout |
| 36 Lane shares per batch, by tokens | one line per lane | english 100% |
| 37 Data position next to the loss | training bits per byte (left) and `data_tokens_seen` (right) | 16,384 → 20,004,864 tokens; bits per byte 3.17 → 1.667 |

Each legend shows the current, min, max and mean value (as on the V4 dashboard).

## 5. What this does not cover

- **Real per-batch composition.** The trainer (Team 05's `train_week2.py`) does not pass the batch's documents to
  `batch_composition()`. Until it does, composition exists only as derived from a run record, as here.
- **Words** for dry run 2: the record has no text, so `lane_share_words` and `data_words_seen` are left out, not guessed.
- **Data position inside a shard** (shard id, row): the record has no per-step shard or row; the position is in
  tokens and bytes.

## 6. Reproduce

```bash
docker start era-v5-clickhouse        # clickhouse/README.md section 1
python -I teams/08-monitoring/metrics_logger/dryrun2_composition.py teams/05-architecture/results/dryrun2-1234/metrics.jsonl --out ./out/dryrun2-1234/metrics.jsonl
python -I teams/08-monitoring/alarms/alarms.py --jsonl ./out/dryrun2-1234/metrics.jsonl
python -I teams/08-monitoring/clickhouse/load_jsonl.py --run-id dryrun2-1234 ./out/dryrun2-1234/metrics.jsonl   # then panels 35-37
PYTHONPATH=teams/08-monitoring pytest teams/08-monitoring/metrics_logger/test_composition.py \
  teams/08-monitoring/alarms/tests/test_indic_share.py teams/08-monitoring/grafana/test_private_composition_panels.py -q
```
