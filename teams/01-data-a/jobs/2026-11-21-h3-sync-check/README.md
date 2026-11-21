# H3 sync check on CUDA (21 Nov 2026)

Week-4 To do: run `h3.py` with `"sync_debug": true` on a CUDA GPU. The 19 Nov rehearsal (#599) ran with `sync_debug: false`.
This is our own check on a cloud VM, not a TSAI job. `h3.py` is not changed, and the config is the rehearsal's
(`jobs/2026-11-19-first-training/h3.json`) with `device: cuda` and `sync_debug: true`. Report-only: nothing is removed.

```text
Owner:    Smita Sasindran
Code:     teams/01-data-a/dedup/h3.py (with h3_align.py, h3_signals.py), commit <fill in: git rev-parse HEAD on the VM>
Config:   teams/01-data-a/jobs/2026-11-21-h3-sync-check/h3.json
Inputs:   the same 7 parts as the rehearsal, from week-2-cleaned (TSAI's 5 Nov cleaning of sample v0, not the rehearsal's spec v1.1 cleaning; see "Inputs"), under out/h3_sync_check/clean/{train,heldout}/<pack>/part-NNNNN.parquet
Model:    sentence-transformers/LaBSE revision 836121a0533e5664b21c7aacc5d22951f2b8b25b in ../models/LaBSE
Hardware: <fill in: GPU, driver, torch and CUDA versions>
```

## What it checks

With `sync_debug` on CUDA, `h3.py` calls `torch.cuda.set_sync_debug_mode("warn")` after the read and encode stages and
turns it off at the end. Torch then warns at every host-device sync in the url, retrieve, verify_read and verify stages.
That includes the encoder's forward passes on the sentences of the verified pairs (`encode()` runs inside the verify
stage). The encoding of the document heads comes before the switch and is not covered. `h3_design_v1.md` ("Checks")
expects no warnings inside a loop; the README expects one host copy per stage result.

## Inputs (the 7 parts the rehearsal read, from week-2-cleaned)

```text
train/en-fineweb-edu/part-00000.parquet, part-00001.parquet
train/ind-hi-fw2/part-00000.parquet
train/ind-sa-fw2/part-00000.parquet
heldout/en-fineweb-edu/part-00000.parquet
heldout/ind-hi-fw2/part-00000.parquet
heldout/ind-sa-fw2/part-00000.parquet
```

## Run

From the repository root, with the Python 3.12 environment of `dedup/requirements_h3.txt` and the pinned LaBSE staged:

```sh
rm -rf out/h3_sync_check/h3 out/h3_sync_check/h3_cache
python -I -c "import torch; assert torch.cuda.is_available(), 'no CUDA GPU'; print('CUDA', torch.version.cuda, torch.cuda.get_device_name(0))"
python -I -W always teams/01-data-a/dedup/h3.py --config teams/01-data-a/jobs/2026-11-21-h3-sync-check/h3.json 2>&1 | tee out/h3_sync_check/h3_sync_check.log
```

`-W always` is needed because Python shows a warning from one source line only once by default, which would hide a sync
inside a loop. `-I` ignores `PYTHONWARNINGS`, so the flag goes on the command line.

Optional scaling check: run again with `"pair_batch": 256`, `out` and `cache` set to other folders under `out/`, and compare
the warning counts. A count that grows with the number of batches is a sync inside a loop.

## Reading the log

Warnings go to stderr, which the run command's `2>&1 | tee` puts in the log. Each starts with the Python file and line
that triggered it, then `UserWarning: called a synchronizing CUDA operation`.

```sh
grep -c "synchronizing CUDA operation" out/h3_sync_check/h3_sync_check.log
grep "synchronizing CUDA operation" out/h3_sync_check/h3_sync_check.log | sed 's/: UserWarning.*//' | sort | uniq -c | sort -rn
```

Expected from reading the code (to be confirmed by the log): the stage results copied to the host. In `h3_align.py:50`
`cross_topk` copies 5 tensors per language pair (15 for the 3 pairs), and `h3.py` copies 2 at the end of verify
(`aligned`, `mean_cos`). The URL stage copies nothing here, since it has 0 pairs. Anything else is a finding:
- a line in `h3.py` or `h3_align.py` with a count that grows with the number of batches, pairs or documents: a sync inside
  a loop (fail);
- lines in `torch` or `transformers` files, with about one warning per encoder batch: a sync inside the model's forward
  pass, not in our code (note it, see the next section).

## Result

<fill in after the run: number of warnings, the lines they come from, pass or fail>

Also check `h3_summary.json`: `device` cuda, `precision` fp16, `sync_debug` true, `model.safetensors` `77d8e1f2…`, and the
counts of #599 for comparison only (91,559 documents encoded, 9,343 verified, 0 qualifying; 205.7 s there). The inputs are
not the rehearsal's: only the two train/en-fineweb-edu parts are byte-identical to its cleaned parts (same sha256). The
heldout parts are the uncleaned raw parts (their sha256 equals the rehearsal's cleaner input), and train/ind-hi-fw2 has
14,125 rows against 13,801 there. Totals: en 72,106 rows (72,100), hi 14,257 (13,932), sa 5,722 (5,721), so the counts
will be close but not equal.

## Not covered

- The encoding of the document heads, which comes before the switch.
- The URL-pair path with pairs in it: the 3 packs give 34 URL groups and 0 pairs across the configured language pairs.
- The `max_verify` cut-off: 9,343 pairs are verified, under 10,000.
- The or–en pair of E5c's scope.

## If the log shows warnings

- In our loops (`h3.py`, `h3_align.py`): fix in code (keep values as tensors, copy to the host once after the loop), then
  rerun the 71 H3 tests, this check, and compare the counts and `h3_matches.csv` with the first run. Iterate on a small
  run first (`"max_docs_per_pack": 500` and a new cache folder).
- In `torch` or `transformers` code, in the model's forward pass: report it with the count and the lines. It is not ours to
  fix here; whether it costs time shows in the encode and verify rates of `h3_summary.json`.
