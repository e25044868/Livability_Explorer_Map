from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping

from app.domain.models import PlaceCategory, PlaceDraft
from app.services.coordinates import validate_wgs84


def _text(value: object) -> str | None:
    value = str(value or "").strip()
    return value or None


def _id(prefix: str, *values: object) -> str:
    return prefix + hashlib.sha256("|".join(str(v or "") for v in values).encode()).hexdigest()[:22]


def _yes(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "是", "有"}


def normalize_drinking_water(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    output = []
    for row in rows:
        if not _yes(row.get("waterdispenser")):
            continue
        name = _text(row.get("placename")) or "公共飲水機"
        coordinate = validate_wgs84(row.get("latitude"), row.get("longitude"))
        output.append(
            PlaceDraft(
                external_id=_id("moenv-water-", row.get("recordid"), name),
                name=name,
                category=PlaceCategory.DRINKING_WATER,
                subcategory=_text(row.get("stationtype")),
                address=_text(row.get("address")),
                city=_text(row.get("city")),
                district=_text(row.get("district")),
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                phone=_text(row.get("phone")),
                source_dataset="Cool map 涼適點－飲水機",
                source_agency="環境部氣候變遷署",
                properties={
                    "opening_hours": _text(row.get("openinghours")),
                    "accessible": _yes(row.get("isaccessible")),
                    "indoor": not _yes(row.get("isoutdoor")),
                    "air_conditioning": _yes(row.get("airconditioning")),
                    "restroom": _yes(row.get("restroom")),
                    "seats": _yes(row.get("seats")),
                    "station_type": _text(row.get("stationtype")),
                },
            )
        )
    return output


def normalize_shelters(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    output = []
    for row in rows:
        area = _text(row.get("縣市及鄉鎮市區")) or ""
        city_match = re.match(r"^(.{2,3}[縣市])", area)
        city = city_match.group(1).replace("台", "臺") if city_match else None
        district = area[len(city_match.group(1)) :] or None if city_match else None
        name = _text(row.get("避難收容處所名稱")) or "避難收容處所"
        coordinate = validate_wgs84(row.get("緯度"), row.get("經度"))
        capacity_text = _text(row.get("預計收容人數"))
        try:
            capacity = int(float(capacity_text or 0))
        except ValueError:
            capacity = None
        output.append(
            PlaceDraft(
                external_id=_id("nfa-shelter-", row.get("序號"), name, area),
                name=name,
                category=PlaceCategory.SHELTER,
                subcategory="避難收容處所",
                address=_text(row.get("避難收容處所地址")),
                city=city,
                district=district,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                phone=_text(row.get("管理人電話")),
                source_dataset="避難收容處所點位檔",
                source_agency="內政部消防署",
                properties={
                    "capacity": capacity,
                    "disaster_types": _text(row.get("適用災害類別")),
                    "indoor": _yes(row.get("室內")),
                    "outdoor": _yes(row.get("室外")),
                    "vulnerable_friendly": _yes(row.get("適合避難弱者安置")),
                    "service_villages": _text(row.get("預計收容村里")),
                },
            )
        )
    return output
