import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import admin_edition as admin_edition_api
from app.api import admin_registrations as admin_registrations_api
from app.api import admin_views as admin_views_api
from app.api import auth as auth_api
from app.api import me as me_api
from app.api import public as public_api
from app.config import Settings, get_settings
from app.db import get_db, make_engine, make_session_factory, utcnow
from app.email import build_email_sender
from app.services.participants import ensure_admin

logger = logging.getLogger(__name__)

# Only the public registration page may be embedded, and only by Google Sites.
EMBED_ANCESTORS = "https://sites.google.com https://*.googleusercontent.com"


def _mount_frontend(app: FastAPI, static_dir: Path) -> None:
    """Serve the built frontend, falling back to index.html for client-side routes."""
    index = static_dir / "index.html"
    root = static_dir.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (static_dir / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        return FileResponse(index)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if settings.admin_email:
            with app.state.session_factory() as db:
                ensure_admin(db, settings.admin_email, settings.admin_password)
        else:
            logger.warning("ADMIN_EMAIL is not set: no admin will be created")
        yield

    app = FastAPI(
        title="Cissonauti Booking",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = make_engine(settings.database_url)
    app.state.session_factory = make_session_factory(app.state.engine)
    app.state.email_sender = build_email_sender(settings)
    app.state.clock = utcnow

    @app.get("/api/health")
    def health(db: Session = Depends(get_db)) -> dict[str, str]:
        try:
            db.execute(text("SELECT 1"))
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Database unavailable") from exc
        return {"status": "ok"}

    app.include_router(auth_api.router)
    app.include_router(me_api.router)
    app.include_router(admin_edition_api.router)
    app.include_router(admin_registrations_api.router)
    app.include_router(admin_views_api.router)
    app.include_router(public_api.router)

    @app.middleware("http")
    async def frame_policy(request: Request, call_next):
        response = await call_next(request)
        embeddable = request.url.path.rstrip("/") == "/iscrizione"
        response.headers["Content-Security-Policy"] = (
            f"frame-ancestors {EMBED_ANCESTORS}" if embeddable else "frame-ancestors 'self'"
        )
        return response

    static_dir = Path(settings.static_dir)
    if (static_dir / "index.html").is_file():
        _mount_frontend(app, static_dir)

    return app


app = create_app()
