import json
import math

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import (
    B2StreetSegment,
    SegmentDatasetVersion,
    SegmentMatchProposal,
    StravaActivity,
    StravaStream,
    utc_now,
)
from app.schemas.proposals import (
    ProposalGenerationSummary,
    ProposalResponse,
    ProposalStatusResponse,
)
from app.services.segment_matcher import SegmentMatcher


class ProposalGenerationError(RuntimeError):
    pass


class ProposalService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._matcher = SegmentMatcher(settings)

    def generate(self) -> ProposalGenerationSummary:
        active_dataset = self._active_dataset()
        if active_dataset is None:
            raise ProposalGenerationError("No active segment dataset is loaded")

        streams = (
            self._db.query(StravaStream)
            .join(StravaActivity, StravaActivity.strava_activity_id == StravaStream.strava_activity_id)
            .filter(StravaActivity.sport_type.in_(self._settings.sync_sport_types))
            .order_by(StravaStream.created_at.asc(), StravaStream.id.asc())
            .limit(self._settings.match_max_activities_per_run)
            .all()
        )
        if not streams:
            return ProposalGenerationSummary(
                activities_processed=0,
                streams_processed=0,
                candidate_segments_checked=0,
                proposals_created=0,
                proposals_updated=0,
                proposals_skipped=0,
                errors_count=0,
            )

        activities_processed: set[str] = set()
        candidate_segments_checked = 0
        proposals_created = 0
        proposals_updated = 0
        proposals_skipped = 0
        errors_count = 0

        for stream in streams:
            activities_processed.add(stream.strava_activity_id)
            try:
                stream_points = json.loads(stream.latlng_json)
                candidates = self._candidate_segments(active_dataset.id, stream_points)
                candidate_segments_checked += len(candidates)
                for segment in candidates:
                    match = self._matcher.match(stream_points, segment)
                    if match is None:
                        continue
                    result = self._upsert_proposal(active_dataset.id, stream, segment, match)
                    if result == "created":
                        proposals_created += 1
                    elif result == "updated":
                        proposals_updated += 1
                    else:
                        proposals_skipped += 1
            except Exception:
                errors_count += 1

        self._db.commit()
        return ProposalGenerationSummary(
            activities_processed=len(activities_processed),
            streams_processed=len(streams),
            candidate_segments_checked=candidate_segments_checked,
            proposals_created=proposals_created,
            proposals_updated=proposals_updated,
            proposals_skipped=proposals_skipped,
            errors_count=errors_count,
        )

    def list_proposals(
        self,
        status: str | None = "proposed",
        arrondissement: str | None = None,
        street_name: str | None = None,
        limit: int = 100,
        include_raw: bool = False,
    ) -> list[ProposalResponse]:
        query = self._db.query(SegmentMatchProposal)
        if status:
            query = query.filter(SegmentMatchProposal.status == status)
        if arrondissement:
            query = query.filter(SegmentMatchProposal.arrondissement == arrondissement)
        if street_name:
            query = query.filter(SegmentMatchProposal.street_name.ilike(f"%{street_name}%"))
        proposals = (
            query.order_by(
                SegmentMatchProposal.confidence_score.desc(),
                SegmentMatchProposal.coverage_ratio.desc(),
                SegmentMatchProposal.id.asc(),
            )
            .limit(limit)
            .all()
        )
        return [self._response(proposal, include_raw=include_raw) for proposal in proposals]

    def status(self) -> ProposalStatusResponse:
        active_dataset = self._active_dataset()
        latest_created_at = self._db.query(func.max(SegmentMatchProposal.created_at)).scalar()
        return ProposalStatusResponse(
            total_proposals=self._db.query(SegmentMatchProposal).count(),
            proposed_count=self._count_status("proposed"),
            accepted_count=self._count_status("accepted"),
            dismissed_count=self._count_status("dismissed"),
            active_dataset_version_id=active_dataset.id if active_dataset is not None else None,
            activities_with_streams_count=(
                self._db.query(StravaActivity)
                .filter(StravaActivity.streams_downloaded.is_(True))
                .count()
            ),
            latest_proposal_created_at=latest_created_at,
        )

    def set_status(self, proposal_id: int, status: str) -> SegmentMatchProposal | None:
        proposal = (
            self._db.query(SegmentMatchProposal)
            .filter(SegmentMatchProposal.id == proposal_id)
            .one_or_none()
        )
        if proposal is None:
            return None
        now = utc_now()
        proposal.status = status
        if status == "dismissed":
            proposal.dismissed_at = now
        elif status == "accepted":
            proposal.accepted_at = now
        self._db.add(proposal)
        self._db.commit()
        self._db.refresh(proposal)
        return proposal

    def _active_dataset(self) -> SegmentDatasetVersion | None:
        return (
            self._db.query(SegmentDatasetVersion)
            .filter(SegmentDatasetVersion.is_active.is_(True))
            .order_by(SegmentDatasetVersion.created_at.desc(), SegmentDatasetVersion.id.desc())
            .first()
        )

    def _candidate_segments(self, dataset_version_id: int, stream_points: list[list[float]]) -> list[B2StreetSegment]:
        if not stream_points:
            return []
        lats = [point[0] for point in stream_points]
        lons = [point[1] for point in stream_points]
        avg_lat = sum(lats) / len(lats)
        lat_buffer = self._settings.match_candidate_bbox_buffer_meters / 111_320.0
        lon_buffer = self._settings.match_candidate_bbox_buffer_meters / (
            111_320.0 * max(0.1, math.cos(math.radians(avg_lat)))
        )
        return (
            self._db.query(B2StreetSegment)
            .filter(B2StreetSegment.dataset_version_id == dataset_version_id)
            .filter(B2StreetSegment.max_lat >= min(lats) - lat_buffer)
            .filter(B2StreetSegment.min_lat <= max(lats) + lat_buffer)
            .filter(B2StreetSegment.max_lon >= min(lons) - lon_buffer)
            .filter(B2StreetSegment.min_lon <= max(lons) + lon_buffer)
            .all()
        )

    def _upsert_proposal(
        self,
        dataset_version_id: int,
        stream: StravaStream,
        segment: B2StreetSegment,
        match,
    ) -> str:
        existing = (
            self._db.query(SegmentMatchProposal)
            .filter(SegmentMatchProposal.dataset_version_id == dataset_version_id)
            .filter(SegmentMatchProposal.strava_activity_id == stream.strava_activity_id)
            .filter(SegmentMatchProposal.logical_segment_id == segment.logical_segment_id)
            .one_or_none()
        )
        if existing is not None and existing.status in {"accepted", "dismissed"}:
            return "skipped"
        proposal = existing or SegmentMatchProposal(
            dataset_version_id=dataset_version_id,
            strava_activity_id=stream.strava_activity_id,
            segment_id=segment.segment_id,
            logical_segment_id=segment.logical_segment_id,
            street_name=segment.street_name,
            arrondissement=segment.arrondissement,
            segment_length_meters=segment.length_meters,
            covered_length_meters=0.0,
            coverage_ratio=0.0,
            min_distance_meters=0.0,
            avg_distance_meters=0.0,
            max_distance_meters=0.0,
            matched_points_count=0,
            confidence_score=0.0,
            status="proposed",
        )
        proposal.segment_id = segment.segment_id
        proposal.street_name = segment.street_name
        proposal.arrondissement = segment.arrondissement
        proposal.segment_length_meters = segment.length_meters
        proposal.covered_length_meters = match.covered_length_meters
        proposal.coverage_ratio = match.coverage_ratio
        proposal.min_distance_meters = match.min_distance_meters
        proposal.avg_distance_meters = match.avg_distance_meters
        proposal.max_distance_meters = match.max_distance_meters
        proposal.matched_points_count = match.matched_points_count
        proposal.confidence_score = match.confidence_score
        proposal.raw_match_json = json.dumps(match.raw_match, separators=(",", ":"))
        self._db.add(proposal)
        return "created" if existing is None else "updated"

    def _count_status(self, status: str) -> int:
        return (
            self._db.query(SegmentMatchProposal)
            .filter(SegmentMatchProposal.status == status)
            .count()
        )

    def _response(self, proposal: SegmentMatchProposal, include_raw: bool) -> ProposalResponse:
        return ProposalResponse(
            id=proposal.id,
            strava_activity_id=proposal.strava_activity_id,
            segment_id=proposal.segment_id,
            logical_segment_id=proposal.logical_segment_id,
            street_name=proposal.street_name,
            arrondissement=proposal.arrondissement,
            segment_length_meters=proposal.segment_length_meters,
            covered_length_meters=proposal.covered_length_meters,
            coverage_ratio=proposal.coverage_ratio,
            avg_distance_meters=proposal.avg_distance_meters,
            matched_points_count=proposal.matched_points_count,
            confidence_score=proposal.confidence_score,
            status=proposal.status,
            created_at=proposal.created_at,
            raw_match=json.loads(proposal.raw_match_json) if include_raw and proposal.raw_match_json else None,
        )
