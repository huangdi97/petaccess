from pathlib import Path

import pytest
from scripts.android_acceptance.ensure_adjust_resize import (
    ManifestContractError,
    enforce,
    manifest_has_adjust_resize,
    patch_manifest_text,
)


BASE = """<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <application>
    <activity
      android:name=".MainActivity"
      android:exported="true">
      <intent-filter>
        <action android:name="android.intent.action.MAIN" />
      </intent-filter>
    </activity>
  </application>
</manifest>
"""


def test_patch_adds_adjust_resize_to_main_activity() -> None:
    patched = patch_manifest_text(BASE)

    assert 'android:windowSoftInputMode="adjustResize"' in patched
    assert manifest_has_adjust_resize(patched)


def test_patch_replaces_existing_soft_input_mode() -> None:
    source = BASE.replace(
        'android:exported="true"',
        'android:exported="true" android:windowSoftInputMode="adjustPan"',
    )

    patched = patch_manifest_text(source)

    assert 'android:windowSoftInputMode="adjustPan"' not in patched
    assert 'android:windowSoftInputMode="adjustResize"' in patched


def test_patch_is_idempotent() -> None:
    once = patch_manifest_text(BASE)
    twice = patch_manifest_text(once)

    assert twice == once


def test_check_mode_rejects_missing_contract(tmp_path: Path) -> None:
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(BASE, encoding="utf-8")

    with pytest.raises(ManifestContractError):
        enforce(manifest, check_only=True)


def test_enforce_writes_and_then_checks(tmp_path: Path) -> None:
    manifest = tmp_path / "AndroidManifest.xml"
    manifest.write_text(BASE, encoding="utf-8")

    enforce(manifest, check_only=False)
    enforce(manifest, check_only=True)

    assert manifest_has_adjust_resize(manifest.read_text(encoding="utf-8"))


def test_missing_main_activity_is_rejected() -> None:
    with pytest.raises(ManifestContractError):
        patch_manifest_text("<manifest><application /></manifest>")
