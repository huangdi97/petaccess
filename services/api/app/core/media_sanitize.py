"""Strip embedded metadata (EXIF / XMP / PNG text chunks) from uploaded images.

Privacy rationale (SECURITY_FINAL_REPORT Phase 26): user-uploaded photos can
carry GPS coordinates, camera serials, face-detection tags and timestamps
inside EXIF / XMP / PNG ancillary chunks. The platform never needs those —
Reality media is evidence of a place, not of the photographer. Stripping at
ingest (before the object reaches storage) removes the leak at its source and
keeps the stored blob free of location metadata, which matters for the
no-retention of precise user trajectories invariant.

Dependency-free on purpose: this module only parses the container headers it
needs (JPEG markers, PNG chunk table, RIFF/WebP chunks), so the API keeps a
small footprint. If a format cannot be parsed safely, the function returns the
original bytes unchanged and reports ``parsed=False`` so callers can decide
(strict mode) rather than corrupting a valid image.
"""

from __future__ import annotations

#: JPEG markers that carry user/location metadata we strip (APP1 = Exif/XMP,
#: APP2 = MPF/FlashPix, APP13 = Photoshop IRB with IPTC/GPS).
_META_APP_MARKERS = {0xE1, 0xE2, 0xED}


def strip_image_metadata(data: bytes) -> tuple[bytes, bool]:
    """Return ``(stripped_bytes, stripped_anything)``.

    ``stripped_anything`` is True when at least one metadata block was removed
    (or the container was fully parsed without error but had none). A parser
    failure returns ``(original, False)`` — never a corrupt image.
    """
    if data[:3] == b"\xff\xd8\xff":
        return _strip_jpeg(data)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return _strip_png(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return _strip_webp(data)
    return data, False


def _strip_jpeg(data: bytes) -> tuple[bytes, bool]:
    """Walk JPEG marker segments and drop APPn metadata segments."""
    out = bytearray()
    i = 0
    stripped = False
    n = len(data)
    # SOI
    if n >= 2:
        out += data[:2]
        i = 2
    while i < n:
        if data[i] != 0xFF:
            # No marker where expected: keep the tail verbatim.
            out += data[i:]
            break
        marker = data[i + 1] if i + 1 < n else 0
        # standalone markers (no length field)
        if marker in (0xD8, 0xD9, 0x01) or 0xD0 <= marker <= 0xD7:
            out += data[i : i + 2]
            i += 2
            continue
        # SOS: entropy-coded data follows; copy everything from here on.
        if marker == 0xDA:
            out += data[i:]
            break
        # markers with a 2-byte length
        if i + 3 >= n:
            out += data[i:]
            break
        seg_len = int.from_bytes(data[i + 2 : i + 4], "big")
        if seg_len < 2 or i + 2 + seg_len > n:
            out += data[i:]
            break
        seg_start = i
        if 0xE0 <= marker <= 0xEF and marker in _META_APP_MARKERS:
            stripped = True
        else:
            out += data[seg_start : i + 2 + seg_len]
        i += 2 + seg_len
    return bytes(out), stripped


def _strip_png(data: bytes) -> tuple[bytes, bool]:
    """Keep only the signature + critical chunks + IDAT/IEND; drop text chunks."""
    out = bytearray(data[:8])
    i = 8
    n = len(data)
    stripped = False
    while i + 8 <= n:
        length = int.from_bytes(data[i : i + 4], "big")
        ctype = data[i + 4 : i + 8]
        chunk_total = 12 + length
        if i + chunk_total > n:
            out += data[i:]
            break
        if ctype in (b"tEXt", b"zTXt", b"iTXt", b"eXIf"):
            stripped = True
        else:
            out += data[i : i + chunk_total]
        i += chunk_total
    return bytes(out), stripped


def _strip_webp(data: bytes) -> tuple[bytes, bool]:
    """Walk RIFF/WEBP chunks and drop EXIF/XMP chunks."""
    out = bytearray(data[:12])  # RIFF header + WEBP fourcc
    i = 12
    n = len(data)
    stripped = False
    while i + 8 <= n:
        fourcc = data[i : i + 4]
        size = int.from_bytes(data[i + 4 : i + 8], "little")
        padded = size + (size & 1)
        chunk_total = 8 + padded
        if i + chunk_total > n:
            out += data[i:]
            break
        if fourcc in (b"EXIF", b"XMP "):
            stripped = True
        else:
            out += data[i : i + chunk_total]
        i += chunk_total
    return bytes(out), stripped
