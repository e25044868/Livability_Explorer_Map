from app.domain.models import PlaceCategory
from app.importers.tdx_parking import normalize_tdx_parking_rows


def test_tdx_parking_normalizer_uses_shared_place_model() -> None:
    places = normalize_tdx_parking_rows(
        [
            {
                "CarParkID": "TPE001",
                "CarParkName": {"Zh_tw": "測試停車場"},
                "Address": "臺北市中正區測試路1號",
                "CarParkPosition": {"PositionLat": 25.04, "PositionLon": 121.51},
                "TotalSpaces": 50,
            }
        ],
        "臺北市",
    )
    assert places[0].category is PlaceCategory.PARKING
    assert places[0].city == "臺北市"
    assert places[0].properties["car_spaces"] == 50
