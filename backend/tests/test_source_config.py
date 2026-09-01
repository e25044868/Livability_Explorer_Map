from pathlib import Path

import pytest
from app.sources.config import DownloadConfig, load_source_config
from pydantic import ValidationError


def test_project_parking_config_loads() -> None:
    config = load_source_config(Path("data_sources/parking_kaohsiung.yaml"))
    assert config.dataset_key == "kcg_public_offstreet_parking"
    assert config.download.allowed_hosts == ["openapi.kcg.gov.tw"]


def test_tourism_facilities_config_loads() -> None:
    config = load_source_config(Path("data_sources/tourism_facilities_taiwan.yaml"))
    assert config.dataset_key == "tourism_facilities_taiwan"
    assert config.category == "tourism_facility"
    assert config.download.encoding == "utf-8-sig"


def test_download_config_rejects_non_https_and_credentials() -> None:
    with pytest.raises(ValidationError):
        DownloadConfig(
            url="http://example.gov.tw/data",
            allowed_hosts=["example.gov.tw"],
            format="json",
        )
    with pytest.raises(ValidationError):
        DownloadConfig(
            url="https://user:secret@example.gov.tw/data",
            allowed_hosts=["example.gov.tw"],
            format="json",
        )
