from app.api.v1.ai import (
    MapCoordinate,
    MapNormalizeIn,
    MapTranslateIn,
    normalize_map_coordinates,
    translate_map_coordinates,
)


def test_translate_map_coordinates_fails_open_to_wgs84_mock() -> None:
    body = MapTranslateIn(coordinates=[MapCoordinate(lat=31.23, lng=121.47)])
    result = translate_map_coordinates(body)
    assert result["provider"] == "mock"
    assert result["coordinate_system"] == "EPSG:4326"
    assert result["coordinates"] == [{"lat": 31.23, "lng": 121.47}]


def test_normalize_map_coordinates_is_identity_when_real_provider_is_disabled() -> None:
    body = MapNormalizeIn(coordinates=[MapCoordinate(lat=31.23, lng=121.47)])
    result = normalize_map_coordinates(body)
    assert result["provider"] == "mock"
    assert result["coordinate_system"] == "EPSG:4326"
    assert result["coordinates"] == [{"lat": 31.23, "lng": 121.47}]
