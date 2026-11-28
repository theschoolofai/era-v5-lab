# clean.py: spec v1.1

**[`teams/01-data-a/spec_v1_1/clean.py`](clean.py)** is the cleaner built from the combined spec, [`sheets/specv1_1.md`](sheets/specv1_1.md) (TSAI, Gate 2).
- **What it holds:** 245 rules and the shared F1: code 24, English 23, math 21, sci 24, Indic 153.
- **How it runs:** `clean(doc)` takes `{doc_id, text, url, lang_label, pack_id}` and returns `(action, text)`, the action being `keep`, `fix` or `drop`. It picks the pack's family by `pack_id`, runs that family's rules in sheet order, then the shared F1.
- **Run order:** each family's spec v1 rules first, then its spec v1.1 rules. In English, `DA-F1-005` is last.
- **Packs with no rules** pass through unchanged: cadj-notebooks, cadj-stackexchange, ind-ml-fw2, ind-or-fw2, ind-ta-fw2 and ind-ta-sangraha-s. cadj-commits has no rules of its own either, but gets the shared F1 for e-mail addresses only (family `code-adjacent`, an empty pipeline).
- **It is generated:** don't edit it. Change the sheet, then rebuild.
- **It includes the fixes of #49** (the team fork, merged as `34bc882`):
  - speed fixes to `DA-F1-005`, `DA-C1-001` and `DA-D3-005` in the sheet, and to the shared F1 in `build/f1_rule.py`, each with the same output;
  - one change of output: the shared F1 picks its path by `pack_id`, not by the language label, so it also runs on science docs labelled `en`, as in the tokenizer sample.
- **The build is in `build/`:** `build_clean.py` and `f1_rule.py` are spec v1's, with the changes of #49. By default they build `sheets/specv1_1.md` into `spec_v1_1/clean.py`. No file in `spec_v1/` or `tests/spec_v1/` changes: they are as on TSAI main.
- **It includes the speed fixes of #50** (the team fork, merged as `5c4456e`) in the sheet: five code rules (`DA-A6-001`, `DA-A4-002`, `DA-E2-001`, `DA-E3-003`, `DA-E3-004`) and three math rules (`DA-A5-002`, `DA-A8-001`, `DA-C7-001`). On the historical speed runs in `results/cleaner/`, its output was byte for byte that of the build before them (`ea14b0899085…`).

Paths are from `teams/01-data-a`.

## What decides the cleaning

