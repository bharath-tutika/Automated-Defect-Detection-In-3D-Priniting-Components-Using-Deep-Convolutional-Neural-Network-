# Project Folder & Directory Structure Specification

## AI-Based Real-Time 3D Printing Defect Detection System

```
3D-PRINTING-DEFECT-DETECTION/
│
├── app.py                                          # Root WSGI application entrypoint for Gunicorn / Cloud deploy
├── wsgi.py                                         # Production WSGI module alias
├── run.py                                          # Local development server launcher & routing
├── config.py                                       # Global system configuration (paths, class names, thresholds)
├── requirements.txt                                # Python dependencies and framework versions
├── Procfile                                        # Process runner manifest for Gunicorn / Railway / Heroku
├── Dockerfile                                      # Container build instructions for Linux / CUDA
├── Aptfile                                         # OS-level dependencies (OpenCV system libraries)
├── nixpacks.toml                                   # Nixpacks cloud deployment build configuration
├── railway.json                                    # Railway deployment configuration
├── README.md                                       # Comprehensive setup and user guide
│
├── backend/                                        # Core Flask backend & Deep Learning microservices
│   ├── __init__.py                                 # Backend package initialization
│   ├── app.py                                      # Flask app factory, CORS config & blueprint registration
│   │
│   ├── database/                                   # Database models & ORM query handlers
│   │   ├── __init__.py                             # Database package initialization
│   │   └── db_handler.py                           # SQLite schema, Session, DefectLog and Inspection models
│   │
│   ├── dataset/                                    # Computer vision training & validation dataset
│   │   ├── data.yaml                               # YOLOv8 dataset configuration (class names & relative paths)
│   │   ├── train/                                  # Training partition
│   │   │   ├── images/                             # Training image samples (.jpg)
│   │   │   └── labels/                             # YOLO normalized bounding box labels (.txt)
│   │   └── val/                                    # Validation partition
│   │       ├── images/                             # Validation image samples (.jpg)
│   │       └── labels/                             # Validation bounding box labels (.txt)
│   │
│   ├── detection/                                  # Computer Vision inference engines
│   │   ├── __init__.py                             # Detection package exports
│   │   ├── detector.py                             # Base YOLOv8 detector singleton and core bounding box parser
│   │   ├── image_detector.py                       # Static image inspection & OpenCV bounding box renderer
│   │   ├── video_detector.py                       # Sequential video inspection and defect summary aggregator
│   │   └── camera_detector.py                      # Real-time webcam MJPEG streamer & debounce defect logger
│   │
│   ├── models/                                     # Deep learning weights & export artifacts
│   │   ├── pretrained/                             # Base YOLOv8 weights (yolo_base.pt)
│   │   ├── trained/                                # Fine-tuned weights (best.pt, last.pt)
│   │   └── exports/                                # Quantized / exported model checkpoints (ONNX/TensorRT)
│   │
│   ├── notebooks/                                  # Jupyter research & analysis notebooks
│   │   ├── 01_dataset_analysis.ipynb               # Class distribution and bounding box exploratory analysis
│   │   ├── 02_data_preprocessing.ipynb             # Image augmentation, letterboxing, and normalization tests
│   │   ├── 03_model_training.ipynb                 # Transfer learning training runs and hyperparameter tuning
│   │   ├── 04_model_evaluation.ipynb               # Validation metrics, Precision-Recall & Confusion Matrix
│   │   └── 05_live_detection_testing.ipynb         # Hardware camera diagnostics and latency profiling
│   │
│   ├── preprocessing/                              # Image & frame transformation pipelines
│   │   ├── __init__.py                             # Preprocessing package exports
│   │   ├── image_preprocessing.py                  # Static image resizing, letterboxing, and color space transforms
│   │   └── frame_preprocessing.py                  # Video / camera frame buffer extraction and normalization
│   │
│   ├── routes/                                     # Flask REST API Blueprints
│   │   ├── __init__.py                             # Route blueprint exports
│   │   ├── image_routes.py                         # Single image upload and inspection endpoint (/api/inspect/image)
│   │   ├── video_routes.py                         # Video upload and asynchronous analysis endpoint (/api/inspect/video)
│   │   ├── camera_routes.py                        # Live MJPEG stream and camera controller (/api/camera/stream)
│   │   ├── dashboard_routes.py                     # KPI metrics, defect frequency & class analytics (/api/dashboard/*)
│   │   └── history_routes.py                       # Inspection log retrieval, filtering, and exports (/api/history/*)
│   │
│   ├── storage/                                    # File caching and persistence directory
│   │   ├── uploads/                                # Temporary incoming uploaded media
│   │   ├── results/                                # Annotated output images and processed videos
│   │   └── snapshots/                              # Real-time camera defect capture snapshots
│   │
│   ├── tests/                                      # Automated test suite and validation scripts
│   │   ├── check_webcam.py                         # Hardware camera device scanner and index diagnostic
│   │   ├── test_detector.py                        # YOLOv8 engine model loading and inference test
│   │   ├── test_image.py                           # Static image inspection pipeline verification
│   │   ├── test_video.py                           # Video processing pipeline verification
│   │   ├── test_camera.py                          # VideoCapture frame grabbing verification
│   │   ├── test_database.py                        # Database schema creation, insertion, and query test
│   │   ├── test_api_e2e.py                         # Full Flask REST API end-to-end integration test
│   │   ├── test_live_inference.py                  # Inference latency and throughput benchmarking
│   │   ├── test_live_system.py                     # Integrated live webcam and database persistence test
│   │   ├── test_real_model_inference.py            # Model validation on realistic test cases
│   │   └── test_all_features_deep.py               # Comprehensive cross-module system test
│   │
│   ├── training/                                   # Model training, validation, and evaluation scripts
│   │   ├── train.py                                # YOLOv8 training execution script with hyperparameters
│   │   ├── validate.py                             # Validation run script calculating mAP, Precision, and Recall
│   │   ├── evaluate.py                             # Evaluation harness generating comprehensive metric summaries
│   │   ├── test.py                                 # Standalone test inference script
│   │   ├── confusion_matrix.py                     # Normalized and raw confusion matrix generator
│   │   ├── generate_starter_dataset.py             # Starter dataset synthesis and augmentation script
│   │   └── results/                                # Training run outputs, loss curves, confusion matrices, and metrics
│   │       ├── metrics.txt                         # Tabulated numerical evaluation metrics
│   │       ├── training_results.png                # Combined training loss and validation metric plots
│   │       ├── confusion_matrix.png                # 7-Class confusion matrix visualization
│   │       └── train_run/                          # Ultralytics training run artifacts (weights, curves, CSV)
│   │
│   └── utils/                                      # Helper utility modules
│       ├── __init__.py                             # Utils package exports
│       ├── file_handler.py                         # Secure file upload validation, extension checking & saving
│       ├── logger.py                               # Structured console and file logging configuration
│       └── response.py                             # Standardized REST JSON response envelope formatters
│
├── database/                                       # Relational database persistence
│   └── defect_detection.db                         # Production SQLite database storing inspections & defect logs
│
├── deployment/                                     # Containerization and production deployment configurations
│   ├── Dockerfile                                  # Multi-stage container build definition for Linux/CUDA environments
│   ├── Procfile                                    # Process declaration for cloud deployment platforms (Railway/Heroku)
│   ├── gunicorn.conf.py                            # Production WSGI server multi-worker configuration
│   ├── Aptfile                                     # Linux OS-level dependencies (OpenCV system libraries)
│   ├── nixpacks.toml                               # Nixpacks cloud build configuration
│   ├── railpack.json                               # Railway buildpack manifest
│   ├── railway.json                                # Railway deployment lifecycle settings
│   └── app.py                                      # Production deployment entrypoint wrapper
│
├── documentation/                                  # Technical specifications, reports, and generators
│   ├── 3D_Printing_Defect_Detection_Technical_Report.docx  # Master Technical Monograph in Word (.docx) format
│   ├── 3D_Printing_Defect_Detection_Project_Metrics.xlsx   # Comprehensive project metrics & evaluation spreadsheet
│   ├── 3D_Printing_Defect_Inspection_Results_Output.xlsx   # Exported inspection records spreadsheet
│   ├── generate_master_technical_report.py         # Automated generator for master Word technical report
│   ├── export_inspection_results_excel.py          # Script exporting SQLite inspection logs to Excel
│   ├── generate_documentation_and_sheets.py        # Master batch document and spreadsheet generator
│   ├── folder_structure.md                         # Detailed project folder and file architecture documentation
│   ├── abstract.md                                 # Project abstract and executive summary
│   ├── objectives.md                               # Scientific and technical objectives
│   ├── methodology.md                              # End-to-end methodology and workflow
│   ├── system_architecture.md                      # System architecture, tiers, and data pipelines
│   ├── hardware_requirements.md                    # Hardware specifications and sensor setups
│   ├── software_requirements.md                    # Software dependencies and libraries
│   ├── results.md                                  # Experimental results, metrics, and comparisons
│   └── future_scope.md                             # Future research directions and edge deployment plans
│
└── frontend/                                       # Responsive client-side Web User Interface
    ├── index.html                                  # Central navigation portal and platform overview
    │
    ├── assets/                                     # Static media assets
    │   ├── icons/                                  # UI icon glyphs
    │   ├── images/                                 # Platform graphics and banner illustrations
    │   └── logos/                                  # Application logos
    │
    ├── css/                                        # Modular stylesheet system
    │   ├── style.css                               # Core typography, dark glassmorphism design system & variables
    │   ├── dashboard.css                           # Analytics dashboard grid layout, KPI cards & chart styling
    │   ├── inspection.css                          # Inspection viewports, canvas overlays, and result tables
    │   └── responsive.css                          # Mobile and tablet responsive breakpoint rules
    │
    ├── js/                                         # Client-side JavaScript controllers
    │   ├── app.js                                  # Global UI controls, theme toggling, and toast notification system
    │   ├── dashboard.js                            # Telemetry data fetching and dynamic KPI card updates
    │   ├── charts.js                               # Chart.js graphs (defect distribution, quality ratio, timeline)
    │   ├── image-inspection.js                     # Image upload, canvas bounding box rendering, and result badges
    │   ├── video-inspection.js                     # Video upload, frame-by-frame playback, and timestamp list
    │   ├── live-camera.js                          # Live MJPEG stream display, real-time alert polling & thresholding
    │   └── history.js                              # Inspection history table pagination, filtering, and export
    │
    └── pages/                                      # Modular HTML application views
        ├── dashboard.html                          # Real-time analytics and KPI monitoring dashboard
        ├── image-inspection.html                   # Static image upload and instant bounding box defect inspection
        ├── video-inspection.html                   # Recorded video time-lapse defect inspection and timeline review
        ├── live-inspection.html                    # Real-time webcam optical stream with live defect alerts
        ├── history.html                            # Historical audit trail table of all completed inspections
        └── model-performance.html                  # Deep learning evaluation metrics, confusion matrix & loss curves
```
