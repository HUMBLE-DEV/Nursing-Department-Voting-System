from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ElectionSettings(SQLModel, table=True):
    """
    A single-row table holding the voting window the admin sets.
    We always work with id=1 — there's only ever one election window at a time.
    Datetimes are stored as naive UTC (see election_clock.py for why).
    """
    id: Optional[int] = Field(default=1, primary_key=True)
    opens_at: Optional[datetime] = Field(default=None)
    closes_at: Optional[datetime] = Field(default=None)