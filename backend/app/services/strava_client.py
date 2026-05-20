import httpx

from app.core.config import Settings, get_settings
from app.schemas.strava import StravaTokenResponse


class StravaClientError(RuntimeError):
    pass


class StravaClient:
    def __init__(
        self,
        settings: Settings,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._http_client = http_client or httpx.Client(timeout=10.0)

    def exchange_code_for_token(self, code: str) -> StravaTokenResponse:
        return self._post_token(
            {
                "client_id": self._settings.strava_client_id,
                "client_secret": self._settings.strava_client_secret,
                "code": code,
                "grant_type": "authorization_code",
            }
        )

    def refresh_access_token(self, refresh_token: str) -> StravaTokenResponse:
        return self._post_token(
            {
                "client_id": self._settings.strava_client_id,
                "client_secret": self._settings.strava_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        )

    def _post_token(self, data: dict[str, str]) -> StravaTokenResponse:
        try:
            response = self._http_client.post(self._settings.strava_token_url, data=data)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise StravaClientError("Strava token request failed") from exc
        return StravaTokenResponse.model_validate(response.json())


def get_strava_client() -> StravaClient:
    return StravaClient(get_settings())
