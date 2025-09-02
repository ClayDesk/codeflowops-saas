"""
Minimal GitHub OAuth Authentication Routes for debugging
"""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter()

@router.get("/test")
def test_endpoint():
    """Simple test endpoint to verify the router is working"""
    return {"status": "GitHub auth routes are working!", "test": True}

@router.get("/github/test")
def github_test_endpoint():
    """Test GitHub route path"""
    return {"status": "GitHub test endpoint working", "path": "/github/test"}

# Basic info endpoint
@router.get("/github/status")
def github_status():
    """GitHub OAuth status endpoint"""
    return {
        "service": "GitHub OAuth",
        "status": "active",
        "endpoints": ["/github/test", "/github/status", "/test"]
    }

logger.info("✅ Minimal GitHub auth routes loaded successfully")
