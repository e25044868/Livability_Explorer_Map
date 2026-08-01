import pytest
from app.domain.models import LocationAccuracy, PlaceCategory
from app.importers.parking import normalize_parking_rows


def test_continuation_row_inherits_parent_without_inventing_zero_values() -> None:
    rows = [
        {
            "型式": "平面",
            "行政區": "甲仙區",
            "場名": "甲仙林森",
            "位置": "A區：林森路70號旁",
            "緯度": "23.082862",
            "經度": "120.587988",
            "收費標準": "小車計次(30元/6小時)",
            "大車": "0",
            "小車": "35",
            "機車": "0",
            "管理業者": "測試業者",
            "聯絡電話": "071234567",
            "履約起迄": "113/04/01～119/03/31",
        },
        {
            "型式": "-",
            "行政區": "-",
            "場名": "-",
            "位置": "B區：林森路75號旁",
            "緯度": "23.082262",
            "經度": "120.587394",
            "收費標準": "-",
            "大車": "-",
            "小車": "-",
            "機車": "-",
            "管理業者": "-",
            "聯絡電話": "-",
            "履約起迄": "-",
        },
    ]

    places = normalize_parking_rows(rows)

    assert [place.name for place in places] == ["甲仙林森 A區", "甲仙林森 B區"]
    assert all(place.category is PlaceCategory.PARKING for place in places)
    assert places[1].district == "甲仙區"
    assert places[1].properties["car_spaces"] == 35
    assert places[1].properties["zone_label"] == "B"
    assert places[1].canonical_group_key == places[0].canonical_group_key
    assert places[1].location_accuracy is LocationAccuracy.EXACT_COORDINATE


def test_continuation_before_parent_is_rejected() -> None:
    with pytest.raises(ValueError, match="延續符號"):
        normalize_parking_rows(
            [{"場名": "-", "位置": "B區：某路", "緯度": "22.6", "經度": "120.3"}]
        )
