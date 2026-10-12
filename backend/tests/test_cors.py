import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

from app.core.config import Settings, settings


def create_app_with_cors(app_settings: Settings) -> FastAPI:
    app = FastAPI(title="TestApp")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=app_settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app


def test_cors_default_origins():
    """Verify default CORS origins contain production and local dev origins without trailing slashes."""
    origins = settings.cors_origins
    assert "https://contest-mind.vercel.app" in origins
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "http://localhost:8000" in origins
    assert "http://127.0.0.1:8000" in origins
    for origin in origins:
        assert not origin.endswith("/"), f"Origin '{origin}' should not end with a trailing slash"


def test_cors_parsing_variations():
    """Verify comma-separated and JSON string formats from environment variables are parsed correctly."""
    # Comma-separated with whitespace and trailing slash
    custom_settings_csv = Settings(
        BACKEND_CORS_ORIGINS="https://contest-mind.vercel.app/ , http://localhost:3000/ "
    )
    assert custom_settings_csv.cors_origins == [
        "https://contest-mind.vercel.app",
        "http://localhost:3000",
    ]

    # JSON array string with trailing slash
    custom_settings_json = Settings(
        BACKEND_CORS_ORIGINS='["https://contest-mind.vercel.app/", "http://localhost:3000"]'
    )
    assert custom_settings_json.cors_origins == [
        "https://contest-mind.vercel.app",
        "http://localhost:3000",
    ]


def test_cors_allowed_origins_receive_allow_header():
    """Verify allowed origins receive Access-Control-Allow-Origin."""
    app = create_app_with_cors(settings)
    client = TestClient(app)

    # Production frontend
    res = client.get("/api/v1/health", headers={"Origin": "https://contest-mind.vercel.app"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://contest-mind.vercel.app"

    # Local development frontend
    res_local = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert res_local.status_code == 200
    assert res_local.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_disallowed_origin_blocked():
    """Verify disallowed origins do NOT receive Access-Control-Allow-Origin header."""
    app = create_app_with_cors(settings)
    client = TestClient(app)

    # Disallowed attacker origin
    res = client.get("/api/v1/health", headers={"Origin": "https://attacker-website.com"})
    assert res.status_code == 200
    assert "access-control-allow-origin" not in res.headers


def test_cors_preflight_options():
    """Verify OPTIONS preflight requests for allowed vs disallowed origins."""
    app = create_app_with_cors(settings)
    client = TestClient(app)

    # Preflight from allowed origin
    res_allowed = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://contest-mind.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_allowed.status_code == 200
    assert res_allowed.headers.get("access-control-allow-origin") == "https://contest-mind.vercel.app"

    # Preflight from disallowed origin
    res_disallowed = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://malicious.org",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Disallowed origin does not receive Access-Control-Allow-Origin
    assert "access-control-allow-origin" not in res_disallowed.headers


def test_cors_credentials_disabled_by_default():
    """Verify allow_credentials is not set to true when CORS_ALLOW_CREDENTIALS is False."""
    assert settings.CORS_ALLOW_CREDENTIALS is False
    app = create_app_with_cors(settings)
    client = TestClient(app)

    res = client.get("/api/v1/health", headers={"Origin": "https://contest-mind.vercel.app"})
    assert res.headers.get("access-control-allow-credentials") != "true"
