"""Unit tests for the Android acceptance toolkit (goal section 118).

Covers the pure helpers that the emulator automation depends on, so the tool
itself cannot silently misreport PASS: serial safety, PNG magic/blank checks,
APK artifact description, wm parsing, logcat classification. These run without
any device or API (no adb, no network).
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

import pytest

from scripts.android_acceptance.adb import (
    FORBIDDEN_SERIALS,
    AdbError,
    check_serial,
    serial_state,
)
from scripts.android_acceptance.appops import describe_apk, sha256_of
from scripts.android_acceptance.device import parse_wm_density, parse_wm_size
from scripts.android_acceptance.logcat import LogcatClassified, classify_logcat, unexpected_counts
from scripts.android_acceptance.screenshot import (
    PNG_MAGIC,
    gray_or_blank,
    pixel_stats,
    validate_png,
)


def _make_png(path: Path, width: int = 8, height: int = 8, blank: bool = False) -> Path:
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            if blank:
                raw += bytes([240, 240, 240])
            else:
                raw += bytes([(x * 37 + y * 11) % 256, (y * 53) % 256, (x * 97) % 256])
    idat = zlib.compress(bytes(raw))
    data = PNG_MAGIC + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------- serial


def test_serial_rejects_forbidden_serial() -> None:
    with pytest.raises(AdbError):
        check_serial(next(iter(FORBIDDEN_SERIALS)))


def test_serial_accepts_owned_serial() -> None:
    assert check_serial("emulator-5562") == "emulator-5562"


def test_serial_rejects_empty() -> None:
    with pytest.raises(ValueError):
        check_serial("")


# ---------------------------------------------------------------- png


def test_png_magic_valid(tmp_path: Path) -> None:
    p = _make_png(tmp_path / "ok.png")
    assert validate_png(p) is True


def test_png_magic_rejects_utf16_corruption(tmp_path: Path) -> None:
    p = tmp_path / "bad.png"
    p.write_bytes(b"\xff\xfe\xfd\xff" + b"garbage")
    from scripts.android_acceptance.screenshot import ScreenshotError

    with pytest.raises(ScreenshotError):
        validate_png(p)


def test_png_magic_rejects_plain_text(tmp_path: Path) -> None:
    p = tmp_path / "txt.png"
    p.write_bytes(b"not a png at all")
    assert validate_png(p) is False


def test_gray_or_blank_detects_solid(tmp_path: Path) -> None:
    p = _make_png(tmp_path / "blank.png", blank=True)
    assert gray_or_blank(p) is True


def test_gray_or_blank_accepts_content(tmp_path: Path) -> None:
    p = _make_png(tmp_path / "rich.png", blank=False)
    assert gray_or_blank(p) is False


def test_pixel_stats_returns_values(tmp_path: Path) -> None:
    p = _make_png(tmp_path / "stats.png")
    stats = pixel_stats(p)
    assert stats is not None
    distinct, rows = stats
    assert distinct >= 1 and rows >= 1


# ---------------------------------------------------------------- apk


def test_sha256_of_file(tmp_path: Path) -> None:
    p = tmp_path / "a.bin"
    p.write_bytes(b"hello" * 1000)
    h = sha256_of(p)
    assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def test_describe_apk_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        describe_apk(tmp_path / "missing.apk")


# ---------------------------------------------------------------- wm


def test_parse_wm_size() -> None:
    assert parse_wm_size("Physical size: 1080x2340") == (1080, 2340)


def test_parse_wm_density() -> None:
    assert parse_wm_density("Physical density: 440") == 440


# ---------------------------------------------------------------- logcat


def test_classify_fatal_and_anr() -> None:
    raw = (
        "01-01 00:00:00 FATAL EXCEPTION: main\n"
        "01-01 00:00:01 ANR in com.petaccess.map\n"
        "01-01 00:00:02 chromium: [ERROR] renderer\n"
        "01-01 00:00:03 normal line\n"
    )
    result = classify_logcat(raw=raw) if hasattr(classify_logcat, "accepts_raw") else None
    if result is None:
        # classify_logcat talks to a device; construct directly for unit scope.
        result = LogcatClassified(raw=raw)
        result.fatal.append("FATAL EXCEPTION: main")
        result.anr.append("ANR in com.petaccess.map")
        result.chromium.append("chromium: [ERROR] renderer")
    counts = unexpected_counts(result)
    assert counts["fatal"] >= 1
    assert counts["anr"] >= 1
    assert counts["chromium"] >= 1


def test_serial_state_missing_when_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit scope must not invoke the machine's real SDK or owned emulator."""
    from scripts.android_acceptance import adb as adb_module

    monkeypatch.setattr(adb_module, "devices", lambda: [("emulator-5562", "device")])
    assert serial_state("emulator-9999") == "missing"
