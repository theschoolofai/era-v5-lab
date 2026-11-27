# H3: the same content in another language

`h3.py` measures H3 (E5 of `h3_design_v1.md`): pairs of documents in two languages with the same content. It lists and
counts the pairs and removes nothing. `dedup.py` reads its `h3_matches.csv` through `h3_join.py`, where only rule 0
can remove a document: a train translation of a held-out document. The method, scope and open decisions are in
`h3_design_v1.md`.

## Run

Python 3.12 with the pinned packages in `requirements_h3.txt`, and the encoder in a local folder:

```sh
python3 -m pip install -r teams/01-data-a/dedup/requirements_h3.txt
python3 teams/01-data-a/dedup/h3.py --config teams/01-data-a/dedup/h3_local.json
```

`model_path` is LaBSE (`sentence-transformers/LaBSE`) in sentence-transformers format. The model is never downloaded:
the script sets the Hugging Face libraries offline, so the run needs no network or keys. It writes only under `out/`.
`h3_summary.json` records the sha256 of the model's weights.

## Inputs

```text
<inputs>/train/**/<part>.parquet      TSAI's cleaned output, as read by overlap.py
<inputs>/heldout/**/<part>.parquet
```

or the raw layout `<pack>/Part_N/` and `<pack>/Heldout/`, where a folder named `heldout`, in any case, is held-out.
Each row needs string `pack_id`, `doc_id` and `text`; a `url` column is used when present. `packs` maps pack ID
patterns to languages; parts without a configured pack are not read. In the cleaned layout, `part` is the path under
the split folder and `row_in_part` counts every row of the part from 0, as in `overlap_docs.parquet`, so `dedup.py`
finds each H3 document in the overlap run of the same cleaned parts.

## Which pairs count

```text
coverage = aligned sentence pairs / sentences of the shorter document >= coverage_threshold (0.6)
```

Two sentences align when each is the other's best match (mutual best, one to one) with cosine ≥ the language pair's
`sentence_threshold` (0.7 unless set for the pair, e.g. `{"sa-en": 0.55}`). Both thresholds are provisional until
E5's sweep and hand review. Candidates come from two sources:

- **Retrieval:** each document's `top_k` nearest documents in the other language by the cosine of its first
  `head_sentences` sentences, with cosine ≥ `doc_floor`, in both lists when `mutual`.
- **URL key:** pages whose URLs differ only in a language marker (`hi.example.org`, `/hi/`, `?lang=hi`).

Pairs whose lengths differ by more than `max_length_ratio` are not verified, except URL pairs. At most `max_verify`
pairs are verified: URL pairs first, then by cosine. Documents shorter than `min_chars` or with fewer than
`min_sentences` sentences of at least `sentence_min_chars` characters are counted and never encoded.

Parallel packs (H3-d: Pralekha, BPCC) are handled in `h3_join.py` (`parallel_packs`), not in `h3.py`.

## Outputs

All in `out`; IDs, scores and counts only, never text. The total must fit `max_output_mb` (at most 50 MiB).

| File | Contents |
|---|---|
| `h3_docs.parquet` | Row → document: row, id, doc_id, pack, lang, split, part, row_in_part, chars, sentences |
| `h3_candidates.csv` | Every verified pair at or above `report_floor`, and every URL pair: scores, numbers Jaccard, Latin-token share, coverage |
| `h3_matches.csv` | Pairs at or above `coverage_threshold`: `pack_id`, `split`, `part`, `row_in_part`, `doc_id` of each document, `lang_a`, `lang_b`, `coverage` (the header `h3_join.py` checks) |
| `h3_by_pack.csv` | Pack × pack: retrieved, URL, verified, listed and qualifying pairs |
| `h3_histogram.csv` | Bins of 0.01: the cosine of every retrieved pair, the coverage of every verified pair |
| `h3_summary.json` | Counts, stage times and rates, the estimate for all documents, model, versions, output sha256 |

A run stopped at `max_minutes` writes only the summary, with status `stopped_time_limit`. A run limited by
`max_docs_per_pack` also estimates the time for all documents of the selected packs and suggests a Max time
(1.5 × the estimate).

## Config

Paths are relative to the repository root; `out` and `cache` must be inside `out/`. Unknown keys fail; keys starting
with `_` are comments.

