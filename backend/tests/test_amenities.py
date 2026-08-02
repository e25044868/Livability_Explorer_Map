from app.importers.amenities import normalize_drinking_water, normalize_shelters
from app.importers.national import normalize_national_aed


def test_drinking_water_filters_rows_without_dispenser() -> None:
    rows = [
        {
            "recordid": "1",
            "placename": "有水",
            "waterdispenser": "1",
            "latitude": "25",
            "longitude": "121",
            "city": "臺北市",
        },
        {
            "recordid": "2",
            "placename": "無水",
            "waterdispenser": "0",
            "latitude": "25",
            "longitude": "121",
        },
    ]
    places = normalize_drinking_water(rows)
    assert len(places) == 1
    assert places[0].category.value == "drinking_water"


def test_shelter_normalizes_city_and_capacity() -> None:
    places = normalize_shelters(
        [
            {
                "序號": "1",
                "縣市及鄉鎮市區": "高雄市苓雅區",
                "避難收容處所名稱": "活動中心",
                "經度": "120.31",
                "緯度": "22.62",
                "預計收容人數": "120",
                "室內": "是",
            }
        ]
    )
    assert places[0].city == "高雄市"
    assert places[0].district == "苓雅區"
    assert places[0].properties["capacity"] == 120


def test_shelter_uses_verified_coordinate_for_pingtung_school() -> None:
    places = normalize_shelters(
        [
            {
                "序號": "1",
                "縣市及鄉鎮市區": "屏東縣屏東市",
                "避難收容處所名稱": "國立屏東高級工業職業學校",
                "避難收容處所地址": "建國路25號",
                "緯度": "22.3948",
                "經度": "120.2912",
            }
        ]
    )

    place = places[0]
    assert place.latitude == 22.662873975834
    assert place.longitude == 120.48644449124
    assert place.properties["coordinate_correction"] == "verified_co_located_official_aed"


def test_shelter_keeps_known_pingtung_sea_coordinate_off_map() -> None:
    places = normalize_shelters(
        [
            {
                "序號": "1",
                "縣市及鄉鎮市區": "屏東縣屏東市",
                "避難收容處所名稱": "屏東市復興公園",
                "避難收容處所地址": "建興南路35號",
                "緯度": "22.3931",
                "經度": "120.2857",
            }
        ]
    )

    place = places[0]
    assert place.latitude is None
    assert place.longitude is None
    assert place.location_accuracy.value == "invalid"


def test_aed_keeps_known_address_coordinate_conflict_off_map() -> None:
    places = normalize_national_aed(
        [
            {
                "AEDID": "1",
                "場所名稱": "佳平村活動廣場",
                "場所地址": "屏東縣泰武鄉佳平村1鄰3號",
                "場所縣市": "屏東縣",
                "地點LAT": "23.449832",
                "地點LNG": "120.480566",
            }
        ]
    )

    place = places[0]
    assert place.latitude is None
    assert place.longitude is None
    assert place.location_accuracy.value == "invalid"
