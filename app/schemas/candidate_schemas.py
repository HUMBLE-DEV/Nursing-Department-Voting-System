import uuid
from typing import Optional
from pydantic import BaseModel


class PortfolioCreate(BaseModel):
    title: str


class PortfolioOut(BaseModel):
    id: int
    title: str

    class Config:
        from_attributes = True


class CandidateOut(BaseModel):
    uid: uuid.UUID
    name: str
    bio: str
    photo_url: Optional[str]
    portfolio_id: int

    class Config:
        from_attributes = True
