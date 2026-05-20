from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class StravaToken(Base):
    __tablename__ = "strava_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    athlete_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scope: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    token_type: Mapped[str] = mapped_column(String(64), nullable=False, default="Bearer")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class AuthState(Base):
    __tablename__ = "auth_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    state: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StravaActivity(Base):
    __tablename__ = "strava_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strava_activity_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    athlete_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    sport_type: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    type: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_date_local: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    distance_meters: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    moving_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    elapsed_time_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_elevation_gain: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    commute: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    trainer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    map_polyline: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    streams_downloaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class StravaStream(Base):
    __tablename__ = "strava_streams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strava_activity_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("strava_activities.strava_activity_id"),
        unique=True,
        nullable=False,
        index=True,
    )
    latlng_json: Mapped[str] = mapped_column(Text, nullable=False)
    distance_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    stream_point_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="running")
    activities_fetched: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activities_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activities_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streams_downloaded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)


class SyncError(Base):
    __tablename__ = "sync_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sync_run_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sync_runs.id"),
        nullable=False,
        index=True,
    )
    strava_activity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    step: Mapped[str] = mapped_column(String(64), nullable=False)
    error_type: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
