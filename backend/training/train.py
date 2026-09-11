"""
YOLO Model Training Script for 3D Printing Defect Detection.

Supports GPU (CUDA) auto-detection, CPU fallback, configurable hyperparameters,
and automated export of best weights to models/trained/best.pt.
"""

import argparse
import sys
import shutil
from pathlib import Path
import torch

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    BASE_DIR,
    IMAGE_SIZE,
    PRETRAINED_MODEL_PATH,
    TRAINING_RESULTS_DIR,
    TRAINING_RESULTS_PLOT,
)
from backend.utils.logger import app_logger


def parse_args():
    default_model = str(PRETRAINED_MODEL_PATH) if PRETRAINED_MODEL_PATH.exists() else "yolov8n.pt"
    parser = argparse.ArgumentParser(description="Train YOLO model on 3D Printing Defect Dataset")
    parser.add_argument("--data", type=str, default=str(BASE_DIR / "backend" / "dataset" / "data.yaml"), help="Path to data.yaml")
    parser.add_argument("--model", type=str, default=default_model, help="Base pretrained model (e.g. models/pretrained/yolo_base.pt, yolov8n.pt)")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size (e.g. 8, 16, 32)")
    parser.add_argument("--imgsz", type=int, default=IMAGE_SIZE, help="Image resolution")
    parser.add_argument("--lr0", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--device", type=str, default="", help="Device: '0', '0,1', or 'cpu'. Auto-detects if empty.")
    parser.add_argument("--workers", type=int, default=4, help="DataLoader workers")
    return parser.parse_args()


def detect_device(requested_device: str) -> str:
    """Automatically detect best available compute device."""
    if requested_device:
        return requested_device
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        app_logger.info(f"CUDA GPU detected: {gpu_name}")
        return "0"
    app_logger.info("CUDA not available. Falling back to CPU.")
    return "cpu"


def main():
    args = parse_args()
    device = detect_device(args.device)

    data_path = Path(args.data)
    if not data_path.exists():
        app_logger.critical(f"Dataset config file not found at: {data_path}")
        print(f"Error: {data_path} not found. Ensure dataset/data.yaml exists.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("  3D PRINTING DEFECT DETECTION - YOLO TRAINING PIPELINE")
    print("=" * 70)
    print(f"  Dataset Config : {data_path}")
    print(f"  Base Model     : {args.model}")
    print(f"  Epochs         : {args.epochs}")
    print(f"  Batch Size     : {args.batch}")
    print(f"  Image Size     : {args.imgsz}")
    print(f"  Compute Device : {device}")
    print("=" * 70 + "\n")

    try:
        from ultralytics import YOLO

        model = YOLO(args.model)
        app_logger.info("Initiating model training...")

        results = model.train(
            data=str(data_path),
            epochs=args.epochs,
            batch=args.batch,
            imgsz=args.imgsz,
            lr0=args.lr0,
            device=device,
            workers=args.workers,
            project=str(TRAINING_RESULTS_DIR),
            name="train_run",
            exist_ok=True,
            plots=True,
        )

        app_logger.info("Training completed successfully.")

        # Copy best.pt and last.pt to models/trained/
        trained_dir = BASE_DIR / "backend" / "models" / "trained"
        trained_dir.mkdir(parents=True, exist_ok=True)

        run_weights_dir = TRAINING_RESULTS_DIR / "train_run" / "weights"
        if run_weights_dir.exists():
            best_weight = run_weights_dir / "best.pt"
            last_weight = run_weights_dir / "last.pt"

            if best_weight.exists():
                shutil.copy(best_weight, trained_dir / "best.pt")
                print(f"[SUCCESS] Copied best weights to -> {trained_dir / 'best.pt'}")

            if last_weight.exists():
                shutil.copy(last_weight, trained_dir / "last.pt")
                print(f"[SUCCESS] Copied last weights to -> {trained_dir / 'last.pt'}")

        # Copy results.png if produced by YOLO
        yolo_plot = TRAINING_RESULTS_DIR / "train_run" / "results.png"
        if yolo_plot.exists():
            shutil.copy(yolo_plot, TRAINING_RESULTS_PLOT)
            print(f"[SUCCESS] Training curves plot saved to -> {TRAINING_RESULTS_PLOT}")

        print("\nTraining workflow finished successfully!")

    except Exception as e:
        app_logger.critical(f"Training pipeline failed: {e}", exc_info=True)
        print(f"Training failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
