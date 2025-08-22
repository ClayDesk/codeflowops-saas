# WebSocket Routes for Real-time Monitoring
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from ..services.websocket_service import get_websocket_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/deployment/{deployment_id}")
async def websocket_deployment_monitor(websocket: WebSocket, deployment_id: str):
    """
    WebSocket endpoint for monitoring a specific deployment
    
    Usage:
    - Connect to ws://localhost:8000/api/ws/deployment/{deployment_id}
    - Receive real-time updates about deployment progress, logs, and status
    """
    logger.info(f"WebSocket connection requested for deployment: {deployment_id}")
    websocket_service = get_websocket_service()
    await websocket_service.connect_deployment_monitor(websocket, deployment_id)

@router.websocket("/ws/system")
async def websocket_system_monitor(websocket: WebSocket):
    """
    WebSocket endpoint for system-wide monitoring
    
    Usage:
    - Connect to ws://localhost:8000/api/ws/system
    - Receive system-wide notifications and status updates
    """
    logger.info("System WebSocket connection requested")
    websocket_service = get_websocket_service()
    await websocket_service.connect_system_monitor(websocket)

@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket service statistics"""
    websocket_service = get_websocket_service()
    return {
        "status": "success",
        "data": websocket_service.get_stats()
    }
