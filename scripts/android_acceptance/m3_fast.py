"""M3 Android FAST — 复用现有 acceptance 工具链的 self-healing adb。

执行：确保 App 运行 → CDP 探测 Home/Search/Nav（真实 DOM）→ 截图归档。
uses own serial emulator-5556；adb 调用全部走 scripts/android_acceptance/adb.py。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "android_acceptance"))

from adb import (  # noqa: E402
    adb,
    adb_binary,
    shell,
    shell_pidof,
    wait_for_device,
)

SERIAL = "emulator-5556"
PKG = "com.petaccess.map"
SHOT_DIR = ROOT / "artifacts" / "ui-audit" / "android"
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

    for step in ("home", "search", "nav"):
        try:
            results[step] = cdp_probe(pid, step)
        except Exception as e:  # noqa: BLE001 - report, keep going
            results[step] = f"ERROR {e}"

    for name in ("home-m3-final", "search-m3-final"):
        try:
            results[f"shot_{name}"] = f"bytes={screenshot(name)}"
        except Exception as e:  # noqa: BLE001
            results[f"shot_{name}"] = f"ERROR {e}"

    print(json.dumps(results, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
