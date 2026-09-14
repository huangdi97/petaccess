"""Data-quality KPI helpers (P4 "data quality metrics", design #37).

These guard the arithmetic that the admin dashboard shows, because the SQL that
feeds it cannot be executed in the current environment (no PostGIS). The pure
functions are therefore the only part of the KPI path that can actually be
verified here — so they are verified properly, including the edge cases that
would otherwise surface as a silent ``NaN`` or an inflated backlog.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.quality_metrics import (
    age_days,
    distribution,
    is_overdue,
    median_age_days,
    ratio,
)

NOW = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)


# ------------------------------------------------------------------ ratio


def test_ratio_is_a_plain_share_rounded_to_three_places():
    assert ratio(1, 2) == 0.5
    assert ratio(2, 3) == 0.667
    assert ratio(0, 5) == 0.0
    assert ratio(5, 5) == 1.0


def test_ratio_returns_zero_for_an_empty_denominator():
    """An empty table means "nothing to report", not a 0/0 error.

    Returning NaN here would serialise into the JSON response as a non-standard
    token and break the dashboard.
    """
    assert ratio(0, 0) == 0.0
    assert ratio(3, 0) == 0.0
    assert ratio(0, -1) == 0.0


# --------------------------------------------------------------- age_days


def test_age_days_counts_whole_days():
    assert age_days(NOW - timedelta(days=3), NOW) == 3
    assert age_days(NOW - timedelta(hours=23), NOW) == 0
    assert age_days(NOW, NOW) == 0


def test_age_days_is_none_when_the_timestamp_is_unknown():
    assert age_days(None, NOW) is None


def test_age_days_is_negative_for_a_future_timestamp():
    """A rule recorded in the future is a data defect and must stay visible."""
    assert age_days(NOW + timedelta(days=2), NOW) == -2


def test_age_days_treats_naive_timestamps_as_utc():
    naive = (NOW - timedelta(days=4)).replace(tzinfo=None)
    assert age_days(naive, NOW) == 4


# ------------------------------------------------------- median_age_days


def test_median_age_odd_count_picks_the_middle_value():
    values = [NOW - timedelta(days=d) for d in (1, 10, 3)]
    assert median_age_days(values, NOW) == 3


def test_median_age_even_count_averages_the_two_middle_values():
    values = [NOW - timedelta(days=d) for d in (1, 2, 10, 11)]
    assert median_age_days(values, NOW) == 6


def test_median_age_ignores_unknown_timestamps():
    values = [NOW - timedelta(days=4), None, NOW - timedelta(days=6)]
    assert median_age_days(values, NOW) == 5


def test_median_age_is_none_when_nothing_is_known():
    assert median_age_days([], NOW) is None
    assert median_age_days([None, None], NOW) is None


# ----------------------------------------------------------- distribution


def test_distribution_always_reports_every_declared_bucket():
    """The dashboard renders a stable shape; a missing bucket must read 0."""
    out = distribution(["A", "B"], ["A", "A"])
    assert out == {"A": 2, "B": 0, "other": 0}


def test_distribution_folds_unrecognised_values_into_other():
    out = distribution(["A"], ["A", "Z", None])
    assert out == {"A": 1, "other": 2}


def test_distribution_handles_an_empty_input():
    assert distribution(["A", "B"], []) == {"A": 0, "B": 0, "other": 0}


# -------------------------------------------------------------- is_overdue


def test_is_overdue_flags_only_current_rules_past_their_review_date():
    past = NOW - timedelta(days=1)
    future = NOW + timedelta(days=1)
    assert is_overdue(past, "current", NOW) is True
    assert is_overdue(future, "current", NOW) is False


@pytest.mark.parametrize("status", ["superseded", "retired", "draft"])
def test_is_overdue_ignores_rules_that_are_already_out_of_force(status: str):
    """Otherwise the freshness backlog counts work nobody has to do."""
    assert is_overdue(NOW - timedelta(days=30), status, NOW) is False


def test_is_overdue_is_false_without_a_due_date():
    assert is_overdue(None, "current", NOW) is False


def test_is_overdue_accepts_naive_due_dates():
    naive_past = (NOW - timedelta(days=1)).replace(tzinfo=None)
    assert is_overdue(naive_past, "current", NOW) is True
