from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from app.sources.downloader import system_trust_context

TOKEN_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
PARKING_URL = "https://tdx.transportdata.tw/api/basic/v1/Parking/OffStreet/CarPark/City/{city}"
AVAILABILITY_URL = (
    "https://tdx.transportdata.tw/api/basic/v1/Parking/OffStreet/ParkingAvailability/City/{city}"
)
BIKE_STATION_URL = "https://tdx.transportdata.tw/api/basic/v2/Bike/Station/City/{city}"
BIKE_AVAILABILITY_URL = "https://tdx.transportdata.tw/api/basic/v2/Bike/Availability/City/{city}"


@dataclass(frozen=True, slots=True)
class TdxCredentials:
    client_id: str
    client_secret: str


class TdxParkingClient:
    def __init__(
        self, credentials: TdxCredentials, client: httpx.AsyncClient | None = None
    ) -> None:
        self.credentials = credentials
        self.client = client

    async def fetch_city(self, city: str) -> bytes:
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(
            timeout=httpx.Timeout(30), trust_env=False, verify=system_trust_context()
        )
        try:
            token_response = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret,
                },
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise RuntimeError("TDX token 回應缺少 access_token")
            response = await client.get(
                PARKING_URL.format(city=city),
                params={"$format": "JSON"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.content
        finally:
            if owns_client:
                await client.aclose()


    async def fetch_city_with_availability(self, city: str) -> tuple[bytes, bytes]:
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(
            timeout=httpx.Timeout(30), trust_env=False, verify=system_trust_context()
        )
        try:
            token_response = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.credentials.client_id,
                    "client_secret": self.credentials.client_secret,
                },
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            token_response.raise_for_status()
            token = token_response.json().get("access_token")
            if not token:
                raise RuntimeError("TDX token 回應缺少 access_token")
            headers = {"Authorization": f"Bearer {token}"}
            basic, live = await asyncio.gather(
                client.get(
                    PARKING_URL.format(city=city), params={"$format": "JSON"}, headers=headers
                ),
                client.get(
                    AVAILABILITY_URL.format(city=city), params={"$format": "JSON"}, headers=headers
                ),
            )
            basic.raise_for_status()
            live.raise_for_status()
            return basic.content, live.content
        finally:
            if owns_client:
                await client.aclose()


class TdxBikeClient(TdxParkingClient):
    def __init__(
        self, credentials: TdxCredentials, client: httpx.AsyncClient | None = None
    ) -> None:
        super().__init__(credentials, client)
        self._access_token: str | None = None

    async def fetch_city_with_availability(self, city: str) -> tuple[bytes, bytes]:
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(
            timeout=httpx.Timeout(30), trust_env=False, verify=system_trust_context()
        )
        try:
            headers = {"Authorization": f"Bearer {await self._get_access_token(client)}"}
            stations = await client.get(
                BIKE_STATION_URL.format(city=city),
                params={"$format": "JSON"},
                headers=headers,
            )
            stations.raise_for_status()
            # Keep periodic imports well below TDX's per-source burst limits.
            await asyncio.sleep(1.1)
            availability = await client.get(
                BIKE_AVAILABILITY_URL.format(city=city),
                params={"$format": "JSON"},
                headers=headers,
            )
            availability.raise_for_status()
            return stations.content, availability.content
        finally:
            if owns_client:
                await client.aclose()

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        if self._access_token:
            return self._access_token
        token_response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
            },
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise RuntimeError("TDX token 回應缺少 access_token")
        self._access_token = access_token
        return access_token
