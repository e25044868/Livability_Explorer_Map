from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import LocationAccuracy, PlaceDraft
from app.sources.config import QualityGateConfig


@dataclass(frozen=True, slots=True)
class QualityReport:
    accepted: bool
    record_count: int
    invalid_coordinate_count: int
    invalid_coordinate_ratio: float
    previous_record_count: int | None
    record_count_change_ratio: float | None
    failures: tuple[str, ...]


def evaluate_quality(
    places: list[PlaceDraft],
    gates: QualityGateConfig,
    *,
    previous_record_count: int | None = None,
) -> QualityReport:
    count = len(places)
    invalid = sum(place.location_accuracy is LocationAccuracy.INVALID for place in places)
    invalid_ratio = invalid / count if count else 1.0
    change_ratio: float | None = None
    failures: list[str] = []
    if count < gates.minimum_records:
        failures.append("record_count_below_minimum")
    if invalid_ratio > gates.maximum_invalid_coordinate_ratio:
        failures.append("invalid_coordinate_ratio_exceeded")
    if previous_record_count and previous_record_count > 0:
        change_ratio = abs(count - previous_record_count) / previous_record_count
        if change_ratio > gates.maximum_record_count_change_ratio:
            failures.append("record_count_change_ratio_exceeded")
    return QualityReport(
        accepted=not failures,
        record_count=count,
        invalid_coordinate_count=invalid,
        invalid_coordinate_ratio=invalid_ratio,
        previous_record_count=previous_record_count,
        record_count_change_ratio=change_ratio,
        failures=tuple(failures),
    )
