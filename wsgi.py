"""
WSGI entry point for Gunicorn, uWSGI, and production web servers.
"""

from app import app, application

if __name__ == "__main__":
    app.run()
