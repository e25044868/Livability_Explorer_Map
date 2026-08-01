from __future__ import annotations

import ipaddress
import socket
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
import truststore

from app.sources.config import SourceConfig


class DownloadRejectedError(RuntimeError):
    pass


class DownloadTooLargeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DownloadResult:
    content: bytes
    content_type: str
    status_code: int
    final_url: str


Resolver = Callable[[str], list[str]]


def system_trust_context() -> ssl.SSLContext:
    """使用作業系統 CA store；仍維持憑證與 hostname 驗證。"""
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def system_resolver(host: str) -> list[str]:
    return sorted({item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})


def validate_public_addresses(host: str, resolver: Resolver = system_resolver) -> None:
    addresses = resolver(host)
    if not addresses:
        raise DownloadRejectedError("DNS 未回傳可用位址")
    for raw_address in addresses:
        address = ipaddress.ip_address(raw_address)
        if not address.is_global:
            raise DownloadRejectedError(f"host 解析到非公開 IP：{raw_address}")


async def download_source(
    config: SourceConfig,
    *,
    client: httpx.AsyncClient | None = None,
    resolver: Resolver = system_resolver,
) -> DownloadResult:
    config.ensure_download_host_allowed()
    parsed = urlparse(config.download.url)
    host = (parsed.hostname or "").lower().rstrip(".")
    validate_public_addresses(host, resolver)

    owns_client = client is None
    active_client = client or httpx.AsyncClient(
        timeout=httpx.Timeout(config.download.timeout_seconds),
        follow_redirects=False,
        trust_env=False,
        verify=system_trust_context(),
    )
    try:
        async with active_client.stream(
            "GET",
            config.download.url,
            headers={
                "Accept": (
                    "text/csv" if config.download.format.lower() == "csv" else "application/json"
                ),
                "User-Agent": "livability-map-importer/0.1",
            },
        ) as response:
            if 300 <= response.status_code < 400:
                raise DownloadRejectedError("下載端點發生未允許的重新導向")
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            expected_format = config.download.format.lower()
            is_json = "json" in content_type
            # Some audited government portals serve CSV downloads as generic binary.
            # The importer still validates the expected header before publishing.
            is_csv = (
                "csv" in content_type
                or "text/plain" in content_type
                or "application/octet-stream" in content_type
            )
            if (expected_format == "json" and not is_json) or (
                expected_format == "csv" and not is_csv
            ):
                raise DownloadRejectedError(f"回應不是 {expected_format.upper()} content-type")
            declared_length = response.headers.get("content-length")
            if declared_length and int(declared_length) > config.download.max_bytes:
                raise DownloadTooLargeError("Content-Length 超過下載上限")
            chunks: list[bytes] = []
            received = 0
            async for chunk in response.aiter_bytes():
                received += len(chunk)
                if received > config.download.max_bytes:
                    raise DownloadTooLargeError("串流內容超過下載上限")
                chunks.append(chunk)
            return DownloadResult(
                content=b"".join(chunks),
                content_type=content_type,
                status_code=response.status_code,
                final_url=str(response.url),
            )
    finally:
        if owns_client:
            await active_client.aclose()
