# Project Abstract

## AI-Based Real-Time 3D Printing Defect Detection Using Computer Vision

### Overview
Additive manufacturing (3D printing) via Fused Deposition Modeling (FDM) has evolved from rapid prototyping into mainstream direct digital manufacturing for aerospace, biomedical, automotive, and customized consumer goods. However, FDM processes remain prone to physical defects caused by mechanical vibrations, improper thermal dynamics, material inconsistencies, and nozzle clogs. Traditional manual post-print inspection results in substantial wastage of thermoplastic filaments (PLA, PETG, ABS), wasted energy, and idle printer hours.

This project introduces an end-to-end, automated computer vision and deep learning inspection platform powered by the Ultralytics YOLO (You Only Look Once) object detection architecture. The system provides real-time in-situ monitoring, image-based batch quality assurance, and video timelapse processing to classify and localize common FDM defect categories:

1. **Stringing (Oozing)**
2. **Warping (Bed Detachment)**
3. **Layer Shift (Step Skips)**
4. **Under-Extrusion (Voids/Gaps)**
5. **Over-Extrusion (Blobs/Zits)**
6. **Spaghetti Failure (Print Detachment)**
7. **Normal / Good Print**

### Key Engineering Features
- **Tri-Modal Inspection Pipeline**: Supports static photo inspection, streaming video analysis, and low-latency webcam monitoring.
- **Debounced Anomaly Logging**: Automated snapshot logging when defect confidence exceeds thresholds, preventing database flooding.
- **Relational Audit Trail**: SQLite database with SQLAlchemy ORM logging all inspections, detection coordinates, confidences, and timestamps.
- **Edge-Ready & Graceful**: Dynamic model availability handling that warns the operator if weights (`best.pt`) are uncalibrated or absent, avoiding fabricated predictions.
