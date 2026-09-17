"""§19 / §20 / §26 — the production integrity closure, locked down.

Three regressions that the closure round earned:

**§19 — a governed delete commits *last***. The previous implementation
committed and *then* checked the invariants, so a failed check printed
"rolled back" while the rows were already durable. The test does not assert on
log text: it opens a **second** connection and asks the server whether the row
is still there, because the only thing that distinguishes a real rollback from a
claimed one is what another session sees.

**§20 — a fixture legal Source must not outlive its fixture**. ``jurisdiction_rule``
has no ``place_id``, so a place-scoped cleanup removed the place and left the
Source behind. The test builds that exact shape and asserts the Source goes too —
and, just as importantly, that a Source still referenced by a *surviving* rule is
kept.

Both run against the disposable TEST database (``tests/conftest.py`` refuses
anything else).
"""

from __future__ import annotations

import json
import os
import uuid

import psycopg
import pytest
from demo_closure_cleanup import governed_delete, orphan_sources, plan_steps

pytestmark = pytest.mark.integration


def _url() -> str:
    """The suite's own DATABASE_URL, in libpq form.

    Read from the environment rather than from `dev_api_server.database_url_for`,
    which resolves `.env` and would hand back *production*.
    """
    url = os.environ.get("DATABASE_URL", "")
    assert url, "DATABASE_URL 未设置——无法证明回滚发生在一个真实连接上"
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


@pytest.fixture
def conn():
    connection = psycopg.connect(_url())
    yield connection
    connection.close()


def _new_id() -> str:
    return str(uuid.uuid4())


def _make_source(cur, issuer: str) -> str:
    """A Source with every NOT NULL column filled.

    ``source_availability`` / ``directness`` / ``spatial_precision`` are NOT NULL
    with no default; the values below are the ones real production rows use, so
    the fixture is shaped like the thing it stands in for.
    """
    sid = _new_id()
    cur.execute(
        "insert into source (id, source_type, issuer, issuer_verification, collected_at,"
        " source_availability, directness, spatial_precision,"
        " created_at, updated_at) values (%s, 'statute_or_regulation', %s, 'verified',"
        " now(), 'available_online', 'direct', 'unknown', now(), now())",
        (sid, issuer),
    )
    return sid


def _make_jurisdiction_rule(cur, jid: str, issuer: str, source_id: str) -> str:
    """A place-less legal rule — the shape that stranded a Source last round."""
    cur.execute(
        "insert into jurisdiction_rule (id, jurisdiction_level, jurisdiction_id,"
        " authority, instrument_type, document_name, animal_scope, venue_scope,"
        " action, effect, mandatory_level, status, review_status, source_id,"
        " created_at, updated_at)"
        " values (%s, 'municipal', 'test-city', %s, 'regulation', %s, 'dog',"
        " 'public_place', 'enter', 'prohibited', 'mandatory', 'current',"
        " 'not_reviewed', %s, now(), now())",
        (jid, issuer, issuer, source_id),
    )
    return jid


def _make_place(cur, name: str) -> str:
    pid = _new_id()
    cur.execute(
        "insert into place (id, canonical_name, place_type, lifecycle_status,"
        " created_at, updated_at) values (%s, %s, 'cafe', 'active', now(), now())",
        (pid, name),
    )
    return pid


# --------------------------------------------------------------------------- #
# §19 — mutate → check → commit
# --------------------------------------------------------------------------- #


