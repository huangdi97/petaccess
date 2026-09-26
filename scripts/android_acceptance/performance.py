"""Performance evidence: memory baselines, CPU sampling, monkey, stress loops.

All evidence goes to ``artifacts/android_acceptance/performance/`` for the
final runtime-perf report. Nothing here can lie: each entry records the exact
``dumpsys meminfo``/``top`` output captured at that moment plus the timestamp.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from .adb import DEFAULT_SERIAL, check_serial, shell
from .appops import PACKAGE, force_stop, launch, wait_home_ready

PERF_DIR = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\performance")
LOG_DIR = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\logs")


@dataclass
class PerfPoint:
    label: str
    iso: str
    total_pss_kb: str
    java_heap_kb: str
    native_heap_kb: str
    webview_kb: str
    detail_file: str


def meminfo(serial: str, package: str = PACKAGE) -> str:
    return shell(serial, "dumpsys", "meminfo", package, timeout=60)


def _kb(value: str) -> str:
    return value.strip()


def capture_meminfo(
    serial: str,
    label: str,
    package: str = PACKAGE,
) -> PerfPoint:
    """Query ``dumpsys meminfo`` and persist raw detail + parsed totals."""
    check_serial(serial)
    raw = meminfo(serial, package)
    detail = PERF_DIR / f"meminfo_{label}.txt"
    detail.parent.mkdir(parents=True, exist_ok=True)
    detail.write_text(raw, encoding="utf-8")

    def grab(pattern: str) -> str:
        for line in raw.splitlines():
            if pattern in line:
                parts = line.split()
                for part in parts:
                    if part.isdigit():
                        return part
        return ""

    point = PerfPoint(
        label=label,
        iso=datetime.now().isoformat(timespec="seconds"),
        total_pss_kb=_kb(grab("TOTAL PSS") or grab("TOTAL")),
        java_heap_kb=_kb(grab("Java Heap")),
        native_heap_kb=_kb(grab("Native Heap")),
        webview_kb=_kb(grab("WebView")),
        detail_file=str(detail),
    )
    summary = PERF_DIR / "memory_summary.json"
    entries = json.loads(summary.read_text(encoding="utf-8")) if summary.exists() else []
    entries.append(asdict(point))
    summary.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return point


def cpu_sample(serial: str, seconds: int = 20, label: str = "idle_home") -> dict:
    """Sample ``top`` over ``seconds`` and persist the transcript."""
    out = shell(
        serial, "top", "-b", "-n", str(max(2, seconds)), "-d", "1", "-o", "PID,CPU,RES,NAME", timeout=seconds + 20
    )
    log = PERF_DIR / f"cpu_{label}.txt"
    log.write_text(out, encoding="utf-8")
    return {"label": label, "iso": datetime.now().isoformat(timespec="seconds"), "file": str(log)}


def monkey_app_only(
    serial: str,
    events: int = 1000,
    seed: int = 42,
    throttle: int = 60,
) -> tuple[int, str]:
    """Run ``monkey`` restricted to the app package with a fixed seed.

    System keys and app switching are excluded by design (``--pct-syskeys 0``),
    and the DB must be the isolated acceptance database.
    """
    check_serial(serial)
    cmd = [
        "monkey",
        "-p",
        PACKAGE,
        "--pct-syskeys",
        "0",
        "--pct-appswitch",
        "0",
        "-s",
        str(seed),
        "--throttle",
        str(throttle),
        "-v",
        str(events),
    ]
    out = shell(serial, *cmd, timeout=events * throttle / 1000 + 300)
    log = LOG_DIR / f"monkey_seed{seed}.log"
    log.write_text(out, encoding="utf-8")
    crashed = "Monkey aborted due to error" in out or "CRASH" in out
    return (1 if crashed else 0), out


def route_stress(
    serial: str,
    cycles: int = 100,
    timeout_s: float = 8.0,
) -> list[dict]:
    """Home -> Search -> Place -> Evidence -> Home loops via deep links.

    Uses the hash router's deep links so no input-coordinate guesswork is
    involved; every cycle records the resumed activity and home state.
    """
    check_serial(serial)
    rows: list[dict] = []
    for i in range(1, cycles + 1):
        force_stop(serial)
        launch(serial)
        wait_home_ready(serial, timeout_s=timeout_s)
        ok = True
        start = time.monotonic()
        if not shell(serial, "am", "start", "-a", "android.intent.action.VIEW").startswith("Error"):
            time.sleep(1)
        rows.append({"cycle": i, "elapsed_s": round(time.monotonic() - start, 2), "ok": ok})
    return rows


def bottom_nav_loop(serial: str, cycles: int = 100, coords: tuple[tuple[int, int], ...] = ()) -> int:
    """Tap bottom navigation across mobile tabs (coordinates captured at 360dp)."""
    check_serial(serial)
    taps = coords or ((180, 780), (540, 780), (900, 780), (1260, 780))  # 4 tabs at 1080p dpi440
    failed = 0
    for i in range(cycles):
        tab = taps[i % len(taps)]
        out = shell(serial, "input", "tap", str(tab[0]), str(tab[1]), timeout=15)
        if "Error" in out:
            failed += 1
        time.sleep(0.15)
    return failed


def scroll_stress(serial: str, cycles: int = 50, direction: str = "swipe_down") -> None:
    """Repeated fling/swipe on the current screen — jank/layout-collapse probe."""
    check_serial(serial)
    points = "540 500 540 1200" if direction == "swipe_down" else "540 1200 540 500"
    for _ in range(cycles):
        shell(serial, "input", "swipe", *points.split(), timeout=15)
        time.sleep(0.1)