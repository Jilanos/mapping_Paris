from dataclasses import dataclass
from datetime import UTC
import json
import math

from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import (
    B2StreetSegment,
    ProposalGenerationJob,
    SegmentDatasetVersion,
    SegmentMatchProposal,
    StravaActivity,
    StravaActivityProposalProcessing,
    StravaStream,
    utc_now,
)
from app.schemas.proposals import (
    ProposalGenerationJobResponse,
    ProposalGenerationSummary,
    ProposalProcessingResetResponse,
    ProposalResponse,
    ProposalStatusResponse,
)
from app.services.segment_matcher import SegmentMatcher
from app.services.segment_matcher import SegmentMatch


class ProposalGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProposalCandidate:
    dataset_version_id: int
    stream: StravaStream
    segment: B2StreetSegment
    match: SegmentMatch


@dataclass(frozen=True)
class ProposalPage:
    proposals: list[ProposalResponse]
    total: int
    limit: int
    offset: int
    returned: int
    has_more: bool
    next_offset: int | None


class ProposalService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._matcher = SegmentMatcher(settings)

    def generate(
        self,
        only_unprocessed: bool = False,
        max_activities: int | None = None,
        job_id: int | None = None,
    ) -> ProposalGenerationSummary:
        active_dataset = self._active_dataset()
        if active_dataset is None:
            raise ProposalGenerationError("No active segment dataset is loaded")

        activity_ids_with_proposals = self._activity_ids_with_proposals(active_dataset.id)
        processed_activity_ids = self._processed_activity_ids(active_dataset.id)
        streams_total = self._eligible_stream_count()
        effective_limit = self._effective_activity_limit(max_activities)
        streams = self._streams_for_generation(
            processed_activity_ids,
            only_unprocessed=only_unprocessed,
            limit=effective_limit,
        )
        skipped_already_processed = 0
        if only_unprocessed:
            skipped_already_processed = min(streams_total, len(processed_activity_ids))
        elif len(streams) < effective_limit:
            skipped_already_processed = 0
        pending_processing = max(0, streams_total - len(processed_activity_ids))
        if not streams:
            summary = ProposalGenerationSummary(
                activities_with_streams_total=streams_total,
                activities_already_had_proposals=len(activity_ids_with_proposals),
                activities_without_existing_proposals=max(0, streams_total - len(activity_ids_with_proposals)),
                activities_already_processed=len(processed_activity_ids),
                activities_pending_processing=pending_processing,
                activities_processed=0,
                streams_processed=0,
                activities_skipped_already_processed=skipped_already_processed,
                candidate_segments_checked=0,
                proposals_created=0,
                proposals_updated=0,
                proposals_skipped=0,
                errors_count=0,
            )
            if job_id is not None:
                self._update_job_from_summary(job_id, summary, status="running", message="No activities pending")
            return summary

        activities_processed: set[str] = set()
        streams_processed = 0
        candidate_segments_checked = 0
        proposals_created = 0
        proposals_updated = 0
        proposals_skipped = 0
        errors_count = 0

        for stream in streams:
            activity_created = 0
            activity_updated = 0
            activity_skipped = 0
            activity_candidate_segments_checked = 0
            try:
                self._mark_activity_running(active_dataset.id, stream.strava_activity_id)
                self._db.commit()
                stream_points = json.loads(stream.latlng_json)
                candidates = self._candidate_segments(active_dataset.id, stream_points)
                activity_candidate_segments_checked = len(candidates)
                best_candidates: dict[tuple[int, str, str], ProposalCandidate] = {}
                for segment in candidates:
                    match = self._matcher.match(stream_points, segment)
                    if match is None:
                        continue
                    candidate = ProposalCandidate(
                        dataset_version_id=active_dataset.id,
                        stream=stream,
                        segment=segment,
                        match=match,
                    )
                    key = (
                        active_dataset.id,
                        stream.strava_activity_id,
                        segment.logical_segment_id,
                    )
                    current = best_candidates.get(key)
                    if current is None or self._candidate_is_better(candidate, current):
                        best_candidates[key] = candidate

                for candidate in best_candidates.values():
                    result = self._upsert_proposal(
                        candidate.dataset_version_id,
                        candidate.stream,
                        candidate.segment,
                        candidate.match,
                    )
                    if result == "created":
                        activity_created += 1
                    elif result == "updated":
                        activity_updated += 1
                    else:
                        activity_skipped += 1
                self._db.commit()
                self._mark_activity_processed(
                    dataset_version_id=active_dataset.id,
                    activity_id=stream.strava_activity_id,
                    proposals_created=activity_created,
                    proposals_updated=activity_updated,
                    proposals_skipped=activity_skipped,
                    error_message=None,
                )
                self._db.commit()
                activities_processed.add(stream.strava_activity_id)
                streams_processed += 1
                candidate_segments_checked += activity_candidate_segments_checked
                proposals_created += activity_created
                proposals_updated += activity_updated
                proposals_skipped += activity_skipped
            except IntegrityError as exc:
                self._db.rollback()
                errors_count += 1
                self._mark_activity_failed(
                    active_dataset.id,
                    stream.strava_activity_id,
                    "Proposal generation created duplicate logical segment candidates",
                )
                self._db.commit()
                if not job_id:
                    raise ProposalGenerationError(
                        "Proposal generation created duplicate logical segment candidates"
                    ) from exc
            except Exception:
                self._db.rollback()
                errors_count += 1
                self._mark_activity_failed(
                    active_dataset.id,
                    stream.strava_activity_id,
                    "Activity stream could not be matched",
                )
                self._db.commit()
            finally:
                if job_id is not None:
                    partial = ProposalGenerationSummary(
                        activities_with_streams_total=streams_total,
                        activities_already_had_proposals=len(activity_ids_with_proposals),
                        activities_without_existing_proposals=max(0, streams_total - len(activity_ids_with_proposals)),
                        activities_already_processed=len(processed_activity_ids),
                        activities_pending_processing=pending_processing,
                        activities_processed=len(activities_processed),
                        streams_processed=streams_processed,
                        activities_skipped_already_processed=skipped_already_processed,
                        candidate_segments_checked=candidate_segments_checked,
                        proposals_created=proposals_created,
                        proposals_updated=proposals_updated,
                        proposals_skipped=proposals_skipped,
                        errors_count=errors_count,
                    )
                    self._update_job_from_summary(
                        job_id,
                        partial,
                        status="running",
                        message=f"Processed {len(activities_processed)} activities",
                    )

        summary = ProposalGenerationSummary(
            activities_with_streams_total=streams_total,
            activities_already_had_proposals=len(activity_ids_with_proposals),
            activities_without_existing_proposals=max(0, streams_total - len(activity_ids_with_proposals)),
            activities_already_processed=len(processed_activity_ids),
            activities_pending_processing=pending_processing,
            activities_processed=len(activities_processed),
            streams_processed=streams_processed,
            activities_skipped_already_processed=skipped_already_processed,
            candidate_segments_checked=candidate_segments_checked,
            proposals_created=proposals_created,
            proposals_updated=proposals_updated,
            proposals_skipped=proposals_skipped,
            errors_count=errors_count,
        )
        if job_id is not None:
            self._update_job_from_summary(job_id, summary, status="running", message="Proposal counters updated")
        return summary

    def _update_job_from_summary(
        self,
        job_id: int,
        summary: ProposalGenerationSummary,
        status: str,
        message: str | None = None,
    ) -> None:
        job = self._db.query(ProposalGenerationJob).filter(ProposalGenerationJob.id == job_id).one_or_none()
        if job is None:
            return
        job.status = status
        job.message = message
        job.activities_with_streams_total = summary.activities_with_streams_total
        job.activities_already_processed = summary.activities_already_processed
        job.activities_pending_processing = summary.activities_pending_processing
        job.activities_processed = summary.activities_processed
        job.streams_processed = summary.streams_processed
        job.candidate_segments_checked = summary.candidate_segments_checked
        job.proposals_created = summary.proposals_created
        job.proposals_updated = summary.proposals_updated
        job.proposals_skipped = summary.proposals_skipped
        job.errors_count = summary.errors_count
        self._db.add(job)
        self._db.commit()

    def _eligible_stream_query(self):
        return (
            self._db.query(StravaStream)
            .join(StravaActivity, StravaActivity.strava_activity_id == StravaStream.strava_activity_id)
            .filter(StravaActivity.sport_type.in_(self._settings.sync_sport_types))
        )

    def _eligible_stream_count(self) -> int:
        return self._eligible_stream_query().count()

    def _activity_ids_with_proposals(self, dataset_version_id: int) -> set[str]:
        rows = (
            self._db.query(SegmentMatchProposal.strava_activity_id)
            .filter(SegmentMatchProposal.dataset_version_id == dataset_version_id)
            .distinct()
            .all()
        )
        return {str(row[0]) for row in rows}

    def _processed_activity_ids(self, dataset_version_id: int) -> set[str]:
        rows = (
            self._db.query(StravaActivityProposalProcessing.strava_activity_id)
            .filter(StravaActivityProposalProcessing.dataset_version_id == dataset_version_id)
            .filter(StravaActivityProposalProcessing.status == "processed")
            .all()
        )
        return {str(row[0]) for row in rows}

    def _effective_activity_limit(self, requested_max_activities: int | None) -> int:
        configured = max(1, self._settings.match_max_activities_per_run)
        requested = requested_max_activities if requested_max_activities is not None else configured
        return min(max(1, requested), 500)

    def _streams_for_generation(
        self,
        processed_activity_ids: set[str],
        only_unprocessed: bool,
        limit: int,
    ) -> list[StravaStream]:
        unprocessed = (
            self._eligible_stream_query()
            .filter(~StravaStream.strava_activity_id.in_(processed_activity_ids))
            .order_by(StravaStream.created_at.asc(), StravaStream.id.asc())
            .limit(limit)
            .all()
        )
        if only_unprocessed or len(unprocessed) >= limit:
            return unprocessed
        existing = (
            self._eligible_stream_query()
            .filter(StravaStream.strava_activity_id.in_(processed_activity_ids))
            .order_by(StravaStream.created_at.asc(), StravaStream.id.asc())
            .limit(limit - len(unprocessed))
            .all()
        )
        return unprocessed + existing

    def _mark_activity_processed(
        self,
        dataset_version_id: int,
        activity_id: str,
        proposals_created: int,
        proposals_updated: int,
        proposals_skipped: int,
        error_message: str | None,
    ) -> None:
        processing = (
            self._db.query(StravaActivityProposalProcessing)
            .filter(StravaActivityProposalProcessing.dataset_version_id == dataset_version_id)
            .filter(StravaActivityProposalProcessing.strava_activity_id == activity_id)
            .one_or_none()
        )
        if processing is None:
            processing = StravaActivityProposalProcessing(
                dataset_version_id=dataset_version_id,
                strava_activity_id=activity_id,
            )
        processing.status = "failed" if error_message else "processed"
        processing.processed_at = utc_now()
        processing.proposals_created = proposals_created
        processing.proposals_updated = proposals_updated
        processing.proposals_skipped = proposals_skipped
        processing.error_message = error_message
        self._db.add(processing)

    def _mark_activity_running(self, dataset_version_id: int, activity_id: str) -> None:
        processing = self._activity_processing(dataset_version_id, activity_id)
        if processing is None:
            processing = StravaActivityProposalProcessing(
                dataset_version_id=dataset_version_id,
                strava_activity_id=activity_id,
            )
        processing.status = "running"
        processing.error_message = None
        self._db.add(processing)

    def _mark_activity_failed(self, dataset_version_id: int, activity_id: str, error_message: str) -> None:
        processing = self._activity_processing(dataset_version_id, activity_id)
        if processing is None:
            processing = StravaActivityProposalProcessing(
                dataset_version_id=dataset_version_id,
                strava_activity_id=activity_id,
            )
        processing.status = "failed"
        processing.processed_at = utc_now()
        processing.error_message = error_message
        self._db.add(processing)

    def _activity_processing(
        self,
        dataset_version_id: int,
        activity_id: str,
    ) -> StravaActivityProposalProcessing | None:
        return (
            self._db.query(StravaActivityProposalProcessing)
            .filter(StravaActivityProposalProcessing.dataset_version_id == dataset_version_id)
            .filter(StravaActivityProposalProcessing.strava_activity_id == activity_id)
            .one_or_none()
        )

    def list_proposals(
        self,
        status: str | None = "proposed",
        arrondissement: str | None = None,
        street_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
        include_raw: bool = False,
    ) -> ProposalPage:
        query = self._db.query(SegmentMatchProposal)
        if status:
            query = query.filter(SegmentMatchProposal.status == status)
        if arrondissement:
            query = query.filter(SegmentMatchProposal.arrondissement == arrondissement)
        if street_name:
            query = query.filter(SegmentMatchProposal.street_name.ilike(f"%{street_name}%"))
        total = query.count()
        proposals = (
            query.order_by(
                SegmentMatchProposal.confidence_score.desc(),
                SegmentMatchProposal.coverage_ratio.desc(),
                SegmentMatchProposal.id.asc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )
        returned = len(proposals)
        next_offset = offset + returned
        has_more = next_offset < total
        return ProposalPage(
            proposals=[self._response(proposal, include_raw=include_raw) for proposal in proposals],
            total=total,
            limit=limit,
            offset=offset,
            returned=returned,
            has_more=has_more,
            next_offset=next_offset if has_more else None,
        )

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

    def reset_processing(self, include_proposals: bool = False) -> ProposalProcessingResetResponse:
        active_dataset = self._active_dataset()
        if active_dataset is None:
            raise ProposalGenerationError("No active segment dataset is loaded")
        query = self._db.query(StravaActivityProposalProcessing).filter(
            StravaActivityProposalProcessing.dataset_version_id == active_dataset.id
        )
        reset_count = query.count()
        query.delete(synchronize_session=False)
        proposals_deleted = 0
        if include_proposals:
            proposal_query = self._db.query(SegmentMatchProposal).filter(
                SegmentMatchProposal.dataset_version_id == active_dataset.id
            )
            proposals_deleted = proposal_query.count()
            proposal_query.delete(synchronize_session=False)
        self._db.commit()
        return ProposalProcessingResetResponse(
            dataset_version_id=active_dataset.id,
            processing_records_reset=reset_count,
            proposals_deleted=proposals_deleted,
        )

    def latest_job(self) -> ProposalGenerationJob | None:
        return (
            self._db.query(ProposalGenerationJob)
            .order_by(ProposalGenerationJob.created_at.desc(), ProposalGenerationJob.id.desc())
            .first()
        )

    def running_job(self) -> ProposalGenerationJob | None:
        jobs = (
            self._db.query(ProposalGenerationJob)
            .filter(ProposalGenerationJob.status.in_(["pending", "running"]))
            .order_by(ProposalGenerationJob.created_at.desc(), ProposalGenerationJob.id.desc())
            .all()
        )
        for job in jobs:
            if self._job_is_stale(job):
                self._mark_job_stale(job)
        if any(job.status == "failed" for job in jobs):
            self._db.commit()
        return next((job for job in jobs if job.status in {"pending", "running"}), None)

    def reset_stale_jobs(self) -> int:
        jobs = (
            self._db.query(ProposalGenerationJob)
            .filter(ProposalGenerationJob.status.in_(["pending", "running"]))
            .all()
        )
        reset_count = 0
        for job in jobs:
            if self._job_is_stale(job):
                self._mark_job_stale(job)
                reset_count += 1
        if reset_count:
            self._db.commit()
        return reset_count

    def get_job(self, job_id: int) -> ProposalGenerationJob | None:
        return (
            self._db.query(ProposalGenerationJob)
            .filter(ProposalGenerationJob.id == job_id)
            .one_or_none()
        )

    def job_response(self, job: ProposalGenerationJob | None) -> ProposalGenerationJobResponse:
        if job is None:
            return ProposalGenerationJobResponse(status="none")
        return ProposalGenerationJobResponse(
            id=job.id,
            status=job.status,
            started_at=job.started_at,
            finished_at=job.finished_at,
            message=job.message,
            error_message=job.error_message,
            activities_with_streams_total=job.activities_with_streams_total,
            activities_already_processed=job.activities_already_processed,
            activities_pending_processing=job.activities_pending_processing,
            activities_processed=job.activities_processed,
            streams_processed=job.streams_processed,
            candidate_segments_checked=job.candidate_segments_checked,
            proposals_created=job.proposals_created,
            proposals_updated=job.proposals_updated,
            proposals_skipped=job.proposals_skipped,
            errors_count=job.errors_count,
        )

    def _job_is_stale(self, job: ProposalGenerationJob) -> bool:
        reference = job.updated_at or job.started_at or job.created_at
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=UTC)
        return (utc_now() - reference).total_seconds() > self._settings.proposal_job_stale_after_seconds

    def _mark_job_stale(self, job: ProposalGenerationJob) -> None:
        job.status = "failed"
        job.finished_at = utc_now()
        job.message = "Proposal generation job became stale"
        job.error_message = "Job marked failed because it became stale"
        self._db.add(job)

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
        if existing is not None and not self._match_is_better_than_existing(match, existing):
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

    def _candidate_is_better(self, candidate: ProposalCandidate, current: ProposalCandidate) -> bool:
        return self._candidate_sort_key(candidate) > self._candidate_sort_key(current)

    def _candidate_sort_key(self, candidate: ProposalCandidate) -> tuple[float, float, float, str]:
        return (
            candidate.match.confidence_score,
            candidate.match.coverage_ratio,
            -candidate.match.avg_distance_meters,
            candidate.segment.segment_id,
        )

    def _match_is_better_than_existing(self, match: SegmentMatch, existing: SegmentMatchProposal) -> bool:
        return (
            match.confidence_score,
            match.coverage_ratio,
            -match.avg_distance_meters,
        ) > (
            existing.confidence_score,
            existing.coverage_ratio,
            -existing.avg_distance_meters,
        )

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
