# Software Requirements

## Operating System Compatibility
- **Windows**: Windows 10 / Windows 11 (64-bit)
- **Linux**: Ubuntu 20.04 LTS / 22.04 LTS / Debian 11+
- **macOS**: macOS 12 (Monterey) or higher (Apple Silicon / Intel)

## Core Software Dependencies
- **Python**: Version 3.11+
- **Package Manager**: `pip` or `uv`
- **Web Browser**: Google Chrome, Mozilla Firefox, Microsoft Edge, Safari (with modern HTML5 & JavaScript support)

## Key Python Packages
| Package | Version | Purpose |
| :--- | :--- | :--- |
| `Flask` | $\ge 3.0.0$ | Core web framework & REST API server |
| `Flask-Cors` | $\ge 4.0.0$ | Cross-Origin Resource Sharing |
| `opencv-python` | $\ge 4.8.0$ | Video I/O, camera streaming, bounding box rendering |
| `ultralytics` | $\ge 8.1.0$ | YOLO object detection engine & training framework |
| `torch` | $\ge 2.0.0$ | Deep learning tensor computation & CUDA acceleration |
| `torchvision` | $\ge 0.15.0$ | Computer vision datasets and transformations |
| `SQLAlchemy` | $\ge 2.0.0$ | ORM database abstraction & SQLite session management |
| `Pillow` | $\ge 10.0.0$ | Image format validation and manipulation |
| `numpy` | $\ge 1.24.0$ | Numerical array operations and buffer decoding |
| `matplotlib` | $\ge 3.7.0$ | Plotting confusion matrix and training curves |
