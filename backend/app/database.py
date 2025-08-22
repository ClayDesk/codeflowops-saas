"""
Database configuration and session management - Simplified for development
"""

from typing import Generator
from .models.deployment import MockDB


def get_db() -> Generator[MockDB, None, None]:
    """
    Get database session - using mock implementation for development
    """
    db = MockDB()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables - no-op for mock implementation
    """
    pass
