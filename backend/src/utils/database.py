# Database Connection and Session Management
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator
import os
from contextlib import contextmanager
from pathlib import Path

# Database URL from environment or default to SQLite

# Get absolute path to database file with fallback handling
def get_database_url():
    """Get database URL with proper fallback handling for production environments"""
    # Check if DATABASE_URL is explicitly set
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    
    # Try to use the preferred data directory
    try:
        backend_dir = Path(__file__).parent.parent.parent
        data_dir = backend_dir.parent / "data"
        db_path = data_dir / "codeflowops.db"
        
        # Try to create directory
        data_dir.mkdir(exist_ok=True)
        
        # Test if we can write to the directory
        test_file = data_dir / ".test_write"
        test_file.touch()
        test_file.unlink()
        
        return f"sqlite:///{str(db_path)}"
        
    except (PermissionError, OSError) as e:
        # Fallback to tmp directory or current directory
        import tempfile
        try:
            # Try temp directory
            temp_dir = Path(tempfile.gettempdir()) / "codeflowops"
            temp_dir.mkdir(exist_ok=True)
            temp_db_path = temp_dir / "codeflowops.db"
            return f"sqlite:///{str(temp_db_path)}"
        except:
            # Final fallback to current directory
            current_db_path = Path.cwd() / "codeflowops.db"
            return f"sqlite:///{str(current_db_path)}"

DATABASE_URL = get_database_url()

# Create engine with SQLite-specific settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL debugging
    )
else:
    # PostgreSQL settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        echo=False  # Set to True for SQL debugging
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database
    """
    from ..models.enhanced_models import Base as EnhancedBase
    
    EnhancedBase.metadata.create_all(bind=engine)

def init_database():
    """
    Initialize database with default data
    """
    create_tables()
    
    # Billing plans initialization removed (Stripe functionality removed)
    # Plans are now managed through environment configuration only
