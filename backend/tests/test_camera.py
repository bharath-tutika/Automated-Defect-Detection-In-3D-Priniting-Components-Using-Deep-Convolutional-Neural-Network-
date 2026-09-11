"""
Unit tests for Live Camera stream manager and endpoints.
"""

import unittest
from backend.app import create_app
from backend.detection.camera_detector import CameraManager


class TestCameraManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_camera_manager_singleton(self):
        """Test CameraManager singleton instance."""
        m1 = CameraManager.get_instance()
        m2 = CameraManager.get_instance()
        self.assertIs(m1, m2)

    def test_camera_status_api(self):
        """Test GET /api/camera/status endpoint."""
        response = self.client.get("/api/camera/status")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIn("is_running", data["data"])
        self.assertIn("fps", data["data"])

    def test_camera_snapshot_when_offline(self):
        """Verify snapshot fails gracefully when camera is not running."""
        manager = CameraManager.get_instance()
        manager.stop()  # Ensure offline

        response = self.client.post("/api/camera/snapshot")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data["success"])


if __name__ == "__main__":
    unittest.main()
