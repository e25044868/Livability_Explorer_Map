from __future__ import annotations

import asyncio
import csv
import io
import json
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.publisher import SqlAlchemyImportPublisher
from app.importers.amenities import normalize_drinking_water, normalize_shelters
from app.importers.quality import evaluate_quality
from app.importers.snapshots import FileRawSnapshotStore
from app.settings import Settings
from app.sources.config import SourceConfig, load_source_config
from app.sources.downloader import system_trust_context, validate_public_addresses


async def _cool_map_rows(config: SourceConfig) -> tuple[bytes, list[dict[str, object]]]:
    parsed = urlsplit(config.download.url)
    base = dict(parse_qsl(parsed.query))
    rows = []
    async with httpx.AsyncClient(
        timeout=30, verify=system_trust_context(), trust_env=False
    ) as client:
        for offset in range(0, 100_000, 1000):
            query = urlencode({**base, "limit": "1000", "offset": str(offset)})
            response = await client.get(
                urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, ""))
            )
            response.raise_for_status()
            page = response.json()
            if not isinstance(page, list):
                raise ValueError("涼適點 API 回應不是 list")
            rows.extend(page)
            if len(page) < 1000:
                break
    return json.dumps({"data": rows}, ensure_ascii=False).encode(), rows


async def _shelter_content(config: SourceConfig) -> bytes:
    parsed = urlsplit(config.download.url)
    validate_public_addresses(parsed.hostname or "")
    async with httpx.AsyncClient(
        timeout=60, verify=system_trust_context(), trust_env=False, follow_redirects=False
    ) as client:
        response = await client.get(
            config.download.url,
            headers={"Accept": "text/csv", "User-Agent": "livability-map-importer/0.1"},
        )
        response.raise_for_status()
        content = response.content
    if len(content) > config.download.max_bytes:
        raise ValueError("避難處所檔案超過下載上限")
    return content


async def main_async(snapshot_root: Path = Path("data/raw")) -> list[dict[str, object]]:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    engine = create_engine(settings.database_url, pool_pre_ping=True, poolclass=NullPool)
    publisher = SqlAlchemyImportPublisher(sessionmaker(engine, expire_on_commit=False))
    results = []
    try:
        for path in (
            Path("data_sources/drinking_water_taiwan.yaml"),
            Path("data_sources/shelter_taiwan.yaml"),
        ):
            config = load_source_config(path)
            if config.category == "drinking_water":
                content, rows = await _cool_map_rows(config)
                places = normalize_drinking_water(rows)
            else:
                downloaded = await _shelter_content(config)
                rows = list(csv.DictReader(io.StringIO(downloaded.decode("utf-8-sig"))))
                required = {"避難收容處所名稱", "經度", "緯度"}
                if not rows or not required.issubset(rows[0]):
                    raise ValueError("避難處所 CSV 缺少必要欄位")
                places = normalize_shelters(rows)
                content = json.dumps({"data": rows}, ensure_ascii=False).encode()
            snapshot = FileRawSnapshotStore(snapshot_root).save(
                config.dataset_key, content, source_url=config.download.url
            )
            quality = evaluate_quality(
                places,
                config.quality_gates,
                previous_record_count=publisher.previous_record_count(config.dataset_key),
            )
            published = (
                publisher.publish(config, snapshot, places, quality) if quality.accepted else 0
            )
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
