import csv
import io
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.core.deps import require_admin
from app.models.portfolio import Portfolio
from app.models.candidate import Candidate
from app.models.roster import ApprovedRoster
from app.models.vote import Vote
from app.schemas.candidate_schemas import PortfolioCreate, PortfolioOut, CandidateOut
from app.schemas.vote_schemas import ResultsOut
from app.schemas.election_schemas import ElectionSettingsUpdate, ElectionSettingsOut
from app.services.vote_service import build_results
from app.services.election_clock import get_settings, is_voting_open, to_naive_utc, to_ghana_local, GHANA_TZ

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/portfolios", response_model=PortfolioOut)
async def create_portfolio(payload: PortfolioCreate, session: AsyncSession = Depends(get_session)):
    existing = await session.exec(select(Portfolio).where(Portfolio.title == payload.title))
    if existing.first() is not None:
        raise HTTPException(status_code=400, detail="Portfolio already exists.")
    portfolio = Portfolio(title=payload.title)
    session.add(portfolio)
    await session.commit()
    await session.refresh(portfolio)
    return portfolio


@router.get("/portfolios", response_model=List[PortfolioOut])
async def list_portfolios(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Portfolio))
    return result.all()


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(portfolio_id: int, session: AsyncSession = Depends(get_session)):
    """
    Deletes a portfolio the admin added by mistake, along with any candidates
    and votes attached to it. Use with care once voting has started — this
    permanently removes any votes already cast for it.
    """
    portfolio = await session.get(Portfolio, portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    # delete dependent rows first (SQLite doesn't cascade-delete automatically)
    votes = (await session.exec(select(Vote).where(Vote.portfolio_id == portfolio_id))).all()
    for vote in votes:
        await session.delete(vote)

    candidates = (await session.exec(select(Candidate).where(Candidate.portfolio_id == portfolio_id))).all()
    for candidate in candidates:
        await session.delete(candidate)

    await session.delete(portfolio)
    await session.commit()
    return {"message": f'"{portfolio.title}" and its candidates/votes were deleted.'}


@router.post("/candidates", response_model=CandidateOut)
async def create_candidate(
    name: str = Form(...),
    bio: str = Form(""),
    portfolio_id: int = Form(...),
    photo: UploadFile = File(None),
    session: AsyncSession = Depends(get_session),
):
    portfolio = await session.get(Portfolio, portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found.")

    photo_url = None
    if photo is not None and photo.filename:
        extension = photo.filename.rsplit(".", 1)[-1] if "." in photo.filename else "jpg"
        filename = f"{uuid.uuid4()}.{extension}"
        file_path = f"static/candidates/{filename}"
        contents = await photo.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        photo_url = f"/{file_path}"

    candidate = Candidate(name=name, bio=bio, portfolio_id=portfolio_id, photo_url=photo_url)
    session.add(candidate)
    await session.commit()
    await session.refresh(candidate)
    return candidate


@router.get("/candidates", response_model=List[CandidateOut])
async def list_candidates(session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Candidate))
    return result.all()


@router.post("/roster/upload")
async def upload_roster(file: UploadFile = File(...), session: AsyncSession = Depends(get_session)):
    """
    Accepts a CSV with two columns: level,index_number
    Example row: 300,UENR/CS/21/0045
    Run this ONCE before registration opens, with every eligible student in it.
    """
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))

    added = 0
    for row in reader:
        level = (row.get("level") or "").strip()
        index_number = (row.get("index_number") or "").strip()
        if not level or not index_number:
            continue

        existing = await session.exec(
            select(ApprovedRoster).where(
                ApprovedRoster.level == level, ApprovedRoster.index_number == index_number
            )
        )
        if existing.first() is not None:
            continue

        session.add(ApprovedRoster(level=level, index_number=index_number))
        added += 1

    await session.commit()
    return {"message": f"{added} roster entries added."}


@router.get("/results", response_model=ResultsOut)
async def get_results(session: AsyncSession = Depends(get_session)):
    return await build_results(session)


@router.get("/election-settings", response_model=ElectionSettingsOut)
async def get_election_settings(session: AsyncSession = Depends(get_session)):
    settings = await get_settings(session)
    return ElectionSettingsOut(
        opens_at=to_ghana_local(settings.opens_at) if settings.opens_at else None,
        closes_at=to_ghana_local(settings.closes_at) if settings.closes_at else None,
        voting_open=await is_voting_open(session),
    )


@router.post("/election-settings", response_model=ElectionSettingsOut)
async def update_election_settings(
    payload: ElectionSettingsUpdate, session: AsyncSession = Depends(get_session)
):
    """
    The admin submits opens_at/closes_at as Ghana-local datetimes (from a
    datetime-local input on the dashboard). We store them as naive UTC.
    """
    settings = await get_settings(session)

    if payload.opens_at is not None:
        settings.opens_at = to_naive_utc(payload.opens_at.replace(tzinfo=GHANA_TZ))
    if payload.closes_at is not None:
        settings.closes_at = to_naive_utc(payload.closes_at.replace(tzinfo=GHANA_TZ))

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    return ElectionSettingsOut(
        opens_at=to_ghana_local(settings.opens_at) if settings.opens_at else None,
        closes_at=to_ghana_local(settings.closes_at) if settings.closes_at else None,
        voting_open=await is_voting_open(session),
    )
