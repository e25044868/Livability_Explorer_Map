from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PlaceCategory(StrEnum):
    PARKING = "parking"
    TOILET = "toilet"
    AED = "aed"
    PHARMACY = "pharmacy"
    MEDICAL = "medical"
    MOTORCYCLE_CHARGING = "motorcycle_charging"
    DRINKING_WATER = "drinking_water"
    SHELTER = "shelter"
    PUBLIC_WIFI = "public_wifi"
    RESCUE_UNIT = "rescue_unit"
    POLICE = "police"
    LIBRARY = "library"
    PUBLIC_BICYCLE = "public_bicycle"


class LocationAccuracy(StrEnum):
    EXACT_COORDINATE = "exact_coordinate"
    CONVERTED_COORDINATE = "converted_coordinate"
    ADDRESS_GEOCODED = "address_geocoded"
    DISTRICT_ONLY = "district_only"
    INVALID = "invalid"


class RelationType(StrEnum):
    PART_OF = "part_of"
    SAME_ADDRESS = "same_address"
    NEARBY = "nearby"
    POSSIBLE_SAME_ENTITY = "possible_same_entity"


class EvidenceMethod(StrEnum):
    SOURCE_EXPLICIT = "source_explicit"
    ADDRESS_MATCH = "address_match"
    SPATIAL_DISTANCE = "spatial_distance"
    MANUAL_VERIFIED = "manual_verified"


@dataclass(frozen=True, slots=True)
class PlaceDraft:
    external_id: str
    name: str
    category: PlaceCategory
    address: str | None
    city: str | None
    district: str | None
    latitude: float | None
    longitude: float | None
    location_accuracy: LocationAccuracy
    source_dataset: str
    source_agency: str
    phone: str | None = None
    subcategory: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    canonical_group_key: str | None = None


@dataclass(frozen=True, slots=True)
class PlaceRelationDraft:
    from_external_id: str
    to_external_id: str
    relation_type: RelationType
    evidence_method: EvidenceMethod
    confidence: float
    distance_meters: float | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence 必須介於 0 與 1")
        if self.distance_meters is not None and self.distance_meters < 0:
            raise ValueError("distance_meters 不得小於 0")
