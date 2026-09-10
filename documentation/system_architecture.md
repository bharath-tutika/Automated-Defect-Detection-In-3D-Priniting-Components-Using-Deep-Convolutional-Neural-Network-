# System Architecture

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Client ["Frontend Layer (Browser / UI)"]
        UI_Dash["Dashboard (Chart.js)"]
        UI_Img["Image Inspection"]
        UI_Vid["Video Inspection"]
        UI_Cam["Live Stream (MJPEG)"]
        UI_Hist["Audit History"]
        UI_Perf["Model Performance"]
    end

    subgraph Server ["Backend Layer (Flask 3.x)"]
        Router["Flask REST API Router"]
        StaticServe["Static Media & Results Server"]
        Config["Central Config Module (config.py)"]
        Logger["Logging Module (application.log)"]
    end

    subgraph VisionEngine ["Computer Vision & AI Detection Layer"]
        Detector["YOLODetector (Singleton)"]
        ImgPipeline["Image Pipeline"]
        VidPipeline["Video Stream Pipeline"]
        CamManager["CameraManager (Thread-safe)"]
        Preprocess["Preprocessing (OpenCV / PIL)"]
    end

    subgraph Storage ["Persistence & Model Weights"]
        Weights["models/trained/best.pt"]
        DB[(SQLite: defect_detection.db)]
        Uploads["uploads/ (Images & Videos)"]
        Results["results/ (Annotated Media & Snapshots)"]
    end

    UI_Img -->|POST /api/image/predict| Router
    UI_Vid -->|POST /api/video/predict| Router
    UI_Cam -->|GET /api/camera/stream| Router
    UI_Cam -->|POST /api/camera/start| Router
    UI_Hist -->|GET /api/history| Router
    UI_Dash -->|GET /api/dashboard/stats| Router

    Router --> Detector
    Router --> ImgPipeline
    Router --> VidPipeline
    Router --> CamManager

    Detector --> Weights
    ImgPipeline --> Preprocess
    VidPipeline --> Preprocess
    CamManager --> Preprocess

    ImgPipeline --> Results
    VidPipeline --> Results
    CamManager --> Results
    ImgPipeline --> DB
    VidPipeline --> DB
    CamManager --> DB
```

## Modular Components

1. **`config.py`**: Central source of truth for defect classes, thresholds, and paths.
2. **`backend/detection/detector.py`**: Singleton YOLO wrapper with graceful handling of missing model weights.
3. **`backend/detection/camera_detector.py`**: Background camera thread with MJPEG multipart generator.
4. **`backend/database/`**: SQLAlchemy models with foreign key constraints, cascading deletes, and pagination.
5. **`frontend/`**: Vanilla HTML5, CSS3, Chart.js, and modular JS clients.
