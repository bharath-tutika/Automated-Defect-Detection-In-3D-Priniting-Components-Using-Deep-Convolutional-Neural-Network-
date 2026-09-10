"""
Root application entry point for Railway, Railpack, Nixpacks, and WSGI servers.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import HOST, PORT, DEBUG
from backend.app import create_app
from run import ensure_directories, check_system_readiness

ensure_directories()
app = create_app()

if __name__ == "__main__":
    check_system_readiness()
    app.run(host=HOST, port=PORT, debug=DEBUG)
