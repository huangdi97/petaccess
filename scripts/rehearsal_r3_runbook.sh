#!/usr/bin/env bash
# Publish rehearsal runbook — Batch 01 of R2-FINAL-R3.
#
# Two phases, because the clone cannot be taken while the API holds a connection
# to the source database (CREATE DATABASE ... TEMPLATE refuses a busy source).
#
#   phase0  stop the API, clone petaccess -> rehearsal DB, (re)print the guard
#   phase1  API already running against the rehearsal DB: execute the batch,
#           prove it is idempotent, then run the verification drills
#
# Every step writes its evidence into artifacts/ so the report can cite files
# rather than a terminal transcript.
#
# Usage:
#   bash scripts/rehearsal_r3_runbook.sh phase0
#   # start: .venv/Scripts/python.exe scripts/dev_api_server.py --db-name \
#   #        petaccess_publish_rehearsal_r3 --port 8010
#   bash scripts/rehearsal_r3_runbook.sh phase1
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

PY="${PY:-.venv/Scripts/python.exe}"
DB="${DB:-petaccess_publish_rehearsal_r3}"
API="${API:-http://127.0.0.1:8010}"
MANIFEST="${MANIFEST:-docs/governance/publish_batches/R2_FINAL_R3_BATCH_01.json}"
#: --max-approve is a second-layer safety cap over the manifest, never the
#: selection — but it must be at least the manifest's size or the run refuses for
#: a reason that has nothing to do with the batch's integrity.
MAX_APPROVE="${MAX_APPROVE:-12}"
ART="${ART:-artifacts}"

mkdir -p "$ART"

phase0() {
  echo "== phase0: rebuild the rehearsal database =="
  if curl -s -m 2 "$API/api/v1/ping" >/dev/null 2>&1; then
    echo "REFUSED — something is still serving on $API." >&2
    echo "Stop it first; the clone needs an exclusive source database." >&2
    exit 4
  fi
  "$PY" scripts/rehearsal_db.py --db-name "$DB" --source petaccess \
    --clone --force-terminate --confirm --json | tee "$ART/rehearsal_db_fingerprint.json"
}

phase1() {
  echo "== phase1: execute the batch on the rehearsal database =="
  for _ in $(seq 1 15); do
    curl -s -m 2 "$API/api/v1/ping" | grep -q pong && break
    sleep 2
  done
  curl -s -m 2 "$API/api/v1/ping" | grep -q pong || { echo "API not up on $API" >&2; exit 4; }

  local token
  token="$("$PY" - "$API" <<'PY'
import sys, httpx
base = sys.argv[1]
r = httpx.post(f"{base}/api/v1/auth/login",
               json={"email": "admin@demo-petaccess.com", "password": "admin12345"},
               timeout=20.0, trust_env=False)
r.raise_for_status()
print(r.json()["access_token"])
PY
)"

  echo "-- 1/3 execute (--max-approve $MAX_APPROVE over $MANIFEST) --"
  "$PY" scripts/publish_reviewed_r1.py --execute --batch-file "$MANIFEST" \
    --max-approve "$MAX_APPROVE" --database-name "$DB" --reviewer huangdi97 --token "$token" --json \
    --snapshot-out "$ART/rehearsal_execute_r3_receipt.json" \
    > "$ART/rehearsal_execute_r3.json" 2>&1
  grep -E '^(PREPUBLISH_PASS|PREPUBLISH_BLOCKED|ACCESS_RULE_CREATE_COUNT|RULE_EXCEPTION_CREATE_COUNT|NOOP_COUNT|BLOCKED_COUNT)' \
    "$ART/rehearsal_execute_r3.json"

  echo "-- 2/3 idempotency (expect zero new writes) --"
  "$PY" scripts/publish_reviewed_r1.py --execute --batch-file "$MANIFEST" \
    --max-approve "$MAX_APPROVE" --database-name "$DB" --reviewer huangdi97 --token "$token" \
    --snapshot-out "$ART/rehearsal_idempotency_receipt.json" \
    > "$ART/rehearsal_idempotency_run2.txt" 2>&1
  grep -E '^(NOOP_COUNT|ACCESS_RULE_CREATE_COUNT|RULE_EXCEPTION_CREATE_COUNT|SELF_SUPERSEDE|DUPLICATE_PLAN)' \
    "$ART/rehearsal_idempotency_run2.txt"

  echo "-- 3/3 verification drills (linkage / resolver / rollback / supersession / watch) --"
  "$PY" scripts/verify_publish_r3.py --db-name "$DB" --api "$API" --batch-file "$MANIFEST" \
    --out "$ART/publish_rehearsal_r3_verification.json"
}

case "${1:-}" in
  phase0) phase0 ;;
  phase1) phase1 ;;
  *) echo "usage: $0 phase0|phase1" >&2; exit 2 ;;
esac
