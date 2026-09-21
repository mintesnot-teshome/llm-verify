"""Tests for API authentication, rate limiting, and SSRF defenses."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from starlette.requests import Request

from src.config import Settings, get_settings
from src.main import app
from src.security import require_api_access, validate_outbound_api_url


def _request() -> Request:
    return Request({"type": "http", "client": ("203.0.113.10", 12345)})


def test_api_routes_are_protected_but_health_is_public() -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_access_key="route-secret",
        api_requests_per_minute=0,
    )
    try:
        client = TestClient(app)
        assert client.get("/health").status_code == 200
        response = client.get("/api/v1/benchmarks/")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_access_requires_valid_bearer_key() -> None:
    settings = Settings(api_access_key="correct", api_requests_per_minute=0)

    with pytest.raises(HTTPException) as missing:
        await require_api_access(_request(), None, settings)
    with pytest.raises(HTTPException) as invalid:
        await require_api_access(
            _request(),
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong"),
            settings,
        )

    assert missing.value.status_code == 401
    assert invalid.value.status_code == 401
    await require_api_access(
        _request(),
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="correct"),
        settings,
    )


@pytest.mark.asyncio
async def test_api_access_is_rate_limited() -> None:
    key = f"test-{uuid4()}"
    settings = Settings(api_access_key=key, api_requests_per_minute=1)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=key)

    await require_api_access(_request(), credentials, settings)
    with pytest.raises(HTTPException) as limited:
        await require_api_access(_request(), credentials, settings)

    assert limited.value.status_code == 429
    assert "Retry-After" in limited.value.headers


def test_custom_api_hosts_must_be_explicitly_allowed() -> None:
    settings = Settings()

    with pytest.raises(ValueError, match="ALLOWED_API_HOSTS"):
        validate_outbound_api_url("https://api.example.com/v1", settings)

    trusted = Settings(allowed_api_hosts="api.example.com,localhost")
    validate_outbound_api_url("https://api.example.com/v1", trusted)
    validate_outbound_api_url("http://localhost:11434/v1", trusted)


def test_outbound_api_url_rejects_unsafe_shapes() -> None:
    settings = Settings(allowed_api_hosts="api.example.com")

    for url in (
        "file:///etc/passwd",
        "https://user:password@api.example.com/v1",
        "https://api.example.com/v1?redirect=http://localhost",
    ):
        with pytest.raises(ValueError):
            validate_outbound_api_url(url, settings)
