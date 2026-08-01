from app.domain.models import LocationAccuracy
from app.services.coordinates import haversine_meters, validate_wgs84


def test_valid_kaohsiung_coordinate() -> None:
    result = validate_wgs84("22.62467082", "120.2867526")
    assert result.accuracy is LocationAccuracy.EXACT_COORDINATE
    assert result.latitude == 22.62467082


def test_empty_and_out_of_range_coordinates_are_invalid() -> None:
    assert validate_wgs84("", "").accuracy is LocationAccuracy.INVALID
    assert validate_wgs84("120.3", "22.6").accuracy is LocationAccuracy.INVALID
    assert validate_wgs84("0", "0").accuracy is LocationAccuracy.INVALID


def test_haversine_returns_reasonable_distance() -> None:
    distance = haversine_meters(22.62467, 120.28675, 22.62467, 120.28775)
    assert 90 < distance < 120
