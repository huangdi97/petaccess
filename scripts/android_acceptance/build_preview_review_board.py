"""Build an offline HTML review board from packaged Android runtime evidence.

The board is for human visual review only. It never upgrades machine runtime
PASS into Human Visual Acceptance. Screenshots are referenced in-place so the
downloaded GitHub Actions artifact remains self-contained.
"""

from __future__ import annotations

import html
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(
    os.environ.get(
        "PETACCESS_ANDROID_EVIDENCE_DIR",
        str(REPO_ROOT / "artifacts" / "android_acceptance"),
    )
)
RUNTIME_DIR = EVIDENCE_ROOT / "runtime"
SCREENSHOT_DIR = EVIDENCE_ROOT / "screenshots"
OUT = EVIDENCE_ROOT / "ANDROID_RUNTIME_REVIEW_BOARD.html"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _relative(path: Path) -> str:
    return path.relative_to(EVIDENCE_ROOT).as_posix()


def _card(route: dict) -> str:
    snapshot = route.get("snapshot") if isinstance(route.get("snapshot"), dict) else {}
    screenshot_raw = route.get("screenshot")
    screenshot = Path(screenshot_raw) if isinstance(screenshot_raw, str) else None
    if screenshot is not None and not screenshot.is_absolute():
        screenshot = EVIDENCE_ROOT / screenshot

    if screenshot is None or not screenshot.exists():
        image = '<div class="missing">截图缺失 · 不得视为视觉验收完成</div>'
    else:
        src = html.escape(_relative(screenshot))
        image = (
            f'<a href="{src}"><img loading="lazy" src="{src}" '
            f'alt="{html.escape(str(route.get("name", "Android route")))} screenshot" /></a>'
        )

    ok = route.get("ok") is True
    status_class = "pass" if ok else "fail"
    status_text = "RUNTIME PASS" if ok else "RUNTIME FAIL"
    state = snapshot.get("uiState") or "-"
    fixture = snapshot.get("uiFixture") or "-"
    viewport = snapshot.get("viewport") if isinstance(snapshot.get("viewport"), dict) else {}
    doc = snapshot.get("document") if isinstance(snapshot.get("document"), dict) else {}
    viewport_size = f"{viewport.get('width', '-')}×{viewport.get('height', '-')}"
    document_size = f"{doc.get('scrollWidth', '-')}×{doc.get('scrollHeight', '-')}"
    overflow = html.escape(str(snapshot.get("horizontalOverflow", "-")))

    return f"""
    <article class="route-card">
      <header>
        <div>
          <span class="tag">{html.escape(str(route.get("tag", "-")))}</span>
          <h2>{html.escape(str(route.get("name", "unknown")))}</h2>
          <code>{html.escape(str(route.get("hash", "")))}</code>
        </div>
        <span class="status {status_class}">{status_text}</span>
      </header>
      <div class="shot">{image}</div>
      <dl>
        <div><dt>page</dt><dd>{html.escape(str(snapshot.get("uiPage") or "-"))}</dd></div>
        <div><dt>state</dt><dd>{html.escape(str(state))}</dd></div>
        <div><dt>fixture</dt><dd>{html.escape(str(fixture))}</dd></div>
        <div><dt>viewport</dt><dd>{viewport_size}</dd></div>
        <div><dt>document</dt><dd>{document_size}</dd></div>
        <div><dt>overflow</dt><dd>{overflow}</dd></div>
        <div><dt>safe top</dt><dd>{html.escape(str(snapshot.get("safeAreaTop", "-")))}</dd></div>
        <div><dt>content top</dt><dd>{html.escape(str(snapshot.get("contentTop", "-")))}</dd></div>
      </dl>
      {f'<p class="error">{html.escape(str(route.get("error")))}</p>' if route.get("error") else ""}
    </article>
    """


