"""Watch-notification idempotency under clock drift (§20).

``notify_rule_changes`` decides "has this rule changed since I last told you?"
by comparing two timestamps:

    AccessRule.updated_at  >  WatchSubscription.last_notified_at

``updated_at`` is written by PostgreSQL. ``last_notified_at`` used to be written
from the *worker process* — ``datetime.now(UTC)``. That comparison is therefore
made between two clocks, and nothing keeps them together. A Docker container a
few seconds ahead of its host (the normal case here, measured at ~22s) makes
``updated_at > last_notified_at`` stay true after the first notification, so
**every sweep re-notifies the same watchers** until the clocks agree again. The
sweep interval is hourly, so in production this shows up as duplicates rather
than as a hung loop — which is exactly the kind of failure that survives review.

The regression test below does not need a skewed clock to exist: it pins the
invariant *directly* by moving the process clock an hour into the past. Under the
old code that is indistinguishable from drift and the second sweep duplicates;
with the watermark read from ``SELECT now()`` the process clock is not consulted
at all, and the second sweep is a no-op.

Requires a live PostgreSQL (ENV-01) and Redis (the mock notification sink).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.models import AccessRule, Place, Source, User
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

WATCH_PREFIX = "观察哨测试场所"


@pytest.fixture
def db_session():
    """Session rolled back per test; the sweep's own session is cleaned up too."""
    from app.db.session import get_session_factory

    session = get_session_factory()()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def watched_venue(db_session):
    """A scratch place with one current rule, plus a watcher on that place.

    Committed (not merely flushed) because the worker task opens its own session
    and must be able to see the rows. Torn down afterwards: the sweep commits, so
    a rollback alone would leave the fixtures behind in a development database.
    """
    from app.models import WatchSubscription

    user = db_session.query(User).first()
    if user is None:  # pragma: no cover - a seeded development database has one
        pytest.skip("no user row available to own a watch subscription")

    suffix = uuid.uuid4().hex[:6]
    place = Place(
        id=str(uuid.uuid4()),
        canonical_name=f"{WATCH_PREFIX}-{suffix}",
        place_type=PlaceType.CAFE.value,
    )
    source = Source(
        id=str(uuid.uuid4()),
        source_type=SourceType.OFFICIAL_OPERATOR_POLICY.value,
        issuer=f"观察哨测试来源-{suffix}",
        issuer_verification=IssuerVerification.VERIFIED.value,
        directness=Directness.DIRECT.value,
        collected_at=datetime.now(UTC),
    )
    db_session.add_all([place, source])
    db_session.flush()

    rule = AccessRule(
        id=str(uuid.uuid4()),
        place_id=place.id,
        animal_scope="dog",
        action=RuleAction.ENTER.value,
        effect=RuleEffect.ALLOWED.value,
        rule_origin=RuleOrigin.OPERATOR_DECLARED.value,
        source_id=source.id,
        recorded_at=datetime.now(UTC),
        status=RuleStatus.CURRENT.value,
    )
    watch = WatchSubscription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        target_type="place",
        target_id=place.id,
        channels=["in_app"],
        last_notified_at=None,
    )
    db_session.add_all([rule, watch])
    db_session.commit()

    try:
        yield place, rule, watch
    finally:
        from app.models import WatchSubscription as WS

        cleanup = db_session
        cleanup.query(WS).filter(WS.id == watch.id).delete()
        cleanup.query(AccessRule).filter(AccessRule.id == rule.id).delete()
        cleanup.query(Source).filter(Source.id == source.id).delete()
        cleanup.query(Place).filter(Place.id == place.id).delete()
        cleanup.commit()


def _sink_messages_for(place_name: str) -> list[dict]:
    """Mock-sink entries addressed to this drill's place.

    The sweep is global — it notifies every eligible watch — so counting the
    whole sink would measure other people's subscriptions.
    """
    import redis as redis_lib

    from app.core.config import get_settings

    client = redis_lib.Redis.from_url(get_settings().redis_url, decode_responses=True)
    out: list[dict] = []
    for raw in client.lrange("mock:notifications", 0, -1):
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:  # pragma: no cover - sink is written by us
            continue
        if place_name in str(item.get("title") or ""):
            out.append(item)
    return out


def test_a_second_sweep_does_not_renotify(watched_venue):
    from app.worker.tasks import notify_rule_changes

    place, _, _ = watched_venue
    before = len(_sink_messages_for(place.canonical_name))

    notify_rule_changes.run()
    after_first = _sink_messages_for(place.canonical_name)
    assert len(after_first) - before == 1, "首次 sweep 应恰好通知一次"

    notify_rule_changes.run()
    after_second = _sink_messages_for(place.canonical_name)
    assert len(after_second) == len(after_first), (
        f"retry sweep 重复通知了同一订阅：{[m.get('sent_at') for m in after_second]}"
    )


def test_the_watermark_is_not_taken_from_the_worker_clock(watched_venue, monkeypatch):
    """Process-clock skew must not make the sweep re-notify.

    The process clock is moved an hour into the past. If the watermark were
    written from it, ``updated_at`` (database clock) would still look newer than
    the watermark and the retry would duplicate — the production symptom.
    """
    from app.worker import tasks as tasks_module

    class SkewedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001
            return datetime.now(tz) - timedelta(hours=1)

    monkeypatch.setattr(tasks_module, "datetime", SkewedDatetime)

    place, _, _ = watched_venue
    before = len(_sink_messages_for(place.canonical_name))

    tasks_module.notify_rule_changes.run()
    first = _sink_messages_for(place.canonical_name)
    assert len(first) - before == 1

    tasks_module.notify_rule_changes.run()
    second = _sink_messages_for(place.canonical_name)
    assert len(second) == len(first), (
        "进程时钟比数据库慢 1 小时时重复通知 —— 水位线与比较对象不在同一时钟域："
        f"{[m.get('sent_at') for m in second]}"
    )
