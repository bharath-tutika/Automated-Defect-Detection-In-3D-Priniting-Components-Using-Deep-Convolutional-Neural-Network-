"""
Database connection and session factory using SQLAlchemy and SQLite.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

from config import DATABASE_PATH, SQLALCHEMY_DATABASE_URI
from backend.utils.logger import app_logger

# Ensure database directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Create engine with connect_args for SQLite multi-threading support
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionFactory)

Base = declarative_base()


def init_db() -> None:
    """Initialize database tables."""
    try:
        # Import models so they are registered with Base metadata
        import backend.database.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        app_logger.info(f"Database initialized successfully at {DATABASE_PATH}")
    except Exception as e:
        app_logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        raise


@contextmanager
def get_db_session():
    """
    Context manager for transactional database operations.
    Ensures rollback on error and proper session closing.
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        app_logger.error(f"Database session transaction failed: {e}")
        raise
    finally:
        session.close()
