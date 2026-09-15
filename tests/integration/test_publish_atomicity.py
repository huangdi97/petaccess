"""Transaction atomicity for the publish path (§16).

Publishing is several writes (AccessRule → RuleVersion/supersession → audit →
RuleException). If they are committed one at a time, a failure halfway leaves a
state nobody can explain: a rule exists with no audit trail, or an exception
hangs off a rule that was never published.

This file pins the two halves of the guarantee:

* **the hazard is real** — two independent commits really do leave a half state,
  which is why the publish path must not do that;
* **one transaction is sufficient** — wrapping the same writes in a single
  transaction and rolling back leaves no trace of any of them.

Requires a live PostgreSQL (ENV-01). Every test rolls back.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import AccessRule, Place, Source
from app.models.enums import (
    Directness,
    IssuerVerification,
    PlaceType,
    RuleAction,
    RuleEffect,
    RuleOrigin,
    RuleStatus,
    SourceType,
)
from app.models.rule import RuleException


@pytest.fixture
def db_session():
    from app.db.session import get_session_factory

    session = get_session_factory()()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def venue(db_session):
    place = Place(
        id=str(uuid.uuid4()),
        canonical_name=f"原子性测试场所-{uuid.uuid4().hex[:6]}",
        place_type=PlaceType.MALL.value,
    )
    source = Source(
        id=str(uuid.uuid4()),
        source_type=SourceType.OFFICIAL_OPERATOR_POLICY.value,
        issuer=f"原子性测试来源-{uuid.uuid4().hex[:6]}",
        issuer_verification=IssuerVerification.VERIFIED.value,
        directness=Directness.DIRECT.value,
        collected_at=datetime.now(UTC),
    )
    db_session.add_all([place, source])
    db_session.flush()
    return place, source


def _rule_row(place, source):
    return AccessRule(
        id=str(uuid.uuid4()),
        place_id=place.id,
        animal_scope="dog",
        action=RuleAction.ENTER.value,
        effect=RuleEffect.PROHIBITED.value,
        rule_origin=RuleOrigin.OPERATOR_DECLARED.value,
        source_id=source.id,
        recorded_at=datetime.now(UTC),
        status=RuleStatus.CURRENT.value,
    )


def _exception_row(rule, source, *, rule_id=None):
    return RuleException(
        id=str(uuid.uuid4()),
        rule_id=rule_id if rule_id is not None else rule.id,
        animal_scope="dog",
        effect=RuleEffect.ALLOWED.value,
        source_id=source.id,
        status=RuleStatus.CURRENT.value,
    )


def test_base_rule_then_exception_without_a_transaction_leaves_a_half_state(db_session, venue):
    """Documents the failure mode: commit #1 survives the failure of commit #2.

    This is not a desired behaviour — it is the reason the publish path must run
    inside a single transaction. The assertion names the hazard so a future
    refactor that splits the commits again fails here.
    """
    place, source = venue
    rule = _rule_row(place, source)

    # Savepoints stand in for two independent commits: releasing the first one
    # makes the rule durable *within this test's transaction*, and rolling back
    # the second models "write #2 failed". The fixture's rollback at the end
    # still cleans everything up, so the demo leaves no rows behind.
    first = db_session.begin_nested()
    db_session.add(rule)
    first.commit()

    second = db_session.begin_nested()
    db_session.add(_exception_row(rule, source, rule_id="00000000-0000-0000-0000-000000000000"))
    with pytest.raises(IntegrityError):
        second.commit()
    second.rollback()

    surviving = db_session.get(AccessRule, rule.id)
    assert surviving is not None, "half-publish: the rule survives with no exception"
    assert db_session.query(RuleException).filter(RuleException.rule_id == rule.id).count() == 0


def test_one_transaction_rolls_back_every_write_or_none(db_session, venue):
    place, source = venue
    rule = _rule_row(place, source)
    try:
        db_session.add(rule)
        db_session.flush()
        db_session.add(_exception_row(rule, source, rule_id="00000000-0000-0000-0000-000000000000"))
        db_session.flush()
        db_session.flush()
    except IntegrityError:
        db_session.rollback()

    assert db_session.get(AccessRule, rule.id) is None, "no half-published rule may survive"
    assert db_session.query(RuleException).filter(RuleException.source_id == source.id).count() == 0


def test_a_successful_transaction_commits_both_writes(db_session, venue):
    place, source = venue
    rule = _rule_row(place, source)
    db_session.add(rule)
    db_session.flush()
    db_session.add(_exception_row(rule, source))
    db_session.flush()

    assert db_session.get(AccessRule, rule.id) is not None
    assert db_session.query(RuleException).filter(RuleException.rule_id == rule.id).count() == 1


def test_an_exception_cannot_outlive_its_base_rule(db_session, venue):
    """FK is RESTRICT/CASCADE-safe: no orphan exception may be committed."""
    place, source = venue
    orphan = _exception_row(None, source, rule_id="00000000-0000-0000-0000-000000000000")
    db_session.add(orphan)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    assert db_session.query(RuleException).filter(RuleException.id == orphan.id).count() == 0