def _width_card(profile: dict, page: dict) -> str:
    profile_id = str(profile.get("profile") or "unknown")
    action = str(page.get("action") or "unknown")
    screenshot_raw = page.get("screenshot")
    screenshot = Path(screenshot_raw) if isinstance(screenshot_raw, str) else None
    if screenshot is not None and not screenshot.is_absolute():
        screenshot = EVIDENCE_ROOT / screenshot

    if screenshot is None or not screenshot.exists():
        image = '<div class="missing">截图缺失 · 该尺寸不得视为通过</div>'
    else:
        src = html.escape(_relative(screenshot))
        image = (
            f'<a href="{src}"><img loading="lazy" src="{src}" '
            f'alt="{html.escape(profile_id)} {html.escape(action)} screenshot" /></a>'
        )

    ok = page.get("ok") is True
    status_class = "pass" if ok else "fail"
    status_text = "SIZE PASS" if ok else "SIZE FAIL"
    viewport = page.get("viewport_width", "-")
    scroll = page.get("scroll_width", "-")
    safe_top = page.get("safe_area_top", "-")
    content_top = page.get("content_top", "-")

    return f"""
    <article class="route-card">
      <header>
        <div>
          <span class="tag">{html.escape(profile_id)}</span>
          <h2>{html.escape(action)}</h2>
          <code>{html.escape(str(profile.get("wm_size") or ""))}</code>
        </div>
        <span class="status {status_class}">{status_text}</span>
      </header>
      <div class="shot">{image}</div>
      <dl>
        <div><dt>viewport width</dt><dd>{html.escape(str(viewport))}</dd></div>
        <div><dt>scroll width</dt><dd>{html.escape(str(scroll))}</dd></div>
        <div><dt>safe top</dt><dd>{html.escape(str(safe_top))}</dd></div>
        <div><dt>content top</dt><dd>{html.escape(str(content_top))}</dd></div>
        <div><dt>wm density</dt><dd>{html.escape(str(profile.get("wm_density") or "-"))}</dd></div>
        <div><dt>overflow</dt><dd>
          {html.escape(str(page.get("horizontal_overflow", "-")))}
        </dd></div>
      </dl>
      {f'<p class="error">{html.escape(str(page.get("error")))}</p>' if page.get("error") else ""}
    </article>
    """


def main() -> int:
    journey = _load_json(RUNTIME_DIR / "cdp_journey_playwright.json")
    fast = _load_json(RUNTIME_DIR / "m3_fast.json")
    coverage = _load_json(EVIDENCE_ROOT / "coverage_matrix.json")
    width_matrix = _load_json(RUNTIME_DIR / "width_matrix.json")

    routes = journey.get("routes") if isinstance(journey.get("routes"), list) else []
    cards = "\n".join(_card(route) for route in routes)
    route_pass = sum(1 for route in routes if route.get("ok") is True)

    width_profiles = (
        width_matrix.get("profiles") if isinstance(width_matrix.get("profiles"), list) else []
    )
    width_cards = "\n".join(
        _width_card(profile, page)
        for profile in width_profiles
        if isinstance(profile, dict)
        for page in profile.get("pages", [])
        if isinstance(page, dict)
    )
    width_pass = sum(
        1
        for profile in width_profiles
        if isinstance(profile, dict)
        for page in profile.get("pages", [])
        if isinstance(page, dict) and page.get("ok") is True
    )
    width_total = sum(
        1
        for profile in width_profiles
        if isinstance(profile, dict)
        for page in profile.get("pages", [])
        if isinstance(page, dict)
    )
    fast_result = fast.get("result", "UNKNOWN")
    coverage_routes = (
        coverage.get("matrix", {}).get("Routes", "UNKNOWN")
        if isinstance(coverage.get("matrix"), dict)
        else "UNKNOWN"
    )
    coverage_auth = (
        coverage.get("matrix", {}).get("Authenticated States", "UNKNOWN")
        if isinstance(coverage.get("matrix"), dict)
        else "UNKNOWN"
    )
    coverage_sizes = (
        coverage.get("matrix", {}).get("Device Sizes", "UNKNOWN")
        if isinstance(coverage.get("matrix"), dict)
        else "UNKNOWN"
    )
    auth_routes = [route for route in routes if route.get("authenticated") is True]
    auth_pass = sum(1 for route in auth_routes if route.get("ok") is True)
    map_provider = journey.get("mapProviderSurface") or "unknown"

    html_doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>PetAccess · Android Runtime Review Board</title>
