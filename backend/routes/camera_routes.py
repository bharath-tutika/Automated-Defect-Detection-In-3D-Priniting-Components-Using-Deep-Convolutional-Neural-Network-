"""
Live Camera Inspection API Routes.
Provides MJPEG streaming, status checks, start/stop hardware controls, and snapshot saving.
"""

from flask import Blueprint, Response, request, jsonify

from config import CAMERA_INDEX
from backend.detection.camera_detector import CameraManager
from backend.utils.response import api_success, api_error
from backend.utils.logger import app_logger

camera_bp = Blueprint("camera_bp", __name__, url_prefix="/api/camera")


@camera_bp.route("/devices", methods=["GET"])
def list_camera_devices():
    """
    List all detected video input devices on the system.
    """
    try:
        devices = CameraManager.list_available_cameras()
        current_idx = CameraManager.get_instance().camera_index
        return api_success(
            data={"devices": devices, "current_index": current_idx},
            message="Camera devices enumerated successfully.",
        )
    except Exception as e:
        app_logger.error(f"Error scanning camera devices: {e}")
        return api_error(f"Failed to scan camera devices: {str(e)}", status_code=500)


@camera_bp.route("/status", methods=["GET"])
def get_camera_status():
    """
    Query real-time camera state, streaming status, FPS, and latest detections.
    """
    try:
        manager = CameraManager.get_instance()
        status_data = manager.get_status()
        return api_success(data=status_data, message="Camera status retrieved.")
    except Exception as e:
        app_logger.error(f"Error fetching camera status: {e}")
        return api_error(f"Failed to get camera status: {str(e)}", status_code=500)


@camera_bp.route("/start", methods=["POST"])
def start_camera():
    """
    Start webcam feed and background inference loop.
    Optional JSON/form parameter: 'camera_index'
    """
    try:
        cam_idx = None
        if request.is_json and request.json and "camera_index" in request.json:
            try:
                cam_idx = int(request.json["camera_index"])
            except (ValueError, TypeError):
                cam_idx = None
        elif request.form and "camera_index" in request.form:
            try:
                cam_idx = int(request.form["camera_index"])
            except (ValueError, TypeError):
                cam_idx = None

        if cam_idx is None:
            cam_idx = CAMERA_INDEX

        manager = CameraManager.get_instance(cam_idx)
        success, message = manager.start(camera_index=cam_idx)

        if not success:
            return api_error(message=message, status_code=503)

        return api_success(data=manager.get_status(), message=message)
    except Exception as e:
        app_logger.error(f"Error starting camera: {e}", exc_info=True)
        return api_error(
            "Camera could not be accessed. Please ensure Windows desktop app camera permissions are enabled and the camera is plugged in.",
            status_code=500,
        )


@camera_bp.route("/stop", methods=["POST"])
def stop_camera():
    """
    Stop webcam feed and release capture device.
    """
    try:
        manager = CameraManager.get_instance()
        success, message = manager.stop()
        return api_success(data=manager.get_status(), message=message)
    except Exception as e:
        app_logger.error(f"Error stopping camera: {e}")
        return api_error(f"Failed to stop camera: {str(e)}", status_code=500)


@camera_bp.route("/stream", methods=["GET"])
def stream_camera():
    """
    MJPEG live video stream endpoint.
    Accepts optional ?camera_index=<int> query param.
    """
    try:
        req_cam_idx = request.args.get("camera_index", None, type=int)
        manager = CameraManager.get_instance()

        if req_cam_idx is not None and manager.is_running and manager.camera_index != req_cam_idx:
            # Switch to requested camera device
            manager.start(camera_index=req_cam_idx)
        elif not manager.is_running:
            # Auto-start with requested or default index
            success, _ = manager.start(camera_index=req_cam_idx)
            if not success:
                return Response(
                    "Camera not available.",
                    status=503,
                    mimetype="text/plain",
                )

        return Response(
            manager.generate_mjpeg_stream(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
        )
    except Exception as e:
        app_logger.error(f"Streaming error: {e}")
        return Response(f"Streaming error: {e}", status=500, mimetype="text/plain")


@camera_bp.route("/snapshot", methods=["POST"])
def capture_snapshot():
    """
    Manually save the current camera frame as an inspection record.
    """
    try:
        manager = CameraManager.get_instance()
        if not manager.is_running:
            return api_error("Cannot capture snapshot: camera is not running.", status_code=400)

        result = manager.save_manual_snapshot()
        if not result.get("success", False):
            return api_error(result.get("error", "Snapshot failed"), status_code=500)

        return api_success(data=result, message="Defect frame captured and saved.")
    except Exception as e:
        app_logger.error(f"Snapshot error: {e}")
        return api_error(f"Failed to capture frame: {str(e)}", status_code=500)
