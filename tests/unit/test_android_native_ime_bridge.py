from pathlib import Path

import pytest
from scripts.android_acceptance.ensure_native_ime_bridge import (
    ActivityContractError,
    activity_has_bridge,
    enforce,
    patch_activity_text,
)


BARE = """package com.petaccess.map.preview

class MainActivity : TauriActivity()
"""


def test_patch_adds_native_ime_bridge() -> None:
    patched = patch_activity_text(BARE)

    assert activity_has_bridge(patched)
    assert "override fun onWebViewCreate(webView: WebView)" in patched
    assert "WindowInsets.Type.ime()" in patched
    assert 'window.dispatchEvent(new CustomEvent("petaccess:native-ime"' in patched


def test_patch_preserves_package_name() -> None:
    patched = patch_activity_text(BARE)

    assert patched.startswith("package com.petaccess.map.preview\n")


def test_patch_is_idempotent() -> None:
    once = patch_activity_text(BARE)
    twice = patch_activity_text(once)

    assert twice == once


def test_unknown_activity_body_is_rejected() -> None:
    custom = """package com.petaccess.map

class MainActivity : TauriActivity() {
  override fun onStart() {
    super.onStart()
  }
}
"""

    with pytest.raises(ActivityContractError):
        patch_activity_text(custom)


def test_enforce_patches_generated_activity(tmp_path: Path) -> None:
    activity = tmp_path / "com" / "petaccess" / "map" / "MainActivity.kt"
    activity.parent.mkdir(parents=True)
    activity.write_text(BARE, encoding="utf-8")

    resolved = enforce(tmp_path, check_only=False)
    enforce(tmp_path, check_only=True)

    assert resolved == activity
    assert activity_has_bridge(activity.read_text(encoding="utf-8"))


def test_multiple_activity_files_are_rejected(tmp_path: Path) -> None:
    for name in ("one", "two"):
        activity = tmp_path / name / "MainActivity.kt"
        activity.parent.mkdir(parents=True)
        activity.write_text(BARE, encoding="utf-8")

    with pytest.raises(ActivityContractError):
        enforce(tmp_path, check_only=False)
