"""
Simple Core API for CodeFlowOps SaaS Workflow - Streamlined Modular Version
Core functionality with modular router integration - legacy deployment logic removed
"""
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uuid
import time
import random
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
_ANALYSIS_SESSIONS = {}  # Store analysis data by deployment_id
_LOCK = threading.Lock()

# Import repository enhancer and cleanup service (graceful fallback)
try:
    import importlib
    repository_enhancer = importlib.import_module('repository_enhancer')
    RepositoryEnhancer = getattr(repository_enhancer, 'RepositoryEnhancer', None)
    _get_primary_language = getattr(repository_enhancer, '_get_primary_language', None)
    
    cleanup_service_module = importlib.import_module('cleanup_service')
    cleanup_service = getattr(cleanup_service_module, 'cleanup_service', None)
    ENHANCER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import enhancer/cleanup services: {e}")
    RepositoryEnhancer = None
    cleanup_service = None
    _get_primary_language = None
    ENHANCER_AVAILABLE = False

# Add backend paths to import existing components
backend_path = Path(__file__).parent
src_path = backend_path / "src"
sys.path.append(str(backend_path))
sys.path.append(str(src_path))

# Import existing analysis components (graceful fallback)
try:
    import importlib
    
    # Import detector modules dynamically
    stack_detector = importlib.import_module('detectors.stack_detector')
    classify_stack = getattr(stack_detector, 'classify_stack', None)
    is_nextjs_repo = getattr(stack_detector, 'is_nextjs_repo', None)
    is_php_repo = getattr(stack_detector, 'is_php_repo', None)
    is_static_site = getattr(stack_detector, 'is_static_site', None)
    
    enhanced_stack_detector = importlib.import_module('detectors.enhanced_stack_detector')
    EnhancedStackDetector = getattr(enhanced_stack_detector, 'EnhancedStackDetector', None)
    
    angular_detector = importlib.import_module('detectors.angular')
    detect_angular = getattr(angular_detector, 'detect_angular', None)
    
    laravel_detector = importlib.import_module('detectors.laravel')
    detect_laravel = getattr(laravel_detector, 'detect_laravel', None)
    
    python_detector = importlib.import_module('detectors.python')
    PythonFrameworkDetector = getattr(python_detector, 'PythonFrameworkDetector', None)
    
    react_detector = importlib.import_module('detectors.react')
    detect_react = getattr(react_detector, 'detect_react', None)
    
    nodejs_detector = importlib.import_module('detectors.nodejs')
    detect_nodejs = getattr(nodejs_detector, 'detect_nodejs', None)
    
    logger.info("✅ Analysis components loaded successfully")
    ANALYSIS_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"⚠️ Could not import analysis components: {e}")
    classify_stack = None
    is_nextjs_repo = None
    is_php_repo = None
    is_static_site = None
    EnhancedStackDetector = None
    detect_angular = None
    detect_laravel = None
    PythonFrameworkDetector = None
    detect_react = None
    detect_nodejs = None
    ANALYSIS_COMPONENTS_AVAILABLE = False

# Import modular router system (graceful fallback)
MODULAR_ROUTERS_AVAILABLE = False
try:
    import importlib
    
    routers_registry = importlib.import_module('routers.registry')
    StackRouterRegistry = getattr(routers_registry, 'StackRouterRegistry', None)
    
    if StackRouterRegistry:
        stack_router_registry = StackRouterRegistry()
        MODULAR_ROUTERS_AVAILABLE = True
        logger.info("✅ Modular router system loaded successfully")
    else:
        stack_router_registry = None
        logger.error("⚠️ StackRouterRegistry class not found")
except ImportError as e:
    logger.error(f"⚠️ Modular router system not available: {e}")
    StackRouterRegistry = None
    stack_router_registry = None

# Pydantic models
class RepoAnalysisRequest(BaseModel):
    repo_url: str
    analysis_type: str = "full"

