"""
Direct verification of real YOLO model inference.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.detection.detector import YOLODetector

def main():
    print("=" * 70)
    print("  DIRECT REAL YOLO MODEL INFERENCE VERIFICATION")
    print("=" * 70)

    detector = YOLODetector.get_instance()
    print(f"Model Path:     {detector.model_path}")
    print(f"Model Loaded:   {detector.model_loaded}")
    print(f"Model Classes:  {detector.model_classes}")

    test_images = sorted(Path("dataset/test/images").glob("*.jpg"))
    print(f"\nFound {len(test_images)} test image(s) in dataset/test/images.")

    for img_path in test_images[:7]:
        res = detector.predict(img_path)
        status = res.get("status")
        dominant = res.get("dominant_defect")
        conf = res.get("confidence")
        detections = res.get("detections", [])
        time_ms = res.get("processing_time_ms")

        print(f"\n[Test File: {img_path.name}]")
        print(f"  -> Status:          {status}")
        print(f"  -> Dominant Defect: {dominant}")
        print(f"  -> Confidence:      {conf}")
        print(f"  -> Inference Time:  {time_ms} ms")
        print(f"  -> Bounding Boxes:  {len(detections)}")

        for d in detections:
            bbox = d.get("bbox", {})
            print(f"     - Class: {d.get('class_name')} | Raw: {d.get('raw_class')} | Conf: {d.get('confidence')} | Box: [{bbox.get('x1')}, {bbox.get('y1')}] -> [{bbox.get('x2')}, {bbox.get('y2')}]")

    print("\n" + "=" * 70)
    print("  DIRECT INFERENCE VERIFICATION COMPLETE")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
