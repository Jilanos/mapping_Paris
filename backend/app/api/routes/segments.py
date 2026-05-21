import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import B2StreetSegment, SegmentDatasetVersion
from app.db.session import get_db
from app.schemas.segments import (
    SegmentDatasetStatusResponse,
    SegmentDatasetSummary,
    SegmentDatasetsResponse,
    SegmentSearchResponse,
    SegmentSearchResult,
)
from app.services.segment_dataset_store import SegmentDatasetStore

router = APIRouter(prefix="/segments", tags=["segments"])


@router.get("/status", response_model=SegmentDatasetStatusResponse)
def segment_dataset_status(db: Session = Depends(get_db)) -> SegmentDatasetStatusResponse:
    active = SegmentDatasetStore(db).active_version()
    if active is None:
        return SegmentDatasetStatusResponse(loaded=False)
    return SegmentDatasetStatusResponse(
        loaded=True,
        active_dataset_version_id=active.id,
        dataset_hash=active.dataset_hash,
        segment_count=active.segment_count,
        logical_segment_count=active.logical_segment_count,
        created_at=active.created_at,
        source_file_name=active.source_file_name,
    )


@router.get("/datasets", response_model=SegmentDatasetsResponse)
def segment_datasets(db: Session = Depends(get_db)) -> SegmentDatasetsResponse:
    versions = SegmentDatasetStore(db).recent_versions()
    return SegmentDatasetsResponse(datasets=[_dataset_summary(version) for version in versions])


@router.get("/search", response_model=SegmentSearchResponse)
def search_segments(
    arrondissement: str | None = None,
    street_name: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    include_geometry: bool = False,
    db: Session = Depends(get_db),
) -> SegmentSearchResponse:
    segments = SegmentDatasetStore(db).search_segments(
        arrondissement=arrondissement,
        street_name=street_name,
        limit=limit,
    )
    return SegmentSearchResponse(
        segments=[_segment_result(segment, include_geometry) for segment in segments]
    )


def _dataset_summary(version: SegmentDatasetVersion) -> SegmentDatasetSummary:
    return SegmentDatasetSummary(
        id=version.id,
        dataset_hash=version.dataset_hash,
        segment_count=version.segment_count,
        logical_segment_count=version.logical_segment_count,
        created_at=version.created_at,
        is_active=version.is_active,
    )


def _segment_result(segment: B2StreetSegment, include_geometry: bool) -> SegmentSearchResult:
    return SegmentSearchResult(
        segment_id=segment.segment_id,
        logical_segment_id=segment.logical_segment_id,
        street_name=segment.street_name,
        arrondissement=segment.arrondissement,
        length_meters=segment.length_meters,
        bbox={
            "min_lat": segment.min_lat,
            "min_lon": segment.min_lon,
            "max_lat": segment.max_lat,
            "max_lon": segment.max_lon,
        },
        geometry=json.loads(segment.geometry_json) if include_geometry else None,
    )
