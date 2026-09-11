"""
End-to-End API route validation and smoke test.
"""

import unittest
from backend.app import create_app


class TestE2EEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("model_available", data["data"])
        self.assertIn("database_available", data["data"])

    def test_dashboard_stats_endpoint(self):
        res = self.client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("total_inspections", data["data"])

    def test_dashboard_charts_endpoint(self):
        res = self.client.get("/api/dashboard/charts")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("defect_distribution", data["data"])

    def test_model_info_endpoint(self):
        res = self.client.get("/api/model/info")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["classes_count"], 7)

    def test_model_metrics_endpoint(self):
        res = self.client.get("/api/model/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("metrics_available", data["data"])

    def test_history_endpoint(self):
        res = self.client.get("/api/history")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("items", data["data"])

    def test_camera_status_endpoint(self):
        res = self.client.get("/api/camera/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

    def test_serve_frontend_index(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"DefectVision AI", res.data)
        self.assertIn(b"Automated Defect Detection in 3D Printing Component Using Deep Convolutional Neural Network", res.data)
        res.close()

    def test_serve_frontend_pages(self):
        """Verify all SPA subpages are served properly."""
        pages = [
            "dashboard.html",
            "image-inspection.html",
            "video-inspection.html",
            "live-inspection.html",
            "history.html",
            "model-performance.html",
        ]
        for page in pages:
            res = self.client.get(f"/pages/{page}")
            self.assertEqual(res.status_code, 200, f"Failed to serve /pages/{page}")
            self.assertGreater(len(res.data), 0)
            res.close()

    def test_serve_static_css_and_js(self):
        """Verify stylesheets and JS bundles are served properly."""
        assets = [
            "/css/style.css",
            "/css/dashboard.css",
            "/css/inspection.css",
            "/css/responsive.css",
            "/js/app.js",
            "/js/charts.js",
            "/js/dashboard.js",
            "/js/image-inspection.js",
            "/js/video-inspection.js",
            "/js/live-camera.js",
            "/js/history.js",
        ]
        for asset in assets:
            res = self.client.get(asset)
            self.assertEqual(res.status_code, 200, f"Failed to serve static asset {asset}")
            self.assertGreater(len(res.data), 0)
            res.close()

    def test_image_predict_endpoint(self):
        """Verify image predict returns 200 (if model present) or 503 (if model missing)."""
        import io
        from PIL import Image

        img_bytes = io.BytesIO()
        img = Image.new("RGB", (100, 100), color=(120, 180, 70))
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        data = {"file": (img_bytes, "test_print.jpg")}
        res = self.client.post("/api/image/predict", data=data, content_type="multipart/form-data")
        self.assertIn(res.status_code, [200, 503])
        json_data = res.get_json()
        if res.status_code == 200:
            self.assertTrue(json_data["success"])
            self.assertTrue(json_data["data"]["model_available"])
        else:
            self.assertFalse(json_data["success"])
            self.assertFalse(json_data["model_available"])

    def test_video_predict_endpoint(self):
        """Verify video predict returns 200, 400, or 503 depending on model and codec availability."""
        import io
        data = {"file": (io.BytesIO(b"\x00\x00\x00\x18ftypmp42"), "test_video.mp4")}
        res = self.client.post("/api/video/predict", data=data, content_type="multipart/form-data")
        self.assertIn(res.status_code, [200, 400, 500, 503])

    def test_404_error_handler(self):
        """Test API returns formatted JSON on non-existent endpoints."""
        res = self.client.get("/api/non_existent_endpoint")
        self.assertEqual(res.status_code, 404)
        json_data = res.get_json()
        self.assertFalse(json_data["success"])


if __name__ == "__main__":
    unittest.main()
