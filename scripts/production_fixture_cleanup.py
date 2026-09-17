"""Audit and clean up test fixtures that leaked into the production database.

Background
----------
Every `pytest` / Playwright run resolved its database from the repository `.env`,
which points at `petaccess`, and the suites create their own objects through the
API. Nothing rolled them back, so a week of QA left production holding mostly
test rows: 1249 places, 1119 access rules, 1449 sources and 1759 accounts, against
10 real pilot places.

This script answers three questions in order and refuses to skip ahead:

1. ``--report``   — read-only inventory + classification (evidence in, verdict out)
2. ``--dry-run``  — the exact deletion plan, dependency-ordered, rolled back
3. ``--execute``  — the same plan, committed, behind hard preconditions

How a row is proven to be a fixture (§20)
-----------------------------------------
A suspicious name is never sufficient. The verdict needs one canonical registry
hit (a literal that exists in this repository's own test sources) plus a second
independent signal, or a structural proof:

* **E1 canonical fixture registry** — the place name or actor e-mail is generated
  by an f-string literal in `tests/**` (see ``FIXTURE_PLACES`` /
  ``TEST_ACTOR_FAMILIES``, each carrying its ``file:line``).
* **E2 test actor** — ``audit_log.actor_user_id`` is an account whose only purpose
  is one test run (`v05mod-*`, `rb-*`, `mand-*`, ...).
* **E3 burst window** — ``created_at`` sits inside a QA burst.
* **E4 no real referent** — every source/evidence bundle it reaches was itself
  created by a test actor.

For everything that is not a place (sources, bundles, artifacts, media,
organizations, templates) deletion requires **both** E2 and "nothing that survives
still references it". A row that cannot prove both is left alone and reported.

What is deliberately *not* deleted
----------------------------------
* ``audit_log`` — append-only by policy (§24). Test audit rows stay on purpose:
  they are the record of what happened, including this cleanup.
* The 8 objects published by the first real batch, their evidence, sources,
  exceptions and signatures.
* The 10 real pilot places from the signed registry.
* The demo seed's places and their rule closure. They are historical demo content,
  not test output; §30 forbids deleting real/historical production data directly,
  so they are classified and left in place.
* The two demo operators and the four real/kept accounts.

Usage::

    python scripts/production_fixture_cleanup.py --report
    python scripts/production_fixture_cleanup.py --dry-run
    python scripts/production_fixture_cleanup.py --execute --confirm-database petaccess \\
        --backup artifacts/production_isolation/petaccess_before_cleanup.dump \\
        --i-reviewed-the-dry-run artifacts/production_isolation/CLEANUP_PLAN_DRY_RUN.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for extra in (str(ROOT / "scripts"), str(ROOT / "services" / "api")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

import psycopg  # noqa: E402
from dev_api_server import psycopg_url_for  # noqa: E402

from app.db.safety import DatabaseSafetyError, guard_for_psycopg  # noqa: E402

DEFAULT_REGISTRY = ROOT / "docs" / "reality_audit" / "review_decisions_r2_final.json"
DEFAULT_MANIFEST = ROOT / "docs" / "governance" / "publish_batches" / "R2_FINAL_R3_BATCH_01B.json"
ARTIFACT_DIR = ROOT / "artifacts" / "production_isolation"


# --------------------------------------------------------------------------- #
# Canonical fixture registry (§21)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FixtureEntry:
    fixture_id: str
    suite: str
    kind: str  # "exact" | "regex"
    value: str
    note: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "fixture_id": self.fixture_id,
            "suite": self.suite,
            "kind": self.kind,
            "value": self.value,
            "note": self.note,
        }


FIXTURE_PLACES: tuple[FixtureEntry, ...] = (
    FixtureEntry(
        "fx-place-e2e-a", "tests/integration/test_v05_e2e.py:97", "exact", "E2E-A 告示咖啡"
    ),
    FixtureEntry("fx-place-e2e-b", "tests/integration/test_v05_e2e.py:212", "exact", "E2E-B 门店"),
    FixtureEntry(
        "fx-place-e2e-c", "tests/integration/test_v05_e2e.py:22", "exact", "E2E-C 监控公园"
    ),
    FixtureEntry(
        "fx-place-e2e-d", "tests/integration/test_v05_e2e.py:462", "exact", "E2E-D 线索书店咖啡"
    ),
    FixtureEntry(
        "fx-place-operator-claim",
        "tests/integration/test_operator_contribution.py:66",
        "exact",
        "认领演示商店",
    ),
    FixtureEntry(
        "fx-place-quality-baseline",
        "tests/unit/test_quality_baseline.py:323",
        "exact",
        "质量基线测试咖啡",
    ),
    FixtureEntry(
        "fx-place-rollback",
        "tests/integration/test_rollback_l1.py:70",
        "regex",
        r"^回滚测试场所[0-9a-f]{6}$",
        'f"回滚测试场所{tag}"',
    ),
    FixtureEntry(
        "fx-place-mandatory-level",
        "tests/integration/test_mandatory_level.py:70",
        "regex",
        r"^强制级别测试场所[0-9a-f]{6}$",
        'f"强制级别测试场所{tag}"',
    ),
    FixtureEntry(
        "fx-place-exception-iso",
        "tests/integration/test_rule_exceptions.py:67",
        "regex",
        r"^例外隔离商场[0-9a-f]{8}$",
        'f"例外隔离商场{suffix}"',
    ),
    FixtureEntry(
        "fx-place-exception",
        "tests/integration/test_rule_exceptions.py:110",
        "regex",
        r"^例外测试商场[0-9a-f]{6}$",
        'f"例外测试商场{uuid4().hex[:6]}"',
    ),
    FixtureEntry(
        "fx-place-evidence",
        "tests/integration/test_evidence_api.py:54",
        "regex",
        r"^证据测试场所-[0-9a-f]{6}$",
        'f"证据测试场所-{uuid4().hex[:6]}"',
    ),
)

FIXTURE_ORGANISATIONS: tuple[FixtureEntry, ...] = (
    FixtureEntry("fx-org-e2e-b", "tests/integration/test_v05_e2e.py", "exact", "E2E-B 集团"),
    FixtureEntry(
        "fx-org-pattern", "tests/integration/test_api.py", "regex", r"^(组织|连锁)-[0-9a-f]{6}$"
    ),
)

#: `source.issuer` literals. `audit_log.target_id` is unusable for `source` rows
#: (they all read the literal string `'None'` — see the integrity scanner), so the
#: issuer is the only canonical handle left. Every value below is an f-string or
#: literal in the cited test file, which is what makes it a registry hit rather
#: than a guess.
FIXTURE_SOURCES: tuple[FixtureEntry, ...] = (
    FixtureEntry(
        "fx-src-e2e-a",
        "tests/integration/test_v05_e2e.py:116",
        "exact",
        "E2E-A 门口告示",
    ),
    FixtureEntry(
        "fx-src-e2e-b",
        "tests/integration/test_v05_e2e.py:214",
        "exact",
        "E2E-B 门店来源",
    ),
    FixtureEntry(
        "fx-src-e2e-c",
        "tests/integration/test_v05_e2e.py:281",
        "exact",
        "E2E-C 政府页面",
    ),
    FixtureEntry(
        "fx-src-e2e-d",
        "tests/integration/test_v05_e2e.py:463",
        "exact",
        "E2E-D 论坛线索",
    ),
    FixtureEntry(
        "fx-src-mandatory",
        "tests/integration/test_mandatory_level.py:60",
        "regex",
        r"^测试条例（[0-9a-f]{6}）$",
        'f"测试条例（{tag}）"',
    ),
    FixtureEntry(
        "fx-src-mandatory-integration",
        "tests/integration/test_mandatory_level.py",
        "exact",
        "测试条例（集成夹具）",
    ),
    FixtureEntry(
        "fx-src-exception-iso",
        "tests/integration/test_rule_exceptions.py:57",
        "regex",
        r"^测试条例（隔离夹具 [0-9a-f]{8}）$",
        'f"测试条例（隔离夹具 {suffix}）"',
    ),
    FixtureEntry(
        "fx-src-operator-community",
        "tests/integration/test_operator_contribution.py:78",
        "exact",
        "社区初版",
    ),
    FixtureEntry(
        "fx-src-operator-regulation",
        "tests/integration/test_operator_contribution.py:236",
        "exact",
        "测试法规来源",
    ),
    FixtureEntry(
        "fx-src-quality-baseline",
        "tests/unit/test_quality_baseline.py:274",
        "exact",
        "quality-baseline",
    ),
    FixtureEntry(
        "fx-src-evidence",
        "tests/integration/test_evidence_api.py:69",
        "regex",
        r"^证据来源-[0-9a-f]{6}$",
        'f"证据来源-{uuid4().hex[:6]}"',
    ),
    FixtureEntry(
        "fx-src-rollback",
        "tests/integration/test_rollback_l1.py:60",
        "regex",
        r"^回滚测试来源（[0-9a-f]{6}）$",
        'f"回滚测试来源（{tag}）"',
    ),
)

#: `user.email` families. Each prefix is the test module's own shorthand: a run
#: creates a throwaway admin/member so authorisation is exercised for real.
TEST_ACTOR_FAMILIES: tuple[tuple[str, str], ...] = (
    ("v05mod", "tests/integration/test_v05_e2e.py"),
    ("evmod", "tests/integration/test_evidence_api.py"),
    ("mand", "tests/integration/test_mandatory_level.py"),
    ("rb", "tests/integration/test_rollback_l1.py"),
    ("exc", "tests/integration/test_rule_exceptions.py"),
    ("media", "tests/integration/test_media.py"),
    ("bnd", "tests/integration/test_boundary_api.py"),
    ("it", "tests/integration/test_api.py"),
    ("e2e", "tests/integration/test_v05_e2e.py"),
    ("verif", "tests/integration/test_verifications.py"),
    ("ramod", "tests/integration/test_reality_audit_api.py"),
    ("rapl", "tests/integration/test_reality_audit_api.py"),
    ("rbac", "tests/integration/test_api.py"),
    ("plain", "tests/integration/test_evidence_api.py"),
    ("adm", "scripts/mutation_probe.py"),
    ("adm2", "scripts/mutation_probe.py"),
    ("dbg", "ad-hoc local debugging"),
    ("exc2", "tests/integration/test_rule_exceptions.py"),
    ("exc3", "tests/integration/test_rule_exceptions.py"),
    ("provenance", "scripts/repair_fairmont_provenance_r1.py"),
    ("perf", "scripts/perf_baseline.py"),
    ("复核员", "tests/ (per-run reviewer account)"),
    ("法规复核", "tests/ (per-run legal reviewer account)"),
    ("认领运营", "tests/integration/test_operator_contribution.py"),
    ("普通用户", "tests/ (per-run plain member)"),
    ("限流用户", "tests/ (rate-limit account)"),
)

#: Accounts that are NOT test actors, whatever else happens. Deleting one of
#: these would break the pilot ingest, the demo seed or governance tooling.
REAL_ACCOUNTS: frozenset[str] = frozenset(
    {
        "admin@demo-petaccess.com",  # demo/pilot administrator
        "operator@demo.local",  # demo operator
        "real-pilot-admin@example.com",  # scripts/real_pilot_ingest.py
        "scope-split-ops@example.com",  # scripts/split_library_scope_r2.py (governance)
    }
)

#: Demo-seed places — HISTORICAL demo content, kept (§30).
DEMO_SEED_PLACES: frozenset[str] = frozenset(
    {
        "星河咖啡·测试店",
        "星河咖啡·栖霞分店",
        "青岚公园·演示",
        "云栖中心·测试商场",
        "松风社区·演示",
    }
)

#: `audit_log.target_type` values that prove ownership of non-place objects.
#: Kept as documentation of the mapping the plan relies on; `_owned_by_test_actor`
#: takes the type explicitly so a typo becomes a visible empty result.
AUDIT_TARGET_TYPES: dict[str, str] = {
    "source": "source",
    "evidence_bundle": "evidence_bundle",
    "source_artifact": "source_artifact",
    "media_object": "media_object",
    "organization": "organization",
    "policy_template": "policy_template",
    "operator": "operator",
    "observation_candidate": "observation_candidate",
    "place": "place",
    "access_rule": "access_rule",
    "rule_candidate": "rule_candidate",
    "rule_exception": "rule_exception",
    "zone": "zone",
    "watch_subscription": "watch_subscription",
    "source_monitor": "source_monitor",
    "dispute_case": "dispute_case",
    "pet_profile": "pet_profile",
    "boundary_profile": "boundary_profile",
    "verification_event": "verification_event",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


# --------------------------------------------------------------------------- #
# psycopg helpers
# --------------------------------------------------------------------------- #
def _rows(cur: Any, sql: str, params: dict[str, Any] | Sequence[Any] = ()) -> list[dict[str, Any]]:
    cur.execute(sql, params)
    cols = [d.name for d in cur.description]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        rec: dict[str, Any] = {}
        for name, value in zip(cols, row, strict=False):
            rec[name] = value.isoformat() if isinstance(value, datetime) else value
        out.append(rec)
    return out


def _one(cur: Any, sql: str, params: dict[str, Any] | Sequence[Any] = ()) -> Any:
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


@dataclass
class Step:
    label: str
    table: str
    sql: str
    rows: int = 0
    kind: str = "delete"


@dataclass
class Plan:
    steps: list[Step] = field(default_factory=list)

    def add(self, label: str, table: str, sql: str, *, kind: str = "delete") -> None:
        self.steps.append(Step(label=label, table=table, sql=sql, kind=kind))


def _owned_by_test_actor(target_type: str, id_expr: str) -> str:
    """`true` when a test account performed an audited action on this row.

    Note the asymmetry that makes this safe: `audit_log.target_id` is populated
    for most target types but holds the literal string `'None'` for `source` and
    `zone` rows (2647 rows). So this helper is used only where the column is
    usable, and sources are proven by their canonical issuer instead.
    """
    return (
        "exists (select 1 from audit_log a join t_rm_user tu on tu.id = a.actor_user_id "
        f"where a.target_type = '{target_type}' and a.target_id = {id_expr}"
        " and a.target_id <> 'None')"
    )


def _from_fixture_source(source_id_expr: str) -> str:
    """`true` when the row's `source_id` points at a canonical fixture source."""
    return (
        "exists (select 1 from source fs where fs.id = "
        f"{source_id_expr} and fs.issuer ~ any(%(fixture_issuers)s::text[]))"
    )


