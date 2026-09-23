"""media_sanitize — strip EXIF/XMP/PNG-text metadata from uploaded images.

Privacy invariant (Phase 26): user-uploaded photos must not carry GPS / camera
/ timestamp metadata into the object store. The sanitizer is dependency-free
and conservative: unparsable input passes through unchanged.
"""

from app.core.media_sanitize import strip_image_metadata

# Minimal valid containers built by hand so the test does not depend on Pillow.


def _jpeg_with_exif() -> bytes:
    # SOI + APP1(Exif) + DQT(0xDB) + SOF0(0xC0) + SOS + EOI
    app1 = b"\xff\xe1" + (16).to_bytes(2, "big") + b"Exif\x00\x00" + b"GPS\x00" * 4
    dqt = b"\xff\xdb" + (3).to_bytes(2, "big") + b"\x00"
    sof = b"\xff\xc0" + (11).to_bytes(2, "big") + b"\x08\x00\x01\x00\x01\x01\x01\x00"
    sos = b"\xff\xda" + (2).to_bytes(2, "big") + b"\x00"
    return b"\xff\xd8" + app1 + dqt + sof + sos + b"\x12\x34" + b"\xff\xd9"


def _jpeg_clean() -> bytes:
    dqt = b"\xff\xdb" + (3).to_bytes(2, "big") + b"\x00"
    sof = b"\xff\xc0" + (11).to_bytes(2, "big") + b"\x08\x00\x01\x00\x01\x01\x01\x00"
    sos = b"\xff\xda" + (2).to_bytes(2, "big") + b"\x00"
    return b"\xff\xd8" + dqt + sof + sos + b"\x12\x34" + b"\xff\xd9"


def _png_with_text() -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(ctype: bytes, payload: bytes) -> bytes:
        return len(payload).to_bytes(4, "big") + ctype + payload + b"\x00" * 4
        return len(payload).to_bytes(4, "big") + ctype + payload + b"\x00" * 4

    return (
        sig
        + chunk(b"IHDR", b"\x00" * 13)
        + chunk(b"tEXt", b"Comment\x00GPS=31.2,121.4")
        + chunk(b"IEND", b"")
    )


def _webp_with_exif() -> bytes:
    riff = b"RIFF" + (40).to_bytes(4, "little") + b"WEBP"
    vp8 = b"VP8 " + (10).to_bytes(4, "little") + b"\x00" * 10
    exif = b"EXIF" + (8).to_bytes(4, "little") + b"GPS\x00" * 2
    return riff + vp8 + exif


def test_jpeg_exif_stripped():
    out, stripped = strip_image_metadata(_jpeg_with_exif())
    assert stripped is True
    assert b"Exif" not in out
    assert out.startswith(b"\xff\xd8")
    assert out.endswith(b"\xff\xd9")


def test_jpeg_clean_unchanged():
    src = _jpeg_clean()
    out, stripped = strip_image_metadata(src)
    assert out == src
    assert stripped is False


def test_png_text_stripped():
    out, stripped = strip_image_metadata(_png_with_text())
    assert stripped is True
    assert b"tEXt" not in out
    assert b"GPS" not in out
    assert out.startswith(b"\x89PNG")
    assert b"IEND" in out


def test_webp_exif_stripped():
    out, stripped = strip_image_metadata(_webp_with_exif())
    assert stripped is True
    assert b"EXIF" not in out
    assert out.startswith(b"RIFF")
    assert b"WEBP" in out


def test_unknown_bytes_unchanged():
    src = b"\x00\x01\x02 not an image"
    out, stripped = strip_image_metadata(src)
    assert out == src
    assert stripped is False


def test_truncated_jpeg_unchanged():
    src = _jpeg_with_exif()[:12]  # cut mid-segment length field → unparsable
    out, stripped = strip_image_metadata(src)
    assert out == src
    assert stripped is False
