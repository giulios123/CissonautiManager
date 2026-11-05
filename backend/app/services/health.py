"""Dietary needs: the diet, and allergies kept only with the specific consent."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.booking import can_edit_slots, effective_status
from app.domain.meals import check_health_data
from app.models import DOC_HEALTH, Booking, Edition
from app.services import edition as edition_service
from app.services.booking_changes import NotEditable


class ConsentRequired(Exception):
    pass


class ConsentTextChanged(Exception):
    """The consent text was updated after the person read it: they must read it again."""


class NoConsentText(Exception):
    """The admins have not published the consent text yet: allergies cannot be collected."""


def save_dietary(
    db: Session,
    booking: Booking,
    diet: str | None,
    allergies: str | None,
    consent: bool,
    now: datetime,
    consent_version: int | None = None,
) -> Booking:
    """Store the diet and, with consent, the allergies. Without consent nothing health related is
    kept: withdrawing it clears the allergies at once.

    `consent_version` is the version of the text the person read: it must be the current one,
    so a text published while the page was open is never recorded as accepted.
    """
    if not can_edit_slots(effective_status(booking.status, booking.hold_expires_at, now)):
        raise NotEditable()
    check = check_health_data(allergies, consent)
    if not check.ok:
        raise ConsentRequired()
    booking.diet = diet
    booking.allergies = check.allergies
    if consent:
        edition = db.get(Edition, booking.edition_id)
        assert edition is not None
        document = edition_service.latest_legal_document(db, edition, DOC_HEALTH)
        if document is None:
            raise NoConsentText()
        if consent_version != document.version:
            raise ConsentTextChanged()
        if booking.health_consent_document_id != document.id:
            booking.health_consent_document_id = document.id
            booking.health_consent_at = now
    else:
        booking.health_consent_document_id = None
        booking.health_consent_at = None
    db.commit()
    return booking
