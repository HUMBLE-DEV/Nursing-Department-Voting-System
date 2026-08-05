import uuid
from typing import List, Optional
from pydantic import BaseModel


class VoteChoice(BaseModel):
    portfolio_id: int
    candidate_uid: uuid.UUID
    # Only used for referendum-style portfolios (exactly one candidate).
    # True = Yes, False = No, None = normal multi-candidate portfolio.
    is_yes: Optional[bool] = None


class VoteSubmit(BaseModel):
    choices: List[VoteChoice]


class CandidateResult(BaseModel):
    candidate_uid: uuid.UUID
    name: str
    votes: int


class PortfolioResult(BaseModel):
    portfolio_id: int
    title: str
    is_referendum: bool = False   # True when this was a single-aspirant Yes/No vote
    yes_votes: int = 0
    no_votes: int = 0
    candidates: List[CandidateResult]


class ResultsOut(BaseModel):
    total_voters: int
    total_votes_cast: int
    portfolios: List[PortfolioResult]