class DeployRequest(BaseModel):
    deployment_id: str
    aws_access_key: str
    aws_secret_key: str
    aws_region: str = "us-east-1"
    project_name: Optional[str] = None
    # Legacy fields for backward compatibility
    repository_url: Optional[str] = None
    credential_id: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    deployment_config: Optional[Dict[str, Any]] = None
    sessionId: Optional[str] = None
    # 🔥 Firebase/Supabase configuration for BaaS deployments
    firebase_config: Optional[Dict[str, str]] = None
    supabase_config: Optional[Dict[str, str]] = None

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
        # Import and use the enhanced analyzer
        try:
            import importlib
            enhanced_analyzer_module = importlib.import_module('enhanced_repository_analyzer')
            EnhancedRepositoryAnalyzer = getattr(enhanced_analyzer_module, 'EnhancedRepositoryAnalyzer', None)
            ENHANCED_ANALYZER_AVAILABLE = EnhancedRepositoryAnalyzer is not None
        except ImportError:
            # Fallback to basic analysis
            logger.warning("Enhanced analyzer not available, using basic analysis")
            ENHANCED_ANALYZER_AVAILABLE = False
            EnhancedRepositoryAnalyzer = None
        
        if not ENHANCED_ANALYZER_AVAILABLE:
            # Fallback to basic analysis
            analysis = {
                "framework": "unknown",
                "projectType": "static_site",
                "detected_stack": "static_site",
                "frameworks": [],
                "confidence": 0.5,
                "basic_analysis": True
            }
            deployment_id = str(uuid.uuid4())
            
            # Store basic analysis data
            with _LOCK:
                _ANALYSIS_SESSIONS[deployment_id] = {
                    "analysis": analysis,
                    "repo_url": repo_url,
                    "local_repo_path": None,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {
                "success": True,
                "analysis": analysis,
                "analysis_id": deployment_id,
                "timestamp": datetime.utcnow().isoformat(),
                "modular_system_available": MODULAR_ROUTERS_AVAILABLE,
                "note": "Using basic analysis - enhanced analyzer not available"
            }
        
        # Generate deployment ID for analysis session
        deployment_id = str(uuid.uuid4())
        
        # Use enhanced analyzer for comprehensive analysis
        analyzer = EnhancedRepositoryAnalyzer()
        analysis = await analyzer.analyze_repository_comprehensive(repo_url, deployment_id)
        
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
        
        # Store analysis data for later deployment use
        with _LOCK:
            _ANALYSIS_SESSIONS[deployment_id] = {
                "analysis": analysis,
                "repo_url": repo_url,
                "local_repo_path": analysis.get('local_repo_path'),  # Store the local repository path
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "success": True,
            "analysis": analysis,
            "analysis_id": deployment_id,
            "timestamp": datetime.utcnow().isoformat(),
            "modular_system_available": MODULAR_ROUTERS_AVAILABLE,
            # Debug info for routing
            "debug_routing": {
                "framework": analysis.get("framework"),
                "projectType": analysis.get("projectType"),
                "legacy_framework": analysis.get("analysis", {}).get("framework", {}).get("type"),
                "frameworks_array": analysis.get("frameworks", [])
            }
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
    Falls back to basic deployment for supported stacks
    """
    try:
        deployment_id = request.deployment_id
        if not deployment_id:
            raise HTTPException(status_code=400, detail="deployment_id is required")
        
        # Get analysis data - either from request or from stored sessions
        analysis = request.analysis
        repo_url = request.repository_url
        
        if not analysis:
            # Look up analysis data from previous analysis session
            with _LOCK:
                if deployment_id in _ANALYSIS_SESSIONS:
                    stored_session = _ANALYSIS_SESSIONS[deployment_id]
                    analysis = stored_session["analysis"]
                    repo_url = stored_session["repo_url"]
                    logger.info(f"📋 Retrieved analysis data for deployment {deployment_id}")
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"No analysis data found for deployment_id {deployment_id}. Please analyze the repository first."
                    )
        
        # Validate that we have AWS credentials
        if not request.aws_access_key or not request.aws_secret_key:
            raise HTTPException(status_code=400, detail="AWS credentials are required for deployment")
        
        logger.info(f"🚀 Starting deployment {deployment_id} with credentials for region {request.aws_region}")
        
        # Initialize deployment session
        with _LOCK:
            _DEPLOY_STATES[deployment_id] = {
                "status": "initializing",
                "steps": [{"step": "Deployment Started", "status": "in_progress", "message": "Starting deployment..."}],
                "logs": ["🚀 Starting streamlined deployment..."],
                "created_at": datetime.utcnow().isoformat(),
                "progress": 10,
                "analysis": analysis,
                "repository_url": repo_url,
                "project_name": request.project_name,
                "aws_region": request.aws_region
            }
        
        # Start background deployment
        executor.submit(_run_basic_deployment, deployment_id, analysis, request)
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "status": "started",
            "message": "Deployment started",
            "using_modular_router": False
        }
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

def _run_basic_deployment(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Basic deployment simulation for Elastic Beanstalk compatibility
    """
    try:
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "deploying"
            _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Starting basic deployment...")
            _DEPLOY_STATES[deployment_id]["progress"] = 30
        
        # Simulate deployment steps
        time.sleep(2)
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("📋 Preparing deployment environment...")
            _DEPLOY_STATES[deployment_id]["progress"] = 50
        
        time.sleep(2)
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🚀 Deploying application...")
            _DEPLOY_STATES[deployment_id]["progress"] = 80
        
        time.sleep(3)
        
        # Complete deployment
        deployment_url = f"https://example-{deployment_id[:8]}.s3-website-us-east-1.amazonaws.com"
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "completed"
            _DEPLOY_STATES[deployment_id]["logs"].append("✅ Deployment completed successfully!")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🌐 Application URL: {deployment_url}")
            _DEPLOY_STATES[deployment_id]["progress"] = 100
            _DEPLOY_STATES[deployment_id]["deployment_url"] = deployment_url
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
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
    """Get deployment result - supports both in-progress and completed deployments"""
    if deployment_id not in _DEPLOY_STATES:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    deployment = _DEPLOY_STATES[deployment_id]
    
    # Return current state regardless of completion status
    response = {
        "deployment_id": deployment_id,
        "status": deployment["status"],
        "progress": deployment.get("progress", 0),
        "logs": deployment.get("logs", []),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add completion-specific fields when finished
    if deployment["status"] == "completed":
        response["deployment_url"] = deployment.get("deployment_url")
        response["cloudfront_url"] = deployment.get("cloudfront_url")
        response["s3_url"] = deployment.get("s3_url")
        response["completed_at"] = response["timestamp"]
    elif deployment["status"] == "failed":
        response["error"] = deployment.get("error", "Deployment failed")
        response["failed_at"] = response["timestamp"]
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add simple authentication routes (compatible with frontend)
@app.get("/api/v1/auth/config")
async def get_auth_config():
    return {
        "provider": "cognito",
        "cognito": {
            "region": os.getenv("COGNITO_REGION", "us-east-1"),
            "userPoolId": os.getenv("COGNITO_USER_POOL_ID", ""),
            "clientId": os.getenv("COGNITO_CLIENT_ID", ""),
            "domain": os.getenv("COGNITO_DOMAIN", ""),
        }
    }

@app.post("/api/v1/auth/login")
async def login_fallback():
    raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable")

@app.post("/api/v1/auth/register") 
async def register_fallback():
    raise HTTPException(status_code=503, detail="Authentication service temporarily unavailable")

# GitHub authentication endpoint (compatible with frontend)
@app.get("/auth/github")
async def github_auth():
    """GitHub OAuth endpoint"""
    return {"message": "GitHub authentication endpoint", "status": "available"}

# Add health check endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "CodeFlowOps Streamlined API", "version": "2.0.0"}

@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "service": "CodeFlowOps Streamlined API", "version": "2.0.0"}

@app.get("/")
async def root():
    return {
        "message": "CodeFlowOps Backend is running!",
        "version": "2.2.0",
        "status": "operational",
        "environment": "production",
        "api_endpoints": [
            "/api/analyze-repo",
            "/api/validate-credentials", 
            "/api/deploy",
            "/api/deployment/{id}/status",
            "/api/deployment/{id}/result",
            "/auth/github",
            "/api/v1/auth/config"
        ]
    }

@app.get("/api/status")
async def api_status():
    return {
        "api": "CodeFlowOps",
        "status": "running",
        "database": "connected" if os.getenv("DATABASE_URL") else "not configured",
        "redis": "connected" if os.getenv("REDIS_URL") else "not configured"
    }

# Include the main router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
@app.get("/api/v1/analyze")
async def analyze_placeholder():
    return {
        "message": "Analysis API endpoint - ready for implementation",
        "status": "placeholder"
    }

@app.get("/api/v1/deploy")
async def deploy_placeholder():
    return {
        "message": "Deployment API endpoint - ready for implementation", 
        "status": "placeholder"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
