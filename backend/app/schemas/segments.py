from datetime import datetime

from pydantic import BaseModel


class SegmentDatasetStatusResponse(BaseModel):
    loaded: bool
    active_dataset_version_id: int | None = None
    dataset_hash: str | None = None
    segment_count: int | None = None
    logical_segment_count: int | None = None
    created_at: datetime | None = None
    source_file_name: str | None = None


class SegmentDatasetSummary(BaseModel):
    id: int
    dataset_hash: str
    segment_count: int
    logical_segment_count: int
    created_at: datetime
    is_active: bool


class SegmentDatasetsResponse(BaseModel):
    datasets: list[SegmentDatasetSummary]


class SegmentSearchResult(BaseModel):
    segment_id: str
    logical_segment_id: str
    street_name: str
    arrondissement: str
    length_meters: float
    bbox: dict[str, float]
    geometry: list[list[float]] | None = None


class SegmentSearchResponse(BaseModel):
    segments: list[SegmentSearchResult]
