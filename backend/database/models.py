"""
SQLAlchemy ORM models for Inspection records and Individual Defect Detections.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from backend.database.database import Base


class Inspection(Base):
    """
    Master inspection record representing an image, video, or live frame analysis.
    """
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_type = Column(String(20), nullable=False, index=True)  # 'image', 'video', 'live'
    original_filename = Column(String(255), nullable=True)
    result_filename = Column(String(255), nullable=True)
    defect_type = Column(String(100), nullable=True, index=True)  # Dominant defect or summary
    confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    status = Column(String(20), nullable=False, default="GOOD", index=True)  # 'GOOD', 'DEFECT'
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    processing_time = Column(Float, nullable=True)  # In milliseconds or seconds
    source = Column(String(100), nullable=True)  # e.g., 'Web Upload', 'Camera Stream 0'
    notes = Column(Text, nullable=True)

    # Relationships
    detections = relationship("Detection", back_populates="inspection", cascade="all, delete-orphan", lazy="joined")

    def to_dict(self, include_detections: bool = True):
        """Serialize Inspection record to dictionary."""
        data = {
            "id": self.id,
            "inspection_type": self.inspection_type,
            "original_filename": self.original_filename,
            "result_filename": self.result_filename,
            "defect_type": self.defect_type,
            "confidence": round(self.confidence, 4) if self.confidence is not None else 0.0,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "processing_time": round(self.processing_time, 2) if self.processing_time is not None else 0.0,
            "source": self.source,
            "notes": self.notes,
        }
        if include_detections:
            data["detections"] = [d.to_dict() for d in self.detections]
            data["detection_count"] = len(self.detections)
        return data


class Detection(Base):
    """
    Individual object detection bounding box within an inspection.
    """
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    class_name = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    inspection = relationship("Inspection", back_populates="detections")

    def to_dict(self):
        """Serialize Detection to dictionary."""
        return {
            "id": self.id,
            "inspection_id": self.inspection_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": {
                "x1": round(self.x1, 2),
                "y1": round(self.y1, 2),
                "x2": round(self.x2, 2),
                "y2": round(self.y2, 2),
            },
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
