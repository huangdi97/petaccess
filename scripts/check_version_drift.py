#!/usr/bin/env python3
"""v0.1.0 version single-source-of-truth gate (Phase AE).

Checks that every publishable surface declares the SAME version and returns
non-zero on drift so CI can block a release with mismatched versions.

Checked surfaces:
- root package.json (workspace version)
- apps/client-h5/package.json
- apps/admin/package.json
- apps/client/package.json
- packages/design-tokens/package.json
- packages/api-client/package.json
- packages/client-core/package.json
- apps/client-h5/src-tauri/tauri.conf.json (bundle version)
- apps/client-h5/src-tauri/Cargo.toml  (crate version)
- Android versionName comes from tauri.conf via gen/tauri.properties; the
  canonical source is tauri.conf.json, which this script checks. The Android
  APK metadata is verified at build time (aapt2 badging, see
  docs/release/ANDROID_SIGNING.md).

Expected value: 0.1.0
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = "0.1.0"

PACKAGE_JSONS = [
    "package.json",
    "apps/client-h5/package.json",
    "apps/admin/package.json",
    "apps/client/package.json",
    "packages/design-tokens/package.json",
    "packages/api-client/package.json",
    "packages/client-core/package.json",
]

#: (path, regex, group) for non-JSON version sources
TEXT_SOURCES = [
    ("apps/client-h5/src-tauri/tauri.conf.json", r'"version"\s*:\s*"([^"]+)"', 1),
    ("apps/client-h5/src-tauri/Cargo.toml", r'^version\s*=\s*"([^"]+)"', 1),
]


def check_package_json(rel: str, found: list[str], errors: list[str]) -> None:
    p = ROOT / rel
    if not p.exists():
        errors.append(f"{rel}: missing")
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    version = data.get("version")
    found.append(f"{rel}: {version}")
    if version != EXPECTED:
        errors.append(f"{rel}: expected {EXPECTED}, got {version!r}")


def check_text(rel: str, pattern: str, group: int, found: list[str], errors: list[str]) -> None:
    p = ROOT / rel
    if not p.exists():
        errors.append(f"{rel}: missing")
        return
    m = re.search(pattern, p.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        errors.append(f"{rel}: version pattern not found")
        return
    version = m.group(group)
    found.append(f"{rel}: {version}")
    if version != EXPECTED:
        errors.append(f"{rel}: expected {EXPECTED}, got {version!r}")


def main() -> int:
    found: list[str] = []
    errors: list[str] = []
    for rel in PACKAGE_JSONS:
        check_package_json(rel, found, errors)
    for rel, pat, grp in TEXT_SOURCES:
        check_text(rel, pat, grp, found, errors)

    print("VERSION_SSOT check (expected 0.1.0)")
    for line in found:
        print(f"  {line}")
    if errors:
        for e in errors:
            print(f"  DRIFT: {e}")
        print("RESULT: FAIL (VERSION_DRIFT > 0)")
        return 1
    print("RESULT: PASS (VERSION_DRIFT = 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
