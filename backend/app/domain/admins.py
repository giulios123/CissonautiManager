from dataclasses import dataclass

SELF = "self"
SEED = "seed_admin"
LAST = "last_admin"


@dataclass(frozen=True)
class RemoveCheck:
    allowed: bool
    reason: str | None = None


def can_remove_admin(
    target_id: int,
    actor_id: int,
    admin_count: int,
    target_email: str,
    seed_email: str | None,
) -> RemoveCheck:
    """Admins cannot remove themselves, the admin set by ADMIN_EMAIL, or the last admin.

    The seed admin is promoted again at every startup, so removing it from the panel would
    silently not stick: it is changed through the environment variable instead.
    """
    if target_id == actor_id:
        return RemoveCheck(False, SELF)
    if seed_email and target_email.strip().lower() == seed_email.strip().lower():
        return RemoveCheck(False, SEED)
    if admin_count <= 1:
        return RemoveCheck(False, LAST)
    return RemoveCheck(True)