def test_failed_invariant_rolls_back_for_real(conn) -> None:
    """A refused cleanup must leave the database exactly as it was.

    Asserted from a second connection: inside the failed transaction the row is
    invisible either way, so only another session can tell a real rollback from a
    message that says "rolled back".
    """
    name = f"回滚验证场所-{uuid.uuid4().hex[:8]}"
    with conn.cursor() as cur:
        pid = _make_place(cur, name)
    conn.commit()

    def _mutate(cur):
        cur.execute("delete from place where id = %s", (pid,))
        return {"deleted": {"place": cur.rowcount}}

    def _failing_check(cur):
        return {"verdict": "FAIL", "failures": ["deliberate invariant breach"]}

    outcome = governed_delete(conn, _mutate, _failing_check)

    assert outcome["committed"] is False
    assert outcome["checks"]["verdict"] == "FAIL"

    with psycopg.connect(_url()) as other, other.cursor() as cur:
        cur.execute("select count(*) from place where id = %s", (pid,))
        assert cur.fetchone()[0] == 1, "回滚没有真正发生：另一个会话已经看不到这行"

    # ...and the passing case really does commit, so the gate is not a no-op.
    def _passing_check(cur):
        cur.execute("select count(*) from place where id = %s", (pid,))
        return {"verdict": "PASS" if cur.fetchone()[0] == 0 else "FAIL", "failures": []}

    outcome_ok = governed_delete(conn, lambda cur: _mutate(cur), _passing_check, dry_run=False)
    assert outcome_ok["committed"] is True
    with psycopg.connect(_url()) as other, other.cursor() as cur:
        cur.execute("select count(*) from place where id = %s", (pid,))
        assert cur.fetchone()[0] == 0


def test_dry_run_never_commits(conn) -> None:
    """A plan is a plan: ``dry_run=True`` must leave the row in place."""
    name = f"计划验证场所-{uuid.uuid4().hex[:8]}"
    with conn.cursor() as cur:
        pid = _make_place(cur, name)
    conn.commit()

    def _mutate(cur):
        cur.execute("delete from place where id = %s", (pid,))
        return {"deleted": {"place": cur.rowcount}}

    outcome = governed_delete(
        conn, _mutate, lambda cur: {"verdict": "PASS", "failures": []}, dry_run=True
    )
    assert outcome["committed"] is False

    with psycopg.connect(_url()) as other, other.cursor() as cur:
        cur.execute("select count(*) from place where id = %s", (pid,))
        assert cur.fetchone()[0] == 1

    with conn.cursor() as cur:
        cur.execute("delete from place where id = %s", (pid,))
    conn.commit()


# --------------------------------------------------------------------------- #
# §20 — a fixture legal Source must not survive its fixture
# --------------------------------------------------------------------------- #


def test_jurisdiction_fixture_source_is_removed_with_its_rule(conn) -> None:
    """The exact shape that stranded a Source in the previous round.

    A ``jurisdiction_rule`` has no ``place_id``, so nothing place-scoped can
    reach it. The closure must name it explicitly, and its Source must go with
    it once nothing else points at it.
    """
    issuer = f"回滚法源-{uuid.uuid4().hex[:6]}"
    with conn.cursor() as cur:
        sid = _make_source(cur, issuer)
        jid = _make_jurisdiction_rule(cur, f"reg_test_{uuid.uuid4().hex[:6]}", issuer, sid)
    conn.commit()

    targets = {
        "place_ids": [],
        "zone_ids": [],
        "rule_ids": [],
        "candidate_ids": [],
        "jurisdiction_rule_ids": [jid],
        "source_ids": [sid],
    }
    with conn.cursor() as cur:
        for _label, sql, params in plan_steps(cur, targets):
            cur.execute(sql, params)
        orphans, _retained = orphan_sources(cur, targets["source_ids"])
        assert orphans == [sid], "法律层规则删除后其 Source 应成为孤儿并被清理"
        for orphan in orphans:
            cur.execute("delete from source where id = %s", (orphan,))
    conn.commit()

    with conn.cursor() as cur:
        cur.execute("select count(*) from jurisdiction_rule where id = %s", (jid,))
        assert cur.fetchone()[0] == 0
        cur.execute("select count(*) from source where id = %s", (sid,))
        assert cur.fetchone()[0] == 0, "夹具遗留：法律层 Source 没有随夹具一起清除"


