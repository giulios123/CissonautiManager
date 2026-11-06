from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailAttachment:
    """A file sent with an email. With a `content_id` it is an inline picture that the HTML part
    shows with `<img src="cid:...">`."""

    name: str
    content_type: str
    content: bytes
    content_id: str | None = None


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str
    # Optional HTML version: the plain text stays for clients that do not show HTML.
    html: str | None = None
    attachments: tuple[EmailAttachment, ...] = ()


@dataclass(frozen=True)
class RegistrationExtras:
    """What the organizers customized. Empty fields mean the standard wording."""

    subject: str | None = None
    body: str | None = None
    card_png: bytes | None = None
    card_text: str = ""


class EmailSender(ABC):
    """Outgoing email. Providers: console (development) and Azure Communication Services."""

    @abstractmethod
    def send(self, message: EmailMessage) -> None: ...
