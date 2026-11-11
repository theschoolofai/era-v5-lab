#!/usr/bin/env bash
# Before/after check for a clean.py speed-up: same output sha256, docs/s, per-rule profile, harm tests unchanged.
# Runs the steps of results/spec_v1/speed_v1.md one stage at a time (or all together) with speed_check.py,
# run_clean.py and make_harm_tests.py. Everything is written under --work, never into the repo.
#
#   oneoff/speed_compare.sh [options] STAGE...
#
# Stages (run in the order given):
#   trees       build $WORK/before and $WORK/after (git archive of the two revisions; clean.py is the only difference)
#   speed       hash and time both clean.py on the 13 sample packs, then compare (sha256 equal? docs/s)
#   code        re-time the 6 code packs, 2 rounds alternating before/after, 5 repeats (noise check)
#   profile     per-rule time of both trees on en-dclm and en-fineweb-edu (500 docs); the top rule not yet fixed is next
#   harm        make_harm_tests.py on both trees, then diff the results (only rules_file_sha256 should differ)
#   all         trees speed code profile harm   (a few minutes; the large parts are NOT included)
#   bigprofile  profile the after tree on the first --slice docs of a large week-2 part (default 5000; minutes)
#   big         the full week-2 part-00000 of en-dclm and en-fineweb-edu, both trees, in the background (about 30 min)
#
# Options (or the environment variable in brackets):
#   --before REV   revision whose clean.py is "before"                  [BEFORE, default: 730253d^]
#   --after  REV   revision for "after", or "worktree" = HEAD plus the clean.py in your working copy [AFTER, default: HEAD]
#   --packs DIR    the 13 sample packs, <pack>.parquet                  [PACKS, default: <repo parent>/week1-packs]
#   --week2 DIR    the week-2 sample (train/<pack>/part-00000.parquet)  [WEEK2, default: <repo parent>/week-2]
#   --work DIR     where trees, results and logs go                     [WORK, default: <repo parent>/scratchpad/clean-speed]
#   --python PATH  Python with pyarrow                                  [PY, default: the era5 conda python]
#   --slice N      docs for bigprofile                                  [SLICE, default 5000]
#   --exclude PACK pack left out of speed (repeatable, default ind-mr-sangraha-v)
# Each stage prints what it did; the results files are in $WORK (before.json, after.json, speed_table.md, harm/, profile/).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(git -C "$HERE" rev-parse --show-toplevel)"
TEAM="$(dirname "${HERE#"$REPO"/}")"                      # teams/01-data-a
PARENT="$(dirname "$REPO")"
BEFORE="${BEFORE:-730253d^}"; AFTER="${AFTER:-HEAD}"
PACKS="${PACKS:-$PARENT/week1-packs}"; WEEK2="${WEEK2:-$PARENT/week-2}"
WORK="${WORK:-$PARENT/scratchpad/clean-speed}"
PY="${PY:-/home/forest/miniconda3/envs/era5/bin/python}"
SLICE="${SLICE:-5000}"; EXCLUDE=(ind-mr-sangraha-v); STAGES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --before) BEFORE="$2"; shift 2;; --after) AFTER="$2"; shift 2;; --packs) PACKS="$2"; shift 2;;
    --week2) WEEK2="$2"; shift 2;; --work) WORK="$2"; shift 2;; --python) PY="$2"; shift 2;;
    --slice) SLICE="$2"; shift 2;; --exclude) EXCLUDE+=("$2"); shift 2;;
    -h|--help) sed -n '2,32p' "$0"; exit 0;;
    -*) echo "unknown option $1" >&2; exit 2;; *) STAGES+=("$1"); shift;;
  esac
