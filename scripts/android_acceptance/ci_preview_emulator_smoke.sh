#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

APK_DIR="${PREVIEW_APK_DIR:-$ROOT/preview-apk}"
PACKAGE="${PETACCESS_ANDROID_PACKAGE:-com.petaccess.map.preview}"
EVIDENCE_ROOT="${PETACCESS_ANDROID_EVIDENCE_DIR:-$ROOT/artifacts/android-preview-runtime}"

SERIAL="${PETACCESS_ANDROID_SERIAL:-}"
if [[ -z "$SERIAL" ]]; then
  SERIAL="$(adb devices | awk '$2 == "device" && $1 ~ /^emulator-/ { print $1; exit }')"
fi
if [[ -z "$SERIAL" ]]; then
  echo "No online Android emulator found"
  adb devices -l || true
  exit 1
fi

export PETACCESS_ANDROID_SERIAL="$SERIAL"
export PETACCESS_ANDROID_PACKAGE="$PACKAGE"
export PETACCESS_ANDROID_EVIDENCE_DIR="$EVIDENCE_ROOT"
export PETACCESS_ANDROID_FAST_SCREENSHOT_DIR="$EVIDENCE_ROOT/screenshots/fast"

mkdir -p "$EVIDENCE_ROOT/runtime" "$EVIDENCE_ROOT/screenshots" "$EVIDENCE_ROOT/logs"

APK="$(find "$APK_DIR" -type f -name '*.apk' | head -1)"
if [[ -z "$APK" || ! -f "$APK" ]]; then
  echo "Preview APK not found under $APK_DIR"
  find "$APK_DIR" -maxdepth 3 -type f -print || true
  exit 1
fi

echo "Android CI runtime: serial=$SERIAL package=$PACKAGE apk=$APK"
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/v1/ping

adb -s "$SERIAL" install -r "$APK"
adb -s "$SERIAL" shell pm path "$PACKAGE" | tee "$EVIDENCE_ROOT/runtime/package-path.txt"
grep -q '^package:' "$EVIDENCE_ROOT/runtime/package-path.txt"

python scripts/android_acceptance/m3_fast.py

# FAST intentionally finishes MainActivity when it verifies Home -> system Back.
# Raw adb can transiently fail while the emulator/5037 daemon is settling, so
# the post-FAST relaunch must be self-healing too. Do not let one am-start or
# pidof exit code terminate this set -e script before the semantic readiness
# gate has a chance to decide the result.
CDP_READY=0
STABLE_PID=""
STABLE_COUNT=0
READY_LOG="$EVIDENCE_ROOT/runtime/post-fast-cdp-ready.log"
: > "$READY_LOG"

# /json becoming reachable is not enough: after Activity recreation the old
# WebView target can remain listed briefly while its websocket is already
# closing. Require two consecutive real Runtime.evaluate snapshots from the
# same process before launching the full journey. When the process is absent,
# actively retry MainActivity launch rather than trusting one adb command.
for _ in $(seq 1 60); do
  PID="$(adb -s "$SERIAL" shell pidof "$PACKAGE" 2>/dev/null | tr -d '\r\n' || true)"
  if [[ -z "$PID" ]]; then
    adb -s "$SERIAL" shell am start -n "$PACKAGE/.MainActivity" >>"$READY_LOG" 2>&1 || true
    sleep 0.75
    continue
  fi

  adb -s "$SERIAL" forward --remove tcp:9223 >/dev/null 2>&1 || true
  if adb -s "$SERIAL" forward tcp:9223 "localabstract:webview_devtools_remote_$PID" >/dev/null 2>&1; then
    if node scripts/android_acceptance/cdp_probe.cjs 9223 snapshot >>"$READY_LOG" 2>&1; then
      if [[ "$PID" == "$STABLE_PID" ]]; then
        STABLE_COUNT=$((STABLE_COUNT + 1))
      else
        STABLE_PID="$PID"
        STABLE_COUNT=1
      fi
      if [[ "$STABLE_COUNT" -ge 2 ]]; then
        CDP_READY=1
        break
      fi
    else
      STABLE_COUNT=0
      STABLE_PID="$PID"
    fi
  fi
  sleep 0.75
done

if [[ "$CDP_READY" != "1" ]]; then
  echo "Preview WebView did not reach two stable CDP snapshots after FAST relaunch"
  tail -80 "$READY_LOG" || true
  adb -s "$SERIAL" shell dumpsys activity activities | tail -120 || true
  exit 1
fi

AUTH_TOKEN="$(python - <<'PY'
import json
import time
import urllib.request

base = "http://127.0.0.1:8000/api/v1"
email = f"android-runtime-{int(time.time() * 1000)}@example.com"
password = "passw0rd123"


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"{path} -> HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


post(
    "/auth/register",
    {"display_name": "Android Runtime", "email": email, "password": password},
)
token = post("/auth/login", {"email": email, "password": password}).get("access_token")
if not token:
    raise RuntimeError("Android runtime login returned no access_token")
print(token)
PY
)"
if [[ -z "$AUTH_TOKEN" ]]; then
  echo "Failed to create Android runtime auth token"
  exit 1
fi
export PETACCESS_ANDROID_AUTH_TOKEN="$AUTH_TOKEN"

node scripts/android_acceptance/cdp_journey.cjs
python scripts/android_acceptance/width_matrix.py
python scripts/android_acceptance/coverage_matrix.py
python scripts/android_acceptance/build_preview_review_board.py

python - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["PETACCESS_ANDROID_EVIDENCE_DIR"])
coverage = json.loads((root / "coverage_matrix.json").read_text(encoding="utf-8"))
journey = json.loads(
    (root / "runtime" / "cdp_journey_playwright.json").read_text(encoding="utf-8")
)
assert coverage["matrix"]["Routes"] == "COVERED", coverage
assert journey["result"] == "PASS", journey
assert len(journey["routes"]) >= 28, len(journey["routes"])
assert journey["authenticatedSweepRequested"] is True, journey
assert journey["authenticatedCases"] >= 7, journey
assert coverage["required_router_pages"] == 19, coverage
assert coverage["observed_router_pages"] >= 19, coverage
assert coverage["matrix"]["Authenticated States"] == "COVERED", coverage
assert coverage["matrix"]["Visual"] == "COVERED", coverage
assert coverage["matrix"]["Governed Media"] == "COVERED", coverage
assert coverage["governed_media"]["decoded"] is True, coverage
assert set(coverage["observed_authenticated_case_ids"]) >= set(
    coverage["required_authenticated_case_ids"]
), coverage
print(
    "Android Preview semantic journey: "
    f"{len(journey['routes'])}/{len(journey['routes'])} PASS "
    f"(authenticated={journey['authenticatedCases']})"
)
PY

adb -s "$SERIAL" shell dumpsys package "$PACKAGE" > "$EVIDENCE_ROOT/runtime/package-dump.txt"
adb -s "$SERIAL" logcat -d -t 3000 > "$EVIDENCE_ROOT/logs/logcat-tail.txt"

echo "ANDROID_PREVIEW_EMULATOR_SMOKE=PASS"
