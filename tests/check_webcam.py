"""
Webcam Hardware & Streaming Diagnostics Script.
Tests physical camera devices via OpenCV VideoCapture on multiple indices (0, 1, 2),
measures frame capture speed/resolution, and validates backend CameraManager streaming pipeline.
"""

import sys
import time
from pathlib import Path
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.detection.camera_detector import CameraManager
from backend.detection.detector import YOLODetector


def probe_webcams():
    print("\n" + "=" * 70)
    print("  WEBCAM HARDWARE & STREAMING DIAGNOSTICS")
    print("=" * 70)

    found_cameras = []

    # Probe indices 0 to 3
    for idx in range(4):
        print(f"\n[Probing Camera Index {idx}]")
        # Try MSMF first, then DSHOW for Windows
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(idx)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w, c = frame.shape
                fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                backend_name = cap.getBackendName()
                print(f"  -> Status:    ONLINE & FUNCTIONAL")
                print(f"  -> Backend:   {backend_name}")
                print(f"  -> Resolution: {w}x{h} ({c} channels)")
                print(f"  -> FPS:       {fps}")
                found_cameras.append((idx, w, h, fps))
            else:
                print(f"  -> Opened device but could not read frame (device busy or virtual driver).")
            cap.release()
        else:
            print(f"  -> No device detected at index {idx}.")

    print("\n" + "-" * 70)
    if found_cameras:
        print(f"[SUMMARY] Found {len(found_cameras)} active hardware camera(s):")
        for idx, w, h, fps in found_cameras:
            print(f"  - Camera {idx}: {w}x{h} @ {fps} FPS")
    else:
        print("[SUMMARY] No physical webcam hardware is currently attached or accessible.")
        print("  -> The application will operate with graceful camera offline handling.")
        print("  -> When a webcam is plugged in, clicking 'Start Camera' in the UI will connect immediately.")

    # -------------------------------------------------------------
    # Test Backend CameraManager Integration
    # -------------------------------------------------------------
    print("\n[Testing Backend CameraManager Subsystem]")
    manager = CameraManager.get_instance()
    detector = YOLODetector.get_instance()

    print(f"  - Manager Singleton: OK")
    print(f"  - Initial is_running: {manager.is_running}")

    if found_cameras:
        print("  - Testing live frame acquisition & YOLO defect detection loop...")
        start_ok = manager.start(camera_index=found_cameras[0][0])
        print(f"  - CameraManager.start() returned: {start_ok}")
        if start_ok:
            time.sleep(1.5)
            frame_bytes = manager.get_latest_frame_bytes()
            print(f"  - Captured JPEG frame size: {len(frame_bytes) if frame_bytes else 0} bytes")
            print(f"  - Telemetry FPS: {manager.fps}, Status: {manager.latest_status}, Defect: {manager.dominant_defect}")
            manager.stop()
            print(f"  - CameraManager.stop() executed cleanly.")
    else:
        print("  - Testing offline fallback in CameraManager...")
        start_res = manager.start(camera_index=0)
        print(f"  - Offline start handled safely without crashing (Returned: {start_res})")
        manager.stop()

    print("=" * 70 + "\n")
    return len(found_cameras) > 0


if __name__ == "__main__":
    probe_webcams()
