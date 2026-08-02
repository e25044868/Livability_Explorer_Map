from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping

from app.domain.models import PlaceCategory, PlaceDraft
from app.services.coordinates import validate_wgs84


def _text(value: object) -> str | None:
    value = str(value or "").strip()
    return value or None


def _localized_text(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("Zh_tw")) or _text(value.get("En"))
    return _text(value)


def normalize_tdx_bike_rows(
    stations: Iterable[Mapping[str, object]], availability_by_id: Mapping[str, Mapping[str, object]], city_name: str
) -> list[PlaceDraft]:
    places: list[PlaceDraft] = []
    for row in stations:
        station_id = _text(row.get("StationUID")) or hashlib.sha256(repr(row).encode()).hexdigest()[:22]
        position = row.get("StationPosition")
        position_map = position if isinstance(position, Mapping) else {}
        coordinate = validate_wgs84(position_map.get("PositionLat"), position_map.get("PositionLon"))
        name = _localized_text(row.get("StationName")) or station_id
        live = availability_by_id.get(station_id, {})
        places.append(
            PlaceDraft(
                external_id=f"tdx-bike-{station_id}",
                name=name,
                category=PlaceCategory.PUBLIC_BICYCLE,
                subcategory=_text(row.get("ServiceType")),
                address=_localized_text(row.get("StationAddress")),
                city=city_name,
                district=None,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                source_dataset="TDX 公共自行車站點與即時車位資料",
                source_agency="交通部 TDX",
                properties={
                    "station_capacity": row.get("BikesCapacity"),
                    "available_rent_bikes": live.get("AvailableRentBikes"),
                    "available_return_bikes": live.get("AvailableReturnBikes"),
                    "service_status": live.get("ServiceStatus"),
                    "live_updated_at": live.get("UpdateTime"),
                    "bike_sharing_type": row.get("ServiceType"),
                },
            )
        )
    return places
