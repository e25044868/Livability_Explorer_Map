from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable, Mapping

from app.domain.models import PlaceCategory, PlaceDraft
from app.services.coordinates import validate_wgs84

SOURCE_DATASET = "高雄市公有路外停車場一覽表"
SOURCE_AGENCY = "高雄市政府交通局"


def _clean(value: object) -> str | None:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    return None if text in {"", "-"} else text


def _integer_or_none(value: object) -> int | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


def _zone_label(address: str | None) -> str | None:
    if not address:
        return None
    match = re.match(r"^([A-Za-zＡ-Ｚａ-ｚ])區\s*[：:]", address)
    return unicodedata.normalize("NFKC", match.group(1)).upper() if match else None


def _stable_id(*parts: str | None) -> str:
    source = "|".join(part or "" for part in parts)
    return "kcg-parking-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]


def normalize_parking_rows(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    """正規化官方停車資料，將 `-` 場名視為上一場站的後續分區。"""
    output: list[PlaceDraft] = []
    parent_name: str | None = None
    parent_district: str | None = None
    parent_metadata: dict[str, object] = {}

    for row_number, row in enumerate(rows, start=1):
        explicit_name = _clean(row.get("場名"))
        if explicit_name:
            parent_name = explicit_name
            parent_district = _clean(row.get("行政區"))
            parent_metadata = {
                "facility_type": _clean(row.get("型式")),
                "fee_description": _clean(row.get("收費標準")),
                "large_vehicle_spaces": _integer_or_none(row.get("大車")),
                "car_spaces": _integer_or_none(row.get("小車")),
                "motorcycle_spaces": _integer_or_none(row.get("機車")),
                "operator": _clean(row.get("管理業者")),
                "contract_period_raw": _clean(row.get("履約起迄")),
            }
        if parent_name is None:
            raise ValueError(f"第 {row_number} 筆在任何有效場名前使用延續符號")

        address = _clean(row.get("位置"))
        zone = _zone_label(address)
        display_name = f"{parent_name} {zone}區" if zone else parent_name
        coordinate = validate_wgs84(row.get("緯度"), row.get("經度"))
        properties = dict(parent_metadata)
        properties.update(
            {
                "parent_name": parent_name,
                "zone_label": zone,
                "source_row_number": row_number,
                "coordinate_error": coordinate.error,
            }
        )
        phone = _clean(row.get("聯絡電話"))
        external_id = _stable_id(
            parent_name,
            zone,
            address,
            str(coordinate.latitude),
            str(coordinate.longitude),
        )
        output.append(
            PlaceDraft(
                external_id=external_id,
                name=display_name,
                category=PlaceCategory.PARKING,
                subcategory=properties.get("facility_type"),  # type: ignore[arg-type]
                address=address,
                city="高雄市",
                district=parent_district,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                phone=phone,
                properties=properties,
                source_dataset=SOURCE_DATASET,
                source_agency=SOURCE_AGENCY,
                canonical_group_key=_stable_id(parent_name, parent_district),
            )
        )
    return output
