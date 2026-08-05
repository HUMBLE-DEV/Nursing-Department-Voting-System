import uuid

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.vote import Vote
from app.models.candidate import Candidate
from app.models.portfolio import Portfolio
from app.models.voter import Voter
from app.schemas.vote_schemas import ResultsOut, PortfolioResult, CandidateResult


async def candidate_belongs_to_portfolio(
    session: AsyncSession, candidate_uid: uuid.UUID, portfolio_id: int
) -> bool:
    """Stops a tampered request from pairing a President candidate with the Secretary slot."""
    candidate = await session.get(Candidate, candidate_uid)
    return candidate is not None and candidate.portfolio_id == portfolio_id


async def build_results(session: AsyncSession) -> ResultsOut:
    """
    Vote counts are calculated live with COUNT() on every request, instead of
    storing a running counter on the Candidate row. Slightly more DB work, but
    it can never drift out of sync under concurrent voting.

    Portfolios with exactly one candidate are treated as referendums: instead
    of "candidate X: N votes", we report Yes/No totals for that one aspirant.
    """
    portfolios_result = await session.exec(select(Portfolio))
    portfolios = portfolios_result.all()

    total_voters = (
        await session.exec(select(func.count()).select_from(Voter).where(Voter.role == "student"))
    ).one()
    total_votes_cast = (await session.exec(select(func.count()).select_from(Vote))).one()

    portfolio_results = []
    for portfolio in portfolios:
        candidates = (
            await session.exec(select(Candidate).where(Candidate.portfolio_id == portfolio.id))
        ).all()

        is_referendum = len(candidates) == 1

        if is_referendum:
            candidate = candidates[0]
            yes_votes = (
                await session.exec(
                    select(func.count()).select_from(Vote).where(
                        Vote.portfolio_id == portfolio.id, Vote.is_yes == True  # noqa: E712
                    )
                )
            ).one()
            no_votes = (
                await session.exec(
                    select(func.count()).select_from(Vote).where(
                        Vote.portfolio_id == portfolio.id, Vote.is_yes == False  # noqa: E712
                    )
                )
            ).one()
            portfolio_results.append(
                PortfolioResult(
                    portfolio_id=portfolio.id,
                    title=portfolio.title,
                    is_referendum=True,
                    yes_votes=yes_votes,
                    no_votes=no_votes,
                    candidates=[CandidateResult(candidate_uid=candidate.uid, name=candidate.name, votes=yes_votes)],
                )
            )
            continue

        candidate_results = []
        for candidate in candidates:
            vote_count = (
                await session.exec(
                    select(func.count()).select_from(Vote).where(Vote.candidate_uid == candidate.uid)
                )
            ).one()
            candidate_results.append(
                CandidateResult(candidate_uid=candidate.uid, name=candidate.name, votes=vote_count)
            )

        candidate_results.sort(key=lambda c: c.votes, reverse=True)
        portfolio_results.append(
            PortfolioResult(portfolio_id=portfolio.id, title=portfolio.title, candidates=candidate_results)
        )

    return ResultsOut(
        total_voters=total_voters,
        total_votes_cast=total_votes_cast,
        portfolios=portfolio_results,
    )
