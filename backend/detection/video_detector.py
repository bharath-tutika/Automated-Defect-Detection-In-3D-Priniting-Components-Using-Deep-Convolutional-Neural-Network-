"""
Video Inspection Pipeline.
Processes uploaded video frame-by-frame using OpenCV and YOLO without loading the entire video into RAM.
Generates an annotated output video and aggregates defect analytics.
"""

import time
from pathlib import Path
from typing import Any, Dict, Optional
import cv2
import numpy as np

from config import (
    FRAME_SKIP,
    RESULT_VIDEOS_DIR,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
)
from backend.detection.detector import YOLODetector
from backend.database.database import get_db_session
from backend.database.crud import create_inspection_record
from backend.utils.file_handler import generate_unique_filename
from backend.utils.logger import app_logger


def process_video_inspection(
    video_path: Path,
    original_filename: str,
    frame_skip: Optional[int] = None,
    conf_threshold: Optional[float] = None,
    iou_threshold: Optional[float] = None,
    progress_callback: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Process video stream frame-by-frame, write annotated video, and aggregate metrics.
    """
    start_time = time.perf_counter()
    detector = YOLODetector.get_instance()
    if not detector.model_loaded:
        detector.reload()

    if not detector.model_loaded:
        return {
            "success": False,
            "model_available": False,
            "error": detector.load_error or "Trained YOLO model not found. Please place best.pt in models/trained/best.pt.",
            "status": "MODEL_NOT_FOUND",
            "message": "Trained YOLO model not found. Please place best.pt in models/trained/best.pt.",
        }

    if not video_path.exists():
        return {"success": False, "error": f"Video file not found at {video_path}", "status": "ERROR"}

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"success": False, "error": "Could not open video file. Invalid or unsupported video codec.", "status": "ERROR"}

    # Video properties
    skip = frame_skip if frame_skip is not None and frame_skip >= 1 else FRAME_SKIP
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Output setup
    result_filename = generate_unique_filename(original_filename, prefix="annotated")
    # Ensure MP4 extension for browser playback
    if not result_filename.lower().endswith(".mp4"):
        result_filename = result_filename.rsplit(".", 1)[0] + ".mp4"
    result_file_path = RESULT_VIDEOS_DIR / result_filename
    result_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Use mp4v or avc1 fourcc for video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(result_file_path), fourcc, fps, (width, height))

    frame_idx = 0
    defect_frames_count = 0
    defect_class_tally: Dict[str, int] = {}
    all_detections_summary: Dict[str, float] = {}  # class -> max confidence
    latest_detections: list = []
    latest_status = "GOOD"

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Run inference periodically or use previous frame's bounding boxes
            if frame_idx % skip == 0:
                inference = detector.predict(
                    frame,
                    conf_threshold=conf_threshold,
                    iou_threshold=iou_threshold,
                )
                latest_status = inference.get("status", "GOOD")
                latest_detections = inference.get("detections", [])

                if latest_status == "DEFECT":
                    defect_frames_count += 1
                    for det in latest_detections:
                        if det.get("is_defect", True):
                            cname = det.get("class_name", "Defect")
                            conf = det.get("confidence", 0.0)
                            defect_class_tally[cname] = defect_class_tally.get(cname, 0) + 1
                            all_detections_summary[cname] = max(all_detections_summary.get(cname, 0.0), conf)

            # Draw annotations on output frame
            annotated_frame = detector.draw_annotations(
                frame,
                latest_detections,
                status=latest_status,
                fps=fps,
            )
            out.write(annotated_frame)
            frame_idx += 1

            # Progress tracking hook
            if progress_callback and total_frames > 0 and frame_idx % 10 == 0:
                progress_callback(int((frame_idx / total_frames) * 100))

    finally:
        cap.release()
        out.release()

    elapsed_sec = round(time.perf_counter() - start_time, 2)
    overall_status = "DEFECT" if defect_frames_count > 0 else "GOOD"
    dominant_defect = (
        max(defect_class_tally.items(), key=lambda x: x[1])[0]
        if defect_class_tally
        else "No Defect Detected"
    )
    max_confidence = (
        max(all_detections_summary.values())
        if all_detections_summary
        else 0.0
    )

    # Save to Database
    inspection_id = None
    try:
        with get_db_session() as session:
            record = create_inspection_record(
                session=session,
                inspection_type="video",
                status=overall_status,
                original_filename=original_filename,
                result_filename=result_filename,
                defect_type=dominant_defect,
                confidence=max_confidence,
                processing_time=elapsed_sec,
                source="Video Upload",
                notes=f"Total frames: {frame_idx}, Defective frames: {defect_frames_count}",
            )
            inspection_id = record.id
    except Exception as db_err:
        app_logger.error(f"Failed to record video inspection in database: {db_err}")

    return {
        "success": True,
        "inspection_id": inspection_id,
        "model_available": True,
        "status": overall_status,
        "dominant_defect": dominant_defect,
        "defect_summary": defect_class_tally,
        "max_confidence": round(max_confidence, 4),
        "total_frames": frame_idx,
        "defect_frames": defect_frames_count,
        "fps": round(fps, 1),
        "original_filename": original_filename,
        "result_filename": result_filename,
        "original_video_url": f"/uploads/videos/{original_filename}",
        "result_video_url": f"/results/videos/{result_filename}",
        "processing_time_seconds": elapsed_sec,
    }
