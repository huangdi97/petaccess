"""Test-only ASGI wrapper: mounts the real API behind delay/status injection.

This is acceptance instrumentation, never product code. It reads a control file
(runtime/backend_control.json) written by the acceptance harness:

- ``delay_ms``: sleep before passing each request to the real app (slow backend)
- ``status``:   when set, respond with that status for whitelisted probes without
                touching the real app (HTTP error matrix) — still bounded to the
                acceptance DB role via the same guard as dev_api_server.py.

Injected responses carry the same CORS headers the real app middleware adds,
so the WebView observes a genuine HTTP status (not "Failed to fetch").
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import sys
from pathlib import Path

PTY = Path(__file__).resolve().parents[2]  # repo root
API_DIR = PTY / "services" / "api"
CONTROL_FILE = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\runtime\backend_control.json")

_status_control = {"delay_ms": 0, "status": None, "paths": []}


def _read_control() -> None:
    try:
        data = json.loads(CONTROL_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    _status_control.update(
        {
            "delay_ms": int(data.get("delay_ms", 0) or 0),
            "status": int(data["status"]) if data.get("status") else None,
            "paths": list(data.get("paths", [])),
        }
    )


class ControlMiddleware:
    """ASGI middleware: delay + optional status override for whitelisted paths."""

    def __init__(self, app: object) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: object, send: object) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)  # type: ignore[misc]
            return
        _read_control()
        delay = _status_control["delay_ms"]
        if delay and delay > 0:
            await asyncio.sleep(delay / 1000.0)
        st = _status_control["status"]
        path = scope.get("path", "")
        paths = _status_control["paths"]
        if st and paths and any(path.startswith(p) for p in paths):
            body = json.dumps({"detail": f"injected test status {st}", "test_only": True}).encode(
                "utf-8"
            )
            await send(
                {
                    "type": "http.response.start",
                    "status": st,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"access-control-allow-origin", b"http://tauri.localhost"),
                        (b"access-control-allow-credentials", b"true"),
                        (b"vary", b"Origin"),
                        (b"content-length", str(len(body)).encode()),
                        (b"connection", b"close"),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)  # type: ignore[misc]
        await self.app(scope, receive, send)  # type: ignore[misc]


def _import_dev_server():
    """Import the repo's dev_api_server from a clean module name."""
    sys.path.insert(0, str(PTY / "scripts"))
    return importlib.import_module("dev_api_server")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-name", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--port", type=int, default=8010)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--log-level", default="warning")
    args = ap.parse_args()

    dev = _import_dev_server()
    url = dev.database_url_for(args.db_name)
    os.environ["DATABASE_URL"] = url or ""
    live_name, role = dev.probe_role(dev.psycopg_url_for(args.db_name))
    if role.value.upper() != args.role.upper():
        print(f"REFUSED role {role.value} != {args.role}", file=sys.stderr)
        return 3
    print(f"WRAPPER TARGET_DB = {live_name} role={role.value}", file=sys.stderr)
    os.environ["DB_ROLE"] = role.value
    os.chdir(API_DIR)

    import uvicorn

    from app.main import app  # noqa: PLC0415

    wrapped = ControlMiddleware(app)
    uvicorn.run(wrapped, host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
