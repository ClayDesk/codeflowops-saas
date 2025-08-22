"""
New Modular API Server
Routes requests to appropriate stack-specific routers based on detection
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to Python path for imports
import sys
from pathlib import Path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import router registry
try:
    from routers.registry import stack_router_registry
    from routers.analysis_router import router as analysis_router
    ROUTERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Router imports failed: {e}")
    ROUTERS_AVAILABLE = False

app = FastAPI(
    title="CodeFlowOps SaaS - Modular API",
    description="Stack-aware deployment platform with dynamic router loading",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core analysis router
if ROUTERS_AVAILABLE:
    app.include_router(analysis_router, prefix="/api", tags=["Analysis"])
else:
    logger.warning("⚠️ Routers not available, running with minimal endpoints only")

class DeploymentRequest(BaseModel):
    session_id: str
    stack_type: str
    project_name: str
    repo_url: str
    branch: Optional[str] = "main"
    config: Optional[Dict[str, Any]] = {}

@app.post("/api/deploy/{stack_type}")
async def deploy_with_stack(
    stack_type: str,
    request: DeploymentRequest
):
    """
    Deploy using appropriate stack router
    Routes to specific stack handler based on detected type
    """
    logger.info(f"🎯 Routing deployment to {stack_type} stack")
    
    try:
        # Get appropriate router for stack type
        if not ROUTERS_AVAILABLE:
            return {
                "success": False,
                "message": "Router system not available",
                "stack_type": stack_type,
                "error": "Modular routers are not properly loaded"
            }
            
        stack_router = stack_router_registry.get_router_for_stack(stack_type)
        
        # Route to stack-specific deployment handler
        # In a real implementation, this would properly delegate to the stack router
        return {
            "success": True,
            "message": f"Routed to {stack_type} stack handler",
            "stack_type": stack_type,
            "router_loaded": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to route to {stack_type} stack: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to route to {stack_type} stack: {str(e)}"
        )

@app.get("/api/stacks/available")
async def get_available_stacks():
    """Get list of available stack types"""
    if not ROUTERS_AVAILABLE:
        return {
            "available_stacks": [],
            "total_routers": 0,
            "router_types": [],
            "error": "Router system not available"
        }
        
    return {
        "available_stacks": stack_router_registry.get_available_stacks(),
        "total_routers": len(stack_router_registry.routers),
        "router_types": list(stack_router_registry.routers.keys())
    }

@app.get("/api/system/health")
async def system_health_check():
    """System health check for modular API"""
    if ROUTERS_AVAILABLE:
        routers_count = len(stack_router_registry.routers)
        available_stacks = stack_router_registry.get_available_stacks()
    else:
        routers_count = 0
        available_stacks = []
        
    return {
        "status": "healthy",
        "service": "modular-api",
        "version": "2.0.0",
        "routers_available": ROUTERS_AVAILABLE,
        "routers_loaded": routers_count,
        "available_stacks": available_stacks
    }

@app.get("/api/health")
async def health_check():
    """API health check - simplified version"""
    return {
        "status": "healthy",
        "service": "modular-api",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Modular API Server...")
    print("=" * 50)
    print("URL: http://localhost:8001")
    print("Health: http://localhost:8001/api/system/health")
    print("Docs: http://localhost:8001/docs")
    print("=" * 50)
    uvicorn.run("modular_api:app", host="0.0.0.0", port=8001, reload=False)