def test_source_referenced_by_a_surviving_rule_is_retained(conn) -> None:
    """§8 — a shared real Source must survive a fixture cleanup.

    The mirror image of the previous test, and the one that protects real data:
    the same deletion plan must *keep* a Source that a surviving rule still uses.
    """
    issuer = f"共享法源-{uuid.uuid4().hex[:6]}"
    with conn.cursor() as cur:
        sid = _make_source(cur, issuer)
        jid = _make_jurisdiction_rule(cur, f"reg_test_{uuid.uuid4().hex[:6]}", issuer, sid)
        # ``ck_access_rule_needs_owner``: a rule must belong to a place or a zone,
        # so the "surviving business rule" needs a surviving place to hang on.
        surviving_place = _make_place(cur, f"存活商业场所-{uuid.uuid4().hex[:8]}")
        rid = _new_id()
        cur.execute(
            "insert into access_rule (id, place_id, animal_scope, action, effect, status,"
            " source_id, rule_origin, recorded_at, created_at, updated_at)"
            " values (%s, %s, 'dog', 'enter', 'prohibited', 'current', %s, 'imported',"
            " now(), now(), now())",
            (rid, surviving_place, sid),
        )
    conn.commit()

    targets = {
        "place_ids": [],
        "zone_ids": [],
        "rule_ids": [],
        "candidate_ids": [],
        "jurisdiction_rule_ids": [jid],
        "source_ids": [sid],
    }
    with conn.cursor() as cur:
        for _label, sql, params in plan_steps(cur, targets):
            cur.execute(sql, params)
        orphans, retained = orphan_sources(cur, targets["source_ids"])
        assert orphans == [], "仍被真实规则引用的 Source 不得被清理"
        assert [r["source_id"] for r in retained] == [sid]

    with conn.cursor() as cur:
        cur.execute("select count(*) from source where id = %s", (sid,))
        assert cur.fetchone()[0] == 1

    # tidy up
    with conn.cursor() as cur:
        cur.execute("delete from access_rule where id = %s", (rid,))
        cur.execute("delete from place where id = %s", (surviving_place,))
        cur.execute("delete from source where id = %s", (sid,))
    conn.commit()


# --------------------------------------------------------------------------- #
# §24 — a cleanup may only append to the audit trail
# --------------------------------------------------------------------------- #


def _delete(cur, pid: str) -> int:
    cur.execute("delete from place where id = %s", (pid,))
    return cur.rowcount


def test_governed_delete_audit_row_is_append_only(conn) -> None:
    """The governance record of a cleanup is a new row, never an edit.

    The count is scoped by a per-run token rather than by the action name, so a
    re-run (or a row left behind by an earlier run) cannot make the assertion
    pass or fail for the wrong reason.
    """
    token = f"UNIT_TEST_APPEND_ONLY_{uuid.uuid4().hex}"
    with conn.cursor() as cur:
        cur.execute("select count(*) from audit_log")
        before = int(cur.fetchone()[0])

    name = f"审计验证场所-{uuid.uuid4().hex[:8]}"
    with conn.cursor() as cur:
        pid = _make_place(cur, name)
    conn.commit()

    governed_delete(
        conn,
        lambda cur: {"deleted": {"place": _delete(cur, pid)}},
        lambda cur: {"verdict": "PASS", "failures": []},
        audit=[
            None,
            "governance-cleanup",
            "governance.cleanup",
            "place",
            pid[:36],
            json.dumps({"deleted": {}}),
            json.dumps({"reason": token}),
        ],
    )

    with conn.cursor() as cur:
        cur.execute("select count(*) from audit_log")
        after = int(cur.fetchone()[0])
        cur.execute(
            "select count(*) from audit_log where action = 'governance.cleanup'"
            " and detail->>'reason' = %s",
            (token,),
        )
        assert cur.fetchone()[0] == 1

    assert after == before + 1, "清理只能追加审计，不能改写或删除既有审计"
