from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
from dataclasses import asdict
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.publisher import SqlAlchemyImportPublisher
from app.importers.national import normalize_national_aed, normalize_national_toilets
from app.importers.quality import evaluate_quality
from app.importers.snapshots import FileRawSnapshotStore
from app.settings import Settings
from app.sources.config import SourceConfig, load_source_config
from app.sources.downloader import (
    download_source,
    system_trust_context,
    validate_public_addresses,
)


async def _download_all_toilets(config: SourceConfig) -> bytes:
    parsed = urlsplit(config.download.url)
    validate_public_addresses(parsed.hostname or "")
    base_params = dict(parse_qsl(parsed.query))
    rows: list[dict[str, object]] = []
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(config.download.timeout_seconds),
        follow_redirects=False,
        trust_env=False,
        verify=system_trust_context(),
        headers={"Accept": "application/json", "User-Agent": "livability-map-importer/0.1"},
    ) as client:
        for offset in range(0, 100_000, 1000):
            params = {**base_params, "limit": "1000", "offset": str(offset)}
            url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(params), ""))
            response = await client.get(url)
            response.raise_for_status()
            page = response.json()
            if not isinstance(page, list):
                raise ValueError("全國公廁 API 回應不是 list")
            rows.extend(page)
            if len(page) < 1000:
                break
    content = json.dumps({"data": rows}, ensure_ascii=False).encode("utf-8")
    if len(content) > config.download.max_bytes:
        raise ValueError("全國公廁合併資料超過下載上限")
    return content


async def _load_places(
    config: SourceConfig, snapshot_path: Path | None = None
) -> tuple[bytes, list[object]]:
    if snapshot_path is not None:
        content = snapshot_path.read_bytes()
        if config.category == "toilet":
            return content, normalize_national_toilets(json.loads(content)["data"])
        reader = csv.DictReader(io.StringIO(content.decode(config.download.encoding)))
        return content, normalize_national_aed(list(reader))
    if config.category == "toilet":
        content = await _download_all_toilets(config)
        payload = json.loads(content)
        return content, normalize_national_toilets(payload["data"])
    downloaded = await download_source(config)
    reader = csv.DictReader(io.StringIO(downloaded.content.decode(config.download.encoding)))
    rows = list(reader)
    content = json.dumps({"data": rows}, ensure_ascii=False).encode("utf-8")
    return content, normalize_national_aed(rows)


async def publish_one(
    config_path: Path,
    snapshot_root: Path,
    publisher: SqlAlchemyImportPublisher,
    snapshot_path: Path | None = None,
) -> dict[str, object]:
    config = load_source_config(config_path)
    content, places = await _load_places(config, snapshot_path)
    snapshot = FileRawSnapshotStore(snapshot_root).save(
        config.dataset_key, content, source_url=config.download.url
    )
    quality = evaluate_quality(
        places,  # type: ignore[arg-type]
        config.quality_gates,
        previous_record_count=publisher.previous_record_count(config.dataset_key),
    )
    published = publisher.publish(config, snapshot, places, quality) if quality.accepted else 0  # type: ignore[arg-type]
    return {"dataset_key": config.dataset_key, "quality": asdict(quality), "published": published}


async def main_async(
    snapshot_root: Path, toilet_snapshot: Path | None = None, skip_toilet: bool = False
) -> list[dict[str, object]]:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    engine = create_engine(settings.database_url, pool_pre_ping=True, poolclass=NullPool)
    sessions = sessionmaker(engine, expire_on_commit=False)
    publisher = SqlAlchemyImportPublisher(sessions)
    try:
        results = []
        sources = [(Path("data_sources/aed_taiwan.yaml"), None)]
        if not skip_toilet:
            sources.insert(0, (Path("data_sources/toilet_taiwan.yaml"), toilet_snapshot))
        for config_path, snapshot_path in sources:
            results.append(await publish_one(config_path, snapshot_root, publisher, snapshot_path))
        if all(result["published"] for result in results):
            with sessions() as session, session.begin():
                session.execute(
                    text("""
                    UPDATE places SET is_active = false
                    WHERE data_source_id IN (
                        SELECT id FROM data_sources WHERE dataset_key IN (
                            'kcg_public_toilets', 'kcg_public_aed'
                        )
                    )
                """)
                )
                session.execute(
                    text("""
                    UPDATE data_sources SET is_enabled = false
                    WHERE dataset_key IN ('kcg_public_toilets', 'kcg_public_aed')
                """)
                )
        return results
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="下載、驗證並發布全國公廁與 AED")
    parser.add_argument("--snapshot-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--toilet-snapshot", type=Path)
    parser.add_argument("--skip-toilet", action="store_true")
    args = parser.parse_args()
    result = asyncio.run(main_async(args.snapshot_root, args.toilet_snapshot, args.skip_toilet))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
