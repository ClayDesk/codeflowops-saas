"""
Simple Session Storage for GitHub OAuth
Database-backed session storage to replace in-memory sessions
"""
import os
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

# Try to use the existing centralized database
try:
    from .database import get_db_session
    USE_CENTRAL_DB = True
    print("Using centralized PostgreSQL database for session storage")
except ImportError:
    # Fallback to SQLite if centralized DB not available
    import sqlite3
    import json
    USE_CENTRAL_DB = False
    print("Falling back to SQLite for session storage")

if USE_CENTRAL_DB:
    # Use the centralized PostgreSQL database
    from sqlalchemy import Column, String, DateTime, Text
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class GitHubSession(Base):
        __tablename__ = "github_sessions"
        
        session_id = Column(String(255), primary_key=True)
        user_data = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        expires_at = Column(DateTime, nullable=False)
        
    class SessionStorage:
        def __init__(self):
            self._initialized = False
        
        def _ensure_initialized(self):
            """Lazy initialization to avoid import-time database connections"""
            if self._initialized:
                return
            self.init_tables()
            self._initialized = True
        
        def init_tables(self):
            """Initialize session tables if they don't exist"""
            try:
                from .database import engine
                Base.metadata.create_all(bind=engine)
                print("Session storage initialized in centralized database")
            except Exception as e:
                print(f"Warning: Could not initialize session tables in centralized DB: {e}")
                # Don't fail on import, just print warning
        
        def set(self, session_id: str, user_data: Dict[str, Any], expires_in_hours: int = 24):
            """Store session data"""
            self._ensure_initialized()
            try:
                import json
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
                user_data_json = json.dumps(user_data, default=str)
                
                with get_db_session() as db:
                    # Delete existing session if any
                    db.query(GitHubSession).filter(GitHubSession.session_id == session_id).delete()
                    
                    # Create new session
                    session = GitHubSession(
                        session_id=session_id,
                        user_data=user_data_json,
                        expires_at=expires_at
                    )
                    db.add(session)
                    db.commit()
                    return True
            except Exception as e:
                print(f"Error storing session in centralized DB: {e}")
                return False
        
        def get(self, session_id: str) -> Optional[Dict[str, Any]]:
            """Retrieve session data"""
            self._ensure_initialized()
            try:
                import json
                with get_db_session() as db:
                    session = db.query(GitHubSession).filter(GitHubSession.session_id == session_id).first()
                    
                    if session:
                        # Check if session has expired
                        if datetime.utcnow() > session.expires_at:
                            self.delete(session_id)
                            return None
                        
                        return json.loads(session.user_data)
                    return None
            except Exception as e:
                print(f"Error retrieving session from centralized DB: {e}")
                return None
        
        def delete(self, session_id: str):
            """Delete session"""
            self._ensure_initialized()
            try:
                with get_db_session() as db:
                    db.query(GitHubSession).filter(GitHubSession.session_id == session_id).delete()
                    db.commit()
                    return True
            except Exception as e:
                print(f"Error deleting session from centralized DB: {e}")
                return False

else:
    # Fallback SQLite implementation
    import sqlite3
    import json
    
    class SessionStorage:
        def __init__(self, db_path: str = None):
            self._initialized = False
            if db_path is None:
                # Use environment variable or default to a writable location
                self.db_path = os.getenv("SESSION_DB_PATH", "/tmp/codeflowops_sessions.db")
                # Ensure the directory exists
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            else:
                self.db_path = db_path
        
        def _ensure_initialized(self):
            """Lazy initialization to avoid import-time database connections"""
            if self._initialized:
                return
            self.init_tables()
            self._initialized = True
        
        def init_tables(self):
            """Initialize session tables if they don't exist"""
            try:
                print(f"Initializing session storage at: {self.db_path}")
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS github_sessions (
                            session_id TEXT PRIMARY KEY,
                            user_data TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP NOT NULL
                        )
                    """)
                    conn.commit()
                    print(f"Session storage initialized successfully at: {self.db_path}")
            except Exception as e:
                print(f"Warning: Could not initialize session tables at {self.db_path}: {e}")
                # Don't fail on import, just print warning
        
        def set(self, session_id: str, user_data: Dict[str, Any], expires_in_hours: int = 24):
            """Store session data"""
            self._ensure_initialized()
            try:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
                user_data_json = json.dumps(user_data, default=str)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO github_sessions 
                        (session_id, user_data, expires_at)
                        VALUES (?, ?, ?)
                    """, (session_id, user_data_json, expires_at))
                    conn.commit()
                    return True
            except Exception as e:
                print(f"Error storing session: {e}")
                return False
        
        def get(self, session_id: str) -> Optional[Dict[str, Any]]:
            """Retrieve session data"""
            self._ensure_initialized()
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT user_data, expires_at FROM github_sessions 
                        WHERE session_id = ?
                    """, (session_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        user_data_json, expires_at_str = result
                        expires_at = datetime.fromisoformat(expires_at_str)
                        
                        # Check if session has expired
                        if datetime.utcnow() > expires_at:
                            self.delete(session_id)
                            return None
                        
                        return json.loads(user_data_json)
                    return None
            except Exception as e:
                print(f"Error retrieving session: {e}")
                return None
        
        def delete(self, session_id: str):
            """Delete session"""
            self._ensure_initialized()
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM github_sessions WHERE session_id = ?", (session_id,))
                    conn.commit()
                    return True
            except Exception as e:
                print(f"Error deleting session: {e}")
                return False

# Global session storage instance
session_storage = SessionStorage()
