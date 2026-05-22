from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class SyncStravaRequest(BaseModel):
    max_pages: int | None = Field(default=None, ge=1)
    per_page: int | None = Field(default=None, ge=1)


class SyncRunSummary(BaseModel):
    id: int
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    activities_fetched: int
    activities_created: int
    activities_updated: int
    streams_downloaded: int
    pages_requested: int = 0
    skipped_existing_activities: int = 0
    errors_count: int
    message: str | None = None


class SyncStatusResponse(BaseModel):
    connected: bool
    latest_sync: SyncRunSummary | None = None
    stored_activities: int
    stored_streams: int
    activities_with_streams: int


class SyncRunsResponse(BaseModel):
    runs: list[SyncRunSummary]