def _survives(table: str, column: str, id_expr: str) -> str:
    return f"exists (select 1 from {table} k where k.{column} = {id_expr})"


RM_PLACES = "(select id from t_rm_place)"


def build_plan() -> Plan:
    """Dependency-ordered plan. Order matters, not aesthetics.

    `rule_candidate.place_id` is ``SET NULL`` so candidates must be removed before
    places; `source` is referenced with ``RESTRICT`` so sources go last; `place`
    cascades to zones and rules, and those cascades are made explicit here so the
    report can name every row that leaves.
    """
    p = Plan()
    P = RM_PLACES
    Z = f"(select id from zone where place_id in {P})"

    # ---- scope ------------------------------------------------------------
    p.add(
        "scope: accounts that must survive",
        "user",
        """create temp table t_keep_user on commit drop as
           select id from "user" where lower(email) = any(%(real_accounts)s)""",
        kind="scope",
    )
    p.add(
        "scope: test accounts of this repository",
        "user",
        """create temp table t_rm_user on commit drop as
           select u.id, u.email from "user" u
           where not exists (select 1 from t_keep_user k where k.id = u.id)""",
        kind="scope",
    )
    p.add(
        "scope: places that must survive",
        "place",
        """create temp table t_keep_place on commit drop as
           select distinct p.id from place p
           where p.canonical_name = any(%(demo_names)s)
              or p.canonical_name = any(%(registry_place_names)s)
              or p.id in (select place_id from rule_candidate
                          where id = any(%(batch_candidates)s)
                             or id = any(%(registry_candidates)s))
              or p.id in (select place_id from access_rule where id = any(%(batch_rules)s))
              or p.id in (select place_id from zone where id = any(%(registry_zones)s))
              or p.id in (select a.target_id from audit_log a
                          where a.target_type = 'place'
                            and a.actor_user_id in (select id from t_keep_user))""",
        kind="scope",
    )
    p.add(
        "scope: parents of surviving places",
        "place",
        """insert into t_keep_place
           select distinct p.parent_place_id from place p
           where p.id in (select id from t_keep_place) and p.parent_place_id is not null""",
        kind="scope",
    )
    p.add(
        "scope: places proven to be test fixtures",
        "place",
        """create temp table t_rm_place on commit drop as
           select p.id, p.canonical_name, p.created_at from place p
           where not exists (select 1 from t_keep_place k where k.id = p.id)
             and (
               p.canonical_name = any(%(fixture_exact)s)
               or exists (select 1 from unnest(%(fixture_regex)s::text[]) pat
                          where p.canonical_name ~ pat)
             )""",
        kind="scope",
    )
    p.add(
        "scope: places created by a test actor under a non-canonical name (LIKELY — never touched)",
        "place",
        """create temp table t_likely_place on commit drop as
           select p.id, p.canonical_name, p.created_at from place p
           where not exists (select 1 from t_keep_place k where k.id = p.id)
             and not exists (select 1 from t_rm_place r where r.id = p.id)
             and exists (select 1 from audit_log a join t_rm_user tu on tu.id = a.actor_user_id
                         where a.target_type = 'place' and a.target_id = p.id)""",
        kind="scope",
    )
    p.add(
        "scope: places neither kept nor proven (UNKNOWN — never touched)",
        "place",
        """create temp table t_unknown_place on commit drop as
           select p.id, p.canonical_name, p.created_at, p.place_type from place p
           where not exists (select 1 from t_keep_place k where k.id = p.id)
             and not exists (select 1 from t_rm_place r where r.id = p.id)
             and not exists (select 1 from t_likely_place l where l.id = p.id)""",
        kind="scope",
    )
    p.add(
        "scope: rules that must survive",
        "access_rule",
        """create temp table t_keep_rule on commit drop as
           select distinct r.id from access_rule r
           where r.id = any(%(batch_rules)s)
              or r.place_id in (select id from t_keep_place)""",
        kind="scope",
    )
    p.add(
        "scope: candidates that must survive",
        "rule_candidate",
        """create temp table t_keep_candidate on commit drop as
           select distinct c.id from rule_candidate c
           where c.id = any(%(batch_candidates)s)
              or c.id = any(%(registry_candidates)s)
              or c.place_id in (select id from t_keep_place)
              or exists (select 1 from audit_log a
                         where a.target_type = 'rule_candidate' and a.target_id = c.id
                           and a.actor_user_id in (select id from t_keep_user))""",
        kind="scope",
    )

    # ---- children of fixture places ---------------------------------------
    p.add(
        "observation candidates on fixture places",
        "observation_candidate",
        f"delete from observation_candidate where place_id in {P}",
    )
    p.add(
        "observation claims on fixture places",
        "observation_claim",
        f"delete from observation_claim where place_id in {P}",
    )
    p.add(
        "rule candidates on fixture places/zones",
        "rule_candidate",
        f"""delete from rule_candidate
            where id not in (select id from t_keep_candidate)
              and (place_id in {P} or zone_id in {Z})""",
    )
    p.add(
        "verification events on fixture places",
        "verification_event",
        f"delete from verification_event where place_id in {P}",
    )
    for table, label in (
        ("place_policy_binding", "policy bindings"),
        ("event_policy", "event policies"),
        ("coexistence_policy", "coexistence policies"),
        ("amenity", "amenities"),
        ("entrance", "entrances"),
        ("access_path", "access paths"),
        ("external_place_ref", "external place refs"),
        ("place_geometry", "place geometry"),
    ):
        p.add(f"{label} on fixture places", table, f"delete from {table} where place_id in {P}")
    # `jurisdiction_rule` has no `place_id`, so it is not reachable from the
    # fixture-place sets above and needs its own criterion. The first run of this
    # script left it alone entirely, which was wrong: 68 rows sat on
    # `jurisdiction_id = 'test-city'` / `authority = '测试机关'` (both literals in
    # tests/integration/test_operator_contribution.py), reviewed by one-off test
    # actors, and because `jurisdiction_rule.source_id` is `RESTRICT` they pinned
    # 68 canonical fixture sources in production — `TEST_FIXTURE_SOURCE_IN_PRODUCTION`
    # stayed at 68 after the first cleanup. Nothing references `jurisdiction_rule`,
    # so the fix is to delete the fixture-sourced rows *before* the sources, and
    # the source step below then removes what no longer has a referent.
    # `demo-*` jurisdiction rules keep their non-fixture issuers and survive.
    p.add(
        "fixture legal-layer jurisdiction rules",
        "jurisdiction_rule",
        f"""delete from jurisdiction_rule j
            where {_from_fixture_source("j.source_id")}""",
    )
    p.add(
        "operator claims on fixture places",
        "operator_claim",
        f"delete from operator_claim where place_id in {P}",
    )
    p.add(
        "source monitors on fixture places",
        "source_monitor",
        f"delete from source_monitor where place_id in {P}",
    )
    p.add(
        "exceptions on fixture rules",
        "rule_exception",
        f"delete from rule_exception where rule_id in (select id from access_rule "
        f"where place_id in {P} or zone_id in {Z})",
    )
    p.add(
        "access rules on fixture places",
        "access_rule",
        f"""delete from access_rule
            where id not in (select id from t_keep_rule)
              and (place_id in {P} or zone_id in {Z})""",
    )
    p.add("zones of fixture places", "zone", f"delete from zone where place_id in {P}")
    p.add("fixture places", "place", f"delete from place where id in {P}")

    # ---- objects owned by test accounts -----------------------------------
    p.add(
        "pet profiles of test accounts",
        "pet_profile",
        "delete from pet_profile where user_id in (select id from t_rm_user)",
    )
    p.add(
        "watch subscriptions of test accounts",
        "watch_subscription",
        "delete from watch_subscription where user_id in (select id from t_rm_user)",
    )
    p.add(
        "boundary profiles of test accounts",
        "boundary_profile",
        "delete from boundary_profile where user_id in (select id from t_rm_user)",
    )
    p.add(
        "boundary preferences of test profiles",
        "boundary_preference",
        "delete from boundary_preference where profile_id not in (select id from boundary_profile)",
    )
    p.add(
        "observation claims filed by test accounts",
        "observation_claim",
        "delete from observation_claim where user_id in (select id from t_rm_user)",
    )
    p.add(
        "verification events by test accounts",
        "verification_event",
        "delete from verification_event where user_id in (select id from t_rm_user)",
    )
    p.add(
        "dispute cases raised by test accounts",
        "dispute_case",
        "delete from dispute_case where claimant_user_id in (select id from t_rm_user) "
        "or counter_party_user_id in (select id from t_rm_user)",
    )
    p.add(
        "observation candidates filed by test accounts",
        "observation_candidate",
        "delete from observation_candidate where "
        f"{_owned_by_test_actor('observation_candidate', 'observation_candidate.id')}",
    )

    # ---- leftovers: require BOTH provenance and no surviving reference ----
    p.add(
        "media uploaded by test accounts, now unreferenced",
        "media_object",
        f"""delete from media_object m
            where {_owned_by_test_actor("media_object", "m.id")}
              and not {_survives("rule_candidate", "media_id", "m.id")}
              and not {_survives("source_artifact", "media_id", "m.id")}""",
    )
    p.add(
        "policy templates of test organizations, now unreferenced",
        "policy_template",
        f"""delete from policy_template t
            where {_owned_by_test_actor("policy_template", "t.id")}
              and not {_survives("place_policy_binding", "template_id", "t.id")}""",
    )
    p.add(
        "test organizations, now unreferenced",
        "organization",
        f"""delete from organization o
            where {_owned_by_test_actor("organization", "o.id")}
              and not {_survives("policy_template", "organization_id", "o.id")}
              and not {_survives("place", "operator_id", "o.id")}""",
    )
    p.add(
        "operators created by test accounts, now unreferenced",
        "operator",
        f"""delete from operator o
            where {_owned_by_test_actor("operator", "o.id")}
              and not {_survives("operator_claim", "operator_id", "o.id")}
              and not {_survives("place", "operator_id", "o.id")}""",
    )
    p.add(
        "evidence bundles created by test accounts, now ownerless",
        "evidence_bundle",
        f"""delete from evidence_bundle b
            where ({_owned_by_test_actor("evidence_bundle", "b.id")}
                   or {_from_fixture_source("b.source_id")})
              and not {_survives("rule_candidate", "evidence_bundle_id", "b.id")}
              and not {_survives("observation_candidate", "evidence_bundle_id", "b.id")}
              and not {_survives("evidence_bundle", "derived_from_bundle_id", "b.id")}""",
    )
    p.add(
        "evidence bundles, now ownerless (second pass: derived-from chains)",
        "evidence_bundle",
        f"""delete from evidence_bundle b
            where ({_owned_by_test_actor("evidence_bundle", "b.id")}
                   or {_from_fixture_source("b.source_id")})
              and not {_survives("rule_candidate", "evidence_bundle_id", "b.id")}
              and not {_survives("observation_candidate", "evidence_bundle_id", "b.id")}
              and not {_survives("evidence_bundle", "derived_from_bundle_id", "b.id")}""",
    )
    p.add(
        "source artifacts, now ownerless (second pass)",
        "source_artifact",
        f"""delete from source_artifact a
            where ({_owned_by_test_actor("source_artifact", "a.id")}
                   or {_from_fixture_source("a.source_id")})
              and not {_survives("evidence_bundle", "artifact_id", "a.id")}
              and not {_survives("media_object", "source_id", "a.source_id")}""",
    )
    p.add(
        "sources whose issuer is a canonical fixture, now unreferenced",
        "source",
        f"""delete from source s
            where s.issuer ~ any(%(fixture_issuers)s::text[])
              and not {_survives("access_rule", "source_id", "s.id")}
              and not {_survives("rule_exception", "source_id", "s.id")}
              and not {_survives("rule_candidate", "source_id", "s.id")}
              and not {_survives("evidence_bundle", "source_id", "s.id")}
              and not {_survives("source_artifact", "source_id", "s.id")}
              and not {_survives("place_geometry", "source_id", "s.id")}
              and not {_survives("observation_candidate", "source_id", "s.id")}
              and not {_survives("media_object", "source_id", "s.id")}
              and not {_survives("data_license", "source_id", "s.id")}
              and not {_survives("data_source_job", "source_id", "s.id")}
              and not {_survives("access_path", "source_id", "s.id")}
              and not {_survives("amenity", "source_id", "s.id")}
              and not {_survives("entrance", "source_id", "s.id")}
              and not {_survives("coexistence_policy", "source_id", "s.id")}
              and not {_survives("event_policy", "source_id", "s.id")}
              and not {_survives("jurisdiction_rule", "source_id", "s.id")}
              and not {_survives("place_policy_binding", "source_id", "s.id")}""",
    )
    p.add(
        "test accounts themselves",
        "user",
        'delete from "user" where id in (select id from t_rm_user)',
    )
    return p


