"""
Live YOLO Inference Integration Test.
This test requires the application server to be RUNNING at http://127.0.0.1:5000.
Run as a standalone script:   python tests/test_live_inference.py
Or after starting the server: .venv\\Scripts\\python run.py
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check_server():
    """Return True if the server is reachable."""
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=3)
        return True
    except Exception:
        return False


def run_live_inference():
    print("=" * 70)
    print("  TESTING LIVE YOLO INFERENCE ON REAL TEST SAMPLES")
    print("=" * 70)

    # 1. Health Check
    req = urllib.request.Request(f"{BASE_URL}/api/health")
    with urllib.request.urlopen(req) as resp:
        health = json.loads(resp.read().decode("utf-8"))
        model_ok = health.get('data', {}).get('model_available', False)
        print(f"1. Health Check -> Model Available: {model_ok}")
        if not model_ok:
            print("   NOTE: AI model weights not found. Inference results will show MODEL_NOT_FOUND.")

    # 2. Empirical Metrics Check
    req = urllib.request.Request(f"{BASE_URL}/api/model/metrics")
    with urllib.request.urlopen(req) as resp:
        metrics = json.loads(resp.read().decode("utf-8"))
        metrics_available = metrics.get('data', {}).get('metrics_available', False)
        print(f"2. Model Metrics -> Available: {metrics_available}")
        if metrics_available:
            print(f"   Metrics: {metrics['data']['metrics']}")

    # 3. Test on synthetic test samples
    test_files = [
        ("Stringing Test", PROJECT_ROOT / "dataset/test/images/test_stringing_00.jpg"),
        ("Normal Good Print Test", PROJECT_ROOT / "dataset/test/images/test_normal_00.jpg"),
        ("Spaghetti Failure Test", PROJECT_ROOT / "dataset/test/images/test_spaghetti_00.jpg"),
    ]

    boundary = "----TestBoundaryYOLO"

    for label, p in test_files:
        if not Path(p).exists():
            print(f"\n   Skipping {label} (file not found at: {p})")
            continue

        img_data = Path(p).read_bytes()
        filename = Path(p).name
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + img_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = urllib.request.Request(
            f"{BASE_URL}/api/image/predict",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                d = res.get("data", {})
                print(f"\n3. Inspection Result: {label}")
                print(f"   -> HTTP Status:       {resp.status}")
                print(f"   -> Detection Status:  {d.get('status')} ({d.get('dominant_defect')})")
                print(f"   -> Confidence:        {d.get('confidence_percentage')}%")
                print(f"   -> Processing Time:   {d.get('processing_time_ms')} ms")
                print(f"   -> Annotated Image:   {d.get('result_image_url')}")
                print(f"   -> Localized Objects: {len(d.get('detections', []))} box(es)")
                for det in d.get("detections", []):
                    bbox = det.get("bbox", {})
                    print(f"      - {det.get('class_name')} ({det.get('confidence'):.2f}): [{bbox.get('x1')}, {bbox.get('y1')}] -> [{bbox.get('x2')}, {bbox.get('y2')}]")
        except urllib.error.HTTPError as e:
            body_txt = e.read().decode("utf-8", errors="ignore")
            try:
                err_data = json.loads(body_txt)
            except Exception:
                err_data = {}
            print(f"\n   [{label}] API responded with HTTP {e.code}: {err_data.get('error', body_txt[:200])}")

    print("\n" + "=" * 70)
    print("  LIVE INFERENCE CHECKS COMPLETED!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    if not check_server():
        print(f"\n[ERROR] Server is not running at {BASE_URL}.")
        print("Start it with: .venv\\Scripts\\python run.py\n")
        sys.exit(1)
    run_live_inference()
