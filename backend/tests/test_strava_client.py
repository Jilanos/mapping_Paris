import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.services.strava_client import StravaClient  # noqa: E402


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        strava_client_id="example-client-id",
        strava_client_secret="example-client-secret",
        strava_token_url="https://www.strava.com/oauth/token",
    )


def test_exchange_code_for_token_maps_strava_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://www.strava.com/oauth/token"
        body = request.content.decode("utf-8")
        assert "grant_type=authorization_code" in body
        assert "code=example-code" in body
        return httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_at": 1893456000,
                "scope": "read,activity:read_all",
                "token_type": "Bearer",
                "athlete": {"id": 12345},
            },
        )

    client = StravaClient(_settings(), httpx.Client(transport=httpx.MockTransport(handler)))

    token = client.exchange_code_for_token("example-code")

    assert token.access_token == "new-access"
    assert token.refresh_token == "new-refresh"
    assert token.athlete_id == "12345"


def test_refresh_access_token_maps_strava_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode("utf-8")
        assert "grant_type=refresh_token" in body
        assert "refresh_token=old-refresh" in body
        return httpx.Response(
            200,
            json={
                "access_token": "refreshed-access",
                "refresh_token": "refreshed-refresh",
                "expires_at": 1893456000,
                "scope": "read,activity:read_all",
                "token_type": "Bearer",
            },
        )

    client = StravaClient(_settings(), httpx.Client(transport=httpx.MockTransport(handler)))

    token = client.refresh_access_token("old-refresh")

    assert token.access_token == "refreshed-access"
    assert token.refresh_token == "refreshed-refresh"
