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

PID="$(adb -s "$SERIAL" shell pidof "$PACKAGE" | tr -d '\r\n')"
if [[ -z "$PID" ]]; then
  echo "Preview process is not running after FAST"
  exit 1
fi

adb -s "$SERIAL" forward --remove tcp:9223 >/dev/null 2>&1 || true
adb -s "$SERIAL" forward tcp:9223 "localabstract:webview_devtools_remote_$PID"
sleep 2

node scripts/android_acceptance/cdp_journey.cjs
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
assert len(journey["routes"]) >= 21, len(journey["routes"])
assert coverage["required_router_pages"] == 19, coverage
assert coverage["observed_router_pages"] >= 19, coverage
print(f"Android Preview semantic journey: {len(journey['routes'])}/{len(journey['routes'])} PASS")
PY

adb -s "$SERIAL" shell dumpsys package "$PACKAGE" > "$EVIDENCE_ROOT/runtime/package-dump.txt"
adb -s "$SERIAL" logcat -d -t 3000 > "$EVIDENCE_ROOT/logs/logcat-tail.txt"

echo "ANDROID_PREVIEW_EMULATOR_SMOKE=PASS"
