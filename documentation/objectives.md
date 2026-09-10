# Project Objectives

## 1. Primary Objectives
1. **Develop an In-Situ Computer Vision Defect Detector**:
   Construct a deep-learning object detection pipeline using YOLO to identify and localize 3D printing failures in real-time.

2. **Automate Defect Classification Across 7 Categories**:
   Detect Normal Print, Stringing, Warping, Layer Shift, Under-Extrusion, Over-Extrusion, and Spaghetti failures with bounding boxes and calibrated confidence percentages.

3. **Deliver Tri-Modal Inspection Capabilities**:
   - **Image Inspection**: High-resolution single image upload, defect localization, and annotated visual rendering.
   - **Video Inspection**: Sequential frame-by-frame processing without loading entire video files into memory, with defect frequency tracking.
   - **Live Camera Stream**: Real-time webcam monitoring with configurable frame skipping, live FPS measurement, and automated defect snapshotting.

4. **Construct an Academic & Industrial Quality Assurance Interface**:
   Build a responsive web application featuring real-time telemetry, KPI analytics (Total Inspections, Good Prints, Defects Detected, Defect Rate), defect distribution charts, and a searchable inspection audit trail.

5. **Ensure Robust Software Architecture**:
   - Strict avoidance of fabricated metrics or mock predictions.
   - Graceful degradation when weights (`models/trained/best.pt`) or webcam hardware are unavailable.
   - Clean modular codebase separating computer vision inference, data models, routes, and UI presentation.
