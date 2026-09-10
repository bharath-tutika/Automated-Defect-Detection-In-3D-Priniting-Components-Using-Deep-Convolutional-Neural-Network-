"""
Video and camera frame preprocessing utilities.
"""

import cv2
import numpy as np
from typing import Tuple


def resize_frame(frame: np.ndarray, target_width: int = 640) -> np.ndarray:
    """
    Proportionally resize a video or camera frame to target width.
    """
    h, w = frame.shape[:2]
    if w <= target_width:
        return frame
    ratio = target_width / float(w)
    target_height = int(h * ratio)
    return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)


def format_duration(seconds: float) -> str:
    """Format duration in seconds into mm:ss or hh:mm:ss."""
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"
