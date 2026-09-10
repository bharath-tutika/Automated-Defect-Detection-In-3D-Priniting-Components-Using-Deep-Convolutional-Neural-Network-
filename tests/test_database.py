"""
Unit tests for SQLite database operations and CRUD layer.
"""

import unittest
from backend.database.database import init_db, get_db_session
from backend.database.models import Inspection, Detection
from backend.database.crud import (
    create_inspection_record,
    get_inspection_by_id,
    list_inspections,
    delete_inspection,
    get_dashboard_stats,
)


class TestDatabaseCRUD(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_create_and_get_inspection(self):
        """Test inserting a new inspection and querying it back."""
        with get_db_session() as session:
            record = create_inspection_record(
                session=session,
                inspection_type="image",
                status="DEFECT",
                original_filename="test_sample.jpg",
                result_filename="annotated_test_sample.jpg",
                defect_type="Stringing",
                confidence=0.885,
                processing_time=45.2,
                source="Unit Test",
                detections=[
                    {
                        "class_name": "Stringing",
                        "confidence": 0.885,
                        "bbox": {"x1": 10.0, "y1": 20.0, "x2": 100.0, "y2": 150.0},
                    }
                ],
            )
            rec_id = record.id
            self.assertIsNotNone(rec_id)

        # Retrieve
        with get_db_session() as session:
            retrieved = get_inspection_by_id(session, rec_id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.status, "DEFECT")
            self.assertEqual(retrieved.defect_type, "Stringing")
            self.assertEqual(len(retrieved.detections), 1)
            self.assertEqual(retrieved.detections[0].class_name, "Stringing")

    def test_list_inspections_pagination(self):
        """Test listing inspections with pagination and filters."""
        with get_db_session() as session:
            items, total, pages = list_inspections(session, page=1, per_page=5)
            self.assertIsInstance(items, list)
            self.assertGreaterEqual(total, 1)
            self.assertGreaterEqual(pages, 1)

    def test_dashboard_stats(self):
        """Verify dashboard KPI metrics calculation."""
        with get_db_session() as session:
            stats = get_dashboard_stats(session)
            self.assertIn("total_inspections", stats)
            self.assertIn("good_prints", stats)
            self.assertIn("defects_detected", stats)
            self.assertIn("defect_rate", stats)
            self.assertIsInstance(stats["defect_rate"], float)

    def test_delete_inspection(self):
        """Test deleting an inspection record."""
        with get_db_session() as session:
            rec = create_inspection_record(
                session=session,
                inspection_type="live",
                status="GOOD",
                original_filename="to_delete.jpg",
            )
            del_id = rec.id

        with get_db_session() as session:
            deleted = delete_inspection(session, del_id)
            self.assertTrue(deleted)

        with get_db_session() as session:
            check = get_inspection_by_id(session, del_id)
            self.assertIsNone(check)


if __name__ == "__main__":
    unittest.main()
