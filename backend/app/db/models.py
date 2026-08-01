from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import UserDefinedType


class GeographyPoint(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw: object) -> str:
        return "geography(Point,4326)"


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON().with_variant(JSONB, "postgresql")}


class DataSourceRecord(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    source_agency: Mapped[str] = mapped_column(String, nullable=False)
    public_metadata_url: Mapped[str | None] = mapped_column(Text)
    update_frequency: Mapped[str | None] = mapped_column(String)
    license_name: Mapped[str | None] = mapped_column(String)
    config_version: Mapped[str] = mapped_column(String, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ImportRunRecord(Base):
    __tablename__ = "import_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, nullable=False)
    downloaded_count: Mapped[int | None] = mapped_column(Integer)
    valid_count: Mapped[int | None] = mapped_column(Integer)
    invalid_count: Mapped[int | None] = mapped_column(Integer)
    published_count: Mapped[int | None] = mapped_column(Integer)
    quality_metrics: Mapped[dict[str, Any]] = mapped_column(default=dict, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)


class RawImportRecord(Base):
    __tablename__ = "raw_imports"
    __table_args__ = (UniqueConstraint("data_source_id", "content_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    import_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("import_runs.id"), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    raw_data: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    import_status: Mapped[str] = mapped_column(String, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String)
    error_message: Mapped[str | None] = mapped_column(Text)


class PlaceRecord(Base):
    __tablename__ = "places"
    __table_args__ = (UniqueConstraint("data_source_id", "external_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, default=uuid.uuid4
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    subcategory: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(Text)
    normalized_address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String)
    district: Mapped[str | None] = mapped_column(String)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    geom: Mapped[object | None] = mapped_column(GeographyPoint())
    phone: Mapped[str | None] = mapped_column(String)
    opening_hours: Mapped[str | None] = mapped_column(Text)
    location_accuracy: Mapped[str] = mapped_column(String, nullable=False)
    properties: Mapped[dict[str, Any]] = mapped_column(default=dict, nullable=False)
    canonical_group_key: Mapped[str | None] = mapped_column(String)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
