from app.main import create_app
from fastapi.testclient import TestClient


def test_places_rejects_unconditional_download() -> None:
    client = TestClient(create_app())
    response = client.get("/api/places")
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_request"


def test_places_allows_district_and_never_exceeds_requested_limit() -> None:
    client = TestClient(create_app())
    response = client.get("/api/places", params={"district": "新興區", "limit": 300})
    assert response.status_code == 200
    assert response.json() == {"items": [], "count": 0, "limit": 300, "data_version": "empty"}


def test_categories_use_motorcycle_charging_label() -> None:
    client = TestClient(create_app())
    response = client.get("/api/categories")
    labels = {item["key"]: item["label"] for item in response.json()}
    assert labels["motorcycle_charging"] == "機車充電"
    assert "charging_station" not in labels


def test_districts_returns_an_empty_list_when_no_data_is_available() -> None:
    client = TestClient(create_app())
    response = client.get("/api/districts", params={"city": "高雄市"})
    assert response.status_code == 200
    assert response.json() == []


def test_search_rejects_one_character_keyword() -> None:
    client = TestClient(create_app())
    response = client.get("/api/search", params={"keyword": "醫"})
    assert response.status_code == 400


def test_missing_detail_uses_uniform_error_json() -> None:
    client = TestClient(create_app())
    response = client.get("/api/places/not-found")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "invalid_request"
    assert body["message"] == "找不到設施"
    assert body["request_id"]
    assert response.headers["X-Request-ID"] == body["request_id"]