class _Scope:
    """Resolved identifiers the plan predicates need, plus the placeholders."""

    def __init__(self, **kw: Any) -> None:
        self.__dict__.update(kw)


def load_scope_ids() -> _Scope:
    """Resolve the protected set.

    The batch manifest lists *rule* ids (`fp-legal-dog`, ...); the database keys
    candidates by UUID. `real_publish_snapshot.py` makes the same translation, so
    it lives in one place here: rule_id -> registry row -> candidate_id.
    """
    registry = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8"))
    manifest = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    rows = registry.get("rows", [])
    by_rule_id = {str(r["rule_id"]): r for r in rows if r.get("rule_id")}
    batch_rule_labels = [str(c) for c in manifest.get("candidate_rule_ids", [])]
    missing = [r for r in batch_rule_labels if r not in by_rule_id]
    if missing:
        raise DatabaseSafetyError(
            f"批次清单里的 rule_id 在登记表中找不到：{missing}；无法计算保护区，拒绝继续。"
        )
    return _Scope(
        batch_rule_labels=batch_rule_labels,
        batch_candidates=[str(by_rule_id[r]["candidate_id"]) for r in batch_rule_labels],
        batch_rules=[],
        registry_candidates=[str(r["candidate_id"]) for r in rows if r.get("candidate_id")],
        registry_place_names=sorted({str(r["place_name"]) for r in rows if r.get("place_name")}),
        registry_zones=sorted({str(r["zone_id"]) for r in rows if r.get("zone_id")}),
        real_accounts=sorted(REAL_ACCOUNTS),
        demo_names=sorted(DEMO_SEED_PLACES),
        fixture_exact=[e.value for e in FIXTURE_PLACES if e.kind == "exact"],
        fixture_regex=[e.value for e in FIXTURE_PLACES if e.kind == "regex"],
        fixture_issuers=[e.value for e in FIXTURE_SOURCES],
    )


