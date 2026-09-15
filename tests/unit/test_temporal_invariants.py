"""Time / timezone invariants (§27).

Every timestamp the platform persists is timezone-aware. Mixing naive and aware
datetimes raises ``TypeError`` in Python, which is the *correct* outcome: a
silent comparison would either let an expired rule govern or suppress a live
one. These tests lock that behaviour, plus the window boundaries that decide
whether a rule is in force at a given instant.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import DateTime, inspect

from app.db.base import Base
from app.models import civic, evidence, media, observation, place, rule, user, v05  # noqa: F401
from app.models.rule import RuleException
from app.rulespec.v05_resolver import (
    LayeredException,
    LayeredRule,
    RuleLayer,
    resolve,
)

CN = ZoneInfo("Asia/Shanghai")
NY = ZoneInfo("America/New_York")


def lr(id_, *, from_=None, to=None, effect="prohibited", layer=RuleLayer.OPERATOR_POLICY.value):
    return LayeredRule(
        id=id_,
        animal_scope="dog",
        action="enter",
        effect=effect,
        rule_layer=layer,
        origin="operator_direct",
        subject_scope_normalized="ordinary_dog",
        normalization_type="exact",
        effective_from=from_,
        effective_to=to,
    )


def base(now, **overrides):
    kw = dict(
        legal=[],
        guidance=[],
        template_rules=[],
        operator_rules=[],
        event_rules=[],
        animal="dog",
        service_role="none",
        action="enter",
        zone_id=None,
        now=now,
    )
    kw.update(overrides)
    return kw


# --------------------------------------------------------------------------
# persistence: every stored datetime is timezone-aware
# --------------------------------------------------------------------------


def _datetime_columns():
    for mapper in Base.registry.mappers:
        for column in mapper.columns:
            if isinstance(column.type, DateTime):
                yield mapper.class_.__name__, column


def test_every_persisted_datetime_column_is_timezone_aware():
    naive = [
        f"{cls}.{col.key}" for cls, col in _datetime_columns() if col.type.timezone is not True
    ]
    assert naive == [], f"naive datetime columns would mix with aware values: {naive}"


def test_the_scan_actually_saw_the_rule_tables():
    """Guard against the previous test passing because nothing was imported."""
    cols = {f"{cls}.{col.key}" for cls, col in _datetime_columns()}
    assert "AccessRule.effective_from" in cols
    assert "RuleException.effective_to" in cols
    assert "Source.collected_at" in cols


def test_rule_exception_windows_are_timezone_aware_columns():
    exc_cols = {c.name: c for c in inspect(RuleException).columns}
    assert exc_cols["effective_from"].type.timezone is True
    assert exc_cols["effective_to"].type.timezone is True


# --------------------------------------------------------------------------
# naive / aware must fail loudly
# --------------------------------------------------------------------------


def test_comparing_a_naive_now_against_an_aware_window_raises():
    rule_obj = lr("R1", from_=datetime(2026, 1, 1, tzinfo=UTC))
    with pytest.raises(TypeError):
        resolve(**base(now=datetime(2026, 6, 1), operator_rules=[rule_obj]))  # naive now


def test_naive_exception_window_raises_instead_of_silently_applying():
    base_rule = LayeredRule(
        id="B1",
        animal_scope="dog",
        action="enter",
        effect="prohibited",
        rule_layer=RuleLayer.OPERATOR_POLICY.value,
        origin="operator_direct",
        subject_scope_normalized="dog",
        normalization_type="exact",
    )
    exc = LayeredException(
        id="E1",
        rule_id="B1",
        animal_scope="dog",
        effect="allowed",
        source_id="s1",
        subject_scope_normalized="ordinary_dog",
        normalization_type="exact",
        effective_from=datetime(2026, 1, 1),  # naive on purpose
    )
    with pytest.raises(TypeError):
        exc.active_at(datetime(2026, 6, 1, tzinfo=UTC))
    # and the same failure surfaces through the resolver, not just the helper
    with pytest.raises(TypeError):
        resolve(
            **base(
                now=datetime(2026, 6, 1, tzinfo=UTC),
                operator_rules=[base_rule],
                exceptions=[exc],
            )
        )


# --------------------------------------------------------------------------
# window boundaries
# --------------------------------------------------------------------------


def test_effective_from_is_inclusive():
    start = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    rs = resolve(**base(now=start, operator_rules=[lr("R1", from_=start, effect="prohibited")]))
    assert rs.effect == "prohibited"


def test_one_instant_before_effective_from_is_outside_the_window():
    start = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    rs = resolve(
        **base(now=start - timedelta(microseconds=1), operator_rules=[lr("R1", from_=start)])
    )
    assert rs.effect == "unknown"


def test_effective_to_is_inclusive():
    end = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    rs = resolve(**base(now=end, operator_rules=[lr("R1", to=end, effect="prohibited")]))
    assert rs.effect == "prohibited"


def test_one_instant_after_effective_to_is_outside_the_window():
    end = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    rs = resolve(**base(now=end + timedelta(microseconds=1), operator_rules=[lr("R1", to=end)]))
    assert rs.effect == "unknown"


def test_midnight_boundary_in_asia_shanghai_is_the_same_instant_as_utc():
    """08:00 Asia/Shanghai == 00:00 UTC — a venue's local midnight is not a UTC day."""
    local_midnight = datetime(2026, 9, 15, 0, 0, tzinfo=CN)
    utc_equivalent = datetime(2026, 9, 14, 16, 0, tzinfo=UTC)
    assert local_midnight == utc_equivalent
    rs_local = resolve(**base(now=local_midnight, operator_rules=[lr("R1", from_=utc_equivalent)]))
    assert rs_local.effect == "prohibited"


