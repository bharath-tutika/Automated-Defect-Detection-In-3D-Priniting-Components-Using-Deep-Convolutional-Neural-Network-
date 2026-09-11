"""
AI Detection Engine using YOLO (Ultralytics).
Handles model loading once, graceful missing-model behavior, inference execution,
and standard annotation rendering.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import cv2
import numpy as np

from config import (
    MODEL_PATH,
    PRETRAINED_MODEL_PATH,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    IMAGE_SIZE,
    DEFECT_CLASSES,
    CLASS_NAME_TO_LABEL,
)
from backend.utils.logger import app_logger


class YOLODetector:
    """
    Central AI Object Detector for 3D Printing Defect Detection.
    Maintains a single model instance in memory.
    """
    _instance: Optional["YOLODetector"] = None

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.model = None
        self.model_loaded = False
        self.model_classes: Dict[int, str] = {}
        self.load_error: Optional[str] = None
        self._load_model()

    @classmethod
    def get_instance(cls, model_path: Optional[Path] = None) -> "YOLODetector":
        """Singleton accessor for detector instance."""
        if cls._instance is None:
            cls._instance = YOLODetector(model_path)
        elif model_path and cls._instance.model_path != Path(model_path):
            cls._instance = YOLODetector(model_path)
        return cls._instance

    def _load_model(self) -> None:
        """
        Attempt to load YOLO model weights if file exists.
        Loads model ONCE and inspects model.names.
        """
        self.model = None
        self.model_loaded = False
        self.model_classes = {}
        self.load_error = None

        print("\n" + "-" * 60)
        print(f"MODEL PATH:    {self.model_path}")
        print(f"MODEL EXISTS:  {self.model_path.exists()}")

        selected_path = None
        if self.model_path.exists():
            selected_path = self.model_path
        elif PRETRAINED_MODEL_PATH and PRETRAINED_MODEL_PATH.exists():
            selected_path = PRETRAINED_MODEL_PATH
        else:
            # Fallback to YOLOv8 base model so server never crashes
            selected_path = "yolov8n.pt"

        try:
            from ultralytics import YOLO
            app_logger.info(f"Loading YOLO model from {selected_path}...")
            self.model = YOLO(str(selected_path))
            self.model_loaded = True

            # Extract actual class names directly from the loaded model
            if hasattr(self.model, "names") and self.model.names:
                self.model_classes = {int(k): str(v) for k, v in self.model.names.items()}
            elif hasattr(self.model, "model") and hasattr(self.model.model, "names") and self.model.model.names:
                self.model_classes = {int(k): str(v) for k, v in self.model.model.names.items()}
            else:
                self.model_classes = {k: v["name"] for k, v in DEFECT_CLASSES.items()}

            print(f"MODEL LOADED:  True ({selected_path})")
            print(f"MODEL CLASSES: {self.model_classes}")
            print("-" * 60 + "\n")
            app_logger.info(f"YOLO model loaded successfully from {selected_path} with classes: {self.model_classes}")
        except Exception as e:
            self.load_error = f"Error loading model from {selected_path}: {str(e)}"
            print(f"MODEL LOADED:  False (Error: {e})")
            print("-" * 60 + "\n")
            app_logger.error(self.load_error, exc_info=True)
            self.model_loaded = False

    def reload(self) -> bool:
        """Reload or check for newly added model weights."""
        self._load_model()
        return self.model_loaded

    def predict(
        self,
        image_input: Union[str, Path, np.ndarray],
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Perform real object detection on an image input using the YOLO model.
        Returns ONLY actual detections returned by YOLO without mock values.
        """
        start_time = time.perf_counter()

        if not self.model_loaded or self.model is None:
            # Check if model has been added since startup
            if self.model_path.exists():
                self._load_model()

        if not self.model_loaded or self.model is None:
            return {
                "success": False,
                "model_available": False,
                "status": "MODEL_NOT_FOUND",
                "message": "Trained YOLO model not found. Please place best.pt in models/trained/best.pt.",
                "error": self.load_error or f"Trained YOLO model not found at '{self.model_path}'. Add models/trained/best.pt to enable AI detection.",
                "detections": [],
                "defect_count": 0,
                "processing_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
            }

        conf = conf_threshold if conf_threshold is not None else CONFIDENCE_THRESHOLD
        iou = iou_threshold if iou_threshold is not None else IOU_THRESHOLD

        try:
            results = self.model(
                image_input,
                conf=conf,
                iou=iou,
                imgsz=IMAGE_SIZE,
                verbose=False
            )

            detections: List[Dict[str, Any]] = []
            has_defect = False
            dominant_defect = None
            max_conf = 0.0

            if results and len(results) > 0:
                result = results[0]
                boxes = result.boxes

                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        confidence = float(box.conf[0].item())
                        coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                        # Read actual class name from the model's own class mapping
                        raw_class_name = self.model_classes.get(cls_id, f"class_{cls_id}")

                        # Check if config provides a custom human-readable label
                        class_info = DEFECT_CLASSES.get(cls_id, {})
                        display_label = class_info.get("label", raw_class_name.replace("_", " ").title())
                        is_defect = class_info.get(
                            "is_defect",
                            raw_class_name.lower() not in ["normal", "good", "good_print", "good print"]
                        )

                        if is_defect:
                            has_defect = True
                            if confidence > max_conf:
                                max_conf = confidence
                                dominant_defect = display_label
                        else:
                            if not has_defect and confidence > max_conf:
                                max_conf = confidence
                                dominant_defect = display_label

                        detections.append({
                            "class_id": cls_id,
                            "class_name": display_label,
                            "raw_class": raw_class_name,
                            "confidence": round(confidence, 4),
                            "is_defect": is_defect,
                            "bbox": {
                                "x1": round(coords[0], 1),
                                "y1": round(coords[1], 1),
                                "x2": round(coords[2], 1),
                                "y2": round(coords[3], 1),
                            },
                        })

            status = "DEFECT" if has_defect else "GOOD"
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if len(detections) == 0:
                status = "GOOD"
                dominant_defect = "No Defect Detected"
                actual_conf = 0.0
            else:
                actual_conf = round(max_conf, 4)

            return {
                "success": True,
                "model_available": True,
                "status": status,
                "dominant_defect": dominant_defect or ("No Defect Detected" if status == "GOOD" else "Defect Detected"),
                "max_confidence": actual_conf,
                "confidence": actual_conf,
                "confidence_percentage": round(actual_conf * 100, 2) if actual_conf > 0 else 0.0,
                "detections": detections,
                "defect_count": sum(1 for d in detections if d["is_defect"]),
                "total_detections": len(detections),
                "processing_time_ms": elapsed_ms,
            }

        except Exception as e:
            app_logger.error(f"Inference error: {e}", exc_info=True)
            return {
                "success": False,
                "model_available": True,
                "status": "ERROR",
                "error": f"Inference execution failed: {str(e)}",
                "detections": [],
                "defect_count": 0,
                "processing_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
            }

    @staticmethod
    def draw_annotations(
        img: np.ndarray,
        detections: List[Dict[str, Any]],
        status: str = "GOOD",
        fps: Optional[float] = None,
    ) -> np.ndarray:
        """
        Draw clean bounding boxes, defect labels, confidence badges, and status banner.
        """
        annotated = img.copy()
        h, w = annotated.shape[:2]

        # Colors (BGR)
        COLOR_DEFECT = (0, 0, 220)       # Vivid Crimson Red for defects
        COLOR_GOOD = (40, 180, 40)        # Bright Emerald Green for normal / good
        COLOR_TEXT = (255, 255, 255)      # White
        COLOR_BG_DARK = (20, 20, 25)      # Dark translucent background

        # Draw individual detection bounding boxes
        for det in detections:
            bbox = det.get("bbox", {})
            x1 = int(bbox.get("x1", 0))
            y1 = int(bbox.get("y1", 0))
            x2 = int(bbox.get("x2", 0))
            y2 = int(bbox.get("y2", 0))

            is_defect = det.get("is_defect", True)
            box_color = COLOR_DEFECT if is_defect else COLOR_GOOD
            class_name = det.get("class_name", "Defect")
            conf = det.get("confidence", 0.0)
            label = f"{class_name} {int(conf * 100)}%"

            # Draw box with rounded corners / thick border
            thickness = max(2, int(min(w, h) / 300))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, thickness)

            # Label banner
            font_scale = max(0.5, min(w, h) / 900)
            font_thick = max(1, int(font_scale * 2))
            (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thick)

            label_y1 = max(0, y1 - text_h - 10)
            label_y2 = y1
            label_x2 = min(w, x1 + text_w + 14)

            # Label background badge
            cv2.rectangle(annotated, (x1, label_y1), (label_x2, label_y2), box_color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 7, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                COLOR_TEXT,
                font_thick,
                cv2.LINE_AA,
            )

        # Header Status Banner Overlay (Top Left)
        banner_color = COLOR_DEFECT if status == "DEFECT" else COLOR_GOOD
        banner_text = "STATUS: DEFECT DETECTED" if status == "DEFECT" else "STATUS: GOOD PRINT"
        if status == "UNKNOWN":
            banner_color = (120, 120, 120)
            banner_text = "STATUS: MODEL NOT LOADED"

        status_scale = max(0.6, min(w, h) / 800)
        status_thick = max(1, int(status_scale * 2))
        (st_w, st_h), _ = cv2.getTextSize(banner_text, cv2.FONT_HERSHEY_SIMPLEX, status_scale, status_thick)

        # Header box
        padding = 10
        cv2.rectangle(annotated, (15, 15), (15 + st_w + padding * 2, 15 + st_h + padding * 2), (20, 20, 20), -1)
        cv2.rectangle(annotated, (15, 15), (15 + st_w + padding * 2, 15 + st_h + padding * 2), banner_color, 2)
        cv2.putText(
            annotated,
            banner_text,
            (15 + padding, 15 + padding + st_h),
            cv2.FONT_HERSHEY_SIMPLEX,
            status_scale,
            banner_color,
            status_thick,
            cv2.LINE_AA,
        )

        # Draw FPS counter if provided (Top Right)
        if fps is not None:
            fps_text = f"FPS: {fps:.1f}"
            (f_w, f_h), _ = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, status_scale, status_thick)
            fx = w - f_w - padding * 2 - 15
            cv2.rectangle(annotated, (fx, 15), (w - 15, 15 + f_h + padding * 2), (20, 20, 20), -1)
            cv2.rectangle(annotated, (fx, 15), (w - 15, 15 + f_h + padding * 2), (0, 200, 255), 2)
            cv2.putText(
                annotated,
                fps_text,
                (fx + padding, 15 + padding + f_h),
                cv2.FONT_HERSHEY_SIMPLEX,
                status_scale,
                (0, 220, 255),
                status_thick,
                cv2.LINE_AA,
            )

        return annotated
