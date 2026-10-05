"""Runtime backend control for network/error scenarios (sections 26/60/61).

The acceptance API on :8010 is the app's backend. Simulating slow/error/offline
must NOT edit product code, so this module owns a *test-only* launcher that
mounts the real ``app.main:app`` behind a middleware reading a small control
file. Scenarios simply write the control file:

- ``offline``  -> stop the API process entirely (network_test uses process
  stop/start; the wrapper here only adds delay/status injection).
- ``delay_ms`` -> sleep before forwarding (slow backend 1/3/8s).
- ``status``   -> override the response status (HTTP error matrix 400..503).

The wrapper is started only for this acceptance session on :8010 and is never
merged into product code; control files live under the evidence dir.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

CONTROL = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\runtime\backend_control.json")
RUNNER = Path(__file__).with_name("api_wrapper.py")
API_LOG = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\logs\api_wrapper.log")

_SESSION = os.environ.get("PI_SCRATCH_DIR") or str(Path.home() / ".pi-desktop")
API_PID_FILE = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\runtime\api_pid.txt")


class BackendControlError(RuntimeError):
    """Control-file or subprocess failure."""


def _control() -> dict:
    if not CONTROL.exists():
        return {}
    try:
        return json.loads(CONTROL.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_control(**fields: object) -> None:
    data = _control()
    data.update(fields)
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    CONTROL.write_text(json.dumps(data), encoding="utf-8")


def clear_control() -> None:
    if CONTROL.exists():
        CONTROL.unlink()


def start_wrapper(
    db_name: str = "petaccess_e2e_android",
    role: str = "E2E",
    port: int = 8010,
) -> int:
    """Start (or reuse) the test-only wrapper API and return its PID.

    Fails if anything tries to point at PRODUCTION: the wrapper itself re-
    validates the DB role before binding (same guard as dev_api_server.py).
    """
    if API_PID_FILE.exists():
        pid = int(API_PID_FILE.read_text().strip() or "0")
        if _pid_alive(pid):
            return pid
    venv_py = sys.executable
    cmd = [
        venv_py,
        str(RUNNER),
        "--db-name",
        db_name,
        "--role",
        role,
        "--port",
        str(port),
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=open(API_LOG, "ab"),
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    time.sleep(2)
    API_PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    return proc.pid


def stop_wrapper() -> None:
    """Stop the acceptance wrapper by its actual 8010 listener owner."""
    try:
        conn = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetTCPConnection -State Listen -LocalPort 8010 -ErrorAction SilentlyContinue | "
                "Select-Object -First 1 -ExpandProperty OwningProcess",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
        if conn and conn.isdigit():
            subprocess.run(["taskkill", "/PID", conn, "/T", "/F"], capture_output=True)
    except Exception:
        pass
    if API_PID_FILE.exists():
        API_PID_FILE.unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    return (
        subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True
        ).stdout.count(str(pid))
        > 1
    )


def probe_ready(url: str = "http://127.0.0.1:8010/api/v1/regulations", timeout: int = 30) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            import urllib.request

            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(1)
    return False
