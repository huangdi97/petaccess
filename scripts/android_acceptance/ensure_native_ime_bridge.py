"""Patch Tauri's generated MainActivity with a native IME inset bridge.

Android WebView before Chromium/WebView M139 can visibly show the software
keyboard without shrinking the web VisualViewport. PetAccess therefore keeps
the web heuristic for browsers/new WebViews but also publishes Android's
authoritative IME WindowInsets state into the packaged WebView.

The generated Android project is intentionally not committed, so this patch is
applied after every tauri android init and verified before APK build.
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
_BARE_ACTIVITY_RE = re.compile(
    r"(?m)^class\s+MainActivity\s*:\s*TauriActivity\(\)\s*$"
)

BRIDGE_BODY = r'''
import android.graphics.Rect
import android.os.Build
import android.view.WindowInsets
import android.webkit.WebView

class MainActivity : TauriActivity() {
  // PETACCESS_NATIVE_IME_BRIDGE
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
  }
}
'''.strip()


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


def patch_activity_text(source: str) -> str:
    package = _PACKAGE_RE.search(source)
    if package is None:
        raise ActivityContractError("package declaration not found in MainActivity.kt")

    if activity_has_bridge(source):
        return source

    if _BARE_ACTIVITY_RE.search(source) is None:
        raise ActivityContractError(
            "MainActivity.kt is no longer the expected bare TauriActivity scaffold; "
            "refusing to overwrite unknown native code"
        )

    return f"package {package.group('package')}\n\n{BRIDGE_BODY}\n"


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