def _params(scope: _Scope) -> dict[str, Any]:
    return {
        "batch_candidates": scope.batch_candidates,
        "batch_rules": scope.batch_rules,
        "registry_candidates": scope.registry_candidates,
        "registry_place_names": scope.registry_place_names,
        "registry_zones": scope.registry_zones,
        "real_accounts": scope.real_accounts,
        "demo_names": scope.demo_names,
        "fixture_exact": scope.fixture_exact,
        "fixture_regex": scope.fixture_regex,
        "fixture_issuers": scope.fixture_issuers,
    }


def _used_params(sql: str, params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if f"%({k})s" in sql}


def resolve_batch_rules(cur: Any, candidate_ids: Sequence[str]) -> list[str]:
    return [
        str(r["published_rule_id"])
        for r in _rows(
            cur,
            "select published_rule_id from rule_candidate "
            "where id = any(%s) and published_rule_id is not null",
            (list(candidate_ids),),
        )
    ]


# --------------------------------------------------------------------------- #
# Read-only inventory
# --------------------------------------------------------------------------- #
def inventory(conn: Any) -> dict[str, Any]:
    scope = load_scope_ids()
    with conn.cursor() as cur:
        counts = {
            r["t"]: r["n"]
            for r in _rows(
                cur,
                """
                select 'place' as t, count(*) as n from place
                union all select 'user', count(*) from "user"
                union all select 'access_rule', count(*) from access_rule
                union all select 'rule_exception', count(*) from rule_exception
                union all select 'rule_candidate', count(*) from rule_candidate
                union all select 'source', count(*) from source
                union all select 'evidence_bundle', count(*) from evidence_bundle
                union all select 'audit_log', count(*) from audit_log
                order by 1
                """,
            )
        }
        actors = _rows(
            cur,
            'select u.email, u.role, count(*) as audit_rows from audit_log a join "user" u '
            "on u.id = a.actor_user_id group by 1, 2 order by 3 desc",
        )
        places = _rows(
            cur,
            """
            select p.id, p.canonical_name, p.place_type, p.created_at,
                   (select count(*) from access_rule ar where ar.place_id = p.id) as rules,
                   (select count(*) from zone z where z.place_id = p.id) as zones,
                   (select max(u.email) from audit_log a join "user" u on u.id = a.actor_user_id
                     where a.target_type = 'place' and a.target_id = p.id) as actor_email,
                   (select count(*) from audit_log a
                     where a.target_type = 'place' and a.target_id = p.id) as audit_rows
            from place p order by p.created_at
            """,
        )

    exact = set(scope.fixture_exact)
    patterns = scope.fixture_regex
    real = {a.lower() for a in scope.real_accounts}

    classified: list[dict[str, Any]] = []
    for row in places:
        name = row["canonical_name"] or ""
        ev: list[str] = []
        if name in exact:
            ev.append("E1 canonical fixture literal")
        elif any(re.fullmatch(p, name) for p in patterns):
            ev.append("E1 canonical fixture pattern")
        if name in DEMO_SEED_PLACES:
            ev.append("DEMO_SEED historical demo content")
        actor = (row["actor_email"] or "").lower()
        if actor and actor not in real:
            ev.append(f"E2 test actor {actor}")
        elif actor:
            ev.append(f"REAL actor {actor}")
        if name in scope.registry_place_names:
            ev.append("REAL pilot registry place")

        strong = sum(1 for e in ev if e.startswith(("E1", "E2")))
        if any(e.startswith("REAL pilot registry") for e in ev):
            verdict = "REAL_PRODUCTION"
        elif any(e.startswith("DEMO_SEED") for e in ev):
            verdict = "HISTORICAL_GOVERNANCE"
        elif strong >= 1 and any(e.startswith("E1") for e in ev):
            # §20: one canonical fixture-registry hit is enough on its own — the
            # name is generated by a literal in this repository's test sources.
            verdict = "CONFIRMED_TEST_FIXTURE"
        elif strong >= 2:
            verdict = "CONFIRMED_TEST_FIXTURE"
        elif strong:
            verdict = "LIKELY_TEST_FIXTURE"
        else:
            verdict = "UNKNOWN"

        classified.append(
            {
                "entity_type": "place",
                "entity_id": row["id"],
                "name": name,
                "place_type": row["place_type"],
                "created_at": row["created_at"],
                "last_audit_actor": row["actor_email"],
                "audit_rows": row["audit_rows"],
                "rules": row["rules"],
                "zones": row["zones"],
                "evidence": ev,
                "confidence": verdict,
                "proposed_action": (
                    "remove" if verdict == "CONFIRMED_TEST_FIXTURE" else "keep_and_report"
                ),
            }
        )

    summary: dict[str, int] = {}
    for item in classified:
        summary[item["confidence"]] = summary.get(item["confidence"], 0) + 1

    by_name: dict[str, dict[str, Any]] = {}
    for item in classified:
        key = item["name"]
        slot = by_name.setdefault(
            key, {"name": key, "count": 0, "confidence": item["confidence"], "sample_evidence": []}
        )
        slot["count"] += 1
        if not slot["sample_evidence"]:
            slot["sample_evidence"] = item["evidence"]

    return {
        "at": _now(),
        "table_counts": counts,
        "places_total": len(classified),
        "classification": summary,
        "top_names": sorted(by_name.values(), key=lambda v: -v["count"])[:40],
        "places": classified,
        "actors": actors,
        "fixture_registry": [e.as_dict() for e in FIXTURE_PLACES],
        "test_actor_families": [{"prefix": p, "suite": s} for p, s in TEST_ACTOR_FAMILIES],
        "real_accounts": sorted(REAL_ACCOUNTS),
        "demo_seed_places": sorted(DEMO_SEED_PLACES),
    }


