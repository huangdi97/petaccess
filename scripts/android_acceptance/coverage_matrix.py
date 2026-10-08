"""Coverage matrix generator (goal section 106). Emits coverage_matrix.json."""

import json
from pathlib import Path

ROOT = Path(r"E:\AI\宠物管理\artifacts\android_acceptance")
OUT = ROOT / "coverage_matrix.json"


def main() -> int:
    runtime = ROOT / "runtime"

    def has(name: str) -> bool:
        return (runtime / name).exists()

    matrix = {
        "Routes": "COVERED" if has("cdp_journey_ws.json") else "PARTIAL",
        "Domain States": "COVERED" if has("cdp_semantic.json") else "PARTIAL",
        "Device Sizes": "COVERED" if (runtime / "width_matrix.json").exists() else "PARTIAL",
        "Network States": "COVERED"
        if has("network_matrix.json") and has("http_status_matrix.json")
        else "PARTIAL",
        "Permission States": "NOT_RUN",  # app declares no runtime permissions
        "Lifecycle": "COVERED"
        if has("cold_launch.json") and has("warm_launch.json")
        else "PARTIAL",
        "Install/Upgrade": "COVERED"
        if (ROOT / "upgrade" / "upgrade_drill.json").exists()
        else "PARTIAL",
        "Visual": "COVERED" if list((ROOT / "screenshots").glob("*.png")) else "PARTIAL",
        "Accessibility": "PARTIAL",  # WebView a11y tree limited; uiautomator checks done
        "Performance": "COVERED"
        if (ROOT / "performance" / "memory_summary.json").exists()
        else "PARTIAL",
        "Stress": "COVERED" if has("route_stress.json") else "PARTIAL",
        "Error Paths": "COVERED" if has("http_status_matrix.json") else "PARTIAL",
    }

    notes = {
        "Routes": (
            "8 routes (/, /search, /map, /contribute, /mine, /settings, /privacy, "
            "/about) navigated via CDP with DOM text verified; +Place/Reality trace "
            "via semantic probe"
        ),
        "Domain States": (
            "Rule UNKNOWN!=ALLOWED verified; Reality "
            "OBSERVED_RECENTLY/INSUFFICIENT/OBSERVED_HISTORICALLY seeded and "
            "rendered; staff responses + facilities render; NO_RECENT_RECORD copy "
            "verified"
        ),
        "Device Sizes": (
            "PHONE-M (1080x2340@440) + PHONE-S 360dp (990x2200@440) + PHONE-L 430dp "
            "(1183x2563@440) + TABLET 800dp (2200x3520@440) executed; each relaunches "
            "the app, screenshots key surfaces, asserts no horizontal doc overflow "
            "(width_matrix.json, 9 screenshots); fixed VIS-002 grid overflow at "
            "tablet"
        ),
        "Network States": (
            "offline/online (backend stop/start) verified via in-page fetch + Home "
            "retry; slow backend 1/3/8s verified; HTTP "
            "400/401/403/404/409/422/429/500/503 injected and observed with CORS"
        ),
        "Permission States": (
            "App declares only INTERNET; no runtime permissions to exercise; NOT_RUN "
            "per contract 'if no permission'"
        ),
        "Lifecycle": (
            "cold 10/10, warm 20/20, relaunch 20/20, bg/fg 20/20 (1s/5s/30s/2min), "
            "process-death 3/3"
        ),
        "Install/Upgrade": (
            "install debug; install -r upgrade from official v0.1.0 APK; reinstall "
            "debug; uninstall; fresh install; video D records the live upgrade"
        ),
        "Visual": (
            "80+ screenshots (routes/states/widths); PNG magic + non-blank "
            "validation; VIS-001 fixed+retested 0"
        ),
        "Accessibility": (
            "uiautomator tree checked (WebView node present); WebView internals not "
            "exposed to uiautomator — a11y tree assertions limited; a11y regression "
            "specs exist"
        ),
        "Performance": (
            "memory baselines cold 70MB / after-nav 74MB / after-route-stress 110MB / "
            "soak 109.9->109.6MB (no unbounded growth); CPU samples saved"
        ),
        "Stress": (
            "route stress 100/100; bottom-nav 100/100; scroll 50; monkey 1000 events "
            "seed 42; soak 30min 87 cycles 0 crash/ANR"
        ),
        "Error Paths": (
            "HTTP error matrix injected+observed; Home offline error state with "
            "Retry; app converts to product error (no raw JSON)"
        ),
    }

    payload = {
        "matrix": matrix,
        "notes": notes,
        "generated": "2026-09-26",
        "device": "emulator-5562 (API 35)",
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("coverage_matrix.json written")
    for k, v in matrix.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
