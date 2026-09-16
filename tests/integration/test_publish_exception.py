"""RuleException publication: the write path, not just the plan.

The publisher's dry-run can say "this candidate is a carve-out of that base
rule", but the sentence only means something if the write does the same thing.
``publish_exception`` is that write, and these tests exercise it against a real
Postgres inside a transaction that is rolled back — so the invariants are proved
on the same code path production would take, without publishing anything.

What is proved here:

* a carve-out lands in ``rule_exception``, never as a second AccessRule;
* the ADR-025 scope layer (source_scope_exact / subject_scope_normalized /
  normalization_type / normative_effect / holder_scope) survives verbatim;
* a **cross-layer** binding is refused at the boundary, so an operator's "we
  allow it" cannot be laundered into the LEGAL layer even if the plan were wrong;
* a missing or superseded base is refused;
* a failed base never leaves a half-attached carve-out behind;
* the dry-run issues **zero** writes.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.errors import ApiError
from app.db.session import get_session_factory
from app.models import AccessRule, EvidenceBundle, Place, RuleCandidate, RuleException, Source
from app.models.enums import RuleStatus
from app.models.evidence import SourceArtifact
from app.services.candidate_service import publish_exception

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "publish_reviewed_r1.py"
REGISTRY = REPO / "docs" / "reality_audit" / "review_decisions_r2_final.json"


@pytest.fixture
def session():
    """A real session whose work is always rolled back."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def mod():
    spec = importlib.util.spec_from_file_location("publish_reviewed_r1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source(db, *, source_type="statute_or_regulation"):
    src = Source(
        source_type=source_type,
        issuer=f"集成测试来源 {uuid.uuid4().hex[:8]}",
        issuer_verification="verified",
        directness="direct",
        source_availability="available_online",
        spatial_precision="unknown",
        collected_at=datetime.now(UTC),
        observed_at=datetime.now(UTC),
    )
    db.add(src)
    db.flush()
    return src


def _place(db):
    place = Place(
        canonical_name=f"例外发布测试场所 {uuid.uuid4().hex[:8]}",
        place_type="mall",
        lifecycle_status="active",
    )
    db.add(place)
    db.flush()
    return place


def _evidence(db, source):
    artifact = SourceArtifact(
        source_id=source.id,
        source_platform="official_website",
        publisher_type="official",
        artifact_type="statute_text",
        source_url="https://example.invalid/test",
        content_hash="a" * 64,
        collected_at=datetime.now(UTC),
        evidence_strength="primary_direct",
        storage_allowed=True,
        display_allowed=True,
        redistribution_allowed=False,
    )
    db.add(artifact)
    db.flush()
    bundle = EvidenceBundle(
        artifact_id=artifact.id,
        source_id=source.id,
        source_platform="official_website",
        publisher_type="official",
        source_url="https://example.invalid/test",
        captured_at=datetime.now(UTC),
        evidence_class="official_document",
        quoted_fragment="禁止携带犬只进入商场；盲人携带导盲犬的，不受本条规定的限制。",
        content_hash="a" * 64,
        place_match_evidence={"matched_by": "canonical_name_and_address"},
        license_metadata={"storage_allowed": True, "display_allowed": True},
    )
    db.add(bundle)
    db.flush()
    return bundle


def _candidate(
    db,
    *,
    source,
    place,
    bundle,
    effect="allowed",
    animal_scope="service_dog",
    rule_layer="LEGAL",
    mandatory_level="mandatory",
    subject="guide_dog",
    normalization="exact",
    normative_effect="exempt_from_prohibition",
    holder="person_with_disability",
):
    cand = RuleCandidate(
        source_id=source.id,
        place_id=place.id,
        zone_id=None,
        animal_scope=animal_scope,
        action="enter",
        effect=effect,
        rule_layer=rule_layer,
        mandatory_level=mandatory_level,
        proposed_conditions=[],
        extraction_method="import",
        review_status="APPROVED",
        evidence_bundle_id=bundle.id,
        source_scope_exact="导盲犬",
        subject_scope_normalized=subject,
        normalization_type=normalization,
        normative_effect=normative_effect,
        holder_scope=holder,
    )
    db.add(cand)
    db.flush()
    return cand


def _base_rule(db, *, source, place, rule_layer="LEGAL", effect="prohibited"):
    rule = AccessRule(
        place_id=place.id,
        zone_id=None,
        animal_scope="dog",
        action="enter",
        effect=effect,
        source_id=source.id,
        rule_origin="imported",
        recorded_at=datetime.now(UTC),
        status="current",
        rule_layer=rule_layer,
        mandatory_level="mandatory" if rule_layer == "LEGAL" else "operator_discretion",
    )
    db.add(rule)
    db.flush()
    return rule


def _counts(db) -> dict[str, int]:
    from sqlalchemy import func, select

    return {
        "access_rule": db.scalar(select(func.count()).select_from(AccessRule)),
        "rule_exception": db.scalar(select(func.count()).select_from(RuleException)),
        "rule_candidate": db.scalar(select(func.count()).select_from(RuleCandidate)),
    }


# ---------------------------------------------------------------- the happy path


def test_a_carve_out_is_written_as_a_rule_exception_not_a_second_rule(session):
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    cand = _candidate(session, source=src, place=place, bundle=bundle)
    before_rules = _counts(session)["access_rule"]

    exc = publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")

    assert isinstance(exc, RuleException)
    assert exc.rule_id == base.id, "例外必须挂到 base 规则上"
    assert _counts(session)["access_rule"] == before_rules, "不得因此多出一条 AccessRule"
    assert cand.review_status == "PUBLISHED"
    assert cand.published_rule_id == base.id


def test_the_source_faithful_scope_survives_the_write(session):
    """ADR-025 / ADR-028: publishing must not re-derive or widen the subject."""
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    cand = _candidate(session, source=src, place=place, bundle=bundle)

    exc = publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")

    assert exc.source_scope_exact == "导盲犬", "来源原话必须原样保留"
    assert exc.subject_scope_normalized == "guide_dog"
    assert exc.normalization_type == "exact"
    assert exc.normative_effect == "exempt_from_prohibition"
    assert exc.holder_scope == "person_with_disability"
    assert exc.source_id == src.id, "例外必须有来源（列为 NOT NULL）"
    assert exc.status == RuleStatus.CURRENT


def test_the_written_exception_reaches_the_resolver(session):
    """The point of the carve-out is that the resolver can see it."""
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    cand = _candidate(session, source=src, place=place, bundle=bundle)
    publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")

    from sqlalchemy import select

    from app.models import RuleException as RuleExceptionModel

    stored = session.scalars(
        select(RuleExceptionModel).where(RuleExceptionModel.rule_id == base.id)
    ).all()
    assert len(stored) == 1
    assert stored[0].status == "current"


# ---------------------------------------------------------------- refusals


def test_a_cross_layer_binding_is_refused_at_the_write_boundary(session):
    """OPERATOR carve-out onto a LEGAL prohibition: refused, not coerced.

    ``rule_exception`` inherits its base rule's layer in the resolver, so letting
    this through would let an operator's allowance out-vote the statute.
    """
    src = _source(session, source_type="official_operator_policy")
    place = _place(session)
    bundle = _evidence(session, src)
    legal_base = _base_rule(session, source=src, place=place, rule_layer="LEGAL")
    cand = _candidate(
        session,
        source=src,
        place=place,
        bundle=bundle,
        rule_layer="OPERATOR_POLICY",
        mandatory_level="operator_discretion",
        normative_effect=None,
    )
    before = _counts(session)

    with pytest.raises(ApiError) as excinfo:
        publish_exception(session, cand, base_rule_id=legal_base.id, reviewer_id="reviewer-1")

    assert getattr(excinfo.value, "code", None) == "cross_layer_exception_binding"
    assert _counts(session) == before, "被拒绝的绑定不得留下半成品"
    assert cand.review_status == "APPROVED", "被拒绝后候选状态必须原样"


def test_a_missing_base_is_refused(session):
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    cand = _candidate(session, source=src, place=place, bundle=bundle)

    with pytest.raises(ApiError) as excinfo:
        publish_exception(session, cand, base_rule_id=str(uuid.uuid4()), reviewer_id="reviewer-1")
    assert getattr(excinfo.value, "code", None) == "exception_base_missing"
    assert cand.review_status == "APPROVED"


def test_a_superseded_base_is_refused(session):
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    base.status = RuleStatus.SUPERSEDED
    session.flush()
    cand = _candidate(session, source=src, place=place, bundle=bundle)

    with pytest.raises(ApiError) as excinfo:
        publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")
    assert getattr(excinfo.value, "code", None) == "exception_base_not_current"


def test_a_candidate_that_is_not_approved_is_refused(session):
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    cand = _candidate(session, source=src, place=place, bundle=bundle)
    cand.review_status = "REVIEW_PENDING"
    session.flush()

    with pytest.raises(ApiError) as excinfo:
        publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")
    assert getattr(excinfo.value, "code", None) == "candidate_not_approved"


def test_the_publish_gate_still_applies_to_a_carve_out(session):
    """A carve-out is a published normative statement, not a note."""
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    cand = _candidate(session, source=src, place=place, bundle=bundle)
    cand.evidence_bundle_id = None
    cand.media_id = None
    session.flush()
    before = _counts(session)

    with pytest.raises(ApiError) as excinfo:
        publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")
    assert getattr(excinfo.value, "code", None) == "evidence_missing"
    assert _counts(session) == before


# ---------------------------------------------------------------- transaction shape


def test_a_failed_base_leaves_no_half_attached_carve_out(session):
    """§11: base succeeds, carve-out fails ⇒ no unexplainable half-published state."""
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    cand = _candidate(
        session,
        source=src,
        place=place,
        bundle=bundle,
        rule_layer="OPERATOR_POLICY",
        mandatory_level="operator_discretion",
    )

    # the base is fine; the carve-out's binding is not
    with pytest.raises(ApiError):
        publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")

    from sqlalchemy import func, select

    remaining = session.scalar(
        select(func.count()).select_from(RuleException).where(RuleException.rule_id == base.id)
    )
    assert remaining == 0, "失败后不得残留指向 base 的例外"
    assert base.status == "current", "base 本身不受影响"


def test_publishing_a_carve_out_twice_is_impossible(session):
    """The CAS on review_status is what makes a re-run safe."""
    src = _source(session)
    place = _place(session)
    bundle = _evidence(session, src)
    base = _base_rule(session, source=src, place=place)
    cand = _candidate(session, source=src, place=place, bundle=bundle)
    publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")

    with pytest.raises(ApiError) as excinfo:
        publish_exception(session, cand, base_rule_id=base.id, reviewer_id="reviewer-1")
    assert getattr(excinfo.value, "code", None) == "candidate_not_approved"


# ---------------------------------------------------------------- dry-run is read-only


def test_the_real_gate_reads_the_signed_register_candidates(session, mod):
    """The dry-run's gate port must resolve every APPROVED row against the DB."""
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    approved = [
        r for r in registry["rows"] if r["final_decision"] in ("APPROVED", "APPROVED_WITH_NOTE")
    ]
    gate = mod.DatabaseGate(session)
    outcomes = {
        r["rule_id"]: gate.evaluate(candidate_id=r["candidate_id"], rule_id=r["rule_id"])
        for r in approved
    }
    assert len(outcomes) == len(approved) == 23
    missing = [k for k, v in outcomes.items() if v.status == mod.GATE_NOT_RUN]
    assert missing == [], f"闸门必须真实执行：{missing}"
    # every APPROVED row got a real verdict, and the report cannot claim PASS
    # for a row the gate never saw
    assert {v.status for v in outcomes.values()} <= {mod.GATE_PASS, mod.GATE_BLOCKED}
    held = [r["rule_id"] for r in registry["rows"] if r["final_decision"] == "HOLD"]
    assert "lib-sd-op-military" in held, "军警犬豁免已由人类 HOLD，不得出现在被评估集合中"
    assert "lib-sd-op-military" not in outcomes


def test_the_dry_run_writes_nothing(mod, session):
    """§14: run the real pipeline and prove the database did not move."""
    from sqlalchemy import text

    def counts():
        return {
            t: int(session.execute(text(f"SELECT count(*) FROM {t}")).scalar_one())
            for t in ("access_rule", "rule_exception", "rule_candidate", "audit_log")
        }

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = [dict(r) for r in registry["rows"]]
    mod.annotate_from_db(rows, session)
    before = counts()

    gate = mod.DatabaseGate(session)
    plan = mod.build_plan(
        rows,
        bindings=mod.canonical_exception_bindings(registry),
        gate=gate,
        revision=registry["revision"],
        reviewer=mod.signed_reviewer(rows),
    )
    mod.plan_integrity(plan, rows_by_rule={r["rule_id"]: r for r in rows}, supersession_edges={})

    assert counts() == before, "dry-run 触碰了数据库"
    assert plan.gate_ran is True
    assert len(plan.writable) == 23


def test_the_cli_dry_run_leaves_the_database_untouched():
    """The strongest form: the command a human actually runs, end to end."""
    from sqlalchemy import text

    db = get_session_factory()()

    def counts():
        return {
            t: int(db.execute(text(f"SELECT count(*) FROM {t}")).scalar_one())
            for t in ("access_rule", "rule_exception", "rule_candidate", "audit_log")
        }

    try:
        before = counts()
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--dry-run", "--max-approve", "23", "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            check=False,
        )
        assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
        assert counts() == before, "CLI dry-run 不得写库"
        payload = proc.stdout[proc.stdout.rindex('{\n  "summary"') :]
        report = json.loads(payload)
        assert report["summary"]["DRY_RUN_ZERO_DB_MUTATION"] is True
        assert report["summary"]["prepublish_pass"] == 23
        assert report["summary"]["prepublish_blocked"] == 0
        assert report["summary"]["rule_exception_create_count"] == 11
        assert report["summary"]["hold_publishable"] == 0
        assert report["summary"]["rejected_publishable"] == 0
        assert report["integrity"]["CROSS_LAYER_EXCEPTION"] == 0
        assert report["integrity"]["SELF_SUPERSEDE"] == 0
        assert report["integrity"]["DUPLICATE_PUBLICATION_PLAN"] == 0
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------- HTTP surface


