from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.domain.models import PlaceDraft
from app.importers.parking import normalize_parking_rows
from app.importers.quality import QualityReport, evaluate_quality
from app.importers.snapshots import FileRawSnapshotStore, RawSnapshot
from app.sources.config import SourceConfig, load_source_config
from app.sources.downloader import download_source


class ImportPublisher(Protocol):
    def previous_record_count(self, dataset_key: str) -> int | None: ...

    def publish(
        self,
        config: SourceConfig,
        snapshot: RawSnapshot,
        places: list[PlaceDraft],
        quality: QualityReport,
    ) -> int: ...


@dataclass(frozen=True, slots=True)
class ImportResult:
    snapshot: RawSnapshot
    quality: QualityReport
    published_count: int


async def import_parking_source(
    config_path: Path,
    snapshot_root: Path,
    publisher: ImportPublisher,
) -> ImportResult:
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
    quality = evaluate_quality(
        places,
        config.quality_gates,
        previous_record_count=publisher.previous_record_count(config.dataset_key),
    )
    if not quality.accepted:
        return ImportResult(snapshot=snapshot, quality=quality, published_count=0)
    published_count = publisher.publish(config, snapshot, places, quality)
    return ImportResult(snapshot=snapshot, quality=quality, published_count=published_count)
