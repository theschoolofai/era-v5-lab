#!/bin/zsh
# H3 harm check with planted cases (task 3.5) on the week-1 diagnosis packs, ruled scope (sa-en, sa-hi, hi-en, prose).
# The run of jobs/logs/2026-11-19-h3-harm-diag-local.txt, plus pairs whose answer is known (h3_harm_plant.py), so that
# removal is tested at E5c's thresholds and not only "nothing removed".
# Production order: spec v1.1 clean.py (use_clean.py + spec_v1/run_clean.py), overlap.py, h3.py, dedup.py.
# The diagnosis packs have no held-out split, and H3 can only remove a train translation of a held-out document. So each
# language takes a turn as held-out (sa, then hi, then en), and every gold document is a train document against the
# other two languages in two of the three runs. dedup.py runs three times per layout: no H3, h3.remove false, h3.remove
# true. h3_harm_check.py then checks every planted case and the harm check, and exits 1 if one fails.
# Inputs outside the repository: the diagnosis packs, FLORES+ devtest (G9's revision e707e62e) and the ind-sa-fw2
# same-page pairs with the ones read as real translations. Everything they hold stays in out/.
# Run from the repository root:  mkdir -p out && zsh teams/01-data-a/dedup/run_h3_harm.sh 2>&1 | tee out/h3harm.log
set -euo pipefail
SCR=${0:A:h}
DIAG=../../../All-parquets            # the week-1 diagnosis packs, 500 documents each
FLORES=../flores_plus                 # FLORES+ devtest: devtest/<code>.jsonl
KNOWN=../known_pairs.parquet          # build_known_pairs.py's 433 ind-sa-fw2 same-page pairs
REAL=../real_translations.csv         # the ones read by hand as real translations
OUT=out/h3harm
PACKS=(ind-sa-fw2 ind-hi-fw2 ind-hi-hplt ind-hi-indiccorp ind-hi-sangraha-s ind-hi-sangraha-v en-fineweb-edu en-dclm en-nemotroncc)
typeset -A PLANG
PLANG=(ind-sa-fw2 sa ind-hi-fw2 hi ind-hi-hplt hi ind-hi-indiccorp hi ind-hi-sangraha-s hi ind-hi-sangraha-v hi
       en-fineweb-edu en en-dclm en en-nemotroncc en)

echo "H3 harm check with planted cases on the diagnosis packs, $(date '+%A %d %B %Y %H:%M')"
echo "commit $(git rev-parse --short HEAD) ($(git log -1 --format=%s))"
echo "$(python3 --version), $(uname -sm)"
rm -rf $OUT out/h3harm_cache          # cold start: no cleaned files, no embedding cache
mkdir -p $OUT/clean
T0=$SECONDS

echo "\n== 0. Input files (SHA-256)"
for p in $PACKS; do shasum -a 256 $DIAG/$p.parquet; done
shasum -a 256 $FLORES/devtest/eng_Latn.jsonl $FLORES/devtest/hin_Deva.jsonl $FLORES/devtest/san_Deva.jsonl $KNOWN $REAL

echo "\n== 1. spec v1.1 clean.py on each pack"
t=$SECONDS
for p in $PACKS; do
  python3 -I teams/01-data-a/spec_v1_1/use_clean.py teams/01-data-a/spec_v1/run_clean.py --pack $DIAG/$p.parquet --out $OUT/clean
done
echo "clean seconds: $((SECONDS - t))"

echo "\n== 2. Layouts (one language held-out in each), planted cases and configs"
for held in sa hi en; do
  for p in $PACKS; do
    split=train; [[ ${PLANG[$p]} == $held ]] && split=heldout
    mkdir -p $OUT/$held-held/inputs/$split/$p
    cp $OUT/clean/${p}_clean.parquet $OUT/$held-held/inputs/$split/$p/part-00000.parquet
  done
done
python3 -I $SCR/h3_harm_plant.py --out $OUT --flores-dir $FLORES --known-pairs $KNOWN --real $REAL
python3 -I $SCR/h3_harm_configs.py $OUT

for held in sa hi en; do
  R=$OUT/$held-held
  echo "\n== 3. $held held-out: overlap.py"
  t=$SECONDS; python3 teams/01-data-a/dedup/overlap.py --config $R/overlap.json; echo "overlap seconds: $((SECONDS - t))"
  echo "\n== 4. $held held-out: h3.py"
  t=$SECONDS; python3 teams/01-data-a/dedup/h3.py --config $R/h3.json; echo "h3 seconds: $((SECONDS - t))"
  for m in noh3 report remove; do
    echo "\n== 5. $held held-out: dedup.py, $m"
    python3 teams/01-data-a/dedup/dedup.py --config $R/dedup_$m.json
  done
done

echo "\n== 6. Harm check with the planted cases"
rc=0                                  # zsh reserves $status
python3 -I $SCR/h3_harm_check.py --out $OUT --gold teams/01-data-a/gold teams/02-data-b/gold || rc=$?
echo "\nwall seconds: $((SECONDS - T0))"
exit $rc
