from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.election_settings import ElectionSettings

# The admin sets times in Ghana local time; we convert to/from this zone
# whenever we talk to a human, but store everything as naive UTC in the DB
# (naive, because SQLite/Postgres both drop timezone info by default, and
# comparing an aware "now" against a naive stored value throws an error).
GHANA_TZ = timezone.utc

async def get_settings(session: AsyncSession) -> ElectionSettings:
    """Always returns the single settings row, creating an empty one if needed."""
    settings = await session.get(ElectionSettings, 1)
    if settings is None:
        settings = ElectionSettings(id=1, opens_at=None, closes_at=None)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


async def is_voting_open(session: AsyncSession) -> bool:
    """
    Voting is open when:
    - no opens_at is set, OR now is past opens_at, AND
    - no closes_at is set, OR now is before closes_at.
    If the admin hasn't configured anything yet, voting is OPEN by default —
    this is deliberate so testing isn't blocked, but it means you MUST set a
    real closing time before a real election, or it never locks.
    """
    settings = await get_settings(session)
    now = datetime.utcnow()

    if settings.opens_at is not None and now < settings.opens_at:
        return False
    if settings.closes_at is not None and now >= settings.closes_at:
        return False
    return True


def to_naive_utc(local_dt: datetime) -> datetime:
    """Converts a Ghana-local datetime (from the admin's form) into naive UTC for storage."""
    if local_dt.tzinfo is None:
        local_dt = local_dt.replace(tzinfo=GHANA_TZ)
    return local_dt.astimezone(timezone.utc).replace(tzinfo=None)


def to_ghana_local(naive_utc_dt: datetime) -> datetime:
    """Converts a stored naive-UTC datetime back into Ghana-local, for showing the admin."""
    return naive_utc_dt.replace(tzinfo=timezone.utc).astimezone(GHANA_TZ)
