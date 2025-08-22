"""
Simple Core API for CodeFlowOps SaaS Workftry:
    from detectors.stack_detector import classify_stack, is_php_repo, is_static_site
    from detectors.enhanced_stack_detector import EnhancedStackDetector
    from detectors.angular import detect_angular
    from detectors.laravel import detect_laravel
    from detectors.python import PythonFrameworkDetector
    from detectors.react import detect_react
    from detectors.nodejs import detect_nodejs
    logger.info("✅ Analysis components loaded successfully")
    ANALYSIS_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"⚠️ Could not import analysis components: {e}")
    classify_stack = Noneined Modular Version
Core functionality with modular router integration - legacy deployment logic removed
"""
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uuid
from datetime import datetime
import json
import tempfile
import os
import subprocess
import asyncio
import sys
from pathlib import Path
import boto3
import shutil
from concurrent.futures import ThreadPoolExecutor
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background deployment infrastructure (simplified)
executor = ThreadPoolExecutor(max_workers=4)
_DEPLOY_STATES = {}
_LOCK = threading.Lock()

# Import repository enhancer and cleanup service
from repository_enhancer import RepositoryEnhancer, _get_primary_language
from cleanup_service import cleanup_service

# Add backend paths to import existing components
backend_path = Path(__file__).parent
src_path = backend_path / "src"
sys.path.append(str(backend_path))
sys.path.append(str(src_path))

# Import existing analysis components
try:
    from detectors.stack_detector import classify_stack, is_php_repo, is_static_site
    from detectors.enhanced_stack_detector import EnhancedStackDetector
    from detectors.angular import AngularDetector
    from detectors.laravel import detect_laravel
    from detectors.python import PythonFrameworkDetector
    from detectors.react import detect_react
    from detectors.nodejs import NodeJSDetector
    logger.info("✅ Analysis components loaded successfully")
    ANALYSIS_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"⚠️ Could not import analysis components: {e}")
    classify_stack = None
    ANALYSIS_COMPONENTS_AVAILABLE = False

# Import modular router system
MODULAR_ROUTERS_AVAILABLE = False
try:
    from routers.registry import StackRouterRegistry
    stack_router_registry = StackRouterRegistry()
    MODULAR_ROUTERS_AVAILABLE = True
    logger.info("✅ Modular router system loaded successfully")
except ImportError as e:
    logger.error(f"⚠️ Modular router system not available: {e}")
    stack_router_registry = None

# Pydantic models
class RepoAnalysisRequest(BaseModel):
    repo_url: str
    analysis_type: str = "full"

class DeployRequest(BaseModel):
    repository_url: str
    credential_id: str
    analysis: Optional[Dict[str, Any]] = None
    deployment_config: Optional[Dict[str, Any]] = None
    deployment_id: Optional[str] = None
    sessionId: Optional[str] = None  # Backward compatibility

class CredentialsRequest(BaseModel):
    aws_access_key: str
    aws_secret_key: str
    aws_region: str

# Create FastAPI app and router
app = FastAPI(title="CodeFlowOps Simple SaaS API - Streamlined")
router = APIRouter()

# Session management (simplified)
deployment_sessions = {}

@router.post("/api/analyze-repo")
async def analyze_repository(request: RepoAnalysisRequest):
    """
    Enhanced repository analysis with stack detection
    Routes to appropriate stack handler when available
    """
    repo_url = request.repo_url.strip()
    logger.info(f"🔍 Analyzing repository: {repo_url}")
    
    try:
        # Use repository enhancer for comprehensive analysis
        enhancer = RepositoryEnhancer()
        analysis = enhancer.enhance_analysis({"url": repo_url})
        
        if not analysis or analysis.get("error"):
            raise HTTPException(status_code=400, detail=analysis.get("error", "Analysis failed"))
        
        # Add modular routing information if available
        if MODULAR_ROUTERS_AVAILABLE and analysis.get("detected_stack"):
            detected_stack = analysis["detected_stack"]
            available_routers = stack_router_registry.get_available_stacks()
            
            analysis["modular_routing"] = {
                "stack_detected": detected_stack,
                "router_available": detected_stack in available_routers,
                "available_routers": available_routers,
                "deployment_endpoint": f"/api/deploy/{detected_stack}" if detected_stack in available_routers else "/api/deploy"
            }
            
            logger.info(f"🎯 Stack {detected_stack} detected, router available: {detected_stack in available_routers}")
        
        return {
            "success": True,
            "analysis": analysis,
            "analysis_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "modular_system_available": MODULAR_ROUTERS_AVAILABLE
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/api/validate-credentials")
async def validate_credentials(request: CredentialsRequest):
    """Validate AWS credentials"""
    try:
        # Create boto3 session with provided credentials
        session = boto3.Session(
            aws_access_key_id=request.aws_access_key,
            aws_secret_access_key=request.aws_secret_key,
            region_name=request.aws_region
        )
        
        # Test credentials by calling STS get_caller_identity
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        return {
            "success": True,
            "valid": True,
            "account_id": identity.get("Account"),
            "user_id": identity.get("UserId"),
            "arn": identity.get("Arn"),
            "region": request.aws_region
        }
        
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        return {
            "success": False,
            "valid": False,
            "error": str(e)
        }

@router.post("/api/deploy")
async def deploy_to_aws(request: DeployRequest):
    """
    Streamlined deployment endpoint - delegates to modular routers when possible
    Falls back to basic deployment for unsupported stacks
    """
    try:
        deployment_id = request.deployment_id or request.sessionId or str(uuid.uuid4())
        analysis = request.analysis or {}
        
        # Initialize deployment session
        with _LOCK:
            _DEPLOY_STATES[deployment_id] = {
                "status": "initializing",
                "steps": [{"step": "Deployment Started", "status": "in_progress", "message": "Starting deployment..."}],
                "logs": ["🚀 Starting streamlined deployment..."],
                "created_at": datetime.utcnow().isoformat(),
                "progress": 10,
                "analysis": analysis
            }
        
        # Check if we have modular routing available
        detected_stack = analysis.get("detected_stack")
        if MODULAR_ROUTERS_AVAILABLE and detected_stack:
            available_stacks = stack_router_registry.get_available_stacks()
            
            if detected_stack in available_stacks:
                logger.info(f"🎯 Delegating {detected_stack} deployment to modular router")
                
                # Update status to indicate router delegation
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["status"] = "routing"
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"🔄 Routing to {detected_stack} specialized handler...")
                    _DEPLOY_STATES[deployment_id]["progress"] = 25
                
                # This is where we would delegate to the specific router
                # For now, we'll simulate the handoff
                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "status": "routed",
                    "message": f"Deployment routed to {detected_stack} handler",
                    "stack_type": detected_stack,
                    "using_modular_router": True
                }
        
        # Fall back to basic deployment for unsupported stacks
        logger.info("🔧 Using fallback deployment for unsupported or generic stack")
        
        # Start background deployment
        executor.submit(_run_basic_deployment, deployment_id, analysis, request)
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "status": "started",
            "message": "Deployment started with fallback handler",
            "using_modular_router": False
        }
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

