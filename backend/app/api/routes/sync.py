from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.crypto import EncryptionConfigError
from app.db.session import get_db
from app.schemas.sync import SyncRunsResponse, SyncRunSummary, SyncStatusResponse, SyncStravaRequest
from app.services.strava_client import StravaClient, StravaClientError, get_strava_client
from app.services.strava_sync_service import (
    StravaSyncService,
    SyncConfigError,
    SyncNotConnectedError,
)

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/strava", response_model=SyncRunSummary)
def sync_strava(
    request: SyncStravaRequest | None = None,
    db: Session = Depends(get_db),
    strava_client: StravaClient = Depends(get_strava_client),
) -> SyncRunSummary:
    service = StravaSyncService(db, get_settings(), strava_client)
    try:
        return service.run_sync(
            max_pages=request.max_pages if request else None,
            per_page=request.per_page if request else None,
        )
    except SyncNotConnectedError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (SyncConfigError, EncryptionConfigError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StravaClientError as exc:
        raise HTTPException(status_code=502, detail="Strava sync request failed") from exc


@router.get("/status", response_model=SyncStatusResponse)
def sync_status(
    db: Session = Depends(get_db),
    strava_client: StravaClient = Depends(get_strava_client),
) -> SyncStatusResponse:
    return StravaSyncService(db, get_settings(), strava_client).status()


@router.get("/runs", response_model=SyncRunsResponse)
def sync_runs(
    db: Session = Depends(get_db),
    strava_client: StravaClient = Depends(get_strava_client),
) -> SyncRunsResponse:
    return SyncRunsResponse(
        runs=StravaSyncService(db, get_settings(), strava_client).recent_runs()
    )
