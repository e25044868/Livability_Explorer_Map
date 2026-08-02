from app.domain.models import LocationAccuracy, PlaceCategory
from app.importers.public_services import (
    normalize_libraries,
    normalize_police,
    normalize_public_wifi,
    normalize_rescue_units,
)


def test_normalize_libraries_flattens_city_groups_and_keeps_coordinates() -> None:
    places = normalize_libraries([{
        "縣市": "屏東縣",
        "圖書館資訊": [{
            "Name": "屏東市立圖書館", "Area": "屏東市", "Address": "屏東縣屏東市公園路1號",
            "TEL": "08-1234567", "Longitude": 120.4908, "Latitude": 22.6765, "URL": "https://example.test/library",
        }],
    }])
    assert len(places) == 1
    assert places[0].category.value == "library"
    assert places[0].city == "屏東縣"
    assert places[0].district == "屏東市"
    assert places[0].latitude == 22.6765
    assert places[0].properties["website"] == "https://example.test/library"


def test_normalize_public_wifi_keeps_verified_coordinates_and_agency() -> None:
    places = normalize_public_wifi([
        {
            "Name": "市政大樓 Wi-Fi",
            "Address": "802高雄市苓雅區四維三路2號",
            "Area": "政府機關",
            "Agency": "高雄市政府",
            "Latitude": "22.6269",
            "Longitude": "120.2944",
        }
    ])
    assert places[0].category is PlaceCategory.PUBLIC_WIFI
    assert places[0].city == "高雄市"
    assert places[0].district == "苓雅區"
    assert places[0].properties["agency"] == "高雄市政府"
    assert places[0].location_accuracy is LocationAccuracy.EXACT_COORDINATE


def test_normalize_rescue_unit_uses_published_longitude_latitude_values() -> None:
    places = normalize_rescue_units([
        {
            "消防隊名稱": "屏東分隊",
            "地址": "900屏東縣屏東市中正路375號",
            "聯絡電話": "08-7364224",
            "X座標_TWD97TM121": "120.4890",
            "Y座標_TWD97TM121": "22.6760",
            "是否與消防隊同址": "是",
        }
    ])
    assert places[0].category is PlaceCategory.RESCUE_UNIT
    assert places[0].latitude == 22.676
    assert places[0].longitude == 120.489
    assert places[0].properties["co_located_with_fire_station"] is True


def test_normalize_police_converts_tm2_coordinates_to_wgs84() -> None:
    places = normalize_police([
        {
            "中文單位名稱": "高雄市政府警察局新興分局中正三路派出所",
            "英文單位名稱": "Zhongzheng 3rd Road Police Station",
            "地址": "800高雄市新興區中正三路25號",
            "電話": "07-2363171",
            "POINT_X": "177129",
            "POINT_Y": "2501648",
        }
    ])
    assert places[0].category is PlaceCategory.POLICE
    assert places[0].location_accuracy is LocationAccuracy.CONVERTED_COORDINATE
    assert 22 < (places[0].latitude or 0) < 23
    assert 120 < (places[0].longitude or 0) < 121
    assert places[0].properties["unit_type"] == "派出所"
