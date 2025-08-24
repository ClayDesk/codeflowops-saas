"""
Simple Auth Router - Fallback for development
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.get("/health")
async def auth_health():
    """Auth service health check"""
    return {
        "status": "healthy",
        "service": "auth",
        "message": "Authentication service is operational (development mode)"
    }

@router.post("/login")
async def login(credentials: Dict[str, Any]):
    """Mock login endpoint for development"""
    return {
        "status": "success",
        "message": "Login successful (development mode)",
        "token": "dev-token-123",
        "user": {
            "id": "dev-user",
            "email": "dev@example.com"
        }
    }

@router.post("/logout")
async def logout():
    """Mock logout endpoint for development"""
    return {
        "status": "success",
        "message": "Logout successful"
    }
