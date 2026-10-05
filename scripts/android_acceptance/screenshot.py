"""Runbook-safe screenshot capture + PNG integrity validation.

Capture is binary-safe: ``adb -s SERIAL exec-out screencap -p`` writes raw bytes
to the target path without any PowerShell/Out-File redirect (REG-002). Every
written file is validated against the PNG magic ``89504E47``; a UTF-16-corrupted
file (magic ``FFFEFDFF``) fails loudly instead of being passed on as evidence.
"""

from __future__ import annotations

import struct
import subprocess
from pathlib import Path

from .adb import SDK_ADB, check_serial

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
#: Known corruption marker from capturing through a UTF-16 redirect.
BAD_UTF16_MAGIC = b"\xff\xfe\xfd\xff"
SCREENSHOT_DIR = Path(r"E:\AI\宠物管理\artifacts\android_acceptance\screenshots")


class ScreenshotError(RuntimeError):
    """A capture or validation failure."""


def validate_png(path: Path) -> bool:
    """True when ``path`` is a regular PNG whose magic matches 89504E47."""
    if not path.is_file():
        return False
    if path.stat().st_size < 8:
        return False
    with path.open("rb") as fh:
        head = fh.read(8)
    if head.startswith(BAD_UTF16_MAGIC):
        raise ScreenshotError(f"corrupted (UTF-16) PNG: {path} — magic FFFEFDFF")
    return head == PNG_MAGIC


def pixel_stats(path: Path) -> tuple[int, int] | None:
    """(distinct scanlines, sampled rows) using only stdlib zlib.

    Enough to reject solid-white/solid-gray captures: a real screen has many
    distinct scanlines, a blank one collapses to a handful. Returns None for
    non-PNG or unsupported bit depth/color type.
    """
    import zlib

    if not validate_png(path):
        return None
    data = path.read_bytes()
    idat = bytearray()
    width = 0
    stride = 0
    pos = 8
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        ctype = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        if ctype == b"IHDR":
            width, _h, bitdepth, coltype = struct.unpack(">IIBB", chunk[:10])
            if bitdepth != 8:
                return None
            px_stride = {0: 1, 2: 3, 4: 2, 6: 4}.get(coltype)
            stride = width * px_stride + 1 if px_stride else 0
            if px_stride is None or stride == 0:
                return None
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
        pos += 12 + length
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error:
        return None
    # Raw scanlines: each row is prefixed by one filter byte.
    rows = [raw[i : i + stride] for i in range(0, len(raw), stride)][:200]
    distinct_rows = len({bytes(r) for r in rows})
    return (distinct_rows, len(rows))


def capture(serial: str, path: str | Path) -> Path:
    """Capture a screenshot for ``serial`` and write a validated PNG."""
    check_serial(serial)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(SDK_ADB), "-s", serial, "exec-out", "screencap", "-p"],
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", "replace")[:300]
        raise ScreenshotError(f"screencap rc={proc.returncode}: {err}")
    target.write_bytes(proc.stdout)
    if not validate_png(target):
        raise ScreenshotError(f"invalid PNG at {target} (magic check failed)")
    return target


def capture_default_name(
    serial: str, device_tag: str, route: str, state: str, scenario: str
) -> Path:
    """Persist a screenshot under the unified evidence naming (section 111)."""
    safe = lambda s: "".join(c if c.isalnum() or c in "_-." else "_" for c in s)
    name = f"{safe(device_tag)}__{safe(route)}__{safe(state)}__{safe(scenario)}.png"
    return capture(serial, SCREENSHOT_DIR / name)


def gray_or_blank(path: Path) -> bool:
    """True when a validated PNG looks like a solid/blank screen.

    A real screen has thousands of colors and many distinct scanlines; a gray
    or white screen collapses to a handful. This is a cheap pre-check — the
    final gate also includes logcat and uiautomator assertions.
    """
    stats = pixel_stats(path)
    if not stats:
        return True
    distinct, rows = stats
    return distinct < 4 or distinct < max(8, rows // 20)
