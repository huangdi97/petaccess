"""Enforce the Android IME resize contract on Tauri generated manifests.

Tauri regenerates gen/android from configuration, so PetAccess must apply the
mobile shell requirement after tauri android init and before every APK build.
adjustResize keeps the WebView bounds honest on Android/WebView versions that
do not yet expose IME occlusion through the VisualViewport API.

This script intentionally edits only the generated MainActivity declaration.
It is idempotent and can also be used in --check mode.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_MANIFEST = Path(
    "apps/client-h5/src-tauri/gen/android/app/src/main/AndroidManifest.xml"
)
TARGET_VALUE = "adjustResize"

_ACTIVITY_RE = re.compile(
    r'(?P<open><activity\b[^>]*\bandroid:name\s*=\s*"[^"]*MainActivity"[^>]*)(?P<close>>)',
    re.DOTALL,
)
_SOFT_INPUT_RE = re.compile(
    r'android:windowSoftInputMode\s*=\s*"(?P<value>[^"]*)"'
)


class ManifestContractError(RuntimeError):
    """Raised when the generated Android manifest cannot satisfy the contract."""


def _main_activity_opening(manifest: str) -> re.Match[str]:
    match = _ACTIVITY_RE.search(manifest)
    if match is None:
        raise ManifestContractError("MainActivity declaration not found in AndroidManifest.xml")
    return match


def manifest_has_adjust_resize(manifest: str) -> bool:
    """Return True only when MainActivity explicitly requests adjustResize."""

    match = _main_activity_opening(manifest)
    attr = _SOFT_INPUT_RE.search(match.group("open"))
    return attr is not None and attr.group("value") == TARGET_VALUE


def patch_manifest_text(manifest: str) -> str:
    """Return manifest text with MainActivity pinned to adjustResize."""

    match = _main_activity_opening(manifest)
    opening = match.group("open")
    attr = _SOFT_INPUT_RE.search(opening)

    if attr is not None:
        patched_opening = _SOFT_INPUT_RE.sub(
            f'android:windowSoftInputMode="{TARGET_VALUE}"',
            opening,
            count=1,
        )
    else:
        line_start = manifest.rfind("\n", 0, match.start("open")) + 1
        activity_indent = manifest[line_start : match.start("open")]
        attribute_indent = f"{activity_indent}    "
        patched_opening = (
            f'{opening}\n{attribute_indent}'
            f'android:windowSoftInputMode="{TARGET_VALUE}"'
        )

    patched = (
        manifest[: match.start("open")]
        + patched_opening
        + manifest[match.end("open") :]
    )

    if not manifest_has_adjust_resize(patched):
        raise ManifestContractError("failed to apply adjustResize to MainActivity")
    return patched


def enforce(path: Path, *, check_only: bool) -> None:
    if not path.is_file():
        raise ManifestContractError(f"Android manifest not found: {path}")

    original = path.read_text(encoding="utf-8")
    if check_only:
        if not manifest_has_adjust_resize(original):
            raise ManifestContractError(
                f"{path}: MainActivity must declare "
                'android:windowSoftInputMode="adjustResize"'
            )
        print(f"PASS adjustResize: {path}")
        return

    patched = patch_manifest_text(original)
    if patched != original:
        path.write_text(patched, encoding="utf-8")
        print(f"PATCHED adjustResize: {path}")
    else:
        print(f"UNCHANGED adjustResize already present: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        enforce(args.manifest, check_only=args.check)
    except ManifestContractError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
