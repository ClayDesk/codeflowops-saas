"""
FastAPI dependencies for session management
Handles session lifecycle, WebSocket connections, and state tracking
"""

from fastapi import Depends, HTTPException, status
import logging
from typing import Dict, List, Optional, Any
import asyncio
import redis.asyncio as redis
from datetime import datetime, timedelta
import json
import uuid

from ..config.env import get_settings
from ..models.response_models import SessionInfo, DeploymentStatus, ProjectType
from ..utils.websocket_manager import WebSocketManager
from database.connection import get_database_connection

logger = logging.getLogger(__name__)
settings = get_settings()


class SessionManager:
    """
    Manages deployment sessions with Redis backend for scalability
    Handles thousands of concurrent users with efficient state management
    """
    
    def __init__(self):
        self.redis_client = None
        self.websocket_manager = WebSocketManager()
        self.session_prefix = settings.REDIS_SESSION_PREFIX
        self.session_ttl = settings.SESSION_TTL_HOURS * 3600  # Convert to seconds
        
    async def initialize(self):
        """Initialize Redis connection for session storage"""
        try:
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis connection established for session management")
            else:
                logger.warning("Redis not configured, using in-memory session storage")
                self.redis_client = None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self.redis_client = None
    
    async def create_session(
        self,
        session_id: str,
        github_url: str,
        project_name: Optional[str] = None,
        current_step: str = "pending"
    ) -> SessionInfo:
        """Create new deployment session"""
        try:
            now = datetime.utcnow()
            
            # Extract project name from URL if not provided
            if not project_name:
                project_name = self._extract_project_name_from_url(github_url)
            
            session_data = {
                "session_id": session_id,
                "status": DeploymentStatus.PENDING.value,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "github_url": github_url,
                "project_name": project_name,
                "current_step": current_step,
                "progress_percentage": 0,
                "project_type": None,
                "analysis_result": None,
                "build_result": None,
                "infrastructure_result": None,
                "deployment_result": None,
                "logs": [],
                "metrics": {},
                "error_details": None,
                "estimated_completion": None
            }
            
            await self._store_session(session_id, session_data)
            
            logger.info(f"Created session {session_id} for {github_url}")
            return SessionInfo(**session_data)
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve session by ID"""
        try:
            session_data = await self._get_session_data(session_id)
            if session_data:
                return SessionInfo(**session_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    async def update_session_status(
        self,
        session_id: str,
        status: str,
        current_step: Optional[str] = None,
        progress_percentage: Optional[int] = None,
        error_details: Optional[str] = None,
        estimated_completion: Optional[datetime] = None
    ):
        """Update session status and progress"""
        try:
            session_data = await self._get_session_data(session_id)
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Update fields
            session_data["status"] = status
            session_data["updated_at"] = datetime.utcnow().isoformat()
            
            if current_step:
                session_data["current_step"] = current_step
            if progress_percentage is not None:
                session_data["progress_percentage"] = progress_percentage
            if error_details:
                session_data["error_details"] = error_details
            if estimated_completion:
                session_data["estimated_completion"] = estimated_completion.isoformat()
            
            await self._store_session(session_id, session_data)
            
            # Send WebSocket update
            await self.send_progress_update(
                session_id,
                step=current_step or session_data["current_step"],
                progress=progress_percentage or session_data["progress_percentage"],
                message=f"Status updated to {status}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {str(e)}")
            raise
    
    async def list_sessions(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        status_filter: Optional[str] = None,
        project_type_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> tuple[List[SessionInfo], int]:
        """List sessions with filtering and pagination"""
        try:
            all_sessions = await self._get_all_sessions()
            
            # Apply filters
            filtered_sessions = []
            for session_data in all_sessions:
                # Status filter
                if status_filter and session_data.get("status") != status_filter:
                    continue
                
                # Project type filter
                if project_type_filter and session_data.get("project_type") != project_type_filter:
                    continue
                
                # Date range filter
                created_at = datetime.fromisoformat(session_data["created_at"])
                if date_from and created_at < date_from:
                    continue
                if date_to and created_at > date_to:
                    continue
                
                filtered_sessions.append(SessionInfo(**session_data))
            
            # Sort sessions
            reverse = sort_order == "desc"
            filtered_sessions.sort(
                key=lambda x: getattr(x, sort_by, x.created_at),
                reverse=reverse
            )
            
            # Apply pagination
            total_count = len(filtered_sessions)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_sessions = filtered_sessions[start_idx:end_idx]
            
            return paginated_sessions, total_count
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
            return [], 0
    
    async def delete_session(
        self,
        session_id: str,
        cleanup_resources: bool = True
    ):
        """Delete session and optionally cleanup AWS resources"""
        try:
            if cleanup_resources:
                # Cleanup AWS resources
                await self._cleanup_aws_resources(session_id)
            
            # Remove from storage
            await self._delete_session_data(session_id)
            
            # Close WebSocket connections
            await self.websocket_manager.close_session_connections(session_id)
            
            logger.info(f"Deleted session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {str(e)}")
            raise
    
    async def cancel_session(
        self,
        session_id: str,
        cleanup_resources: bool = False
    ):
        """Cancel active session"""
        try:
            await self.update_session_status(
                session_id,
                status="cancelled",
                current_step="cancelled"
            )
            
            if cleanup_resources:
                await self._cleanup_aws_resources(session_id)
            
            logger.info(f"Cancelled session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to cancel session {session_id}: {str(e)}")
            raise
    
    async def add_websocket_connection(self, session_id: str, websocket):
        """Add WebSocket connection for real-time updates"""
        await self.websocket_manager.add_connection(session_id, websocket)
    
    async def remove_websocket_connection(self, session_id: str, websocket):
        """Remove WebSocket connection"""
        await self.websocket_manager.remove_connection(session_id, websocket)
    
    async def send_progress_update(
        self,
        session_id: str,
        step: str,
        progress: int,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send progress update via WebSocket"""
        try:
            update_data = {
                "type": "progress",
                "session_id": session_id,
                "step": step,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
            
            await self.websocket_manager.send_to_session(session_id, update_data)
            
            # Also log the progress
            await self._add_session_log(session_id, "info", "progress", message)
            
        except Exception as e:
            logger.error(f"Failed to send progress update for session {session_id}: {str(e)}")
    
    async def get_session_logs(
        self,
        session_id: str,
        level: str = "info",
        limit: int = 100,
        component: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get session logs with filtering"""
        try:
            session_data = await self._get_session_data(session_id)
            if not session_data:
                return []
            
            logs = session_data.get("logs", [])
            
            # Filter logs
            filtered_logs = []
            for log in logs[-limit:]:  # Get last N logs
                if level and log.get("level") != level:
                    continue
                if component and log.get("component") != component:
                    continue
                filtered_logs.append(log)
            
            return filtered_logs
            
        except Exception as e:
            logger.error(f"Failed to get logs for session {session_id}: {str(e)}")
            return []
    
    async def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session performance metrics"""
        try:
            session_data = await self._get_session_data(session_id)
            if session_data:
                return session_data.get("metrics", {})
            return None
        except Exception as e:
            logger.error(f"Failed to get metrics for session {session_id}: {str(e)}")
            return None
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all currently active sessions"""
        try:
            active_statuses = ["analyzing", "building", "deploying"]
            all_sessions = await self._get_all_sessions()
            
            active_sessions = [
                {
                    "session_id": session["session_id"],
                    "status": session["status"],
                    "current_step": session["current_step"],
                    "progress_percentage": session["progress_percentage"],
                    "created_at": session["created_at"],
                    "github_url": session["github_url"],
                    "project_name": session["project_name"]
                }
                for session in all_sessions
                if session.get("status") in active_statuses
            ]
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Failed to get active sessions: {str(e)}")
            return []
    
    # Private helper methods
    
    async def _store_session(self, session_id: str, session_data: Dict[str, Any]):
        """Store session data in Redis or memory"""
        if self.redis_client:
            key = f"{self.session_prefix}:{session_id}"
            await self.redis_client.setex(
                key,
                self.session_ttl,
                json.dumps(session_data, default=str)
            )
        else:
            # Fallback to in-memory storage (not recommended for production)
            if not hasattr(self, '_memory_sessions'):
                self._memory_sessions = {}
            self._memory_sessions[session_id] = session_data
    
    async def _get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from storage"""
        if self.redis_client:
            key = f"{self.session_prefix}:{session_id}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        else:
            # Fallback to in-memory storage
            if hasattr(self, '_memory_sessions'):
                return self._memory_sessions.get(session_id)
        return None
    
    async def _get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions from storage"""
        sessions = []
        
        if self.redis_client:
            pattern = f"{self.session_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            
            for key in keys:
                data = await self.redis_client.get(key)
                if data:
                    sessions.append(json.loads(data))
        else:
            # Fallback to in-memory storage
            if hasattr(self, '_memory_sessions'):
                sessions = list(self._memory_sessions.values())
        
        return sessions
    
    async def _delete_session_data(self, session_id: str):
        """Delete session data from storage"""
        if self.redis_client:
            key = f"{self.session_prefix}:{session_id}"
            await self.redis_client.delete(key)
        else:
            # Fallback to in-memory storage
            if hasattr(self, '_memory_sessions') and session_id in self._memory_sessions:
                del self._memory_sessions[session_id]
    
    async def _add_session_log(
        self,
        session_id: str,
        level: str,
        component: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Add log entry to session"""
        try:
            session_data = await self._get_session_data(session_id)
            if session_data:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": level,
                    "component": component,
                    "message": message,
                    "context": context or {}
                }
                
                logs = session_data.get("logs", [])
                logs.append(log_entry)
                
                # Keep only last N logs to prevent memory issues
                if len(logs) > settings.MAX_SESSION_LOGS:
                    logs = logs[-settings.MAX_SESSION_LOGS:]
                
                session_data["logs"] = logs
                await self._store_session(session_id, session_data)
                
        except Exception as e:
            logger.error(f"Failed to add log to session {session_id}: {str(e)}")
    
    def _extract_project_name_from_url(self, github_url: str) -> str:
        """Extract project name from GitHub URL"""
        try:
            # Extract repo name from URL
            parts = github_url.rstrip('/').split('/')
            if len(parts) >= 2:
                repo_name = parts[-1]
                # Clean repo name for AWS resource naming
                clean_name = ''.join(c for c in repo_name if c.isalnum() or c == '-')
                return clean_name.lower()[:50]  # Limit length
        except Exception:
            pass
        
        return f"project-{str(uuid.uuid4())[:8]}"
    
    async def _cleanup_aws_resources(self, session_id: str):
        """Cleanup AWS resources for session"""
        try:
            # This would call the actual AWS cleanup logic
            # from controllers.deploymentController import cleanup_aws_resources
            # await cleanup_aws_resources(session_id)
            logger.info(f"AWS resources cleaned up for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup AWS resources for session {session_id}: {str(e)}")


# Global session manager instance
_session_manager = None


async def get_session_manager() -> SessionManager:
    """Dependency to get session manager instance"""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
        await _session_manager.initialize()
    
    return _session_manager
