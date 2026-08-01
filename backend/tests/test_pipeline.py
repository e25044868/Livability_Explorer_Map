import asyncio
import json
from pathlib import Path

import yaml
from app.importers import pipeline
from app.importers.quality import QualityReport
from app.importers.snapshots import RawSnapshot
from app.sources.config import SourceConfig
from app.sources.downloader import DownloadResult
from pytest import MonkeyPatch


class FakePublisher:
    def __init__(self) -> None:
        self.published = False

    def previous_record_count(self, dataset_key: str) -> int | None:
        return 1

    def publish(
        self,
        config: SourceConfig,
        snapshot: RawSnapshot,
        places: list,
        quality: QualityReport,
    ) -> int:
        self.published = True
        assert snapshot.payload_path.exists()
        assert quality.accepted
        return len(places)


def test_pipeline_snapshots_validates_and_publishes(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    payload = {
        "data": [
            {
                "型式": "平面",
                "行政區": "新興區",
                "場名": "測試停車場",
                "位置": "中正三路1號",
                "緯度": "22.63",
                "經度": "120.30",
                "小車": "10",
            }
        ]
    }
    config = {
        "dataset_key": "test_parking",
        "dataset_id": "1",
        "name": "test",
        "category": "parking",
        "source_agency": "test",
        "download": {
            "url": "https://data.example.gov.tw/source.json",
            "allowed_hosts": ["data.example.gov.tw"],
            "format": "json",
        },
        "payload_path": "data",
        "quality_gates": {
            "minimum_records": 1,
            "maximum_invalid_coordinate_ratio": 0,
            "maximum_record_count_change_ratio": 0.5,
        },
    }
    config_path = tmp_path / "source.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")

    async def fake_download(config: SourceConfig) -> DownloadResult:
        return DownloadResult(
            content=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json",
            status_code=200,
            final_url=config.download.url,
        )

    monkeypatch.setattr(pipeline, "download_source", fake_download)
    publisher = FakePublisher()
    result = asyncio.run(pipeline.import_parking_source(config_path, tmp_path / "raw", publisher))
    assert result.published_count == 1
    assert publisher.published
    assert result.snapshot.payload_path.read_bytes()
