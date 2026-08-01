import pytest
from app.api.schemas import PlaceSummaryResponse, RelationEvidenceResponse
from pydantic import ValidationError


def test_relation_schema_keeps_relation_and_evidence_separate() -> None:
    response = RelationEvidenceResponse(
        relation_type="nearby",
        evidence_method="spatial_distance",
        label="32 公尺內有機車充電站",
        confidence=0.7,
        distance_meters=32,
    )
    assert response.relation_type == "nearby"
    assert response.evidence_method == "spatial_distance"


def test_public_place_schema_rejects_internal_fields() -> None:
    with pytest.raises(ValidationError):
        PlaceSummaryResponse(
            public_id="public-1",
            name="測試停車場",
            category="parking",
            location_accuracy="exact_coordinate",
            database_id=123,
        )


def test_public_place_schema_accepts_query_distance() -> None:
    response = PlaceSummaryResponse(
        public_id="parking-1",
        name="測試停車場",
        category="parking",
        latitude=22.63,
        longitude=120.3,
        distance_meters=245.7,
        location_accuracy="exact_coordinate",
    )

    assert response.distance_meters == 245.7
