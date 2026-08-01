from __future__ import annotations

import hashlib
import unicodedata
from collections.abc import Iterable, Mapping

from app.domain.models import PlaceCategory, PlaceDraft
from app.services.coordinates import validate_wgs84

SOURCE_DATASET = "高雄市公廁位置"
SOURCE_AGENCY = "高雄市政府環境保護局"


def _clean(value: object) -> str | None:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    return text or None


def _stable_id(*parts: str | None) -> str:
    source = "|".join(part or "" for part in parts)
    return "kcg-toilet-" + hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]


def _toilet_type(name: str) -> str:
    if "無障礙" in name:
        return "無障礙廁所"
    if "親子" in name or "哺乳" in name:
        return "親子廁所"
    if "女" in name:
        return "女廁"
    if "男" in name:
        return "男廁"
    return "公共廁所"


def normalize_toilet_rows(rows: Iterable[Mapping[str, object]]) -> list[PlaceDraft]:
    output: list[PlaceDraft] = []
    for row_number, row in enumerate(rows, start=1):
        name = _clean(row.get("name")) or f"公共廁所 {row_number}"
        address = _clean(row.get("address"))
        coordinate = validate_wgs84(row.get("Lat"), row.get("Lng"))
        toilet_type = _toilet_type(name)
        output.append(
            PlaceDraft(
                external_id=_stable_id(_clean(row.get("Seq")), name, address),
                name=name,
                category=PlaceCategory.TOILET,
                subcategory=toilet_type,
                address=address,
                city="高雄市",
                district=None,
                latitude=coordinate.latitude,
                longitude=coordinate.longitude,
                location_accuracy=coordinate.accuracy,
                source_dataset=SOURCE_DATASET,
                source_agency=SOURCE_AGENCY,
                properties={
                    "toilet_type": toilet_type,
                    "accessible": "無障礙" in name,
                    "coordinate_error": coordinate.error,
                },
            )
        )
    return output