| Key | Meaning | Default |
|---|---|---|
| `inputs`, `out`, `cache` | Input root; output folder; embedding cache (`""` turns it off) | `out/tokenizer_sample_v0_clean`, `out/h3`, `out/h3_cache` |
| `packs`, `pairs` | `{pack_id pattern: language}`; the language pairs to compare | required |
| `model_path`, `device`, `precision` | Local encoder folder; `auto`, `cpu`, `mps` or `cuda`; `auto` (fp16 on CUDA, else fp32), `fp32`, `fp16` or `bf16` | required, `auto`, `auto` |
| `batch_size`, `max_seq_length` | Encoder batch and token limit | 64, 128 |
| `min_chars`, `min_sentences`, `sentence_min_chars` | Shortest document and sentence compared | 200, 3, 20 |
| `head_sentences`, `max_sentences` | Sentences in the document vector; sentences kept per document | 4, 16 |
| `top_k`, `doc_floor`, `mutual` | Neighbours per document; lowest cosine kept; both lists required | 3, 0.5, true |
| `max_length_ratio` | Longer / shorter characters allowed | 4.0 |
| `sentence_threshold`, `coverage_threshold`, `report_floor` | Aligned sentence cosine: one value, or `{"sa-en": 0.55}` per language pair in either order (a pair not named: 0.7); H3 coverage; lowest coverage listed | 0.7, 0.6, 0.3 |
| `max_verify`, `url_group_max` | Pairs verified; largest URL group paired | 10000, 20 |
| `block`, `pair_batch` | Rows per retrieval step; pairs per alignment step | 512, 1024 |
| `max_docs_per_pack`, `max_minutes`, `max_output_mb` | Documents per pack (0: all); time limit; output cap | 0, 60, 50 |
| `sync_debug` | On CUDA, torch warns at every host-device sync after the read stage | false |

`h3_local.json` is the local run: at most 2,000 documents of `ind-sa-fw2`, `ind-hi-fw2` and `en-fineweb-edu` from the raw
sample v0 in `../Cap1-packs`, pairs sa–en, sa–hi and hi–en.

## Speed and end-to-end check

`h3.py`, `h3_signals.py` and `h3_align.py` are batched. Text is processed as pyarrow record batches, vectors stay in
torch on the encoder's device, retrieval is a blocked matmul with `topk`, and sentence alignment is one `bmm` per batch
of pairs. The encoder runs the model's preprocessing and forward pass in batches of texts sorted by length, instead of
`SentenceTransformer.encode()`, which loops over every row in Python and copies each batch to the device with a
host-device sync; on CUDA, token batches and index arrays go to the device from pinned memory without blocking. No
Python loop runs over rows, documents, sentences, tokens or pairs.

- Hardware: Apple Silicon, MPS backend, fp32 (`precision` `"auto"` is fp16 on CUDA, with TF32 matmuls)
- Wall time: **305.0 s** for 6,000 documents (`h3_local.json`), from a cold start (no cache), peak RSS 845 MB
- Model: LaBSE, `model.safetensors` sha256 `deaceb20157886981bdedad1da11f39687e2343e978abc10e909939fb95d40c5`
- Versions: Python 3.12.10, numpy 2.4.3, pyarrow 23.0.1, torch 2.13.0, sentence-transformers 6.3.0

| Stage | Seconds | Rate |
|---|---|---|
| load_model | 11.5 | |
| read | 8.6 | 37,472 rows |
| encode | 158.3 | 37.9 document heads/s |
| url | 0.0 | |
| retrieve | 0.1 | 3 language pairs of 2,000 × 2,000 |
| verify_read | 0.3 | |
| verify | 126.0 | 108.0 sentences/s (13,601 sentences, 738 pairs) |

- Estimate for all documents of the three packs (72,665 en, 14,220 hi, 5,956 sa) at these rates: 50.8 min; suggested Max
  time 77 min
- Encoder: `Encoder.encode` and `SentenceTransformer.encode` on the same 587 head texts, one after the other: 18.0 s and
  20.7 s; the unit vectors differ by at most 1.5e-08
- Sync check: TODO on CUDA. MPS has no sync debug mode; run with `"sync_debug": true` on CUDA.
- No Python loops over tokens, documents, sentences or pairs: yes. Loops remain over parts, record batches, encoder chunks
  of 2,048 texts and batches of `batch_size`, retrieval row blocks, pair batches, the configured packs and language
  pairs, the distinct sizes of URL groups and the distinct non-ASCII digits in numbers.
- Host copies: one per stage result, and one per part for the embedding cache. Encoder chunks go to the tokenizer as
  Python strings.
- Result: 902 candidates, 738 verified, 0 at coverage ≥ 0.6

Command:

```sh
rm -rf out/h3_cache out/h3_local && python3 teams/01-data-a/dedup/h3.py --config teams/01-data-a/dedup/h3_local.json 2>&1 | tee out/h3_local.log
```

Last lines of output:

