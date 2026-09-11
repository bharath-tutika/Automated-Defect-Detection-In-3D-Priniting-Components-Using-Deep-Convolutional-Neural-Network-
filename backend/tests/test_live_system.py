"""
Live Integration and Feature Verification Script.
Run this as a standalone script (not through pytest) to validate all endpoints
against a running server at http://127.0.0.1:5000.

Usage:
    python tests/test_live_system.py
"""

import io
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image

BASE_URL = "http://127.0.0.1:5000"


def check_endpoint(name, method, url, expected_status=200, data=None, headers=None):
    """Make an HTTP request and return (status, json_data, raw_body)."""
    headers = headers or {}
    req = urllib.request.Request(
        f"{BASE_URL}{url}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            status = resp.status
            try:
                json_data = json.loads(body)
            except Exception:
                json_data = None
            print(f" [PASS] {name:<40} | Status: {status}")
            return status, json_data, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            json_data = json.loads(body)
        except Exception:
            json_data = None
        if e.code == expected_status:
            print(f" [PASS] {name:<40} | Expected Status: {e.code}")
            return e.code, json_data, body
        else:
            print(f" [FAIL] {name:<40} | Expected {expected_status}, Got {e.code}")
            return e.code, json_data, body
    except Exception as ex:
        print(f" [FAIL] {name:<40} | Error: {ex}")
        return 0, None, str(ex)


def run_all_checks():
    print("\n" + "=" * 70)
    print("  DEFECTVISION AI - LIVE FEATURE VALIDATION TEST RUNNER")
    print("=" * 70)

    # 1. Base Homepage
    check_endpoint("1. Frontend Home Page", "GET", "/", 200)

    # 2. Subpages
    for page in ["dashboard", "image-inspection", "video-inspection", "live-inspection", "history", "model-performance"]:
        check_endpoint(f"   Subpage: {page}", "GET", f"/pages/{page}.html", 200)

    # 3. System Health API
    s, d, _ = check_endpoint("2. System Health Endpoint", "GET", "/api/health", 200)
    if d:
        print(f"      -> System Status:    {d.get('data', {}).get('status')}")
        print(f"      -> Database OK:      {d.get('data', {}).get('database_available')}")
        print(f"      -> AI Model Active:  {d.get('data', {}).get('model_available')}")

    # 4. Dashboard Stats
    s, d, _ = check_endpoint("3. Dashboard Stats KPI API", "GET", "/api/dashboard/stats", 200)
    if d:
        stats = d.get('data', {})
        print(f"      -> Total: {stats.get('total_inspections')}, Good: {stats.get('good_prints')}, Defects: {stats.get('defects_detected')}, Rate: {stats.get('defect_rate')}%")

    # 5. Dashboard Charts
    s, d, _ = check_endpoint("4. Dashboard Chart Distributions", "GET", "/api/dashboard/charts", 200)
    if d:
        charts = d.get('data', {})
        print(f"      -> Chart Datasets: {list(charts.keys())}")

    # 6. Model Info
    s, d, _ = check_endpoint("5. Model Information & Classes", "GET", "/api/model/info", 200)
    if d:
        info = d.get('data', {})
        print(f"      -> Defect Classes: {info.get('classes_count')} registered classes")

    # 7. Model Metrics
    s, d, _ = check_endpoint("6. Model Empirical Metrics API", "GET", "/api/model/metrics", 200)
    if d:
        metrics_info = d.get('data', {})
        print(f"      -> Metrics Available: {metrics_info.get('metrics_available')}")

    # 8. Inspection History
    s, d, _ = check_endpoint("7. Inspection Audit History API", "GET", "/api/history?page=1&per_page=5", 200)
    if d:
        pag = d.get('data', {}).get('pagination', {})
        print(f"      -> Total Records: {pag.get('total_items')} across {pag.get('total_pages')} page(s)")

    # 9. Camera Status
    s, d, _ = check_endpoint("8. Live Camera Status API", "GET", "/api/camera/status", 200)
    if d:
        cam_info = d.get('data', {})
        print(f"      -> Camera Active: {cam_info.get('is_running')}, FPS: {cam_info.get('fps')}")

    # 10. Image Upload Endpoint
    boundary = "----TestFormBoundary123456"
    img_buf = io.BytesIO()
    Image.new("RGB", (120, 120), color=(80, 160, 220)).save(img_buf, format="JPEG")
    img_bytes = img_buf.getvalue()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="sample_print.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    s, d, _ = check_endpoint("9. Image Upload & Inference", "POST", "/api/image/predict", 200, data=body, headers=headers)
    if d:
        print(f"      -> success={d.get('success')}, status={d.get('data', {}).get('status')}, defect={d.get('data', {}).get('dominant_defect')}")

    # 11. Video Upload (malformed => expect error, but graceful)
    vid_body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="sample_timelapse.mp4"\r\n'
        f"Content-Type: video/mp4\r\n\r\n"
    ).encode("utf-8") + b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42" + f"\r\n--{boundary}--\r\n".encode("utf-8")

    s, d, _ = check_endpoint("10. Video Upload (graceful error)", "POST", "/api/video/predict", 500, data=vid_body, headers=headers)
    if d:
        print(f"      -> Gracefully handled: error='{d.get('error')}'")

    print("=" * 70)
    print("  ALL FEATURE VERIFICATION CHECKS COMPLETED!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    # Check that server is up first
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=3)
    except Exception:
        print(f"\n[ERROR] Server is not running at {BASE_URL}.")
        print("Start it first with:  .venv\\Scripts\\python run.py")
        sys.exit(1)
    run_all_checks()
