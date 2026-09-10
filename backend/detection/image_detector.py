"""
Single Image Inspection Pipeline.
Loads uploaded image, runs YOLO inference, annotates defects, saves result, and records in database.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import cv2

from config import RESULT_IMAGES_DIR
from backend.detection.detector import YOLODetector
from backend.preprocessing.image_preprocessing import safe_read_image, safe_write_image
from backend.database.database import get_db_session
from backend.database.crud import create_inspection_record
from backend.utils.file_handler import generate_unique_filename
from backend.utils.logger import app_logger


def process_image_inspection(
    image_path: Path,
    original_filename: str,
    conf_threshold: Optional[float] = None,
    iou_threshold: Optional[float] = None,
    source: str = "Image Upload",
) -> Dict[str, Any]:
    """
    Execute full inspection workflow on a single image file.
    """
    # 1. Load image safely
    img = safe_read_image(image_path)
    if img is None:
        return {
            "success": False,
            "error": "Failed to decode image file. Please provide a valid JPG, PNG, or WEBP image.",
            "status": "ERROR",
        }

    # 2. Run AI Detector
    detector = YOLODetector.get_instance()
    inference_result = detector.predict(img, conf_threshold=conf_threshold, iou_threshold=iou_threshold)

    # 3. Handle model unavailability gracefully
    if not inference_result.get("model_available", False):
        return {
            "success": False,
            "model_available": False,
            "error": inference_result.get("message") or inference_result.get("error", "Trained YOLO model not found. Please place best.pt in models/trained/best.pt."),
            "status": "MODEL_NOT_FOUND",
            "message": "Trained YOLO model not found. Please place best.pt in models/trained/best.pt.",
            "detections": [],
            "processing_time_ms": inference_result.get("processing_time_ms", 0),
        }

    # 4. Generate annotated visualization
    status = inference_result.get("status", "GOOD")
    detections = inference_result.get("detections", [])
    annotated_img = detector.draw_annotations(img, detections, status=status)

    # 5. Save annotated result image
    result_filename = generate_unique_filename(original_filename, prefix="annotated")
    result_file_path = RESULT_IMAGES_DIR / result_filename
    saved = safe_write_image(result_file_path, annotated_img)

    if not saved:
        app_logger.error(f"Failed to save annotated image to {result_file_path}")
        result_filename = original_filename  # fallback

    # 6. Record in Database
    dominant_defect = inference_result.get("dominant_defect", "No Defect Detected")
    max_confidence = inference_result.get("max_confidence", 0.0)
    processing_time = inference_result.get("processing_time_ms", 0.0)
    conf_pct = inference_result.get("confidence_percentage", round(max_confidence * 100, 2) if max_confidence > 0 else 0.0)

    inspection_id = None
    try:
        with get_db_session() as session:
            record = create_inspection_record(
                session=session,
                inspection_type="image",
                status=status,
                original_filename=original_filename,
                result_filename=result_filename,
                defect_type=dominant_defect,
                confidence=max_confidence,
                processing_time=processing_time,
                source=source,
                notes=f"YOLO detections count: {len(detections)}",
                detections=detections,
            )
            inspection_id = record.id
    except Exception as db_err:
        app_logger.error(f"Failed to save inspection record to database: {db_err}")

    return {
        "success": True,
        "inspection_id": inspection_id,
        "model_available": True,
        "status": status,
        "dominant_defect": dominant_defect,
        "confidence": max_confidence,
        "confidence_percentage": conf_pct,
        "detections": detections,
        "defect_count": inference_result.get("defect_count", 0),
        "total_detections": len(detections),
        "original_filename": original_filename,
        "result_filename": result_filename,
        "original_image_url": f"/uploads/images/{original_filename}",
        "result_image_url": f"/results/images/{result_filename}",
        "processing_time_ms": processing_time,
    }
