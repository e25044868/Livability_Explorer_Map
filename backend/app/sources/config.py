from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DownloadConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    allowed_hosts: list[str] = Field(min_length=1)
    format: str
    encoding: str = "utf-8"
    timeout_seconds: float = Field(default=30, gt=0, le=60)
    max_bytes: int = Field(default=10_485_760, gt=0, le=50_000_000)

    @field_validator("url")
    @classmethod
    def validate_https_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("download URL 必須是無帳密的 HTTPS URL")
        return value

    @field_validator("allowed_hosts")
    @classmethod
    def normalize_hosts(cls, value: list[str]) -> list[str]:
        hosts = [host.strip().lower().rstrip(".") for host in value]
        if any(not host or ":" in host or "/" in host for host in hosts):
            raise ValueError("allowed_hosts 只能包含主機名稱")
        return hosts


class QualityGateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    minimum_records: int = Field(ge=1)
    maximum_invalid_coordinate_ratio: float = Field(ge=0, le=1)
    maximum_record_count_change_ratio: float = Field(ge=0, le=1)


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    dataset_key: str = Field(min_length=1)
    dataset_id: str
    name: str
    category: str
    source_agency: str
    download: DownloadConfig
    payload_path: str = "data"
    quality_gates: QualityGateConfig

    def ensure_download_host_allowed(self) -> None:
        host = (urlparse(self.download.url).hostname or "").lower().rstrip(".")
        if host not in self.download.allowed_hosts:
            raise ValueError("download URL host 不在 allowed_hosts")


def load_source_config(path: Path) -> SourceConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("資料來源設定根節點必須是 object")
    config = SourceConfig.model_validate(raw)
    config.ensure_download_host_allowed()
    return config
