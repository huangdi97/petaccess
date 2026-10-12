"""M3 Android FAST — 复用现有 acceptance 工具链的 self-healing adb。

执行：确保 App 运行 → CDP 探测核心 Consumer 页面（真实 DOM）→ 系统 Back → 逐页截图归档。
设备 serial / package 可由环境变量覆盖；adb 调用全部走 scripts/android_acceptance/adb.py。
"""

from __future__ import annotations

import json
import os
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


def cdp_probe(pid: str, step: str) -> str:
    port = 9260
    adb("forward", "--remove", f"tcp:{port}", serial=SERIAL, check=False)
    adb("forward", f"tcp:{port}", f"localabstract:webview_devtools_remote_{pid}", serial=SERIAL)
    time.sleep(1)
    out = subprocess.run(
        ["node", str(PROBE), str(port), step],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if out.returncode != 0:
        raise RuntimeError(
            f"CDP {step} failed rc={out.returncode}: {(out.stderr or out.stdout)[-500:]}"
        )
    return out.stdout.strip()


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
            results[step] = cdp_probe(pid, step)
            results[f"shot_{step}"] = f"bytes={screenshot(f'{step}-m3-final')}"
        except Exception as e:  # noqa: BLE001 - report every route and keep going
            results[step] = f"ERROR {e}"

    # Android product navigation contract: after the FAST journey has visited
    # Reality then Evidence, one system Back must return to Reality. A process
    # exit, blank WebView or wrong route is a product failure, not a platform
    # limitation.
    try:
        shell(SERIAL, "input", "keyevent", "KEYCODE_BACK", timeout=30)
        time.sleep(2)
        back_state = cdp_probe(pid, "snapshot")
        results["hardware_back_from_evidence"] = back_state
        if '"uiPage":"reality"' not in back_state.replace(" ", ""):
            raise RuntimeError(f"expected Reality after Back, got: {back_state}")
        results["shot_hardware_back"] = f"bytes={screenshot('hardware-back-reality-m3-final')}"
    except Exception as e:  # noqa: BLE001
        results["hardware_back_from_evidence"] = f"ERROR {e}"

    try:
        results["nav"] = cdp_probe(pid, "nav")
        results["shot_nav"] = f"bytes={screenshot('nav-home-m3-final')}"
    except Exception as e:  # noqa: BLE001
        results["nav"] = f"ERROR {e}"

    failures = {
        key: value
        for key, value in results.items()
        if isinstance(value, str) and value.startswith("ERROR ")
    }
    results["result"] = "FAIL" if failures else "PASS"
    results["failure_count"] = len(failures)
    print(json.dumps(results, ensure_ascii=False, indent=1))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
