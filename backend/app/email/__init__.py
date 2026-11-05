from app.config import Settings
from app.email.base import EmailMessage, EmailSender
from app.email.console import ConsoleEmailSender


def build_email_sender(settings: Settings) -> EmailSender:
    if settings.email_provider == "console":
        return ConsoleEmailSender()
    raise ValueError(f"Unsupported EMAIL_PROVIDER: {settings.email_provider!r}")


__all__ = ["ConsoleEmailSender", "EmailMessage", "EmailSender", "build_email_sender"]
