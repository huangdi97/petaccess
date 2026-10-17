"""Lightweight extended packaged-runtime gate for Android Preview CI.

This complements the page/IME/width gates with runtime behavior that should be
stable on every Preview candidate: cold launch, warm resume, background/
foreground, process death recovery, memory sampling and route stress.

It intentionally does not claim install-upgrade, full HTTP error injection or
native accessibility coverage; those dimensions remain separate evidence.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

from adb import adb, shell, shell_pidof, wait_for_device

ROOT = Path(__file__).resolve().parents[2]
SERIAL = os.environ.get("PETACCESS_ANDROID_SERIAL", "emulator-5556")
PACKAGE = os.environ.get("PETACCESS_ANDROID_PACKAGE", "com.petaccess.map.preview")
EVIDENCE_ROOT = Path(
    os.environ.get(
        "PETACCESS_ANDROID_EVIDENCE_DIR",
        str(ROOT / "artifacts" / "android-preview-runtime"),
    )
)
RUNTIME = EVIDENCE_ROOT / "runtime"
PERF = EVIDENCE_ROOT / "performance"
PROBE = ROOT / "scripts" / "android_acceptance" / "cdp_probe.cjs"
STRESS = ROOT / "scripts" / "android_acceptance" / "route_stress.cjs"
CDP_PORT = int(os.environ.get("PETACCESS_ANDROID_EXTENDED_CDP_PORT", "9235"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _start_activity() -> None:
    adb(
        "shell",
        "am",
        "start",
        "-n",
        f"{PACKAGE}/.MainActivity",
        serial=SERIAL,
        timeout=60,
        check=False,
    )


def _forward_for_current_process() -> str:
    deadline = time.monotonic() + 45
    last_pid = ""
    while time.monotonic() < deadline:
        pid = shell_pidof(SERIAL, PACKAGE).strip()
        if pid:
            last_pid = pid
            adb(
                "forward",
                "--remove",
                f"tcp:{CDP_PORT}",
                serial=SERIAL,
                timeout=30,
                check=False,
            )
            out = adb(
                "forward",
                f"tcp:{CDP_PORT}",
                f"localabstract:webview_devtools_remote_{pid}",
                serial=SERIAL,
                timeout=30,
                check=False,
            )
            if "error" not in out.lower():
                return pid
        time.sleep(0.5)
    raise RuntimeError(f"WebView CDP process not ready; last pid={last_pid!r}")


def _snapshot(expect_page: str | None = None, timeout_s: float = 30.0) -> dict:
    deadline = time.monotonic() + timeout_s
    last: dict | None = None
    last_error = ""
    while time.monotonic() < deadline:
        _forward_for_current_process()
        proc = subprocess.run(
            ["node", str(PROBE), str(CDP_PORT), "snapshot"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode == 0:
            line = next(
                (row for row in reversed(proc.stdout.splitlines()) if row.startswith("SNAPSHOT ")),
                "",
            )
            if line:
                last = json.loads(line.removeprefix("SNAPSHOT "))
                page_ok = expect_page is None or last.get("uiPage") == expect_page
                if (
                    last.get("shell")
                    and not last.get("horizontalOverflow")
                    and page_ok
                ):
                    return last
        else:
            last_error = (proc.stderr or proc.stdout)[-500:]
        time.sleep(0.5)
    raise RuntimeError(
        f"semantic snapshot timeout expect_page={expect_page!r} last={last!r} error={last_error!r}"
    )


def _memory_pss_kb() -> tuple[int, str]:
    raw = shell(SERIAL, "dumpsys", "meminfo", PACKAGE, timeout=60)
    patterns = [
        r"TOTAL PSS:\s+(\d+)",
        r"TOTAL\s+(\d+)\s+",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return int(match.group(1)), raw
    raise RuntimeError("Unable to parse TOTAL PSS from dumpsys meminfo")


def _launch_cycle(kind: str, total: int, *, background: bool = False, kill: bool = False) -> dict:
    rows: list[dict] = []
    for index in range(1, total + 1):
        started = time.monotonic()
        pid_before = shell_pidof(SERIAL, PACKAGE).strip()

        if kill:
            adb("shell", "am", "kill", PACKAGE, serial=SERIAL, timeout=30, check=False)
            time.sleep(0.8)
        elif background:
            shell(SERIAL, "input", "keyevent", "KEYCODE_HOME", timeout=30)
            time.sleep(0.8)
        elif kind == "cold":
            adb("shell", "am", "force-stop", PACKAGE, serial=SERIAL, timeout=30, check=False)
            time.sleep(0.4)

        _start_activity()
        snapshot = _snapshot(timeout_s=35)
        pid_after = shell_pidof(SERIAL, PACKAGE).strip()
        row = {
            "iteration": index,
            "elapsedMs": round((time.monotonic() - started) * 1000),
            "pidBefore": pid_before or None,
            "pidAfter": pid_after or None,
            "uiPage": snapshot.get("uiPage"),
            "uiState": snapshot.get("uiState"),
            "horizontalOverflow": snapshot.get("horizontalOverflow"),
            "ok": bool(pid_after) and snapshot.get("shell") is True,
        }
        if kill:
            row["processChanged"] = bool(pid_before and pid_after and pid_before != pid_after)
        rows.append(row)

    return {
        "scenario": kind,
        "total": total,
        "passed": sum(1 for row in rows if row["ok"]),
        "failed": sum(1 for row in rows if not row["ok"]),
        "samples": rows,
    }


def _run_stress() -> dict:
    _start_activity()
    _snapshot(timeout_s=30)
    _forward_for_current_process()
    env = os.environ.copy()
    env["PETACCESS_ANDROID_CDP_PORT"] = str(CDP_PORT)
    proc = subprocess.run(
        ["node", str(STRESS), str(CDP_PORT)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"route stress failed: {(proc.stderr or proc.stdout)[-1000:]}")
    path = RUNTIME / "route_stress.json"
    if not path.exists():
        raise RuntimeError("route stress did not write route_stress.json")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    if not wait_for_device(SERIAL, timeout=120):
        raise RuntimeError(f"{SERIAL} not ready")

    RUNTIME.mkdir(parents=True, exist_ok=True)
    PERF.mkdir(parents=True, exist_ok=True)

    cold = _launch_cycle("cold", 3)
    warm = _launch_cycle("warm", 5)
    background = _launch_cycle("background_foreground", 3, background=True)
    process_death = _launch_cycle("process_death", 2, kill=True)

    _start_activity()
    _snapshot(timeout_s=30)
    before_pss, before_raw = _memory_pss_kb()
    (PERF / "meminfo_before_stress.txt").write_text(before_raw, encoding="utf-8")

    stress = _run_stress()

    after_pss, after_raw = _memory_pss_kb()
    (PERF / "meminfo_after_stress.txt").write_text(after_raw, encoding="utf-8")
    growth_kb = after_pss - before_pss
    limit_kb = max(100 * 1024, before_pss)
    performance = {
        "result": "PASS" if growth_kb <= limit_kb else "FAIL",
        "beforeTotalPssKb": before_pss,
        "afterTotalPssKb": after_pss,
        "growthKb": growth_kb,
        "allowedGrowthKb": limit_kb,
        "criterion": "after-before <= max(100MiB, before)",
    }
    _write(PERF / "memory_summary_preview.json", performance)

    lifecycle = {
        "schemaVersion": 1,
        "result": "PASS",
        "scenarios": {
            "cold": cold,
            "warm": warm,
            "background_foreground": background,
            "process_death": process_death,
        },
    }
    for scenario in lifecycle["scenarios"].values():
        if scenario["failed"] != 0 or scenario["passed"] != scenario["total"]:
            lifecycle["result"] = "FAIL"
    _write(RUNTIME / "lifecycle_preview.json", lifecycle)

    result = (
        "PASS"
        if lifecycle["result"] == "PASS"
        and performance["result"] == "PASS"
        and stress.get("result") == "PASS"
        else "FAIL"
    )
    summary = {
        "schemaVersion": 1,
        "result": result,
        "lifecycle": lifecycle["result"],
        "performance": performance["result"],
        "stress": stress.get("result"),
        "stressTransitions": stress.get("transitions"),
    }
    _write(RUNTIME / "extended_runtime.json", summary)
    print(json.dumps(summary, ensure_ascii=False))

    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
