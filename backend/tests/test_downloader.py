import asyncio

import httpx
import pytest
from app.sources.config import SourceConfig
from app.sources.downloader import (
    DownloadRejectedError,
    DownloadTooLargeError,
    download_source,
    validate_public_addresses,
)


def source_config(max_bytes: int = 1000) -> SourceConfig:
    return SourceConfig.model_validate(
        {
            "dataset_key": "test",
            "dataset_id": "1",
            "name": "test",
            "category": "parking",
            "source_agency": "test",
            "download": {
                "url": "https://data.example.gov.tw/source.json",
                "allowed_hosts": ["data.example.gov.tw"],
                "format": "json",
                "max_bytes": max_bytes,
            },
            "quality_gates": {
                "minimum_records": 1,
                "maximum_invalid_coordinate_ratio": 0.1,
                "maximum_record_count_change_ratio": 0.5,
            },
        }
    )


def test_private_dns_address_is_rejected() -> None:
    with pytest.raises(DownloadRejectedError, match="非公開 IP"):
        validate_public_addresses("data.example.gov.tw", lambda _: ["127.0.0.1"])


def test_bounded_json_download_succeeds() -> None:
    async def run() -> bytes:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=b'{"data":[]}',
                request=request,
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            result = await download_source(
                source_config(), client=client, resolver=lambda _: ["8.8.8.8"]
            )
        return result.content

    assert asyncio.run(run()) == b'{"data":[]}'


def test_declared_oversized_download_is_rejected() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                headers={"content-type": "application/json", "content-length": "999"},
                content=b"{}",
                request=request,
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await download_source(
                source_config(max_bytes=10), client=client, resolver=lambda _: ["8.8.8.8"]
            )

    with pytest.raises(DownloadTooLargeError):
        asyncio.run(run())


def test_redirect_is_not_followed() -> None:
    async def run() -> None:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                302,
                headers={"location": "https://evil.example/data"},
                request=request,
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            await download_source(source_config(), client=client, resolver=lambda _: ["8.8.8.8"])

    with pytest.raises(DownloadRejectedError, match="重新導向"):
        asyncio.run(run())
