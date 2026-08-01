from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.db.publisher import SqlAlchemyImportPublisher
from app.importers.parking import normalize_parking_rows
from app.importers.pipeline import import_parking_source
from app.importers.quality import evaluate_quality
from app.importers.snapshots import RawSnapshot
from app.settings import Settings
from app.sources.config import load_source_config


async def publish(
    config_path: Path, snapshot_root: Path, snapshot_path: Path | None = None
) -> dict[str, object]:
    settings = Settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL 未設定")
    engine = create_engine(settings.database_url, pool_pre_ping=True, poolclass=NullPool)
    sessions = sessionmaker(engine, expire_on_commit=False)
    publisher = SqlAlchemyImportPublisher(sessions)
    try:
        if snapshot_path is None:
            result = await import_parking_source(config_path, snapshot_root, publisher)
            return {
                "snapshot_hash": result.snapshot.content_hash,
                "quality": asdict(result.quality),
                "published_count": result.published_count,
            }
        content = snapshot_path.read_bytes()
        config = load_source_config(config_path)
        payload = json.loads(content.decode(config.download.encoding))
        rows = payload.get(config.payload_path)
        if not isinstance(rows, list):
            raise ValueError(f"payload_path `{config.payload_path}` 不是 list")
        places = normalize_parking_rows(rows)
        quality = evaluate_quality(
            places,
            config.quality_gates,
            previous_record_count=publisher.previous_record_count(config.dataset_key),
        )
        digest = hashlib.sha256(content).hexdigest()
        snapshot = RawSnapshot(
            dataset_key=config.dataset_key,
            content_hash=digest,
            fetched_at=datetime.fromtimestamp(snapshot_path.stat().st_mtime, UTC).isoformat(),
            payload_path=snapshot_path,
            metadata_path=snapshot_path.with_suffix(".metadata.json"),
            byte_count=len(content),
        )
        published_count = (
            publisher.publish(config, snapshot, places, quality) if quality.accepted else 0
        )
        return {
            "snapshot_hash": digest,
            "quality": asdict(quality),
            "published_count": published_count,
        }
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="驗證並正式發布高雄停車場資料")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("data_sources/parking_kaohsiung.yaml"),
    )
    parser.add_argument("--snapshot-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--snapshot", type=Path, help="從已驗證 raw snapshot 發布，不重新下載")
    args = parser.parse_args()
    result = asyncio.run(publish(args.config, args.snapshot_root, args.snapshot))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
