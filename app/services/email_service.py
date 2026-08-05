import smtplib
from email.mime.text import MIMEText

from app.config import settings


def send_otp_email(to_email: str, otp_code: str) -> None:
    """
    Sends the one-time verification code by email.
    If SMTP credentials aren't set (e.g. while developing locally), the code
    is printed to the console instead, so you're never blocked during testing.
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

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
