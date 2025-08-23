# WebSocket Service for Real-time Deployment Monitoring
import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)

class WebSocketMessageType(Enum):
    """WebSocket message types"""
    DEPLOYMENT_STATUS = "deployment_status"
    DEPLOYMENT_PROGRESS = "deployment_progress"
    DEPLOYMENT_LOGS = "deployment_logs"
    DEPLOYMENT_ERROR = "deployment_error"
    DEPLOYMENT_COMPLETE = "deployment_complete"
    SYSTEM_STATUS = "system_status"
    HEARTBEAT = "heartbeat"

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Active connections by deployment ID
        self.deployment_connections: Dict[str, Set[WebSocket]] = {}
        # Active connections for system-wide updates
        self.system_connections: Set[WebSocket] = set()
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, deployment_id: Optional[str] = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Store connection metadata
        self.connection_metadata[websocket] = {
            "connected_at": datetime.utcnow(),
            "deployment_id": deployment_id,
            "last_ping": datetime.utcnow()
        }
        
        if deployment_id:
            # Add to deployment-specific connections
            if deployment_id not in self.deployment_connections:
                self.deployment_connections[deployment_id] = set()
            self.deployment_connections[deployment_id].add(websocket)
            logger.info(f"WebSocket connected for deployment {deployment_id}")
        else:
            # Add to system-wide connections
            self.system_connections.add(websocket)
            logger.info("WebSocket connected for system updates")
        
        # Send welcome message
        await self.send_message(websocket, {
            "type": WebSocketMessageType.SYSTEM_STATUS.value,
            "message": "Connected to Smart Deploy real-time monitoring",
            "timestamp": datetime.utcnow().isoformat(),
            "deployment_id": deployment_id
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        metadata = self.connection_metadata.get(websocket, {})
        deployment_id = metadata.get("deployment_id")
        
        if deployment_id and deployment_id in self.deployment_connections:
            self.deployment_connections[deployment_id].discard(websocket)
            if not self.deployment_connections[deployment_id]:
                del self.deployment_connections[deployment_id]
            logger.info(f"WebSocket disconnected from deployment {deployment_id}")
        
        self.system_connections.discard(websocket)
        self.connection_metadata.pop(websocket, None)
        logger.info("WebSocket disconnected")
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            # Remove the connection if it's broken
            self.disconnect(websocket)
    
    async def broadcast_to_deployment(self, deployment_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections monitoring a specific deployment"""
        if deployment_id not in self.deployment_connections:
            return
        
        # Add deployment ID to message
        message["deployment_id"] = deployment_id
        message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected_connections = []
        for websocket in self.deployment_connections[deployment_id].copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to deployment {deployment_id}: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)
    
    async def broadcast_system_wide(self, message: Dict[str, Any]):
        """Broadcast a message to all system-wide connections"""
        message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected_connections = []
        for websocket in self.system_connections.copy():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast system message: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)
    
    def get_connection_count(self, deployment_id: Optional[str] = None) -> int:
        """Get the number of active connections"""
        if deployment_id:
            return len(self.deployment_connections.get(deployment_id, set()))
        return len(self.system_connections)

class WebSocketService:
    """Service for handling real-time WebSocket communications"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.heartbeat_task = None
        self._heartbeat_started = False
    
    def _ensure_heartbeat_started(self):
        """Ensure heartbeat is started when event loop is available"""
        if not self._heartbeat_started:
            try:
                # Check if we have a running event loop
                loop = asyncio.get_running_loop()
                self._start_heartbeat_task()
                self._heartbeat_started = True
            except RuntimeError:
                # No event loop running, will start later
                pass
    
    def _start_heartbeat_task(self):
        """Start the heartbeat task to keep connections alive"""
        async def heartbeat_loop():
            while True:
                try:
                    await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                    await self.send_heartbeat()
                except Exception as e:
                    logger.error(f"Heartbeat error: {e}")
                    await asyncio.sleep(30)  # Continue despite errors
        
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
    
    async def send_heartbeat(self):
        """Send heartbeat to all connections"""
        heartbeat_message = {
            "type": WebSocketMessageType.HEARTBEAT.value,
            "message": "ping",
            "server_time": datetime.utcnow().isoformat()
        }
        
        await self.connection_manager.broadcast_system_wide(heartbeat_message)
    
    async def connect_deployment_monitor(self, websocket: WebSocket, deployment_id: str):
        """Connect a WebSocket for monitoring a specific deployment"""
        # Ensure heartbeat is started
        self._ensure_heartbeat_started()
        
        await self.connection_manager.connect(websocket, deployment_id)
        
        try:
            while True:
                # Wait for messages from client (like pings or requests)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages
                if message.get("type") == "ping":
                    await self.connection_manager.send_message(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error for deployment {deployment_id}: {e}")
            self.connection_manager.disconnect(websocket)
    
    async def connect_system_monitor(self, websocket: WebSocket):
        """Connect a WebSocket for system-wide monitoring"""
        # Ensure heartbeat is started
        self._ensure_heartbeat_started()
        
        await self.connection_manager.connect(websocket)
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages
                if message.get("type") == "ping":
                    await self.connection_manager.send_message(websocket, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error for system monitor: {e}")
            self.connection_manager.disconnect(websocket)
    
    # Deployment event methods
    async def deployment_started(self, deployment_id: str, project_name: str):
        """Notify that a deployment has started"""
        # Ensure heartbeat is started
        self._ensure_heartbeat_started()
        
        message = {
            "type": WebSocketMessageType.DEPLOYMENT_STATUS.value,
            "status": "started",
            "message": f"Deployment started for {project_name}",
            "project_name": project_name
        }
        await self.connection_manager.broadcast_to_deployment(deployment_id, message)
    
    async def deployment_progress(self, deployment_id: str, progress: float, message: str):
        """Update deployment progress"""
        progress_message = {
            "type": WebSocketMessageType.DEPLOYMENT_PROGRESS.value,
            "progress": progress,
            "message": message
        }
        await self.connection_manager.broadcast_to_deployment(deployment_id, progress_message)
    
    async def deployment_logs(self, deployment_id: str, logs: List[str]):
        """Send deployment logs"""
        log_message = {
            "type": WebSocketMessageType.DEPLOYMENT_LOGS.value,
            "logs": logs
        }
        await self.connection_manager.broadcast_to_deployment(deployment_id, log_message)
    
    async def deployment_error(self, deployment_id: str, error: str, error_details: Optional[str] = None):
        """Notify of deployment error"""
        error_message = {
            "type": WebSocketMessageType.DEPLOYMENT_ERROR.value,
            "error": error,
            "error_details": error_details
        }
        await self.connection_manager.broadcast_to_deployment(deployment_id, error_message)
    
    async def deployment_completed(self, deployment_id: str, deployment_url: Optional[str] = None, 
                                 infrastructure_outputs: Optional[Dict[str, Any]] = None):
        """Notify that deployment is completed"""
        completion_message = {
            "type": WebSocketMessageType.DEPLOYMENT_COMPLETE.value,
            "status": "completed",
            "message": "Deployment completed successfully",
            "deployment_url": deployment_url,
            "infrastructure_outputs": infrastructure_outputs
        }
        await self.connection_manager.broadcast_to_deployment(deployment_id, completion_message)
    
    async def system_notification(self, message: str, notification_type: str = "info"):
        """Send system-wide notification"""
        system_message = {
            "type": WebSocketMessageType.SYSTEM_STATUS.value,
            "notification_type": notification_type,
            "message": message
        }
        await self.connection_manager.broadcast_system_wide(system_message)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket service statistics"""
        return {
            "total_system_connections": len(self.connection_manager.system_connections),
            "deployment_connections": {
                deployment_id: len(connections) 
                for deployment_id, connections in self.connection_manager.deployment_connections.items()
            },
            "total_connections": (
                len(self.connection_manager.system_connections) + 
                sum(len(connections) for connections in self.connection_manager.deployment_connections.values())
            )
        }
    
    def cleanup(self):
        """Cleanup WebSocket service"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()

# Global WebSocket service instance
websocket_service = None

def get_websocket_service() -> WebSocketService:
    """Get the global WebSocket service instance, creating it if needed"""
    global websocket_service
    if websocket_service is None:
        websocket_service = WebSocketService()
    return websocket_service
