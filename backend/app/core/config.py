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
    database_url: str = "sqlite:///./mapping_paris_strava_b2.db"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
