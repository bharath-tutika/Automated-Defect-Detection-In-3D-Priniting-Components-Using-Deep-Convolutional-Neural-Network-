# Methodology

## 1. Computer Vision & Deep Learning Pipeline

### 1.1 YOLO Object Detection Framework
The core object detection model uses the single-stage Ultralytics YOLO architecture, which formulates bounding box regression and class probability estimation as a unified regression problem.

```
Input Frame (640x640x3) ──> Backbone (CSPDarknet/Conv) ──> Neck (PANet/FPN) ──> Detection Head (Boxes, Classes, Confidences)
```

- **Loss Functions**: Complete Intersection over Union ($\mathcal{L}_{\text{CIoU}}$) for bounding box spatial accuracy, Binary Cross-Entropy ($\mathcal{L}_{\text{BCE}}$) for class probabilities and objectness.
- **Non-Maximum Suppression (NMS)**: Merges overlapping bounding boxes based on IoU threshold ($0.45$).

---

## 2. Data Preparation & Augmentation
1. **Raw Acquisition**: High-resolution image capture of active 3D prints under varying ambient lighting conditions.
2. **Annotation**: Polygon/rectangular bounding boxes assigned to class IDs:
   - `0`: Normal / Good Print
   - `1`: Stringing
   - `2`: Warping
   - `3`: Layer Shift
   - `4`: Under-Extrusion
   - `5`: Over-Extrusion
   - `6`: Spaghetti Failure
3. **Partitioning**: 70% Training, 20% Validation, 10% Testing.
4. **Augmentation Strategies**: Mosaic augmentation, random horizontal flips, HSV color space jitter, and scale variation.

---

## 3. Streaming and Inference Optimization
- **Singleton Model Management**: Pre-loads YOLO weights once in memory (`YOLODetector`), avoiding cold-start latency per HTTP request.
- **Frame-Skip Strategy**: For video and live camera inspection, inference is performed every $N$ frames (default $N=3$), while bounding boxes are tracked smoothly across intermediate frames to maintain responsive frame rates.
- **Debounced Anomaly Persistence**: When a persistent defect is detected, snapshots and database entries are rate-limited via a configurable debounce timer ($3.0\text{s}$) to eliminate database spamming.
