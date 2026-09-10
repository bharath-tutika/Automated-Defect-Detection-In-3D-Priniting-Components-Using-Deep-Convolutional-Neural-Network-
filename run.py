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


def main():
    check_system_readiness()
    app = create_app()
    app_logger.info(f"Starting server on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
