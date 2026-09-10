"""
Image preprocessing and safe I/O utilities for computer vision pipeline.
"""

from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from config import IMAGE_SIZE
from backend.utils.logger import app_logger


def safe_read_image(image_path: Path) -> Optional[np.ndarray]:
    """
    Safely load an image from disk supporting Windows Unicode/non-ASCII paths.
    Returns BGR numpy array or None on failure.
    """
    try:
        if not image_path.exists():
            app_logger.warning(f"File not found: {image_path}")
            return None

        # Read as binary bytes then decode with OpenCV to handle Windows path quirks
        with open(image_path, "rb") as f:
            file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            app_logger.warning(f"Failed to decode image: {image_path}")
            return None
        return img
    except Exception as e:
        app_logger.error(f"Error reading image {image_path}: {e}")
        return None


def safe_write_image(image_path: Path, img: np.ndarray) -> bool:
    """
    Safely write an image to disk supporting Windows Unicode/non-ASCII paths.
    """
    try:
        image_path.parent.mkdir(parents=True, exist_ok=True)
        ext = image_path.suffix.lower() or ".jpg"
        success, encoded_img = cv2.imencode(ext, img)
        if not success:
            app_logger.error(f"Failed to encode image for {image_path}")
            return False
        with open(image_path, "wb") as f:
            f.write(encoded_img.tobytes())
        return True
    except Exception as e:
        app_logger.error(f"Error writing image {image_path}: {e}")
        return False


def preprocess_image_for_display(img: np.ndarray, max_dimension: int = 1280) -> np.ndarray:
    """
    Resize large images proportionally for optimal web display and storage.
    """
    h, w = img.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img
