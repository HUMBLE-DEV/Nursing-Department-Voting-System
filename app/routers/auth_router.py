from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.voter import Voter
from app.schemas.auth_schemas import (
    RegisterRequest, LoginRequest, OTPVerifyRequest, TokenResponse, MessageResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.core.security import hash_password, verify_password, create_access_token, generate_otp
from app.services.roster_service import index_exists_in_roster
from app.services.email_service import send_otp_email
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)):
    # Step 1: this index number must genuinely belong to this level, per the admin's roster
    is_valid = await index_exists_in_roster(session, payload.level, payload.index_number)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Index number not found for this level. Contact your department admin.",
        )

    # Step 2: block duplicate accounts
    existing = await session.exec(
        select(Voter).where(
            (Voter.index_number == payload.index_number) | (Voter.email == payload.email)
        )
    )
    if existing.first() is not None:
        raise HTTPException(status_code=400, detail="This index number or email is already registered.")

    voter = Voter(
        index_number=payload.index_number,
        level=payload.level,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="student",
    )
    session.add(voter)
    await session.commit()
    return MessageResponse(message="Registration successful. You can now log in.")


@router.post("/login", response_model=MessageResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Voter).where(Voter.index_number == payload.index_number))
    voter = result.first()
    if voter is None or not verify_password(payload.password, voter.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect index number or password.")

    # Password is correct, but a token is NOT issued yet — an email OTP is required first
    otp = generate_otp()
    voter.otp_code = otp
    voter.otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    session.add(voter)
    await session.commit()

    send_otp_email(voter.email, otp)
    return MessageResponse(message="Password confirmed. A verification code has been sent to your email.")


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(payload: OTPVerifyRequest, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Voter).where(Voter.index_number == payload.index_number))
    voter = result.first()

    if voter is None or voter.otp_code is None:
        raise HTTPException(status_code=400, detail="No pending verification for this account.")

    if voter.otp_expires_at is None or datetime.utcnow() > voter.otp_expires_at:
        raise HTTPException(status_code=400, detail="Verification code expired. Please log in again.")

    if payload.otp_code != voter.otp_code:
        raise HTTPException(status_code=400, detail="Incorrect verification code.")

    # correct code — clear it (one-time use only) and mark the account verified
    voter.otp_code = None
    voter.otp_expires_at = None
    voter.is_email_verified = True
    session.add(voter)
    await session.commit()

    token = create_access_token(data={"sub": str(voter.uid)})
    return TokenResponse(access_token=token, role=voter.role)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    """
    Sends a reset code — but ONLY if the index number AND email both match an
    existing account. Either way, the response message is identical, so this
    endpoint can't be used to check whether a given index number is registered.
    """
    result = await session.exec(select(Voter).where(Voter.index_number == payload.index_number))
    voter = result.first()

    generic_message = "If that index number and email match an account, a reset code has been sent."

    if voter is None or voter.email.lower() != payload.email.lower():
        return MessageResponse(message=generic_message)

    otp = generate_otp()
    voter.otp_code = otp
    voter.otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    session.add(voter)
    await session.commit()

    send_otp_email(voter.email, otp)
    return MessageResponse(message=generic_message)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Voter).where(Voter.index_number == payload.index_number))
    voter = result.first()

    if voter is None or voter.otp_code is None:
        raise HTTPException(status_code=400, detail="No pending reset request for this account.")

    if voter.otp_expires_at is None or datetime.utcnow() > voter.otp_expires_at:
        raise HTTPException(status_code=400, detail="Reset code expired. Please request a new one.")

    if payload.otp_code != voter.otp_code:
        raise HTTPException(status_code=400, detail="Incorrect reset code.")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    voter.password_hash = hash_password(payload.new_password)
    voter.otp_code = None
    voter.otp_expires_at = None
    session.add(voter)
    await session.commit()

    return MessageResponse(message="Password reset successful. You can now log in with your new password.")
