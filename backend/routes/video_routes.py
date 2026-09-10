"""
Video Inspection API Routes.
Provides endpoint for uploading and analyzing 3D print videos.
"""

from pathlib import Path
from flask import Blueprint, request, jsonify

from config import UPLOAD_VIDEOS_DIR, ALLOWED_VIDEO_EXTENSIONS, MAX_UPLOAD_SIZE
from backend.utils.file_handler import (
    is_allowed_video,
    generate_unique_filename,
)
from backend.detection.video_detector import process_video_inspection
from backend.utils.response import api_success, api_error
from backend.utils.logger import app_logger

video_bp = Blueprint("video_bp", __name__, url_prefix="/api/video")


@video_bp.route("/predict", methods=["POST"])
def predict_video():
    """
    Analyze an uploaded 3D print video frame-by-frame for defects.
    Form field: 'file'
    Optional fields: 'frame_skip', 'conf_threshold', 'iou_threshold'
    """
    if "file" not in request.files:
        return api_error("No video file provided in the request.", status_code=400)

    file = request.files["file"]
    if not file or file.filename == "":
        return api_error("No video selected for upload.", status_code=400)

    if not is_allowed_video(file.filename):
        allowed_str = ", ".join(ALLOWED_VIDEO_EXTENSIONS)
        return api_error(
            f"Unsupported video format '{file.filename}'. Allowed formats: {allowed_str}",
            status_code=415,
        )

    try:
        unique_name = generate_unique_filename(file.filename, prefix="upload_vid")
        saved_path = UPLOAD_VIDEOS_DIR / unique_name
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        file.save(str(saved_path))

        # Check size
        file_size = saved_path.stat().st_size
        if file_size == 0:
            saved_path.unlink()
            return api_error("Video file is empty (0 bytes).", status_code=400)

        # Parse parameters
        frame_skip = request.form.get("frame_skip", type=int)
        conf_thresh = request.form.get("conf_threshold", type=float)
        iou_thresh = request.form.get("iou_threshold", type=float)

        app_logger.info(f"Processing uploaded video: {unique_name} (Size: {file_size // 1024} KB)")

        # Process video
        result = process_video_inspection(
            video_path=saved_path,
            original_filename=unique_name,
            frame_skip=frame_skip,
            conf_threshold=conf_thresh,
            iou_threshold=iou_thresh,
        )

        if not result.get("model_available", True):
            return api_error(
                message=result.get("error", "Trained model not found. Add models/trained/best.pt to enable AI detection."),
                status_code=503,
                model_available=False,
                data=result,
            )

        if not result.get("success", False):
            return api_error(result.get("error", "Video processing failed"), status_code=500)

        return api_success(
            data=result,
            message=f"Video inspection completed. Status: {result['status']}",
            status_code=200,
        )

    except Exception as e:
        app_logger.error(f"Unexpected error in video predict route: {e}", exc_info=True)
        return api_error(f"Internal server error: {str(e)}", status_code=500)
