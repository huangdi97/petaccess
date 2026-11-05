"""Install an Android Preview APK on a USB device and run the canonical FAST gate.

Usage:
    python scripts/android_acceptance/preview_usb_smoke.py \
        --apk path/to/PetAccess-preview-usb-device-<sha>-debug.apk \
        --serial <adb-serial>

Preconditions:
- the PetAccess API is listening on host 127.0.0.1:8000;
- the device is authorized in adb;
- the APK is the isolated debug Preview package (com.petaccess.map.preview).

This helper never touches the signed release package. It preserves Preview data when
possible; only an incompatible debug signature may trigger uninstall/reinstall of the
isolated Preview package.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANDROID_TOOLS = ROOT / "scripts" / "android_acceptance"
sys.path.insert(0, str(ANDROID_TOOLS))

from adb import adb, shell, wait_for_device  # noqa: E402

PREVIEW_PACKAGE = "com.petaccess.map.preview"
DEFAULT_API_PORT = 8000


def _assert_host_api_ready(port: int) -> None:
    checks: tuple[tuple[str, str, object], ...] = (
        ("/health", "status", "ok"),
        ("/api/v1/ping", "pong", True),
    )
    for route, key, expected in checks:
        url = f"http://127.0.0.1:{port}{route}"
        try:
            with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310
                if response.status != 200:
                    raise SystemExit(f"PetAccess API check failed: {url} -> HTTP {response.status}")
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise SystemExit(f"PetAccess API check failed: {url}: {exc}") from exc
        if payload.get(key) != expected:
            raise SystemExit(
                f"PetAccess API check failed: {url} expected {key}={expected!r}, got {payload!r}"
            )


def _resolve_aapt() -> Path:
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    candidates: list[Path] = []
    if sdk:
        build_tools = Path(sdk) / "build-tools"
        if build_tools.is_dir():
            executable = "aapt.exe" if os.name == "nt" else "aapt"
            candidates.extend(
                version / executable
                for version in sorted(build_tools.iterdir(), reverse=True)
                if version.is_dir()
            )
    candidates.append(
        Path(r"C:\Users\Kaiser\AppData\Local\Android\Sdk\build-tools\36.0.0\aapt.exe")
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit("aapt not found; set ANDROID_HOME/ANDROID_SDK_ROOT to the Android SDK")


def _apk_package(apk: Path) -> str:
    proc = subprocess.run(
        [str(_resolve_aapt()), "dump", "badging", str(apk)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise SystemExit(f"aapt failed for {apk}: {(proc.stderr or proc.stdout)[-600:]}")
    match = re.search(r"package: name='([^']+)'", proc.stdout)
    if not match:
        raise SystemExit(f"could not read package id from APK: {apk}")
    return match.group(1)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install PetAccess Preview over USB, reverse the API port, then run Android FAST."
        )
    )
    parser.add_argument("--apk", type=Path, required=True, help="Preview debug APK path")
    parser.add_argument(
        "--serial",
        default=os.environ.get("PETACCESS_ANDROID_SERIAL"),
        help="adb device serial; required unless PETACCESS_ANDROID_SERIAL is set",
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=DEFAULT_API_PORT,
        help=f"host/device loopback API port (default: {DEFAULT_API_PORT})",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="reuse an already-installed Preview package",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    apk = args.apk.resolve()
    serial = args.serial

    if not serial:
        raise SystemExit("--serial is required (or set PETACCESS_ANDROID_SERIAL)")
    if not apk.is_file():
        raise SystemExit(f"APK not found: {apk}")
    package_name = _apk_package(apk)
    if package_name != PREVIEW_PACKAGE:
        raise SystemExit(
            f"refusing to install {package_name!r}; expected isolated Preview package "
            f"{PREVIEW_PACKAGE!r}"
        )
    _assert_host_api_ready(args.api_port)
    if not wait_for_device(serial, timeout=120):
        raise SystemExit(f"adb device not ready: {serial}")

    if not args.skip_install:
        print(f"[preview] installing {apk.name} on {serial}")
        install_out = adb(
            "install",
            "-r",
            str(apk),
            serial=serial,
            timeout=300,
            check=False,
        )
        if "Success" not in install_out and "INSTALL_FAILED_UPDATE_INCOMPATIBLE" in install_out:
            print("[preview] debug signature changed; reinstalling Preview package only")
            uninstall_out = adb("uninstall", PREVIEW_PACKAGE, serial=serial, check=False)
            if "Success" not in uninstall_out and "Unknown package" not in uninstall_out:
                raise SystemExit(f"Preview uninstall failed: {uninstall_out[-600:]}")
            install_out = adb("install", str(apk), serial=serial, timeout=300, check=False)
        if "Success" not in install_out:
            raise SystemExit(f"APK install did not report Success: {install_out[-600:]}")

    package_path = shell(serial, "pm", "path", PREVIEW_PACKAGE).strip()
    if not package_path.startswith("package:"):
        raise SystemExit(
            f"{PREVIEW_PACKAGE} is not installed after preview install; got: {package_path!r}"
        )

    port = str(args.api_port)
    adb("reverse", f"tcp:{port}", f"tcp:{port}", serial=serial)
    reverse_list = adb("reverse", "--list", serial=serial)
    if f"tcp:{port} tcp:{port}" not in reverse_list:
        raise SystemExit(f"adb reverse tcp:{port} was not established: {reverse_list}")

    env = os.environ.copy()
    env["PETACCESS_ANDROID_PACKAGE"] = PREVIEW_PACKAGE
    env["PETACCESS_ANDROID_SERIAL"] = serial

    fast = ANDROID_TOOLS / "m3_fast.py"
    print(
        f"[preview] running FAST for package={PREVIEW_PACKAGE} serial={serial} api=127.0.0.1:{port}"
    )
    result = subprocess.run(
        [sys.executable, str(fast)],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("[preview] install + adb reverse + Android FAST = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
