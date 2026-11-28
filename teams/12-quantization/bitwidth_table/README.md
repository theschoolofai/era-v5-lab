# Per bit-width table: size, memory, speed and quality (Lab 5 tasks 1 and 7)

The Lab 5 brief (28 Nov) asks for one table, due Wed 2 Dec 7:00 AM IST: for 16, 8, 6, 5 and 4 bits, the file size, memory, speed and quality loss on our 20 items and 100 prompts, on 16 GB and 32 GB Macs. The rows come from several people on several Macs, so everyone writes them with the same script, and one script builds the table.

| Part | Who | Where it comes from |
|---|---|---|
| Quality loss against bf16 | dry run 2 job (TSAI runs it) | `scores.json` and `prompts/summary.json` from `jobs/2026-11-27-dryrun2-quantize-eval.md` |
| 16 GB Mac rows | s9k96 (MacBook Air M5) | `measure_mac.py` |
| 32 GB Mac rows | sourav-dhar (M6) | `measure_mac.py` |
| 64 GB Mac rows, labelled 64 GB | SomaKorada07 (M3 Max) | `measure_mac.py` |
| The table | therahulbhati | `build_table.py` |

## 1. Measure on your Mac

Use the llama.cpp b11669 build from the staging recipe (#883, `stage_dryrun_inputs.py`). `measure_mac.py` needs `llama-bench`, which that build does not make by default:

```bash
cmake --build ./work/llama.cpp-b11669/build --target llama-bench -j 8
python teams/12-quantization/bitwidth_table/measure_mac.py \
    --bench ./work/llama.cpp-b11669/build/bin/llama-bench --build b11669 \
    --contributor <github login> --out teams/12-quantization/bitwidth_table/rows/<login>_<ram>gb.csv \
    <the GGUF files>
```

Pass all five formats of the same model (bf16, Q8_0, Q6_K, Q5_K_M, Q4_K_M). The format and model name come from the file name (`<model>-<format>.gguf`, as `quantize_eval.py` names them), or from `--format` and `--model`. Close other apps first: the speed numbers move with the load on the machine.

Each file gets two `llama-bench` runs:

| Run | Command | Columns |
|---|---|---|
| speed | `-p 512 -n 128 -r 5 -ngl 99` | `pp512_tok_s` (prompt), `tg128_tok_s` (generation), empty context |
| long | `-p 0 -n 16 -d 8192 -r 1 -ngl 99 -v` | `tg16_at_depth_tok_s` with 8,192 tokens in the cache; the memory |

Memory is what llama.cpp allocates in the long run, read from its own log: the weights, the KV cache for the context it reserved (`kv_cells`), and the compute buffers. `total_mb` is their sum and `kv_mb_per_1k` is the KV cache per 1,024 tokens. `fits_gpu` compares the total with the GPU working-set limit Metal reports (`recommendedMaxWorkingSetSize`, 5,727 MB, two thirds of RAM, on an 8 GB M1). macOS's own counters (`/usr/bin/time -l` peak memory footprint, resident set) are not used. On a 270 MB bf16 file they reported 80 MB, because they leave out the Metal buffers on unified memory.

Every row carries the GGUF's sha256. Rows from different Macs for the same model and format must be the same file, and so must the job's files. `build_table.py` lists every mismatch.

## 2. Build the table

```bash
python teams/12-quantization/bitwidth_table/build_table.py \
    --rows teams/12-quantization/bitwidth_table/rows/*.csv \
    --scores ./out/dryrun2-g12/scores.json --prompts ./out/dryrun2-g12/prompts/summary.json \
    --out teams/12-quantization/bitwidth_table/table.md
```

`--scores` and `--prompts` are optional, so the speed and memory part can be built before the job has run. Quality is always against bf16 of the same export: the score change on the 20 items, and on the 100 prompts the greedy outputs identical to bf16 and the mean shared prefix, with Team 10's 55 slots and our 45 apart (no Team 10 prompt text). `--strict` exits 1 on a sha256 mismatch.

## Which files

Our model first: the dry run 2 GGUFs. The job deletes its GGUFs at the end, so the Mac rows need a local export of the same weights (the weights-only copy Shubham asked TSAI for) with the same command and build. The sha256 check then shows whether the local files are the job's files. Until that copy exists, the public models Shubham proposed (1B, 3B and 7B, to show where the 16 GB limit is) use the same script. Everyone should take the same files (repo, revision and sha256).

## What I ran (therahulbhati, 28 Nov)

On an Apple M1 MacBook Air with 8 GB (macOS 27.2.1, llama.cpp b11669 at 620d222, Metal), with SmolLM2-135M as a stand-in. These are not our model's numbers:

| Format | bpw | Size (MB) | Prompt tok/s | Gen tok/s | Gen tok/s at 8,192 | Memory at 8,192: weights + KV + compute = total (MB) | GPU limit (MB) |
|---|---:|---:|---:|---:|---:|---|---:|
| bf16 | 16.0 | 270.9 | 4789.0 | 138.1 | 95.4 | 269.1 + 194.6 + 127.6 = 591.4 | 5726.6 |
| Q8_0 | 8.51 | 144.8 | 5349.8 | 183.2 | 108.5 | 143.0 + 194.6 + 127.6 = 465.3 | 5726.6 |
| Q4_K_M | 6.17 | 105.5 | 4590.7 | 172.2 | 88.2 | 103.7 + 194.6 + 127.6 = 426.0 | 5726.6 |

The Q4_K_M file is at 6.17 bpw because SmolLM2's embedding table is a large share of a 135M model and `quantize_eval.py` keeps the output layer at Q8_0. Speeds move by 10 to 20% between runs on this laptop (the Q4_K_M generation numbers came out below Q8_0's), so each row is one sitting on one machine. `python test_bitwidth_table.py`: 9 tests pass. They run against a fake `llama-bench` and cover the row columns, the units, a failed run, a log without buffer sizes, sha256 mismatches, reruns and a table without the job.
