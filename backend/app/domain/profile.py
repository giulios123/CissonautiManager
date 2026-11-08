"""Shared profile value checks used by public, participant and admin APIs."""

import unicodedata
from collections.abc import Mapping, Sequence
from urllib.parse import urlsplit

ABSENT_PROFILE_VALUES = {"none", "non possiedo", "i don't have it"}
ITALY_NAMES = {"italia", "italy"}


class InvalidProfileValue(ValueError):
    def __init__(self, message_key: str) -> None:
        self.message_key = message_key
        super().__init__(message_key)


def fold_geographic_text(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(char)
    )


def validate_social_profiles(telegram: str, linkedin: str) -> None:
    telegram_value = telegram.strip()
    if telegram_value.casefold() not in ABSENT_PROFILE_VALUES and not (
        telegram_value.startswith("@")
    ):
        raise InvalidProfileValue("profile.invalid_telegram")

    linkedin_value = linkedin.strip()
    if linkedin_value.casefold() in ABSENT_PROFILE_VALUES:
        return
    try:
        parsed = urlsplit(linkedin_value)
    except ValueError as exc:
        raise InvalidProfileValue("profile.invalid_linkedin") from exc
    hostname = (parsed.hostname or "").casefold()
    if (
        parsed.scheme.casefold() != "https"
        or not (hostname == "linkedin.com" or hostname.endswith(".linkedin.com"))
        or not parsed.path.strip("/")
    ):
        raise InvalidProfileValue("profile.invalid_linkedin")


def validate_geography(
    city: str,
    country: str,
    province: str | None,
    istat_code: str | None,
    municipalities: Sequence[Mapping[str, str]],
) -> None:
    if istat_code:
        municipality = next(
            (item for item in municipalities if item["istat_code"] == istat_code), None
        )
        if (
            municipality is None
            or country.strip().casefold() not in ITALY_NAMES
            or fold_geographic_text(municipality["name"]) != fold_geographic_text(city)
            or municipality["province"] != (province or "")
        ):
            raise InvalidProfileValue("profile.invalid_municipality")
    elif country.strip().casefold() in ITALY_NAMES and not (province or "").strip():
        raise InvalidProfileValue("profile.province_required")
