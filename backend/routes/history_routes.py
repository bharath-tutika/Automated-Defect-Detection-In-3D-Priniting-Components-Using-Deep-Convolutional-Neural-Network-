"""
Inspection History API Routes.
Provides searchable, filterable, paginated access to past inspection records.
"""

from flask import Blueprint, request, jsonify

from backend.database.database import get_db_session
from backend.database.crud import (
    list_inspections,
    get_inspection_by_id,
    delete_inspection,
)
from backend.utils.response import api_success, api_error
from backend.utils.logger import app_logger

history_bp = Blueprint("history_bp", __name__, url_prefix="/api/history")


@history_bp.route("", methods=["GET"])
def get_history():
    """
    Retrieve paginated inspection history with optional search and filters.
    Query params:
    - page (int, default 1)
    - per_page (int, default 10)
    - search (str)
    - type (str: image, video, live)
    - status (str: GOOD, DEFECT)
    - defect (str)
    """
    try:
        page = request.args.get("page", default=1, type=int)
        per_page = min(request.args.get("per_page", default=10, type=int), 100)
        search = request.args.get("search", default=None, type=str)
        inspection_type = request.args.get("type", default=None, type=str)
        status = request.args.get("status", default=None, type=str)
        defect_type = request.args.get("defect", default=None, type=str)

        with get_db_session() as session:
            records, total_count, total_pages = list_inspections(
                session=session,
                page=page,
                per_page=per_page,
                search=search,
                inspection_type=inspection_type,
                status=status,
                defect_type=defect_type,
            )
            items = [record.to_dict(include_detections=True) for record in records]

        return api_success(
            data={
                "items": items,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_items": total_count,
                    "total_pages": total_pages,
                },
            },
            message=f"Retrieved {len(items)} inspection records.",
        )
    except Exception as e:
        app_logger.error(f"Error fetching history: {e}", exc_info=True)
        return api_error(f"Failed to retrieve history: {str(e)}", status_code=500)


@history_bp.route("/<int:inspection_id>", methods=["GET"])
def get_inspection_detail(inspection_id: int):
    """
    Retrieve single inspection record with all detection coordinates.
    """
    try:
        with get_db_session() as session:
            record = get_inspection_by_id(session, inspection_id)
            if not record:
                return api_error(f"Inspection record #{inspection_id} not found.", status_code=404)
            data = record.to_dict(include_detections=True)

        return api_success(data=data, message=f"Inspection #{inspection_id} retrieved.")
    except Exception as e:
        app_logger.error(f"Error fetching inspection #{inspection_id}: {e}")
        return api_error(f"Error retrieving record: {str(e)}", status_code=500)


@history_bp.route("/<int:inspection_id>", methods=["DELETE"])
def delete_inspection_endpoint(inspection_id: int):
    """
    Delete an inspection record by ID.
    """
    try:
        with get_db_session() as session:
            success = delete_inspection(session, inspection_id)
            if not success:
                return api_error(f"Inspection record #{inspection_id} not found.", status_code=404)

        return api_success(message=f"Inspection #{inspection_id} deleted successfully.")
    except Exception as e:
        app_logger.error(f"Error deleting inspection #{inspection_id}: {e}")
        return api_error(f"Failed to delete record: {str(e)}", status_code=500)


@history_bp.route("/export-excel", methods=["GET"])
def export_excel_endpoint():
    """
    Generate and download the complete or filtered Excel inspection results output sheet.
    Supports ?id=123 (single inspection) or ?search=...&type=...&status=...&defect=... (filtered export).
    """
    try:
        from flask import send_file, request
        from backend.utils.export_excel import (
            generate_master_inspection_excel,
            generate_single_inspection_excel,
            get_export_filename,
        )

        # Check if single inspection requested via query param
        target_id = request.args.get("id", type=int)
        if target_id:
            out_path = generate_single_inspection_excel(target_id)
            filename = out_path.name
        else:
            filters = {
                "search": request.args.get("search", ""),
                "type": request.args.get("type", "all"),
                "status": request.args.get("status", "ALL"),
                "defect": request.args.get("defect", "all"),
            }
            out_path = generate_master_inspection_excel(filters=filters)
            filename = out_path.name

        return send_file(
            str(out_path),
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        app_logger.error(f"Error generating Excel export: {e}", exc_info=True)
        return api_error(f"Failed to export Excel: {str(e)}", status_code=500)


@history_bp.route("/export-excel/<int:inspection_id>", methods=["GET"])
def export_single_excel_endpoint(inspection_id: int):
    """
    Generate and download an Excel report for a specific single inspection record.
    """
    try:
        from flask import send_file
        from backend.utils.export_excel import generate_single_inspection_excel

        out_path = generate_single_inspection_excel(inspection_id)
        filename = f"Inspection_Report_#{inspection_id}.xlsx"

        return send_file(
            str(out_path),
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ValueError as ve:
        return api_error(str(ve), status_code=404)
    except Exception as e:
        app_logger.error(f"Error exporting single inspection #{inspection_id} Excel: {e}", exc_info=True)
        return api_error(f"Failed to export Excel: {str(e)}", status_code=500)


