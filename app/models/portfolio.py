from typing import Optional
from sqlmodel import SQLModel, Field


class Portfolio(SQLModel, table=True):
    """An electoral position, e.g. 'President', 'Secretary'."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(unique=True, index=True)
