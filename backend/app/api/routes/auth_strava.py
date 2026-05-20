from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.crypto import EncryptionConfigError
from app.db.models import StravaToken
from app.db.session import get_db
from app.schemas.strava import AuthStatusResponse, OAuthSuccessResponse, RefreshSuccessResponse
from app.services.auth_state_store import AuthStateStore
from app.services.strava_client import StravaClient, StravaClientError, get_strava_client
from app.services.token_store import TokenStore

router = APIRouter(prefix="/auth/strava", tags=["strava-auth"])


def _require_start_config(settings: Settings) -> None:
    if not settings.strava_client_id.strip() or not settings.strava_redirect_uri.strip():
        raise HTTPException(
            status_code=503,
            detail="Strava OAuth start requires STRAVA_CLIENT_ID and STRAVA_REDIRECT_URI",
        )


def _require_oauth_config(settings: Settings) -> None:
    if not settings.strava_configured:
        raise HTTPException(
            status_code=503,
            detail="Strava OAuth requires STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REDIRECT_URI",
        )


@router.get("/start")
def start_strava_auth(db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    _require_start_config(settings)
    auth_state = AuthStateStore(db).create(settings.auth_state_ttl_seconds)
    params = {
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": settings.strava_scopes,
        "state": auth_state.state,
    }
    return RedirectResponse(f"{settings.strava_authorize_url}?{urlencode(params)}")


@router.get("/callback", response_model=OAuthSuccessResponse)
def strava_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
    strava_client: StravaClient = Depends(get_strava_client),
) -> OAuthSuccessResponse:
    if error:
        raise HTTPException(status_code=400, detail="Strava authorization was denied")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Strava callback requires code and state")
    settings = get_settings()
    _require_oauth_config(settings)
    if AuthStateStore(db).consume_valid(state) is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    try:
        token_response = strava_client.exchange_code_for_token(code)
        TokenStore(db, settings).save(token_response)
    except EncryptionConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StravaClientError as exc:
        raise HTTPException(status_code=502, detail="Strava token exchange failed") from exc
    return OAuthSuccessResponse()


@router.post("/refresh", response_model=RefreshSuccessResponse)
def refresh_strava_token(
    db: Session = Depends(get_db),
    strava_client: StravaClient = Depends(get_strava_client),
) -> RefreshSuccessResponse:
    settings = get_settings()
    _require_oauth_config(settings)
    try:
        token_store = TokenStore(db, settings)
        refresh_token = token_store.get_refresh_token()
        if refresh_token is None:
            raise HTTPException(status_code=404, detail="No Strava token is stored")
        token_store.save(strava_client.refresh_access_token(refresh_token))
    except EncryptionConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StravaClientError as exc:
        raise HTTPException(status_code=502, detail="Strava token refresh failed") from exc
    return RefreshSuccessResponse()


@router.get("/status", response_model=AuthStatusResponse)
def strava_status(db: Session = Depends(get_db)) -> AuthStatusResponse:
    settings = get_settings()
    latest = db.query(StravaToken).order_by(
        StravaToken.updated_at.desc(),
        StravaToken.id.desc(),
    ).first()
    return AuthStatusResponse(
        configured=settings.strava_configured,
        connected=latest is not None,
        expires_at=latest.expires_at if latest is not None else None,
        scope=latest.scope if latest is not None else None,
    )
