from __future__ import annotations

import asyncio
import csv
import io
import json
import zipfile
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.publisher import SqlAlchemyImportPublisher
from app.importers.public_services import (
    normalize_libraries,
    normalize_police,
    normalize_public_wifi,
    normalize_rescue_units,
    normalize_tourism_facilities,
)
from app.importers.quality import evaluate_quality
from app.importers.snapshots import FileRawSnapshotStore
from app.settings import Settings
from app.sources.config import SourceConfig, load_source_config
from app.sources.downloader import download_source

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _csv_rows(content: bytes, encoding: str) -> list[dict[str, object]]:
    return list(csv.DictReader(io.StringIO(content.decode(encoding))))


def _police_rows(content: bytes, encoding: str) -> list[dict[str, object]]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        members = [
            member
            for member in archive.infolist()
            if member.filename.lower().endswith(".csv")
            and not member.filename.lower().endswith("manifest.csv")
        ]
        if len(members) != 1 or members[0].is_dir() or members[0].file_size > 50_000_000:
            raise ValueError("警察資料 ZIP 內容不符合預期")
        with archive.open(members[0]) as stream:
            return _csv_rows(stream.read(), encoding)


def _normalise(config: SourceConfig, content: bytes) -> tuple[bytes, list]:
    if config.category == "public_wifi":
        raw = json.loads(content.decode(config.download.encoding))
        rows = raw.get(config.payload_path) if isinstance(raw, dict) else raw
        if not isinstance(rows, list):
            raise ValueError("公共 Wi-Fi JSON 缺少資料陣列")
        return json.dumps({"data": rows}, ensure_ascii=False).encode(), normalize_public_wifi(rows)
    if config.category == "rescue_unit":
        rows = _csv_rows(content, config.download.encoding)
        required = {"消防隊名稱", "地址", "X座標_TWD97TM121", "Y座標_TWD97TM121"}
        if not rows or not required.issubset(rows[0]):
            raise ValueError("消防／救援資料 CSV 缺少必要欄位")
        return json.dumps({"data": rows}, ensure_ascii=False).encode(), normalize_rescue_units(rows)
    if config.category == "police":
        rows = _police_rows(content, config.download.encoding)
        required = {"中文單位名稱", "地址", "POINT_X", "POINT_Y"}
        if not rows or not required.issubset(rows[0]):
            raise ValueError("警察資料 CSV 缺少必要欄位")
        return json.dumps({"data": rows}, ensure_ascii=False).encode(), normalize_police(rows)
    if config.category == "library":
        rows = json.loads(content.decode(config.download.encoding))
        if not isinstance(rows, list):
            raise ValueError("公共圖書館 JSON 缺少縣市資料陣列")
        return json.dumps({"data": rows}, ensure_ascii=False).encode(), normalize_libraries(rows)
    if config.category == "tourism_facility":
        rows = json.loads(content.decode(config.download.encoding))
        if not isinstance(rows, list):
            raise ValueError("風景區公共設施 JSON 缺少資料陣列")
        required = {"設施編號", "設施大類", "設施坐標X", "設施坐標Y"}
        if not rows or not required.issubset(rows[0]):
            raise ValueError("風景區公共設施 JSON 缺少必要欄位")
        snapshot_content = json.dumps({"data": rows}, ensure_ascii=False).encode()
        return snapshot_content, normalize_tourism_facilities(rows)
    raise ValueError(f"未支援的類別：{config.category}")


async def main_async(snapshot_root: Path | None = None) -> list[dict[str, object]]:
    snapshot_root = snapshot_root or PROJECT_ROOT / "data" / "raw"
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    engine = create_engine(settings.database_url, pool_pre_ping=True, poolclass=NullPool)
    publisher = SqlAlchemyImportPublisher(sessionmaker(engine, expire_on_commit=False))
    results: list[dict[str, object]] = []
    try:
        for source_path in (
            PROJECT_ROOT / "data_sources" / "public_wifi_taiwan.yaml",
            PROJECT_ROOT / "data_sources" / "rescue_units_taiwan.yaml",
            PROJECT_ROOT / "data_sources" / "police_taiwan.yaml",
            PROJECT_ROOT / "data_sources" / "libraries_taiwan.yaml",
            PROJECT_ROOT / "data_sources" / "tourism_facilities_taiwan.yaml",
        ):
            config = load_source_config(source_path)
            downloaded = await download_source(config)
            snapshot_content, places = _normalise(config, downloaded.content)
            snapshot = FileRawSnapshotStore(snapshot_root).save(
                config.dataset_key, snapshot_content, source_url=downloaded.final_url
            )
            quality = evaluate_quality(
                places,
                config.quality_gates,
                previous_record_count=publisher.previous_record_count(config.dataset_key),
            )
            published = 0
            if quality.accepted:
                published = publisher.publish(config, snapshot, places, quality)
            results.append(
                {
                    "dataset_key": config.dataset_key,
                    "quality": asdict(quality),
                    "published": published,
                }
            )
        return results
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main_async()), ensure_ascii=False, indent=2))
