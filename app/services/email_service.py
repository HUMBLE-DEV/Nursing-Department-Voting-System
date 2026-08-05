import smtplib
import socket
from email.mime.text import MIMEText

from app.config import settings


def send_otp_email(to_email: str, otp_code: str) -> None:
    """
    Sends the one-time verification code by email.
    If SMTP credentials aren't set (e.g. while developing locally), the code
    is printed to the console instead, so you're never blocked during testing.

    IMPORTANT: this function is meant to be run via FastAPI's BackgroundTasks
    (see auth_router.py), not called directly inside a request — that way a
    slow or unreachable SMTP server can never hang the response the student
    is waiting on. It also never raises: a failed send is logged, not thrown,
    so it can't crash the request that queued it.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"[DEV MODE - no SMTP configured] OTP for {to_email}: {otp_code}")
        return

    message = MIMEText(
        f"Your voting portal verification code is: {otp_code}\n"
        f"This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.\n\n"
        f"If you did not request this, you can ignore this email."
    )
    message["Subject"] = "Your Voting Portal Verification Code"
    message["From"] = settings.SMTP_USER
    message["To"] = to_email

    try:
        # timeout=10 means a dead/blocked connection fails fast instead of
        # hanging for the default (much longer) socket timeout
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except (smtplib.SMTPException, socket.error, OSError) as err:
        # Common causes: wrong SMTP_HOST/PORT, a Gmail password instead of an
        # App Password, or the network/firewall blocking outbound port 587.
        print(f"[EMAIL SEND FAILED] Could not send OTP to {to_email}: {err}")
        print(f"[EMAIL SEND FAILED] For reference, the code was: {otp_code}")
