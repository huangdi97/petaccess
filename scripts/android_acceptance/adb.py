"""Runbook-safe adb wrapper: single SDK binary, every call bound to OWN_SERIAL.

Runbook constraints this enforces (ANDROID_TAURI_FORENSIC_RUNBOOK.md):

- Only the SDK platform-tools adb (1.0.41) is invoked, never ``C:\\Android\\adb.exe``
  (1.0.32), which would churn/kill the 5037 server and disturb other agents.
- We never run ``kill-server`` / ``reconnect offline`` / taskkill adb.
- Every device command carries ``-s SERIAL``; the default is ``emulator-5562``
  (this acceptance session's owned AVD) unless ``--serial`` overrides it.
- Screenshots use ``exec-out screencap -p`` redirected to a file by the caller
  (binary-safe; no PowerShell ``>`` on raw bytes here).

Self-healing: an unrelated agent session periodically calls the old adb binary,
which restarts the 5037 server mid-run (runbook section 1, "churn"). Device
commands therefore retry briefly instead of failing a whole scenario.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

SDK_ADB = Path(
    r"C:\Users\Kaiser\AppData\Local\Android\Sdk\platform-tools\adb.exe"
)
DEFAULT_SERIAL = "emulator-5562"
FORBIDDEN_SERIALS = frozenset({"emulator-5554"})
HARDCODED_ADB = r"C:\Android\adb.exe"


class AdbError(RuntimeError):
    """A failing adb invocation with its return code and stderr."""


def check_serial(serial: str) -> str:
    """Validate a serial before it is used in any adb command."""
    if not serial:
        raise ValueError("serial must not be empty")
    if serial in FORBIDDEN_SERIALS:
        raise AdbError(f"serial {serial} is owned by another agent and is off-limits")
    return serial


def adb_binary() -> str:
    """The single SDK adb path (existence checked at first use)."""
    if not SDK_ADB.exists():
        raise AdbError(f"SDK adb missing at {SDK_ADB}")
    return str(SDK_ADB)


def _run(cmd: list[str], timeout: int) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def adb(
    *args: str,
    serial: str = DEFAULT_SERIAL,
    timeout: int = 120,
    check: bool = True,
) -> str:
    """Run adb against ``serial``; return combined stdout+stderr text."""
    check_serial(serial)
    cmd = [adb_binary(), "-s", serial, *args]
    last_rc = -1
    # The external agent's churn can take 30-60s to settle (runbook 1); a
    # longer retry window keeps a scenario from dying on one hiccup.
    for attempt in range(8):
        last_rc, last_out = _run(cmd, timeout)
        if last_rc == 0:
            return last_out
        if f"device '{serial}' not found" in last_out or "device offline" in last_out:
            time.sleep(5 + attempt * 6)
            continue
        break
    if check:
        raise AdbError(f"adb {' '.join(args)} rc={last_rc}: {last_out[-600:]}")
    return last_out
def adb_global(*args: str, timeout: int = 120, check: bool = True) -> str:
    """An adb server-level command (no -s). Never kill-server / reconnect."""
    cmd = [adb_binary(), *args]
    last_rc = -1
    last_out = ""
    for attempt in range(4):
        last_rc, last_out = _run(cmd, timeout)
        if last_rc == 0:
            return last_out
        if "daemon not running" in last_out or "doesn't match this client" in last_out:
            time.sleep(2 + attempt * 3)
            continue
        break
    if check:
        raise AdbError(f"adb {' '.join(args)} rc={last_rc}: {last_out[-600:]}")
    return last_out


def devices() -> list[tuple[str, str]]:
    """Parse ``adb devices -l`` into [(serial, state)] pairs."""
    text = adb_global("devices", "-l")
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            rows.append((parts[0], parts[1]))
    return rows


def serial_state(serial: str = DEFAULT_SERIAL) -> str:
    """Current adb state ('device', 'offline', ...) or 'missing'."""
    for dev, state in devices():
        if dev == serial:
            return state
    return "missing"


def wait_for_device(serial: str = DEFAULT_SERIAL, timeout: int = 180) -> bool:
    """Block until ``serial`` shows state 'device' (or timeout)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if serial_state(serial) == "device":
            return True
        time.sleep(5)
    return False


def shell(serial: str, *args: str, timeout: int = 60) -> str:
    """adb -s SERIAL shell with check=True."""
    return adb("shell", *args, serial=serial, timeout=timeout, check=True)


def shell_pidof(serial: str, package: str) -> str:
    """PID of a package's process (empty string when not running)."""
    out = shell(serial, "pidof", package)
    return out.strip()


def package_running(serial: str, package: str) -> bool:
    return bool(shell_pidof(serial, package))