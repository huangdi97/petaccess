"""Idempotency-key behaviour (§17).

The key contract is that a replayed high-risk write produces one of
``created / already_exists / ignored / conflict`` — never a duplicate row. The
Redis-backed cache is best-effort by design (a Redis outage must not block a
publish, and must not be mistaken for "no key seen before"), so this test pins
the *deterministic* half of the contract: key derivation and the empty-key
short-circuit.
"""

from __future__ import annotations

from app.core import idempotency


def test_the_same_key_always_derives_the_same_cache_key():
    assert idempotency._key("publish", "abc-123") == idempotency._key("publish", "abc-123")


def test_different_scopes_do_not_collide():
    """A publish key must never replay as, say, a withdrawal key."""
    assert idempotency._key("publish", "k") != idempotency._key("withdraw", "k")


def test_different_keys_do_not_collide_within_a_scope():
    assert idempotency._key("publish", "a") != idempotency._key("publish", "b")


def test_an_empty_key_is_not_a_key():
    """No idempotency key means no idempotency — never a shared default bucket."""
    assert idempotency.get_cached("publish", "") is None
    idempotency.store("publish", "", {"ok": True})  # must not raise
    assert idempotency.get_cached("publish", "") is None


def test_a_redis_outage_does_not_raise_into_the_request_path():
    """Best-effort cache: unreachable Redis degrades to 'no cached response'."""
    try:
        idempotency.store("publish", "outage-key", {"ok": True})
        idempotency.get_cached("publish", "outage-key")
    except Exception as exc:  # noqa: BLE001 - the point is that nothing escapes
        raise AssertionError(f"redis failure leaked to the caller: {exc!r}") from exc


def test_inflight_reservation_never_raises_when_redis_is_down():
    try:
        idempotency.check_inflight("publish", "outage-inflight")
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"redis failure leaked to the caller: {exc!r}") from exc
