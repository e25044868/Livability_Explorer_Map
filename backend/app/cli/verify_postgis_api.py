from __future__ import annotations

import asyncio
import json
import sys

import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.read_repository import PostgresPlaceReadRepository
from app.main import create_app
from app.settings import Settings


async def verify() -> dict[str, object]:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    repository = PostgresPlaceReadRepository(async_sessionmaker(engine, expire_on_commit=False))
    app = create_app(repository, settings=settings)
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            radius = await client.get(
                "/api/places",
                params={"lat": 22.6273, "lng": 120.3014, "radius": 3000, "limit": 50},
            )
            viewport = await client.get(
                "/api/places",
                params={
                    "north": 22.66,
                    "south": 22.59,
                    "east": 120.34,
                    "west": 120.27,
                    "limit": 100,
                },
            )
            summary = await client.get(
                "/api/nearby-summary",
                params={"lat": 22.6273, "lng": 120.3014, "radius": 3000},
            )
            unconditional = await client.get("/api/places")
            over_limit = await client.get(
                "/api/places", params={"district": "新興區", "limit": 501}
            )
            for response in (radius, viewport, summary):
                response.raise_for_status()
            return {
                "radius": {
                    "status": radius.status_code,
                    "count": radius.json()["count"],
                    "all_have_public_ids": all(
                        item.get("public_id") and "database_id" not in item
                        for item in radius.json()["items"]
                    ),
                },
                "viewport": {
                    "status": viewport.status_code,
                    "count": viewport.json()["count"],
                },
                "summary": {
                    "status": summary.status_code,
                    "parking": summary.json()["summary"].get("parking", 0),
                },
                "guards": {
                    "unconditional_status": unconditional.status_code,
                    "over_limit_status": over_limit.status_code,
                },
            }
    finally:
        await engine.dispose()


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print(json.dumps(asyncio.run(verify()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
