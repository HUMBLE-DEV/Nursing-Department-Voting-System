import uuid
from typing import Optional
from sqlmodel import SQLModel, Field


class Candidate(SQLModel, table=True):
    """A person running for a specific Portfolio."""
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    bio: str = Field(default="", max_length=300)
    photo_url: Optional[str] = Field(default=None)
    portfolio_id: int = Field(foreign_key="portfolio.id")
