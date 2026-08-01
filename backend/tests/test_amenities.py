from app.importers.amenities import normalize_drinking_water, normalize_shelters


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