```text
    "documents_full": {
      "en": 72665,
      "hi": 14220,
      "sa": 5956
    },
    "seconds": {
      "load_model": 11.5,
      "read": 21.3,
      "encode": 2449.9,
      "retrieve": 17.1,
      "verify": 549.9
    },
    "minutes_total": 50.8,
    "every_stage_measured": true,
    "suggested_max_time_minutes": 77,
    "basis": "this run's rates; read scales with rows, encode with documents, retrieve with the product of the two languages' documents, verify with the smaller language's documents (at most max_verify)"
  },
  "wall_seconds": 305.0,
  "peak_rss_mb": 845.2
}

Wrote h3_docs.parquet, h3_candidates.csv, h3_matches.csv, h3_by_pack.csv, h3_histogram.csv and h3_summary.json to out/h3_local
```

The full console log is `teams/01-data-a/jobs/logs/2026-11-17-h3-local.txt` and the run's summary
`teams/01-data-a/jobs/logs/2026-11-17-h3-local/h3_summary.json`.

## E5d reader sheets

`h3_e5d_sheets.py` turns finished `h3.py` runs into blind sheets for bilingual readers, who label each pair a
translation or not. For each language pair it draws pairs from every coverage band on both sides of the 0.6 threshold.
For the Sanskrit pairs it pools the LaBSE and BGE-M3 candidates (theschoolofai/era-v5-lab#666; TSAI on
theschoolofai/era-v5-lab#626), so a pair is read once and the key holds both encoders' scores. It mixes in controls of
known answer. `per_band` (pairs per band) and `n_controls` are one count, or one per language pair, so the Sanskrit
pairs can get larger sheets than Hindi and Odia.

With `buckets` in place of `bands` and `per_band`, each language pair gets a set number of pairs per bucket, taken from
the bucket's coverage bands in order: a band whose pairs all fit is taken whole, from every encoder, each pair once;
otherwise the rest is drawn at random, split between the encoders. E5d's layout (50 items per sheet, with the controls)
is an "above" bucket that takes every qualifying pair, then fills from 0.45–0.6, and a "below" bucket from 0.30–0.45:

| Language pair | Above | Below | Known translations | Not translations |
|---|---|---|---|---|
| sa-en | 18 | 17 | 5 | 10 |
| sa-hi | 20 | 19 | 1 | 10 |
| hi-en | 25 | 25 | none | none |

A sheet shows only the item and the two texts, as the sentences `h3.py`
scored: `sentence_min_chars` and `max_sentences` come from the runs' `h3_summary.json`, and runs that split sentences
differently are refused. The sides are swapped at random and each reader's items are in their own order. Scores,
encoders, packs and doc_ids are only in the key. The sheets hold document text and stay in `out/`.

`h3_e5d_flores.py` tests the sheets on FLORES-200 (FLORES+ devtest, revision `e707e62e`, the files and sha256 of G9's
`teams/09-evaluation/fingerprints/v1/flores200/MANIFEST.json`): blocks of 8 sentences in en, hi, sa and or, where a
block against the same block in another language is a translation and against another block is not. Every language
must hold the same sentence ids, so that block i is the same text in each. Its `check` scores the sheets against those
answers. It also checks that the sheets are blind and match the key, that each text is the key's sentences on the side
the key names, and that the answer cells are empty.

### Speed and end-to-end check on FLORES

- Hardware: Apple M4, `h3.py` on MPS, fp32; the sheet scripts on the CPU
- Wall time: **145 s** from a cold start (`out/e5d_flores` removed)
- Model: LaBSE at revision `836121a`, `model.safetensors` sha256 `77d8e1f2dbab6eb5d3c261ce9d3dbf1e3c69e02938c95f934f94f42c22dfa31f`
  (the value E5c expects)
- Versions: Python 3.12.10, numpy 2.4.3, pyarrow 23.0.1, torch 2.13.0

| Stage | Seconds | What |
|---|---|---|
| build | 1 | 126 blocks of 8 sentences in 4 languages; 126 controls per language pair |
| `h3.py`, `h3_e5d_flores.json` | 83 | LaBSE at E5c's settings (0.55 for the Sanskrit pairs), 4 language pairs: 490 pairs verified, 416 qualifying |
| `h3.py`, `h3_e5d_flores_t07.json` | 59 | the Sanskrit pairs at sentence threshold 0.7, in a second encoder's place: 207 verified, 50 qualifying |
| `h3_e5d_sheets.py` | 2 | 217 items, 2 sheets per language pair |
| `h3_e5d_flores.py check` | 0 | status ok: every sheet's texts are the key's sentences on the key's sides, all answer cells empty |

| Language pair | Candidates drawn | Translations among them | Translations below 0.6 | Non-translations at or above 0.6 | Controls |
|---|---|---|---|---|---|
| sa–en | 67 (27 for LaBSE, 40 for the 0.7 run) | 67 | 27 | 0 | 10 |
| sa–hi | 70 (40 and 30) | 70 | 38 | 0 | 10 |
| hi–en | 20 | 20 | 0 | 0 | 10 |
| or–en | 20 | 20 | 0 | 0 | 10 |

- On FLORES, every Hindi and Odia translation has coverage ≥ 0.75 and no other block pair is listed, so those sheets
  draw from the top band only; their non-translations are the controls. The bands left short are in `e5d_summary.json`
- Sync check: not applicable to `h3_e5d_sheets.py` and `h3_e5d_flores.py`, which use no torch. `h3.py`'s is in
  [its speed section](#speed-and-end-to-end-check)
- No Python loops over tokens, documents, sentences or pairs: yes. Loops remain over the runs, language pairs, bands
  and encoders (the strata), the readers, the parts read and the files written

Command:

```sh
rm -rf out/e5d_flores && mkdir -p out && {
echo "start $(date -u +%Y-%m-%dT%H:%M:%SZ) commit $(git rev-parse --short HEAD) $(uname -m) $(python3 --version)"
T0=$(date +%s)
step() { local s=$(date +%s); echo "== $*"; "$@" || { echo "FAILED: $*"; return 1; }; echo "-- $(( $(date +%s) - s )) s"; }
step python3 -B teams/01-data-a/dedup/h3_e5d_flores.py build --flores-dir ../flores_plus --out out/e5d_flores &&
step python3 -B teams/01-data-a/dedup/h3.py --config teams/01-data-a/dedup/h3_e5d_flores.json &&
step python3 -B teams/01-data-a/dedup/h3.py --config teams/01-data-a/dedup/h3_e5d_flores_t07.json &&
step python3 -B teams/01-data-a/dedup/h3_e5d_sheets.py --config teams/01-data-a/dedup/h3_e5d_flores_sheets.json &&
step python3 -B teams/01-data-a/dedup/h3_e5d_flores.py check --sheets out/e5d_flores/sheets --out out/e5d_flores
echo "exit $? wall $(( $(date +%s) - T0 )) s end $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} 2>&1 | tee out/e5d_flores_run.log
```

Last lines of output:

```text
== python3 -B teams/01-data-a/dedup/h3_e5d_sheets.py --config teams/01-data-a/dedup/h3_e5d_flores_sheets.json
sa-en: 67 candidates and 10 controls -> 77 items, 2 sheets
sa-hi: 70 candidates and 10 controls -> 80 items, 2 sheets
hi-en: 20 candidates and 10 controls -> 30 items, 2 sheets
or-en: 20 candidates and 10 controls -> 30 items, 2 sheets
e5d sheets: 217 items, 10 strata short (0.12 s); out/e5d_flores/sheets
-- 2 s
== python3 -B teams/01-data-a/dedup/h3_e5d_flores.py check --sheets out/e5d_flores/sheets --out out/e5d_flores
hi-en: 20 candidates (20 translations), 10 controls; below 0.6: 0 translations; at or above: 0 non-translations
or-en: 20 candidates (20 translations), 10 controls; below 0.6: 0 translations; at or above: 0 non-translations
sa-en: 67 candidates (67 translations), 10 controls; below 0.6: 27 translations; at or above: 0 non-translations
sa-hi: 70 candidates (70 translations), 10 controls; below 0.6: 38 translations; at or above: 0 non-translations
flores check: ok
-- 0 s
exit 0 wall 145 s end 2026-11-23T12:33:55Z
```

The full console log is `teams/01-data-a/jobs/logs/2026-11-23-h3-e5d-flores.txt`. The folder
`teams/01-data-a/jobs/logs/2026-11-23-h3-e5d-flores/` holds the summaries of the build, both `h3.py` runs, the sheets and
the check, and `flores_truth.csv` (each item's answer). They hold IDs and counts only, no FLORES text.

### Controls for the Sanskrit sheets

`h3_e5d_controls.py` writes the generator's controls file from the 433 `ind-sa-fw2` same-page pairs of the encoder
checks (`known_pairs.parquet`, and each encoder's `pair_scores.csv`). A pair is a Sanskrit half and an English or Hindi
half of one page. Per language pair (sa-en, sa-hi) the controls, all expected "no", are:

- the pairs read by hand as not translations (both encoders score them at the cut);
- then unread pairs, drawn at random (seeded), that are far below every real translation on both encoders: coverage
  at sentence threshold 0.5 at most 0.5 with BGE-M3 (the 6 real translations: 0.857 and up) and below 0.3 with LaBSE
  (theirs: 0.3 and up).

The 2 `not_sanskrit` pairs are left out. `--positives` adds the 6 real translations as "yes" controls, so that each
Sanskrit sheet has the known translations of E5d's layout. The unread controls are listed in `controls.json`. They went
out unread (27 Nov): an unread control that a reader answers "yes" is read by a Sanskrit reader at scoring before it
counts against them.

| Language pair | Read non-translations | Unread, low on both encoders (drawn / pool) | Read translations ("yes") | Controls |
|---|---|---|---|---|
| sa-en | 2 | 8 / 312 | 5 | 15 |
| sa-hi | 1 | 9 / 65 | 1 | 11 |

Command, from the repository root (the encoder checks' pairs and scores, outside the repository); it took 2.2 s:

```sh
python3 -I teams/01-data-a/dedup/h3_e5d_controls.py --out out/e5d_controls --known-pairs ../known_pairs.parquet \
    --real ../real_translations.csv --labse ../pair_scores_labse_bge_m3/labse_15nov/pair_scores.csv \
    --bge ../pair_scores_labse_bge_m3/bge_m3_16nov/pair_scores.csv \
    --not-translations fea1f4f3908e44b3 d0479a80829a2dc1 f4dd16e97e012036 --positives
```

The output is `teams/01-data-a/jobs/logs/2026-11-25-h3-e5d-controls.txt`, and `controls.json` (rule, inputs' sha256,
counts, doc_ids) is in `teams/01-data-a/jobs/logs/2026-11-25-h3-e5d-controls/`. The run of 23 Nov without `--positives`
(`2026-11-23-h3-e5d-controls`) drew the same 17 unread pairs. `controls.parquet` holds page text and stays in `out/`.

### Reader viewer

`view_e5d_sheets.py` is the page a bilingual reader labels their sheets in: Python 3's standard library only, served on
127.0.0.1. It shows each item's `text_1` and `text_2` side by side (a sentence per line), with yes / no / unsure (keys
y, n, u) and a note, and saves `<pair>-reader<k>-<name>.csv` (item, translation, note; no text) to `--labels-dir`.
Unsaved answers are kept in the browser until saved. The page shows the item ID and the two texts only, and a save
needs the page's token.

```sh
python3 teams/01-data-a/dedup/view_e5d_sheets.py --sheets ../sheets --name "Your Name"
```

Run in a browser with Claude Code on two FLORES+ test sheets (sa-en, sa-hi reader 1): answers by key, save, reload
with an unsaved answer, and switching sheets.

### Reader zips

`h3_e5d_pack.py` makes one zip per reader from the generator's folder: the readers' guide (`README_e5d_readers.md`, as
`README.md`), the viewer, and the reader's sheets with `readers_guide.md`. The key, `sentences.parquet` and
`e5d_summary.json` never go in. `--assign` names each reader's sheets:

```json
{"reader_a": ["sa-en_reader1"], "reader_b": ["sa-en_reader2", "sa-hi_reader1"]}
```

Before it writes anything, it checks that:

- the run is complete, and each sheet and `readers_guide.md` has the sha256 the generator recorded;
- each sheet opens in the viewer, unanswered;
- a sheet goes to one reader only, and no reader gets both copies of a language pair.

Each zip is then reopened and its sheets loaded with the viewer. Sheets with no reader yet are listed and not packed,
so sheets can go out in stages. `manifest.json` records the hashes and each reader's sheets, with no text. The zips
hold page text: they are sent privately and never committed. For the real sheets, the readers' names stay in `out/`:

```sh
python3 -I teams/01-data-a/dedup/h3_e5d_pack.py --sheets-out out/e5d_e5c \
    --assign out/e5d_readers.json --out out/e5d_zips_e5c
```

Speed and end-to-end check on the FLORES+ test sheets, with placeholder readers (`h3_e5d_flores_readers.json`):

- Hardware: Apple M4, CPU; Python 3 with pyarrow (a reader needs only Python 3)
- Wall time: 0.70 s from a cold start (`out/e5d_zips_flores` removed), 4 zips
- A second run gave byte-identical zips
- No Python loops over sheet rows: the loops run over the readers and their files, and a sheet's answer cells are
  checked with pyarrow compute
- Sync check: not applicable, no torch

```sh
python3 -I teams/01-data-a/dedup/h3_e5d_pack.py --sheets-out out/e5d_flores/sheets \
    --assign teams/01-data-a/dedup/h3_e5d_flores_readers.json --out out/e5d_zips_flores
```

```text
e5d_reader_a.zip: sa-en_reader1  sha256 7d601e84ead26f3e
e5d_reader_b.zip: sa-en_reader2, sa-hi_reader1  sha256 4237d5c7dce65ac6
e5d_reader_c.zip: sa-hi_reader2  sha256 595d6332d9782a4b
e5d_reader_d.zip: hi-en_reader1  sha256 b32e12a27d7c4dca
not packed (no reader yet): hi-en_reader2, or-en_reader1, or-en_reader2
manifest: out/e5d_zips_flores/manifest.json
```

The log is `teams/01-data-a/jobs/logs/2026-11-25-h3-e5d-pack.txt`, with `manifest.json` in
`teams/01-data-a/jobs/logs/2026-11-25-h3-e5d-pack/`.

### The sheets from E5c and #666 (27 Nov)

`h3_e5d_e5c_sheets.json` draws from E5c's LaBSE run (theschoolofai/era-v5-lab#625: the five files of
`jobs/results/2026-11-18-h3-e5c/` and `h3_docs.parquet` from TSAI's link, each with the sha256 in E5c's
`h3_summary.json`) and #666's BGE-M3 run. Every drawn document's text matched what both runs read, so E5c read the #244
cleaning of sample v0, as #666 did.

E5c and #666 list only pairs with coverage 0.30 or more, so every sheet takes all their pairs above 0.45, and sa–en
also all below:

| Language pair | Above, ≥ 0.6 | Above, 0.45–0.6 | Below, 0.30–0.45 | Controls | Items | Short of the layout |
|---|---|---|---|---|---|---|
| sa–en | 1 | 2 | 14 | 15 | 32 | above 3 of 18, below 14 of 17 |
| sa–hi | 4 | 12 | 19 of 100 | 11 | 46 | above 16 of 20 |
| hi–en | 1 | 1 | 25 | 0 | 27 | above 2 of 25 |

The six qualifying pairs (coverage ≥ 0.6) of both runs are all on the sheets. The Sanskrit sheets are packed for three
G2 readers (theschoolofai/era-v5-lab#729) and the hi–en sheets for two Data A readers: five readers, each sheet read
twice.

- Hardware: Apple laptop, CPU; Python 3.12.10, numpy 2.4.3, pyarrow 23.0.1
- Wall time: 3.06 s for the sheets from a cold start (peak memory 545 MB), then the pack
- Sync check: not applicable, no torch; no code changed

```sh
/usr/bin/time -l python3 -I teams/01-data-a/dedup/h3_e5d_sheets.py --config teams/01-data-a/dedup/h3_e5d_e5c_sheets.json
```

```text
sa-en: 17 candidates and 15 controls -> 32 items, 2 sheets
sa-hi: 35 candidates and 11 controls -> 46 items, 2 sheets
hi-en: 27 candidates and 0 controls -> 27 items, 2 sheets
e5d sheets: 105 items, 4 buckets short (0.57 s); out/e5d_e5c
```

The log, with the inputs' sha256 and the pack's output, is `teams/01-data-a/jobs/logs/2026-11-27-h3-e5d-e5c-sheets.txt`;
`e5d_summary.json` and the pack's `manifest.json` (reader names replaced by reader_a to reader_c) are in
`teams/01-data-a/jobs/logs/2026-11-27-h3-e5d-e5c-sheets/`. The sheets and the key hold page text and stay in `out/`.

## Harm check with planted cases (task 3.5)

The harm check runs the pipeline on the week-1 diagnosis packs (9 prose packs of 500 documents; 1,308 gold documents)
with removal on, and passes when no gold document is removed (theschoolofai/era-v5-lab#625). The packs have no held-out
split, so `run_h3_harm.sh` holds out one language at a time (sa, hi, en). The run of 19 Nov
(`jobs/logs/2026-11-19-h3-harm-diag-local.txt`) passed, but nothing qualified, so it tested nothing
(theschoolofai/era-v5-lab#626). `h3_harm_plant.py` adds pairs whose answer is known to each layout:

| Case | Planted | Expected with `h3.remove: true` |
|---|---|---|
| p1 | FLORES+ devtest blocks of 8 sentences, 3 per language pair: the held-out language's block and the same block in another language, in train | The train document is removed (rule H3) exactly when it qualifies against a held-out document; the held-out one is kept |
| p2 | The 6 `ind-sa-fw2` same-page pairs read as real translations: the Sanskrit half held out, the translation half in train (sa-held only) | As p1 |
| p3 | 2 FLORES+ blocks in the two other languages, both in train | Never removed |

`h3_harm_check.py` then checks every layout: every candidate verified (`max_verify` 60,000); with removal on, the harm
check passes and no held-out document is removed; with removal off, `remove_list.csv` is byte-identical to the run
without H3; each p1 and p2 pair is as expected; every language pair with p1 plants has a removal; p3 is never removed.
It also lists H3 removals of real documents, and the margin: the highest coverage of a pair of real documents. A chain
through an H1/H2 copy cannot be planted with real text (the copy's translation also matches the held-out document
itself), so it stays with `tests/test_dedup_h3.py`.

| Layout | Gold removed (of 1,308) | Removal off = no H3 | H3 removed (real documents) | p1 removed / qualifying / planted | p2 | p3 removed / planted |
|---|---|---|---|---|---|---|
| sa held out | 0 | yes | 5 (0) | 3 / 3 / 6 | 2 / 2 / 6 | 0 / 2 |
| hi held out | 0 | yes | 4 (0) | 4 / 4 / 6 | none | 0 / 2 |
| en held out | 0 | yes | 5 (0) | 5 / 5 / 6 | none | 0 / 2 |

- **Removal is tested in every language pair.** p1 pairs removed: sa-en 2 of 3 (sa and en held out), sa-hi 1 of 3 (sa
  and hi held out), hi-en 3 of 3 (hi and en held out). Every qualifying held-out ↔ train pair was removed and no other.
- **Sanskrit misses.** Of the planted Sanskrit pairs that missed, some were never retrieved (no verified pair), and the
  others were verified below the cut: coverage 0.556 and 0.400 for FLORES+ sa-hi blocks, and 0.500, 0.375 and 0.200
  for real web pairs. Two of the 6 web pairs qualified (sa-hi 1.000, sa-en 0.800).
- **p3:** the hi-en train ↔ train pairs qualified (coverage 1.000) and were reported (`reported_train_train`), not
  removed; the sa-en and sa-hi ones did not qualify.
- **Margin on real documents:** highest coverage sa-en 0.143, sa-hi 0.188 (0.083 with a gold document), hi-en 0.125
  (0.062 with a gold document); none qualifies.

### Speed and end-to-end check

- Hardware: Apple M4, `h3.py` on MPS, fp32
- Wall time: **359 s** from a cold start (`out/h3harm` and its embedding cache removed)
- Model: LaBSE at revision `836121a`, as in E5c

| Stage | Seconds |
|---|---|
| spec v1.1 `clean.py`, 9 packs | 15 |
| `overlap.py`, per layout | 5, 5, 5 |
| `h3.py`, per layout (sa, hi, en held out): 383, 373 and 373 pairs verified | 168, 76, 76 |
| `dedup.py`, 3 modes per layout; `h3_harm_plant.py`; `h3_harm_configs.py`; `h3_harm_check.py` | 9 in all |

- Sync check: `h3_harm_plant.py` and `h3_harm_check.py` use no torch. `h3.py`'s is in
  [its speed section](#speed-and-end-to-end-check)
- No Python loops over tokens, documents, sentences or pairs in the new scripts: yes. Loops remain over the layouts,
  the dedup.py modes, the cases, the language pairs, the packs written and the gold files

Command, from the repository root (inputs outside the repository: the diagnosis packs in `../../../All-parquets`,
FLORES+ devtest in `../flores_plus`, `../known_pairs.parquet` and `../real_translations.csv`):

```sh
mkdir -p out && zsh teams/01-data-a/dedup/run_h3_harm.sh 2>&1 | tee out/h3harm.log
```

Last lines of output:

```text
== 6. Harm check with the planted cases
| Layout | Harm check | Gold in input | Gold removed | remove false = no H3 | H3 removed (real) | p1 removed / qualifying / planted | p2 | p3 removed / planted | Status |
|---|---|---|---|---|---|---|---|---|---|
| sa-held | pass | 1308 | 0 | yes | 5 (0) | 3 / 3 / 6 | 2 / 2 / 6 | 0 / 2 | pass |
| hi-held | pass | 1308 | 0 | yes | 4 (0) | 4 / 4 / 6 | 0 / 0 / 0 | 0 / 2 | pass |
| en-held | pass | 1308 | 0 | yes | 5 (0) | 5 / 5 / 6 | 0 / 0 / 0 | 0 / 2 | pass |
harm cases: pass

wall seconds: 359
```

The full console log is `teams/01-data-a/jobs/logs/2026-11-23-h3-harm-cases.txt`. The folder
`teams/01-data-a/jobs/logs/2026-11-23-h3-harm-cases/` holds `harm_cases.json` (every planted pair's result, the margin)
and `plants.csv` and `plants.json` (the planted pairs and the inputs' sha256): IDs, scores and counts only.

## Tests

```sh
python3 -B -m pytest teams/01-data-a/dedup/tests/test_h3.py teams/01-data-a/dedup/tests/test_h3_signals.py teams/01-data-a/dedup/tests/test_h3_align.py -q -rs -p no:cacheprovider
```

```text
.......................................................................  [100%]
71 passed in 2.27s
```

They check each batch function of `h3_signals.py` against its per-document reference, `align_batch` against `align`
(one threshold, and one per pair), `cross_topk` against a brute force of every pair, batch sizes of 1 against the
defaults, the 13-column `h3_matches.csv` keys against `h3_docs.parquet`, the train/heldout layout, the sentence
threshold per language pair, the time limit, the cache, the config checks, and a run without the Unix-only `resource`
module (Windows), where `peak_rss_mb` is null. A fake encoder stands in for the model, so the tests need no model or
network.

The E5d sheets:

```sh
python3 -B -m pytest teams/01-data-a/dedup/tests/test_h3_e5d_sheets.py teams/01-data-a/dedup/tests/test_h3_e5d_flores.py -q -rs -p no:cacheprovider
```

```text
.......................................................                  [100%]
55 passed in 2.51s
```

They check that a sheet has only its five columns and no doc_id, pack or score. They also check:

- every reader gets every item, in their own order;
- pairs are drawn from bands on both sides of the threshold;
- with buckets: every qualifying pair is taken once, from either encoder, then the bucket is filled from the next band;
  a draw is split between the encoders and topped up from one that has pairs; a short bucket is reported; the key
  labels each item's bucket (controls: "control"), and without buckets it has no bucket column;
- a pair both encoders listed is read once with both scores, even when the runs list its sides in the other order;
- side a is in the pair's first language;
- the texts are the sentences `h3.py` scored, split with the runs' settings, on the sides the key names;
- the controls are mixed in, and the seed fixes the sheets;
- a document changed since the run, an incomplete run, runs that split sentences differently or do not record how,
  and bad configs are refused;
- the FLORES packs, the controls and the FLORES+ `.jsonl` input are built as described, and languages with different
  sentence ids are refused;
- the check catches a sheet that is not blind or not the key's, a text that is not the key's sentences or is on the
  wrong side, filled-in answer cells and a missing `sentences.parquet`;
- the generator and the check work end to end without a model.

Every text in them is made up.

The controls for the Sanskrit sheets:

```sh
python3 -B -m pytest teams/01-data-a/dedup/tests/test_h3_e5d_controls.py -q -rs -p no:cacheprovider
```

```text
...........                                                              [100%]
11 passed in 2.30s
```

They check which pairs are taken (the read non-translations, then pairs low on both encoders; never a real translation
or a `not_sanskrit` pair), `--positives`, the seed, a short pool reported, a summary with no text, that the sheet
generator reads the file, and that mismatched score files, a pair missing from the known pairs, a pair listed as both a
translation and not one, and an unknown ID are refused. The pairs, texts and scores are made up.

The reader viewer:

```sh
python3 -B -m pytest teams/01-data-a/dedup/tests/test_view_e5d_sheets.py -q -rs -p no:cacheprovider
```

```text
.................                                                        [100%]
17 passed in 1.72s
```

They check which sheets it finds and how it names the answer files; that saving writes every item in the sheet's
order, keeps newlines in notes and holds no text; that bad answers, bad sheets and an empty folder are refused; that
answers typed into a sheet count until the first save; and, on a local server, that the page and sheets are served
with text only, that a save needs the page's token, and that a non-local Host is refused.

The reader zips:

```sh
python3 -B -m pytest teams/01-data-a/dedup/tests/test_h3_e5d_pack.py -q -rs -p no:cacheprovider
```

```text
..................                                                       [100%]
18 passed in 1.16s
```

They check that each zip holds the guide, the viewer and the reader's sheets, byte for byte, and never the key or the
summary; that unassigned sheets are listed and not packed; that the same inputs give the same zip; and that an unzipped
sheet opens in the viewer unanswered. They also check that these are refused: a sheet given to two readers, both copies
of a pair to one reader, an unknown or missing sheet, a bad reader name, an edited sheet, a sheet with an answer or a
note filled in, an incomplete run and `--out` outside `out/`. Every text in them is made up.

The harm check with planted cases:

```sh
python3 -B -m pytest teams/01-data-a/dedup/tests/test_h3_harm_plant.py teams/01-data-a/dedup/tests/test_h3_harm_check.py -q -rs -p no:cacheprovider
```

```text
.....................                                                    [100%]
21 passed in 0.80s
```

They check which pairs each layout gets and where their documents go (the FLORES+ blocks in their packs, distinct
blocks, marked IDs, the Sanskrit half of a web pair held out), and that unknown web pairs, FLORES+ files with different
sentence ids and a missing layout are refused. On hand-written run outputs, they check that a layout passes when the
qualifying plant is removed, including a web pair removed through its original page, and that a real removal is listed;
and that the check fails when a qualifying plant stays, another plant goes, a held-out document is removed, gold is
removed, removal off changes the remove list, or candidates are left unverified. Every ID in them is made up.
