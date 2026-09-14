"""Design-token and neutral-copy guards (UI_UX_IMPLEMENTATION_SPEC §3/§8/§9).

The spec fixes two things that must not drift as the UI grows:

  §3  A status is icon + text + colour — never colour alone.
  §8  Copy is neutral: no ranking, no "bad venue", no "civilised index".
  §9  Tokens exist in one place (packages/design-tokens) and are consumed by the
      apps rather than re-declared.

These are source-level guards so they run without a database, a browser or a
build step. They are deliberately strict about *user-facing* files and silent
about comments, so documenting a forbidden term does not trip the guard.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOKENS_TS = REPO / "packages" / "design-tokens" / "src" / "index.ts"
TOKENS_CSS = REPO / "packages" / "design-tokens" / "src" / "tokens.css"
H5_SRC = REPO / "apps" / "client-h5" / "src"
ADMIN_SRC = REPO / "apps" / "admin" / "src"

STATUS_KEYS = ["ALLOWED", "CONDITIONAL", "RESTRICTED", "UNKNOWN", "CONFLICT", "STALE"]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _user_facing_sources() -> list[Path]:
    out: list[Path] = []
    for root in (H5_SRC, ADMIN_SRC):
        for ext in ("*.vue", "*.ts"):
            out.extend(sorted(root.rglob(ext)))
    return out


def _strip_comments(text: str) -> str:
    """Drop // line comments and /* */ blocks so documented terms do not count."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(?m)^\s*//.*$", "", text)
    return text


# --------------------------------------------------------------- §9 tokens


def test_design_token_package_exists_and_is_the_single_source():
    assert TOKENS_TS.exists(), "packages/design-tokens/src/index.ts missing"
    assert TOKENS_CSS.exists(), "packages/design-tokens/src/tokens.css missing"
    css = _read(TOKENS_CSS)
    for group in ("color", "space", "radius", "font", "elevation", "motion", "layout"):
        assert f"--pa-{group}" in css, f"token group '{group}' missing from tokens.css"


def test_every_status_has_icon_text_and_colour():
    """§3: no status may be expressible by colour alone."""
    ts = _read(TOKENS_TS)
    block = ts.split("STATUS_SEMANTICS", 1)[1]
    for key in STATUS_KEYS:
        assert f"{key}:" in block, f"STATUS_SEMANTICS missing {key}"
    for field in ("label:", "icon:", "ariaLabel:", "colorVar:", "bgVar:"):
        assert block.count(field) >= len(STATUS_KEYS), f"status field '{field}' incomplete"


def test_status_badge_component_renders_icon_and_label():
    badge = H5_SRC / "components" / "StatusBadge.vue"
    assert badge.exists(), "StatusBadge.vue missing"
    src = _read(badge)
    assert "status-badge__icon" in src, "StatusBadge must render the icon element"
    assert "semantics.label" in src, "StatusBadge must render the text label"
    assert "aria" in src, "StatusBadge must expose an accessible label"


def test_app_styles_consume_tokens_instead_of_redeclaring_them():
    for label, styles in (
        ("client-h5", H5_SRC / "styles.css"),
        ("admin", ADMIN_SRC / "styles.css"),
    ):
        text = _read(styles)
        assert "@petaccess/design-tokens/tokens.css" in text, (
            f"{label} must import the shared token sheet"
        )


def test_both_apps_declare_the_token_package_as_a_dependency():
    """§9: the apps depend on the package, they do not vendor a copy."""
    for app in ("client-h5", "admin"):
        pkg = json.loads(_read(REPO / "apps" / app / "package.json"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        assert "@petaccess/design-tokens" in deps, f"{app} does not depend on the token package"


def test_app_stylesheets_and_components_have_no_hardcoded_colours():
    """§9: every colour resolves to a token, so one edit restyles everything.

    Raw hex/rgb literals in an app file are the failure mode this guards: they
    silently opt out of the design system and cannot be themed.
    """
    literal = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(")
    offenders: list[str] = []
    for root in (H5_SRC, ADMIN_SRC):
        for path in sorted(list(root.rglob("*.css")) + list(root.rglob("*.vue"))):
            source = _strip_comments(_read(path))
            for match in literal.finditer(source):
                offenders.append(f"{path.relative_to(REPO)}: {match.group(0)}")
    assert not offenders, "hard-coded colour outside the token package: " + "; ".join(offenders)


def test_admin_reuses_the_shared_status_and_source_badges():
    """Admin must not re-invent the status vocabulary as bare coloured pills."""
    for name, must_have in (
        ("StatusBadge.vue", ("status-badge__icon", "semantics.label", "aria")),
        ("SourceBadge.vue", ("source-badge", "badgeForSourceType")),
    ):
        path = ADMIN_SRC / "components" / name
        assert path.exists(), f"admin/{name} missing"
        src = _read(path)
        for needle in must_have:
            assert needle in src, f"admin/{name} must contain {needle!r}"


# ------------------------------------------------------------- §8 neutral copy


def test_no_forbidden_copy_in_user_facing_sources():
    ts = _read(TOKENS_TS)
    # the array literal is `export const FORBIDDEN_COPY: readonly string[] = [ ... ] as const;`
    body = ts.split("FORBIDDEN_COPY", 1)[1]
    literal = body.split("= [", 1)[1].split("] as const", 1)[0]
    forbidden = re.findall(r'"([^"]+)"', literal)
    assert forbidden, "FORBIDDEN_COPY list is empty"

    offenders: list[str] = []
    for path in _user_facing_sources():
        source = _strip_comments(_read(path))
        for term in forbidden:
            if term in source:
                offenders.append(f"{path.relative_to(REPO)}: '{term}'")
    assert not offenders, "value-laden copy found: " + "; ".join(offenders)


def test_unknown_is_never_presented_as_allowed():
    """§2.10: UNKNOWN must never be worded as permission."""
    ts = _read(TOKENS_TS)
    assert '"尚未核验"' in ts
    assert "不代表允许" in ts


def test_observation_disclaimer_present():
    ts = _read(TOKENS_TS)
    assert "现场记录 ≠ 场所正式政策" in ts
