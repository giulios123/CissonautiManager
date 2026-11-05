import logging

from app.email.base import EmailMessage, EmailSender

logger = logging.getLogger("app.email")


class ConsoleEmailSender(EmailSender):
    """Writes emails to the log instead of sending them. For local development."""

    def send(self, message: EmailMessage) -> None:
        logger.warning("EMAIL to=%s subject=%s\n%s\n", message.to, message.subject, message.body)
