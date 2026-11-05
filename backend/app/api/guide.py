from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings
from app.deps import get_settings_dep, require_admin
from app.models import Participant
from app.services.release_notes import load_release_notes

router = APIRouter(tags=["guide"])


class VersionOut(BaseModel):
    version: str
    built_at: datetime | None = None


class ReleaseOut(BaseModel):
    version: str
    date: datetime | None = None
    features: list[str] = []
    fixes: list[str] = []


class ReleaseNotesOut(BaseModel):
    releases: list[ReleaseOut]


@router.get("/api/version", response_model=VersionOut)
def version(settings: Settings = Depends(get_settings_dep)) -> VersionOut:
    built_at = datetime.fromisoformat(settings.built_at) if settings.built_at else None
    return VersionOut(version=settings.app_version, built_at=built_at)


@router.get("/api/admin/release-notes", response_model=ReleaseNotesOut)
def release_notes(
    _: Participant = Depends(require_admin), settings: Settings = Depends(get_settings_dep)
) -> ReleaseNotesOut:
    return ReleaseNotesOut(releases=load_release_notes(settings.release_notes_path))
