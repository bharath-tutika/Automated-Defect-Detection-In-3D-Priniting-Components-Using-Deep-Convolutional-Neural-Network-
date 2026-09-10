"""
Standardized JSON response helper for Flask API routes.
"""

from typing import Any, Dict, Optional
from flask import jsonify, Response


def api_success(
    data: Optional[Dict[str, Any]] = None,
    message: str = "Operation successful",
    status_code: int = 200,
    **kwargs: Any
) -> tuple[Response, int]:
    """
    Format a standardized successful JSON response.
    """
    payload: Dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        payload["data"] = data

    # Merge additional top-level keyword arguments if provided
    for key, value in kwargs.items():
        payload[key] = value

    return jsonify(payload), status_code


def api_error(
    message: str = "An error occurred",
    status_code: int = 400,
    errors: Optional[Any] = None,
    **kwargs: Any
) -> tuple[Response, int]:
    """
    Format a standardized error JSON response.
    """
    payload: Dict[str, Any] = {
        "success": False,
        "error": message,
    }
    if errors is not None:
        payload["details"] = errors

    for key, value in kwargs.items():
        payload[key] = value

    return jsonify(payload), status_code
