"""Minimal GCJ-02 -> WGS84 normalization for map viewport queries.

Persisted PetAccess geometry is EPSG:4326/WGS84. Tencent GL renders GCJ-02.
This module is used only to normalize an interactive render-center back into
the governed query coordinate system; provider coordinates are never persisted.
"""

from __future__ import annotations

import math

_A = 6378245.0
_EE = 0.00669342162296594323
_PI = math.pi


def _outside_china(lat: float, lng: float) -> bool:
    return lng < 72.004 or lng > 137.8347 or lat < 0.8293 or lat > 55.8271


def _transform_lat(x: float, y: float) -> float:
    value = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y
    value += 0.2 * math.sqrt(abs(x))
    value += (20.0 * math.sin(6.0 * x * _PI) + 20.0 * math.sin(2.0 * x * _PI)) * 2 / 3
    value += (20.0 * math.sin(y * _PI) + 40.0 * math.sin(y / 3 * _PI)) * 2 / 3
    value += (160.0 * math.sin(y / 12 * _PI) + 320 * math.sin(y * _PI / 30)) * 2 / 3
    return value


def _transform_lng(x: float, y: float) -> float:
    value = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y
    value += 0.1 * math.sqrt(abs(x))
    value += (20.0 * math.sin(6.0 * x * _PI) + 20.0 * math.sin(2.0 * x * _PI)) * 2 / 3
    value += (20.0 * math.sin(x * _PI) + 40.0 * math.sin(x / 3 * _PI)) * 2 / 3
    value += (150.0 * math.sin(x / 12 * _PI) + 300.0 * math.sin(x / 30 * _PI)) * 2 / 3
    return value


def wgs84_to_gcj02(lat: float, lng: float) -> tuple[float, float]:
    """Pure forward transform used only to solve the inverse numerically."""

    if _outside_china(lat, lng):
        return lat, lng
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * _PI
    magic = math.sin(radlat)
    magic = 1 - _EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((_A * (1 - _EE)) / (magic * sqrt_magic) * _PI)
    dlng = (dlng * 180.0) / (_A / sqrt_magic * math.cos(radlat) * _PI)
    return lat + dlat, lng + dlng


def gcj02_to_wgs84(lat: float, lng: float) -> tuple[float, float]:
    """Iteratively invert GCJ-02 with sub-meter coordinate tolerance."""

    if _outside_china(lat, lng):
        return lat, lng
    guess_lat, guess_lng = lat, lng
    for _ in range(8):
        rendered_lat, rendered_lng = wgs84_to_gcj02(guess_lat, guess_lng)
        error_lat = rendered_lat - lat
        error_lng = rendered_lng - lng
        guess_lat -= error_lat
        guess_lng -= error_lng
        if abs(error_lat) < 1e-7 and abs(error_lng) < 1e-7:
            break
    return guess_lat, guess_lng
