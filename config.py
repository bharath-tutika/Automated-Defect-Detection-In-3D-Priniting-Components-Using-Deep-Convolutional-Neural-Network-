"""
Central Configuration Module for 3D Printing Defect Detection System.

All application parameters, class mappings, thresholds, and file paths are
defined centrally here to avoid duplication across backend, detection,
and frontend modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables if .env exists
load_dotenv()

# Base Project Directory
BASE_DIR = Path(__file__).resolve().parent

def _parse_port(default: int = 8080) -> int:
    """Safely parse PORT from environment variable, handling strings like '$PORT'."""
    raw = os.getenv("PORT", os.getenv("FLASK_PORT", str(default)))
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default

# Server Settings
HOST = os.getenv("FLASK_HOST", os.getenv("HOST", "0.0.0.0"))
PORT = _parse_port(8080)
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
SECRET_KEY = os.getenv("SECRET_KEY", "3d-printing-defect-detection-secret-key-2026")

# AI Model Configuration
MODEL_PATH = Path(os.getenv("MODEL_PATH", BASE_DIR / "models" / "trained" / "best.pt"))
PRETRAINED_MODEL_PATH = Path(os.getenv("PRETRAINED_MODEL_PATH", BASE_DIR / "models" / "pretrained" / "yolo_base.pt"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.50))
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", 0.45))
IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", 640))

# Defect Classes Mapping (Central Single Source of Truth)
# id -> { name (YOLO identifier), label (Human-readable UI display), is_defect }
DEFECT_CLASSES = {
    0: {"name": "normal", "label": "Normal / Good Print", "is_defect": False},
    1: {"name": "stringing", "label": "Stringing", "is_defect": True},
    2: {"name": "warping", "label": "Warping", "is_defect": True},
    3: {"name": "layer_shift", "label": "Layer Shift", "is_defect": True},
    4: {"name": "under_extrusion", "label": "Under-Extrusion", "is_defect": True},
    5: {"name": "over_extrusion", "label": "Over-Extrusion", "is_defect": True},
    6: {"name": "spaghetti", "label": "Spaghetti Failure", "is_defect": True},
}

CLASS_NAME_TO_ID = {v["name"]: k for k, v in DEFECT_CLASSES.items()}
CLASS_ID_TO_LABEL = {k: v["label"] for k, v in DEFECT_CLASSES.items()}
CLASS_NAME_TO_LABEL = {v["name"]: v["label"] for k, v in DEFECT_CLASSES.items()}

# Camera Configuration
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
FRAME_SKIP = int(os.getenv("FRAME_SKIP", 3))
CAMERA_DEBOUNCE_SECONDS = float(os.getenv("CAMERA_DEBOUNCE_SECONDS", 3.0))

# Upload & File Storage Paths
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_IMAGES_DIR = UPLOAD_FOLDER / "images"
UPLOAD_VIDEOS_DIR = UPLOAD_FOLDER / "videos"
UPLOAD_TEMP_DIR = UPLOAD_FOLDER / "temporary"

RESULT_FOLDER = BASE_DIR / "results"
RESULT_IMAGES_DIR = RESULT_FOLDER / "images"
RESULT_VIDEOS_DIR = RESULT_FOLDER / "videos"
RESULT_LIVE_FRAMES_DIR = RESULT_FOLDER / "live_frames"
RESULT_REPORTS_DIR = RESULT_FOLDER / "reports"

# File Limits and Extensions
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "webm"}

# Database Configuration
DATABASE_PATH = BASE_DIR / "database" / "defect_detection.db"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH.as_posix()}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Logging Configuration
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "application.log"

# Training Output Paths
TRAINING_DIR = BASE_DIR / "training"
TRAINING_RESULTS_DIR = TRAINING_DIR / "results"
METRICS_FILE = TRAINING_RESULTS_DIR / "metrics.txt"
CONFUSION_MATRIX_FILE = TRAINING_RESULTS_DIR / "confusion_matrix.png"
TRAINING_RESULTS_PLOT = TRAINING_RESULTS_DIR / "training_results.png"
