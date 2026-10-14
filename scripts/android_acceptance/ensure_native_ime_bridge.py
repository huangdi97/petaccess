"""Patch Tauri's generated MainActivity with a native IME inset bridge.

Android WebView before Chromium/WebView M139 can visibly show the software
keyboard without shrinking the web VisualViewport. PetAccess therefore keeps
the web heuristic for browsers/new WebViews but also publishes Android's
authoritative IME WindowInsets state into the packaged WebView.

The generated Android project is intentionally not committed, so this patch is
applied after every tauri android init and verified before APK build. Existing
Tauri activity code such as edge-to-edge setup is preserved; the patch only
adds imports and bridge members.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_ACTIVITY_ROOT = Path(
    "apps/client-h5/src-tauri/gen/android/app/src/main/java"
)
BRIDGE_MARKER = "PETACCESS_NATIVE_IME_BRIDGE"

_PACKAGE_RE = re.compile(r"(?m)^package\s+(?P<package>[A-Za-z0-9_.]+)\s*$")
_ACTIVITY_CLASS_RE = re.compile(
    r"class\s+MainActivity\s*:\s*TauriActivity\(\)\s*\{"
)

_NATIVE_IMPORTS = """import android.graphics.Rect
import android.os.Build
import android.view.WindowInsets
import android.webkit.WebView"""

BRIDGE_MEMBERS = r'''  // PETACCESS_NATIVE_IME_BRIDGE
  private var lastImeVisible: Boolean? = null
  private var lastImeHeight: Int = -1

  override fun onWebViewCreate(webView: WebView) {
    val root = window.decorView

    root.setOnApplyWindowInsetsListener { view, insets ->
      if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
        val imeInsets = insets.getInsets(WindowInsets.Type.ime())
        publishImeState(webView, insets.isVisible(WindowInsets.Type.ime()), imeInsets.bottom)
      } else {
        publishLegacyImeState(webView, view.height)
      }
      insets
    }

    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
      root.viewTreeObserver.addOnGlobalLayoutListener {
        publishLegacyImeState(webView, root.height)
      }
    }

    root.post { root.requestApplyInsets() }
  }

  private fun publishLegacyImeState(webView: WebView, rootHeight: Int) {
    if (rootHeight <= 0) return

    val frame = Rect()
    window.decorView.getWindowVisibleDisplayFrame(frame)
    val occluded = (rootHeight - frame.bottom).coerceAtLeast(0)
    val visible = occluded >= (rootHeight * 0.15f).toInt()
    publishImeState(webView, visible, occluded)
  }

  private fun publishImeState(webView: WebView, visible: Boolean, height: Int) {
    if (lastImeVisible == visible && lastImeHeight == height) return
    lastImeVisible = visible
    lastImeHeight = height

    val script =
      """
      (() => {
        const detail = { visible: $visible, height: $height };
        window.__PETACCESS_NATIVE_IME__ = detail;
        window.dispatchEvent(new CustomEvent("petaccess:native-ime", { detail }));
      })();
      """.trimIndent()

    webView.post {
      webView.evaluateJavascript(script, null)
    }
  }'''


class ActivityContractError(RuntimeError):
    """Raised when the generated Tauri activity cannot be patched safely."""


def find_main_activity(root: Path) -> Path:
    matches = sorted(root.glob("**/MainActivity.kt"))
    if len(matches) != 1:
        raise ActivityContractError(
            f"expected exactly one MainActivity.kt under {root}, found {len(matches)}"
        )
    return matches[0]


def activity_has_bridge(source: str) -> bool:
    return BRIDGE_MARKER in source and "petaccess:native-ime" in source


def _insert_imports(source: str, package: re.Match[str]) -> str:
    missing = [
        line
        for line in _NATIVE_IMPORTS.splitlines()
        if line not in source
    ]
    if not missing:
        return source

    insertion = "\n" + "\n".join(missing)
    return source[: package.end()] + insertion + source[package.end() :]


def patch_activity_text(source: str) -> str:
    package = _PACKAGE_RE.search(source)
    if package is None:
        raise ActivityContractError("package declaration not found in MainActivity.kt")

    if activity_has_bridge(source):
        return source

    if "onWebViewCreate(" in source:
        raise ActivityContractError(
            "MainActivity.kt already overrides onWebViewCreate; refusing to merge "
            "the IME bridge into unknown WebView lifecycle code"
        )

    class_match = _ACTIVITY_CLASS_RE.search(source)
    if class_match is None:
        raise ActivityContractError(
            "MainActivity TauriActivity class declaration not found; refusing to "
            "modify unknown native code"
        )

    patched = _insert_imports(source, package)
    class_match = _ACTIVITY_CLASS_RE.search(patched)
    if class_match is None:
        raise ActivityContractError("MainActivity declaration disappeared after import patch")

    closing = patched.rfind("}")
    if closing <= class_match.end():
        raise ActivityContractError("MainActivity closing brace not found")

    before_closing = patched[:closing].rstrip()
    after_closing = patched[closing:]
    patched = f"{before_closing}\n\n{BRIDGE_MEMBERS}\n{after_closing}"

    if not activity_has_bridge(patched):
        raise ActivityContractError("failed to inject native IME bridge")
    return patched


def enforce(root: Path, *, check_only: bool) -> Path:
    activity = find_main_activity(root)
    original = activity.read_text(encoding="utf-8")

    if check_only:
        if not activity_has_bridge(original):
            raise ActivityContractError(f"{activity}: native IME bridge is missing")
        print(f"PASS native IME bridge: {activity}")
        return activity

    patched = patch_activity_text(original)
    if patched != original:
        activity.write_text(patched, encoding="utf-8")
        print(f"PATCHED native IME bridge: {activity}")
    else:
        print(f"UNCHANGED native IME bridge already present: {activity}")

    if not activity_has_bridge(activity.read_text(encoding="utf-8")):
        raise ActivityContractError("native IME bridge verification failed")
    return activity


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activity-root", type=Path, default=DEFAULT_ACTIVITY_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        enforce(args.activity_root, check_only=args.check)
    except ActivityContractError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
