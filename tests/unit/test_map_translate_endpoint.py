from app.api.v1.ai import MapCoordinate, MapTranslateIn, translate_map_coordinates


def test_translate_map_coordinates_fails_open_to_wgs84_mock() -> None:
    body = MapTranslateIn(coordinates=[MapCoordinate(lat=31.23, lng=121.47)])
    result = translate_map_coordinates(body)
    assert result["provider"] == "mock"
    assert result["coordinate_system"] == "EPSG:4326"
    assert result["coordinates"] == [{"lat": 31.23, "lng": 121.47}]
