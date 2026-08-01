from app.main import create_app
from app.settings import Settings
from fastapi.testclient import TestClient


def test_production_can_disable_api_documentation() -> None:
    app = create_app(settings=Settings(enable_api_docs=False))
    client = TestClient(app)
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_env_example_parses_cors_allowlist() -> None:
    settings = Settings(_env_file=".env.example")
    assert settings.cors_allowed_origins == ["http://localhost:5173"]
