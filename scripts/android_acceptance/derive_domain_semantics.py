"""Derive product-truth semantic coverage from packaged Android CDP evidence.

This gate intentionally checks rendered Consumer copy from the packaged Tauri
WebView. Backend fixtures or unit tests cannot satisfy it by themselves.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = Path(
    os.environ.get(
        "PETACCESS_ANDROID_EVIDENCE_DIR",
        str(ROOT / "artifacts" / "android-preview-runtime"),
    )
)
JOURNEY = EVIDENCE_ROOT / "runtime" / "cdp_journey_playwright.json"
OUT = EVIDENCE_ROOT / "runtime" / "domain_semantics.json"

REQUIRED: dict[str, list[str]] = {
    "search": [
        "信息不足不等于允许或禁止",
        "明确允许",
        "有条件",
        "明确限制",
        "来源不一致",
    ],
    "place-overview": [
        "工作人员处理",
        "动物设施",
        "规则与现场",
    ],
    "place-space": [
        "不等于允许动物进入",
        "不代表正式准入规则",
    ],
    "reality": [
        "这里只展示经人工核验的现场事实",
        "工作人员处理与设施记录都不等于正式准入规则",
    ],
    "evidence": [
        "现场事实不代表正式准入规则",
        "工作人员处理不等于运营方政策",
        "设施存在不等于允许进入",
    ],
    "settings": [
        "不把信息不足解释成允许或禁止",
        "信息不足表示当前依据不足",
        "用户提交先进入待核验队列",
    ],
}


def main() -> int:
    if not JOURNEY.exists():
        raise RuntimeError(f"missing packaged WebView journey: {JOURNEY}")

    journey = json.loads(JOURNEY.read_text(encoding="utf-8"))
    routes = {
        row.get("name"): row
        for row in journey.get("routes", [])
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }

    checks: list[dict] = []
    failed = False
    for route_name, phrases in REQUIRED.items():
        row = routes.get(route_name)
        text = ""
        route_ok = bool(row and row.get("ok") is True)
        if row and isinstance(row.get("snapshot"), dict):
            text = str(row["snapshot"].get("text") or "")
        for phrase in phrases:
            ok = route_ok and phrase in text
            checks.append(
                {
                    "route": route_name,
                    "phrase": phrase,
                    "ok": ok,
                }
            )
            if not ok:
                failed = True

    payload = {
        "schemaVersion": 1,
        "result": "FAIL" if failed else "PASS",
        "source": str(JOURNEY),
        "requiredRoutes": sorted(REQUIRED),
        "checks": checks,
        "passed": sum(1 for row in checks if row["ok"]),
        "failed": sum(1 for row in checks if not row["ok"]),
        "invariants": {
            "unknownIsNotAllowed": True,
            "observationIsNotRule": True,
            "staffResponseIsNotOperatorPolicy": True,
            "facilityIsNotEntryPolicy": True,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
