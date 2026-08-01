from __future__ import annotations

import re
import unicodedata

from app.domain.models import (
    EvidenceMethod,
    PlaceDraft,
    PlaceRelationDraft,
    RelationType,
)
from app.services.coordinates import haversine_meters


def normalize_address(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[\s,，。()（）-]", "", normalized)
    normalized = normalized.replace("臺", "台")
    return normalized


def relate_charging_to_parking(
    parking: PlaceDraft,
    charging: PlaceDraft,
    *,
    nearby_threshold_meters: float = 50,
) -> PlaceRelationDraft | None:
    """建立可解釋的充電關聯，不把鄰近推定冒充場內官方設施。"""
    parking_address = normalize_address(parking.address)
    charging_address = normalize_address(charging.address)
    if parking_address and parking_address == charging_address:
        return PlaceRelationDraft(
            from_external_id=parking.external_id,
            to_external_id=charging.external_id,
            relation_type=RelationType.SAME_ADDRESS,
            evidence_method=EvidenceMethod.ADDRESS_MATCH,
            confidence=0.9,
            evidence={"public_label": "同址有機車充電站"},
        )

    if None not in (
        parking.latitude,
        parking.longitude,
        charging.latitude,
        charging.longitude,
    ):
        distance = haversine_meters(
            parking.latitude,  # type: ignore[arg-type]
            parking.longitude,  # type: ignore[arg-type]
            charging.latitude,  # type: ignore[arg-type]
            charging.longitude,  # type: ignore[arg-type]
        )
        if distance <= nearby_threshold_meters:
            return PlaceRelationDraft(
                from_external_id=parking.external_id,
                to_external_id=charging.external_id,
                relation_type=RelationType.NEARBY,
                evidence_method=EvidenceMethod.SPATIAL_DISTANCE,
                confidence=0.7,
                distance_meters=round(distance, 1),
                evidence={"public_label": f"{round(distance):.0f} 公尺內有機車充電站"},
            )
    return None
