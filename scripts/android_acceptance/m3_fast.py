"""M3 Android FAST — 复用现有 acceptance 工具链的 self-healing adb。

执行：确保 App 运行 → CDP 探测核心 Consumer 页面（真实 DOM）→ 系统 Back → 逐页截图归档。
设备 serial / package 可由环境变量覆盖；adb 调用全部走 scripts/android_acceptance/adb.py。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "android_acceptance"))

from adb import (  # noqa: E402
    DEFAULT_SERIAL,
    adb,
    adb_binary,
    shell,
    shell_pidof,
    wait_for_device,
)

SERIAL = os.environ.get("PETACCESS_ANDROID_SERIAL", DEFAULT_SERIAL)
PKG = os.environ.get("PETACCESS_ANDROID_PACKAGE", "com.petaccess.map")
SHOT_DIR = Path(
    os.environ.get(
        "PETACCESS_ANDROID_FAST_SCREENSHOT_DIR",
        str(ROOT / "artifacts" / "ui-audit" / "android"),
    )
)
EVIDENCE_ROOT = Path(
    os.environ.get(
        "PETACCESS_ANDROID_EVIDENCE_DIR",
        str(ROOT / "artifacts" / "android_acceptance"),
    )
)
PROBE = ROOT / "scripts" / "android_acceptance" / "cdp_probe.cjs"


def ensure_app() -> str:
    if not wait_for_device(SERIAL, timeout=120):
        raise RuntimeError(f"{SERIAL} not online after 120s")
    pid = shell_pidof(SERIAL, PKG)
    if not pid:
        shell(SERIAL, "am", "start", "-n", f"{PKG}/.MainActivity")
        time.sleep(12)
        pid = shell_pidof(SERIAL, PKG)
    if not pid:
        raise RuntimeError("app not running")
    return pid


def cdp_probe(step: str, retries: int = 4) -> str:
    """Probe the current packaged WebView, healing API-level CDP socket churn.

    Android 36 can recreate/invalidate the WebView devtools target around
    hardware-Back/activity transitions while the PetAccess Activity itself
    remains healthy. Never pin the whole FAST run to the launch-time PID/socket:
    resolve the current process and rebuild the adb forward before every probe.

    This retries transport failures only. A missing app process or a semantic
    page mismatch still fails the caller's product assertion.
    """

    port = 9260
    last_error = "no attempt"
    for attempt in range(retries):
        current_pid = shell_pidof(SERIAL, PKG)
        if not current_pid:
            raise RuntimeError(f"{PKG} process missing before CDP {step}")

        adb("forward", "--remove", f"tcp:{port}", serial=SERIAL, check=False)
        adb(
            "forward",
            f"tcp:{port}",
            f"localabstract:webview_devtools_remote_{current_pid}",
            serial=SERIAL,
        )
        time.sleep(0.75 + attempt * 0.5)

        out = subprocess.run(
            ["node", str(PROBE), str(port), step],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if out.returncode == 0:
            return out.stdout.strip()

        last_error = (out.stderr or out.stdout or "").strip()
        retryable = any(
            marker in last_error.lower()
            for marker in (
                "socket hang up",
                "no debuggable webview page",
                "connection reset",
                "econnreset",
                "econnrefused",
                "uncaught",
            )
        )
        if not retryable or attempt == retries - 1:
            break
        time.sleep(0.75 + attempt)

    raise RuntimeError(f"CDP {step} failed after {retries} attempts: {last_error[-500:]}")


def wait_for_page(pid: str, expected_page: str, timeout_s: float = 30.0) -> str:
    """Wait for the packaged Consumer surface instead of sleeping a fixed boot delay."""

    deadline = time.monotonic() + timeout_s
    last_state = ""
    last_error = ""
    needle = f'"uiPage":"{expected_page}"'
    while time.monotonic() < deadline:
        try:
            state = cdp_probe("snapshot")
            last_state = state
            compact = state.replace(" ", "")
            if needle in compact and '"shell":true' in compact:
                return state
        except Exception as exc:  # noqa: BLE001 - startup may not expose CDP immediately
            last_error = str(exc)
        time.sleep(0.75)
    detail = last_state or last_error or "no CDP state observed"
    raise RuntimeError(f"timed out waiting for {expected_page}: {detail}")


def wait_for_android_back_state(
    pid: str,
    expected: str,
    timeout_s: float = 20.0,
) -> str:
    """Wait for explicit Android Back ownership on the packaged WebView."""

    deadline = time.monotonic() + timeout_s
    last_state = ""
    last_error = ""
    expected_marker = f'"androidBack":"{expected}"'
    while time.monotonic() < deadline:
        try:
            state = cdp_probe("snapshot")
            last_state = state
            compact = state.replace(" ", "")
            if expected_marker in compact:
                return state
            if '"androidBack":"failed"' in compact:
                raise RuntimeError(f"Android Back handler reported failed: {state}")
        except Exception as exc:  # noqa: BLE001 - ownership sync follows router readiness
            last_error = str(exc)
        time.sleep(0.5)
    detail = last_state or last_error or "no Android Back state observed"
    raise RuntimeError(f"timed out waiting for Android Back state={expected} pid={pid}: {detail}")


def wait_for_pid(timeout_s: float = 20.0) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        pid = shell_pidof(SERIAL, PKG)
        if pid:
            return pid
        time.sleep(0.5)
    raise RuntimeError(f"{PKG} process missing after launch")


def android_sdk_level() -> int:
    raw = shell(SERIAL, "getprop", "ro.build.version.sdk", timeout=30).strip()
    try:
        return int(raw)
    except ValueError:
        return 0


def android_navigation_mode() -> str:
    """Return Android's secure navigation_mode when available.

    AOSP convention: 2 = gestural navigation, 1 = two-button, 0 = three-button.
    OEMs may vary, so unknown values intentionally fall back to system keyevent.
    """

    return shell(SERIAL, "settings", "get", "secure", "navigation_mode", timeout=30).strip()


def display_size() -> tuple[int, int]:
    raw = shell(SERIAL, "wm", "size", timeout=30)
    for line in reversed(raw.splitlines()):
        if "size:" not in line:
            continue
        value = line.split("size:", 1)[1].strip()
        if "x" not in value:
            continue
        width, height = value.split("x", 1)
        try:
            return int(width), int(height)
        except ValueError:
            continue
    return 1080, 2400


def trigger_system_back() -> str:
    """Exercise Android's system Back action without injecting app touch input.

    Android 16 / targetSdk 36 no longer dispatches KEYCODE_BACK *to the app* for
    back handling. That does not make adb shell input keyevent KEYCODE_BACK an
    app-level key interception: the shell command asks Android to perform the
    system Back action, which AndroidX OnBackPressedDispatcher bridges to the
    platform predictive-back callback used by Tauri.

    A synthetic input swipe is deliberately not used here. In a headless
    emulator it is merely injected touch input and is not a documented automation
    API for SystemUI's edge-gesture recognizer; treating it as one produced false
    API-36 failures where neither the in-app callback nor back-to-home fired.

    Predictive animation/progress remains a manual device acceptance item. This
    automated gate verifies the committed Back semantics:
    nested Consumer route -> previous route, fresh Home -> leave MainActivity.
    """

    sdk = android_sdk_level()
    mode = android_navigation_mode()
    shell(SERIAL, "input", "keyevent", "KEYCODE_BACK", timeout=30)
    return f"system-back-action sdk={sdk} mode={mode or 'unknown'} dispatcher=androidx"


def screenshot(name: str) -> int:
    # Python 捕获字节再写文件：不经 cmd 重定向（REG-002 的 UTF-16 风险只影响
    # PowerShell 管道；subprocess capture_output 是纯字节，安全）。
    proc = subprocess.run(
        [adb_binary(), "-s", SERIAL, "exec-out", "screencap", "-p"],
        capture_output=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"screencap rc={proc.returncode}: {proc.stderr[-200:]}")
    target = SHOT_DIR / f"{name}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(proc.stdout)
    return target.stat().st_size


def main() -> int:
    results: dict[str, str] = {}
    pid = ensure_app()
    results["app_pid"] = pid

    for step in ("home", "search", "map", "place", "reality", "evidence"):
        try:
            results[step] = cdp_probe(step)
            compact = results[step].replace(" ", "")
            expected_back = "system-root" if step == "home" else "intercepting"
            if f'"androidBack":"{expected_back}"' not in compact:
                raise RuntimeError(
                    f"{step} Android Back ownership mismatch; "
                    f"expected {expected_back}: {results[step]}"
                )
            results[f"shot_{step}"] = f"bytes={screenshot(f'{step}-m3-final')}"
        except Exception as e:  # noqa: BLE001 - report every route and keep going
            results[step] = f"ERROR {e}"

    # Android product navigation contract: after the FAST journey has visited
    # Reality then Evidence, one system Back must return to Reality. A process
    # exit, blank WebView or wrong route is a product failure, not a platform
    # limitation.
    try:
        before_back = cdp_probe("snapshot")
        results["hardware_back_before_evidence"] = before_back
        before_match = re.search(r'"androidBackCallbackCount":(\\d+)', before_back)
        before_count = int(before_match.group(1)) if before_match else 0

        back_method = trigger_system_back()
        results["hardware_back_from_evidence_method"] = back_method
        time.sleep(2)

        back_state = cdp_probe("snapshot")
        results["hardware_back_from_evidence"] = back_state
        after_match = re.search(r'"androidBackCallbackCount":(\\d+)', back_state)
        after_count = int(after_match.group(1)) if after_match else 0
        results["hardware_back_callback_delta"] = str(after_count - before_count)

        compact = back_state.replace(" ", "")
        if after_count <= before_count:
            raise RuntimeError(
                "Android Back callback did not fire for injected system Back; "
                f"before={before_count} after={after_count}; state={back_state}"
            )
        if '"androidBackLastAction":"back"' not in compact:
            raise RuntimeError(f"Android Back callback fired with wrong action: {back_state}")
        if '"uiPage":"reality"' not in compact:
            raise RuntimeError(
                "Android Back callback fired but route did not reach Reality: "
                f"{back_state}"
            )

        results["shot_hardware_back"] = f"bytes={screenshot('hardware-back-reality-m3-final')}"
    except Exception as e:  # noqa: BLE001
        results["hardware_back_from_evidence"] = f"ERROR {e}"

    try:
        results["nav"] = cdp_probe("nav")
        results["shot_nav"] = f"bytes={screenshot('nav-home-m3-final')}"
    except Exception as e:  # noqa: BLE001
        results["nav"] = f"ERROR {e}"

    # Packaged-runtime resilience: the app shell must show a real offline state
    # and clear it after recovery. These events exercise the mounted Tauri
    # WebView, not a desktop-H5 test double.
    try:
        offline_state = cdp_probe("offline")
        results["offline"] = offline_state
        if '"offlineBanner":true' not in offline_state.replace(" ", ""):
            raise RuntimeError(f"offline banner did not appear: {offline_state}")
        results["shot_offline"] = f"bytes={screenshot('offline-banner-m3-final')}"
    except Exception as e:  # noqa: BLE001
        results["offline"] = f"ERROR {e}"

    try:
        recovery_state = cdp_probe("recovery")
        results["recovery"] = recovery_state
        if '"offlineBanner":false' not in recovery_state.replace(" ", ""):
            raise RuntimeError(f"offline banner did not clear: {recovery_state}")
        results["shot_recovery"] = f"bytes={screenshot('online-recovery-m3-final')}"
    except Exception as e:  # noqa: BLE001
        results["recovery"] = f"ERROR {e}"

    # Android lifecycle contract: leaving the activity for Home and reopening
    # it must restore a valid Consumer surface instead of a blank WebView or
    # horizontal-overflow layout. NAV above deliberately leaves us on Home.
    try:
        shell(SERIAL, "input", "keyevent", "KEYCODE_HOME", timeout=30)
        time.sleep(1.5)
        shell(SERIAL, "am", "start", "-n", f"{PKG}/.MainActivity", timeout=30)
        time.sleep(2.5)
        resumed_pid = shell_pidof(SERIAL, PKG)
        if not resumed_pid:
            raise RuntimeError("app process missing after activity resume")
        pid = resumed_pid
        resumed_state = cdp_probe("snapshot")
        results["activity_resume"] = resumed_state
        compact = resumed_state.replace(" ", "")
        if '"shell":true' not in compact:
            raise RuntimeError(f"Consumer shell missing after activity resume: {resumed_state}")
        if '"horizontalOverflow":true' in compact:
            raise RuntimeError(f"horizontal overflow after activity resume: {resumed_state}")
        results["shot_activity_resume"] = f"bytes={screenshot('activity-resume-m3-final')}"
    except Exception as e:  # noqa: BLE001
        results["activity_resume"] = f"ERROR {e}"

    # Root navigation contract: a fresh Home launch has no Consumer history.
    # At a fresh Home root PetAccess must expose system-root ownership, meaning
    # there is no app Back listener consuming predictive back. One system Back
    # must therefore leave the PetAccess activity through Android's native
    # back-to-home path. Do not capture the launcher screen: this gate may also
    # run on a user's physical device.
    try:
        shell(SERIAL, "am", "force-stop", PKG, timeout=30)
        time.sleep(1)
        shell(SERIAL, "am", "start", "-n", f"{PKG}/.MainActivity", timeout=30)
        root_pid = wait_for_pid(timeout_s=20)
        root_state = wait_for_page(root_pid, "home", timeout_s=30)
        results["fresh_home_before_back"] = root_state
        back_ready_state = wait_for_android_back_state(
            root_pid,
            "system-root",
            timeout_s=20,
        )
        results["fresh_home_back_ready"] = back_ready_state

        back_method = trigger_system_back()
        results["hardware_back_from_home_method"] = back_method

        deadline = time.monotonic() + 10
        resumed_lines: list[str] = []
        while time.monotonic() < deadline:
            activities = shell(SERIAL, "dumpsys", "activity", "activities", timeout=30)
            resumed_lines = [
                line.strip()
                for line in activities.splitlines()
                if "ResumedActivity" in line or "topResumedActivity" in line
            ]
            if not any(PKG in line for line in resumed_lines):
                break
            time.sleep(0.5)

        if any(PKG in line for line in resumed_lines):
            raise RuntimeError("Home Back left PetAccess resumed: " + " | ".join(resumed_lines[:4]))
        results["hardware_back_from_home"] = "PASS activity_finished; resumed=" + (
            " | ".join(resumed_lines[:4]) if resumed_lines else "(none reported)"
        )
    except Exception as e:  # noqa: BLE001
        results["hardware_back_from_home"] = f"ERROR {e}"

    failures = {
        key: value
        for key, value in results.items()
        if isinstance(value, str) and value.startswith("ERROR ")
    }
    results["result"] = "FAIL" if failures else "PASS"
    results["failure_count"] = len(failures)
    payload = json.dumps(results, ensure_ascii=False, indent=1)
    runtime_dir = EVIDENCE_ROOT / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "m3_fast.json").write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
