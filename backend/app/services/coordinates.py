from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

from app.domain.models import LocationAccuracy

TAIWAN_LATITUDE_RANGE = (21.5, 25.5)
TAIWAN_LONGITUDE_RANGE = (119.0, 122.5)
EARTH_RADIUS_METERS = 6_371_000


@dataclass(frozen=True, slots=True)
class CoordinateResult:
    latitude: float | None
    longitude: float | None
    accuracy: LocationAccuracy
    error: str | None = None


def validate_wgs84(latitude: object, longitude: object) -> CoordinateResult:
    try:
        lat = float(str(latitude).strip())
        lng = float(str(longitude).strip())
    except (TypeError, ValueError):
        return CoordinateResult(None, None, LocationAccuracy.INVALID, "coordinate_not_numeric")

    if lat == 0 or lng == 0:
        return CoordinateResult(None, None, LocationAccuracy.INVALID, "coordinate_zero")
    if not TAIWAN_LATITUDE_RANGE[0] <= lat <= TAIWAN_LATITUDE_RANGE[1]:
        return CoordinateResult(None, None, LocationAccuracy.INVALID, "latitude_out_of_range")
    if not TAIWAN_LONGITUDE_RANGE[0] <= lng <= TAIWAN_LONGITUDE_RANGE[1]:
        return CoordinateResult(None, None, LocationAccuracy.INVALID, "longitude_out_of_range")
    return CoordinateResult(lat, lng, LocationAccuracy.EXACT_COORDINATE)


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    lat1_r, lng1_r, lat2_r, lng2_r = map(radians, (lat1, lng1, lat2, lng2))
    dlat = lat2_r - lat1_r
    dlng = lng2_r - lng1_r
    value = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(value))