done
[ ${#STAGES[@]} -eq 0 ] && { sed -n '2,32p' "$0"; exit 2; }
[ "${STAGES[*]}" = "all" ] && STAGES=(trees speed code profile harm)
PIN=(); command -v taskset >/dev/null && PIN=(taskset -c 0)
CHECK="$HERE/speed_check.py"; FAIL=0
SPEEDCHECK_X=(); for p in "${EXCLUDE[@]}"; do SPEEDCHECK_X+=("$p"); done
mkdir -p "$WORK"
say() { printf '\n== %s\n' "$*"; }
tree() { echo "$WORK/$1/$TEAM/spec_v1"; }

stage_trees() {
  say "trees: before = $BEFORE, after = $AFTER"
  rm -rf "$WORK/before" "$WORK/after"; mkdir -p "$WORK/before" "$WORK/after"
  local rev="$AFTER"; [ "$AFTER" = worktree ] && rev=HEAD
  git -C "$REPO" archive "$rev" | tar -x -C "$WORK/after"
  [ "$AFTER" = worktree ] && cp "$REPO/$TEAM/spec_v1/clean.py" "$(tree after)/clean.py"
  cp -r "$WORK/after/." "$WORK/before/"
  git -C "$REPO" show "$BEFORE:$TEAM/spec_v1/clean.py" > "$(tree before)/clean.py" || { echo "no clean.py at $BEFORE"; exit 1; }
  sha256sum "$(tree before)/clean.py" "$(tree after)/clean.py" | cut -c1-12,65- | sed 's/^/  /'
  echo "  (before first, after second)"
}

need_trees() { [ -f "$(tree before)/clean.py" ] && [ -f "$(tree after)/clean.py" ] || { echo "run the trees stage first"; exit 1; }; }

stage_speed() {
  need_trees; say "speed: output sha256 and docs/s on $PACKS (excluding ${EXCLUDE[*]})"
  for side in before after; do
    "${PIN[@]}" "$PY" -I "$CHECK" run --clean-dir "$(tree $side)" --packs "$PACKS" --exclude "${EXCLUDE[@]}" \
      --repeat 3 --progress 0 --out "$WORK/$side.json" 2> "$WORK/$side.log" || { echo "$side run failed, see $WORK/$side.log"; FAIL=1; return; }
    echo "  $side done"
  done
  "$PY" -I "$CHECK" compare "$WORK/before.json" "$WORK/after.json" --md "$WORK/speed_table.md" || FAIL=1
}

stage_code() {
  need_trees; say "code: noise check on the 6 code packs, alternating before/after"
  for i in 1 2; do
    for side in before after; do
      "${PIN[@]}" "$PY" -I "$CHECK" run --clean-dir "$(tree $side)" --packs "$PACKS" \
        --only code-cpp code-go code-java code-js-ts code-python code-rust --repeat 5 --progress 0 \
        --out "$WORK/${side}_code_$i.json" 2>/dev/null || { echo "$side round $i failed"; FAIL=1; return; }
    done
    echo "-- round $i"; "$PY" -I "$CHECK" compare "$WORK/before_code_$i.json" "$WORK/after_code_$i.json" || FAIL=1
  done
}

stage_profile() {
  need_trees; say "profile: per-rule time, 500 docs, one core (top 10 rules)"
  mkdir -p "$WORK/profile"
  for pack in en-dclm en-fineweb-edu; do
    for side in before after; do
      "${PIN[@]}" "$PY" -I "$(tree $side)/run_clean.py" --pack "$PACKS/$pack.parquet" \
        --out "$WORK/profile/$side-$pack" 2> "$WORK/profile/$side-$pack.log" >/dev/null
      echo "-- $side $pack"; grep -A11 "slowest rules" "$WORK/profile/$side-$pack.log"
    done
  done
  echo; echo "next slowest rule = the top rule of the AFTER profile that you have not just fixed"
}

stage_harm() {
  need_trees; say "harm: make_harm_tests.py on both trees (a few minutes)"
  mkdir -p "$WORK/harm/before" "$WORK/harm/after"; local pids=()
  for side in before after; do
    "$PY" -I "$(tree $side)/validate/make_harm_tests.py" "$WORK/after" "$PACKS" \
      --out "$WORK/harm/$side/harm_tests.md" --results "$WORK/harm/$side/results" > "$WORK/harm/$side.log" 2>&1 &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p" || { echo "a harm run failed, see $WORK/harm/*.log"; FAIL=1; return; }; done
  echo "-- per-pack result files, ignoring rules_file_sha256 (the clean.py hash):"
  local bad=0
  for f in "$WORK"/harm/before/results/*.json; do
    n="$(basename "$f")"
    if ! diff -q <(grep -v rules_file_sha256 "$f") <(grep -v rules_file_sha256 "$WORK/harm/after/results/$n") >/dev/null; then
      echo "  DIFFERS: $n"; bad=1
    fi
  done
  [ $bad -eq 0 ] && echo "  all result files identical: every gold changed/dropped count and PASS is unchanged" || FAIL=1
  echo "-- harm_tests.md diff (expect only the date and, if the Indic scope changed between the revisions, Indic lines):"
  diff "$WORK/harm/before/harm_tests.md" "$WORK/harm/after/harm_tests.md" | cut -c1-200 || true
}

stage_bigprofile() {
  need_trees; say "bigprofile: after tree, first $SLICE docs of week-2 en-dclm part-00000"
  mkdir -p "$WORK/bigprofile"
  "$PY" -I - "$WEEK2/train/en-dclm/part-00000.parquet" "$WORK/bigprofile/en-dclm.parquet" "$SLICE" <<'EOF'
import sys, pyarrow.parquet as pq
pq.write_table(pq.read_table(sys.argv[1]).slice(0, int(sys.argv[3])), sys.argv[2])
EOF
  "${PIN[@]}" "$PY" -I "$(tree after)/run_clean.py" --pack "$WORK/bigprofile/en-dclm.parquet" \
    --out "$WORK/bigprofile/out" 2> "$WORK/bigprofile/after.log" >/dev/null
  grep -A11 "slowest rules" "$WORK/bigprofile/after.log"
}

stage_big() {
  need_trees; say "big: full week-2 parts, both trees, in the background (about 30 min); logs in $WORK/*_big.log"
  mkdir -p "$WORK/big"
  for pack in en-dclm en-fineweb-edu; do ln -sf "$WEEK2/train/$pack/part-00000.parquet" "$WORK/big/$pack.parquet"; done
  local core=0
  for side in before after; do
    nohup taskset -c $core "$PY" -I "$CHECK" run --clean-dir "$(tree $side)" --packs "$WORK/big" --repeat 1 \
      --out "$WORK/${side}_big.json" > "$WORK/${side}_big.log" 2>&1 &
    core=$((core + 1))
  done
  echo "  started. Watch: tail -f $WORK/before_big.log"
  echo "  when both say 'wrote': $PY -I $CHECK compare $WORK/before_big.json $WORK/after_big.json --md $WORK/speed_table_big.md"
}

for s in "${STAGES[@]}"; do
  case "$s" in
    trees|speed|code|profile|harm|bigprofile|big) "stage_$s";;
    *) echo "unknown stage $s" >&2; exit 2;;
  esac
done
[ $FAIL -eq 0 ] && say "finished, no failures" || { say "finished WITH FAILURES, see above"; exit 1; }
