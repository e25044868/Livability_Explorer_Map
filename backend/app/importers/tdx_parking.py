from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping

from app.domain.models import PlaceCategory, PlaceDraft
from app.services.coordinates import validate_wgs84


def normalize_tdx_parking_rows(
    rows: Iterable[Mapping[str, object]], city_name: str
) -> list[PlaceDraft]:
    output: list[PlaceDraft] = []
    for row in rows:
        position = row.get("CarParkPosition")
        position_map = position if isinstance(position, Mapping) else {}
        coordinate = validate_wgs84(
            position_map.get("PositionLat"), position_map.get("PositionLon")
        )
        multilingual_name = row.get("CarParkName")
        name_map = multilingual_name if isinstance(multilingual_name, Mapping) else {}
        name = str(name_map.get("Zh_tw") or row.get("CarParkID") or "未命名停車場")
        external_id = str(row.get("CarParkID") or hashlib.sha256(name.encode()).hexdigest()[:20])
        address = str(row.get("Address") or "").strip() or None
        output.append(
            PlaceDraft(
                external_id=f"tdx-{external_id}",
                name=name,
                category=PlaceCategory.PARKING,
                subcategory=str(row.get("CarParkType") or "").strip() or None,
                address=address,
                city=city_name,
                district=None,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                phone=str(row.get("Telephone") or "").strip() or None,
                source_dataset="TDX 指定縣市停車場基本資料",
                source_agency="交通部 TDX",
                properties={
                    "car_spaces": row.get("TotalSpaces"),
                    "total_spaces": row.get("TotalSpaces"),
                    "motorcycle_spaces": row.get("MotorcycleSpaces"),
                    "fee_description": row.get("FareDescription"),
                    "operator": row.get("OperatorName"),
                    "operation_time": row.get("OperationTime"),
                    "available_spaces": row.get("AvailableSpaces"),
                    "service_status": row.get("ServiceStatus"),
                    "live_updated_at": row.get("UpdateTime"),
                    "ev_spaces": row.get("EVSpaces") or row.get("ChargingSpaces"),
                    "accessible_spaces": row.get("HandicapSpaces"),
                    "parent_child_spaces": row.get("ParentChildSpaces")
                    or row.get("WomenAndChildrenSpaces"),
                    "height_limit": row.get("HeightRestriction"),
                    "monthly_pass": row.get("MonthlyTicket") or row.get("SeasonTicket"),
                },
            )
        )
    return output
