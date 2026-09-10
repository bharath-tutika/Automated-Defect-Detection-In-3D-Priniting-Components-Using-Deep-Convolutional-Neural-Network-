"""
Comprehensive Model Evaluation Script.
Computes Precision, Recall, F1-score, mAP@50, mAP@50-95 and exports metrics to training/results/metrics.txt.
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    BASE_DIR,
    MODEL_PATH,
    IMAGE_SIZE,
    METRICS_FILE,
    CONFUSION_MATRIX_FILE,
    TRAINING_RESULTS_DIR,
)
from backend.utils.logger import app_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate YOLO model and generate metric logs")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="Path to trained model (.pt)")
    parser.add_argument("--data", type=str, default=str(BASE_DIR / "dataset" / "data.yaml"), help="Path to data.yaml")
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

        print(f"Evaluating model: {model_path}...")
        model = YOLO(str(model_path))
        metrics = model.val(data=args.data, imgsz=IMAGE_SIZE, split="val")

        p = float(metrics.box.mp)
        r = float(metrics.box.mr)
        map50 = float(metrics.box.map50)
        map50_95 = float(metrics.box.map)
        f1 = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

        TRAINING_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        metrics_text = f"""Model: {model_path.name}
Architecture: Ultralytics YOLO
Precision: {p:.4f}
Recall: {r:.4f}
F1-Score: {f1:.4f}
mAP@50: {map50:.4f}
mAP@50-95: {map50_95:.4f}
Evaluated Image Size: {IMAGE_SIZE}
Status: EVALUATED
"""
        METRICS_FILE.write_text(metrics_text, encoding="utf-8")
        print(f"[SUCCESS] Metrics exported to -> {METRICS_FILE}")
        print("\n" + metrics_text)

    except Exception as e:
        app_logger.error(f"Evaluation error: {e}", exc_info=True)
        print(f"Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