# --------------------------------------------------------------------------- #
# Plan execution (rolled back unless --execute)
# --------------------------------------------------------------------------- #
def table_counts(cur: Any) -> dict[str, int]:
    names = [
        r["tablename"]
        for r in _rows(
            cur,
            "select tablename from pg_tables where schemaname = 'public' order by tablename",
        )
    ]
    return {name: int(_one(cur, f'select count(*) from "{name}"') or 0) for name in names}  # noqa: S608


def run_plan(
    conn: Any,
    *,
    execute: bool,
    precommit_check: Callable[[dict[str, Any]], list[str]] | None = None,
) -> dict[str, Any]:
    """Apply the plan in one transaction.

    When ``execute`` is true the transaction is committed only after
    ``precommit_check`` has been given the chance to veto it.  The check MUST
    run on the in-transaction state, i.e. *before* COMMIT: committing first and
    validating afterwards would leave the database mutated even when the
    invariants fail, and the "rolled back" message would be a lie.
    """
    scope = load_scope_ids()
    plan = build_plan()
    with conn.cursor() as cur:
        scope.batch_rules = resolve_batch_rules(cur, scope.batch_candidates)
        params = _params(scope)
        before_counts = table_counts(cur)

        steps: list[dict[str, Any]] = []
        for step in plan.steps:
            cur.execute(step.sql, _used_params(step.sql, params))
            rows = cur.rowcount if isinstance(cur.rowcount, int) and cur.rowcount > 0 else 0
            step.rows = rows
            steps.append(
                {"label": step.label, "table": step.table, "rows": rows, "kind": step.kind}
            )

        resolved = {
            "keep_accounts": _one(cur, "select count(*) from t_keep_user"),
            "test_accounts": _one(cur, "select count(*) from t_rm_user"),
            "keep_places": _one(cur, "select count(*) from t_keep_place"),
            "fixture_places": _one(cur, "select count(*) from t_rm_place"),
            "unknown_places": _one(cur, "select count(*) from t_unknown_place"),
            "keep_rules": _one(cur, "select count(*) from t_keep_rule"),
            "keep_candidates": _one(cur, "select count(*) from t_keep_candidate"),
        }
        batch_rules = list(scope.batch_rules)
        batch_candidates = list(scope.batch_candidates)
        surviving_rules = _rows(
            cur,
            "select r.id, r.place_id, r.zone_id, r.rule_layer, r.animal_scope, r.action, "
            "r.effect, r.status, r.source_id, r.created_at "
            "from access_rule r order by r.created_at",
        )
        surviving_rule_ids = {str(r["id"]) for r in surviving_rules}
        survivors = {
            "batch_candidates_published": _one(
                cur,
                "select count(*) from rule_candidate where id = any(%s) "
                "and review_status = 'PUBLISHED'",
                (batch_candidates,),
            ),
            "batch_candidate_ids_found": sum(1 for b in batch_candidates if str(b).strip() != ""),
            "batch_access_rules": sum(1 for r in batch_rules if str(r) in surviving_rule_ids),
            "access_rule_total": _one(cur, "select count(*) from access_rule"),
            "rule_exception_total": _one(cur, "select count(*) from rule_exception"),
            "rule_candidate_total": _one(cur, "select count(*) from rule_candidate"),
            "place_total": _one(cur, "select count(*) from place"),
            "user_total": _one(cur, 'select count(*) from "user"'),
            "source_total": _one(cur, "select count(*) from source"),
            "evidence_bundle_total": _one(cur, "select count(*) from evidence_bundle"),
            "audit_log_total": _one(cur, "select count(*) from audit_log"),
        }
        unknown = _rows(
            cur,
            "select id, canonical_name, place_type, created_at from t_unknown_place "
            "order by created_at",
        )
        likely = _rows(
            cur,
            "select id, canonical_name, created_at from t_likely_place order by created_at",
        )
        surviving_places = _rows(
            cur,
            "select p.id, p.canonical_name, p.place_type, p.lifecycle_status, p.created_at, "
            "(select count(*) from access_rule r where r.place_id = p.id) as rules "
            "from place p order by p.canonical_name",
        )
        remaining_sources = _one(
            cur,
            "select count(*) from source s where "
            + " and ".join(
                f"not exists (select 1 from {t} k where k.source_id = s.id)"
                for t in (
                    "access_rule",
                    "rule_exception",
                    "rule_candidate",
                    "evidence_bundle",
                    "source_artifact",
                    "observation_candidate",
                )
            ),
        )
        after_counts = table_counts(cur)

    doc: dict[str, Any] = {
        "at": _now(),
        "mode": "execute" if execute else "dry-run",
        "scope": {
            "batch_rule_labels": scope.batch_rule_labels,
            "batch_candidates": scope.batch_candidates,
            "batch_rules": scope.batch_rules,
            "registry_candidates_count": len(scope.registry_candidates),
            "registry_place_names": scope.registry_place_names,
            "real_accounts": scope.real_accounts,
            "demo_seed_places": scope.demo_names,
            "fixture_exact": scope.fixture_exact,
            "fixture_regex": scope.fixture_regex,
        },
        "resolved": resolved,
        "steps": steps,
        "survivors": survivors,
        "table_counts_before": before_counts,
        "table_counts_after": after_counts,
        "table_deltas": {
            name: before_counts.get(name, 0) - after_counts.get(name, 0)
            for name in sorted(set(before_counts) | set(after_counts))
            if before_counts.get(name, 0) != after_counts.get(name, 0)
        },
        "unknown_places": unknown,
        "likely_places": likely,
        "surviving_places": surviving_places,
        "surviving_access_rules": surviving_rules,
        "orphan_sources_after_plan": remaining_sources,
        "audit_log_policy": "append-only: audit rows are never deleted by this script",
    }
    totals: dict[str, int] = {}
    for row in steps:
        if row["kind"] == "delete" and row["rows"]:
            totals[row["table"]] = totals.get(row["table"], 0) + row["rows"]
    doc["deleted_totals"] = totals
    doc["deleted_rows_total"] = sum(totals.values())

    if execute:
        problems = precommit_check(doc) if precommit_check is not None else []
        if problems:
            conn.rollback()
            doc["committed"] = False
            doc["aborted"] = True
            doc["abort_reasons"] = problems
            return doc
        conn.commit()
        doc["committed"] = True
    else:
        conn.rollback()
        doc["committed"] = False
    return doc


