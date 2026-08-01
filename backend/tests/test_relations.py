from app.domain.models import (
    EvidenceMethod,
    LocationAccuracy,
    PlaceCategory,
    PlaceDraft,
    RelationType,
)
from app.services.relations import relate_charging_to_parking


def place(
    external_id: str,
    category: PlaceCategory,
    address: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> PlaceDraft:
    return PlaceDraft(
        external_id=external_id,
        name=external_id,
        category=category,
        address=address,
        city="高雄市",
        district="新興區",
        latitude=latitude,
        longitude=longitude,
        location_accuracy=(
            LocationAccuracy.EXACT_COORDINATE
            if latitude is not None
            else LocationAccuracy.ADDRESS_GEOCODED
        ),
        source_dataset="test",
        source_agency="test",
    )


def test_same_address_relation_is_not_labeled_as_source_explicit() -> None:
    parking = place("parking-1", PlaceCategory.PARKING, "高雄市新興區中正三路 34 號")
    charging = place("charging-1", PlaceCategory.MOTORCYCLE_CHARGING, "高雄市新興區中正三路34號")
    relation = relate_charging_to_parking(parking, charging)

    assert relation is not None
    assert relation.relation_type is RelationType.SAME_ADDRESS
    assert relation.evidence_method is EvidenceMethod.ADDRESS_MATCH
    assert relation.evidence["public_label"] == "同址有機車充電站"


def test_nearby_relation_exposes_distance_and_lower_confidence() -> None:
    parking = place("parking-1", PlaceCategory.PARKING, "地址 A", 22.62467, 120.28675)
    charging = place("charging-1", PlaceCategory.MOTORCYCLE_CHARGING, "地址 B", 22.62467, 120.28705)
    relation = relate_charging_to_parking(parking, charging)

    assert relation is not None
    assert relation.relation_type is RelationType.NEARBY
    assert relation.confidence == 0.7
    assert relation.distance_meters is not None
    assert relation.distance_meters < 50


def test_far_away_places_do_not_get_relation() -> None:
    parking = place("parking-1", PlaceCategory.PARKING, "地址 A", 22.62, 120.28)
    charging = place("charging-1", PlaceCategory.MOTORCYCLE_CHARGING, "地址 B", 22.65, 120.31)
    assert relate_charging_to_parking(parking, charging) is None
