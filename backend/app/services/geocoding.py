from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx


async def administrative_area(lat: float, lng: float) -> tuple[str, str | None]:
    """Use NLSC's official point-in-administrative-boundary service."""
    url = f"https://api.nlsc.gov.tw/other/TownVillagePointQuery/{lng}/{lat}/4326"
    async with httpx.AsyncClient(timeout=10, follow_redirects=True, trust_env=True) as client:
        response = await client.get(url, headers={"User-Agent": "LivabilityMap/0.2"})
        response.raise_for_status()
    root = ET.fromstring(response.content)
    city = root.findtext(".//ctyName")
    district = root.findtext(".//townName")
    if not city:
        raise ValueError("座標不在可辨識的臺灣行政區內")
    return city.replace("台", "臺"), district


async def geocode_landmarks(keyword: str, limit: int = 8) -> list[dict[str, object]]:
    """Search addresses/landmarks in Taiwan through Nominatim."""
    async with httpx.AsyncClient(timeout=10, follow_redirects=True, trust_env=True) as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": keyword,
                "format": "jsonv2",
                "countrycodes": "tw",
                "addressdetails": 1,
                "limit": limit,
            },
            headers={"User-Agent": "LivabilityMap/0.2 (local application)"},
        )
        response.raise_for_status()
    results = []
    for row in response.json():
        address = row.get("address") or {}
        city = address.get("city") or address.get("county")
        district = address.get("suburb") or address.get("town") or address.get("city_district")
        results.append(
            {
                "name": row.get("name") or str(row.get("display_name", "")).split(",")[0],
                "address": row.get("display_name") or "",
                "latitude": float(row["lat"]),
                "longitude": float(row["lon"]),
                "city": str(city).replace("台", "臺") if city else None,
                "district": district,
            }
        )
    return results
