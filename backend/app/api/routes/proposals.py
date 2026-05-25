from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import ProposalGenerationJob, utc_now
from app.db.session import SessionLocal, get_db
from app.schemas.proposals import (
    ProposalGenerationJobResponse,
    ProposalGenerationRequest,
    ProposalGenerationSummary,
    ProposalMutationResponse,
    ProposalProcessingResetRequest,
    ProposalProcessingResetResponse,
    ProposalsResponse,
    ProposalStatusResponse,
)
from app.services.proposal_service import ProposalGenerationError, ProposalService

router = APIRouter(prefix="/proposals", tags=["proposals"])


def _run_proposal_generation_job(
    job_id: int,
    only_unprocessed: bool,
    max_activities: int | None,
) -> None:
    with SessionLocal() as db:
        job = db.query(ProposalGenerationJob).filter(ProposalGenerationJob.id == job_id).one_or_none()
        if job is None:
            return
        now = utc_now()
        job.status = "running"
        job.started_at = now
        job.updated_at = now
        job.message = "Proposal generation running"
        db.add(job)
        db.commit()
        try:
            summary = ProposalService(db, get_settings()).generate(
                only_unprocessed=only_unprocessed,
                max_activities=max_activities,
                job_id=job_id,
            )
            job = db.query(ProposalGenerationJob).filter(ProposalGenerationJob.id == job_id).one()
            job.status = "success"
            job.finished_at = utc_now()
            job.message = "Proposal generation completed"
            job.error_message = None
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
            db.add(job)
            db.commit()
        except Exception as exc:
            db.rollback()
            job = db.query(ProposalGenerationJob).filter(ProposalGenerationJob.id == job_id).one_or_none()
            if job is not None:
                job.status = "failed"
                job.finished_at = utc_now()
                job.error_message = str(exc)
                job.message = "Proposal generation failed"
                db.add(job)
                db.commit()


@router.post("/generate", response_model=ProposalGenerationSummary)
def generate_proposals(
    request: ProposalGenerationRequest | None = None,
    db: Session = Depends(get_db),
) -> ProposalGenerationSummary:
    try:
        return ProposalService(db, get_settings()).generate(
            only_unprocessed=request.only_unprocessed if request else True,
            max_activities=request.max_activities if request else None,
        )
    except ProposalGenerationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/generate/jobs", response_model=ProposalGenerationJobResponse)
def start_proposal_generation_job(
    background_tasks: BackgroundTasks,
    request: ProposalGenerationRequest | None = None,
    db: Session = Depends(get_db),
) -> ProposalGenerationJobResponse:
    service = ProposalService(db, get_settings())
    running = service.running_job()
    if running is not None:
        return service.job_response(running)

    job = ProposalGenerationJob(
        status="pending",
        message="Proposal generation queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(
        _run_proposal_generation_job,
        job.id,
        request.only_unprocessed if request else True,
        request.max_activities if request else None,
    )
    return service.job_response(job)


@router.get("/generate/jobs/latest", response_model=ProposalGenerationJobResponse)
def latest_proposal_generation_job(db: Session = Depends(get_db)) -> ProposalGenerationJobResponse:
    service = ProposalService(db, get_settings())
    return service.job_response(service.latest_job())


@router.post("/generate/jobs/reset-stale")
def reset_stale_proposal_generation_jobs(db: Session = Depends(get_db)) -> dict[str, int]:
    reset_count = ProposalService(db, get_settings()).reset_stale_jobs()
    return {"jobs_reset": reset_count}


@router.get("/generate/jobs/{job_id}", response_model=ProposalGenerationJobResponse)
def get_proposal_generation_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> ProposalGenerationJobResponse:
    service = ProposalService(db, get_settings())
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Proposal generation job not found")
    return service.job_response(job)


@router.get("", response_model=ProposalsResponse)
def list_proposals(
    status: str | None = "proposed",
    arrondissement: str | None = None,
    street_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    include_raw: bool = False,
    db: Session = Depends(get_db),
) -> ProposalsResponse:
    service = ProposalService(db, get_settings())
    result = service.list_proposals(
        status=status,
        arrondissement=arrondissement,
        street_name=street_name,
        limit=limit,
        offset=offset,
        include_raw=include_raw,
    )
    return ProposalsResponse(
        proposals=result.proposals,
        total=result.total,
        limit=result.limit,
        offset=result.offset,
        returned=result.returned,
        has_more=result.has_more,
        next_offset=result.next_offset,
    )


@router.get("/status", response_model=ProposalStatusResponse)
def proposal_status(db: Session = Depends(get_db)) -> ProposalStatusResponse:
    return ProposalService(db, get_settings()).status()


@router.post("/processing/reset", response_model=ProposalProcessingResetResponse)
def reset_proposal_processing(
    request: ProposalProcessingResetRequest | None = None,
    db: Session = Depends(get_db),
) -> ProposalProcessingResetResponse:
    try:
        return ProposalService(db, get_settings()).reset_processing(
            include_proposals=request.include_proposals if request else False
        )
    except ProposalGenerationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{proposal_id}/dismiss", response_model=ProposalMutationResponse)
def dismiss_proposal(proposal_id: int, db: Session = Depends(get_db)) -> ProposalMutationResponse:
    proposal = ProposalService(db, get_settings()).set_status(proposal_id, "dismissed")
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalMutationResponse(id=proposal.id, status=proposal.status)


@router.post("/{proposal_id}/accept", response_model=ProposalMutationResponse)
def accept_proposal(proposal_id: int, db: Session = Depends(get_db)) -> ProposalMutationResponse:
    proposal = ProposalService(db, get_settings()).set_status(proposal_id, "accepted")
    if proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalMutationResponse(id=proposal.id, status=proposal.status)
