"""
File management utilities: secure saving, unique names, validation, and sanitization.
"""

import os
import uuid
import time
from pathlib import Path
from typing import Optional, Set
from werkzeug.utils import secure_filename
from PIL import Image

from config import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    MAX_UPLOAD_SIZE,
    UPLOAD_TEMP_DIR,
)
from backend.utils.logger import app_logger


def get_file_extension(filename: str) -> str:
    """Return the lowercase extension without leading dot."""
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""


def is_allowed_image(filename: str) -> bool:
    """Check if file extension is an allowed image format."""
    ext = get_file_extension(filename)
    return ext in ALLOWED_IMAGE_EXTENSIONS


def is_allowed_video(filename: str) -> bool:
    """Check if file extension is an allowed video format."""
    ext = get_file_extension(filename)
    return ext in ALLOWED_VIDEO_EXTENSIONS


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate a sanitized, collision-free filename preserving extension.
    Example: img_20260816_123456_a1b2c3d4_part.png
    """
    ext = get_file_extension(original_filename)
    safe_base = secure_filename(original_filename.rsplit(".", 1)[0]) if "." in original_filename else "file"
    if not safe_base:
        safe_base = "upload"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    unique_token = uuid.uuid4().hex[:8]
    prefix_str = f"{prefix}_" if prefix else ""
    return f"{prefix_str}{timestamp}_{unique_token}_{safe_base}.{ext}" if ext else f"{prefix_str}{timestamp}_{unique_token}_{safe_base}"


def validate_image(file_path: Path) -> tuple[bool, str]:
    """
    Verify that an uploaded image file is valid, non-empty, and uncorrupted.
    """
    try:
        if not file_path.exists():
            return False, "File does not exist on disk."
        
        file_size = file_path.stat().st_size
        if file_size == 0:
            return False, "Image file is empty (0 bytes)."
        
        if file_size > MAX_UPLOAD_SIZE:
            return False, f"File exceeds maximum upload size limit of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB."

        # Verify image integrity using Pillow
        with Image.open(file_path) as img:
            img.verify()
        
        # Test loading the image data after verify
        with Image.open(file_path) as img:
            img.load()
            if img.width < 10 or img.height < 10:
                return False, f"Image dimensions too small ({img.width}x{img.height})."

        return True, "Valid image"
    except Exception as e:
        app_logger.warning(f"Image validation failed for {file_path}: {e}")
        return False, f"Corrupted or unsupported image: {str(e)}"


def cleanup_temp_files(directory: Path = UPLOAD_TEMP_DIR, max_age_seconds: int = 3600) -> int:
    """
    Remove temporary files older than max_age_seconds.
    """
    deleted_count = 0
    try:
        if not directory.exists():
            return 0
        now = time.time()
        for item in directory.iterdir():
            if item.is_file() and item.name != ".gitkeep":
                file_age = now - item.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        item.unlink()
                        deleted_count += 1
                    except Exception as err:
                        app_logger.debug(f"Failed to delete temp file {item}: {err}")
    except Exception as e:
        app_logger.error(f"Error during temp file cleanup in {directory}: {e}")
    return deleted_count
