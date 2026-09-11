"""
Root Application and WSGI Entry Point for Production and Deployment.
Supports Gunicorn (app:app or wsgi:app), Docker, Railway, Render, Heroku, and Local Execution.
"""

import sys
import os
from pathlib import Path

# Ensure project root is at the head of sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    HOST,
    PORT,
    DEBUG,
    UPLOAD_IMAGES_DIR,
    UPLOAD_VIDEOS_DIR,
    UPLOAD_TEMP_DIR,
    RESULT_IMAGES_DIR,
    RESULT_VIDEOS_DIR,
    RESULT_LIVE_FRAMES_DIR,
    RESULT_REPORTS_DIR,
    LOGS_DIR,
    DATABASE_PATH,
)
from backend.app import create_app


def ensure_directories():
    """Ensure all required runtime storage directories exist."""
    directories = [
        UPLOAD_IMAGES_DIR,
        UPLOAD_VIDEOS_DIR,
        UPLOAD_TEMP_DIR,
        RESULT_IMAGES_DIR,
        RESULT_VIDEOS_DIR,
        RESULT_LIVE_FRAMES_DIR,
        RESULT_REPORTS_DIR,
        LOGS_DIR,
        DATABASE_PATH.parent,
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)


# Initialize directories and export application instances for WSGI servers
ensure_directories()
app = create_app()
application = app  # Standard WSGI alias


def _safe_get_port(default=8080) -> int:
    """Safely resolve numeric port, ignoring literal '$PORT' or invalid strings."""
    raw = os.environ.get("PORT", os.environ.get("FLASK_PORT", str(default)))
    if isinstance(raw, str) and (raw.startswith("$") or not raw.isdigit()):
        return default
    try:
        val = int(raw)
        return val if 1 <= val <= 65535 else default
    except (ValueError, TypeError):
        return default


if __name__ == "__main__":
    port_to_bind = _safe_get_port(PORT)
    app.run(host="0.0.0.0", port=port_to_bind, debug=DEBUG)
