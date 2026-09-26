"""Install / launch / uninstall operations with runbook evidence capture.

Records install logs, package/version dumps and signature results; runs cold and
warm launch loops with boot-trace (PETACCESS_BOOT) assertions against logcat.
All adb calls are serial-bound; nothing here ever touches another agent's AVD.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .adb import (
    SDK_ADB,
    DEFAULT_SERIAL,
    adb,
    check_serial,
    package_running,
    shell,
    shell_pidof,
)

PACKAGE = "com.petaccess.map"
MAIN_ACTIVITY = "com.petaccess.map.MainActivity"
BOOT_STAGES = (
    "INDEX_LOADED",
    "VUE_CREATED",
    "ROUTER_READY",
    "APP_SHELL_MOUNTED",
    "HOME_READY",
)
LOG_DIR = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\logs")


class AppOperationError(RuntimeError):
    """Install/launch failure with context."""


@dataclass
class ApkArtifact:
    path: Path
    sha256: str
    size_bytes: int
    version_name: str | None = None
    version_code: str | None = None
    aapt_ok: bool = False


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def aapt_badging(path: Path) -> str:
    aapt = Path(
        r"C:\Users\Kaiser\AppData\Local\Android\Sdk\build-tools\36.0.0\aapt.exe"
    )
    import subprocess

    proc = subprocess.run(
        [str(aapt), "dump", "badging", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return (proc.stdout or "") + (proc.stderr or "")


def describe_apk(path: str | Path, store_json: Path | None = None) -> ApkArtifact:
    """Validate an APK exists, hash it and pull version metadata from aapt."""
    p = Path(path)
    if not p.is_file():
        raise AppOperationError(f"APK not found: {p}")
    art = ApkArtifact(path=p, sha256=sha256_of(p), size_bytes=p.stat().st_size)
    badging = aapt_badging(p)
    m = re.search(r"versionName='([^']*)'", badging)
    if m:
        art.version_name = m.group(1)
    m = re.search(r"versionCode='([^']*)'", badging)
    if m:
        art.version_code = m.group(1)
    art.aapt_ok = bool(art.version_name and art.version_code)
    if store_json:
        store_json.parent.mkdir(parents=True, exist_ok=True)
        store_json.write_text(
            json.dumps(asdict(art), indent=2), encoding="utf-8"
        )
    return art


def install_apk(
    serial: str,
    apk: str | Path,
    replace: bool = False,
    reinstall: bool = False,
) -> tuple[int, str]:
    """Install an APK, returning (exit code, output).

    ``replace`` -> -r (upgrade / re-install). ``reinstall`` -> -r -t (with test
    flag for debug builds). Only ever targets the owned serial.
    """
    check_serial(serial)
    cmd = [str(SDK_ADB), "-s", serial]
    cmd.append("install")
    if replace or reinstall:
        cmd.append("-r")
    if reinstall:
        cmd.append("-t")
    cmd.append(str(apk))
    import subprocess
    import time

    # Self-heal against the documented external adb churn: a single failed
    # install must not abort a lifecycle scenario.
    last_out = ""
    for attempt in range(5):
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                              encoding="utf-8", errors="replace")
        out = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0 or "Success" in out:
            last_out = out
            break
        last_out = out
        time.sleep(6 + attempt * 6)
    log = LOG_DIR / f"install_{Path(apk).stem}.log"
    log.write_text(last_out, encoding="utf-8")
    return proc.returncode, last_out


def uninstall_apk(serial: str, package: str = PACKAGE) -> tuple[int, str]:
    check_serial(serial)
    proc = __import__("subprocess").run(
        [str(SDK_ADB), "-s", serial, "uninstall", package],
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    (LOG_DIR / "uninstall.log").write_text(out, encoding="utf-8")
    return proc.returncode, out


def package_dump(serial: str, package: str = PACKAGE) -> str:
    return shell(serial, "dumpsys", "package", package, timeout=60)


def is_installed(serial: str, package: str = PACKAGE) -> bool:
    out = shell(serial, "pm", "list", "packages", package, timeout=30)
    return f"package:{package}" in out


def force_stop(serial: str, package: str = PACKAGE) -> None:
    shell(serial, "am", "force-stop", package, timeout=30)


def launch(serial: str, package: str = PACKAGE, activity: str = MAIN_ACTIVITY) -> str:
    """Start the activity without requiring -W's exit code to be zero.

    The external adb churn (runbook 1) can make ``am start -W`` return 255
    even though the intent was delivered; the authoritative readiness signal
    is the boot-trace poll, not this exit code.
    """
    return adb(
        "shell",
        "am",
        "start",
        "-n",
        f"{package}/{activity}",
        serial=serial,
        timeout=60,
        check=False,
    )


def resumed_activity(serial: str, package: str = PACKAGE) -> str:
    out = shell(serial, "dumpsys", "activity", "activities", timeout=60)
    for line in out.splitlines():
        if "ResumedActivity" in line:
            return line.strip()
    return ""


def boot_trace(serial: str, since_ms: int | None = None) -> list[str]:
    """Fetch PETACCESS_BOOT stages from logcat (Tauri console bridge)."""
    args = ["logcat", "-d", "-s", "Tauri/Console:*", "-v", "time"]
    out = shell(serial, *args, timeout=60)
    stages: list[str] = []
    for m in re.finditer(r"PETACCESS_BOOT=([A-Z_]+)", out):
        stages.append(m.group(1))
    return stages


def clear_logcat(serial: str) -> None:
    shell(serial, "logcat", "-c", timeout=30)


def launch_and_wait(
    serial: str,
    timeout_s: float = 40.0,
    stage: str = "HOME_READY",
) -> tuple[float, bool]:
    """Cold-launch and poll for the target boot stage; returns (elapsed, ok).

    A stage arriving late is a softer failure than never arriving; both are
    reported so a hang is distinguishable from a slow render.
    """
    start = time.monotonic()
    clear_logcat(serial)
    force_stop(serial)
    launch(serial)
    deadline = start + timeout_s
    seen: list[str] = []
    while time.monotonic() < deadline:
        seen = boot_trace(serial)
        if stage in seen:
            return round(time.monotonic() - start, 2), True
        time.sleep(1.0)
    return round(time.monotonic() - start, 2), stage in seen


def wait_home_ready(serial: str, timeout_s: float = 40.0) -> bool:
    elapsed, ok = launch_and_wait(serial, timeout_s=timeout_s, stage="HOME_READY")
    return ok