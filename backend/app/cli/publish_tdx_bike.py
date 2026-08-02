from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.cli.publish_tdx_parking import CITY_NAMES
from app.db.publisher import SqlAlchemyImportPublisher
from app.importers.quality import evaluate_quality
from app.importers.snapshots import FileRawSnapshotStore
from app.importers.tdx_bike import normalize_tdx_bike_rows
from app.settings import Settings
from app.sources.config import SourceConfig
from app.sources.tdx import BIKE_STATION_URL, TdxBikeClient, TdxCredentials

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _config(city: str) -> SourceConfig:
    return SourceConfig.model_validate(
        {
            "dataset_key": f"tdx_public_bike_{city.lower()}",
            "dataset_id": city,
            "name": f"TDX {CITY_NAMES[city]}公共自行車站",
            "category": "public_bicycle",
            "source_agency": "交通部 TDX",
            "metadata_url": "https://tdx.transportdata.tw/api-service/swagger",
            "download": {
                "url": BIKE_STATION_URL.format(city=city),
                "allowed_hosts": ["tdx.transportdata.tw"],
                "format": "json",
                "timeout_seconds": 30,
                "max_bytes": 50_000_000,
            },
            "quality_gates": {
                "minimum_records": 1,
                "maximum_invalid_coordinate_ratio": 0.1,
                "maximum_record_count_change_ratio": 0.8,
            },
        }
    )


def _rows(payload: object, key: str) -> list[dict[str, object]]:
    rows = payload.get(key, payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("TDX 公共自行車回應不是 list")
    return [row for row in rows if isinstance(row, dict)]


async def publish_city(
    city: str,
    snapshot_root: Path,
    bike_client: TdxBikeClient | None = None,
) -> dict[str, object]:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    if not settings.tdx_client_id or not settings.tdx_client_secret:
        raise RuntimeError("請先設定 TDX_CLIENT_ID 與 TDX_CLIENT_SECRET")

    bike_client = bike_client or TdxBikeClient(
        TdxCredentials(settings.tdx_client_id, settings.tdx_client_secret)
    )
    stations_content, availability_content = await bike_client.fetch_city_with_availability(city)
    stations = _rows(json.loads(stations_content), "Stations")
    availability = _rows(json.loads(availability_content), "Availabilities")
    availability_by_id = {
        str(row.get("StationUID")): row
        for row in availability
        if row.get("StationUID") is not None
    }
    config = _config(city)
    places = normalize_tdx_bike_rows(stations, availability_by_id, CITY_NAMES[city])
    snapshot_content = json.dumps(
        {"stations": stations, "availability": availability}, ensure_ascii=False
    ).encode("utf-8")
    snapshot = FileRawSnapshotStore(snapshot_root).save(
        config.dataset_key, snapshot_content, source_url=config.download.url
    )
    engine = create_engine(settings.database_url, pool_pre_ping=True, poolclass=NullPool)
    publisher = SqlAlchemyImportPublisher(sessionmaker(engine, expire_on_commit=False))
    try:
        quality = evaluate_quality(
            places,
            config.quality_gates,
            previous_record_count=publisher.previous_record_count(config.dataset_key),
        )
        published = publisher.publish(config, snapshot, places, quality) if quality.accepted else 0
        return {"city": city, "quality": asdict(quality), "published": published}
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="發布指定縣市 TDX 公共自行車站")
    parser.add_argument("city", choices=sorted(CITY_NAMES))
    parser.add_argument("--snapshot-root", type=Path, default=PROJECT_ROOT / "data" / "raw")
    args = parser.parse_args()
    result = asyncio.run(publish_city(args.city, args.snapshot_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
