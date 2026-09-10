"""
Live Camera Inspection Pipeline with MJPEG Streaming.
Handles webcam capture, real-time YOLO inference, FPS tracking,
debounce defect logging, and automatic defect snapshot saving.
"""

import time
import threading
import subprocess
import json
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
import cv2
import numpy as np

from config import (
    CAMERA_INDEX,
    FRAME_SKIP,
    CAMERA_DEBOUNCE_SECONDS,
    CONFIDENCE_THRESHOLD,
    RESULT_LIVE_FRAMES_DIR,
)
from backend.detection.detector import YOLODetector
from backend.preprocessing.image_preprocessing import safe_write_image
from backend.database.database import get_db_session
from backend.database.crud import create_inspection_record
from backend.utils.file_handler import generate_unique_filename
from backend.utils.logger import app_logger


class CameraManager:
    """
    Thread-safe webcam capture and real-time streaming manager.
    Supports dynamic device index switching and multi-backend fallback.
    """
    _instance: Optional["CameraManager"] = None
    _lock = threading.Lock()

    def __init__(self, camera_index: int = CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.last_frame: Optional[np.ndarray] = None
        self.last_annotated_frame: Optional[np.ndarray] = None
        self.current_status = "GOOD"
        self.current_defect = "Normal / Good Print"
        self.current_confidence = 0.0
        self.current_detections: List[Dict[str, Any]] = []
        self.fps = 0.0
        self.frame_count = 0
        self.last_defect_log_time = 0.0

        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.error_message: Optional[str] = None

    @classmethod
    def get_instance(cls, camera_index: int = CAMERA_INDEX) -> "CameraManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = CameraManager(camera_index)
            return cls._instance

    @staticmethod
    def list_available_cameras() -> List[Dict[str, Any]]:
        """
        Detect connected camera devices on the system, combining Windows PnP
        enumeration and OpenCV probe testing.
        """
        devices = []
        pnp_names = []
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-PnpDevice -Class Camera -Status OK -ErrorAction SilentlyContinue | Select-Object FriendlyName | ConvertTo-Json",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                parsed = json.loads(res.stdout)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                pnp_names = [item.get("FriendlyName") for item in parsed if item.get("FriendlyName")]
        except Exception as e:
            app_logger.debug(f"PnP camera query notice: {e}")

        # Probe indices 0 to max(len(pnp_names), 3)
        max_probe = max(len(pnp_names) if pnp_names else 0, 3)
        for idx in range(max_probe):
            name = pnp_names[idx] if idx < len(pnp_names) else f"Camera Device {idx}"
            is_active = False
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                try:
                    test_cap = cv2.VideoCapture(idx, backend)
                    if test_cap.isOpened():
                        is_active = True
                        test_cap.release()
                        break
                except Exception:
                    pass

            devices.append({
                "index": idx,
                "name": name,
                "label": f"Cam {idx}: {name}" + (" (Active)" if is_active else ""),
                "is_active": is_active,
            })

        return devices

    def start(self, camera_index: Optional[int] = None) -> tuple[bool, str]:
        """
        Open the camera device and start background capture loop.
        """
        with self._lock:
            if camera_index is not None and camera_index != self.camera_index:
                # Switching to a different camera device
                if self.is_running:
                    self._stop_internal()
                self.camera_index = camera_index

            if self.is_running:
                return True, f"Camera {self.camera_index} is already active."

            app_logger.info(f"Opening camera index {self.camera_index}...")

            # Attempt multiple Windows capture backends (DSHOW, MSMF, Default)
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap or not self.cap.isOpened():
                self.error_message = (
                    f"Camera (Device Index {self.camera_index}) could not be opened.\n\n"
                    "1. Enable Desktop App Camera Access in Windows:\n"
                    "   Settings > Privacy & security > Camera > Toggle 'Let desktop apps access your camera' to ON.\n"
                    "2. Ensure no other application (Zoom, Teams, Windows Camera) is using the webcam.\n"
                    "3. Select a different camera device from the dropdown (e.g. Cam 1 for USB webcam)."
                )
                app_logger.warning(f"Failed to open camera index {self.camera_index}")
                return False, self.error_message

            # Camera opened successfully
            self.is_running = True
            self.stop_event.clear()
            self.error_message = None

            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            app_logger.info(f"Camera {self.camera_index} streaming thread started.")
            return True, f"Camera {self.camera_index} started successfully."

    def _stop_internal(self) -> None:
        """Internal worker to stop thread and release capture without extra lock."""
        self.is_running = False
        self.stop_event.set()
        if self.cap:
            self.cap.release()
            self.cap = None

    def stop(self) -> tuple[bool, str]:
        """
        Stop camera capture and release hardware resources.
        """
        with self._lock:
            if not self.is_running:
                return True, "Camera is already stopped."

            self._stop_internal()
            app_logger.info("Camera stopped and hardware released.")
            return True, "Camera stopped successfully."

    def get_status(self) -> Dict[str, Any]:
        """Return live camera status and latest detection state."""
        return {
            "is_running": self.is_running,
            "camera_index": self.camera_index,
            "fps": round(self.fps, 1),
            "status": self.current_status,
            "dominant_defect": self.current_defect,
            "confidence": round(self.current_confidence, 4),
            "confidence_percentage": round(self.current_confidence * 100, 1),
            "detection_count": len(self.current_detections),
            "detections": self.current_detections,
            "error": self.error_message,
        }

    def _capture_loop(self) -> None:
        """Background thread for continuous frame capture and YOLO inference."""
        detector = YOLODetector.get_instance()
        frame_idx = 0
        fps_start_time = time.time()
        fps_frame_count = 0

        while not self.stop_event.is_set() and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                app_logger.warning("Camera read returned empty frame.")
                time.sleep(0.05)
                continue

            self.last_frame = frame.copy()
            frame_idx += 1
            fps_frame_count += 1

            # Calculate FPS every 10 frames
            if fps_frame_count >= 10:
                elapsed = time.time() - fps_start_time
                self.fps = fps_frame_count / elapsed if elapsed > 0 else 0.0
                fps_start_time = time.time()
                fps_frame_count = 0

            # Run inference periodically based on FRAME_SKIP
            if frame_idx % max(1, FRAME_SKIP) == 0:
                inference = detector.predict(frame)
                self.current_status = inference.get("status", "GOOD")
                self.current_detections = inference.get("detections", [])
                self.current_defect = inference.get("dominant_defect", "Normal / Good Print")
                self.current_confidence = inference.get("max_confidence", 0.0)

                # Automatic defect snapshot debounce logic
                if self.current_status == "DEFECT" and self.current_confidence >= CONFIDENCE_THRESHOLD:
                    now = time.time()
                    if now - self.last_defect_log_time >= CAMERA_DEBOUNCE_SECONDS:
                        self.last_defect_log_time = now
                        self._save_defect_snapshot(frame, self.current_detections, is_auto=True)

            # Generate annotated frame
            annotated = detector.draw_annotations(
                frame,
                self.current_detections,
                status=self.current_status,
                fps=self.fps,
            )
            self.last_annotated_frame = annotated
            time.sleep(0.01)  # small yield for CPU friendliness

    def save_manual_snapshot(self) -> Dict[str, Any]:
        """Manually save the current camera frame and detection record."""
        if not self.is_running or self.last_frame is None:
            return {"success": False, "error": "Camera is not active or no frame available."}
        return self._save_defect_snapshot(self.last_frame, self.current_detections, is_auto=False)

    def _save_defect_snapshot(
        self,
        frame: np.ndarray,
        detections: List[Dict[str, Any]],
        is_auto: bool = False,
    ) -> Dict[str, Any]:
        """Save a frame snapshot to disk and create database record."""
        try:
            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            prefix = "auto_defect" if is_auto else "manual_snapshot"
            filename = generate_unique_filename(f"{prefix}_{timestamp_str}.jpg")
            save_path = RESULT_LIVE_FRAMES_DIR / filename

            # Render annotations on the snapshot
            detector = YOLODetector.get_instance()
            annotated = detector.draw_annotations(frame, detections, status=self.current_status, fps=self.fps)
            saved = safe_write_image(save_path, annotated)

            if not saved:
                return {"success": False, "error": "Failed to write snapshot image to disk."}

            # Record in Database
            with get_db_session() as session:
                record = create_inspection_record(
                    session=session,
                    inspection_type="live",
                    status=self.current_status,
                    original_filename=filename,
                    result_filename=filename,
                    defect_type=self.current_defect,
                    confidence=self.current_confidence,
                    processing_time=round(1000.0 / self.fps, 2) if self.fps > 0 else 0.0,
                    source=f"Live Camera {self.camera_index} ({'Auto Alert' if is_auto else 'Manual Snapshot'})",
                    notes=f"Live inspection snapshot. Detections count: {len(detections)}",
                    detections=detections,
                )
                inspection_id = record.id

            app_logger.info(f"Live defect snapshot saved: {filename} (ID: {inspection_id})")
            return {
                "success": True,
                "inspection_id": inspection_id,
                "filename": filename,
                "image_url": f"/results/live_frames/{filename}",
                "status": self.current_status,
                "defect_type": self.current_defect,
                "confidence": self.current_confidence,
            }
        except Exception as e:
            app_logger.error(f"Error saving camera snapshot: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def generate_mjpeg_stream(self) -> Generator[bytes, None, None]:
        """Yield MJPEG multipart stream frames."""
        while self.is_running:
            if self.last_annotated_frame is not None:
                success, buffer = cv2.imencode(".jpg", self.last_annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if success:
                    frame_bytes = buffer.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
            time.sleep(0.04)  # ~25 FPS stream
