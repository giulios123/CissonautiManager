import secrets

# No 0/O, 1/I/L: codes are read aloud and typed into payment descriptions.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_PREFIX = "CSC-"
CODE_LENGTH = 4


def generate_personal_code() -> str:
    """Personal code used as payment reference, e.g. CSC-7K3P."""
    suffix = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
    return f"{CODE_PREFIX}{suffix}"
