"""A provider's advertised cost is distinct from the camp's receivable."""


def collectable(price_cents: int, payment_mode: str) -> int:
    return 0 if payment_mode == "provider" else price_cents