def test_the_publish_endpoint_accepts_an_exception_base():
    """The new body field is part of the published contract, not a local detail.

    The request body is optional, so an existing caller that sends nothing keeps
    publishing an ordinary AccessRule — the exemption is opt-in and explicit.
    """
    from app.main import app

    schema = app.openapi()
    operation = schema["paths"]["/api/v1/admin/candidates/{candidate_id}/publish"]["post"]
    body_ref = json.dumps(operation.get("requestBody", {}))
    assert "PublishIn" in body_ref, operation
    model = schema["components"]["schemas"]["PublishIn"]
    assert "exception_of_rule_id" in model["properties"], model


def test_publishing_through_http_records_an_exception_audit_entry():
    """End to end through the API: one carve-out, one audit row, no AccessRule.

    The fixtures are built here and removed afterwards, so the pilot data the
    signed register describes is never touched.
    """
    import uuid as _uuid

    from fastapi.testclient import TestClient
    from sqlalchemy import delete, func, select

    from app.main import app
    from app.models import User

    db = get_session_factory()()
    created: dict[str, str] = {}
    try:
        src = _source(db, source_type="official_operator_policy")
        place = _place(db)
        bundle = _evidence(db, src)
        base = _base_rule(db, source=src, place=place, rule_layer="OPERATOR_POLICY")
        cand = _candidate(
            db,
            source=src,
            place=place,
            bundle=bundle,
            rule_layer="OPERATOR_POLICY",
            mandatory_level="operator_discretion",
            normative_effect=None,
        )
        created = {
            "source": src.id,
            "place": place.id,
            "candidate": cand.id,
            "base": base.id,
            "artifact": bundle.artifact_id,
            "bundle": bundle.id,
        }
        db.commit()

        with TestClient(app) as client:
            email = f"publish-exc-{_uuid.uuid4().hex[:8]}@example.com"
            registered = client.post(
                "/api/v1/auth/register",
                json={"display_name": "例外发布测试", "email": email, "password": "passw0rd123"},
            )
            assert registered.status_code == 201, registered.text
            token = registered.json()["access_token"]
            admin = db.query(User).filter(User.email == email).one()
            admin.role = "moderator"
            db.commit()

            before = db.scalar(select(func.count()).select_from(AccessRule))
            response = client.post(
                f"/api/v1/admin/candidates/{cand.id}/publish",
                json={"exception_of_rule_id": base.id},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["publication_type"] == "rule_exception"
            assert body["rule_exception_id"]
            assert body["published_rule_id"] == base.id

        db.expire_all()
        assert db.scalar(select(func.count()).select_from(AccessRule)) == before, (
            "例外发布不得新增 AccessRule"
        )
        audit = db.scalar(
            select(func.count())
            .select_from(__import__("app.models", fromlist=["AuditLog"]).AuditLog)
            .where(
                __import__("app.models", fromlist=["AuditLog"]).AuditLog.action
                == "candidate.publish_exception"
            )
        )
        assert audit >= 1, "例外发布必须留下审计记录"
    finally:
        if created:
            from app.models import AuditLog

            db.rollback()
            db.execute(delete(User).where(User.email.like("publish-exc-%@example.com")))
            db.execute(delete(RuleException).where(RuleException.rule_id == created["base"]))
            db.execute(delete(RuleCandidate).where(RuleCandidate.id == created["candidate"]))
            db.execute(delete(AccessRule).where(AccessRule.id == created["base"]))
            db.execute(delete(EvidenceBundle).where(EvidenceBundle.id == created["bundle"]))
            db.execute(delete(SourceArtifact).where(SourceArtifact.id == created["artifact"]))
            db.execute(delete(Source).where(Source.id == created["source"]))
            db.execute(delete(Place).where(Place.id == created["place"]))
            db.execute(delete(AuditLog).where(AuditLog.action == "candidate.publish_exception"))
            db.commit()
        db.close()
