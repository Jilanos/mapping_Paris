from datetime import datetime

from pydantic import BaseModel
from pydantic import Field


class ProposalGenerationRequest(BaseModel):
    only_unprocessed: bool = False
    max_activities: int | None = Field(default=None, ge=1)


class ProposalGenerationSummary(BaseModel):
    activities_with_streams_total: int = 0
    activities_already_had_proposals: int = 0
    activities_without_existing_proposals: int = 0
    activities_processed: int
    streams_processed: int
    activities_skipped_already_processed: int = 0
    candidate_segments_checked: int
    proposals_created: int
    proposals_updated: int
    proposals_skipped: int
    errors_count: int


class ProposalResponse(BaseModel):
    id: int
    strava_activity_id: str
    segment_id: str
    logical_segment_id: str
    street_name: str
    arrondissement: str
    segment_length_meters: float
    covered_length_meters: float
    coverage_ratio: float
    avg_distance_meters: float
    matched_points_count: int
    confidence_score: float
    status: str
    created_at: datetime
    raw_match: dict | None = None


class ProposalsResponse(BaseModel):
    proposals: list[ProposalResponse]
    total: int = 0
    limit: int = 100
    offset: int = 0
    returned: int = 0
    has_more: bool = False
    next_offset: int | None = None


class ProposalStatusResponse(BaseModel):
    total_proposals: int
    proposed_count: int
    accepted_count: int
    dismissed_count: int
    active_dataset_version_id: int | None
    activities_with_streams_count: int
    latest_proposal_created_at: datetime | None


class ProposalMutationResponse(BaseModel):
    id: int
    status: str
