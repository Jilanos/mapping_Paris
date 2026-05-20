from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "mapping-paris-strava-b2"
    app_version: str = "0.1.0"
    env: str = "local"
    strava_client_id: str = ""
    strava_client_secret: str = ""

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )


settings = Settings()
