from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.proposals import (
    ProposalGenerationSummary,
    ProposalMutationResponse,
    ProposalsResponse,
    ProposalStatusResponse,
)
from app.services.proposal_service import ProposalGenerationError, ProposalService

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("/generate", response_model=ProposalGenerationSummary)
def generate_proposals(db: Session = Depends(get_db)) -> ProposalGenerationSummary:
    try:
        return ProposalService(db, get_settings()).generate()
    except ProposalGenerationError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("", response_model=ProposalsResponse)
def list_proposals(
    status: str | None = "proposed",
    arrondissement: str | None = None,
    street_name: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    include_raw: bool = False,
    db: Session = Depends(get_db),
) -> ProposalsResponse:
    return ProposalsResponse(
        proposals=ProposalService(db, get_settings()).list_proposals(
            status=status,
            arrondissement=arrondissement,
            street_name=street_name,
            limit=limit,
            include_raw=include_raw,
        )
    )


@router.get("/status", response_model=ProposalStatusResponse)
def proposal_status(db: Session = Depends(get_db)) -> ProposalStatusResponse:
    return ProposalService(db, get_settings()).status()


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
