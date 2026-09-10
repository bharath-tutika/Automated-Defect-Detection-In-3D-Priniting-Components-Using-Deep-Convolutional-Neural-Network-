"""
Routes package initialization.
"""

from backend.routes.image_routes import image_bp
from backend.routes.video_routes import video_bp
from backend.routes.camera_routes import camera_bp
from backend.routes.history_routes import history_bp
from backend.routes.dashboard_routes import dashboard_bp

__all__ = [
    "image_bp",
    "video_bp",
    "camera_bp",
    "history_bp",
    "dashboard_bp",
]
