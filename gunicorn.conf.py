"""
Production Gunicorn Configuration.
Safely resolves PORT from cloud environment variables (Railway, Render, Heroku)
without shell interpolation issues.
"""

import os

def get_port() -> str:
    """Safely parse integer port from environment."""
    raw = os.environ.get("PORT", os.environ.get("FLASK_PORT", "8080"))
    if isinstance(raw, str) and raw.startswith("$"):
        raw = os.environ.get(raw[1:], "8080")
    try:
        val = int(raw)
        return str(val) if 1 <= val <= 65535 else "8080"
    except (ValueError, TypeError):
        return "8080"

bind = f"0.0.0.0:{get_port()}"
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
