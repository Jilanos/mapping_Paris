import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402


def test_default_settings_load_without_real_secrets(monkeypatch) -> None:
    for name in (
        "APP_NAME",
        "APP_VERSION",
        "ENV",
        "LOG_LEVEL",
        "API_BASE_URL",
        "STRAVA_CLIENT_ID",
        "STRAVA_CLIENT_SECRET",
        "STRAVA_REDIRECT_URI",
        "STRAVA_SCOPES",
        "STRAVA_AUTHORIZE_URL",
        "STRAVA_TOKEN_URL",
        "AUTH_STATE_TTL_SECONDS",
        "TOKEN_ENCRYPTION_KEY",
        "DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "mapping-paris-strava-b2"
    assert settings.app_version == "0.1.0"
    assert settings.env == "local"
    assert settings.log_level == "INFO"
    assert settings.database_url == "sqlite:///./mapping_paris_strava_b2.db"
    assert settings.strava_client_id == ""
    assert settings.strava_client_secret == ""
    assert settings.strava_redirect_uri == ""
    assert settings.strava_scopes == "read,activity:read_all"
    assert settings.strava_authorize_url == "https://www.strava.com/oauth/authorize"
    assert settings.strava_token_url == "https://www.strava.com/oauth/token"
    assert settings.auth_state_ttl_seconds == 600
    assert settings.token_encryption_key == ""


def test_strava_configured_is_false_when_values_are_missing() -> None:
    settings = Settings(
        _env_file=None,
        strava_client_id="example-client-id",
        strava_client_secret="",
        strava_redirect_uri="http://localhost:8000/auth/strava/callback",
    )

    assert settings.strava_configured is False


def test_strava_configured_is_true_when_required_values_are_environment_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv("STRAVA_CLIENT_ID", "example-client-id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "example-client-secret")
    monkeypatch.setenv(
        "STRAVA_REDIRECT_URI",
        "http://localhost:8000/auth/strava/callback",
    )

    settings = Settings(_env_file=None)

    assert settings.strava_configured is True
