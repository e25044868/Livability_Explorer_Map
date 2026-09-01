from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.queries import PlaceQuery
from app.api.schemas import PlaceSummaryResponse

PUBLIC_PROPERTY_KEYS: dict[str, set[str]] = {
    "parking": {
        "facility_type",
        "fee_description",
        "large_vehicle_spaces",
        "car_spaces",
        "motorcycle_spaces",
        "operator",
        "contract_period_raw",
        "parent_name",
        "zone_label",
        "available_spaces",
        "total_spaces",
        "service_status",
        "live_updated_at",
        "operation_time",
        "ev_spaces",
        "accessible_spaces",
        "parent_child_spaces",
        "height_limit",
        "monthly_pass",
    },
    "toilet": {
        "toilet_type",
        "accessible",
        "floor",
        "grade",
        "facility_category",
        "administration",
        "diaper",
        "opening_hours",
        "gender_friendly",
        "parent_child",
    },
    "aed": {"location_description", "floor", "available_hours", "place_category", "available_24h"},
    "pharmacy": set(),
    "medical": {"institution_code", "specialties"},
    "motorcycle_charging": {"fee_description", "site_name"},
    "drinking_water": {
        "opening_hours",
        "accessible",
        "indoor",
        "air_conditioning",
        "restroom",
        "seats",
        "station_type",
    },
    "shelter": {
        "capacity",
        "disaster_types",
        "indoor",
        "outdoor",
        "vulnerable_friendly",
        "service_villages",
    },
    "public_wifi": {"agency", "venue_type"},
    "rescue_unit": {"co_located_with_fire_station"},
    "police": {"english_name", "unit_type"},
    "library": {"website"},
    "public_bicycle": {
        "station_capacity",
        "available_rent_bikes",
        "available_return_bikes",
        "service_status",
        "live_updated_at",
        "bike_sharing_type",
    },
    "tourism_facility": {
        "facility_type",
        "facility_subtype",
        "management_office",
        "facility_status",
        "facility_description",
        "landscape_area",
        "accessible",
        "parent_child",
    },
}


def public_properties(category: str, properties: dict[str, Any] | None) -> dict[str, Any]:
    allowed = PUBLIC_PROPERTY_KEYS.get(category, set())
    return {key: value for key, value in (properties or {}).items() if key in allowed}


class PostgresPlaceReadRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self.sessions = sessions

    async def list_places(self, query: PlaceQuery) -> tuple[list[PlaceSummaryResponse], str]:
        conditions = ["is_active = true"]
        parameters: dict[str, Any] = {"limit": query.limit}
        if query.lat is not None:
            conditions.append(
                "ST_DWithin(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)"
            )
            parameters.update(lat=query.lat, lng=query.lng, radius=query.radius)
        if query.north is not None:
            conditions.append(
                "geom::geometry && ST_MakeEnvelope(:west, :south, :east, :north, 4326)"
            )
            parameters.update(
                north=query.north,
                south=query.south,
                east=query.east,
                west=query.west,
            )
        if query.city:
            conditions.append("city = :city")
            parameters["city"] = query.city
        if query.district:
            conditions.append("district = :district")
            parameters["district"] = query.district
        if query.categories:
            conditions.append("category = ANY(:categories)")
            parameters["categories"] = list(query.categories)
        if query.keyword:
            conditions.append(
                "(normalized_name ILIKE :keyword OR normalized_address ILIKE :keyword)"
            )
            parameters["keyword"] = f"%{query.keyword}%"
        distance_column = (
            "ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography)"
            if query.lat is not None
            else "NULL"
        )
        statement = text(
            f"""
            SELECT public_id::text, name, category, subcategory, address, phone, city, district,
                   latitude, longitude,
                   location_accuracy, properties, last_synced_at,
                   {distance_column} AS distance_meters
            FROM places
            WHERE {" AND ".join(conditions)}
            ORDER BY distance_meters NULLS LAST, name
            LIMIT :limit
            """
        )
        async with self.sessions() as session:
            rows = (await session.execute(statement, parameters)).mappings().all()
        items = [self._to_summary(dict(row)) for row in rows]
        version = max((row["last_synced_at"].isoformat() for row in rows), default="empty")
        return items, version

    async def get_place(self, public_id: str) -> PlaceSummaryResponse | None:
        statement = text(
            """
            SELECT public_id::text, name, category, subcategory, address, phone, city, district,
                   latitude, longitude,
                   location_accuracy, properties, last_synced_at
            FROM places
            WHERE public_id::text = :public_id AND is_active = true
            """
        )
        async with self.sessions() as session:
            row = (await session.execute(statement, {"public_id": public_id})).mappings().first()
        return self._to_summary(dict(row)) if row else None

    async def nearby_summary(
        self, lat: float, lng: float, radius: int
    ) -> tuple[dict[str, int], str]:
        statement = text(
            """
            SELECT category, count(*)::integer AS count, max(last_synced_at) AS data_version
            FROM places
            WHERE is_active = true
              AND geom IS NOT NULL
              AND ST_DWithin(
                  geom,
                  ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                  :radius
              )
            GROUP BY category
            """
        )
        async with self.sessions() as session:
            rows = (
                (await session.execute(statement, {"lat": lat, "lng": lng, "radius": radius}))
                .mappings()
                .all()
            )
        summary = {row["category"]: row["count"] for row in rows}
        version = max((row["data_version"].isoformat() for row in rows), default="empty")
        return summary, version

    async def list_districts(self, city: str) -> list[str]:
        statement = text(
            """
            SELECT DISTINCT district
            FROM places
            WHERE is_active = true AND city = :city AND district IS NOT NULL AND district <> ''
            ORDER BY district
            """
        )
        async with self.sessions() as session:
            rows = (await session.execute(statement, {"city": city})).scalars().all()
        return [str(district) for district in rows]

    @staticmethod
    def _to_summary(row: dict[str, Any]) -> PlaceSummaryResponse:
        return PlaceSummaryResponse(
            public_id=row["public_id"],
            name=row["name"],
            category=row["category"],
            subcategory=row.get("subcategory"),
            address=row.get("address"),
            phone=row.get("phone"),
            city=row.get("city"),
            district=row.get("district"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            distance_meters=row.get("distance_meters"),
            location_accuracy=row["location_accuracy"],
            properties=public_properties(row["category"], row.get("properties")),
        )
