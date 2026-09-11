"""
Unit tests for Video Inspection pipeline and API endpoints.
"""

import io
import unittest
from backend.app import create_app
from backend.utils.file_handler import is_allowed_video


class TestVideoInspection(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_allowed_video_extensions(self):
        """Test video format extension validator."""
        self.assertTrue(is_allowed_video("print_timelapse.mp4"))
        self.assertTrue(is_allowed_video("capture.AVI"))
        self.assertTrue(is_allowed_video("feed.mov"))
        self.assertFalse(is_allowed_video("image.png"))
        self.assertFalse(is_allowed_video("model.obj"))

    def test_predict_no_video_file(self):
        """Test video prediction route without file."""
        response = self.client.post("/api/video/predict")
        self.assertEqual(response.status_code, 400)
        res = response.get_json()
        self.assertFalse(res["success"])

    def test_predict_unsupported_video_extension(self):
        """Test video prediction route with invalid file format."""
        data = {"file": (io.BytesIO(b"fake data"), "video.xyz")}
        response = self.client.post("/api/video/predict", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 415)


if __name__ == "__main__":
    unittest.main()
