from sqlmodel import select

from app.database import async_session
from app.models.voter import Voter
from app.core.security import hash_password
from app.config import settings


async def create_first_admin():
    """Runs on every startup, but only actually creates an account if no admin exists yet."""
    async with async_session() as session:
        result = await session.exec(select(Voter).where(Voter.role == "admin"))
        if result.first() is not None:
            return  # an admin already exists, nothing to do

        admin = Voter(
            index_number=settings.FIRST_ADMIN_INDEX,
            level="ADMIN",
            email=settings.FIRST_ADMIN_EMAIL,
            password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role="admin",
            is_email_verified=True,  # admin skips the OTP gate for simplicity
        )
        session.add(admin)
        await session.commit()
        print(f"Created first admin account: {settings.FIRST_ADMIN_INDEX}")
