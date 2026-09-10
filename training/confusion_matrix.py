"""
Confusion Matrix Generation Script for 3D Printing Defect Detection.
Plots and saves confusion matrix to training/results/confusion_matrix.png.
"""

import argparse
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    DEFECT_CLASSES,
    CONFUSION_MATRIX_FILE,
    TRAINING_RESULTS_DIR,
    MODEL_PATH,
)
from backend.utils.logger import app_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Confusion Matrix plot for trained model")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="Path to trained model (.pt)")
    return parser.parse_args()


def main():
    args = parse_args()
    model_path = Path(args.model)

    if not model_path.exists():
        print(f"Error: Model file not found at '{model_path}'.")
        print("Please train a model first using: python training/train.py")
        sys.exit(1)

    try:
        from ultralytics import YOLO
        print(f"Loading model {model_path} for confusion matrix computation...")
        model = YOLO(str(model_path))
        val_results = model.val(data="dataset/data.yaml", split="val")

        # Check if Ultralytics generated a confusion matrix
        if hasattr(val_results, "confusion_matrix") and val_results.confusion_matrix is not None:
            matrix = val_results.confusion_matrix.matrix
            class_labels = [v["label"] for k, v in sorted(DEFECT_CLASSES.items())]

            TRAINING_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

            plt.figure(figsize=(10, 8))
            sns.heatmap(
                matrix,
                annot=True,
                fmt=".2f",
                cmap="Blues",
                xticklabels=class_labels,
                yticklabels=class_labels,
            )
            plt.title("3D Printing Defect Detection - Confusion Matrix", fontsize=14, pad=12)
            plt.xlabel("Predicted Class", fontsize=12)
            plt.ylabel("True Class", fontsize=12)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            plt.savefig(CONFUSION_MATRIX_FILE, dpi=300)
            plt.close()
            print(f"[SUCCESS] Confusion matrix saved to -> {CONFUSION_MATRIX_FILE}")
        else:
            print("Validation completed, but no confusion matrix returned by YOLO.")

    except Exception as e:
        app_logger.error(f"Error generating confusion matrix: {e}", exc_info=True)
        print(f"Failed to generate confusion matrix: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
