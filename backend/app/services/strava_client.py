import httpx

from app.core.config import Settings, get_settings
from app.schemas.strava import StravaTokenResponse


class StravaClientError(RuntimeError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        rate_limit: dict[str, str | None] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.rate_limit = rate_limit or {}


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

    def list_activities(
        self,
        access_token: str,
        page: int,
        per_page: int,
        after: int | None = None,
        before: int | None = None,
    ) -> list[dict]:
        params: dict[str, int] = {
            "page": page,
            "per_page": per_page,
        }
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        response = self._get(
            "https://www.strava.com/api/v3/athlete/activities",
            access_token,
            params=params,
        )
        return response.json()

    def get_activity_streams(self, access_token: str, activity_id: str | int) -> dict:
        response = self._get(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            access_token,
            params={
                "keys": "latlng,distance,time",
                "key_by_type": "true",
            },
        )
        return response.json()

    def _post_token(self, data: dict[str, str]) -> StravaTokenResponse:
        try:
            response = self._http_client.post(self._settings.strava_token_url, data=data)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise self._to_client_error("Strava token request failed", exc) from exc
        return StravaTokenResponse.model_validate(response.json())

    def _get(
        self,
        url: str,
        access_token: str,
        params: dict[str, int | str],
    ) -> httpx.Response:
        try:
            response = self._http_client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise self._to_client_error("Strava API request failed", exc) from exc
        return response

    def _to_client_error(self, message: str, exc: httpx.HTTPError) -> StravaClientError:
        response = getattr(exc, "response", None)
        return StravaClientError(
            message,
            status_code=response.status_code if response is not None else None,
            rate_limit=self._rate_limit_headers(response) if response is not None else {},
        )

    def _rate_limit_headers(self, response: httpx.Response) -> dict[str, str | None]:
        return {
            "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
            "X-RateLimit-Usage": response.headers.get("X-RateLimit-Usage"),
            "X-ReadRateLimit-Limit": response.headers.get("X-ReadRateLimit-Limit"),
            "X-ReadRateLimit-Usage": response.headers.get("X-ReadRateLimit-Usage"),
        }


def get_strava_client() -> StravaClient:
    return StravaClient(get_settings())
