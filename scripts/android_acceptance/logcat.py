"""Logcat capture + severity classification (section 80 gate).

The whole suite should be able to answer "were there any unexplained
FATAL / ANR / crash / uncaught-JS / renderer death events?" with a classifier
instead of human eyeballing. This module dumps logcat for the owned serial,
classifies lines into severity buckets, and persists the raw dump as evidence.

Notes on separation of concerns: the *decision* (pass/fail) lives in the
reporting layer; this module only classifies and persists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .adb import DEFAULT_SERIAL, check_serial, shell

LOG_DIR = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\logs")

#: Bundle identifiers this session is allowed to touch.
APP_PACKAGE = "com.petaccess.map"


@dataclass
class LogcatClassified:
    raw: str
    fatal: list[str] = field(default_factory=list)
    anr: list[str] = field(default_factory=list)
    android_runtime: list[str] = field(default_factory=list)
    chromium: list[str] = field(default_factory=list)
    webview: list[str] = field(default_factory=list)
    tauri: list[str] = field(default_factory=list)
    js: list[str] = field(default_factory=list)
    csp: list[str] = field(default_factory=list)
    network: list[str] = field(default_factory=list)
    #: lines that only mention our own package's normal activity
    benign: list[str] = field(default_factory=list)


PATTERNS: dict[str, str] = {
    "fatal": r"FATAL EXCEPTION",
    "anr": r"ANR in \w+\.\w+",
    "android_runtime": r"AndroidRuntime",
    "chromium": r"chromium|cr_|libc|blue chromium",
    "webview": r"WebView|chromium_webview|Android System WebView",
    "tauri": r"Tauri|wry|tao",
    "js": r"Uncaught|TypeError|ReferenceError|SyntaxError|unhandledrejection|Vue warn",
    "csp": r"Content Security Policy|Refused to (load|connect|execute)",
    "network": r"cleartext|CLEARTEXT|NetworkSecurity|ECONNREFUSED|ERR_|net::ERR|TimeoutError|failed to connect",
}


def classify_logcat(serial: str = DEFAULT_SERIAL) -> LogcatClassified:
    """Dump logcat for ``serial`` (full buffer, all tags) and classify lines."""
    check_serial(serial)
    out = shell(serial, "logcat", "-d", "-v", "time", "-t", "20000", timeout=120)
    result = LogcatClassified(raw=out)
    for line in out.splitlines():
        hit = None
        for bucket, pattern in PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE):
                hit = bucket
                break
        if hit:
            getattr(result, hit).append(line)
        elif APP_PACKAGE in line:
            result.benign.append(line)
    return result


def save_evidence(result: LogcatClassified, name: str = "logcat_full") -> Path:
    """Persist the raw dump plus a per-bucket summary sidecar."""
    path = LOG_DIR / f"{name}.log"
    path.write_text(result.raw, encoding="utf-8")
    summary = [
        f"{bucket}: {len(getattr(result, bucket))}"
        for bucket in (
            "fatal",
            "anr",
            "android_runtime",
            "chromium",
            "webview",
            "tauri",
            "js",
            "csp",
            "network",
        )
    ]
    (LOG_DIR / f"{name}.summary.txt").write_text("\n".join(summary), encoding="utf-8")
    return path


def unexpected_counts(result: LogcatClassified) -> dict[str, int]:
    """Raw counts per severity bucket for the final logcat gate."""
    return {
        bucket: len(getattr(result, bucket))
        for bucket in (
            "fatal",
            "anr",
            "android_runtime",
            "chromium",
            "webview",
            "js",
            "csp",
            "network",
        )
    }