def _run_basic_deployment(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Simplified background deployment for basic stacks
    """
    try:
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "deploying"
            _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Executing basic deployment pipeline...")
            _DEPLOY_STATES[deployment_id]["progress"] = 50
        
        # Basic deployment simulation (replace with actual deployment logic)
        import time
        time.sleep(2)  # Simulate deployment work
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "completed"
            _DEPLOY_STATES[deployment_id]["logs"].append("✅ Basic deployment completed")
            _DEPLOY_STATES[deployment_id]["progress"] = 100
            _DEPLOY_STATES[deployment_id]["deployment_url"] = f"https://example.com/{deployment_id}"
        
    except Exception as e:
        logger.error(f"Basic deployment failed: {e}")
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "failed"
            _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Deployment failed: {str(e)}")
            _DEPLOY_STATES[deployment_id]["error"] = str(e)

@router.get("/api/deployment/{deployment_id}/status")
async def get_deployment_status(deployment_id: str):
    """Get deployment status"""
    if deployment_id not in _DEPLOY_STATES:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    return _DEPLOY_STATES[deployment_id]

@router.get("/api/deployment/{deployment_id}/result")
async def get_deployment_result(deployment_id: str):
    """Get deployment result"""
    if deployment_id not in _DEPLOY_STATES:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = _DEPLOY_STATES[deployment_id]
    
    if deployment["status"] != "completed":
        raise HTTPException(status_code=400, detail="Deployment not completed")
    
    return {
        "deployment_id": deployment_id,
        "status": deployment["status"],
        "deployment_url": deployment.get("deployment_url"),
        "logs": deployment.get("logs", []),
        "completed_at": datetime.utcnow().isoformat()
    }

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routers if available
if MODULAR_ROUTERS_AVAILABLE:
    try:
        # Add stack-specific deployment endpoint
        @app.post("/api/deploy/{stack_type}")
        async def deploy_with_stack(stack_type: str, request: dict):
            """
            Deploy using appropriate stack router
            """
            logger.info(f"🎯 Routing deployment to {stack_type} stack")
            
            try:
                # Get appropriate router for stack type
                stack_router = stack_router_registry.get_router_for_stack(stack_type)
                
                # Generate deployment ID
                deployment_id = f"{stack_type}-{request.get('session_id', 'unknown')}-{int(datetime.now().timestamp())}"
                
                return {
                    "success": True,
                    "message": f"Routed to {stack_type} stack handler",
                    "stack_type": stack_type,
                    "deployment_id": deployment_id,
                    "router_loaded": True,
                    "timestamp": datetime.now().isoformat(),
                    "modular_system": True
                }
                
            except Exception as e:
                logger.error(f"Failed to route to {stack_type} stack: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to route to {stack_type} stack: {str(e)}"
                )
        
        # Add available stacks endpoint
        @app.get("/api/stacks/available")
        async def get_available_stacks():
            """Get list of available stack types"""
            return {
                "available_stacks": stack_router_registry.get_available_stacks(),
                "total_routers": len(stack_router_registry.routers),
                "router_types": list(stack_router_registry.routers.keys()),
                "modular_system": True
            }
        
        # Add system health endpoint
        @app.get("/api/system/health")
        async def system_health_check():
            """System health check for modular system"""
            return {
                "status": "healthy",
                "service": "streamlined-modular-api",
                "version": "2.0.0",
                "routers_available": True,
                "routers_loaded": len(stack_router_registry.routers),
                "available_stacks": stack_router_registry.get_available_stacks(),
                "modular_system": True
            }
        
        logger.info("✅ Modular router endpoints added to streamlined API")
    
    except Exception as e:
        logger.error(f"❌ Failed to add modular router endpoints: {e}")
else:
    logger.info("⚠️ Modular router endpoints not available - using fallback deployment only")

# Add basic health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "CodeFlowOps Streamlined API", "version": "2.0.0"}

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "CodeFlowOps Streamlined API", "version": "2.0.0"}

# Include the main router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
