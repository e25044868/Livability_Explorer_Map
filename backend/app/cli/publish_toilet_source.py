from __future__ import annotations

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
from app.importers.toilet import normalize_toilet_rows
from app.settings import Settings
from app.sources.config import load_source_config
from app.sources.downloader import download_source


async def publish(config_path: Path, snapshot_root: Path) -> dict[str, object]:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    config = load_source_config(config_path)
    downloaded = await download_source(config)
    snapshot = FileRawSnapshotStore(snapshot_root).save(
        config.dataset_key, downloaded.content, source_url=config.download.url
    )
    payload = json.loads(downloaded.content.decode(config.download.encoding))
    rows = payload.get(config.payload_path)
    if not isinstance(rows, list):
        raise ValueError(f"payload_path `{config.payload_path}` 不是 list")
    places = normalize_toilet_rows(rows)
    engine = create_engine(settings.database_url, pool_pre_ping=True, poolclass=NullPool)
    publisher = SqlAlchemyImportPublisher(sessionmaker(engine, expire_on_commit=False))
    try:
        quality = evaluate_quality(
            places,
            config.quality_gates,
            previous_record_count=publisher.previous_record_count(config.dataset_key),
        )
        published = publisher.publish(config, snapshot, places, quality) if quality.accepted else 0
        return {"quality": asdict(quality), "published_count": published}
    finally:
        engine.dispose()


def main() -> None:
    result = asyncio.run(publish(Path("data_sources/toilet_kaohsiung.yaml"), Path("data/raw")))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
