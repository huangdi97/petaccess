"""Install an Android Preview APK on a USB device and run the canonical FAST gate.

Usage:
    python scripts/android_acceptance/preview_usb_smoke.py \
        --apk path/to/PetAccess-preview-usb-device-<sha>-debug.apk \
        --serial <adb-serial>

Preconditions:
- the PetAccess API is listening on host 127.0.0.1:8000;
- the device is authorized in adb;
- the APK is the isolated debug Preview package (com.petaccess.map.preview).

This helper never touches the signed release package and never uninstalls user data.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANDROID_TOOLS = ROOT / "scripts" / "android_acceptance"
sys.path.insert(0, str(ANDROID_TOOLS))

from adb import adb, shell, wait_for_device  # noqa: E402

PREVIEW_PACKAGE = "com.petaccess.map.preview"
DEFAULT_API_PORT = 8000


def _host_port_ready(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install PetAccess Preview over USB, reverse the API port, "
            "then run Android FAST."
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
    if not _host_port_ready(args.api_port):
        raise SystemExit(
            f"PetAccess API is not listening on host 127.0.0.1:{args.api_port}; "
            "start the API before USB Preview validation."
        )
    if not wait_for_device(serial, timeout=120):
        raise SystemExit(f"adb device not ready: {serial}")

    if not args.skip_install:
        print(f"[preview] installing {apk.name} on {serial}")
        install_out = adb("install", "-r", str(apk), serial=serial, timeout=300)
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
        f"[preview] running FAST for package={PREVIEW_PACKAGE} serial={serial} "
        f"api=127.0.0.1:{port}"
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
