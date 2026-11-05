import logging

from app.email.base import EmailMessage, EmailSender

logger = logging.getLogger("app.email")


class ConsoleEmailSender(EmailSender):
    """Writes emails to the log instead of sending them. For local development."""

    def send(self, message: EmailMessage) -> None:
        extra = ""
        if message.html:
            extra += f"\n[html part, {len(message.html)} characters]"
        for attachment in message.attachments:
            extra += (
                f"\n[attachment {attachment.name} {attachment.content_type} "
                f"{len(attachment.content)} bytes"
                + (f" cid:{attachment.content_id}" if attachment.content_id else "")
                + "]"
            )
        logger.warning(
            "EMAIL to=%s subject=%s\n%s%s\n", message.to, message.subject, message.body, extra
        )
