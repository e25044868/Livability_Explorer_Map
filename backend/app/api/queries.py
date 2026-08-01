from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastapi import HTTPException

MAX_VIEWPORT_SPAN_DEGREES = 0.5
MAX_RADIUS_METERS = 3000


@dataclass(frozen=True, slots=True)
class PlaceQuery:
    lat: float | None
    lng: float | None
    radius: int | None
    north: float | None
    south: float | None
    east: float | None
    west: float | None
    city: str | None
    district: str | None
    categories: tuple[str, ...]
    keyword: str | None
    limit: int


def validate_place_query(
    *,
    lat: float | None = None,
    lng: float | None = None,
    radius: int | None = None,
    north: float | None = None,
    south: float | None = None,
    east: float | None = None,
    west: float | None = None,
    city: str | None = None,
    district: str | None = None,
    categories: str | None = None,
    keyword: str | None = None,
    limit: int = 300,
) -> PlaceQuery:
    center_values = (lat, lng, radius)
    viewport_values = (north, south, east, west)
    has_center = all(value is not None for value in center_values)
    has_viewport = all(value is not None for value in viewport_values)
    if any(value is not None for value in center_values) and not has_center:
        raise HTTPException(400, "lat、lng、radius 必須一起提供")
    if any(value is not None for value in viewport_values) and not has_viewport:
        raise HTTPException(400, "north、south、east、west 必須一起提供")
    cleaned_keyword = keyword.strip() if keyword else None
    if cleaned_keyword and len(cleaned_keyword) < 2:
        raise HTTPException(400, "keyword 至少 2 個字元")
    if not (has_center or has_viewport or city or district or cleaned_keyword):
        raise HTTPException(400, "必須提供 viewport、中心點與半徑、行政區或有效關鍵字")
    if has_center:
        assert lat is not None and lng is not None and radius is not None
        if not 21.5 <= lat <= 25.5 or not 119 <= lng <= 122.5:
            raise HTTPException(400, "中心座標超出台灣合理範圍")
        if not 1 <= radius <= MAX_RADIUS_METERS:
            raise HTTPException(400, f"radius 必須介於 1 與 {MAX_RADIUS_METERS}")
    if has_viewport:
        assert None not in (north, south, east, west)
        north_value = cast(float, north)
        south_value = cast(float, south)
        east_value = cast(float, east)
        west_value = cast(float, west)
        if north_value <= south_value or east_value <= west_value:
            raise HTTPException(400, "viewport 邊界順序錯誤")
        if north_value - south_value > MAX_VIEWPORT_SPAN_DEGREES:
            raise HTTPException(400, "viewport 範圍過大，請放大地圖")
        if east_value - west_value > MAX_VIEWPORT_SPAN_DEGREES:
            raise HTTPException(400, "viewport 範圍過大，請放大地圖")
    if not 1 <= limit <= 500:
        raise HTTPException(400, "limit 必須介於 1 與 500")
    category_values = tuple(
        dict.fromkeys(item.strip() for item in (categories or "").split(",") if item.strip())
    )
    return PlaceQuery(
        lat=lat,
        lng=lng,
        radius=radius,
        north=north,
        south=south,
        east=east,
        west=west,
        city=city,
        district=district,
        categories=category_values,
        keyword=cleaned_keyword,
        limit=limit,
    )
