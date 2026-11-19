# G10 job request (DRAFT, not sent): keep one SFT arm's weights for Team 9

Same job as #587 with two extra flags. It runs the A2 and A4 arms as before and, for the one arm named by `--keep-arm`, also
writes its final plain weights through Team 7's Checkpointer, so Team 9's `run_lab_ckpt.py --run-dir <kept dir>/g10-sft-a2` can read
and export them (RL model scores, forgetting check).

```bash
python capstone/sft_job_v1.py --g5-root <lab checkout> --run-folder <dir with manifest.json/checkpoint.pt/summary.json> \
    --tokenizer tokenizer.json --byte-table raw_table_P32.npz --heldout H.jsonl --heldout-sources S.jsonl \
    --packs <shard-00000>/pack.firewalled.jsonl ... --rl-tasks cc.jsonl --rl-ids capstone/probe_rl_easy_ids.txt \
    --device cuda --out out/ \
    --keep-weights-dir kept/ --keep-arm a2
```

What leaves the job: one run folder `kept/g10-sft-a2/` (latest.json, commits.jsonl, one step folder with the weights and Team 7's
MANIFEST.json), plus its path, manifest sha256 and step in `summary.json`. Size is the weights only, no optimizer state: parameter
count times bytes per parameter. Estimate, not measured: Team 5's dry run 1 checkpoint is about 2.2 GB with AdamW state (weights plus
two moments, fp32 = 12 bytes per parameter), so about 183 million parameters and about 0.73 GB of fp32 weights (183e6 x 4 bytes).
What still never leaves: the built rows, the held-out answers, the generations and the other arm's weights, all deleted as in #587.
Nothing else changes: without the two flags the outputs are byte-identical to #587.
