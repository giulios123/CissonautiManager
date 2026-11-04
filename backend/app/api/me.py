from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import current_user
from app.models import Participant

router = APIRouter(prefix="/api", tags=["me"])


class MeOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    personal_code: str


@router.get("/me")
def get_me(user: Participant = Depends(current_user)) -> MeOut:
    return MeOut(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        role=user.role,
        personal_code=user.personal_code,
    )
