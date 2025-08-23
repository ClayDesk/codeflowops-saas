"""
WebSocket manager for CodeFlowOps
Handles real-time communication for deployment progress updates
"""

import logging
import json
import asyncio
from typing import Dict, Set, Any, Optional, List
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates
    Supports session-based communication and broadcasting
    """
    
    def __init__(self):
        # Session ID -> Set of WebSocket connections
        self.session_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        
        # User ID -> Set of WebSocket connections
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        
        # WebSocket -> Connection info
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Active connections count
        self.active_connections = 0
        
        # Message queue for offline users
        self.message_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Heartbeat tracking
        self.heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Accept WebSocket connection and register it
        
        Associates connection with session and/or user for targeted messaging
        """
        try:
            await websocket.accept()
            
            connection_id = str(uuid.uuid4())
            self.active_connections += 1
            
            # Store connection info
            self.connection_info[websocket] = {
                "connection_id": connection_id,
                "session_id": session_id,
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow()
            }
            
            # Register connection for session
            if session_id:
                self.session_connections[session_id].add(websocket)
                logger.info(f"WebSocket connected to session {session_id}")
                
                # Send queued messages for this session
                await self._send_queued_messages(session_id, websocket)
            
            # Register connection for user
            if user_id:
                self.user_connections[user_id].add(websocket)
                logger.info(f"WebSocket connected for user {user_id}")
                
                # Send queued messages for this user
                await self._send_queued_user_messages(user_id, websocket)
            
            # Start heartbeat
            self.heartbeat_tasks[websocket] = asyncio.create_task(
                self._heartbeat_loop(websocket)
            )
            
            # Send connection confirmation
            await self._send_to_websocket(websocket, {
                "type": "connection_established",
                "connection_id": connection_id,
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"WebSocket connection established: {connection_id}")
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            await self.disconnect(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """
        Handle WebSocket disconnection and cleanup
        
        Removes connection from all registries and cancels heartbeat
        """
        try:
            connection_info = self.connection_info.get(websocket, {})
            session_id = connection_info.get("session_id")
            user_id = connection_info.get("user_id")
            connection_id = connection_info.get("connection_id", "unknown")
            
            # Remove from session connections
            if session_id and websocket in self.session_connections[session_id]:
                self.session_connections[session_id].discard(websocket)
                if not self.session_connections[session_id]:
                    del self.session_connections[session_id]
            
            # Remove from user connections
            if user_id and websocket in self.user_connections[user_id]:
                self.user_connections[user_id].discard(websocket)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove connection info
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            
            # Cancel heartbeat task
            if websocket in self.heartbeat_tasks:
                self.heartbeat_tasks[websocket].cancel()
                del self.heartbeat_tasks[websocket]
            
            self.active_connections = max(0, self.active_connections - 1)
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"WebSocket disconnect cleanup failed: {str(e)}")
    
    async def send_to_session(self, session_id: str, message: Dict[str, Any]):
        """
        Send message to all connections for a session
        
        Broadcasts message to all WebSocket connections associated with the session
        """
        try:
            connections = self.session_connections.get(session_id, set())
            
            if not connections:
                # Queue message for when session connects
                self.message_queue[f"session:{session_id}"].append({
                    **message,
                    "queued_at": datetime.utcnow().isoformat()
                })
                logger.debug(f"Message queued for session {session_id}")
                return
            
            # Send to all active connections
            disconnected = []
            for websocket in connections:
                try:
                    await self._send_to_websocket(websocket, message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {str(e)}")
                    disconnected.append(websocket)
            
            # Clean up disconnected WebSockets
            for websocket in disconnected:
                await self.disconnect(websocket)
            
            logger.debug(f"Message sent to {len(connections) - len(disconnected)} connections for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to session {session_id}: {str(e)}")
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """
        Send message to all connections for a user
        
        Broadcasts message to all WebSocket connections associated with the user
        """
        try:
            connections = self.user_connections.get(user_id, set())
            
            if not connections:
                # Queue message for when user connects
                self.message_queue[f"user:{user_id}"].append({
                    **message,
                    "queued_at": datetime.utcnow().isoformat()
                })
                logger.debug(f"Message queued for user {user_id}")
                return
            
            # Send to all active connections
            disconnected = []
            for websocket in connections:
                try:
                    await self._send_to_websocket(websocket, message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {str(e)}")
                    disconnected.append(websocket)
            
            # Clean up disconnected WebSockets
            for websocket in disconnected:
                await self.disconnect(websocket)
            
            logger.debug(f"Message sent to {len(connections) - len(disconnected)} connections for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {str(e)}")
    
    async def broadcast(self, message: Dict[str, Any], exclude_session: Optional[str] = None):
        """
        Broadcast message to all active connections
        
        Optionally excludes connections from a specific session
        """
        try:
            all_connections = set()
            
            # Collect all connections
            for connections in self.session_connections.values():
                all_connections.update(connections)
            
            for connections in self.user_connections.values():
                all_connections.update(connections)
            
            # Remove excluded session connections
            if exclude_session:
                excluded_connections = self.session_connections.get(exclude_session, set())
                all_connections = all_connections - excluded_connections
            
            # Send to all connections
            disconnected = []
            for websocket in all_connections:
                try:
                    await self._send_to_websocket(websocket, message)
                except Exception as e:
                    logger.warning(f"Failed to send broadcast to WebSocket: {str(e)}")
                    disconnected.append(websocket)
            
            # Clean up disconnected WebSockets
            for websocket in disconnected:
                await self.disconnect(websocket)
            
            logger.info(f"Broadcast sent to {len(all_connections) - len(disconnected)} connections")
            
        except Exception as e:
            logger.error(f"Broadcast failed: {str(e)}")
    
    async def add_connection(self, session_id: str, websocket: WebSocket):
        """Add WebSocket connection to session (compatibility method)"""
        if websocket not in self.connection_info:
            await self.connect(websocket, session_id=session_id)
        else:
            # Update existing connection with session
            self.connection_info[websocket]["session_id"] = session_id
            self.session_connections[session_id].add(websocket)
    
    async def remove_connection(self, session_id: str, websocket: WebSocket):
        """Remove WebSocket connection from session (compatibility method)"""
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(websocket)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
    
    async def close_session_connections(self, session_id: str):
        """Close all WebSocket connections for a session"""
        try:
            connections = self.session_connections.get(session_id, set()).copy()
            
            for websocket in connections:
                try:
                    await websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {str(e)}")
                finally:
                    await self.disconnect(websocket)
            
            logger.info(f"Closed {len(connections)} connections for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to close session connections: {str(e)}")
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        try:
            return {
                "active_connections": self.active_connections,
                "session_connections": len(self.session_connections),
                "user_connections": len(self.user_connections),
                "queued_messages": sum(len(messages) for messages in self.message_queue.values()),
                "connections_by_session": {
                    session_id: len(connections)
                    for session_id, connections in self.session_connections.items()
                },
                "heartbeat_tasks": len(self.heartbeat_tasks)
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection stats: {str(e)}")
            return {}
    
    async def cleanup_stale_connections(self):
        """Clean up stale connections and expired message queues"""
        try:
            now = datetime.utcnow()
            stale_connections = []
            
            # Find stale connections (no heartbeat for 5 minutes)
            for websocket, info in self.connection_info.items():
                last_heartbeat = info.get("last_heartbeat")
                if last_heartbeat and (now - last_heartbeat).total_seconds() > 300:
                    stale_connections.append(websocket)
            
            # Disconnect stale connections
            for websocket in stale_connections:
                await self.disconnect(websocket)
            
            # Clean up old queued messages (older than 1 hour)
            expired_keys = []
            for key, messages in self.message_queue.items():
                self.message_queue[key] = [
                    msg for msg in messages
                    if "queued_at" in msg and 
                    (now - datetime.fromisoformat(msg["queued_at"])).total_seconds() < 3600
                ]
                if not self.message_queue[key]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.message_queue[key]
            
            if stale_connections or expired_keys:
                logger.info(f"Cleaned up {len(stale_connections)} stale connections and {len(expired_keys)} expired message queues")
                
        except Exception as e:
            logger.error(f"Connection cleanup failed: {str(e)}")
    
    # Private methods
    
    async def _send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific WebSocket connection"""
        try:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()
            
            # Convert to JSON string
            message_str = json.dumps(message, default=str)
            
            # Send message
            await websocket.send_text(message_str)
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {str(e)}")
            raise
    
    async def _send_queued_messages(self, session_id: str, websocket: WebSocket):
        """Send queued messages for a session to a WebSocket"""
        try:
            queue_key = f"session:{session_id}"
            messages = self.message_queue.get(queue_key, [])
            
            for message in messages:
                try:
                    await self._send_to_websocket(websocket, message)
                except Exception as e:
                    logger.warning(f"Failed to send queued message: {str(e)}")
            
            # Clear sent messages
            if queue_key in self.message_queue:
                del self.message_queue[queue_key]
            
            if messages:
                logger.info(f"Sent {len(messages)} queued messages for session {session_id}")
                
        except Exception as e:
            logger.error(f"Failed to send queued messages: {str(e)}")
    
    async def _send_queued_user_messages(self, user_id: str, websocket: WebSocket):
        """Send queued messages for a user to a WebSocket"""
        try:
            queue_key = f"user:{user_id}"
            messages = self.message_queue.get(queue_key, [])
            
            for message in messages:
                try:
                    await self._send_to_websocket(websocket, message)
                except Exception as e:
                    logger.warning(f"Failed to send queued message: {str(e)}")
            
            # Clear sent messages
            if queue_key in self.message_queue:
                del self.message_queue[queue_key]
            
            if messages:
                logger.info(f"Sent {len(messages)} queued messages for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to send queued user messages: {str(e)}")
    
    async def _heartbeat_loop(self, websocket: WebSocket):
        """Heartbeat loop to keep connection alive and detect disconnections"""
        try:
            while websocket in self.connection_info:
                try:
                    # Send ping
                    await websocket.ping()
                    
                    # Update last heartbeat
                    if websocket in self.connection_info:
                        self.connection_info[websocket]["last_heartbeat"] = datetime.utcnow()
                    
                    # Wait for next heartbeat
                    await asyncio.sleep(30)  # 30 seconds
                    
                except (WebSocketDisconnect, ConnectionError):
                    break
                except Exception as e:
                    logger.warning(f"Heartbeat failed: {str(e)}")
                    break
            
        except asyncio.CancelledError:
            pass  # Task was cancelled, this is expected
        except Exception as e:
            logger.error(f"Heartbeat loop error: {str(e)}")
        finally:
            # Ensure cleanup
            if websocket in self.connection_info:
                await self.disconnect(websocket)


# Global WebSocket manager instance
_websocket_manager = None


def get_websocket_manager() -> WebSocketManager:
    """Get global WebSocket manager instance"""
    global _websocket_manager
    
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    
    return _websocket_manager
