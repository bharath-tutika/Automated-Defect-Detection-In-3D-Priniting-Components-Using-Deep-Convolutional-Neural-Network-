import os

def _get_port():
    raw = os.environ.get("PORT", os.environ.get("FLASK_PORT", "8080"))
    try:
        return str(int(raw))
    except (ValueError, TypeError):
        return "8080"

bind = f"0.0.0.0:{_get_port()}"
workers = 1
threads = 4
timeout = 120
