"""
Main Flask Application Factory and Web Server.
Serves both REST API endpoints and the frontend client interface.
"""

from pathlib import Path
from flask import Flask, send_from_directory, jsonify, render_template_string
from flask_cors import CORS

from config import (
    BASE_DIR,
    SECRET_KEY,
    MAX_UPLOAD_SIZE,
    UPLOAD_FOLDER,
    RESULT_FOLDER,
    TRAINING_RESULTS_DIR,
)
from backend.database.database import init_db
from backend.routes.image_routes import image_bp
from backend.routes.video_routes import video_bp
from backend.routes.camera_routes import camera_bp
from backend.routes.history_routes import history_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.utils.logger import app_logger


def create_app() -> Flask:
    """Create and configure Flask application instance."""
    frontend_dir = BASE_DIR / "frontend"

    app = Flask(
        __name__,
        static_folder=str(frontend_dir),
        static_url_path="",
    )

    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE

    # Enable CORS for flexible integration
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize Database Tables
    with app.app_context():
        init_db()

    # Register API Blueprints
    app.register_blueprint(image_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(dashboard_bp)

    # ----------------------------------------------------
    # Frontend Routes & Static Serving
    # ----------------------------------------------------

    @app.route("/")
    def index():
        """Serve root index page."""
        return send_from_directory(str(frontend_dir), "index.html")

    @app.route("/pages/<path:filename>")
    def serve_pages(filename: str):
        """Serve sub-pages."""
        pages_dir = frontend_dir / "pages"
        return send_from_directory(str(pages_dir), filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename: str):
        """Serve stylesheet files."""
        css_dir = frontend_dir / "css"
        return send_from_directory(str(css_dir), filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename: str):
        """Serve JavaScript files."""
        js_dir = frontend_dir / "js"
        return send_from_directory(str(js_dir), filename)

    @app.route("/assets/<path:filename>")
    def serve_assets(filename: str):
        """Serve image and icon assets."""
        assets_dir = frontend_dir / "assets"
        return send_from_directory(str(assets_dir), filename)

    @app.route("/uploads/<path:filename>")
    def serve_uploads(filename: str):
        """Serve uploaded media files securely."""
        return send_from_directory(str(UPLOAD_FOLDER), filename)

    @app.route("/results/<path:filename>")
    def serve_results(filename: str):
        """Serve annotated result images and videos."""
        return send_from_directory(str(RESULT_FOLDER), filename)

    @app.route("/training/results/<path:filename>")
    def serve_training_results(filename: str):
        """Serve training evaluation plots and confusion matrix images."""
        return send_from_directory(str(TRAINING_RESULTS_DIR), filename)

    # ----------------------------------------------------
    # Error Handlers
    # ----------------------------------------------------

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"success": False, "error": "Requested resource was not found."}), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        return jsonify({
            "success": False,
            "error": f"File exceeds maximum upload size limit of {max_mb} MB."
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        app_logger.error(f"Internal server error: {error}")
        return jsonify({"success": False, "error": "Internal server error occurred."}), 500

    return app


if __name__ == "__main__":
    from config import HOST, PORT, DEBUG
    flask_app = create_app()
    flask_app.run(host=HOST, port=PORT, debug=DEBUG)
