from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.publisher import SqlAlchemyImportPublisher
from app.importers.quality import evaluate_quality
from app.importers.snapshots import FileRawSnapshotStore
from app.importers.tdx_parking import normalize_tdx_parking_rows
from app.settings import Settings
from app.sources.config import SourceConfig
from app.sources.tdx import PARKING_URL, TdxCredentials, TdxParkingClient

CITY_NAMES = {
    "Taipei": "臺北市",
    "NewTaipei": "新北市",
    "Taoyuan": "桃園市",
    "Taichung": "臺中市",
    "Tainan": "臺南市",
    "Kaohsiung": "高雄市",
    "Keelung": "基隆市",
    "Hsinchu": "新竹市",
    "HsinchuCounty": "新竹縣",
    "MiaoliCounty": "苗栗縣",
    "ChanghuaCounty": "彰化縣",
    "NantouCounty": "南投縣",
    "YunlinCounty": "雲林縣",
    "ChiayiCounty": "嘉義縣",
    "Chiayi": "嘉義市",
    "PingtungCounty": "屏東縣",
    "YilanCounty": "宜蘭縣",
    "HualienCounty": "花蓮縣",
    "TaitungCounty": "臺東縣",
    "PenghuCounty": "澎湖縣",
    "KinmenCounty": "金門縣",
    "LienchiangCounty": "連江縣",
}


def _config(city: str) -> SourceConfig:
    return SourceConfig.model_validate(
        {
            "dataset_key": f"tdx_parking_{city.lower()}",
            "dataset_id": city,
            "name": f"TDX {CITY_NAMES[city]}停車場",
            "category": "parking",
            "source_agency": "交通部 TDX",
            "metadata_url": "https://data.gov.tw/dataset/161174",
            "download": {
                "url": PARKING_URL.format(city=city),
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


async def publish_city(city: str, snapshot_root: Path) -> dict[str, object]:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    if not settings.tdx_client_id or not settings.tdx_client_secret:
        raise RuntimeError("請先設定 TDX_CLIENT_ID 與 TDX_CLIENT_SECRET")
    content, availability_content = await TdxParkingClient(
        TdxCredentials(settings.tdx_client_id, settings.tdx_client_secret)
    ).fetch_city_with_availability(city)
    payload = json.loads(content)
    rows = payload.get("CarParks", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("TDX 停車場回應不是 list")
    availability_payload = json.loads(availability_content)
    availability_rows = (
        availability_payload.get("ParkingAvailabilities", availability_payload)
        if isinstance(availability_payload, dict)
        else availability_payload
    )
    live_by_id = (
        {str(item.get("CarParkID")): item for item in availability_rows if isinstance(item, dict)}
        if isinstance(availability_rows, list)
        else {}
    )
    rows = [
        {**row, **live_by_id.get(str(row.get("CarParkID")), {})}
        for row in rows
        if isinstance(row, dict)
    ]
    config = _config(city)
    places = normalize_tdx_parking_rows(rows, CITY_NAMES[city])
    snapshot = FileRawSnapshotStore(snapshot_root).save(
        config.dataset_key, content, source_url=config.download.url
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
    parser = argparse.ArgumentParser(description="發布指定縣市 TDX 停車場")
    parser.add_argument("city", choices=sorted(CITY_NAMES))
    parser.add_argument("--snapshot-root", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    result = asyncio.run(publish_city(args.city, args.snapshot_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
