"""
Detection package initialization.
"""

from backend.detection.detector import YOLODetector
from backend.detection.image_detector import process_image_inspection
from backend.detection.video_detector import process_video_inspection
from backend.detection.camera_detector import CameraManager

__all__ = [
    "YOLODetector",
    "process_image_inspection",
    "process_video_inspection",
    "CameraManager",
]
