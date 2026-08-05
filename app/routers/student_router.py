from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.core.deps import get_current_voter
from app.models.voter import Voter
from app.models.candidate import Candidate
from app.models.portfolio import Portfolio
from app.models.vote import Vote
from app.schemas.candidate_schemas import CandidateOut
from app.schemas.vote_schemas import VoteSubmit, ResultsOut
from app.services.election_clock import is_voting_open
from app.services.vote_service import candidate_belongs_to_portfolio, build_results

router = APIRouter(prefix="/api/student", tags=["student"])


def _require_verified(voter: Voter):
    """Both the ballot and the results/bar-graph are gated behind email verification."""
    if not voter.is_email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before continuing.")


@router.get("/ballot")
async def get_ballot(
    voter: Voter = Depends(get_current_voter),
    session: AsyncSession = Depends(get_session),
):
    _require_verified(voter)

    portfolios = (await session.exec(select(Portfolio))).all()

    ballot = []
    for portfolio in portfolios:
        candidates = (
            await session.exec(select(Candidate).where(Candidate.portfolio_id == portfolio.id))
        ).all()
        ballot.append({
            "portfolio_id": portfolio.id,
            "title": portfolio.title,
            # exactly one aspirant -> rendered as a Yes/No referendum on the frontend
            "is_referendum": len(candidates) == 1,
            "candidates": [CandidateOut.model_validate(c) for c in candidates],
        })

    return {"voting_open": await is_voting_open(session), "ballot": ballot}


@router.post("/vote")
async def submit_vote(
    payload: VoteSubmit,
    voter: Voter = Depends(get_current_voter),
    session: AsyncSession = Depends(get_session),
):
    _require_verified(voter)

    if not await is_voting_open(session):
        raise HTTPException(status_code=400, detail="Voting has closed.")

    # validate every choice belongs to the portfolio it claims, and that referendum
    # (single-candidate) portfolios include a Yes/No answer — BEFORE touching the database
    for choice in payload.choices:
        valid = await candidate_belongs_to_portfolio(session, choice.candidate_uid, choice.portfolio_id)
        if not valid:
            raise HTTPException(status_code=400, detail="Invalid candidate/portfolio pairing.")

        candidate_count = (
            await session.exec(select(Candidate).where(Candidate.portfolio_id == choice.portfolio_id))
        ).all()
        is_referendum = len(candidate_count) == 1

        if is_referendum and choice.is_yes is None:
            raise HTTPException(status_code=400, detail="Please answer Yes or No for this portfolio.")
        if not is_referendum and choice.is_yes is not None:
            raise HTTPException(status_code=400, detail="This portfolio does not use Yes/No voting.")

    try:
        for choice in payload.choices:
            session.add(
                Vote(
                    voter_uid=voter.uid,
                    portfolio_id=choice.portfolio_id,
                    candidate_uid=choice.candidate_uid,
                    is_yes=choice.is_yes,
                )
            )
        await session.commit()
    except IntegrityError:
        # this fires if the unique(voter_uid, portfolio_id) constraint is violated —
        # i.e. this student already voted for one of these portfolios
        await session.rollback()
        raise HTTPException(status_code=400, detail="You have already voted for one or more of these portfolios.")

    return {"message": "Vote submitted successfully."}


@router.get("/results", response_model=ResultsOut)
async def student_results(
    voter: Voter = Depends(get_current_voter),
    session: AsyncSession = Depends(get_session),
):
    # only email-verified students can view the live results bar graph
    _require_verified(voter)
    return await build_results(session)
