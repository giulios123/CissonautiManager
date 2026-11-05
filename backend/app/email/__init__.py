from app.config import Settings
from app.email.acs import AcsEmailSender
from app.email.base import EmailMessage, EmailSender
from app.email.console import ConsoleEmailSender


def build_email_sender(settings: Settings) -> EmailSender:
    if settings.email_provider == "console":
        return ConsoleEmailSender()
    if settings.email_provider == "acs":
        if not settings.acs_connection_string:
            raise ValueError("EMAIL_PROVIDER=acs requires ACS_CONNECTION_STRING to be set")
        return AcsEmailSender(settings.acs_connection_string, settings.email_from)
    raise ValueError(f"Unsupported EMAIL_PROVIDER: {settings.email_provider!r}")


__all__ = [
    "AcsEmailSender",
    "ConsoleEmailSender",
    "EmailMessage",
    "EmailSender",
    "build_email_sender",
]
