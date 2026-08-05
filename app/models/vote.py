import uuid
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


class Vote(SQLModel, table=True):
    """
    One student's vote for one candidate in one portfolio.
    The unique constraint is the real double-voting guard: even if two requests
    hit the server at the exact same millisecond, the database itself rejects
    the second insert for the same (voter, portfolio) pair.

    is_yes is only used for "referendum" portfolios — ones with exactly one
    aspirant, voted on as Yes/No rather than picked from a list. It's None
    for normal multi-candidate portfolios.
    """
    __table_args__ = (UniqueConstraint("voter_uid", "portfolio_id", name="uq_voter_portfolio"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    voter_uid: uuid.UUID = Field(foreign_key="voter.uid")
    portfolio_id: int = Field(foreign_key="portfolio.id")
    candidate_uid: uuid.UUID = Field(foreign_key="candidate.uid")
    is_yes: Optional[bool] = Field(default=None)
