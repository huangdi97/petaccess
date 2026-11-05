"""DEV fixture nearby results must honor the actual requested geography."""

from app.services.dev_fixture import fixture_nearby_summaries


def test_nearby_fixtures_match_shanghai_demo_center() -> None:
    nearby = fixture_nearby_summaries(31.23, 121.47, 5000)
    assert len(nearby) == 3
    assert all(item.latitude is not None and item.longitude is not None for item in nearby)
    distances = [item.distance_m for item in nearby]
    assert all(distance is not None for distance in distances)
    assert distances == sorted(distances)


def test_far_away_user_location_does_not_return_shanghai_demo_places() -> None:
    assert fixture_nearby_summaries(39.9042, 116.4074, 5000) == []
    assert fixture_nearby_summaries(40.7128, -74.0060, 50000) == []


def test_small_radius_returns_only_geographically_matching_fixture() -> None:
    nearby = fixture_nearby_summaries(31.2338, 121.4936, 250)
    assert len(nearby) == 1
    assert nearby[0].canonical_name.startswith("滨江公园")
    assert nearby[0].distance_m == 0