def test_a_window_defined_in_utc_governs_the_shanghai_midnight_before_it():
    """The same instant in Shanghai is the previous UTC day."""
    utc_from = datetime(2026, 9, 15, 0, 0, tzinfo=UTC)
    shanghai_before = datetime(2026, 9, 15, 7, 59, tzinfo=CN)  # 23:59 UTC on the 14th
    rs = resolve(**base(now=shanghai_before, operator_rules=[lr("R1", from_=utc_from)]))
    assert rs.effect == "unknown"


def test_dst_transition_does_not_shift_a_window_by_an_hour():
    """America/New_York leaves DST on 2026-11-01; the UTC offset changes."""
    before = datetime(2026, 10, 31, 12, 0, tzinfo=NY)
    after = datetime(2026, 11, 2, 12, 0, tzinfo=NY)
    assert before.utcoffset() == timedelta(hours=-4)
    assert after.utcoffset() == timedelta(hours=-5)
    # Same-tzinfo subtraction is wall-clock (2 days). The elapsed instants differ
    # by 2 days + 1 hour, which is only visible once both are on a fixed offset:
    # computing a validity window in local time without converting is how a rule
    # silently gains or loses an hour across a DST change.
    assert after - before == timedelta(days=2)
    assert after.astimezone(UTC) - before.astimezone(UTC) == timedelta(days=2, hours=1)


def test_exception_window_boundaries_are_inclusive_on_both_ends():
    exc = LayeredException(
        id="E1",
        rule_id="B1",
        animal_scope="dog",
        effect="allowed",
        source_id="s1",
        subject_scope_normalized="ordinary_dog",
        normalization_type="exact",
        effective_from=datetime(2026, 9, 1, tzinfo=UTC),
        effective_to=datetime(2026, 9, 30, tzinfo=UTC),
    )
    # effective_to is an instant, not a calendar day: 2026-09-30T00:00Z is
    # inside the window, 23:59:59 of the same calendar day is already past it.
    assert exc.active_at(datetime(2026, 9, 1, tzinfo=UTC)) is True
    assert exc.active_at(datetime(2026, 9, 30, tzinfo=UTC)) is True
    assert exc.active_at(datetime(2026, 9, 30, 0, 0, 1, tzinfo=UTC)) is False
    assert exc.active_at(datetime(2026, 8, 31, 23, 59, 59, tzinfo=UTC)) is False
