from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import DataSourceRecord, ImportRunRecord, PlaceRecord, RawImportRecord
from app.domain.models import PlaceDraft
from app.importers.quality import QualityReport
from app.importers.snapshots import RawSnapshot
from app.sources.config import SourceConfig


def _normalized(value: str | None) -> str:
    return unicodedata.normalize("NFKC", value or "").strip().lower()


class SqlAlchemyImportPublisher:
    """品質閘門通過後，在單一 transaction 內 upsert 並停用缺少紀錄。"""

    def __init__(self, session_factory: Callable[[], AbstractContextManager[Session]]) -> None:
        self.session_factory = session_factory

    def previous_record_count(self, dataset_key: str) -> int | None:
        with self.session_factory() as session:
            statement = (
                select(func.count(PlaceRecord.id))
                .join(DataSourceRecord, PlaceRecord.data_source_id == DataSourceRecord.id)
                .where(DataSourceRecord.dataset_key == dataset_key, PlaceRecord.is_active.is_(True))
            )
            count = session.scalar(statement)
            return int(count) if count else None

    def publish(
        self,
        config: SourceConfig,
        snapshot: RawSnapshot,
        places: list[PlaceDraft],
        quality: QualityReport,
    ) -> int:
        if not quality.accepted:
            raise ValueError("品質閘門未通過，不得發布")
        config_hash = hashlib.sha256(
            json.dumps(config.model_dump(), sort_keys=True).encode("utf-8")
        ).hexdigest()
        with self.session_factory() as session, session.begin():
            source = session.scalar(
                select(DataSourceRecord).where(DataSourceRecord.dataset_key == config.dataset_key)
            )
            if source is None:
                source = DataSourceRecord(
                    dataset_key=config.dataset_key,
                    name=config.name,
                    category=config.category,
                    source_agency=config.source_agency,
                    public_metadata_url=getattr(config, "metadata_url", None),
                    update_frequency=getattr(config, "update_frequency", None),
                    config_version=config_hash,
                )
                session.add(source)
                session.flush()
            run = ImportRunRecord(
                data_source_id=source.id,
                status="validated",
                downloaded_count=quality.record_count,
                valid_count=quality.record_count - quality.invalid_coordinate_count,
                invalid_count=quality.invalid_coordinate_count,
                quality_metrics={
                    "invalid_coordinate_ratio": quality.invalid_coordinate_ratio,
                    "record_count_change_ratio": quality.record_count_change_ratio,
                    "snapshot_hash": snapshot.content_hash,
                },
            )
            session.add(run)
            session.flush()
            existing_raw = session.scalar(
                select(RawImportRecord).where(
                    RawImportRecord.data_source_id == source.id,
                    RawImportRecord.content_hash == snapshot.content_hash,
                )
            )
            if existing_raw is None:
                raw_payload = json.loads(snapshot.payload_path.read_text(encoding="utf-8"))
                session.add(
                    RawImportRecord(
                        data_source_id=source.id,
                        import_run_id=run.id,
                        fetched_at=datetime.fromisoformat(snapshot.fetched_at),
                        content_hash=snapshot.content_hash,
                        raw_data=raw_payload,
                        record_count=quality.record_count,
                        import_status="validated",
                    )
                )
            external_ids = [place.external_id for place in places]
            now = datetime.now(UTC)
            place_values: list[dict[str, object]] = []
            for place in places:
                values = {
                    "data_source_id": source.id,
                    "external_id": place.external_id,
                    "name": place.name,
                    "normalized_name": _normalized(place.name),
                    "category": place.category.value,
                    "subcategory": place.subcategory,
                    "address": place.address,
                    "normalized_address": _normalized(place.address),
                    "city": place.city,
                    "district": place.district,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "geom": (
                        func.ST_GeogFromText(f"SRID=4326;POINT({place.longitude} {place.latitude})")
                        if place.latitude is not None and place.longitude is not None
                        else None
                    ),
                    "phone": place.phone,
                    "location_accuracy": place.location_accuracy.value,
                    "properties": place.properties,
                    "canonical_group_key": place.canonical_group_key,
                    "last_synced_at": now,
                    "is_active": True,
                }
                place_values.append(values)
            for start in range(0, len(place_values), 1000):
                batch = place_values[start : start + 1000]
                statement = insert(PlaceRecord).values(batch)
                statement = statement.on_conflict_do_update(
                    constraint="places_data_source_id_external_id_key",
                    set_={
                        key: getattr(statement.excluded, key)
                        for key in batch[0]
                        if key not in {"data_source_id", "external_id"}
                    },
                )
                session.execute(statement)
            session.query(PlaceRecord).filter(
                PlaceRecord.data_source_id == source.id,
                PlaceRecord.external_id.not_in(external_ids),
            ).update({PlaceRecord.is_active: False}, synchronize_session=False)
            run.status = "published"
            run.published_count = len(places)
            run.finished_at = now
        return len(places)
