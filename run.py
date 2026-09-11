"""
Entry point for the AI-Based Real-Time 3D Printing Defect Detection Application.

Usage:
    python run.py
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
    MODEL_PATH,
    DATABASE_PATH,
    UPLOAD_IMAGES_DIR,
    UPLOAD_VIDEOS_DIR,
    UPLOAD_TEMP_DIR,
    RESULT_IMAGES_DIR,
    RESULT_VIDEOS_DIR,
    RESULT_LIVE_FRAMES_DIR,
    RESULT_REPORTS_DIR,
    LOGS_DIR,
)
from backend.app import create_app
from backend.utils.logger import app_logger


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


def check_system_readiness():
    """Check AI model weights, database status, and print startup banner."""
    ensure_directories()

    from backend.detection.detector import YOLODetector
    detector = YOLODetector.get_instance()

    print("\n" + "=" * 70)
    print("  AI-BASED REAL-TIME 3D PRINTING DEFECT DETECTION SYSTEM")
    print("  Ultralytics YOLO + Flask + OpenCV + SQLite Engine")
    print("=" * 70)
    print(f"  MODEL PATH:    {detector.model_path}")
    print(f"  MODEL EXISTS:  {detector.model_path.exists()}")
    print(f"  MODEL LOADED:  {detector.model_loaded}")
    if detector.model_loaded:
        print(f"  MODEL CLASSES: {detector.model_classes}")
    else:
        print(f"  LOAD ERROR:    {detector.load_error}")
    print(f"  DATABASE:      {DATABASE_PATH}")
    print(f"  SERVER URL:    http://{HOST}:{PORT}")
    print("=" * 70 + "\n")


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


def get_bound_port(preferred: int = 8080, host: str = "0.0.0.0") -> int:
    """Return preferred port if available, or dynamically find the next open port."""
    if is_port_available(preferred, host):
        return preferred
    
    # In cloud environments with explicit PORT variable, stick to preferred
    if "PORT" in os.environ and os.environ["PORT"].strip() != "":
        return preferred

    candidates = [8080, 5000, 8000, 8888, 5001, 8081, 8082, 3000]
    for p in candidates:
        if p != preferred and is_port_available(p, host):
            print(f"[PORT NOTICE] Port {preferred} was in use; automatically selected available port {p}.")
            return p
            
    return preferred


def main():
    check_system_readiness()
    app = create_app()
    active_port = get_bound_port(PORT, HOST)
    app_logger.info(f"Starting server on http://{HOST}:{active_port}")
    app.run(host=HOST, port=active_port, debug=DEBUG)


if __name__ == "__main__":
    main()

