from datetime import UTC, datetime

from pydantic import BaseModel, Field


class StravaAthlete(BaseModel):
    id: int | None = None


class StravaTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int
    scope: str = ""
    token_type: str = "Bearer"
    athlete: StravaAthlete | None = None

    @property
    def expires_at_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.expires_at, tz=UTC)

    @property
    def athlete_id(self) -> str | None:
        if self.athlete is None or self.athlete.id is None:
            return None
        return str(self.athlete.id)


class AuthStatusResponse(BaseModel):
    configured: bool
    connected: bool
    expires_at: datetime | None = None
    scope: str | None = None


class OAuthSuccessResponse(BaseModel):
    status: str = Field(default="connected")
    connected: bool = True


class RefreshSuccessResponse(BaseModel):
    status: str = Field(default="refreshed")
    connected: bool = True
