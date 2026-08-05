from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    index_number: str
    level: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    index_number: str
    password: str


class OTPVerifyRequest(BaseModel):
    index_number: str
    otp_code: str


class ForgotPasswordRequest(BaseModel):
    index_number: str
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    index_number: str
    otp_code: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class MessageResponse(BaseModel):
    message: str
