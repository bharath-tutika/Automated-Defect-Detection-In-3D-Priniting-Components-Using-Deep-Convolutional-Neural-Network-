"""
Dashboard, Analytics, Model Performance, and System Health API Routes.
"""

from pathlib import Path
from flask import Blueprint, jsonify

from config import (
    MODEL_PATH,
    DEFECT_CLASSES,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    IMAGE_SIZE,
    METRICS_FILE,
    CONFUSION_MATRIX_FILE,
    TRAINING_RESULTS_PLOT,
)
from backend.database.database import get_db_session
from backend.database.crud import get_dashboard_stats, get_dashboard_charts
from backend.detection.detector import YOLODetector
from backend.detection.camera_detector import CameraManager
from backend.utils.response import api_success, api_error
from backend.utils.logger import app_logger

dashboard_bp = Blueprint("dashboard_bp", __name__, url_prefix="/api")


@dashboard_bp.route("/health", methods=["GET"])
def health_check():
    """
    System status and component availability check.
    """
    detector = YOLODetector.get_instance()
    cam_manager = CameraManager.get_instance()

    # Test database connectivity
    db_ok = False
    try:
        with get_db_session() as session:
            db_ok = True
    except Exception:
        db_ok = False

    return api_success(
        data={
            "status": "healthy" if (detector.model_loaded and db_ok) else ("degraded" if db_ok else "unhealthy"),
            "model_available": detector.model_loaded,
            "model_loaded": detector.model_loaded,
            "model_path": str(detector.model_path),
            "model_error": detector.load_error,
            "database_available": db_ok,
            "camera_running": cam_manager.is_running,
        },
        message="System health check completed.",
    )


@dashboard_bp.route("/dashboard/stats", methods=["GET"])
def get_stats():
    """
    Retrieve aggregate inspection statistics for KPI summary cards.
    """
    try:
        with get_db_session() as session:
            stats = get_dashboard_stats(session)
        return api_success(data=stats, message="Dashboard stats retrieved.")
    except Exception as e:
        app_logger.error(f"Error getting dashboard stats: {e}")
        return api_error(f"Failed to load stats: {str(e)}", status_code=500)


@dashboard_bp.route("/dashboard/charts", methods=["GET"])
def get_charts():
    """
    Retrieve dataset distributions for Chart.js dashboard charts.
    """
    try:
        with get_db_session() as session:
            charts = get_dashboard_charts(session)
        return api_success(data=charts, message="Dashboard charts retrieved.")
    except Exception as e:
        app_logger.error(f"Error getting dashboard charts: {e}")
        return api_error(f"Failed to load charts: {str(e)}", status_code=500)


@dashboard_bp.route("/model/info", methods=["GET"])
def get_model_info():
    """
    Retrieve configuration, class list, and loaded model metadata.
    """
    detector = YOLODetector.get_instance()
    classes_list = [
        {"id": k, "name": v["name"], "label": v["label"], "is_defect": v["is_defect"]}
        for k, v in DEFECT_CLASSES.items()
    ]

    return api_success(
        data={
            "model_available": detector.model_loaded,
            "model_loaded": detector.model_loaded,
            "model_path": str(detector.model_path),
            "model_file_exists": detector.model_path.exists(),
            "model_names": detector.model_classes if detector.model_loaded else {},
            "load_error": detector.load_error,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "iou_threshold": IOU_THRESHOLD,
            "image_size": IMAGE_SIZE,
            "classes_count": len(detector.model_classes) if detector.model_loaded else len(DEFECT_CLASSES),
            "classes": classes_list,
        },
        message="Model information retrieved.",
    )


@dashboard_bp.route("/model/metrics", methods=["GET"])
def get_model_metrics():
    """
    Retrieve genuine training & validation metrics if available on disk.
    Strictly returns metrics_available=False if no training was performed.
    """
    has_metrics_file = METRICS_FILE.exists()
    has_cm = CONFUSION_MATRIX_FILE.exists()
    has_plot = TRAINING_RESULTS_PLOT.exists()

    if not has_metrics_file:
        return api_success(
            data={
                "metrics_available": False,
                "message": "Training metrics are not available yet. Train and evaluate the model first.",
                "metrics": None,
                "confusion_matrix_url": None,
                "training_plot_url": None,
            },
            message="No training metrics generated yet.",
        )

    # Read existing metrics safely
    try:
        metrics_content = METRICS_FILE.read_text(encoding="utf-8")
        parsed_metrics = {}
        for line in metrics_content.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                parsed_metrics[k.strip()] = v.strip()

        return api_success(
            data={
                "metrics_available": True,
                "metrics": parsed_metrics,
                "raw_text": metrics_content,
                "confusion_matrix_url": "/training/results/confusion_matrix.png" if has_cm else None,
                "training_plot_url": "/training/results/training_results.png" if has_plot else None,
            },
            message="Training metrics retrieved.",
        )
    except Exception as e:
        app_logger.error(f"Error reading metrics file: {e}")
        return api_error(f"Failed to read metrics file: {str(e)}", status_code=500)
