import aiosmtplib
from email.message import EmailMessage

from src.config.settings import settings


async def send_reset_email(email: str, token: str) -> None:
    """Send password reset email with reset link."""
    if not settings.smtp_host:
        print(f"SMTP not configured. Reset token for {email}: {token}")
        return

    reset_link = (
        f"{settings.frontend_url}/reset-account?token={token}&email={email}"
    )

    msg = EmailMessage()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = email
    msg["Subject"] = "Reset Your Account - Tools Sync"
    msg.set_content(
        f"You requested an account reset for Tools Sync.\n\n"
        f"WARNING: Resetting your account will permanently delete all your "
        f"synced data. This action cannot be undone.\n\n"
        f"Click the link below to reset your account:\n"
        f"{reset_link}\n\n"
        f"This link expires in 1 hour.\n\n"
        f"If you did not request this reset, you can safely ignore this email."
    )

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        use_tls=settings.smtp_secure,
        username=settings.smtp_user,
        password=settings.smtp_pass,
    )
