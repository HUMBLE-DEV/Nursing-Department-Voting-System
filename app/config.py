import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Database ---
    # SQLite is fine for a single-department election (~600 students).
    # The file lives at ./voting.db relative to wherever the app runs.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./voting.db")
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")
    # --- JWT ---
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # NOTE: the election opening/closing time is no longer set here.
    # The admin now sets it from the dashboard (stored in the ElectionSettings table).

    # --- Email (SMTP) for OTP verification ---
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    OTP_EXPIRE_MINUTES: int = 10

    # --- First admin bootstrap (created automatically on first run) ---
    FIRST_ADMIN_INDEX: str = os.getenv("FIRST_ADMIN_INDEX", "ADMIN001")
    FIRST_ADMIN_PASSWORD: str = os.getenv("FIRST_ADMIN_PASSWORD", "changeme123")
    FIRST_ADMIN_EMAIL: str = os.getenv("FIRST_ADMIN_EMAIL", "admin@example.com")


settings = Settings()
