"""
Unit tests for AI Detection Engine (backend/detection/detector.py).
"""

import unittest
import numpy as np
from pathlib import Path

from backend.detection.detector import YOLODetector
from config import DEFECT_CLASSES


class TestYOLODetector(unittest.TestCase):

    def setUp(self):
        self.detector = YOLODetector.get_instance()

    def test_singleton_instance(self):
        """Verify that get_instance returns the identical singleton instance."""
        inst2 = YOLODetector.get_instance()
        self.assertIs(self.detector, inst2)

    def test_missing_model_behavior(self):
        """Verify detector handles missing weights gracefully without throwing."""
        fake_detector = YOLODetector(model_path=Path("non_existent_weights.pt"))
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)

        result = fake_detector.predict(dummy_img)

        self.assertFalse(result.get("success", True))
        self.assertFalse(result.get("model_available", True))
        self.assertIn("error", result)
        self.assertEqual(result.get("detections"), [])
        self.assertEqual(result.get("defect_count"), 0)

    def test_defect_classes_mapping(self):
        """Ensure all 7 defect classes are defined with required attributes."""
        self.assertEqual(len(DEFECT_CLASSES), 7)
        self.assertIn(0, DEFECT_CLASSES)
        self.assertEqual(DEFECT_CLASSES[0]["name"], "normal")
        self.assertFalse(DEFECT_CLASSES[0]["is_defect"])

        # Defect classes
        for cid in range(1, 7):
            self.assertIn(cid, DEFECT_CLASSES)
            self.assertTrue(DEFECT_CLASSES[cid]["is_defect"])

    def test_draw_annotations(self):
        """Verify annotation rendering returns valid RGB image array without crashing."""
        dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_detections = [
            {
                "class_id": 3,
                "class_name": "Layer Shift",
                "confidence": 0.92,
                "is_defect": True,
                "bbox": {"x1": 50, "y1": 50, "x2": 200, "y2": 200}
            }
        ]

        annotated = YOLODetector.draw_annotations(dummy_img, mock_detections, status="DEFECT", fps=24.5)
        self.assertIsInstance(annotated, np.ndarray)
        self.assertEqual(annotated.shape, (480, 640, 3))


if __name__ == "__main__":
    unittest.main()
