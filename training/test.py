"""
YOLO Model Test Evaluation Script.
Runs inference on unseen test partition (dataset/test).
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import BASE_DIR, MODEL_PATH, IMAGE_SIZE
from backend.utils.logger import app_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Test YOLO model on test partition")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="Path to model weights (.pt)")
    parser.add_argument("--data", type=str, default=str(BASE_DIR / "dataset" / "data.yaml"), help="Path to data.yaml")
    parser.add_argument("--imgsz", type=int, default=IMAGE_SIZE, help="Image resolution")
    return parser.parse_args()


def main():
    args = parse_args()
    model_path = Path(args.model)

    if not model_path.exists():
        print(f"Error: Model weights not found at '{model_path}'.")
        print("Please train a model first using: python training/train.py")
        sys.exit(1)

    try:
        from ultralytics import YOLO

        print(f"Testing model: {model_path} against test partition...")
        model = YOLO(str(model_path))
        metrics = model.val(
            data=args.data,
            imgsz=args.imgsz,
            split="test",
        )

        print("\n" + "=" * 60)
        print("  TEST EVALUATION SUMMARY")
        print("=" * 60)
        print(f"  Test Precision  : {metrics.box.mp:.4f}")
        print(f"  Test Recall     : {metrics.box.mr:.4f}")
        print(f"  Test mAP@50     : {metrics.box.map50:.4f}")
        print(f"  Test mAP@50-95  : {metrics.box.map:.4f}")
        print("=" * 60 + "\n")

    except Exception as e:
        app_logger.error(f"Test evaluation failed: {e}", exc_info=True)
        print(f"Test evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
