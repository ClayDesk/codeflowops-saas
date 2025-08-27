"""
Simple Session Storage for GitHub OAuth
Database-backed session storage to replace in-memory sessions
"""
import sqlite3
import json
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import os

class SessionStorage:
    def __init__(self, db_path: str = "data/codeflowops.db"):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Initialize session tables if they don't exist"""
        try:
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
        except Exception as e:
            print(f"Warning: Could not initialize session tables: {e}")
    
    def set(self, session_id: str, user_data: Dict[str, Any], expires_in_hours: int = 24):
        """Store session data"""
        try:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            user_data_json = json.dumps(user_data)
            
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
                    if datetime.now() > expires_at:
                        self.delete(session_id)
                        return None
                    
                    return json.loads(user_data_json)
                return None
        except Exception as e:
            print(f"Error retrieving session: {e}")
            return None
    
    def delete(self, session_id: str):
        """Delete session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM github_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def cleanup_expired(self):
        """Clean up expired sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM github_sessions WHERE expires_at < ?", (datetime.now(),))
                conn.commit()
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")

# Global session storage instance
session_storage = SessionStorage()
