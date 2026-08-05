import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.core.security import decode_access_token
from app.models.voter import Voter

# tokenUrl only matters for FastAPI's auto-generated docs page (Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_voter(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Voter:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = decode_access_token(token)
        voter_uid = payload.get("sub")
        if voter_uid is None:
            raise credentials_error
    except jwt.PyJWTError:
        raise credentials_error

    voter = await session.get(Voter, uuid.UUID(voter_uid))
    if voter is None:
        raise credentials_error
    return voter


async def require_admin(voter: Voter = Depends(get_current_voter)) -> Voter:
    if voter.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return voter
