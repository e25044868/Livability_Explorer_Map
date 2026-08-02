from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import httpx

from app.cli.publish_tdx_bike import CITY_NAMES, PROJECT_ROOT, publish_city
from app.settings import Settings
from app.sources.downloader import system_trust_context
from app.sources.tdx import TdxBikeClient, TdxCredentials

BIKE_CITY_CODES = (
    "Taipei",
    "NewTaipei",
    "Taoyuan",
    "Hsinchu",
    "MiaoliCounty",
    "Taichung",
    "ChanghuaCounty",
    "YunlinCounty",
    "Chiayi",
    "Tainan",
    "Kaohsiung",
    "PingtungCounty",
)


async def publish_many(
    cities: list[str], snapshot_root: Path, delay_seconds: float
) -> list[dict[str, object]]:
    settings = Settings()
    if not settings.tdx_client_id or not settings.tdx_client_secret:
        raise RuntimeError("請先設定 TDX_CLIENT_ID 與 TDX_CLIENT_SECRET")
    results: list[dict[str, object]] = []
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30), trust_env=False, verify=system_trust_context()
    ) as http_client:
        bike_client = TdxBikeClient(
            TdxCredentials(settings.tdx_client_id, settings.tdx_client_secret), http_client
        )
        for index, city in enumerate(cities):
            if index:
                await asyncio.sleep(delay_seconds)
            try:
                results.append(await publish_city(city, snapshot_root, bike_client))
            except httpx.HTTPStatusError as error:
                if error.response.status_code in {400, 404}:
                    results.append(
                        {
                            "city": city,
                            "status": "skipped",
                            "reason": "TDX 沒有提供此縣市公共自行車資料",
                        }
                    )
                    continue
                if error.response.status_code == 429:
                    results.append(
                        {
                            "city": city,
                            "status": "paused",
                            "reason": "TDX 暫時限制請求，請稍後從此縣市續跑",
                        }
                    )
                    break
                raise
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="批次發布 TDX 公共自行車站")
    parser.add_argument("--all", action="store_true", help="逐一發布已知提供公共自行車資料的縣市")
    parser.add_argument("cities", nargs="*", choices=sorted(CITY_NAMES))
    parser.add_argument("--snapshot-root", type=Path, default=PROJECT_ROOT / "data" / "raw")
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=65,
        help="全國批次每個縣市之間的等待秒數，預設 65 秒以避免 TDX 節流",
    )
    args = parser.parse_args()
    if args.all and args.cities:
        parser.error("--all 不能與指定縣市同時使用")
    if not args.all and not args.cities:
        parser.error("請指定 --all 或至少一個縣市")
    if args.delay_seconds < 60 and args.all:
        parser.error("--all 的 delay-seconds 不得小於 60，以避免 TDX 節流")
    cities = list(BIKE_CITY_CODES) if args.all else args.cities
    print(
        json.dumps(
            asyncio.run(publish_many(cities, args.snapshot_root, args.delay_seconds)),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
