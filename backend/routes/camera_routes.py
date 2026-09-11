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


@camera_bp.route("/process_frame", methods=["POST"])
def process_camera_frame():
    """
    Process a single video frame sent directly from the client web browser (Webcam getUserMedia).
    Works seamlessly in cloud deployments without server hardware webcams.
    """
    import base64
    import numpy as np
    import cv2
    from backend.detection.detector import YOLODetector
    from backend.preprocessing.image_preprocessing import safe_write_image
    from backend.database.database import get_db_session
    from backend.database.crud import create_inspection_record
    from backend.utils.file_handler import generate_unique_filename
    from config import RESULT_LIVE_FRAMES_DIR, CONFIDENCE_THRESHOLD

    try:
        data = request.get_json(silent=True) or {}
        image_data = data.get("image")
        if not image_data:
            return api_error("No image frame provided", status_code=400)

        # Strip data URL prefix if present
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]

        # Decode base64 to image
        img_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return api_error("Failed to decode camera frame", status_code=400)

        # Run AI defect detection
        detector = YOLODetector.get_instance()
        inference = detector.predict(frame)

        # Render bounding boxes and annotations
        status = inference.get("status", "GOOD")
        detections = inference.get("detections", [])
        fps = float(data.get("fps", 0.0))
        annotated_frame = detector.draw_annotations(frame, detections, status=status, fps=fps)

        # Encode annotated image back to base64 for real-time display
        _, buffer = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")

        # Handle save snapshot request if requested
        save_snapshot = data.get("save_snapshot", False)
        saved_record = None

        if save_snapshot:
            timestamp_str = cv2.getTickCount()
            filename = generate_unique_filename(f"webcam_snapshot_{timestamp_str}.jpg")
            save_path = RESULT_LIVE_FRAMES_DIR / filename
            safe_write_image(save_path, annotated_frame)

            with get_db_session() as session:
                rec = create_inspection_record(
                    session=session,
                    inspection_type="live",
                    status=status,
                    original_filename=filename,
                    result_filename=filename,
                    defect_type=inference.get("dominant_defect", "Normal / Good Print"),
                    confidence=inference.get("max_confidence", 0.0),
                    processing_time=inference.get("processing_time_ms", 0.0),
                    source="Browser Web Camera",
                    notes=f"Browser webcam inspection snapshot. Detections count: {len(detections)}",
                    detections=detections,
                )
                saved_record = {
                    "inspection_id": rec.id,
                    "filename": filename,
                    "image_url": f"/results/live_frames/{filename}",
                    "status": status,
                    "defect_type": inference.get("dominant_defect", "Normal / Good Print"),
                    "confidence": inference.get("max_confidence", 0.0),
                }

        return api_success(
            data={
                "status": status,
                "dominant_defect": inference.get("dominant_defect", "Normal / Good Print"),
                "confidence": inference.get("max_confidence", 0.0),
                "confidence_percentage": inference.get("confidence_percentage", 0.0),
                "detection_count": len(detections),
                "detections": detections,
                "processing_time_ms": inference.get("processing_time_ms", 0.0),
                "annotated_image": annotated_b64,
                "saved_snapshot": saved_record,
                "model_available": inference.get("model_available", True),
            },
            message="Frame processed successfully.",
        )
    except Exception as e:
        app_logger.error(f"Error processing camera frame: {e}", exc_info=True)
        return api_error(f"Frame processing error: {str(e)}", status_code=500)

