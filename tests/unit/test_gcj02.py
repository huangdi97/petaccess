"""Coordinate-system boundary tests for interactive real-map viewport queries."""

import pytest

from app.providers.gcj02 import gcj02_to_wgs84, wgs84_to_gcj02


def test_gcj02_round_trip_keeps_shanghai_query_center_stable() -> None:
    wgs_lat, wgs_lng = 31.2240, 121.4650
    render_lat, render_lng = wgs84_to_gcj02(wgs_lat, wgs_lng)
    restored_lat, restored_lng = gcj02_to_wgs84(render_lat, render_lng)

    assert restored_lat == pytest.approx(wgs_lat, abs=1e-6)
    assert restored_lng == pytest.approx(wgs_lng, abs=1e-6)
    assert abs(render_lng - wgs_lng) > 0.001


def test_gcj02_normalization_is_identity_outside_china() -> None:
    lat, lng = 37.7749, -122.4194
    assert gcj02_to_wgs84(lat, lng) == (lat, lng)
