from datetime import UTC, datetime, timedelta
import json

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.crypto import EncryptionConfigError
from app.db.models import StravaActivity, StravaStream, StravaToken, SyncError, SyncRun
from app.schemas.strava import StravaTokenResponse
from app.schemas.sync import SyncRunSummary, SyncStatusResponse
from app.services.strava_client import StravaClient, StravaClientError
from app.services.token_store import TokenStore


class SyncConfigError(RuntimeError):
    pass


class SyncNotConnectedError(RuntimeError):
    pass


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class StravaSyncService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        strava_client: StravaClient,
    ) -> None:
        self._db = db
        self._settings = settings
        self._strava_client = strava_client

    def run_sync(self, max_pages: int | None = None, per_page: int | None = None) -> SyncRunSummary:
        sync_run = SyncRun(status="running")
        self._db.add(sync_run)
        self._db.commit()
        self._db.refresh(sync_run)
        try:
            token_store = TokenStore(self._db, self._settings)
            token = self._valid_token(token_store)
            access_token = token_store.get_access_token()
            if access_token is None:
                raise SyncNotConnectedError("No Strava token is stored")

            effective_max_pages = self._effective_max_pages(max_pages)
            effective_per_page = self._effective_per_page(per_page)
            activities, pages_requested = self._fetch_activities(
                access_token,
                max_pages=effective_max_pages,
                per_page=effective_per_page,
            )
            sync_run.activities_fetched = len(activities)
            skipped_existing_activities = 0
            for activity in activities:
                if not self._is_supported_activity(activity):
                    continue
                existing_activity = self._find_activity(str(activity["id"]))
                if existing_activity is not None and existing_activity.streams_downloaded:
                    skipped_existing_activities += 1
                    continue
                db_activity, created = self._upsert_activity(activity, token.athlete_id)
                if created:
                    sync_run.activities_created += 1
                else:
                    sync_run.activities_updated += 1
                if self._settings.strava_sync_download_streams and not db_activity.streams_downloaded:
                    self._download_stream(access_token, db_activity, sync_run)

            sync_run.finished_at = datetime.now(UTC)
            sync_run.status = "partial_failure" if sync_run.errors_count else "success"
            sync_run.message = "Sync completed"
            self._db.add(sync_run)
            self._db.commit()
            self._db.refresh(sync_run)
            return self._summary(
                sync_run,
                pages_requested=pages_requested,
                skipped_existing_activities=skipped_existing_activities,
            )
        except (EncryptionConfigError, SyncConfigError, SyncNotConnectedError):
            sync_run.finished_at = datetime.now(UTC)
            sync_run.status = "failed"
            sync_run.errors_count += 1
            sync_run.message = "Sync failed before activity processing"
            self._db.add(sync_run)
            self._db.commit()
            raise
        except Exception as exc:
            sync_run.finished_at = datetime.now(UTC)
            sync_run.status = "failed"
            sync_run.errors_count += 1
            sync_run.message = "Unexpected sync failure"
            self._record_error(sync_run, None, "sync", exc)
            self._db.add(sync_run)
            self._db.commit()
            raise

    def status(self) -> SyncStatusResponse:
        latest = self._latest_run()
        return SyncStatusResponse(
            connected=self._db.query(StravaToken).first() is not None,
            latest_sync=self._summary(latest) if latest is not None else None,
            stored_activities=self._db.query(StravaActivity).count(),
            stored_streams=self._db.query(StravaStream).count(),
            activities_with_streams=(
                self._db.query(StravaActivity)
                .filter(StravaActivity.streams_downloaded.is_(True))
                .count()
            ),
        )

    def recent_runs(self, limit: int = 10) -> list[SyncRunSummary]:
        runs = self._db.query(SyncRun).order_by(SyncRun.started_at.desc(), SyncRun.id.desc()).limit(limit).all()
        return [self._summary(run) for run in runs]

    def _valid_token(self, token_store: TokenStore) -> StravaToken:
        if not self._settings.strava_configured:
            raise SyncConfigError("Strava sync requires Strava OAuth configuration")
        token = token_store.get_latest()
        if token is None:
            raise SyncNotConnectedError("No Strava token is stored")
        expires_at = _aware(token.expires_at)
        refresh_margin = timedelta(seconds=self._settings.strava_token_refresh_margin_seconds)
        if expires_at <= datetime.now(UTC) + refresh_margin:
            refresh_token = token_store.get_refresh_token()
            if refresh_token is None:
                raise SyncNotConnectedError("No Strava refresh token is stored")
            refreshed = self._strava_client.refresh_access_token(refresh_token)
            token = token_store.save(refreshed)
        return token

    def _effective_max_pages(self, requested_max_pages: int | None) -> int:
        configured_default = max(1, self._settings.strava_sync_max_pages)
        absolute_max = max(1, self._settings.strava_sync_absolute_max_pages)
        return min(max(1, requested_max_pages or configured_default), absolute_max)

    def _effective_per_page(self, requested_per_page: int | None) -> int:
        configured_default = max(1, self._settings.strava_sync_per_page)
        return min(max(1, requested_per_page or configured_default), 100)

    def _fetch_activities(
        self,
        access_token: str,
        max_pages: int,
        per_page: int,
    ) -> tuple[list[dict], int]:
        activities: list[dict] = []
        pages_requested = 0
        for page in range(1, max_pages + 1):
            pages_requested += 1
            page_activities = self._strava_client.list_activities(
                access_token,
                page=page,
                per_page=per_page,
            )
            activities.extend(page_activities)
            if len(page_activities) < per_page:
                break
        return activities, pages_requested

    def _is_supported_activity(self, activity: dict) -> bool:
        sport_type = activity.get("sport_type") or activity.get("type") or ""
        return sport_type in self._settings.sync_sport_types

    def _find_activity(self, activity_id: str) -> StravaActivity | None:
        return (
            self._db.query(StravaActivity)
            .filter(StravaActivity.strava_activity_id == activity_id)
            .one_or_none()
        )

    def _upsert_activity(self, activity: dict, athlete_id: str | None) -> tuple[StravaActivity, bool]:
        activity_id = str(activity["id"])
        db_activity = self._find_activity(activity_id)
        created = db_activity is None
        if db_activity is None:
            db_activity = StravaActivity(strava_activity_id=activity_id)

        db_activity.athlete_id = athlete_id
        db_activity.name = activity.get("name") or ""
        db_activity.sport_type = activity.get("sport_type") or ""
        db_activity.type = activity.get("type") or ""
        db_activity.start_date = _parse_datetime(activity.get("start_date"))
        db_activity.start_date_local = _parse_datetime(activity.get("start_date_local"))
        db_activity.timezone = activity.get("timezone")
        db_activity.distance_meters = float(activity.get("distance") or 0)
        db_activity.moving_time_seconds = int(activity.get("moving_time") or 0)
        db_activity.elapsed_time_seconds = int(activity.get("elapsed_time") or 0)
        db_activity.total_elevation_gain = float(activity.get("total_elevation_gain") or 0)
        db_activity.private = bool(activity.get("private") or False)
        db_activity.commute = bool(activity.get("commute") or False)
        db_activity.trainer = bool(activity.get("trainer") or False)
        db_activity.manual = bool(activity.get("manual") or False)
        db_activity.map_polyline = (activity.get("map") or {}).get("summary_polyline")
        db_activity.raw_json = json.dumps(activity, separators=(",", ":"), sort_keys=True)

        self._db.add(db_activity)
        self._db.commit()
        self._db.refresh(db_activity)
        return db_activity, created

    def _download_stream(
        self,
        access_token: str,
        activity: StravaActivity,
        sync_run: SyncRun,
    ) -> None:
        try:
            streams = self._strava_client.get_activity_streams(
                access_token,
                activity.strava_activity_id,
            )
            latlng_data = (streams.get("latlng") or {}).get("data") or []
            if not latlng_data:
                raise StravaClientError("Strava stream response did not contain latlng data")
            stream = (
                self._db.query(StravaStream)
                .filter(StravaStream.strava_activity_id == activity.strava_activity_id)
                .one_or_none()
            ) or StravaStream(strava_activity_id=activity.strava_activity_id, latlng_json="[]")
            distance_data = (streams.get("distance") or {}).get("data")
            time_data = (streams.get("time") or {}).get("data")
            stream.latlng_json = json.dumps(latlng_data, separators=(",", ":"))
            stream.distance_json = (
                json.dumps(distance_data, separators=(",", ":"))
                if distance_data is not None
                else None
            )
            stream.time_json = (
                json.dumps(time_data, separators=(",", ":")) if time_data is not None else None
            )
            stream.stream_point_count = len(latlng_data)
            activity.streams_downloaded = True
            self._db.add(stream)
            self._db.add(activity)
            sync_run.streams_downloaded += 1
            self._db.commit()
        except Exception as exc:
            sync_run.errors_count += 1
            self._record_error(sync_run, activity.strava_activity_id, "stream_download", exc)
            self._db.add(sync_run)
            self._db.commit()

    def _record_error(
        self,
        sync_run: SyncRun,
        activity_id: str | None,
        step: str,
        exc: Exception,
    ) -> None:
        self._db.add(
            SyncError(
                sync_run_id=sync_run.id,
                strava_activity_id=activity_id,
                step=step,
                error_type=exc.__class__.__name__,
                message=str(exc),
            )
        )

    def _latest_run(self) -> SyncRun | None:
        return self._db.query(SyncRun).order_by(SyncRun.started_at.desc(), SyncRun.id.desc()).first()

    def _summary(
        self,
        run: SyncRun,
        pages_requested: int = 0,
        skipped_existing_activities: int = 0,
    ) -> SyncRunSummary:
        return SyncRunSummary(
            id=run.id,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            activities_fetched=run.activities_fetched,
            activities_created=run.activities_created,
            activities_updated=run.activities_updated,
            streams_downloaded=run.streams_downloaded,
            pages_requested=pages_requested,
            skipped_existing_activities=skipped_existing_activities,
            errors_count=run.errors_count,
            message=run.message,
        )
