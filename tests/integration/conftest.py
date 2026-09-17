"""Integration-suite preconditions: environment *profiles*, not test data.

The suite runs against a disposable `TEST` database (enforced by
`tests/conftest.py`). Two profiles exist, and the difference is deliberate:

``demo``
    `scripts/isolated_db.py --role TEST --reset` — the demo seed only. Every test
    that builds its own fixture passes here. This is the default and the profile
    CI uses.

``pilot``
    the demo seed **plus** the real-pilot evidence chain for the ten places in
    `docs/reality_audit/`, i.e. the 37 candidates of the signed register and
    their source/artifact/bundle lineage. Provisioned by
    `scripts/real_pilot_ingest.py` against an API pointed at the TEST database.

Two publish-gate tests assert the *signed register resolves against the live
database*, which is only meaningful when those rows exist. They skip — naming the
missing profile and the command that supplies it — instead of asserting something
weaker, because a weakened assertion here would silently stop checking the
governance gate.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "reality_audit" / "review_decisions_r2_final.json"

PILOT_PROFILE_HELP = (
    "本测试需要 pilot 档案（登记表 37 条候选及其证据链真实存在于库中）。\n"
    "当前连的是 TEST 档案的 demo 种子，只有 demo 数据。补全方式：\n"
    "  1) python scripts/isolated_db.py --role TEST --reset\n"
    "  2) python scripts/dev_api_server.py --db-name petaccess_test --role TEST --port 8010\n"
    "  3) python scripts/real_pilot_ingest.py   # 走 API 灌入 10 个试点场所的证据链\n"
    "  4) 复核并应用 R2 决策（人类评审轮次），使 23 条 APPROVED 落地\n"
    "详见 docs/engineering/TEST_DATABASE_ISOLATION.md。"
)


def _registry_candidate_ids() -> list[str]:
    rows = json.loads(REGISTRY.read_text(encoding="utf-8"))["rows"]
    return [str(r["candidate_id"]) for r in rows if r.get("candidate_id")]


@pytest.fixture(scope="session")
def pilot_profile() -> int:
    """Skip (with the provisioning recipe) unless the pilot fixture is present."""
    from app.db.session import get_session_factory

    expected = _registry_candidate_ids()
    session = get_session_factory()()
    try:
        present = int(
            session.execute(
                text("SELECT count(*) FROM rule_candidate WHERE id = ANY(:ids)"),
                {"ids": expected},
            ).scalar_one()
        )
    finally:
        session.close()

    if present != len(expected):
        pytest.skip(
            f"pilot 档案缺失：登记表 {len(expected)} 条候选中只找到 {present} 条。\n"
            + PILOT_PROFILE_HELP
        )
    return present
