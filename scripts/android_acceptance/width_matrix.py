"""Packaged Android responsive-width acceptance.

Runs against the already-installed Preview APK on one owned emulator. Each
profile changes Android's logical display, restarts the packaged Tauri app,
probes four high-risk Consumer surfaces through CDP, captures screenshots, and
requires zero horizontal overflow / safe-area overlap.

The original display configuration is always restored in the final cleanup.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "android_acceptance"))

from adb import DEFAULT_SERIAL, adb, adb_binary, shell, shell_pidof, wait_for_device  # noqa: E402

SERIAL = os.environ.get("PETACCESS_ANDROID_SERIAL", DEFAULT_SERIAL)
PACKAGE = os.environ.get("PETACCESS_ANDROID_PACKAGE", "com.petaccess.map.preview")
EVIDENCE_ROOT = Path(
    os.environ.get(
        "PETACCESS_ANDROID_EVIDENCE_DIR",
        str(ROOT / "artifacts" / "android_acceptance"),
    )
)
PROBE = ROOT / "scripts" / "android_acceptance" / "cdp_probe.cjs"
OUT = EVIDENCE_ROOT / "runtime" / "width_matrix.json"
SHOT_DIR = EVIDENCE_ROOT / "screenshots" / "width-matrix"

PROFILES = [
    {"id": "phone-m", "mode": "reset"},
    {"id": "phone-s", "width_px": 990, "height_px": 2200, "density": 440},
    {"id": "phone-l", "width_px": 1183, "height_px": 2563, "density": 440},
    {
        "id": "phone-landscape-compact-height",
        "width_px": 2200,
        "height_px": 990,
        "density": 440,
    },
    {"id": "tablet", "width_px": 2200, "height_px": 3520, "density": 440},
]
ACTIONS = ("home", "search", "map", "place")


def _wait_pid(timeout_s: float = 30.0) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        pid = shell_pidof(SERIAL, PACKAGE)
        if pid:
            return pid
        time.sleep(0.5)
    raise RuntimeError(f"{PACKAGE} process did not start")


def _restart_app() -> str:
    shell(SERIAL, "am", "force-stop", PACKAGE, timeout=30)
    time.sleep(0.75)
    shell(SERIAL, "am", "start", "-n", f"{PACKAGE}/.MainActivity", timeout=30)
    pid = _wait_pid()
    time.sleep(2)
    return pid


def _set_profile(profile: dict) -> None:
    if profile.get("mode") == "reset":
        shell(SERIAL, "wm", "size", "reset", timeout=30)
        shell(SERIAL, "wm", "density", "reset", timeout=30)
    else:
        shell(
            SERIAL,
            "wm",
            "size",
            f"{profile['width_px']}x{profile['height_px']}",
            timeout=30,
        )
        shell(SERIAL, "wm", "density", str(profile["density"]), timeout=30)
    time.sleep(2)


def _probe(pid: str, action: str) -> dict:
    port = 9270
    adb("forward", "--remove", f"tcp:{port}", serial=SERIAL, check=False)
    adb(
        "forward",
        f"tcp:{port}",
        f"localabstract:webview_devtools_remote_{pid}",
        serial=SERIAL,
    )
    time.sleep(0.75)
    proc = subprocess.run(
        ["node", str(PROBE), str(port), action],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{action} probe failed rc={proc.returncode}: {(proc.stderr or proc.stdout)[-700:]}"
        )
    line = (proc.stdout or "").strip().splitlines()[-1]
    brace = line.find("{")
    if brace < 0:
        raise RuntimeError(f"{action} probe returned no JSON: {line[-500:]}")
    return json.loads(line[brace:])


def _screenshot(name: str) -> Path:
    proc = subprocess.run(
        [adb_binary(), "-s", SERIAL, "exec-out", "screencap", "-p"],
        capture_output=True,
        timeout=120,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"screencap failed rc={proc.returncode}: {proc.stderr[-300:]}")
    target = SHOT_DIR / f"{name}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(proc.stdout)
    if target.stat().st_size <= 0:
        raise RuntimeError(f"empty screenshot: {target}")
    return target


def main() -> int:
    if not wait_for_device(SERIAL, timeout=120):
        raise RuntimeError(f"{SERIAL} is not online")

    rows: list[dict] = []
    failures: list[str] = []
    try:
        for profile in PROFILES:
            profile_id = str(profile["id"])
            _set_profile(profile)
            pid = _restart_app()

            page_rows: list[dict] = []
            for action in ACTIONS:
                try:
                    state = _probe(pid, action)
                    shot = _screenshot(f"{profile_id}__{action}")
                    ok = (
                        state.get("shell") is True
                        and state.get("horizontalOverflow") is False
                        and state.get("safeAreaOverlap") is False
                        and state.get("safeAreaBottomOverlap") is False
                    )
                    error = None if ok else f"invalid runtime geometry: {state}"
                except Exception as exc:  # noqa: BLE001 - aggregate matrix failures
                    state = {}
                    shot = None
                    ok = False
                    error = str(exc)

                page_rows.append(
                    {
                        "action": action,
                        "ok": ok,
                        "error": error,
                        "ui_page": state.get("uiPage"),
                        "ui_state": state.get("uiState"),
                        "viewport_width": state.get("viewportWidth"),
                        "scroll_width": state.get("scrollWidth"),
                        "horizontal_overflow": state.get("horizontalOverflow"),
                        "safe_area_top": state.get("safeAreaTop"),
                        "safe_area_bottom": state.get("safeAreaBottom"),
                        "content_top": state.get("contentTop"),
                        "safe_area_overlap": state.get("safeAreaOverlap"),
                        "tabbar_item_bottom": state.get("tabbarItemBottom"),
                        "bottom_safe_limit": state.get("bottomSafeLimit"),
                        "safe_area_bottom_overlap": state.get("safeAreaBottomOverlap"),
                        "ime_state": state.get("imeState"),
                        "screenshot": str(shot) if shot else None,
                    }
                )
                if not ok:
                    failures.append(f"{profile_id}/{action}: {error}")

            rows.append(
                {
                    "profile": profile_id,
                    "requested": profile,
                    "wm_size": shell(SERIAL, "wm", "size").strip(),
                    "wm_density": shell(SERIAL, "wm", "density").strip(),
                    "pages": page_rows,
                    "ok": all(item["ok"] for item in page_rows),
                }
            )
    finally:
        shell(SERIAL, "wm", "size", "reset", timeout=30)
        shell(SERIAL, "wm", "density", "reset", timeout=30)
        time.sleep(2)
        with contextlib.suppress(Exception):
            _restart_app()

    payload = {
        "result": "FAIL" if failures else "PASS",
        "required_profiles": [profile["id"] for profile in PROFILES],
        "required_actions": list(ACTIONS),
        "profiles": rows,
        "failure_count": len(failures),
        "failures": failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
