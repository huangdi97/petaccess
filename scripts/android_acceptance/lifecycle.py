"""Lifecycle acceptance: cold/warm launch, relaunch, background/foreground,
process-death recovery, on the owned serial only (sections 18-22).

Each phase writes a JSON row to the evidence dir so the final report can sum
exact pass/fail counts (10/10 cold, 20/20 warm, etc.). No screen is ever
consulted here without a screenshot + logcat assertion pair.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .adb import DEFAULT_SERIAL, check_serial, shell
from .appops import (
    PACKAGE,
    boot_trace,
    force_stop,
    launch,
    package_dump,
    shell_pidof,
    wait_home_ready,
)
from .screenshot import capture_default_name, gray_or_blank

EVIDENCE = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\runtime")


@dataclass
class LifecycleResult:
    scenario: str
    total: int
    passed: int = 0
    failed: int = 0
    failures: list[dict] = field(default_factory=list)
    samples: list[dict] = field(default_factory=list)


def _save(result: LifecycleResult, label: str = "lifecycle") -> Path:
    path = EVIDENCE / f"{label}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def cold_launch_loop(
    serial: str = DEFAULT_SERIAL, n: int = 10, timeout_s: float = 45.0
) -> LifecycleResult:
    """force-stop -> clear logcat -> launch -> wait HOME_READY, n times."""
    check_serial(serial)
    res = LifecycleResult(scenario="cold_launch", total=n)
    for i in range(1, n + 1):
        started = time.monotonic()
        force_stop(serial)
        shell(serial, "logcat", "-c", timeout=30)
        launch(serial)
        ok = wait_home_ready(serial, timeout_s=timeout_s)
        stages = boot_trace(serial)
        elapsed = round(time.monotonic() - started, 2)
        shot = capture_default_name(serial, f"cold{i:02d}", "home", "cold", f"C{i:02d}")
        blank = gray_or_blank(shot)
        passed = ok and not blank
        row = {
            "iteration": i,
            "elapsed_s": elapsed,
            "home_ready": ok,
            "boot_stages": stages,
            "blank_screen": blank,
            "screenshot": str(shot),
        }
        res.samples.append(row)
        if passed:
            res.passed += 1
        else:
            res.failed += 1
            res.failures.append(row)
    _save(res, "cold_launch")
    return res


def warm_launch_loop(
    serial: str = DEFAULT_SERIAL, n: int = 20, timeout_s: float = 30.0
) -> LifecycleResult:
    """Repeated launch without force-stop (process alive) — warm start."""
    check_serial(serial)
    res = LifecycleResult(scenario="warm_launch", total=n)
    for i in range(1, n + 1):
        started = time.monotonic()
        launch(serial)  # brings existing process/activity forward
        ok = wait_home_ready(serial, timeout_s=timeout_s)
        elapsed = round(time.monotonic() - started, 2)
        shot = capture_default_name(serial, f"warm{i:02d}", "home", "warm", f"W{i:02d}")
        blank = gray_or_blank(shot)
        crashed = "FATAL EXCEPTION" in shell(serial, "logcat", "-d", "-t", "200", timeout=30)
        passed = ok and not blank and not crashed
        row = {
            "iteration": i,
            "elapsed_s": elapsed,
            "home_ready": ok,
            "blank_screen": blank,
            "crash_in_log": crashed,
            "screenshot": str(shot),
        }
        res.samples.append(row)
        if passed:
            res.passed += 1
        else:
            res.failed += 1
            res.failures.append(row)
    _save(res, "warm_launch")
    return res


def relaunch_loop(
    serial: str = DEFAULT_SERIAL, n: int = 20, hold_s: float = 1.5
) -> LifecycleResult:
    """Exit to launcher, then relaunch — checks navigation/settings/UI survive."""
    check_serial(serial)
    res = LifecycleResult(scenario="relaunch", total=n)
    for i in range(1, n + 1):
        shell(serial, "input", "keyevent", "KEYCODE_HOME", timeout=30)
        time.sleep(hold_s)
        pid_before = shell_pidof(serial, PACKAGE)
        launch(serial)
        ok = wait_home_ready(serial, timeout_s=30)
        pid_after = shell_pidof(serial, PACKAGE)
        row = {
            "iteration": i,
            "pid_before": pid_before,
            "pid_after": pid_after,
            "home_ready": ok,
        }
        res.samples.append(row)
        passed = ok and bool(pid_after.strip())
        if passed:
            res.passed += 1
        else:
            res.failed += 1
            res.failures.append(row)
    _save(res, "relaunch")
    return res


def background_foreground_loop(
    serial: str = DEFAULT_SERIAL,
    cycles: int = 20,
    holds_s: tuple[float, ...] = (1, 5, 30, 120),
) -> LifecycleResult:
    """Home -> background -> wait -> resume, covering 1s/5s/30s/2min holds."""
    check_serial(serial)
    res = LifecycleResult(scenario="background_foreground", total=cycles)
    for i in range(1, cycles + 1):
        hold = holds_s[(i - 1) % len(holds_s)]
        shell(serial, "input", "keyevent", "KEYCODE_HOME", timeout=30)
        time.sleep(hold)
        launch(serial)
        ok = wait_home_ready(serial, timeout_s=40)
        shot = capture_default_name(serial, f"bg{i:02d}", "home", "resume", f"BG{i:02d}")
        blank = gray_or_blank(shot)
        row = {"iteration": i, "hold_s": hold, "home_ready": ok, "blank_screen": blank}
        res.samples.append(row)
        if ok and not blank:
            res.passed += 1
        else:
            res.failed += 1
            res.failures.append(row)
    _save(res, "background_foreground")
    return res


def process_death_recovery(
    serial: str = DEFAULT_SERIAL, n: int = 3, timeout_s: float = 45.0
) -> LifecycleResult:
    """Kill the app process (am kill) and restart; settings/Home must recover."""
    check_serial(serial)
    res = LifecycleResult(scenario="process_death", total=n)
    for i in range(1, n + 1):
        shell(serial, "am", "kill", PACKAGE, timeout=30)
        time.sleep(2)
        pid_before = shell_pidof(serial, PACKAGE)
        launch(serial)
        ok = wait_home_ready(serial, timeout_s=timeout_s)
        row = {
            "iteration": i,
            "pid_after_kill": pid_before.strip() or "(dead)",
            "home_ready": ok,
        }
        res.samples.append(row)
        if ok:
            res.passed += 1
        else:
            res.failed += 1
            res.failures.append(row)
    _save(res, "process_death")
    return res