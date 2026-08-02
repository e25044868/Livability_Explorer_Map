from __future__ import annotations

import uuid
from typing import cast

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from app.api.queries import PlaceQuery, validate_place_query
from app.api.repository import EmptyPlaceReadRepository, PlaceReadRepository
from app.api.schemas import (
    AdministrativeAreaResponse,
    CategoryResponse,
    ErrorResponse,
    GeocodeResultResponse,
    NearbySummaryResponse,
    PlaceListResponse,
    PlaceSummaryResponse,
)
from app.db.read_repository import PostgresPlaceReadRepository
from app.domain.models import PlaceCategory
from app.services.geocoding import administrative_area, geocode_landmarks
from app.settings import Settings

CATEGORY_LABELS = {
    PlaceCategory.PARKING: "停車場",
    PlaceCategory.TOILET: "公廁",
    PlaceCategory.AED: "AED",
    PlaceCategory.PHARMACY: "藥局",
    PlaceCategory.MEDICAL: "醫療院所",
    PlaceCategory.MOTORCYCLE_CHARGING: "機車充電",
    PlaceCategory.DRINKING_WATER: "飲水機",
    PlaceCategory.SHELTER: "避難收容處所",
    PlaceCategory.PUBLIC_WIFI: "公共免費 Wi-Fi",
    PlaceCategory.RESCUE_UNIT: "消防／救援據點",
    PlaceCategory.POLICE: "警察機關／派出所",
}


def create_app(
    repository: PlaceReadRepository | None = None,
    *,
    settings: Settings | None = None,
) -> FastAPI:
    active_settings = settings or Settings()
    docs_url = "/docs" if active_settings.enable_api_docs else None
    app = FastAPI(
        title="生活機能探索地圖 API",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url="/redoc" if active_settings.enable_api_docs else None,
        openapi_url="/openapi.json" if active_settings.enable_api_docs else None,
    )
    active_repository = repository or EmptyPlaceReadRepository()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    def get_repository() -> PlaceReadRepository:
        return active_repository

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error="invalid_request",
                message=str(exc.detail),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first_error = exc.errors()[0] if exc.errors() else {}
        message = str(first_error.get("msg", "輸入驗證失敗"))
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="validation_error",
                message=message,
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    @app.get("/api/categories", response_model=list[CategoryResponse])
    async def categories_endpoint() -> list[CategoryResponse]:
        return [
            CategoryResponse(key=category.value, label=label)
            for category, label in CATEGORY_LABELS.items()
        ]

    @app.get("/api/districts", response_model=list[str])
    async def districts_endpoint(
        city: str = Query(min_length=2, max_length=20),
        repo: PlaceReadRepository = Depends(get_repository),
    ) -> list[str]:
        return await repo.list_districts(city)

    @app.get("/api/places", response_model=PlaceListResponse)
    async def places_endpoint(
        lat: float | None = None,
        lng: float | None = None,
        radius: int | None = None,
        north: float | None = None,
        south: float | None = None,
        east: float | None = None,
        west: float | None = None,
        city: str | None = None,
        district: str | None = None,
        categories: str | None = None,
        keyword: str | None = None,
        limit: int = 300,
        repo: PlaceReadRepository = Depends(get_repository),
    ) -> PlaceListResponse:
        query = validate_place_query(
            lat=lat,
            lng=lng,
            radius=radius,
            north=north,
            south=south,
            east=east,
            west=west,
            city=city,
            district=district,
            categories=categories,
            keyword=keyword,
            limit=limit,
        )
        items, version = await repo.list_places(query)
        return PlaceListResponse(
            items=items,
            count=len(items),
            limit=query.limit,
            data_version=version,
        )

    @app.get("/api/places/{public_id}", response_model=PlaceSummaryResponse)
    async def place_detail_endpoint(
        public_id: str,
        repo: PlaceReadRepository = Depends(get_repository),
    ) -> PlaceSummaryResponse:
        place = await repo.get_place(public_id)
        if place is None:
            raise HTTPException(404, "找不到設施")
        return place

    @app.get("/api/nearby-summary", response_model=NearbySummaryResponse)
    async def nearby_summary_endpoint(
        lat: float,
        lng: float,
        radius: int = Query(ge=1, le=3000),
        repo: PlaceReadRepository = Depends(get_repository),
    ) -> NearbySummaryResponse:
        query: PlaceQuery = validate_place_query(lat=lat, lng=lng, radius=radius)
        summary, version = await repo.nearby_summary(
            cast(float, query.lat), cast(float, query.lng), cast(int, query.radius)
        )
        return NearbySummaryResponse(radius_meters=radius, summary=summary, data_version=version)

    @app.get("/api/search", response_model=PlaceListResponse)
    async def search_endpoint(
        keyword: str,
        categories: str | None = None,
        limit: int = Query(default=30, ge=1, le=100),
        repo: PlaceReadRepository = Depends(get_repository),
    ) -> PlaceListResponse:
        query = validate_place_query(keyword=keyword, categories=categories, limit=limit)
        items, version = await repo.list_places(query)
        return PlaceListResponse(items=items, count=len(items), limit=limit, data_version=version)

    @app.get("/api/administrative-area", response_model=AdministrativeAreaResponse)
    async def administrative_area_endpoint(lat: float, lng: float) -> AdministrativeAreaResponse:
        try:
            city, district = await administrative_area(lat, lng)
        except Exception as exc:
            raise HTTPException(502, f"行政區判定暫時無法使用：{exc}") from exc
        return AdministrativeAreaResponse(city=city, district=district)

    @app.get("/api/geocode", response_model=list[GeocodeResultResponse])
    async def geocode_endpoint(
        keyword: str = Query(min_length=2, max_length=100),
    ) -> list[GeocodeResultResponse]:
        try:
            return [GeocodeResultResponse(**row) for row in await geocode_landmarks(keyword)]
        except Exception as exc:
            raise HTTPException(502, "地址搜尋服務暫時無法使用") from exc

    return app


def create_runtime_app() -> FastAPI:
    settings = Settings()
    repository: PlaceReadRepository | None = None
    if settings.database_url:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        repository = PostgresPlaceReadRepository(async_sessionmaker(engine, expire_on_commit=False))
    return create_app(repository, settings=settings)


app = create_runtime_app()