<style>
:root {{
  color-scheme: light;
  font-family:
    Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    "Microsoft YaHei", sans-serif;
  background: #f3f5ef;
  color: #183127;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 24px; max-width: 1800px; margin-inline: auto; }}
h1 {{ margin: 0; font-size: 28px; }}
h2 {{ margin: 3px 0 2px; font-size: 18px; }}
p {{ line-height: 1.6; }}
code {{ overflow-wrap: anywhere; }}
.summary {{
  display: grid;
  grid-template-columns: repeat(auto-fit,minmax(160px,1fr));
  gap: 10px;
  margin: 18px 0 24px;
}}
.summary div, .notice {{
  border: 1px solid #d6ddd2;
  border-radius: 14px;
  background: #fff;
  padding: 14px;
}}
.summary strong {{ display: block; margin-top: 5px; font-size: 20px; }}
.notice {{ border-left: 4px solid #90743e; }}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill,minmax(320px,1fr));
  gap: 18px;
}}
.route-card {{
  min-width: 0;
  background: #fff;
  border: 1px solid #d6ddd2;
  border-radius: 18px;
  padding: 14px;
  box-shadow: 0 4px 18px rgba(24,49,39,.06);
}}
.route-card header {{
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  min-height: 70px;
}}
.tag {{
  display: inline-block;
  font-size: 12px;
  color: #69776f;
}}
.status {{
  white-space: nowrap;
  font-size: 11px;
  font-weight: 700;
  border-radius: 999px;
  padding: 5px 8px;
}}
.status.pass {{ color: #245a3f; background: #e6f1e9; }}
.status.fail {{ color: #8b2931; background: #f8e7e9; }}
.shot {{
  margin-top: 12px;
  border-radius: 14px;
  overflow: hidden;
  background: #eef1ec;
  border: 1px solid #e0e5dc;
  min-height: 240px;
}}
.shot img {{
  display: block;
  width: 100%;
  height: auto;
  max-height: 780px;
  object-fit: contain;
  background: #eef1ec;
}}
.missing {{ padding: 30px; color: #8b2931; }}
dl {{
  display: grid;
  grid-template-columns: repeat(2,minmax(0,1fr));
  gap: 7px 12px;
  margin: 14px 0 0;
}}
dl div {{ min-width: 0; }}
dt {{ color: #78847d; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; }}
dd {{ margin: 2px 0 0; overflow-wrap: anywhere; font-size: 13px; }}
.error {{ color: #8b2931; font-size: 13px; }}
@media (max-width: 640px) {{
  body {{ padding: 12px; }}
  .grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<h1>PetAccess · Android Runtime Review Board</h1>
<p>这里展示的是打包后的 Tauri Android WebView 实际运行截图与语义证据，不是浏览器模拟图。</p>
<section class="summary">
  <div>CDP journey<strong>{html.escape(str(journey.get("result", "UNKNOWN")))}</strong></div>
  <div>Route cases<strong>{route_pass}/{len(routes)}</strong></div>
  <div>FAST<strong>{html.escape(str(fast_result))}</strong></div>
  <div>Route coverage<strong>{html.escape(str(coverage_routes))}</strong></div>
  <div>Authenticated<strong>{auth_pass}/{len(auth_routes)} · \
{html.escape(str(coverage_auth))}</strong></div>
  <div>Device sizes<strong>{width_pass}/{width_total} · \
{html.escape(str(coverage_sizes))}</strong></div>
  <div>Map provider<strong>{html.escape(str(map_provider))}</strong></div>
  <div>Human visual<strong>PENDING</strong></div>
</section>
<p class="notice"><strong>重要：</strong>
Runtime PASS 只证明路由身份、WebView 几何、安全区、overflow 与截图取证成立。
它不能替代你对视觉质量的人工判断；HUMAN_VISUAL_ACCEPTANCE 仍为 PENDING。
</p>
<section class="grid">
{cards if cards else "<p>没有找到当前 Android runtime route screenshot 证据。</p>"}
</section>
<h1 style="margin-top:32px">Responsive width matrix</h1>
<p>
同一个 packaged Android Preview 在 phone-m、约 360dp、约 430dp 与 800dp
下重启并重新验证核心页面。
</p>
<section class="grid">
{width_cards if width_cards else "<p>没有找到当前 Android width-matrix screenshot 证据。</p>"}
</section>
</body>
</html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html_doc, encoding="utf-8")
    print(f"Android review board: {OUT} routes={route_pass}/{len(routes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
