"""Pure helpers behind the admin data-quality KPIs (design #37, P4).

Deliberately *no composite quality score*. The product's red line is that a place
is never reduced to a single number, and the same discipline is applied to its
own operations: the dashboard exposes raw, individually explainable ratios
(rule coverage, source coverage, hash coverage) instead of a blended index that
nobody can decompose when it drops.

Everything here is a pure function so it can be unit-tested without a database,
which matters because the SQL that feeds it cannot run in the current
environment.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

__all__ = ["age_days", "distribution", "is_overdue", "median_age_days", "ratio"]


def ratio(part: int, whole: int) -> float:
    """Share of ``part`` in ``whole``, rounded to 3 dp.

    Returns ``0.0`` for an empty denominator rather than raising or emitting
    ``NaN``: an empty table is "nothing to report", not a 0/0 error, and a NaN
    would silently propagate into the JSON response.
    """
    if whole <= 0:
        return 0.0
    return round(part / whole, 3)


def age_days(value: datetime | None, now: datetime) -> int | None:
    """Whole days between ``value`` and ``now``; ``None`` when unknown.

    A future timestamp yields a negative number rather than being clamped:
    a rule recorded in the future is a real data defect and hiding it behind a
    clamp would make it invisible.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return int((now - value).total_seconds() // 86400)


def median_age_days(values: Iterable[datetime | None], now: datetime) -> int | None:
    """Median age in days, ignoring unknown timestamps.

    Computed in Python rather than with ``percentile_cont`` so the KPI is
    portable and unit-testable; the rule table is small enough that fetching one
    column is cheaper than the risk of a provider-specific SQL expression that
    cannot be exercised in this environment.
    """
    ages = sorted(a for a in (age_days(v, now) for v in values) if a is not None)
    if not ages:
        return None
    mid = len(ages) // 2
    if len(ages) % 2 == 1:
        return ages[mid]
    return (ages[mid - 1] + ages[mid]) // 2


def distribution(keys: Sequence[str], rows: Iterable[str | None]) -> dict[str, int]:
    """Count ``rows`` into ``keys``, folding anything unrecognised into ``other``.

    Every declared key is always present with an explicit 0 so the dashboard can
    render a stable shape instead of guessing which buckets exist today.
    """
    out: dict[str, int] = dict.fromkeys(keys, 0)
    out["other"] = 0
    known = set(keys)
    for row in rows:
        if row in known:
            out[row] += 1
        else:
            out["other"] += 1
    return out


def is_overdue(review_due_at: datetime | None, status: str | None, now: datetime) -> bool:
    """A *current* rule past its review date needs re-verification.

    Superseded/retired rules are excluded: they are already out of force, so
    flagging them as overdue would inflate the freshness backlog with rows
    nobody has to act on.
    """
    if review_due_at is None or status != "current":
        return False
    if review_due_at.tzinfo is None:
        review_due_at = review_due_at.replace(tzinfo=UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return review_due_at < now
