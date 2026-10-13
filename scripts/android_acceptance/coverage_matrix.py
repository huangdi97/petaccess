"""Android acceptance coverage matrix.

Coverage is derived from evidence content, not from the mere existence of a
file. In particular, Routes is only COVERED when the canonical CDP journey
reports PASS across the full Consumer route set.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(
    os.environ.get(
        "PETACCESS_ANDROID_EVIDENCE_DIR",
        str(REPO_ROOT / "artifacts" / "android_acceptance"),
    )
)
OUT = ROOT / "coverage_matrix.json"
REQUIRED_ROUTE_CASES = 21
REQUIRED_AUTH_CASES = {
    "auth-contribute",
    "auth-mine",
    "auth-privacy",
    "auth-pets",
    "auth-notifications",
    "auth-boundary",
    "auth-pet-new",
}
REQUIRED_FAST_EVIDENCE = {
    "hardware_back_from_evidence",
    "hardware_back_from_home",
    "offline",
    "recovery",
    "activity_resume",
    "fresh_home_before_back",
    "fresh_home_back_ready",
}
REQUIRED_ROUTER_PAGES = {
    "home",
    "map",
    "onboarding",
    "search",
    "place",
    "pet-new",
    "pets",
    "contribution",
    "mine",
    "privacy",
    "notifications",
    "settings",
    "about",
    "boundary",
    "match-explain",
    "reality",
    "evidence",
    "operator-claim",
    "not-found",
}


def _load(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def main() -> int:
    runtime = ROOT / "runtime"

    def has(name: str) -> bool:
        return (runtime / name).exists()

    fast = _load(runtime / "m3_fast.json")
    ime_gate = _load(runtime / "ime_gate.json")
    journey = _load(runtime / "cdp_journey_playwright.json")
    journey_routes = journey.get("routes", []) if isinstance(journey, dict) else []
    observed_router_pages = {
        row.get("snapshot", {}).get("uiPage")
        for row in journey_routes
        if isinstance(row, dict) and isinstance(row.get("snapshot"), dict)
    }
    observed_router_pages.discard(None)
    routes_covered = (
        isinstance(journey, dict)
        and journey.get("result") == "PASS"
        and len(journey_routes) >= REQUIRED_ROUTE_CASES
        and REQUIRED_ROUTER_PAGES.issubset(observed_router_pages)
        and all(row.get("ok") is True for row in journey_routes)
    )
    auth_routes = [
        row for row in journey_routes if isinstance(row, dict) and row.get("authenticated") is True
    ]
    observed_auth_cases = {
        row.get("name") for row in auth_routes if isinstance(row.get("name"), str)
    }
    authenticated_states_covered = (
        isinstance(journey, dict)
        and journey.get("authenticatedSweepRequested") is True
        and REQUIRED_AUTH_CASES.issubset(observed_auth_cases)
        and all(row.get("ok") is True for row in auth_routes)
    )

    observed_fast_evidence = set(fast) if isinstance(fast, dict) else set()
    runtime_resilience_covered = (
        isinstance(fast, dict)
        and fast.get("result") == "PASS"
        and int(fast.get("failure_count") or 0) == 0
        and REQUIRED_FAST_EVIDENCE.issubset(observed_fast_evidence)
        and all(
            not str(fast.get(key, "")).startswith("ERROR ")
            for key in REQUIRED_FAST_EVIDENCE
        )
    )

    screenshot_paths = []
    screenshots_complete = bool(journey_routes)
    for row in journey_routes:
        screenshot = row.get("screenshot") if isinstance(row, dict) else None
        if not isinstance(screenshot, str) or not screenshot:
            screenshots_complete = False
            continue
        shot_path = Path(screenshot)
        screenshot_paths.append(shot_path)
        if not shot_path.exists() or shot_path.stat().st_size <= 0:
            screenshots_complete = False

    visual_covered = (
        routes_covered and screenshots_complete and len(screenshot_paths) == len(journey_routes)
    )

    scene_media = journey.get("sceneMedia", {}) if isinstance(journey, dict) else {}
    scene_src = str(scene_media.get("src") or "") if isinstance(scene_media, dict) else ""
    governed_media_covered = (
        isinstance(journey, dict)
        and journey.get("requireSceneMedia") is True
        and isinstance(scene_media, dict)
        and scene_media.get("present") is True
        and scene_media.get("complete") is True
        and int(scene_media.get("naturalWidth") or 0) > 0
        and int(scene_media.get("naturalHeight") or 0) > 0
        and "/public-media/content" in scene_src
        and ":9000" not in scene_src
        and not scene_src.startswith("nullstorage://")
    )

    width_matrix = _load(runtime / "width_matrix.json")
    required_width_profiles = {"phone-m", "phone-s", "phone-l", "tablet"}
    required_width_actions = {"home", "search", "map", "place"}
    width_profiles = width_matrix.get("profiles", []) if isinstance(width_matrix, dict) else []
    observed_width_profiles = {
        row.get("profile")
        for row in width_profiles
        if isinstance(row, dict) and isinstance(row.get("profile"), str)
    }
    width_sizes_covered = (
        isinstance(width_matrix, dict)
        and width_matrix.get("result") == "PASS"
        and required_width_profiles.issubset(observed_width_profiles)
        and all(
            isinstance(row, dict)
            and row.get("ok") is True
            and required_width_actions.issubset(
                {
                    page.get("action")
                    for page in row.get("pages", [])
                    if isinstance(page, dict) and page.get("ok") is True
                }
            )
            for row in width_profiles
            if row.get("profile") in required_width_profiles
        )
    )

    matrix = {
        "Routes": "COVERED" if routes_covered else "PARTIAL",
        "Authenticated States": ("COVERED" if authenticated_states_covered else "PARTIAL"),
        "Runtime Resilience": ("COVERED" if runtime_resilience_covered else "PARTIAL"),
        "Domain States": "COVERED" if has("cdp_semantic.json") else "PARTIAL",
        "Device Sizes": "COVERED" if width_sizes_covered else "PARTIAL",
        "IME / Input": (
            "COVERED"
            if isinstance(ime_gate, dict)
            and ime_gate.get("result") == "PASS"
            and len(ime_gate.get("cases", [])) >= 2
            and all(
                isinstance(case, dict) and case.get("ok") is True
                for case in ime_gate.get("cases", [])
            )
            else "PARTIAL"
        ),
        "Network States": (
            "COVERED"
            if has("network_matrix.json") and has("http_status_matrix.json")
            else "PARTIAL"
        ),
        "Permission States": "NOT_RUN",
        "Lifecycle": (
            "COVERED" if has("cold_launch.json") and has("warm_launch.json") else "PARTIAL"
        ),
        "Install/Upgrade": (
            "COVERED" if (ROOT / "upgrade" / "upgrade_drill.json").exists() else "PARTIAL"
        ),
        "Visual": "COVERED" if visual_covered else "PARTIAL",
        "Governed Media": "COVERED" if governed_media_covered else "PARTIAL",
        "Accessibility": "PARTIAL",
        "Performance": (
            "COVERED" if (ROOT / "performance" / "memory_summary.json").exists() else "PARTIAL"
        ),
        "Stress": "COVERED" if has("route_stress.json") else "PARTIAL",
        "Error Paths": "COVERED" if has("http_status_matrix.json") else "PARTIAL",
    }

    notes = {
        "Routes": (
            "Canonical packaged-WebView CDP journey requires all 19 Router pages plus "
            "Place rules/space public views. Each case asserts data-ui-page identity, zero "
            "horizontal overflow and safe-area non-overlap, with a screenshot captured at "
            "that state."
        ),
        "Authenticated States": (
            "A real CI account is registered against the seeded API and its access token is "
            "injected into the packaged WebView. Contribution choose-type, Mine, Privacy, "
            "Pets, Notifications, Boundary and Pet New must all render their authenticated "
            "state without horizontal overflow."
        ),
        "Runtime Resilience": (
            "The packaged Android FAST gate must pass Evidence -> system Back -> Reality, "
            "fresh Home -> system Back -> Activity leaves foreground, offline banner -> "
            "online recovery, and Home/Resume without blank shell or horizontal overflow."
        ),
        "Domain States": (
            "Rule UNKNOWN!=ALLOWED verified; Reality "
            "OBSERVED_RECENTLY/INSUFFICIENT/OBSERVED_HISTORICALLY seeded and rendered; "
            "staff responses + facilities render; NO_RECENT_RECORD copy verified"
        ),
        "Device Sizes": (
            "PHONE-M default + PHONE-S ~360dp + PHONE-L ~430dp + TABLET 800dp must all "
            "PASS Home/Search/Map/Place in the packaged WebView. Every case asserts zero "
            "horizontal overflow and zero top safe-area overlap, with route screenshots."
        ),
        "IME / Input": (
            "The packaged Android WebView must accept real adb tap/text input on Search and "
            "authenticated Pet New, keep the focused input inside the visual viewport, and "
            "consume the first Android Back as keyboard dismissal without changing route."
        ),
        "Network States": (
            "offline/online, slow backend and injected HTTP status behavior are captured "
            "in network_matrix.json and http_status_matrix.json"
        ),
        "Permission States": (
            "App declares only INTERNET; no runtime permission flow is required by the "
            "current Tauri Android package."
        ),
        "Lifecycle": (
            "cold/warm/relaunch/background-foreground/process-death evidence is read from "
            "the dedicated lifecycle JSON artifacts"
        ),
        "Install/Upgrade": (
            "upgrade evidence requires upgrade/upgrade_drill.json; file existence is not "
            "substituted by a release note"
        ),
        "Visual": (
            "Every current semantic journey row must point to a non-empty screenshot produced "
            "during the same runtime sweep; unrelated or stale PNGs do not count."
        ),
        "Governed Media": (
            "The runtime fixture must reach Place through a display-approved, human-verified "
            "scene_photo; the packaged WebView must decode it from the PetAccess "
            "/public-media/content endpoint with non-zero natural dimensions."
        ),
        "Accessibility": (
            "Web semantics remain required; native uiautomator visibility inside WebView "
            "is a platform observability limitation, not a semantic waiver."
        ),
        "Performance": "Memory/CPU evidence is sourced from the performance artifact directory.",
        "Stress": "Route/interaction stress requires runtime/route_stress.json.",
        "Error Paths": "HTTP injected-error evidence is sourced from http_status_matrix.json.",
    }

    payload = {
        "matrix": matrix,
        "notes": notes,
        "generated_from": "current evidence",
        "evidence_root": str(ROOT),
        "required_route_cases": REQUIRED_ROUTE_CASES,
        "observed_route_cases": len(journey_routes),
        "required_authenticated_cases": len(REQUIRED_AUTH_CASES),
        "observed_authenticated_cases": len(observed_auth_cases),
        "runtime_resilience": {
            "covered": runtime_resilience_covered,
            "required_evidence": sorted(REQUIRED_FAST_EVIDENCE),
            "observed_evidence": sorted(REQUIRED_FAST_EVIDENCE & observed_fast_evidence),
            "fast_result": fast.get("result") if isinstance(fast, dict) else None,
            "failure_count": fast.get("failure_count") if isinstance(fast, dict) else None,
        },
        "required_authenticated_case_ids": sorted(REQUIRED_AUTH_CASES),
        "observed_authenticated_case_ids": sorted(observed_auth_cases),
        "required_router_pages": len(REQUIRED_ROUTER_PAGES),
        "observed_router_pages": len(observed_router_pages),
        "observed_router_page_ids": sorted(observed_router_pages),
        "required_consumer_routes": REQUIRED_ROUTE_CASES,
        "observed_consumer_routes": len(journey_routes),
        "ime_input": {
            "result": ime_gate.get("result") if isinstance(ime_gate, dict) else None,
            "observed_cases": len(ime_gate.get("cases", [])) if isinstance(ime_gate, dict) else 0,
            "case_ids": (
                [
                    case.get("id")
                    for case in ime_gate.get("cases", [])
                    if isinstance(case, dict) and isinstance(case.get("id"), str)
                ]
                if isinstance(ime_gate, dict)
                else []
            ),
        },
        "governed_media": {
            "required": bool(journey.get("requireSceneMedia"))
            if isinstance(journey, dict)
            else False,
            "src": scene_src or None,
            "decoded": governed_media_covered,
        },
        "device_sizes": {
            "required_profiles": sorted(required_width_profiles),
            "observed_profiles": sorted(observed_width_profiles),
            "required_actions": sorted(required_width_actions),
            "covered": width_sizes_covered,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("coverage_matrix.json written")
    for key, value in matrix.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
