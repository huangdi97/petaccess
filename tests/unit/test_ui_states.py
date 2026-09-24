"""UI state-completeness guards (Master Goal §5.5, UI_UX_IMPLEMENTATION_SPEC §3/§10).

Master Goal §5.5 requires every core page to carry loading / skeleton / empty /
success / partial / stale / conflict / error / offline / permission-denied. The
honest way to keep that true as pages change is to assert it on the source: a
view that forgets its error branch fails here rather than in production.

These run without a database, a browser or a build step.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOKENS_TS = REPO / "packages" / "design-tokens" / "src" / "index.ts"
H5_SRC = REPO / "apps" / "client-h5" / "src"
H5_VIEWS = H5_SRC / "views"
H5_COMPONENTS = H5_SRC / "components"
H5_STYLES = H5_SRC / "styles.css"
ADMIN_STYLES = REPO / "apps" / "admin" / "src" / "styles.css"

PAGE_STATE_KEYS = [
    "LOADING",
    "EMPTY",
    "ERROR",
    "OFFLINE",
    "PARTIAL",
    "STALE",
    "CONFLICT",
    "PERMISSION_DENIED",
]

# Every core data-driven page must wire its data states — `loading` via a
# skeleton component, the rest via the shared StateMessage. Offline is a shell
# responsibility since M2 (V020 §29 GlobalOfflineBanner): the shell wires it
# once and every view inherits it, so it is asserted on the shell below, not
# per view.
REQUIRED_PER_VIEW = {
    "HomeView.vue": ("SkeletonList", "StateMessage"),
    "SearchView.vue": ("SkeletonList", "StateMessage"),
    "PlaceView.vue": ("SkeletonList", "StateMessage"),
    "MapView.vue": ("SkeletonList", "StateMessage"),
    "ContributeView.vue": ("StateMessage",),
    "MineView.vue": ("StateMessage",),
    "PetProfileView.vue": ("SkeletonList", "StateMessage"),
    "NotificationsView.vue": ("SkeletonList", "StateMessage"),
    "BoundaryView.vue": ("SkeletonList", "StateMessage"),
    "MatchExplainView.vue": ("StateMessage",),
}

# Views whose rendered content carries no data fetch (static pages, auth flow,
# form entry) declare the reason instead of bolting on a fake loading state
# (M3 E1): `@ui-static` = no data load; `@ui-form` = submit-flow errors are
# inline. Every route view must be in exactly one of the two maps.
DECLARED_STATIC = {
    "AboutView.vue": "@ui-static",
    "PrivacyView.vue": "@ui-static",
    "SettingsView.vue": "@ui-static",
    "OnboardingView.vue": "@ui-static",
    "NotFoundView.vue": "@ui-static",
    "PetNewView.vue": "@ui-form",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ------------------------------------------------------------- §5.5 vocabulary


def test_page_state_vocabulary_covers_every_required_state():
    ts = _read(TOKENS_TS)
    assert "PAGE_STATES" in ts, "PAGE_STATES vocabulary missing from design-tokens"
    block = ts.split("PAGE_STATES", 1)[1]
    for key in PAGE_STATE_KEYS:
        assert f"{key}:" in block, f"PAGE_STATES missing {key}"
    for field in ("icon:", "title:", "description:"):
        assert block.count(field) >= len(PAGE_STATE_KEYS), f"page state field '{field}' incomplete"


def test_page_states_are_never_colour_only():
    """§3/§10: a state needs words, not just a tint."""
    ts = _read(TOKENS_TS)
    block = ts.split("PAGE_STATES", 1)[1]
    # every entry must carry a non-empty title and description literal
    titles = re.findall(r'title:\s*"([^"]*)"', block)
    descriptions = re.findall(r'description:\s*"([^"]*)"', block)
    assert len(titles) >= len(PAGE_STATE_KEYS), "some page states have no title"
    assert len(descriptions) >= len(PAGE_STATE_KEYS), "some page states have no description"
    assert all(t.strip() for t in titles), "a page state has an empty title"
    assert all(d.strip() for d in descriptions), "a page state has an empty description"


def test_state_message_renders_icon_and_title():
    src = _read(H5_COMPONENTS / "StateMessage.vue")
    assert "state-message__icon" in src, "StateMessage must render the icon element"
    assert "state-message__title" in src, "StateMessage must render a text title"
    assert 'role="status"' in src, "StateMessage must announce itself to screen readers"


def test_skeleton_is_announced_and_has_a_card_and_line_variant():
    src = _read(H5_COMPONENTS / "SkeletonList.vue")
    assert "aria-busy" in src, "SkeletonList must mark the region busy"
    assert "skeleton--card" in src or "'skeleton--' + variant" in src
    assert "visually-hidden" in src, "SkeletonList must carry screen-reader text"


# --------------------------------------------------------- §5.5 per-view wiring


def test_core_views_wire_their_loading_error_and_offline_states():
    missing: list[str] = []
    covered = set(REQUIRED_PER_VIEW) | set(DECLARED_STATIC)
    # Every route view must pick one strategy — a new view that does neither
    # fails here instead of silently rendering a blank page on failure.
    for view in sorted(H5_VIEWS.glob("*.vue")):
        name = view.name
        if name not in covered:
            missing.append(f"{name}: no state strategy (REQUIRED_PER_VIEW / DECLARED_STATIC)")
    for name, needles in REQUIRED_PER_VIEW.items():
        path = H5_VIEWS / name
        assert path.exists(), f"core view {name} missing"
        src = _read(path)
        for needle in needles:
            if needle not in src:
                missing.append(f"{name}: {needle}")
    for name, marker in DECLARED_STATIC.items():
        src = _read(H5_VIEWS / name)
        if marker not in src:
            missing.append(f"{name}: missing {marker}")
    # Offline is a shell-level concern (M2 §29): the global banner renders once
    # in ConsumerAppShell and covers every route; per-view offline duplication
    # would defeat the global offline foundation.
    shell = _read(H5_COMPONENTS / "shell" / "ConsumerAppShell.vue")
    if "GlobalOfflineBanner" not in shell:
        missing.append("ConsumerAppShell.vue: GlobalOfflineBanner")
    assert not missing, "core views are missing UI states: " + "; ".join(missing)


def test_offline_state_uses_a_shared_composable_not_ad_hoc_detection():
    composable = H5_SRC / "composables" / "useOnline.ts"
    assert composable.exists(), "useOnline composable missing"
    src = _read(composable)
    assert "navigator.onLine" in src
    # The product must not silently queue writes while offline.
    assert "不接受提交" in src or "does NOT queue" in src


# --------------------------------------------------- §10 reduced motion / a11y


def test_skeleton_animation_is_disabled_under_reduced_motion():
    for label, styles in (("h5", H5_STYLES), ("admin", ADMIN_STYLES)):
        text = _read(styles)
        assert "prefers-reduced-motion" in text, f"{label} stylesheet has no reduced-motion block"
        # the reduced-motion block must actually neutralise the shimmer
        tail = text.split("prefers-reduced-motion", 1)[1]
        assert "animation: none" in tail, f"{label} skeleton still animates under reduced motion"


def test_shared_state_styles_are_present_in_both_apps():
    for label, styles in (("h5", H5_STYLES), ("admin", ADMIN_STYLES)):
        text = _read(styles)
        for cls in (".skeleton", ".empty-state" if label == "admin" else ".state-message"):
            assert cls in text, f"{label} stylesheet missing {cls}"
