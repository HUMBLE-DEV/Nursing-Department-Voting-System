import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Voter(SQLModel, table=True):
    """
    A registered user — either a student ("student") or a department admin ("admin").
    Students must exist in ApprovedRoster (level + index_number) before they can register.
    """
    uid: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    index_number: str = Field(unique=True, index=True)
    level: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: str = Field(default="student")  # "student" or "admin"

    # Email OTP verification (checked at login, required before viewing ballot/results)
    is_email_verified: bool = Field(default=False)
    otp_code: Optional[str] = Field(default=None)
    otp_expires_at: Optional[datetime] = Field(default=None)
