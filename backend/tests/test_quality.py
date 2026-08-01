from app.domain.models import LocationAccuracy, PlaceCategory, PlaceDraft
from app.importers.quality import evaluate_quality
from app.sources.config import QualityGateConfig


def draft(index: int, accuracy: LocationAccuracy) -> PlaceDraft:
    return PlaceDraft(
        external_id=str(index),
        name=str(index),
        category=PlaceCategory.PARKING,
        address=None,
        city="高雄市",
        district=None,
        latitude=22.6 if accuracy is not LocationAccuracy.INVALID else None,
        longitude=120.3 if accuracy is not LocationAccuracy.INVALID else None,
        location_accuracy=accuracy,
        source_dataset="test",
        source_agency="test",
    )


def gates() -> QualityGateConfig:
    return QualityGateConfig(
        minimum_records=2,
        maximum_invalid_coordinate_ratio=0.2,
        maximum_record_count_change_ratio=0.3,
    )


def test_quality_gate_accepts_stable_valid_dataset() -> None:
    report = evaluate_quality(
        [draft(index, LocationAccuracy.EXACT_COORDINATE) for index in range(10)],
        gates(),
        previous_record_count=9,
    )
    assert report.accepted


def test_quality_gate_rejects_invalid_coordinates_and_count_drop() -> None:
    places = [draft(1, LocationAccuracy.EXACT_COORDINATE), draft(2, LocationAccuracy.INVALID)]
    report = evaluate_quality(places, gates(), previous_record_count=10)
    assert not report.accepted
    assert "invalid_coordinate_ratio_exceeded" in report.failures
    assert "record_count_change_ratio_exceeded" in report.failures
