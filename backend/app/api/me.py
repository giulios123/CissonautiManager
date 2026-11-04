from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user
from app.models import Participant
from app.services.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, hash_password

router = APIRouter(prefix="/api", tags=["me"])


class MeOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    personal_code: str
    has_password: bool


class PasswordIn(BaseModel):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


@router.get("/me")
def get_me(user: Participant = Depends(current_user)) -> MeOut:
    return MeOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        personal_code=user.personal_code,
        has_password=user.password_hash is not None,
    )


@router.put("/me/password", status_code=204)
def set_password(
    body: PasswordIn, user: Participant = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    user = db.merge(user)
    user.password_hash = hash_password(body.password)
    db.commit()
