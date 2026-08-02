from app.domain.models import LocationAccuracy, PlaceCategory
from app.importers.tdx_bike import normalize_tdx_bike_rows


def test_normalize_tdx_bike_rows_merges_live_availability() -> None:
    places = normalize_tdx_bike_rows(
        [
            {
                "StationUID": "KHH123",
                "StationName": {"Zh_tw": "中央公園站"},
                "StationAddress": {"Zh_tw": "高雄市前金區中山一路11號"},
                "BikesCapacity": 40,
                "ServiceType": 2,
                "StationPosition": {"PositionLat": 22.6273, "PositionLon": 120.3016},
            }
        ],
        {
            "KHH123": {
                "AvailableRentBikes": 12,
                "AvailableReturnBikes": 28,
                "ServiceStatus": 1,
                "UpdateTime": "2026-08-02T12:00:00+08:00",
            }
        },
        "高雄市",
    )

    assert len(places) == 1
    assert places[0].category is PlaceCategory.PUBLIC_BICYCLE
    assert places[0].location_accuracy is LocationAccuracy.EXACT_COORDINATE
    assert places[0].properties["available_rent_bikes"] == 12
    assert places[0].properties["available_return_bikes"] == 28
    assert places[0].properties["station_capacity"] == 40
