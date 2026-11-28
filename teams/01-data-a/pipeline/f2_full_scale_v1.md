# F2 at full scale (B7), v1

Sourav Dhar · GitHub: sourav-dhar · Team 1 (Data A)

Brief task 7 ("Run F2 (benchmark decontamination) at full scale"), with the rules for every team: "Measure the rate
before you scale" and "Run the benchmark overlap check at the same pass as tokenizing". This note gives the measured
rates, where the time goes, what a full-scale run needs (workers, RAM, time), the command, and what Aneesha's pass
design (D2, `passes_design_v1.md` in #898) can take from it. F2 here is `spec_v1/run_f2.py` / `pipeline/f2_pool.py`
with G9's fingerprint set v2 (`set_sha256 2826a3b8…`), unchanged.

Logs: [`jobs/logs/2026-11-28-b7-f2-rates-mac/`](../jobs/logs/2026-11-28-b7-f2-rates-mac/). Tools:
[`tools/f2_rates.py`](../tools/f2_rates.py), [`tools/f2_breakdown.py`](../tools/f2_breakdown.py).

## 1. Measured rates

Input: all 86 parts of the 38 sample packs (tokenizer sample v0, raw parts: 1,444,766 documents, 6.0 GB of text,
1,262,827,283 p1536 tokens). Machines:
- **Mac:** Apple M6 (2 Super + 4 Performance + 6 Efficiency cores), 32 GB, macOS (spawn start method: each worker
  loads its own copy of the set).
- **Pod:** the 19 Nov rehearsal (Runpod, 32 vCPU, 251 GB RAM, Linux, fork; patilvijay23/era-v5-lab#62), on the
  cleaned and deduplicated parts.

**One worker, alone** (`f2_pool.py --workers 1`, one part each):

| Part | Docs | Text | p1536 tokens | Seconds | MB/s | Tokens/s per core | Peak RSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| en-dclm Part_1 | 46,245 | 256 MB | 55,982,711 | 150 | 1.71 | 373,467 | 1.37 GB |
| code-java Part_1 | 62,834 | 256 MB | 60,956,484 | 94 | 2.71 | 645,042 | 1.37 GB |
| math-finemath Part_1 | 29,122 | 149 MB | 42,205,637 | 88 | 1.68 | 477,439 | 1.40 GB |

**Many workers** (whole sample):

| Run | Workers | Wall | Worker-seconds | Tokens/s (run) | Tokens/s per worker | Peak RSS |
|---|---:|---:|---:|---:|---:|---|
| Mac, 28 Nov | 8 (spawn) | 917 s | 7,259 (4,441 CPU-s) | 1,377,580 | 172,197 | 6,591 MiB (6.9 GB) for all F2 processes at the highest 15 s sample; 1.07 GB largest process (`time -l`) |
| Pod, 19 Nov | 30 (fork) | train pool 687.7 s (9.9 s of it loading the set); held-out pool 28.4 s | 10,802 train + 360 held-out | about 1.65 M (1,132,509,915 train shard tokens ÷ 687.7 s) | about 105,000 (train shard tokens ÷ train worker-seconds) | about 1.3 GB per worker in RSS (largest 1,315 MiB) |

The pod's rates use the tokens of the train shards, which leave out F2's drops and the 7,575 documents left out of the
shards, so F2's real rate there is a little higher; its input was cleaned and deduplicated text, the Mac's was raw.

Per lane on the Mac run (`f2_rates.py`, worker-seconds from each part's `.f2.json`):

| Lane | Parts | Docs | Text MB | p1536 tokens | Worker s | MB/s per worker | Tokens/s per worker | Dropped |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cadj | 6 | 133,116 | 420 | 109,214,051 | 609 | 0.69 | 179,245 | 142 |
| code | 18 | 485,928 | 2,100 | 554,992,122 | 2,533 | 0.83 | 219,113 | 1,056 |
| en | 12 | 426,508 | 1,380 | 289,472,235 | 2,299 | 0.60 | 125,918 | 214 |
| ind | 44 | 345,890 | 1,620 | 186,807,125 | 850 | 1.91 | 219,721 | 360 |
| math | 4 | 47,250 | 300 | 80,767,355 | 611 | 0.49 | 132,167 | 342 |
| sci | 2 | 6,074 | 180 | 41,574,395 | 356 | 0.51 | 116,651 | 14 |
| **all** | 86 | 1,444,766 | 6,000 | 1,262,827,283 | 7,259 | 0.83 | 173,972 | 2,128 |

What these say:
- **Workers share badly.** The same parts took 3.2 to 4.5 times longer inside the 8-worker run than alone (en-dclm
  473 s against 150 s, code-java 426 s against 94 s, math-finemath 353 s against 88 s), so on the Mac 8 workers gave
  1.8 to 2.5 times one worker, not 8. Part of it is waiting for a core: the 8 workers used 4,441 CPU-seconds
  (user + sys, `time -l`) in 7,259 worker-seconds, about 61% of the time on a CPU (4.8 cores busy on average), with
  9.5 M involuntary context switches against 68k to 92k in each one-worker run. Why the processes waited (the Mac's
  three kinds of cores, memory, the scheduler) is not measured. The pod's workers did about 0.105M each.
- **The largest parts set the wall.** On the pod the train pool's 30 workers averaged 360 s of work (10,802 s ÷ 30)
  in a 688 s pool. There were only 48 train parts for 30 workers, and four of them each took over 600 s (en-dclm 677 s,
  en-nemotroncc 662 s, en-fineweb-edu 660 s, en-nemotroncc-synth 612 s). That is consistent with workers waiting with
  nothing to do near the end; the logs do not time it. On the Mac (8 workers, 86 parts) the work was even
  (7,259 s ÷ 8 = 907 s against 917 s wall).
- **Same output.** The single-worker runs dropped the same documents as the 8-worker run (34, 14 and 260).

## 2. Where the time goes

`f2_breakdown.py` on the same three parts, one process (read, check and write timed separately; the profile is of
code-java):

| Part | Set load | Read | Check | Write | Read + write, share of read + check + write |
|---|---:|---:|---:|---:|---:|
| en-dclm Part_1 (256 MB) | 1.8 s | 0.22 s | 136.9 s (1.87 MB/s) | 0.45 s | 0.49% |
| code-java Part_1 (256 MB) | 1.8 s | 0.20 s | 94.0 s (2.72 MB/s) | 0.36 s | 0.59% |
| math-finemath Part_1 (149 MB) | 2.0 s | 0.26 s | 93.4 s (1.59 MB/s) | 0.30 s | 0.60% |

Profile of the code-java check (`--profile`; cProfile makes it about 2.4 times slower, so read the shares): of
225.9 s, the normaliser `words_with_offsets` 77.6 s (34%), blake2b `digest` 27.8 s + dict `get` 19.5 s +
`int.from_bytes` 8.6 s (25%) for 170,724,917 runs, and `Fingerprints.check`'s own loop 72.9 s (32%).
(`breakdown_3parts.txt` in the logs.)

So **reading and writing the parts is under 1% of F2's time here; the check is the rest.** This was one process on
the Mac with the part in the page cache (256 MB read in about 0.2 s); it is not measured on the pod's disks or with 30
workers reading at once. In the profile the check splits
into the normaliser (about a third), the blake2b hash and dict lookup of every 13-word / 20-token run (about a
quarter) and the loop around them (about a third). The loop runs in Python; the hash, the dict lookup and the
regular expressions are C built-ins called from it once per run or word.

## 3. Full-scale plan

**Time.** F2 scales with the tokens it checks. From the measured rates:

| Setup | Rate | 100 B tokens | 1 T tokens |
|---|---:|---:|---:|
| one Linux box like the pod, 30 workers, every worker busy to the end (30 × 105k; best case, not measured) | about 3.1 M tokens/s | about 9 h | about 3.7 days |
| the same box with parts as in the rehearsal (train pool, measured) | about 1.65 M tokens/s | about 17 h | about 7.0 days |
| Sourav's Mac, 8 workers | 1.38 M tokens/s (measured) | about 20 h | about 8.4 days |
| N boxes like the pod, parts spread over them | N × 3.1 M tokens/s | 9 h ÷ N | 3.7 days ÷ N |

The first and last rows are best cases: they assume each worker keeps the pod's measured 105k tokens/s while every
worker is busy, which was not the case in the measured run (the Mac's workers slowed 3 to 4.5 times under load). The corpus-v1 token count (Team 1's task once TSAI's production run returns) gives the real size.
Teams have not seen corpus-v1, so this note does not guess it.

**Compute.** 100 B tokens at about 105k tokens/s per worker is about 265 worker-hours (vCPU-hours on a box like the
pod). F2 needs no GPU.

**RAM.** One worker alone peaked at 1.37 to 1.40 GB (`time -l`, spawn). With 8 spawn workers on the Mac the highest
15 s sample of all F2 processes was 6,591 MiB (6.9 GB), and the largest process 1.07 GB. With fork (Linux),
f2_pool.py's design is that the workers share the loaded set copy-on-write; the rehearsal recorded about 1.3 GB RSS
per worker (largest 1,315 MiB), but RSS counts shared pages in every process and no PSS / USS was recorded, so how
much the 30 workers really shared is not measured (reference counting in CPython can unshare pages). When it does not
fit: fewer workers, since each worker is independent.

**Parts.** The stage ends when its largest part ends, so with N workers there should be many more parts than N and
no part should hold more than about 1/N of the work. In the rehearsal the train pool had 48 parts for 30 workers and
four parts of over 600 s each, in a 688 s pool. f2_pool.py already sends the largest parts first, which helps only
when there are enough parts and none is much larger than the work per worker.

**Command** (per split; `--workers` defaults to the CPUs on Linux):

```bash
python -I teams/01-data-a/pipeline/f2_pool.py --inputs <deduped>/<split> --out <final>/<split> --workers 30
```

- Restart: a part whose `.f2.json` names the same input sha256 and set sha256 is skipped, so a stopped run resumes
  where it stopped (f2_pool.py's docstring; rule 3 of the briefing).
- Several boxes: give each box its own subset of parts as `--inputs` (files are allowed), with the same `--out`
  layout; the parts' `.f2.json` files are what the ledger reads. `f2_summary.json` is written per run, so with several
  boxes there is one per box, to be added up.
- Check: the same `set_sha256` in every `.f2.json` and `kept + dropped + errors = rows` per part (run_f2.py checks
  both).

## 4. F2 in the same pass as tokenizing (C4 in D2)

D2 (`passes_design_v1.md`, #898) lists **C4: the shard writer checks each batch against G9's fingerprint set before
it tokenizes, so no final parts are written** ("Proposal; for F2's owners"). From §2:
- **What it saves:** F2's read and write of every part (under 1% of F2's time in §2, one process with the part in
  the page cache; not measured with many workers or on the pod's disks) and one full copy of the corpus text on disk
  (the final parts), plus the shard writer's read of that copy.
- **What it does not save:** the check itself, more than 99% of F2's time in §2. The check in the shard pass would
  be the same code on the same documents, so it should cost about the same there (not measured).
- **What it costs:** each shard-writer worker needs the set (shared with fork, 1.1 GB each with spawn), and the
  ledger, which now counts F2's drops from the `.f2.json` files, would need them from the shard pass instead.
- **What it changes for others:** the shard writer (B5's code) and the ledger. So C4 is worth it for disk and one
  pass over the text, not for time; it is not built in this note, and would need the shard writer's and the ledger's
  owners.

## 5. What would cut F2's time

- **More boxes** (§3): the check is independent per document, so it splits by part with no change to results.
- **A faster check, same results:** the Python normaliser and per-run hashing are the cost. A compiled version of the
  same check (same normaliser, same blake2b keys, same set) could be several times faster; it would have to give the
  same flagged doc_ids and items on the 38 packs and keep `set_sha256`. That is G9's code (`teams/09-evaluation/
  decontam/fpset.py`), so this note only measures it.
- **Check each document once:** F2 runs after dedup, so repeats of a source in the mix are not checked again.

## 6. For D2 (Aneesha's pass diagram)

- F2's per-part rates and RAM above, per lane and per worker count; the set loads in about 2 s when the files are in
  the page cache (about 20 s cold, run_f2.py's note).
- C4's saving, measured: under 1% of F2's time plus one copy of the text (§4).
- The largest-part effect (§1), which applies to every per-part stage of the pipeline.

## 7. Not measured

- Linux rates at more than 30 workers, and on boxes other than the rehearsal pod.
- The corpus-v1 size (Team 1's token count, once TSAI's production run returns).
- A compiled check (§5).
