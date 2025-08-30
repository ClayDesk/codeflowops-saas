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

# In-memory fallback storage
_memory_sessions = {}

class SessionStorage:
    def __init__(self, db_path: str = "data/codeflowops.db"):
        # Ensure absolute path and create directory if needed
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.getcwd(), db_path)
        
        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = db_path
        self.use_memory_fallback = False
        print(f"📁 Session storage database path: {self.db_path}")
        self.init_tables()
    
    def init_tables(self):
        """Initialize session tables if they don't exist"""
        try:
            print(f"🗃️ Initializing session tables at: {self.db_path}")
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
                print("✅ Session tables initialized successfully")
        except Exception as e:
            print(f"❌ Could not initialize session tables: {e}")
            print("🔄 Falling back to in-memory session storage")
            self.use_memory_fallback = True
    
    def set(self, session_id: str, user_data: Dict[str, Any], expires_in_hours: int = 24):
        """Store session data"""
        if self.use_memory_fallback:
            print(f"💾 Storing session {session_id} in memory: {user_data}")
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            _memory_sessions[session_id] = {
                "data": user_data,
                "expires_at": expires_at
            }
            print(f"✅ Session {session_id} stored in memory")
            return True
            
        try:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
            user_data_json = json.dumps(user_data)
            
            print(f"💾 Storing session {session_id} with data: {user_data}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO github_sessions 
                    (session_id, user_data, expires_at)
                    VALUES (?, ?, ?)
                """, (session_id, user_data_json, expires_at))
                conn.commit()
                print(f"✅ Session {session_id} stored successfully")
                return True
        except Exception as e:
            print(f"❌ Error storing session {session_id}: {e}")
            print("🔄 Falling back to memory storage")
            self.use_memory_fallback = True
            return self.set(session_id, user_data, expires_in_hours)
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        if self.use_memory_fallback:
            print(f"🔍 Looking for session {session_id} in memory")
            if session_id in _memory_sessions:
                session_info = _memory_sessions[session_id]
                if datetime.now() > session_info["expires_at"]:
                    print(f"⏰ Session {session_id} expired, deleting from memory")
                    del _memory_sessions[session_id]
                    return None
                print(f"✅ Session {session_id} found in memory: {session_info['data']}")
                return session_info["data"]
            else:
                print(f"❌ Session {session_id} not found in memory")
                return None
                
        try:
            print(f"🔍 Looking for session: {session_id}")
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
                        print(f"⏰ Session {session_id} expired, deleting")
                        self.delete(session_id)
                        return None
                    
                    session_data = json.loads(user_data_json)
                    print(f"✅ Session {session_id} found with data: {session_data}")
                    return session_data
                else:
                    print(f"❌ Session {session_id} not found in database")
                    return None
        except Exception as e:
            print(f"❌ Error retrieving session {session_id}: {e}")
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
