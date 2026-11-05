import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_release_notes(path: str) -> list[dict]:
    """Releases generated at deploy time, newest first. A missing or broken file means no notes:
    locally nothing generates it, and the guide must still work."""
    file = Path(path)
    if not file.is_file():
        return []
    try:
        releases = json.loads(file.read_text(encoding="utf-8")).get("releases", [])
    except (OSError, ValueError, AttributeError):
        logger.warning("Release notes file %s cannot be read", path)
        return []
    return releases if isinstance(releases, list) else []
