"""
CRUD (Create, Read, Update, Delete) operations for the SQLite database.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from backend.database.models import Inspection, Detection
from backend.utils.logger import app_logger


def create_inspection_record(
    session: Session,
    inspection_type: str,
    status: str,
    original_filename: Optional[str] = None,
    result_filename: Optional[str] = None,
    defect_type: Optional[str] = None,
    confidence: Optional[float] = None,
    processing_time: Optional[float] = None,
    source: Optional[str] = None,
    notes: Optional[str] = None,
    detections: Optional[List[Dict[str, Any]]] = None,
) -> Inspection:
    """
    Create a new Inspection record and associated Detections in a single transaction.
    """
    inspection = Inspection(
        inspection_type=inspection_type,
        status=status,
        original_filename=original_filename,
        result_filename=result_filename,
        defect_type=defect_type or ("Good Print" if status == "GOOD" else "Defect Detected"),
        confidence=confidence or 0.0,
        processing_time=processing_time or 0.0,
        source=source or "System",
        notes=notes,
        timestamp=datetime.utcnow(),
    )
    session.add(inspection)
    session.flush()  # Flush to generate inspection.id

    if detections:
        for det in detections:
            bbox = det.get("bbox", {})
            detection_record = Detection(
                inspection_id=inspection.id,
                class_name=det.get("class_name", "Defect"),
                confidence=det.get("confidence", 0.0),
                x1=bbox.get("x1", 0.0),
                y1=bbox.get("y1", 0.0),
                x2=bbox.get("x2", 0.0),
                y2=bbox.get("y2", 0.0),
                timestamp=datetime.utcnow(),
            )
            session.add(detection_record)

    session.flush()
    return inspection


def get_inspection_by_id(session: Session, inspection_id: int) -> Optional[Inspection]:
    """Retrieve an inspection record by its primary key ID."""
    return session.query(Inspection).filter(Inspection.id == inspection_id).first()


def list_inspections(
    session: Session,
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    inspection_type: Optional[str] = None,
    status: Optional[str] = None,
    defect_type: Optional[str] = None,
) -> Tuple[List[Inspection], int, int]:
    """
    Search and filter inspection records with pagination.
    Returns (items, total_count, total_pages).
    """
    query = session.query(Inspection)

    # Search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Inspection.original_filename.ilike(search_pattern),
                Inspection.result_filename.ilike(search_pattern),
                Inspection.defect_type.ilike(search_pattern),
                Inspection.source.ilike(search_pattern),
            )
        )

    # Specific filters
    if inspection_type and inspection_type.lower() != "all":
        query = query.filter(Inspection.inspection_type == inspection_type.lower())

    if status and status.upper() != "ALL":
        query = query.filter(Inspection.status == status.upper())

    if defect_type and defect_type.lower() != "all":
        query = query.filter(Inspection.defect_type.ilike(f"%{defect_type}%"))

    # Order newest first
    query = query.order_by(desc(Inspection.timestamp))

    total_count = query.count()
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()

    return items, total_count, total_pages


def delete_inspection(session: Session, inspection_id: int) -> bool:
    """Delete an inspection record and its detections."""
    record = session.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not record:
        return False
    session.delete(record)
    session.flush()
    return True


def get_dashboard_stats(session: Session) -> Dict[str, Any]:
    """
    Compute aggregate dashboard metrics:
    - Total Inspections
    - Good Prints
    - Defects Detected
    - Defect Rate (%)
    """
    total = session.query(func.count(Inspection.id)).scalar() or 0
    good_count = session.query(func.count(Inspection.id)).filter(Inspection.status == "GOOD").scalar() or 0
    defect_count = session.query(func.count(Inspection.id)).filter(Inspection.status == "DEFECT").scalar() or 0
    defect_rate = round((defect_count / total * 100), 1) if total > 0 else 0.0

    # Count by inspection type
    image_count = session.query(func.count(Inspection.id)).filter(Inspection.inspection_type == "image").scalar() or 0
    video_count = session.query(func.count(Inspection.id)).filter(Inspection.inspection_type == "video").scalar() or 0
    live_count = session.query(func.count(Inspection.id)).filter(Inspection.inspection_type == "live").scalar() or 0

    return {
        "total_inspections": total,
        "good_prints": good_count,
        "defects_detected": defect_count,
        "defect_rate": defect_rate,
        "by_type": {
            "image": image_count,
            "video": video_count,
            "live": live_count,
        },
    }


def get_dashboard_charts(session: Session) -> Dict[str, Any]:
    """
    Compute chart data:
    1. Defect distribution by class
    2. Status comparison (Good vs Defective)
    3. Activity timeline (last 7 days)
    """
    # 1. Defect distribution from Detections table
    defect_counts = (
        session.query(Detection.class_name, func.count(Detection.id))
        .group_by(Detection.class_name)
        .all()
    )
    defect_labels = [row[0] for row in defect_counts]
    defect_values = [row[1] for row in defect_counts]

    # 2. Good vs Defective
    good_count = session.query(func.count(Inspection.id)).filter(Inspection.status == "GOOD").scalar() or 0
    defect_count = session.query(func.count(Inspection.id)).filter(Inspection.status == "DEFECT").scalar() or 0

    # 3. Last 7 days timeline
    now = datetime.utcnow()
    days_labels = []
    daily_good = []
    daily_defect = []

    for i in range(6, -1, -1):
        day_date = (now - timedelta(days=i)).date()
        day_start = datetime.combine(day_date, datetime.min.time())
        day_end = datetime.combine(day_date, datetime.max.time())

        day_good = (
            session.query(func.count(Inspection.id))
            .filter(Inspection.timestamp >= day_start, Inspection.timestamp <= day_end, Inspection.status == "GOOD")
            .scalar()
            or 0
        )
        day_defect = (
            session.query(func.count(Inspection.id))
            .filter(Inspection.timestamp >= day_start, Inspection.timestamp <= day_end, Inspection.status == "DEFECT")
            .scalar()
            or 0
        )

        days_labels.append(day_date.strftime("%b %d"))
        daily_good.append(day_good)
        daily_defect.append(day_defect)

    return {
        "defect_distribution": {
            "labels": defect_labels,
            "data": defect_values,
        },
        "good_vs_defect": {
            "labels": ["Good Prints", "Defective Prints"],
            "data": [good_count, defect_count],
        },
        "timeline": {
            "labels": days_labels,
            "good_data": daily_good,
            "defect_data": daily_defect,
        },
    }