- **The tools are spec v1's, unchanged:** `spec_v1/run_clean.py`, `spec_v1/run_tokenizer_sample.py` and `spec_v1/validate/make_harm_tests.py`. Each does `import clean`. `use_clean.py` loads `spec_v1_1/clean.py` as `clean` first, then runs the tool, so the tool cleans with spec v1.1.
- **`clean.py` holds two things,** both put in by `build/build_clean.py`:
  - the rules of `sheets/specv1_1.md`, each block's code as the sheet has it, except for its pack lines (below) and these edits by the build:
    - it drops the `AUTHOR` line;
    - it stops `DA-B4-009` from rewriting the `<EMAIL>` tag;
    - it applies two TSAI rulings of 28 Nov while the sheet is frozen. `DA-A5-002` is deferred: Unicode NFC only, never NFKC (#915). `DA-B4-001`'s `{[ ]}` form needs spaces inside, as its `{{ }}` form does, so LaTeX bracket groups are kept (#911, #926). Both move into the sheet when it is unfrozen;
  - the shared F1, from `build/f1_rule.py`. It runs after the rules on the code, math, sci and Indic packs, and on cadj-commits for e-mail addresses only (its phone-like numbers are IP addresses, part numbers and data). English runs its own F1 rule, `DA-F1-005`, instead.
- **The packs a rule runs on are in `SCOPE`,** the table at the top of `clean.py`: 246 entries, one per rule and one for the shared F1.
  - In the sheet, each block names its packs in `SPEC_PACKS`. A block that also guards on its own `ORIGIN` packs (`PACKS` or `_PACKS`) runs only where both allow.
  - The build writes that set once, into `SCOPE`, and points the block's `SPEC_PACKS`, `PACKS` and `_PACKS` at its `SCOPE` entry.
  - `_run` also skips a rule when the doc's `pack_id` is not in its entry, and the pack-to-family table (`_FAMILY`) is made from `SCOPE`. A pack in two families stops the build.
  - `ORIGIN`, `SOURCE` and `SOURCE_ORIGIN` stay in each block as the record of where its rule came from. No code reads them.

## Files

| file | what it is |
|---|---|
| [`spec_v1_1/clean.py`](clean.py) | The cleaner (generated) |
| [`spec_v1_1/use_clean.py`](use_clean.py) | Runs a spec v1 tool, unchanged, on `spec_v1_1/clean.py`: `use_clean.py <tool.py> [the tool's arguments]` |
| [`spec_v1_1/build/build_clean.py`](build/build_clean.py), [`spec_v1_1/build/f1_rule.py`](build/f1_rule.py) | The build of `clean.py`, and the shared F1 it puts in |
| [`spec_v1_1/tests/test_clean.py`](tests/test_clean.py) | Unit tests of `clean.py` and `use_clean.py` |
| [`spec_v1_1/tests/test_speed_equivalence_*.py`](tests/) | Each speed fix of #49 and #50 against a frozen copy of the rule before it (5 files, pytest) |
| [`spec_v1_1/results/speed_v1_1.md`](results/speed_v1_1.md) | The speed logs of each fix, rule by rule (#55) |
| [`spec_v1_1/jobs/tokenizer_sample_v0_clean.json`](jobs/tokenizer_sample_v0_clean.json) | The tokenizer-sample job config, pinned to this `clean.py` |
| [`spec_v1_1/results/cleaner/harm_tests.md`](results/cleaner/harm_tests.md) | Current `clean()` gold harm, including cadj-commits email-only coverage |
| [`spec_v1_1/results/cleaner/speed.md`](results/cleaner/speed.md) | Wall time on each 500-doc sample pack, spec v1 against spec v1.1 |
| [`spec_v1_1/results/cleaner/tokenizer_sample_run.md`](results/cleaner/tokenizer_sample_run.md) | The end-to-end run on all 86 parts of the tokenizer sample v0 (a sample, not the full packs) |

## This cleaner (28 Nov): DA-A5-002 deferred, DA-B4-001 keeps LaTeX groups

`b9e78f73ec5b4a892d978e7bfc1759fa05e9386054a626e5645e6dce49b58d10` is the one cleaner change TSAI ruled for, before
corpus-v1. `pipeline/clean.json` and `jobs/tokenizer_sample_v0_clean.json` pin it.

**What it fixes:**
- **DA-A5-002 is deferred.** It folded ligatures with NFKC and fullwidth letters to ASCII, and the lab rule is Unicode
  NFC only, never NFKC (#915).
- **DA-B4-001's `{[ ]}` form needs spaces inside**, as its `{{ }}` form does. It no longer deletes LaTeX bracket groups
  such as `i^{[j]}` (#911, #926).

Both changes are made by `build/build_clean.py` while the sheet is frozen; `sheets/specv1_1.md` is unchanged.

**Tests:**
- `python3 -m pytest spec_v1_1/tests -q`: **1,961 passed, 26 subtests passed**. `python3 -m unittest discover -s
  spec_v1_1/tests`: **206 tests, OK**, with no expected failures.
- These include `tests/test_clean.py`'s `NormalForm` (#915) and `tests/test_da_b4_001_latex.py`'s `LatexKept` (#911,
  #926). They failed on `d275556e` and were marked as strict expected failures; this cleaner removes the markers.

**The 1% slice of tokenizer sample v0** (all 86 parts, 14,450 rows, `jobs/2026-11-28-clean-fix-1pct/run.json`, commit
`15e9d578`), against the same run with `d275556e` (#898, `run_baseline.json`):

| | `d275556e` | `b9e78f73` |
|---|---|---|
| pipeline checks | 54 / 54 | 54 / 54 |
| rows: raw → dropped by clean → removed by dedup → dropped by F2 → final | 14,450 → 344 → 0 → 14 → 14,092 | the same |
| DA-A5-002 on the math packs | 4 of 472 documents changed | not run (deferred) |
| DA-B4-001 on the math packs | 2 of 472 documents changed | 2 of 472 documents changed |
| cleaned parts that differ | | the two math train parts only |
| shards that differ | | `math-finemath-train-000000`, `math-megamath-train-000000`; the other 46 are byte-identical |

- **Stage seconds** on an Apple M4: clean 10.1 → 9.6, overlap 18.5 → 16.6, F2 35.5 → 33.8, shards 151.6 → 152.0; total
  218.5 → 214.8. An earlier run of this cleaner took 228.0 s. These differences are noise between runs at this size; the
  fix removes one math rule and changes no other code.
- **DA-B4-001's `{[ ]}` form on the slice** (`scripts/count_da_b4_001_latex.py`, #911, on the slice's four math parts):
  the counts are the same with both cleaners. 2 of 294 math-finemath documents have a `{[ ]}` group (6 groups), and
  DA-C3-004 drops both before DA-B4-001 runs; no math-megamath document has one. The slice is too small to show the
  fix. On the 38 sample packs, #911 counts what the old form did: it changed 21 math-finemath documents (20 of them by
  deleting LaTeX groups) and 68 math-megamath documents (61 of them losing only footnote markers `^{[1]}`). Logs:
  `jobs/logs/2026-11-28-clean-fix-1pct/b4_counts_before.json` and `b4_counts_after.json`.
- **Shards and provenance:** `shards/verify_shards.py` finds 0 problems in the 48 shards. `shards/provenance.py` passes
  the chains of `final/train/math-megamath/part-00000` (143 rows) and `final/train/code-go/part-00000` (557 rows), each
  back to its raw part, with cleaner `b9e78f73`, commit `15e9d578` and manifest `3984f041…`. The logs are
  `verify_shards.txt` and `provenance.txt` in the same folder.
- **The log is `jobs/logs/2026-11-28-clean-fix-1pct/run.txt`.** The run's summary files stay out of the repository, as
  TSAI asked for #898. Their sha256, under `out/pipeline/clean-fix-1pct/`:
  - `pipeline_manifest.json` `3984f041c760eed3da953b34ef4ba59f360f3f8850f2781f4913a4df37bc5494`;
  - `overlap/overlap_summary.json` `1799a5dcb22784d17a932644105f9a3cec806ef0dd989de69e917e069b5340b7`;
  - `shards/shards_summary.json` `8654ea28b65b71cb9ccfab97810035cdf74dcae0cf759d86b8273a8a77fbfb5d`;
  - `cleaning_pipeline.json` `cdf399575c5235408fb68cce43483edd2ecfd4755361b730956fa7ef0e360872`.
- **Gold harm for `b9e78f73`** (`scripts/run_current_harm.py` on the 38 sample packs, 11.8 s) is the same as the
  previous cleaner's run (`results/cleaner/harm_2026_11_23/`):
  - 33 testable packs, 4,768 gold documents. 28 of the 32 supported packs PASS, and the same four FAIL: en-nemotroncc,
    math-finemath, sci-finepdfs and ind-te-sangraha-v.
  - The affected gold documents are the same, ID for ID, and `summary.csv` is identical.
  - The one difference: DA-A5-002 is no longer tested on the two math packs, where it changed none of the 112 gold
    documents. DA-B4-001 changes none of them either.
  - Every pack and gold sha256 matches that run. The log is `jobs/logs/2026-11-28-clean-fix-1pct/harm.txt`.
- **Every document of the 38 sample packs, `d275556e` against `b9e78f73`** (19,000 documents, both cleaners' `clean()`
  on each, 29.8 s and 29.5 s):
  - **18,984 are identical.** The 36 non-math packs are identical document for document, the five without gold
    included.
  - **16 differ, all math** (3 in math-finemath, 13 in math-megamath). In each one the new cleaner does less: 13 fixes
    become keeps, and 3 fixes remove less. No drop changes.
  - **Replaying the math pipeline rule by rule** (the replay matches `clean()` on all 16): 14 are DA-A5-002's folds no
    longer applied, and 2 (math-megamath) are DA-B4-001's `{[ ]}` form no longer matching. The other rules change those
    documents as before.
  - The logs are `jobs/logs/2026-11-28-clean-fix-1pct/compare_38.txt` and `trace_16.txt` (counts, document IDs and
    rule IDs only).
- **Every document of tokenizer sample v0, `d275556e` against `b9e78f73`** (all 86 parts, 1,444,766 documents):
  - **1,444,357 are identical.** The 82 non-math parts are identical document for document.
  - **409 differ, all math** (220 math-finemath, 189 math-megamath): 320 because of DA-A5-002 only, 88 because of
    DA-B4-001 only, and 1 because of both.
  - **In 4 of them a later rule acts differently, because DA-A5-002's NFKC fold used to run before it** (all
    math-megamath):
    - DA-C7-002 no longer drops 2 documents that write "ﬁgure" with the U+FB01 ligature, since its pattern matches
      only `figure` (`7f0c9036831f32d1` is kept, `9cb311703c53c1e0` is fixed);
    - DA-A8-001 no longer changes 1 document (`c07b8380d5ccf71f`), which has no ligature; this follows from the B4
      fix;
    - **the shared F1 no longer replaces 1 e-mail address** (`24eb58a1f92356ad`). The address has a ligature next to
      it, and F1 finds it only after the fold.
  - The logs are `jobs/logs/2026-11-28-clean-fix-1pct/sample_math.txt`, `sample_math_rules.txt` and `sample_rest.txt`
    (counts, document IDs and rule IDs only).

## Harm validation of the previous cleaner (after merged #88)

The cleaner rebuild is byte-identical to merged #88:
`d275556ee87a259b05ac5e474ed40b569c2e821aaaffa99d5d07035e40948989`. It retains the five scoped #86 preservation guards and adds
email-only shared F1 on `cadj-commits` with an empty `code-adjacent` pipeline.
Both active job configs pinned this cleaner until 28 Nov.

Fresh full-gold harm: **4,768 documents, 33 testable packs; 28 of 32 supported
packs PASS, four FAIL**. `cadj-commits` now has cleaning coverage and passes all
413 gold documents with zero changes or drops. Every full-pipeline outcome and
affected ID matches the previous run. Only `ind-ta-fw2` remains testable but
unsupported; five packs lack gold. No execution or Indic Unicode-audit errors.

The full 500-document `cadj-commits` pack has 40 email-only changes, zero drops
and no second-pass changes; the other two code-adjacent packs pass through.
**1,952 cleaner tests and nine subtests PASS; 125 job/preparation tests PASS.**
See [the replaced current harm report](results/cleaner/harm_tests.md) for fresh
evidence, raw failures, missing gold and clearly labelled historical comparisons.
Reproduce the gold run with
`scripts/run_current_harm.py --packs <original-packs-folder> --out <output>`.

## Historical harm summary (17 Nov 2026)

From [`results/cleaner/harm_tests.md`](results/cleaner/harm_tests.md), on TSAI's 500-doc sample packs:
- **27 of the 31 packs PASS.** No rule changes a doc on a pack outside its scope.
- **4 packs FAIL:** en-nemotroncc (2 gold docs changed, limit 1), math-finemath (2, limit 1), sci-finepdfs (5, limit 2) and ind-te-sangraha-v (2, limit 1).
- **All 11 of those gold docs are touched by spec v1.1 rules.** 10 are gold contradictions: the gold marks them clean, but each holds the disease its rule targets. The 11th is a false positive of `DA-C7-005`, within that rule's limit.
- **Without the 10 gold contradictions, all 4 packs pass.** As `sheets/NEW_DISEASES.md` records, they are left out of the count for their rule only, and re-read at the next gold refresh.
- **No rule is quarantined or turned off.** The rules behind the 4 FAILs run in `clean.py` as candidates, like every rule of the sheet.

## Build

```
python3 -I spec_v1_1/build/build_clean.py --sheet spec_v1_1/sheets/specv1_1.md --out spec_v1_1/clean.py
```

`tests/test_clean.py` fails if `clean.py` differs from a fresh build.

## Test

```
python3 -m unittest discover -s spec_v1_1/tests
python3 -m pytest spec_v1_1/tests/test_speed_equivalence_*.py
```

The speed tests are pytest tests, so `unittest` does not run them.

## Run

One pack or part:

```
python3 -I spec_v1_1/use_clean.py spec_v1/run_clean.py --pack <pack>.parquet --out <out>
```

For a tokenizer-sample part, also give `--pack-id <pack>`.

The tokenizer sample v0, end to end (the runner writes only beneath `./out/`):

```
python3 -I spec_v1_1/use_clean.py spec_v1/run_tokenizer_sample.py --config spec_v1_1/jobs/tokenizer_sample_v0_clean.json --input-root <sample folder>
```

## Check the results yourself

Every number in `results/cleaner/` can be made again with the steps below. They come from runs of `clean.py` `6a57276c0e83…` on 17 Nov 2026, on an Apple M4 (one core) with Python 3.12.10. Every run is on samples, not on the full packs.

**Set up.** Keep the outputs out of the repository: the tools write where `--out` points, and the tokenizer runner writes beneath `./out/` of the folder it runs in.

```bash
A=<repository>/teams/01-data-a      # this team folder
W=<a work folder outside the repository>
python3 -m pip install -r $A/spec_v1/requirements.txt
```

You also need:
- `<packs>`: TSAI's 500-doc sample packs, named `<pack_id>.parquet`, in one folder.
- `<sample>`: TSAI's tokenizer sample v0, with its `train/` and `heldout/` folders.
- `<checkout>`: a copy of the repository whose Data A gold folder also holds Data B's 18 Indic gold files. The harm tool reads gold only from there.

```bash
cp -R <repository> <checkout>
cp <checkout>/teams/02-data-b/gold/ind-*_gold.csv <checkout>/teams/01-data-a/gold/
```

### 1. `clean.py` is the sheet, built

```bash
shasum -a 256 $A/spec_v1_1/clean.py
python3 -I $A/spec_v1_1/build/build_clean.py --sheet $A/spec_v1_1/sheets/specv1_1.md --out $W/clean_rebuilt.py
shasum -a 256 $W/clean_rebuilt.py
```

- The build ends with `clean_rebuilt.py: rules 246 + shared F1 | code 24 rules on 6 packs, english 23 rules on 4 packs, math 22 rules on 2 packs, sci 24 rules on 1 packs, indic 153 rules on 18 packs | functions: 41`.
- The `strings changed` lines before that name the multi-line strings that putting each block inside a function re-indents: docstrings and verbose regexes, where indenting changes nothing.
- Both hashes are `6a57276c0e83312b09facfba656cca28db0ef59ca851bcfbfa3ef63f16fdd1f2`, the one `jobs/tokenizer_sample_v0_clean.json` pins.

### 2. The unit tests

```bash
cd $A && python3 -m unittest discover -s spec_v1_1/tests
```

It ends in `OK`. `tests/test_clean.py` checks what this README says about `clean.py`:
- it is the same as a fresh build of `sheets/specv1_1.md`;
- it holds 245 rules and the shared F1: code 24, English 23, math 21, sci 24, Indic 153 (`DA-A5-002` is deferred by the build);
- `SCOPE` gives each of the 24 spec v1.1 rules (the medicines of `sheets/NEW_DISEASES.md`) exactly its `ORIGIN` packs;
- each family runs its spec v1 rules first, then its spec v1.1 rules, and English ends with `DA-F1-005`;
- a spec v1 tool run through `use_clean.py` gets `spec_v1_1/clean.py`.

```bash
cd $A && python3 -m pytest -q spec_v1_1/tests/test_speed_equivalence_*.py
```

It ends in `1677 passed`. Each test gives the same texts to a rule after its speed fix and to a frozen copy of it from before, and checks that the results are equal.

### 3. Harm ([`results/cleaner/harm_tests.md`](results/cleaner/harm_tests.md))

```bash
python3 -I $A/spec_v1_1/use_clean.py $A/spec_v1/validate/make_harm_tests.py <checkout> <packs> --out $W/harm/harm_tests.md --results $W/harm
```

- It takes about 2 minutes and exits with 1, because of the gold contradictions.
- The gold docs `clean()` changed or dropped, in `$W/harm/harm_tests.md`, must match `results/cleaner/harm_tests.md` on all 31 packs. Only 4 packs FAIL: en-nemotroncc 2, math-finemath 2, sci-finepdfs 5 and ind-te-sangraha-v 2. Their 11 doc_ids, in the `clean` entry (`changed_ids`, `dropped_ids`) of `$W/harm/specv1_<pack>_harm.json`, are the ones `results/cleaner/harm_tests.md` lists.
- `pack_sha256` in each `$W/harm/specv1_<pack>_harm.json` must equal the one in `results/spec_v1/cleaner/specv1_<pack>_harm.json`. That shows your packs are the files tested here.
- `rules_file_sha256` in those files is the hash of `spec_v1/clean.py` (spec v1, `22d818c72c9f…`), the file next to the tool, not of the cleaner that ran. The last test of step 2 shows which one runs.

### 4. Speed ([`results/cleaner/speed.md`](results/cleaner/speed.md))

Spec v1 there is `spec_v1/clean.py`, as on TSAI main (`22d818c72c9f…`). For each pack, and for runs 1, 2 and 3:

```bash
python3 -I $A/spec_v1/run_clean.py --pack <packs>/<pack>.parquet --out $W/speed/v1/<run>
python3 -I $A/spec_v1_1/use_clean.py $A/spec_v1/run_clean.py --pack <packs>/<pack>.parquet --out $W/speed/v11/<run>
```

- Each `<pack>_summary.json` gives `seconds`, the time of each rule (`rule_seconds`), and `clean_py_sha256`: `22d818c72c9f…` for spec v1, `6a57276c0e83…` for spec v1.1. The table gives the best of the 3 runs.
- The seconds depend on the machine, so compare the two cleaners on one machine.
- The docs fixed and dropped (`actions`) do not depend on it, and must give the table's last column.

### 5. The tokenizer sample, end to end ([`results/cleaner/tokenizer_sample_run.md`](results/cleaner/tokenizer_sample_run.md))

```bash
cd $W && python3 -I $A/spec_v1_1/use_clean.py $A/spec_v1/run_tokenizer_sample.py --config $A/spec_v1_1/jobs/tokenizer_sample_v0_clean.json --input-root <sample>
```

- It takes about 21 minutes and writes `$W/out/tokenizer_sample_v0_clean_specv1_1/`.
- It stops before cleaning anything if `clean.py` is not the one the job pins, or if a part differs from the manifest.
- Its last line holds `"actions": {"drop": 34536, "fix": 363076, "keep": 1047154}`, `"completed_parts": 86`, `"errors": 0`, `"input_rows": 1444766` and `"output_rows": 1410230`.

The stage table, and the rules behind the drops:

```bash
cd $W && python3 -I - <<'EOF'
import csv, json
out = "out/tokenizer_sample_v0_clean_specv1_1"
parts = [json.load(open(f"{out}/reports/{p['part']}.json")) for p in json.load(open(f"{out}/cleaned_manifest.json"))["parts"]]
for status in ("cleaned", "unsupported_passthrough"):
    ps = [p for p in parts if p["status"] == status]
    acts = {a: sum(p["actions"].get(a, 0) for p in ps) for a in ("keep", "fix", "drop")}
    print(status, len(ps), "parts, docs in", sum(p["input_rows"] for p in ps), acts, "docs out", sum(p["output_rows"] for p in ps))
print("drops by rule, all rules:", sum(int(r["drop"]) for r in csv.DictReader(open(f"{out}/rule_counts.csv"))))
EOF
```

- `cleaned`: 72 parts; 1,247,281 docs in; 849,669 kept as is, 363,076 fixed, 34,536 dropped; 1,212,745 docs out.
- `unsupported_passthrough`: 14 parts; 197,485 docs in, all kept; 197,485 out.
- The drops of all rules in `rule_counts.csv` add up to 34,536: each drop is made by one rule of the sheet. Each rule's own count is in its row.

### 6. The second pass

`clean()` again, on each part it cleaned in step 5:

```bash
cd $W
OUT=out/tokenizer_sample_v0_clean_specv1_1
for f in $OUT/train/*/*.parquet $OUT/heldout/*/*.parquet; do
  rel=${f#$OUT/}; split=${rel%%/*}; pack=$(basename "$(dirname "$f")"); name=$(basename "$f" .parquet)
  grep -q '"status": "cleaned"' "$OUT/reports/$rel.json" || continue
  python3 -I $A/spec_v1_1/use_clean.py $A/spec_v1/run_clean.py --pack "$f" --pack-id "$pack" --out "pass2/$split/$pack/$name"
done
python3 -I - <<'EOF'
import collections, glob, json
total, parts = collections.Counter(), 0
for f in glob.glob("pass2/*/*/*/*_summary.json"):
    s = json.load(open(f)); total.update(s["actions"]); parts += 1
print(parts, "parts", dict(total))
EOF
```

It takes about 20 minutes. It gives 72 parts: 1,212,433 docs kept as is, 204 fixed and 108 dropped.
