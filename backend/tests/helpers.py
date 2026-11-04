from datetime import date


def payload(slot_ids_list, **overrides):
    body = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "phone": "+39 333 1234567",
        "invited_by": "Grace",
        "can_bring": "Un talk sulle macchine analitiche",
        "slot_ids": slot_ids_list,
        "accept_privacy": True,
        "accept_disclaimer": True,
        "privacy_version": 1,
        "disclaimer_version": 1,
    }
    body.update(overrides)
    return body


def d(day: int) -> date:
    return date(2026, 7, day)
