from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from config.settings import settings
from app.database.models import Base
import logging

logger = logging.getLogger(__name__)

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for DO Apps
    echo=settings.LOG_LEVEL == "DEBUG",
    connect_args={
        "connect_timeout": 10,
        "options": "-c default_transaction_isolation=read_committed"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def drop_db():
    """Drop all tables (use with caution!)"""
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise

def reset_db():
    """Reset database (drop and recreate)"""
    drop_db()
    init_db()
