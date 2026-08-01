from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RelationEvidenceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relation_type: Literal["part_of", "same_address", "nearby", "possible_same_entity"]
    evidence_method: Literal[
        "source_explicit", "address_match", "spatial_distance", "manual_verified"
    ]
    label: str
    confidence: float = Field(ge=0, le=1)
    distance_meters: float | None = Field(default=None, ge=0)


class PlaceSummaryResponse(BaseModel):
    """公開設施摘要；刻意不含資料庫 id、raw_data 與內部來源 URL。"""

    model_config = ConfigDict(extra="forbid")

    public_id: str
    name: str
    category: str
    subcategory: str | None = None
    address: str | None = None
    phone: str | None = None
    city: str | None = None
    district: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    distance_meters: float | None = Field(default=None, ge=0)
    location_accuracy: str
    properties: dict[str, Any] = Field(default_factory=dict)
    nearby_features: list[RelationEvidenceResponse] = Field(default_factory=list)


class PlaceListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PlaceSummaryResponse]
    count: int = Field(ge=0)
    limit: int = Field(ge=1, le=500)
    data_version: str


class CategoryResponse(BaseModel):
    key: str
    label: str


class NearbySummaryResponse(BaseModel):
    radius_meters: int = Field(gt=0, le=3000)
    summary: dict[str, int]
    data_version: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str | None = None


class AdministrativeAreaResponse(BaseModel):
    city: str
    district: str | None = None


class GeocodeResultResponse(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    city: str | None = None
    district: str | None = None
