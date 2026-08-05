from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.roster import ApprovedRoster


async def index_exists_in_roster(session: AsyncSession, level: str, index_number: str) -> bool:
    """
    This is the check you asked for: confirms the index number the student
    typed actually belongs to that level, according to the admin's uploaded roster.
    """
    statement = select(ApprovedRoster).where(
        ApprovedRoster.level == level,
        ApprovedRoster.index_number == index_number,
    )
    result = await session.exec(statement)
    return result.first() is not None
