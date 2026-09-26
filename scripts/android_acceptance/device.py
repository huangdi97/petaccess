"""Device preflight: own-serial isolation + device characteristics recording.

Guards the P0 ownership rules: refuses to run against any forbidden serial,
writes device facts (api level, wm size/density, model, boot state) so every
later scenario can cross-check the AVD it actually ran on.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .adb import DEFAULT_SERIAL, check_serial, devices, serial_state, shell, wait_for_device


@dataclass
class DeviceFacts:
    serial: str
    state: str
    sdk: str
    model: str
    wm_size: str
    wm_density: str
    logical_width_dp: str | None
    logical_height_dp: str | None
    boot_completed: str
    checked_at_iso: str


def parse_wm_size(out: str) -> tuple[int, int] | None:
    """Parse 'Physical size: 1080x2340' -> (1080, 2340)."""
    import re

    m = re.search(r"(\d{3,5})[xX](\d{3,5})", out)
    return (int(m.group(1)), int(m.group(2))) if m else None


def parse_wm_density(out: str) -> int | None:
    import re

    m = re.search(r"Physical density:\s*(\d+)", out)
    return int(m.group(1)) if m else None


def logical_dp(size: tuple[int, int] | None, density: int | None) -> tuple[str, str] | None:
    if not size or not density:
        return None
    return (f"{size[0] * 160 / density:.0f}dp", f"{size[1] * 160 / density:.0f}dp")


def preflight(
    serial: str = DEFAULT_SERIAL, wait_timeout: int = 240
) -> tuple[DeviceFacts, list[str]]:
    """Verify the owned device is online and record its physical/logical facts.

    Returns (facts, warnings). Raises when the serial is missing/offline after
    ``wait_timeout`` or is a forbidden serial.
    """
    warnings: list[str] = []
    check_serial(serial)
    seen = [d for d, _ in devices()]
    if serial not in seen:
        warnings.append(f"{serial} not in adb devices list at preflight")
    if not wait_for_device(serial, timeout=wait_timeout):
        raise RuntimeError(f"device {serial} did not reach state 'device'")
    sdk = shell(serial, "getprop", "ro.build.version.sdk").strip()
    model = shell(serial, "getprop", "ro.product.model").strip()
    wm_size = shell(serial, "wm", "size").strip()
    wm_density = shell(serial, "wm", "density").strip()
    boot = shell(serial, "getprop", "sys.boot_completed").strip()
    size = parse_wm_size(wm_size)
    density = parse_wm_density(wm_density)
    dp = logical_dp(size, density)
    facts = DeviceFacts(
        serial=serial,
        state=serial_state(serial),
        sdk=sdk,
        model=model,
        wm_size=wm_size,
        wm_density=wm_density,
        logical_width_dp=dp[0] if dp else None,
        logical_height_dp=dp[1] if dp else None,
        boot_completed=boot,
        checked_at_iso=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    )
    return facts, warnings


def set_wm_size(serial: str, width: int, height: int, density: int | None = None) -> None:
    """Switch the owned AVD's logical viewport (section 5, wm size method)."""
    check_serial(serial)
    shell(serial, "wm", "size", f"{width}x{height}", timeout=30)
    if density:
        shell(serial, "wm", "density", str(density), timeout=30)
    time.sleep(3)


def reset_wm(serial: str) -> None:
    """Restore physical defaults; caller re-verifies after (section 5)."""
    check_serial(serial)
    shell(serial, "wm", "size", "reset", timeout=30)
    shell(serial, "wm", "density", "reset", timeout=30)
    time.sleep(3)


def write_device_json(
    facts: DeviceFacts, path: Path, extra: dict | None = None
) -> Path:
    payload = asdict(facts)
    if extra:
        payload.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path