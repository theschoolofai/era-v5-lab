#!/bin/bash
# Back up (and test-restore) the Slurm accounting database (ADR 0002 §1).
#
# In simple words: the accounting database holds every account, budget, fair-share number and job record.
# If it is lost, budgets and the GPU-hour history are gone. We dump it every day, and a backup only counts
# once it has been restored into a scratch database and has the same tables.
#
#   backup_db.sh <dir>                    write <dir>/slurm_acct_db-<UTC time>.sql.gz
#   backup_db.sh --verify-latest <dir>    restore the newest dump into a scratch DB, compare, print JSON
# Needs DB_ROOT_PASSWORD (EC2: from AWS Secrets Manager; Docker test: the test-only value).
set -euo pipefail
HOST="${DB_HOST:-mariadb}"
DB="${DB_NAME:-slurm_acct_db}"
M=(-h "$HOST" -u root "-p${DB_ROOT_PASSWORD:?DB_ROOT_PASSWORD is needed}")

if [[ "${1:-}" == "--verify-latest" ]]; then
  dir="$2"
  f="$(ls -1t "$dir"/"$DB"-*.sql.gz | head -1)"
  scratch="${DB}_restore_test"
  mariadb "${M[@]}" -e "DROP DATABASE IF EXISTS $scratch; CREATE DATABASE $scratch;"
  gunzip -c "$f" | mariadb "${M[@]}" "$scratch"
  q="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema="
  orig="$(mariadb "${M[@]}" -N -e "$q'$DB'")"
  rest="$(mariadb "${M[@]}" -N -e "$q'$scratch'")"
  jobs="$(mariadb "${M[@]}" -N -e "SELECT COUNT(*) FROM $scratch.v5sim_job_table" 2>/dev/null || echo 0)"
  mariadb "${M[@]}" -e "DROP DATABASE $scratch;"
  ok=false; [[ "$orig" == "$rest" && "$orig" -gt 0 ]] && ok=true
  printf '{"ok": %s, "file": "%s", "bytes": %s, "tables": %s, "tables_restored": %s, "job_rows_restored": %s}\n' \
    "$ok" "$(basename "$f")" "$(stat -c %s "$f")" "$orig" "$rest" "$jobs"
  exit 0
fi

dir="${1:?backup dir}"
mkdir -p "$dir"
out="$dir/$DB-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
mariadb-dump "${M[@]}" --single-transaction --routines "$DB" | gzip > "$out"
echo "wrote $out"
