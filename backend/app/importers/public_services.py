from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping

from pyproj import Transformer

from app.domain.models import LocationAccuracy, PlaceCategory, PlaceDraft
from app.services.coordinates import validate_wgs84

_TM2_TO_WGS84 = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _id(prefix: str, *values: object) -> str:
    digest = hashlib.sha256("|".join(str(value or "") for value in values).encode()).hexdigest()
    return f"{prefix}{digest[:22]}"


def _yes(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "是", "有"}


def _city_district(address: object) -> tuple[str | None, str | None]:
    text = re.sub(r"^\s*\d{3,6}\s*", "", _text(address) or "").replace("台", "臺")
    cities = (
        "臺北市|新北市|桃園市|臺中市|臺南市|高雄市|基隆市|新竹市|嘉義市|新竹縣|苗栗縣|彰化縣|"
        "南投縣|雲林縣|嘉義縣|屏東縣|宜蘭縣|花蓮縣|臺東縣|澎湖縣|金門縣|連江縣"
    )
    city_match = re.match(rf"^(?:{cities})", text)
    if not city_match:
        return None, None
    city = city_match.group(0)
    remaining = text[len(city) :]
    district_match = re.match(r"^([^\d]{1,8}(?:區|鄉|鎮|市))", remaining)
    return city, district_match.group(1) if district_match else None


def normalize_public_wifi(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    places: list[PlaceDraft] = []
    for row in rows:
        name = _text(row.get("Name")) or "iTaiwan 公共免費 Wi-Fi"
        address = _text(row.get("Address"))
        city, district = _city_district(address)
        coordinate = validate_wgs84(row.get("Latitude"), row.get("Longitude"))
        places.append(
            PlaceDraft(
                external_id=_id("itaiwan-wifi-", row.get("Area"), name, address),
                name=name,
                category=PlaceCategory.PUBLIC_WIFI,
                subcategory=_text(row.get("Area")),
                address=address,
                city=city,
                district=district,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                source_dataset="iTaiwan 公共區域免費無線上網熱點",
                source_agency=_text(row.get("Agency")) or "數位發展部",
                properties={
                    "agency": _text(row.get("Agency")),
                    "venue_type": _text(row.get("Area")),
                },
            )
        )
    return places


def normalize_rescue_units(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    places: list[PlaceDraft] = []
    for row in rows:
        name = _text(row.get("消防隊名稱")) or "消防／救援據點"
        address = _text(row.get("地址"))
        city, district = _city_district(address)
        # The official header calls these TWD97 fields; published values are longitude/latitude.
        coordinate = validate_wgs84(row.get("Y座標_TWD97TM121"), row.get("X座標_TWD97TM121"))
        places.append(
            PlaceDraft(
                external_id=_id("nfa-rescue-", name, address),
                name=name,
                category=PlaceCategory.RESCUE_UNIT,
                subcategory="消防／救援據點",
                address=address,
                city=city,
                district=district,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                phone=_text(row.get("聯絡電話")),
                source_dataset="救災救護單位位置資訊",
                source_agency="內政部消防署",
                properties={"co_located_with_fire_station": _yes(row.get("是否與消防隊同址"))},
            )
        )
    return places


def normalize_police(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    places: list[PlaceDraft] = []
    for row in rows:
        name = _text(row.get("中文單位名稱")) or "警察機關"
        address = _text(row.get("地址"))
        city, district = _city_district(address)
        try:
            point_x = float(str(row.get("POINT_X")))
            point_y = float(str(row.get("POINT_Y")))
            longitude, latitude = _TM2_TO_WGS84.transform(point_x, point_y)
            coordinate = validate_wgs84(latitude, longitude)
            accuracy = (
                LocationAccuracy.CONVERTED_COORDINATE
                if coordinate.latitude is not None
                else coordinate.accuracy
            )
        except (TypeError, ValueError):
            coordinate = validate_wgs84(None, None)
            accuracy = coordinate.accuracy
        unit_type = "派出所" if "派出所" in name else "分駐所" if "分駐所" in name else "警察機關"
        places.append(
            PlaceDraft(
                external_id=_id("npa-police-", name, address),
                name=name,
                category=PlaceCategory.POLICE,
                subcategory=unit_type,
                address=address,
                city=city,
                district=district,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=accuracy,
                phone=_text(row.get("電話")),
                source_dataset="警察機關地址與座標資料",
                source_agency="內政部警政署",
                properties={"english_name": _text(row.get("英文單位名稱")), "unit_type": unit_type},
            )
        )
    return places


def normalize_libraries(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    """Normalize the nested official Public Library Information Network response."""
    places: list[PlaceDraft] = []
    for city_group in rows:
        if not isinstance(city_group, Mapping):
            continue
        city = _text(city_group.get("縣市"))
        libraries = city_group.get("圖書館資訊")
        if not isinstance(libraries, list):
            continue
        for row in libraries:
            if not isinstance(row, Mapping):
                continue
            name = _text(row.get("Name")) or "公共圖書館"
            address = _text(row.get("Address"))
            parsed_city, district = _city_district(address)
            coordinate = validate_wgs84(row.get("Latitude"), row.get("Longitude"))
            places.append(
                PlaceDraft(
                    external_id=_id("public-library-", name, address),
                    name=name,
                    category=PlaceCategory.LIBRARY,
                    subcategory="公共圖書館",
                    address=address,
                    city=parsed_city or city,
                    district=district or _text(row.get("Area")),
                    latitude=coordinate.latitude,
                    longitude=coordinate.longitude,
                    location_accuracy=coordinate.accuracy,
                    phone=_text(row.get("TEL")),
                    source_dataset="公共圖書館基本資料",
                    source_agency="國立公共資訊圖書館",
                    properties={"website": _text(row.get("URL"))},
                )
            )
    return places
