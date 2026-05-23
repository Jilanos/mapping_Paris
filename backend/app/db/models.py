from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
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


class SegmentDatasetVersion(Base):
    __tablename__ = "segment_dataset_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    logical_segment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class B2StreetSegment(Base):
    __tablename__ = "b2_street_segments"
    __table_args__ = (
        Index("ix_b2_segments_dataset_segment", "dataset_version_id", "segment_id"),
        Index("ix_b2_segments_dataset_logical", "dataset_version_id", "logical_segment_id"),
        Index("ix_b2_segments_bbox", "min_lat", "min_lon", "max_lat", "max_lon"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("segment_dataset_versions.id"),
        nullable=False,
        index=True,
    )
    segment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    logical_segment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    street_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    arrondissement: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    length_meters: Mapped[float] = mapped_column(Float, nullable=False)
    accessibility: Mapped[str | None] = mapped_column(String(128), nullable=True)
    geometry_json: Mapped[str] = mapped_column(Text, nullable=False)
    min_lat: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    min_lon: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    max_lat: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    max_lon: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class SegmentMatchProposal(Base):
    __tablename__ = "segment_match_proposals"
    __table_args__ = (
        UniqueConstraint(
            "dataset_version_id",
            "strava_activity_id",
            "logical_segment_id",
            name="uq_proposal_dataset_activity_logical",
        ),
        Index("ix_proposals_status", "status"),
        Index("ix_proposals_arrondissement", "arrondissement"),
        Index("ix_proposals_street_name", "street_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("segment_dataset_versions.id"),
        nullable=False,
        index=True,
    )
    strava_activity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    segment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    logical_segment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    street_name: Mapped[str] = mapped_column(String(255), nullable=False)
    arrondissement: Mapped[str] = mapped_column(String(16), nullable=False)
    segment_length_meters: Mapped[float] = mapped_column(Float, nullable=False)
    covered_length_meters: Mapped[float] = mapped_column(Float, nullable=False)
    coverage_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    min_distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    avg_distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    max_distance_meters: Mapped[float] = mapped_column(Float, nullable=False)
    matched_points_count: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="proposed", index=True)
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
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_match_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class StravaActivityProposalProcessing(Base):
    __tablename__ = "strava_activity_proposal_processing"
    __table_args__ = (
        UniqueConstraint(
            "dataset_version_id",
            "strava_activity_id",
            name="uq_processing_dataset_activity",
        ),
        Index("ix_processing_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strava_activity_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("strava_activities.strava_activity_id"),
        nullable=False,
        index=True,
    )
    dataset_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("segment_dataset_versions.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proposals_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposals_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposals_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
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


class ProposalGenerationJob(Base):
    __tablename__ = "proposal_generation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    activities_with_streams_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activities_already_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activities_pending_processing: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activities_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streams_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidate_segments_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposals_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposals_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    proposals_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
