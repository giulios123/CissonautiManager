import logging

import pytest

from app.config import Settings
from app.email import AcsEmailSender, ConsoleEmailSender, EmailMessage, build_email_sender


class FakeClient:
    def __init__(self, error: Exception | None = None) -> None:
        self.sent: list[dict] = []
        self.error = error

    def begin_send(self, message: dict):
        if self.error:
            raise self.error
        self.sent.append(message)


MESSAGE = EmailMessage(to="ada@example.com", subject="Ciao", body="Testo della email")


def test_message_is_submitted_with_sender_recipient_and_plain_text():
    client = FakeClient()
    AcsEmailSender("endpoint=x;accesskey=y", "DoNotReply@camp.azurecomm.net", client).send(MESSAGE)
    assert client.sent == [
        {
            "senderAddress": "DoNotReply@camp.azurecomm.net",
            "recipients": {"to": [{"address": "ada@example.com"}]},
            "content": {"subject": "Ciao", "plainText": "Testo della email"},
        }
    ]


def test_a_failed_submission_is_logged_and_not_raised(caplog):
    sender = AcsEmailSender("endpoint=x;accesskey=y", "a@b.c", FakeClient(RuntimeError("boom")))
    with caplog.at_level(logging.ERROR, logger="app.email"):
        sender.send(MESSAGE)  # must not raise
    assert "ada@example.com" in caplog.text
    assert "boom" in caplog.text


def make_settings(**values) -> Settings:
    return Settings(_env_file=None, **values)


def test_console_is_the_default_provider():
    assert isinstance(build_email_sender(make_settings()), ConsoleEmailSender)


def test_acs_provider_builds_the_acs_sender():
    settings = make_settings(
        email_provider="acs",
        email_from="DoNotReply@camp.azurecomm.net",
        acs_connection_string="endpoint=https://camp.communication.azure.com/;accesskey=abc",
    )
    assert isinstance(build_email_sender(settings), AcsEmailSender)


def test_acs_provider_without_connection_string_refuses_to_start():
    with pytest.raises(ValueError, match="ACS_CONNECTION_STRING"):
        build_email_sender(make_settings(email_provider="acs"))


def test_unknown_provider_is_refused():
    with pytest.raises(ValueError, match="Unsupported"):
        build_email_sender(make_settings(email_provider="carrier-pigeon"))


def test_html_and_inline_picture_are_sent_in_the_payload():
    from app.email import EmailAttachment

    client = FakeClient()
    message = EmailMessage(
        to="ada@example.com",
        subject="Ciao",
        body="Testo",
        html='<p>Testo</p><img src="cid:card">',
        attachments=(EmailAttachment("card.png", "image/png", b"\x89PNG", content_id="card"),),
    )
    AcsEmailSender("endpoint=x;accesskey=y", "a@b.c", client).send(message)
    sent = client.sent[0]
    assert sent["content"] == {
        "subject": "Ciao",
        "plainText": "Testo",
        "html": '<p>Testo</p><img src="cid:card">',
    }
    assert sent["attachments"] == [
        {
            "name": "card.png",
            "contentType": "image/png",
            "contentInBase64": "iVBORw==",
            "contentId": "card",
        }
    ]


def test_a_plain_message_has_no_html_or_attachments_key():
    client = FakeClient()
    AcsEmailSender("endpoint=x;accesskey=y", "a@b.c", client).send(MESSAGE)
    assert "attachments" not in client.sent[0]
    assert "html" not in client.sent[0]["content"]


def test_the_console_sender_names_the_extras(caplog):
    from app.email import EmailAttachment

    message = EmailMessage(
        "a@b.c",
        "S",
        "B",
        html="<p>B</p>",
        attachments=(EmailAttachment("c.png", "image/png", b"12", "c"),),
    )
    with caplog.at_level(logging.WARNING, logger="app.email"):
        ConsoleEmailSender().send(message)
    assert "html part" in caplog.text and "c.png image/png 2 bytes cid:c" in caplog.text
