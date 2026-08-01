from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from app.importers.parking import normalize_parking_rows
from app.importers.quality import evaluate_quality
from app.importers.snapshots import FileRawSnapshotStore
from app.sources.config import load_source_config
from app.sources.downloader import download_source


async def validate(config_path: Path, snapshot_root: Path) -> dict[str, object]:
    config = load_source_config(config_path)
    downloaded = await download_source(config)
    snapshot = FileRawSnapshotStore(snapshot_root).save(
        config.dataset_key,
        downloaded.content,
        source_url=config.download.url,
    )
    payload = json.loads(downloaded.content.decode(config.download.encoding))
    rows = payload.get(config.payload_path)
    if not isinstance(rows, list):
        raise ValueError(f"payload_path `{config.payload_path}` 不是 list")
    places = normalize_parking_rows(rows)
    report = evaluate_quality(places, config.quality_gates)
    return {
        "dataset_key": config.dataset_key,
        "snapshot_hash": snapshot.content_hash,
        "snapshot_path": str(snapshot.payload_path),
        "download_bytes": snapshot.byte_count,
        "quality": asdict(report),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="安全下載並驗證停車場來源，不發布正式資料")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("data_sources/parking_kaohsiung.yaml"),
    )
    parser.add_argument("--snapshot-root", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    result = asyncio.run(validate(args.config, args.snapshot_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
