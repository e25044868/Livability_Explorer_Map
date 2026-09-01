from app.domain.models import LocationAccuracy, PlaceCategory
from app.importers.public_services import normalize_tourism_facilities


def test_normalize_tourism_facilities_keeps_selected_verified_public_facilities() -> None:
    places = normalize_tourism_facilities(
        [
            {
                "設施編號": "A-1",
                "設施大類": "基本公共服務設施",
                "設施小類": "哺集乳室",
                "設施名稱": "海岸遊客中心哺集乳室",
                "據點位置": "屏東縣恆春鎮墾丁路1號",
                "管理者聯絡地址": "屏東縣恆春鎮墾丁路2號",
                "管理者連絡電話": "08-0000000",
                "設施坐標X": "120.799",
                "設施坐標Y": "21.945",
                "設施狀態": "正常",
                "管理處": "墾丁國家公園管理處",
                "設施說明": "室內哺乳空間",
                "景觀分區": "墾丁",
            },
            {
                "設施編號": "B-1",
                "設施大類": "工程設施",
                "設施小類": "護欄",
                "設施名稱": "不應上圖",
                "設施坐標X": "120.5",
                "設施坐標Y": "23.5",
            },
        ]
    )
    assert len(places) == 1
    place = places[0]
    assert place.category is PlaceCategory.TOURISM_FACILITY
    assert place.location_accuracy is LocationAccuracy.EXACT_COORDINATE
    assert place.city == "屏東縣"
    assert place.district == "恆春鎮"
    assert place.properties["parent_child"] is True


def test_normalize_tourism_facilities_does_not_show_manager_address_as_site_address() -> None:
    place = normalize_tourism_facilities(
        [
            {
                "設施編號": "C-1",
                "設施大類": "基本公共服務設施",
                "設施小類": "無障礙坡道",
                "設施名稱": "無障礙坡道",
                "據點位置": "",
                "管理者聯絡地址": "高雄市苓雅區四維三路2號",
                "設施坐標X": "120.301",
                "設施坐標Y": "22.627",
            }
        ]
    )[0]
    assert place.address is None
    assert place.city == "高雄市"
    assert place.district == "苓雅區"
    assert place.properties["manager_address"] == "高雄市苓雅區四維三路2號"
    assert place.properties["accessible"] is True
