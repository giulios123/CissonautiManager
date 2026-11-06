"""Public URL for the active edition's optional event logo."""

from hashlib import sha256

from app.models import Edition


def logo_url(edition: Edition | None) -> str | None:
    if edition is None or edition.logo_image is None:
        return None
    digest = sha256(edition.logo_image).hexdigest()
    return f"/api/public/edition/logo?v={digest}"
