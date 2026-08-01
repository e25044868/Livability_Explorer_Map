from app.domain.models import LocationAccuracy, PlaceCategory
from app.importers.toilet import normalize_toilet_rows


def test_toilet_normalizer_keeps_valid_coordinates_and_accessibility() -> None:
    places = normalize_toilet_rows(
        [
            {
                "Seq": "1",
                "name": "公園無障礙廁所",
                "address": "高雄市",
                "Lat": "22.63",
                "Lng": "120.3",
            }
        ]
    )
    assert places[0].category is PlaceCategory.TOILET
    assert places[0].location_accuracy is LocationAccuracy.EXACT_COORDINATE
    assert places[0].properties["accessible"] is True
