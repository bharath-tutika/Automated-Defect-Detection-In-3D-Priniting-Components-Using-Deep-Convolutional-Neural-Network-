"""
Root application entry point for Railway, Railpack, Nixpacks, and WSGI servers (gunicorn).
Exposes a module-level `app` Flask instance for gunicorn to import as `app:app`.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
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


# Create directories and Flask app at module level so gunicorn can import `app`
ensure_directories()
app = create_app()

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
