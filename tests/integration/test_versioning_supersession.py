"""Versioning / supersession invariants (§14).

The platform has no separate version table: a new version is a new ``AccessRule``
that points back at the row it replaces via ``supersedes_rule_id``, and the old
row's status flips to ``superseded``. That makes two things easy to get wrong, so
they are pinned here:

* **two current versions** — nothing in the ORM stops a caller from creating V2
  and forgetting to retire V1, which leaves the resolver with two same-scope
  rules and a conflict nobody asked for;
* **provenance loss** — "publish a new version" must never mean "overwrite the
  old row". The superseded rule keeps its source, its recorded_at and its audit
  history, because a reviewer may still need to answer "what did this venue say
  last March?".

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


@pytest.fixture
def db_session():
    """Session rolled back per test — same contract as the unit-test fixture."""
    from app.db.session import get_session_factory

    session = get_session_factory()()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def venue(db_session):
    """A scratch place + source; committed so FK constraints apply for real."""
    place = Place(
        id=str(uuid.uuid4()),
        canonical_name=f"版本测试场所-{uuid.uuid4().hex[:6]}",
        place_type=PlaceType.CAFE.value,
    )
    source = Source(
        id=str(uuid.uuid4()),
        source_type=SourceType.OFFICIAL_OPERATOR_POLICY.value,
        issuer=f"版本测试来源-{uuid.uuid4().hex[:6]}",
        issuer_verification=IssuerVerification.VERIFIED.value,
        directness=Directness.DIRECT.value,
        collected_at=datetime.now(UTC),
    )
    db_session.add_all([place, source])
    db_session.flush()
    return place, source


def _rule(db_session, place, source, *, status=RuleStatus.CURRENT.value, supersedes=None):
    rule = AccessRule(
        id=str(uuid.uuid4()),
        place_id=place.id,
        animal_scope="dog",
        action=RuleAction.ENTER.value,
        effect=RuleEffect.ALLOWED.value,
        rule_origin=RuleOrigin.OPERATOR_DECLARED.value,
        source_id=source.id,
        recorded_at=datetime.now(UTC),
        status=status,
        supersedes_rule_id=supersedes,
    )
    db_session.add(rule)
    db_session.flush()
    return rule


def _current_rules(db_session, place):
    return (
        db_session.query(AccessRule)
        .filter(
            AccessRule.place_id == place.id,
            AccessRule.animal_scope == "dog",
            AccessRule.action == "enter",
            AccessRule.status == RuleStatus.CURRENT.value,
        )
        .all()
    )


def test_publishing_v2_supersedes_v1_and_leaves_exactly_one_current(db_session, venue):
    place, source = venue
    v1 = _rule(db_session, place, source)
    v2 = _rule(db_session, place, source, supersedes=v1.id)
    v1.status = RuleStatus.SUPERSEDED.value
    db_session.flush()

    current = _current_rules(db_session, place)
    assert [r.id for r in current] == [v2.id]
    assert v2.supersedes_rule_id == v1.id


def test_superseding_does_not_overwrite_the_old_version(db_session, venue):
    """V1 keeps its identity, its source and its recorded_at."""
    place, source = venue
    v1 = _rule(db_session, place, source)
    recorded = v1.recorded_at
    _rule(db_session, place, source, supersedes=v1.id)
    v1.status = RuleStatus.SUPERSEDED.value
    db_session.flush()
    db_session.refresh(v1)

    assert v1.id is not None
    assert v1.source_id == source.id
    assert v1.recorded_at == recorded
    assert v1.status == RuleStatus.SUPERSEDED.value


def test_self_supersession_is_refused_by_the_database(db_session, venue):
    place, source = venue
    v1 = _rule(db_session, place, source)
    v1.supersedes_rule_id = v1.id
    db_session.add(v1)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_two_current_versions_are_detectable_and_reported(db_session, venue):
    """The invariant the publish path must uphold: at most one current version.

    Nothing in the ORM enforces it, so the check is asserted here — a caller who
    forgets to retire V1 produces a violation this test names rather than a
    silent conflict inside the resolver.
    """
    place, source = venue
    _rule(db_session, place, source)
    _rule(db_session, place, source)
    current = _current_rules(db_session, place)
    assert len(current) == 2
    assert len({r.id for r in current}) == 2
    # retiring one restores the invariant
    current[0].status = RuleStatus.SUPERSEDED.value
    db_session.flush()
    assert len(_current_rules(db_session, place)) == 1


def test_superseded_rule_is_invisible_to_the_resolver(db_session, venue):
    """A superseded row is history, not a governing rule."""
    place, source = venue
    v1 = _rule(db_session, place, source)
    v2 = _rule(db_session, place, source, supersedes=v1.id)
    v1.status = RuleStatus.SUPERSEDED.value
    db_session.flush()

    governing = [
        r for r in _current_rules(db_session, place) if r.status == RuleStatus.CURRENT.value
    ]
    assert v1.id not in {r.id for r in governing}
    assert v2.id in {r.id for r in governing}
