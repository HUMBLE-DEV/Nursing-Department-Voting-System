from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


class ApprovedRoster(SQLModel, table=True):
    """
    The pre-loaded list of eligible students (level + index number), uploaded
    by the admin via CSV before registration opens. Registration checks this
    table so nobody can sign up with a fake index number.
    """
    __tablename__ = "approved_roster"
    __table_args__ = (UniqueConstraint("level", "index_number", name="uq_level_index"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    level: str = Field(index=True)
    index_number: str = Field(index=True)
