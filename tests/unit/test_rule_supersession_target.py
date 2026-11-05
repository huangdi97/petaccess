"""Explicit RuleCandidate supersession target invariants."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.models import AccessRule, Place, RuleCandidate, Source
from app.models.enums import Directness, PlaceType, RuleStatus, SourceType
from app.services.candidate_service import publish
from app.services.publish_gate import (
    _has_unresolved_conflict,
    _supersession_target_violations,
)


def _id() -> str:
    return str(uuid.uuid4())


def _place(db_session, name: str = "替换规则测试场所") -> Place:
    row = Place(
        id=_id(),
        canonical_name=f"{name}-{uuid.uuid4().hex[:6]}",
        place_type=PlaceType.MALL,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _source(db_session, issuer: str) -> Source:
    row = Source(
        id=_id(),
        source_type=SourceType.OFFICIAL_OPERATOR_POLICY,
        issuer=issuer,
        collected_at=datetime.now(UTC),
        directness=Directness.SECONDARY,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _rule(db_session, place: Place, source: Source, *, effect: str = "prohibited") -> AccessRule:
    row = AccessRule(
        id=_id(),
        place_id=place.id,
        zone_id=None,
        animal_scope="dog",
        action="enter",
        effect=effect,
        source_id=source.id,
        rule_origin="operator_declared",
        rule_layer="OPERATOR_POLICY",
        status=RuleStatus.CURRENT.value,
        recorded_at=datetime.now(UTC),
    )
    db_session.add(row)
    db_session.flush()
    return row


def _candidate(
    db_session,
    place: Place,
    source: Source,
    *,
    target: AccessRule | None = None,
    effect: str = "allowed",
    layer: str = "OPERATOR_POLICY",
) -> RuleCandidate:
    row = RuleCandidate(
        id=_id(),
        source_id=source.id,
        place_id=place.id,
        animal_scope="dog",
        action="enter",
        effect=effect,
        rule_layer=layer,
        extraction_method="manual",
        review_status="APPROVED",
        supersedes_rule_id=target.id if target else None,
    )
    db_session.add(row)
    db_session.flush()
    return row


def _active_codes(rows: list[tuple[str, bool, str]]) -> set[str]:
    return {code for code, failed, _ in rows if failed}


def test_explicit_replacement_target_is_valid_only_on_same_owner_action_and_layer(db_session):
    place = _place(db_session)
    old_source = _source(db_session, "原规则来源")
    new_source = _source(db_session, "新核验来源")
    target = _rule(db_session, place, old_source)
    candidate = _candidate(db_session, place, new_source, target=target)

    assert _active_codes(_supersession_target_violations(db_session, candidate)) == set()


def test_explicit_target_can_resolve_that_cross_source_effect_conflict(db_session):
    place = _place(db_session)
    old_source = _source(db_session, "旧来源")
    new_source = _source(db_session, "新来源")
    target = _rule(db_session, place, old_source, effect="prohibited")
    candidate = _candidate(db_session, place, new_source, target=target, effect="allowed")

    assert _has_unresolved_conflict(db_session, candidate) is False

    third_source = _source(db_session, "另一独立来源")
    _rule(db_session, place, third_source, effect="prohibited")
    assert _has_unresolved_conflict(db_session, candidate) is True


def test_cross_layer_replacement_is_refused(db_session):
    place = _place(db_session)
    old_source = _source(db_session, "法规来源")
    new_source = _source(db_session, "用户核验来源")
    target = _rule(db_session, place, old_source)
    target.rule_layer = "LEGAL"
    candidate = _candidate(db_session, place, new_source, target=target, layer="OPERATOR_POLICY")
    db_session.flush()

    assert "supersession_layer_mismatch" in _active_codes(
        _supersession_target_violations(db_session, candidate)
    )


def test_noncurrent_replacement_target_is_refused(db_session):
    place = _place(db_session)
    old_source = _source(db_session, "历史来源")
    new_source = _source(db_session, "新来源")
    target = _rule(db_session, place, old_source)
    target.status = RuleStatus.SUPERSEDED.value
    candidate = _candidate(db_session, place, new_source, target=target)
    db_session.flush()

    assert "supersession_target_not_current" in _active_codes(
        _supersession_target_violations(db_session, candidate)
    )


def test_publish_marks_explicit_cross_source_target_superseded(db_session, monkeypatch):
    """Write-boundary semantics: an approved explicit target retires atomically."""

    place = _place(db_session)
    old_source = _source(db_session, "旧规则来源")
    new_source = _source(db_session, "经审核的新来源")
    target = _rule(db_session, place, old_source, effect="prohibited")
    candidate = _candidate(db_session, place, new_source, target=target, effect="allowed")

    # This test isolates supersession mutation semantics. Gate behaviour is
    # covered separately above, so bypass the evidence/freshness prerequisites.
    monkeypatch.setattr(
        "app.services.publish_gate.validate_for_publish",
        lambda db, candidate: None,
    )

    published = publish(db_session, candidate, reviewer_id="reviewer-test")
    db_session.flush()

    assert target.status == RuleStatus.SUPERSEDED
    assert published.supersedes_rule_id == target.id
    assert published.source_id == new_source.id
    assert published.status == RuleStatus.CURRENT
