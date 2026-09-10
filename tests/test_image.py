"""
Unit tests for Image Inspection pipeline and API endpoints.
"""

import io
import unittest
from PIL import Image
import numpy as np

from backend.app import create_app
from backend.utils.file_handler import is_allowed_image, validate_image


class TestImageInspection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_allowed_image_extensions(self):
        """Test extension check logic."""
        self.assertTrue(is_allowed_image("part1.jpg"))
        self.assertTrue(is_allowed_image("part2.PNG"))
        self.assertTrue(is_allowed_image("layer.webp"))
        self.assertFalse(is_allowed_image("script.py"))
        self.assertFalse(is_allowed_image("document.pdf"))

    def test_predict_no_file(self):
        """Test API response when no file is uploaded."""
        response = self.client.post("/api/image/predict")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])

    def test_predict_unsupported_file_extension(self):
        """Test API rejection of unsupported file types."""
        data = {"file": (io.BytesIO(b"dummy text content"), "test.txt")}
        response = self.client.post("/api/image/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 415)
        res = response.get_json()
        self.assertFalse(res["success"])

    def test_predict_valid_image_upload(self):
        """Test upload with synthesized PNG image."""
        # Create small test image
        img_bytes = io.BytesIO()
        img = Image.new("RGB", (200, 200), color=(100, 150, 200))
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        data = {"file": (img_bytes, "test_print.png")}
        response = self.client.post("/api/image/predict", data=data, content_type="multipart/form-data")

        # Returns 200 (if model exists) or 503 (if best.pt not found, with model_available=False)
        self.assertIn(response.status_code, [200, 503])
        res = response.get_json()
        self.assertIn("success", res)


if __name__ == "__main__":
    unittest.main()
