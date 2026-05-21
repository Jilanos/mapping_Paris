from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "mapping-paris-strava-b2"
    app_version: str = "0.1.0"
    env: str = "local"
    log_level: str = "INFO"
    api_base_url: str = ""
    strava_client_id: str = ""
    strava_client_secret: str = ""
    strava_redirect_uri: str = ""
    strava_scopes: str = "read,activity:read_all"
    strava_authorize_url: str = "https://www.strava.com/oauth/authorize"
    strava_token_url: str = "https://www.strava.com/oauth/token"
    auth_state_ttl_seconds: int = 600
    token_encryption_key: str = ""
    database_url: str = "sqlite:///./mapping_paris_strava_b2.db"
    strava_sync_per_page: int = 30
    strava_sync_max_pages: int = 1
    strava_sync_download_streams: bool = True
    strava_sync_sport_types: str = "Run,Ride"
    strava_token_refresh_margin_seconds: int = 300
    segment_dataset_path: str = "../app/src/main/assets/paris_segments.geojson"
    segment_dataset_version: str = ""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def strava_configured(self) -> bool:
        return all(
            value.strip()
            for value in (
                self.strava_client_id,
                self.strava_client_secret,
                self.strava_redirect_uri,
            )
        )

    @property
    def sync_sport_types(self) -> set[str]:
        return {
            value.strip()
            for value in self.strava_sync_sport_types.split(",")
            if value.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
