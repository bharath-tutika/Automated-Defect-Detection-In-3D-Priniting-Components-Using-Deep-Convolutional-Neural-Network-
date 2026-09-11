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


import socket


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.bind((host, port))
            return True
    except OSError:
        return False


def _safe_get_port(default=8080) -> int:
    """Safely resolve numeric port, ignoring literal '$PORT' or invalid strings."""
    raw = os.environ.get("PORT", os.environ.get("FLASK_PORT", str(default)))
    if isinstance(raw, str):
        raw = raw.strip()
        if raw.startswith("$"):
            raw = os.environ.get(raw[1:], str(default))
    try:
        val = int(raw)
        if 1 <= val <= 65535:
            return val
    except (ValueError, TypeError):
        pass
    return default


def get_bound_port(preferred: int = 8080, host: str = "0.0.0.0") -> int:
    """Return preferred port if available, or dynamically find the next open port."""
    if is_port_available(preferred, host):
        return preferred
    
    # In cloud environments with explicit PORT variable, stick to preferred
    if "PORT" in os.environ and os.environ["PORT"].strip() != "":
        return preferred

    # Local fallback search across alternate standard ports
    candidates = [8080, 5000, 8000, 8888, 5001, 8081, 8082, 3000]
    for p in candidates:
        if p != preferred and is_port_available(p, host):
            print(f"[PORT NOTICE] Port {preferred} was in use; automatically selected available port {p}.")
            return p
            
    return preferred


if __name__ == "__main__":
    initial_port = _safe_get_port(PORT)
    port_to_bind = get_bound_port(initial_port, "0.0.0.0")
    print(f"Server starting on http://0.0.0.0:{port_to_bind} (http://localhost:{port_to_bind})")
    app.run(host="0.0.0.0", port=port_to_bind, debug=DEBUG)

