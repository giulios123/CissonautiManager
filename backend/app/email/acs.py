import base64
import logging

from azure.communication.email import EmailClient

from app.email.base import EmailAttachment, EmailMessage, EmailSender

logger = logging.getLogger("app.email")


def _attachment(attachment: EmailAttachment) -> dict:
    data = {
        "name": attachment.name,
        "contentType": attachment.content_type,
        "contentInBase64": base64.b64encode(attachment.content).decode("ascii"),
    }
    if attachment.content_id:
        data["contentId"] = attachment.content_id
    return data


class AcsEmailSender(EmailSender):
    """Sends emails through Azure Communication Services.

    `begin_send` only submits the message (the service answers 202), so the request is quick.
    A rejected submission is logged and never raised: by the time an email goes out the change
    that triggered it is already committed and must not be undone by a mail problem.
    """

    def __init__(self, connection_string: str, sender_address: str, client=None) -> None:
        self._client = client or EmailClient.from_connection_string(connection_string)
        self._sender_address = sender_address

    def send(self, message: EmailMessage) -> None:
        content = {"subject": message.subject, "plainText": message.body}
        if message.html:
            content["html"] = message.html
        payload: dict = {
            "senderAddress": self._sender_address,
            "recipients": {"to": [{"address": message.to}]},
            "content": content,
        }
        if message.attachments:
            payload["attachments"] = [_attachment(a) for a in message.attachments]
        try:
            self._client.begin_send(payload)
        except Exception:
            logger.exception("EMAIL not sent to=%s subject=%s", message.to, message.subject)
