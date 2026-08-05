from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ElectionSettingsUpdate(BaseModel):
    # Sent as plain "YYYY-MM-DDTHH:MM" strings from an HTML <input type="datetime-local">,
    # interpreted as Ghana local time. Either field can be omitted to leave it unchanged.
    opens_at: Optional[datetime] = None
    closes_at: Optional[datetime] = None


class ElectionSettingsOut(BaseModel):
    opens_at: Optional[datetime]
    closes_at: Optional[datetime]
    voting_open: bool
