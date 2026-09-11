"""
YOLO Model Validation Script.
Evaluates model on validation dataset and prints metrics.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import BASE_DIR, MODEL_PATH, IMAGE_SIZE
from backend.utils.logger import app_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Validate YOLO model on validation split")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="Path to model weights (.pt)")
    parser.add_argument("--data", type=str, default=str(BASE_DIR / "backend" / "dataset" / "data.yaml"), help="Path to data.yaml")
    parser.add_argument("--imgsz", type=int, default=IMAGE_SIZE, help="Image resolution")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
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

        print(f"Validating model: {model_path} against {args.data}...")
        model = YOLO(str(model_path))
        metrics = model.val(
            data=args.data,
            imgsz=args.imgsz,
            batch=args.batch,
            split="val",
        )

        print("\n" + "=" * 60)
        print("  VALIDATION RESULTS SUMMARY")
        print("=" * 60)
        print(f"  Precision (P)   : {metrics.box.mp:.4f}")
        print(f"  Recall (R)      : {metrics.box.mr:.4f}")
        print(f"  mAP@50          : {metrics.box.map50:.4f}")
        print(f"  mAP@50-95       : {metrics.box.map:.4f}")
        print("=" * 60 + "\n")

    except Exception as e:
        app_logger.error(f"Validation failed: {e}", exc_info=True)
        print(f"Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
