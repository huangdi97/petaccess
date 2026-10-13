#!/usr/bin/env python3
"""Engineering quality gate for petaccess (M1 + v0.2.0 M1 §40) — entry point.

Aggregates the check functions from `engineering_quality_checks.py`,
`engineering_quality_scan.py`, `engineering_quality_scan2.py`
(silent-catch, magic-status) and `engineering_quality_scan3.py`
(dead-code, duplicate-config), and applies the explicit exemption registry
(`scripts/gate_exemptions.json`). Every exemption must reference a documented
reason in docs/audit/V010_TECH_DEBT_REGISTER.md — no path-based blanket
ignores.

Rules enforced (Master Goal §40):
file>300 / file>250 / vue>200 / vue>150 / ts>300 / fn>60 / cyclo>15 /
cyclo>10 / cycle / type-escape / todo / hardcoded-color /
silent-catch / magic-status / dead-code / duplicate-config

Usage:
    uv run python scripts/check_engineering_quality.py            # full gate
    uv run python scripts/check_engineering_quality.py --json     # machine report
    uv run python scripts/check_engineering_quality.py --dump     # all violations

Exit code: 0 = PASS (no unregistered FAIL), 1 = FAIL.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engineering_quality_checks import check_functions, check_size, dependency_cycles
from engineering_quality_scan import check_todos, check_ts_colors, check_type_escapes
from engineering_quality_scan2 import check_magic_status, check_silent_catches
from engineering_quality_scan3 import check_dead_code, check_duplicate_config

ROOT = Path(__file__).resolve().parent.parent
EXEMPTIONS_FILE = ROOT / "scripts" / "gate_exemptions.json"
PY_ROOTS = [ROOT / "services/api/app", ROOT / "services/worker"]
TS_ROOTS = [ROOT / "apps/client-h5/src", ROOT / "apps/admin/src", ROOT / "packages/client-core/src"]


def check_consumer_runtime_boundary() -> list[dict]:
    """Keep release artifacts on the canonical Vue Consumer + Tauri path."""

    violations: list[dict] = []
    release_path = ROOT / ".github" / "workflows" / "release-ci.yml"
    release_text = release_path.read_text(encoding="utf-8")
    release_without_canonical = release_text.replace("apps/client-h5", "")

    if "tauri android build" not in release_text or "apps/client-h5" not in release_text:
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": ".github/workflows/release-ci.yml",
                "severity": "FAIL",
                "detail": "Android release must build apps/client-h5 through Tauri.",
            }
        )
    if "apps/client/" in release_without_canonical or "HBuilderX" in release_text:
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": ".github/workflows/release-ci.yml",
                "severity": "FAIL",
                "detail": "Legacy apps/client must never participate in current release CI.",
            }
        )

    if "tauri.preview.conf" in release_text or "com.petaccess.map.preview" in release_text:
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": ".github/workflows/release-ci.yml",
                "severity": "FAIL",
                "detail": "Release CI must never consume the Android Preview flavor.",
            }
        )

    required_release_runtime_markers = (
        "PETACCESS_PUBLIC_API_BASE",
        "VITE_TAURI_API_BASE",
        "VITE_TAURI_ANDROID_API_BASE",
        "generate_tauri_release_config.cjs",
        "tauri.release.generated.json",
        "--config src-tauri/tauri.release.generated.json",
    )
    if any(marker not in release_text for marker in required_release_runtime_markers):
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": ".github/workflows/release-ci.yml",
                "severity": "FAIL",
                "detail": (
                    "Signed Windows/Android release builds must fail closed on an explicit "
                    "HTTPS PetAccess API base and strict generated Tauri CSP."
                ),
            }
        )
    release_config_generator = ROOT / "scripts" / "release" / "generate_tauri_release_config.cjs"
    if not release_config_generator.exists():
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": "scripts/release/generate_tauri_release_config.cjs",
                "severity": "FAIL",
                "detail": "Signed-release runtime config generator is required.",
            }
        )

    required_android_sdk = ("platforms;android-36", "build-tools;36.0.0")
    if any(package not in release_text for package in required_android_sdk):
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": ".github/workflows/release-ci.yml",
                "severity": "FAIL",
                "detail": "Android release CI must install API 36 and Build Tools 36.0.0.",
            }
        )

    required_universal_apk_markers = (
        "--apk",
        "outputs/apk/universal/release",
        "arm64-v8a",
        "armeabi-v7a",
        "x86_64",
        "RELEASE_ANDROID_BADGING.txt",
    )
    if any(marker not in release_text for marker in required_universal_apk_markers):
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": ".github/workflows/release-ci.yml",
                "severity": "FAIL",
                "detail": "Android release APK must be verified universal and multi-ABI.",
            }
        )

    canonical_tauri_path = ROOT / "apps" / "client-h5" / "src-tauri" / "tauri.conf.json"
    canonical_tauri = json.loads(canonical_tauri_path.read_text(encoding="utf-8"))
    if canonical_tauri.get("identifier") != "com.petaccess.map":
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": "apps/client-h5/src-tauri/tauri.conf.json",
                "severity": "FAIL",
                "detail": "Canonical Tauri application id must remain com.petaccess.map.",
            }
        )

    preview_config_path = ROOT / "apps" / "client-h5" / "src-tauri" / "tauri.preview.conf.json"
    preview_workflow_path = ROOT / ".github" / "workflows" / "android-preview.yml"
    if preview_config_path.exists() and preview_workflow_path.exists():
        preview_config = json.loads(preview_config_path.read_text(encoding="utf-8"))
        preview_text = preview_workflow_path.read_text(encoding="utf-8")
        if preview_config.get("identifier") != "com.petaccess.map.preview":
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": "apps/client-h5/src-tauri/tauri.preview.conf.json",
                    "severity": "FAIL",
                    "detail": "Android Preview must use the isolated preview application id.",
                }
            )
        preview_android = preview_config.get("bundle", {}).get("android", {})
        if preview_android.get("debugApplicationIdSuffix") is not None:
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": "apps/client-h5/src-tauri/tauri.preview.conf.json",
                    "severity": "FAIL",
                    "detail": (
                        "Preview must keep debugApplicationIdSuffix=null and use its explicit "
                        "preview identifier instead."
                    ),
                }
            )
        if "tauri.preview.conf.json" not in preview_text:
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": ".github/workflows/android-preview.yml",
                    "severity": "FAIL",
                    "detail": "Preview workflow must build through the isolated Tauri config.",
                }
            )
        if "ANDROID_KEYSTORE_BASE64" in preview_text or "release.keystore" in preview_text:
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": ".github/workflows/android-preview.yml",
                    "severity": "FAIL",
                    "detail": "Preview workflow must not consume the release signing identity.",
                }
            )

        if any(package not in preview_text for package in required_android_sdk):
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": ".github/workflows/android-preview.yml",
                    "severity": "FAIL",
                    "detail": (
                        "Android Preview CI must explicitly install API 36 and Build Tools 36.0.0."
                    ),
                }
            )

        required_preview_contract_triggers = (
            "packages/api-client/**",
            "services/api/**",
            "scripts/isolated_db.py",
            "scripts/dev_api_server.py",
            "pyproject.toml",
            "uv.lock",
        )
        if any(trigger not in preview_text for trigger in required_preview_contract_triggers):
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": ".github/workflows/android-preview.yml",
                    "severity": "FAIL",
                    "detail": (
                        "Android Preview must rerun when its API contract, seeded DB bootstrap, "
                        "API server bootstrap or Python dependency lock changes."
                    ),
                }
            )

    phone_preview_workflow_path = ROOT / ".github" / "workflows" / "android-phone-preview.yml"
    if phone_preview_workflow_path.exists():
        phone_preview_text = phone_preview_workflow_path.read_text(encoding="utf-8")
        required_phone_preview_markers = (
            'url.protocol !== "https:"',
            "com.petaccess.map.preview",
            "release_signature=NO",
            "store_release_artifact=NO",
            "require_real_map",
            "/ai/map/config",
            "/ai/map/translate",
            'translated?.provider !== "tencent"',
            'translated?.coordinate_system !== "GCJ-02"',
        )
        if any(marker not in phone_preview_text for marker in required_phone_preview_markers):
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": ".github/workflows/android-phone-preview.yml",
                    "severity": "FAIL",
                    "detail": (
                        "Phone Preview must remain HTTPS-only, use the isolated Preview "
                        "package, and declare that it is not a signed/store Release."
                    ),
                }
            )

        forbidden_phone_preview_markers = (
            "allow_insecure_http",
            "http://localhost:*",
            "http://127.0.0.1:*",
            "http://10.0.2.2:*",
            "ws://10.0.2.2:*",
            "ANDROID_KEYSTORE_BASE64",
            "release.keystore",
        )
        if any(marker in phone_preview_text for marker in forbidden_phone_preview_markers):
            violations.append(
                {
                    "rule": "runtime-boundary",
                    "path": ".github/workflows/android-phone-preview.yml",
                    "severity": "FAIL",
                    "detail": (
                        "Standalone Phone Preview must not regain insecure HTTP/local "
                        "development origins or consume the release signing identity."
                    ),
                }
            )

    legacy_package = json.loads(
        (ROOT / "apps" / "client" / "package.json").read_text(encoding="utf-8")
    )
    if legacy_package.get("petaccessStatus") != "legacy-reference-only":
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": "apps/client/package.json",
                "severity": "FAIL",
                "detail": "Historical uni-app x client must stay explicitly legacy-reference-only.",
            }
        )
    canonical_package = json.loads(
        (ROOT / "apps" / "client-h5" / "package.json").read_text(encoding="utf-8")
    )
    if canonical_package.get("petaccessRole") != "canonical-consumer":
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": "apps/client-h5/package.json",
                "severity": "FAIL",
                "detail": "apps/client-h5 must remain the canonical Consumer implementation.",
            }
        )
    if not (ROOT / "apps" / "client" / "README.md").exists():
        violations.append(
            {
                "rule": "runtime-boundary",
                "path": "apps/client/README.md",
                "severity": "FAIL",
                "detail": "Legacy client freeze notice is required.",
            }
        )
    return violations


def load_exemptions() -> list[dict]:
    if not EXEMPTIONS_FILE.exists():
        return []
    data = json.loads(EXEMPTIONS_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "exemptions" not in data:
        raise SystemExit(f"invalid exemptions file: {EXEMPTIONS_FILE}")
    return data["exemptions"]


def collect() -> list[dict]:
    exemptions = load_exemptions()
    out: list[dict] = []
    out += check_size(exemptions, PY_ROOTS, TS_ROOTS)
    out += check_functions(exemptions, PY_ROOTS)
    cycles = dependency_cycles(PY_ROOTS)
    out += [{"rule": "cycle", "path": "**", "severity": "FAIL", "detail": c} for c in cycles]
    out += check_type_escapes(exemptions, PY_ROOTS, TS_ROOTS)
    out += check_todos(exemptions, PY_ROOTS, TS_ROOTS)
    out += check_ts_colors(exemptions, TS_ROOTS)
    out += check_silent_catches(exemptions, PY_ROOTS, TS_ROOTS)
    out += check_magic_status(exemptions, PY_ROOTS)
    out += check_dead_code(exemptions, PY_ROOTS)
    out += check_duplicate_config(exemptions)
    out += check_consumer_runtime_boundary()
    return out


def render_human(violations: list[dict]) -> str:
    lines = ["engineering quality gate summary"]
    for sev, label in (("FAIL", "FAIL"), ("REVIEW", "review"), ("WARN", "warn")):
        hits = [v for v in violations if v["severity"] == sev]
        lines.append(f"  {label:<7s}{len(hits)}")
        for v in hits[:12]:
            lines.append(f"    {v['rule']:15s} {v['path']} :: {v['detail']}")
        if len(hits) > 12:
            lines.append(f"    ... {len(hits) - 12} more")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="petaccess engineering quality gate (M1 + §40)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable report")
    ap.add_argument("--dump", action="store_true", help="print every violation")
    args = ap.parse_args()

    violations = collect()
    fails = [v for v in violations if v["severity"] == "FAIL"]
    review = [v for v in violations if v["severity"] == "REVIEW"]
    warns = [v for v in violations if v["severity"] == "WARN"]

    if args.json:
        json.dump(
            {
                "violations": violations,
                "fail": len(fails),
                "review": len(review),
                "warn": len(warns),
            },
            sys.stdout,
            indent=2,
        )
        return 1 if fails else 0
    if args.dump:
        for v in violations:
            print(f"[{v['severity']:<6}] {v['rule']:15s} {v['path']} :: {v['detail']}")
        return 1 if fails else 0
    print(render_human(violations))
    status = "FAIL" if fails else "PASS"
    print(f"RESULT: {status} ({len(fails)} FAIL / {len(review)} REVIEW / {len(warns)} WARN)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
