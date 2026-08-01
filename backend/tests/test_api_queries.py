import pytest
from app.api.queries import validate_place_query
from fastapi import HTTPException


def test_unconditional_query_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        validate_place_query()
    assert error.value.status_code == 400


def test_partial_center_and_large_viewport_are_rejected() -> None:
    with pytest.raises(HTTPException):
        validate_place_query(lat=22.6, lng=120.3)
    with pytest.raises(HTTPException):
        validate_place_query(north=23.5, south=22.5, east=121, west=120)


def test_categories_are_deduplicated_and_limit_is_bounded() -> None:
    query = validate_place_query(
        city="高雄市",
        categories="parking,toilet,parking",
        limit=500,
    )
    assert query.categories == ("parking", "toilet")
    with pytest.raises(HTTPException):
        validate_place_query(city="高雄市", limit=501)


def test_keyword_must_have_two_characters() -> None:
    with pytest.raises(HTTPException):
        validate_place_query(keyword="醫")