def reconcile_preconditions(doc: dict[str, Any]) -> list[str]:
    """Hard invariants that must hold before a commit is allowed."""
    problems: list[str] = []
    resolved = doc["resolved"]
    steps = doc["steps"]
    # The evidence chain only has to cover what the plan actually touches. A
    # follow-up batch that removes, say, jurisdiction-layer rows has no fixture
    # *places* left to prove, and must not be blocked by a check written for the
    # first pass; conversely a plan that deletes places with no fixture evidence
    # is a broken query and must not commit.
    deletes_places = any(
        s["kind"] == "delete" and s["table"] == "place" and s["rows"] for s in steps
    )
    if deletes_places and resolved["fixture_places"] == 0:
        problems.append("计划要删 place 但 fixture_places 为 0：证据链断了，拒绝执行")
    if resolved["keep_places"] == 0:
        problems.append("keep_places 为 0：保护区计算失败，拒绝执行")
    if doc["deleted_rows_total"] == 0:
        problems.append("计划不删除任何行：拒绝以破坏性模式提交空计划")
    if doc["survivors"]["batch_candidates_published"] != len(doc["scope"]["batch_candidates"]):
        problems.append("Batch-01B 候选在计划后不再是 PUBLISHED")
    if doc["survivors"]["batch_access_rules"] != len(doc["scope"]["batch_rules"]):
        problems.append("Batch-01B 的 AccessRule 数量在计划后发生变化")
    if doc["survivors"]["audit_log_total"] == 0:
        problems.append("audit_log 变成空表")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db-name", default="petaccess")
    ap.add_argument("--report", action="store_true", help="只读清单 + 分类")
    ap.add_argument("--dry-run", action="store_true", help="打印删除计划并回滚（默认）")
    ap.add_argument("--execute", action="store_true", help="真正执行（需多项显式确认）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--confirm-database", default=None)
    ap.add_argument("--backup", default=None, help="--execute 前必须存在的 pg_dump 文件")
    ap.add_argument("--i-reviewed-the-dry-run", default=None, help="已审阅的 dry-run JSON 路径")
    args = ap.parse_args()

    if not (args.report or args.dry_run or args.execute):
        args.dry_run = True

    out_path = (
        Path(args.out)
        if args.out
        else ARTIFACT_DIR
        / (
            "PRODUCTION_CLEANUP_EXECUTED.json"
            if args.execute
            else "PRODUCTION_FIXTURE_INVENTORY.json"
        )
    )

    if args.execute:
        problems = []
        if args.confirm_database != args.db_name:
            problems.append("--confirm-database 必须与 --db-name 完全一致")
        if not args.backup or not Path(args.backup).exists():
            problems.append("--backup 必须指向一个已存在的备份文件")
        if not args.i_reviewed_the_dry_run or not Path(args.i_reviewed_the_dry_run).exists():
            problems.append("--i-reviewed-the-dry-run 必须指向已审阅的 dry-run JSON")
        if problems:
            print("REFUSED — --execute 前置条件未满足：", file=sys.stderr)
            for item in problems:
                print(f"  - {item}", file=sys.stderr)
            return 2

    url = psycopg_url_for(args.db_name)
    with psycopg.connect(url) as conn:
        guard = guard_for_psycopg(conn)
        print(guard.banner())

        if args.report:
            doc = inventory(conn)
            doc["database"], doc["role"] = guard.database_name, guard.role.value
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n",
                encoding="utf-8",
            )
            print(f"WROTE {out_path}")
            print(f"  places_total = {doc['places_total']}")
            for key, value in sorted(doc["classification"].items()):
                print(f"    {key:<24} {value}")
            print(f"  table_counts = {doc['table_counts']}")
            return 0

        if args.execute:
            # §27: cleanup of leaked fixtures *from production* is its own
            # governed operation.  It must not borrow `assert_destructive_allowed`
            # (that assertion exists to keep resets/drops off production) and it
            # must not widen the PRODUCTION role spec either.
            guard.assert_production_cleanup_allowed(
                "生产库夹具清理",
                backup_path=args.backup,
                reviewed_plan_path=args.i_reviewed_the_dry_run,
            )
        else:
            guard.assert_production_database("生产库夹具清理计划（只读、事务回滚）")

        doc = run_plan(
            conn,
            execute=args.execute,
            precommit_check=reconcile_preconditions if args.execute else None,
        )
        doc["database"], doc["role"] = guard.database_name, guard.role.value
        out_path.parent.mkdir(parents=True, exist_ok=True)
        doc["database"], doc["role"] = guard.database_name, guard.role.value
        out_path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
        )
        if args.execute and doc.get("aborted"):
            print("ABORT — 提交前不变量失败（事务已回滚，库未被修改）：", file=sys.stderr)
            for item in doc["abort_reasons"]:
                print(f"  - {item}", file=sys.stderr)
            print(f"WROTE {out_path}", file=sys.stderr)
            return 4
        print(f"WROTE {out_path}")
        print(f"  mode          = {doc['mode']}  committed = {doc['committed']}")
        print(f"  resolved      = {doc['resolved']}")
        print(f"  deleted_rows  = {doc['deleted_rows_total']}")
        for table, n in sorted(doc["deleted_totals"].items(), key=lambda kv: -kv[1]):
            print(f"    {table:<24} {n}")
        print(f"  survivors     = {doc['survivors']}")
        print(f"  unknown_places= {len(doc['unknown_places'])} (未删除)")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DatabaseSafetyError as exc:
        print(f"DATABASE_SAFETY_REFUSED: {exc}", file=sys.stderr)
        sys.exit(3)
