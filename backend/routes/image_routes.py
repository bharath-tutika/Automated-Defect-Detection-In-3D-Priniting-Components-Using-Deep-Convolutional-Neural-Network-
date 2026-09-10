"""
Image Inspection API Routes.
Provides endpoint for uploading and analyzing 3D print images.
"""

from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from config import UPLOAD_IMAGES_DIR, ALLOWED_IMAGE_EXTENSIONS
from backend.utils.file_handler import (
    is_allowed_image,
    generate_unique_filename,
    validate_image,
)
from backend.detection.image_detector import process_image_inspection
from backend.utils.response import api_success, api_error
from backend.utils.logger import app_logger

image_bp = Blueprint("image_bp", __name__, url_prefix="/api/image")


@image_bp.route("/predict", methods=["POST"])
def predict_image():
    """
    Analyze an uploaded 3D print image for defects.
    Form field: 'file'
    Optional fields: 'conf_threshold', 'iou_threshold'
    """
    if "file" not in request.files:
        return api_error("No file provided in the request.", status_code=400)

    file = request.files["file"]
    if not file or file.filename == "":
        return api_error("No file selected for upload.", status_code=400)

    if not is_allowed_image(file.filename):
        allowed_str = ", ".join(ALLOWED_IMAGE_EXTENSIONS)
        return api_error(
            f"Unsupported file format '{file.filename}'. Allowed formats: {allowed_str}",
            status_code=415,
        )

    try:
        # Save uploaded image safely
        unique_name = generate_unique_filename(file.filename, prefix="upload")
        saved_path = UPLOAD_IMAGES_DIR / unique_name
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        file.save(str(saved_path))

        # Validate file integrity
        is_valid, val_msg = validate_image(saved_path)
        if not is_valid:
            if saved_path.exists():
                saved_path.unlink()
            return api_error(f"Image validation failed: {val_msg}", status_code=400)

        # Parse optional thresholds
        conf_thresh = request.form.get("conf_threshold", type=float)
        iou_thresh = request.form.get("iou_threshold", type=float)

        # Process inspection
        result = process_image_inspection(
            image_path=saved_path,
            original_filename=unique_name,
            conf_threshold=conf_thresh,
            iou_threshold=iou_thresh,
            source="Web Image Upload",
        )

        if not result.get("model_available", True):
            return api_error(
                message=result.get("error", "Trained model not found. Add models/trained/best.pt to enable AI detection."),
                status_code=503,
                model_available=False,
                data=result,
            )

        if not result.get("success", False):
            return api_error(result.get("error", "Inference error occurred"), status_code=500)

        return api_success(
            data=result,
            message=f"Image inspection complete. Status: {result['status']}",
            status_code=200,
        )

    except Exception as e:
        app_logger.error(f"Unexpected error in image predict route: {e}", exc_info=True)
        return api_error(f"Internal server error: {str(e)}", status_code=500)
