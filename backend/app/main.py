from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.config import Settings, get_settings


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
    app = FastAPI(title="Cisonauti Booking", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.settings = settings

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    static_dir = Path(settings.static_dir)
    if (static_dir / "index.html").is_file():
        _mount_frontend(app, static_dir)

    return app


app = create_app()
