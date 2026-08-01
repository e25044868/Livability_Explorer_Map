from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable, Mapping

from app.domain.models import PlaceCategory, PlaceDraft
from app.services.coordinates import validate_wgs84


def _clean(value: object) -> str | None:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    return text or None


def _stable_id(prefix: str, *parts: str | None) -> str:
    source = "|".join(part or "" for part in parts)
    return prefix + hashlib.sha256(source.encode("utf-8")).hexdigest()[:22]


def _city_district(
    address: str | None, explicit_city: str | None = None
) -> tuple[str | None, str | None]:
    city = _clean(explicit_city)
    if city and city == "台北市":
        city = "臺北市"
    if city and city == "台中市":
        city = "臺中市"
    if city and city == "台南市":
        city = "臺南市"
    if city and city == "台東縣":
        city = "臺東縣"
    normalized = _clean(address) or ""
    if city is None:
        match = re.match(r"^(臺?[^縣市]{1,3}[縣市])", normalized)
        city = match.group(1) if match else None
    district = None
    if city and normalized.startswith(city):
        remainder = normalized[len(city) :]
        match = re.match(r"^([^區鄉鎮市]{1,4}[區鄉鎮市])", remainder)
        district = match.group(1) if match else None
    return city, district


def normalize_national_toilets(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    output: list[PlaceDraft] = []
    for index, row in enumerate(rows, start=1):
        name = _clean(row.get("name")) or f"公共廁所 {index}"
        address = _clean(row.get("address"))
        city, district = _city_district(address)
        coordinate = validate_wgs84(row.get("latitude"), row.get("longitude"))
        toilet_type = _clean(row.get("type")) or "公共廁所"
        number = _clean(row.get("number"))
        output.append(
            PlaceDraft(
                external_id=_stable_id("moenv-toilet-", number, name, address),
                name=name,
                category=PlaceCategory.TOILET,
                subcategory=toilet_type,
                address=address,
                city=city,
                district=district,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                source_dataset="全國公廁建檔資料",
                source_agency="環境部環境管理署",
                properties={
                    "toilet_type": toilet_type,
                    "accessible": "無障礙" in toilet_type or "殘障" in name,
                    "grade": _clean(row.get("grade")),
                    "facility_category": _clean(row.get("type2")),
                    "administration": _clean(row.get("administration")),
                    "diaper": _clean(row.get("diaper")) == "1",
                    "opening_hours": _clean(row.get("openinghours")),
                    "gender_friendly": "性別友善" in toilet_type,
                    "parent_child": "親子" in toilet_type or _clean(row.get("diaper")) == "1",
                },
            )
        )
    return output


def normalize_national_aed(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    output: list[PlaceDraft] = []
    for index, row in enumerate(rows, start=1):
        name = _clean(row.get("場所名稱")) or f"AED {index}"
        address = _clean(row.get("場所地址"))
        city, district = _city_district(address, _clean(row.get("場所縣市")))
        coordinate = validate_wgs84(row.get("地點LAT"), row.get("地點LNG"))
        aed_id = _clean(row.get("AEDID")) or _clean(row.get("場所ID"))
        available_hours = _clean(row.get("開放使用時間備註"))
        output.append(
            PlaceDraft(
                external_id=_stable_id("mohw-aed-", aed_id, name, address),
                name=name,
                category=PlaceCategory.AED,
                subcategory=_clean(row.get("場所類型")),
                address=address,
                city=city,
                district=district,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                phone=_clean(row.get("開放時間緊急連絡電話")),
                source_dataset="全國公共場所 AED 位置資訊",
                source_agency="衛生福利部醫事司",
                properties={
                    "location_description": (
                        _clean(row.get("AED地點描述")) or _clean(row.get("AED放置地點"))
                    ),
                    "available_hours": available_hours,
                    "floor": _clean(row.get("AED放置樓層")) or _clean(row.get("樓層")),
                    "available_24h": bool(
                        available_hours
                        and any(token in available_hours for token in ("24小時", "24H", "全天"))
                    ),
                    "place_category": _clean(row.get("場所分類")),
                },
            )
        )
    return output
