from __future__ import annotations

from typing import Protocol

from app.api.queries import PlaceQuery
from app.api.schemas import PlaceSummaryResponse


class PlaceReadRepository(Protocol):
    async def list_places(self, query: PlaceQuery) -> tuple[list[PlaceSummaryResponse], str]: ...

    async def get_place(self, public_id: str) -> PlaceSummaryResponse | None: ...

    async def nearby_summary(
        self, lat: float, lng: float, radius: int
    ) -> tuple[dict[str, int], str]: ...

    async def list_districts(self, city: str) -> list[str]: ...


class EmptyPlaceReadRepository:
    async def list_places(self, query: PlaceQuery) -> tuple[list[PlaceSummaryResponse], str]:
        return [], "empty"

    async def get_place(self, public_id: str) -> PlaceSummaryResponse | None:
        return None

    async def nearby_summary(
        self, lat: float, lng: float, radius: int
    ) -> tuple[dict[str, int], str]:
        return {}, "empty"

    async def list_districts(self, city: str) -> list[str]:
        return []
