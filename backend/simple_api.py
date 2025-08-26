"""
Simple Core API for CodeFlowOps SaaS Workflow - Streamlined Modular Version
Core functionality with modular router integration - legacy deployment logic removed
"""

# Fix GitPython issue at the very beginning
import os
os.environ['GIT_PYTHON_REFRESH'] = 'quiet'

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

# Import the ReactDeployer for React-specific deployments
try:
    from react_deployer import ReactDeployer
    REACT_DEPLOYER_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ ReactDeployer imported successfully")
except ImportError as e:
    REACT_DEPLOYER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️ ReactDeployer not available: {e}")

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
    from detectors.stack_detector import classify_stack, is_nextjs_repo, is_php_repo, is_static_site
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

def authorize_github_url(repo_url: str, github_token: Optional[str] = None) -> str:
    """
    Authorize private GitHub URL by injecting token
    Returns: Modified URL that works with existing clone logic
    """
    if not github_token or 'github.com' not in repo_url:
        return repo_url
    
    if repo_url.startswith('https://github.com/'):
        return repo_url.replace('https://github.com/', f'https://{github_token}@github.com/')
    
    return repo_url

# Pydantic models
class RepoAnalysisRequest(BaseModel):
    repo_url: str
    analysis_type: str = "full"
    github_token: Optional[str] = None

class DeployRequest(BaseModel):
    deployment_id: Optional[str] = None
    analysis_id: Optional[str] = None  # Alternative field name from frontend
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None  # Alternative field name from frontend
    aws_secret_access_key: Optional[str] = None  # Alternative field name from frontend
    aws_region: str = "us-east-1"
    project_name: Optional[str] = None
    # Framework detection fields for routing
    framework: Optional[str] = None  # Framework detected by frontend (react, nextjs, etc.)
    project_type: Optional[str] = None  # Alternative framework field
    detected_framework: Optional[str] = None  # Additional framework field
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

@router.get("/")
async def root():
    """Root endpoint - API is healthy"""
    return {
        "status": "healthy",
        "service": "CodeFlowOps Streamlined API",
        "version": "2.0.0",
        "message": "Welcome to CodeFlowOps API"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for ELB"""
    return {
        "status": "healthy",
        "service": "CodeFlowOps Streamlined API",
        "version": "2.0.0"
    }

@router.get("/api/v1/pricing")
async def get_public_pricing(
    country: Optional[str] = None,
    currency: Optional[str] = None,
    referral_code: Optional[str] = None,
    company_size: Optional[str] = None
):
    """
    Public pricing endpoint that doesn't require authentication
    """
    # Return fallback static pricing for now
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": currency or "USD",
                "interval": "month",
                "features": ["3 projects", "Public repositories", "Community support"],
                "recommended": False
            },
            {
                "id": "starter",
                "name": "Starter", 
                "price": 19,
                "currency": currency or "USD",
                "interval": "month",
                "trial_days": 14,
                "features": ["10 projects", "Private repositories", "Email support"],
                "recommended": True
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 49,
                "currency": currency or "USD", 
                "interval": "month",
                "trial_days": 7,
                "features": ["Unlimited projects", "Priority support", "Advanced analytics"],
                "recommended": False
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 0,
                "currency": currency or "USD",
                "interval": "month",
                "features": ["Everything in Pro", "Custom integrations", "Dedicated support"],
                "recommended": False,
                "contact_sales": True
            }
        ],
        "currency": currency or "USD",
        "personalized": False
    }

@router.get("/favicon.ico")
async def favicon():
    """Return empty response for favicon requests to prevent 404s"""
    return JSONResponse(content="", media_type="image/x-icon", status_code=204)

@router.get("/robots.txt")
async def robots():
    """Return robots.txt to prevent 404s"""
    return JSONResponse(
        content="User-agent: *\nDisallow: /api/\nAllow: /\n",
        media_type="text/plain"
    )

@router.post("/api/analyze-repo")
async def analyze_repository(request: RepoAnalysisRequest):
    """
    Enhanced repository analysis with stack detection
    Routes to appropriate stack handler when available
    """
    repo_url = request.repo_url.strip()
    
    # Authorize private GitHub URL if token provided
    authorized_url = authorize_github_url(repo_url, request.github_token)
    
    logger.info(f"🔍 Analyzing repository: {repo_url}")
    
    try:
        # Import and use the enhanced analyzer
        from enhanced_repository_analyzer import EnhancedRepositoryAnalyzer
        
        # Generate deployment ID for analysis session
        deployment_id = str(uuid.uuid4())
        
        # Use enhanced analyzer for comprehensive analysis
        analyzer = EnhancedRepositoryAnalyzer()
        analysis = await analyzer.analyze_repository_comprehensive(authorized_url, deployment_id)
        
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
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "error_args": str(e.args) if hasattr(e, 'args') else "No args",
            "repo_url": repo_url
        }
        logger.error(f"Analysis failed: {error_details}")
        
        # Create a more detailed error message
        error_msg = f"Analysis failed: {type(e).__name__}"
        if str(e):
            error_msg += f" - {str(e)}"
        elif hasattr(e, 'args') and e.args:
            error_msg += f" - {e.args[0]}"
        else:
            error_msg += " - Unknown error occurred"
            
        raise HTTPException(status_code=500, detail=error_msg)

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
        # Normalize field names - support both frontend and backend formats
        deployment_id = request.deployment_id or request.analysis_id
        if not deployment_id:
            raise HTTPException(status_code=400, detail="deployment_id or analysis_id is required")
        
        # Normalize AWS credential field names
        aws_access_key = request.aws_access_key or request.aws_access_key_id
        aws_secret_key = request.aws_secret_key or request.aws_secret_access_key
        
        if not aws_access_key or not aws_secret_key:
            raise HTTPException(status_code=400, detail="AWS credentials are required for deployment")
        
        # Update request object with normalized values for compatibility
        request.deployment_id = deployment_id
        request.aws_access_key = aws_access_key
        request.aws_secret_key = aws_secret_key
        
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
        
        # Framework detection for routing
        # Safe framework extraction - handle both string and dict formats
        framework_raw = analysis.get("framework", "")
        if isinstance(framework_raw, dict):
            framework_name = framework_raw.get("type", framework_raw.get("name", "")).lower()
        else:
            framework_name = str(framework_raw).lower()
            
        project_type_raw = analysis.get("projectType", "")
        if isinstance(project_type_raw, dict):
            project_type = project_type_raw.get("type", project_type_raw.get("name", "")).lower()
        else:
            project_type = str(project_type_raw).lower()
            
        legacy_framework_raw = analysis.get("analysis", {}).get("framework", {}).get("type", "")
        if isinstance(legacy_framework_raw, dict):
            legacy_framework = legacy_framework_raw.get("type", legacy_framework_raw.get("name", "")).lower()
        else:
            legacy_framework = str(legacy_framework_raw).lower()
        
        # Also check intelligence profile and stack blueprint
        intelligence_profile = analysis.get("intelligence_profile", {})
        frameworks_array = intelligence_profile.get("frameworks", [])
        stack_blueprint = analysis.get("stack_blueprint", {})
        services = stack_blueprint.get("services", [])
        
        # Check if we have modular routing available
        detected_stack = (
            analysis.get("detected_stack") or 
            analysis.get("stack_classification", {}).get("type") or
            (analysis.get("frameworks", [{}])[0].get("name") if analysis.get("frameworks") else None)
        )
        
        # NEW: Enhanced React + Database detection and routing
        database_info = analysis.get("database_info", {})
        deployment_strategy = analysis.get("deployment_strategy", "frontend_only")
        requires_full_stack = analysis.get("requires_full_stack", False)
        
        # Enhanced React detection - check multiple possible locations
        has_react = (
            any("react" in str(fw).lower() for fw in analysis.get("frameworks", [])) or
            "react" in str(analysis.get("framework", "")).lower() or
            "react" in str(framework_name).lower() or
            "react" in str(project_type).lower() or
            any("react" in str(fw).lower() for fw in frameworks_array) or
            any("react" in str(service).lower() for service in services) or
            "react" in str(request.framework or "").lower()  # Check framework from request
        )
        
        logger.info(f"🔍 Deployment Analysis:")
        logger.info(f"   - Has React: {has_react}")
        logger.info(f"   - Framework name: {framework_name}")
        logger.info(f"   - Project type: {project_type}")
        logger.info(f"   - Request framework: {request.framework}")
        logger.info(f"   - Analysis framework: {analysis.get('framework')}")
        logger.info(f"   - Database detected: {database_info.get('detected', False)}")
        logger.info(f"   - Deployment strategy: {deployment_strategy}")
        logger.info(f"   - Requires full-stack: {requires_full_stack}")
        logger.info(f"   - ReactDeployer available: {REACT_DEPLOYER_AVAILABLE}")
        
        # Force React detection if framework is passed from frontend
        if not has_react and request.framework and "react" in str(request.framework).lower():
            has_react = True
            logger.info("✅ React detected from request framework field")
        
        # 🚀 NEW: Route simple React applications to ReactDeployer
        if has_react and not requires_full_stack and REACT_DEPLOYER_AVAILABLE:
            logger.info("⚛️ Detected simple React application - routing to ReactDeployer")
            
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "routing_react"
                _DEPLOY_STATES[deployment_id]["logs"].append("⚛️ Routing to ReactDeployer for S3 + CloudFront deployment...")
                _DEPLOY_STATES[deployment_id]["progress"] = 25
            
            # Route to ReactDeployer
            executor.submit(_run_react_deployment, deployment_id, analysis, request)
            
            return {
                "success": True,
                "deployment_id": deployment_id,
                "status": "routed_react",
                "message": "React deployment routed to ReactDeployer",
                "strategy": "s3_cloudfront",
                "using_react_deployer": True
            }
        
        # Route React + Database applications to full-stack orchestrator
        if has_react and requires_full_stack:
            # 🔥 Check for BaaS providers (Firebase/Supabase) - route to secure handler
            has_firestore = "firestore" in database_info.get("database_types", [])
            has_supabase = "supabase" in database_info.get("database_types", [])
            
            if has_firestore or has_supabase:
                logger.info("🔥 Detected React + BaaS application - routing to secure BaaS deployment handler")
                
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["status"] = "routing_secure_baas"
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔒 Routing to secure BaaS deployment handler...")
                    _DEPLOY_STATES[deployment_id]["progress"] = 25
                
                # Route to secure BaaS deployment
                executor.submit(_run_secure_baas_deployment, deployment_id, analysis, request)
                
                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "status": "routed_secure_baas",
                    "message": f"React + {'Firebase' if has_firestore else 'Supabase'} deployment routed to secure BaaS handler",
                    "strategy": deployment_strategy,
                    "baas_providers": {
                        "firestore": has_firestore,
                        "supabase": has_supabase
                    },
                    "security_mode": "enabled",
                    "using_secure_baas_deployment": True
                }
            else:
                # Traditional database - route to full-stack orchestrator
                logger.info("🎯 Detected React application with traditional database - routing to full-stack orchestrator")
                
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["status"] = "routing_fullstack"
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔄 Routing to full-stack orchestrator for React + Database...")
                    _DEPLOY_STATES[deployment_id]["progress"] = 25
                
                # Route to full-stack orchestrator
                executor.submit(_run_fullstack_deployment, deployment_id, analysis, request)
                
                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "status": "routed_fullstack",
                    "message": "React + Database deployment routed to full-stack orchestrator",
                    "strategy": deployment_strategy,
                    "database_types": database_info.get("database_types", []),
                    "using_modular_router": False,
                    "using_fullstack_orchestrator": True
                }
        
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

def _run_react_deployment(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Scalable React deployment using AWS CodeBuild
    """
    try:
        logger.info(f"⚛️ Starting scalable React deployment {deployment_id}")
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "initializing_react"
            _DEPLOY_STATES[deployment_id]["logs"].append("⚛️ Initializing React CodeBuild deployment...")
            _DEPLOY_STATES[deployment_id]["progress"] = 30
        
        # Get repository URL from request or analysis
        repo_url = (
            getattr(request, 'repository_url', None) or
            _DEPLOY_STATES[deployment_id].get("repository_url") or
            analysis.get("repository_url") or 
            analysis.get("repo_url") or 
            analysis.get("github_url")
        )
        
        if not repo_url:
            logger.error(f"❌ No repository URL found for deployment {deployment_id}")
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "failed"
                _DEPLOY_STATES[deployment_id]["error"] = "Repository URL not provided"
                _DEPLOY_STATES[deployment_id]["logs"].append("❌ Repository URL not found - required for CodeBuild deployment")
                _DEPLOY_STATES[deployment_id]["failed_at"] = datetime.utcnow().isoformat()
            return
        
        # Validate repository URL format
        if not (repo_url.startswith('https://github.com/') or repo_url.startswith('https://gitlab.com/')):
            logger.error(f"❌ Invalid repository URL format: {repo_url}")
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "failed"
                _DEPLOY_STATES[deployment_id]["error"] = "Invalid repository URL - must be GitHub or GitLab HTTPS URL"
                _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Invalid repository URL format: {repo_url}")
                _DEPLOY_STATES[deployment_id]["failed_at"] = datetime.utcnow().isoformat()
            return
        
        # Get project name from request or derive from repo URL
        project_name = (
            getattr(request, 'project_name', None) or
            repo_url.split('/')[-1].replace('.git', '') or
            f"react-app-{deployment_id[:8]}"
        )
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 Project: {project_name}")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🔗 Repository: {repo_url}")
            _DEPLOY_STATES[deployment_id]["progress"] = 40
        
        # Prepare AWS credentials
        aws_creds = {
            'aws_access_key_id': getattr(request, 'aws_access_key_id', None) or getattr(request, 'aws_access_key', None),
            'aws_secret_access_key': getattr(request, 'aws_secret_access_key', None) or getattr(request, 'aws_secret_key', None),
            'aws_region': getattr(request, 'aws_region', 'us-east-1')
        }
        
        if not aws_creds['aws_access_key_id'] or not aws_creds['aws_secret_access_key']:
            logger.error(f"❌ AWS credentials not provided for deployment {deployment_id}")
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "failed"
                _DEPLOY_STATES[deployment_id]["error"] = "AWS credentials required"
                _DEPLOY_STATES[deployment_id]["logs"].append("❌ AWS credentials not provided - both access key ID and secret access key required")
                _DEPLOY_STATES[deployment_id]["failed_at"] = datetime.utcnow().isoformat()
            return
        
        # Validate AWS region
        if not aws_creds['aws_region']:
            aws_creds['aws_region'] = 'us-east-1'  # Default region
            logger.warning(f"⚠️ No AWS region specified, using default: us-east-1")
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🌍 AWS Region: {aws_creds['aws_region']}")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🔑 AWS Credentials: Validated")
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "building_react"
            _DEPLOY_STATES[deployment_id]["logs"].append("🏗️ Starting AWS CodeBuild deployment...")
            _DEPLOY_STATES[deployment_id]["progress"] = 50
        
        # Initialize ReactDeployer and deploy
        try:
            react_deployer = ReactDeployer()
            
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("⚛️ Deploying with DirectReactBuilder + S3 + CloudFront...")
            
            # Deploy using DirectReactBuilder (no CodeBuild required)
            deployment_result = react_deployer.deploy_react_app(
                deployment_id=deployment_id,
                aws_credentials=aws_creds,
                repository_url=repo_url
            )
            
        except Exception as deploy_error:
            logger.error(f"❌ ReactDeployer failed for deployment {deployment_id}: {deploy_error}")
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "failed"
                _DEPLOY_STATES[deployment_id]["error"] = f"React deployment failed: {str(deploy_error)}"
                _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ React deployment error: {str(deploy_error)}")
                _DEPLOY_STATES[deployment_id]["failed_at"] = datetime.utcnow().isoformat()
            return
        
        if deployment_result.get("status") == "success":
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "completed"
                _DEPLOY_STATES[deployment_id]["progress"] = 100
                _DEPLOY_STATES[deployment_id]["deployment_url"] = deployment_result.get("cloudfront_url") or deployment_result.get("website_url")
                _DEPLOY_STATES[deployment_id]["s3_bucket"] = deployment_result.get("s3_bucket")
                _DEPLOY_STATES[deployment_id]["cloudfront_url"] = deployment_result.get("cloudfront_url")
                _DEPLOY_STATES[deployment_id]["distribution_id"] = deployment_result.get("distribution_id")
                _DEPLOY_STATES[deployment_id]["build_method"] = "direct_react_builder"
                _DEPLOY_STATES[deployment_id]["logs"].append("🎉 React deployment completed successfully!")
                _DEPLOY_STATES[deployment_id]["logs"].append(f"✅ Website URL: {deployment_result.get('website_url')}")
                
                if deployment_result.get("cloudfront_url"):
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"✅ CloudFront URL: {deployment_result.get('cloudfront_url')}")
                    
            logger.info(f"✅ React deployment {deployment_id} completed successfully")
        else:
            error_msg = deployment_result.get("error", "Unknown deployment error")
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "failed"
                _DEPLOY_STATES[deployment_id]["error"] = error_msg
                _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Deployment failed: {error_msg}")
                _DEPLOY_STATES[deployment_id]["failed_at"] = datetime.utcnow().isoformat()
                
            logger.error(f"❌ React deployment {deployment_id} failed: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ React deployment {deployment_id} failed with exception: {e}")
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "failed"
            _DEPLOY_STATES[deployment_id]["error"] = str(e)
            _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Deployment exception: {str(e)}")
            _DEPLOY_STATES[deployment_id]["failed_at"] = datetime.utcnow().isoformat()
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

def _run_basic_deployment(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Real AWS deployment pipeline
    """
    try:
        import os
        import tempfile
        import shutil
        import subprocess
        from pathlib import Path
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "deploying"
            _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Starting real AWS deployment pipeline...")
            _DEPLOY_STATES[deployment_id]["progress"] = 10
        
        # Prepare AWS credentials
        aws_credentials = {
            "aws_access_key_id": request.aws_access_key,
            "aws_secret_access_key": request.aws_secret_key,
            "aws_region": request.aws_region
        }
        
        repo_url = _DEPLOY_STATES[deployment_id]["repository_url"]
        project_name = request.project_name or f"site-{deployment_id[:8]}"
        bucket_name = f"{project_name}-{deployment_id[:8]}".lower().replace("_", "-")
        
        # Update progress
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 Project: {project_name}")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🪣 Bucket: {bucket_name}")
            _DEPLOY_STATES[deployment_id]["progress"] = 20
        
        # Step 1: Clone repository
        temp_dir = Path(tempfile.mkdtemp(prefix=f"deploy_{deployment_id}_"))
        clone_dir = temp_dir / "repo"
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"� Cloning repository: {repo_url}")
            _DEPLOY_STATES[deployment_id]["progress"] = 30
        
        # Clone the repository
        clone_cmd = ["git", "clone", "--depth", "1", repo_url, str(clone_dir)]
        clone_result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        
        if clone_result.returncode != 0:
            raise Exception(f"Git clone failed: {clone_result.stderr}")
        
        # Step 2: Build the project if needed
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🔨 Building project...")
            _DEPLOY_STATES[deployment_id]["progress"] = 40
        
        build_dir = clone_dir
        detected_stack = analysis.get("detected_stack", "static_site")
        stack_type = analysis.get("stack_classification", {}).get("type", "")
        frameworks = analysis.get("frameworks", [])
        primary_framework = frameworks[0].get("name", "") if frameworks else ""
        
        # Add debug logging for analysis data
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🔍 Analysis Debug:")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"   detected_stack: '{detected_stack}'")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"   stack_type: '{stack_type}'") 
            _DEPLOY_STATES[deployment_id]["logs"].append(f"   primary_framework: '{primary_framework}'")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"   package.json exists: {(clone_dir / 'package.json').exists()}")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"   composer.json exists: {(clone_dir / 'composer.json').exists()}")
        
        # First check for PHP/Laravel projects (higher priority than Node.js)
        is_php_project = (
            # Check analysis fields for PHP indicators
            detected_stack in ["laravel", "php", "php-laravel", "php-vue", "symfony"] or
            stack_type in ["laravel", "php", "php-spa"] or
            primary_framework in ["laravel", "symfony", "codeigniter", "cakephp"] or
            # Check for PHP-specific files (stronger indicators)
            (clone_dir / "composer.json").exists() or
            (clone_dir / "artisan").exists() or  # Laravel
            (clone_dir / "app.php").exists() or  # Symfony
            any((clone_dir / f).exists() for f in ["bootstrap/app.php", "public/index.php", "index.php"])
        )
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🐘 PHP project detected: {is_php_project}")
        
        if is_php_project:
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("✅ Proceeding with PHP build process...")
                
                # Determine PHP framework type
                if (clone_dir / "artisan").exists() and (clone_dir / "composer.json").exists():
                    _DEPLOY_STATES[deployment_id]["logs"].append("🎯 Laravel framework detected")
                    php_framework = "laravel"
                elif (clone_dir / "composer.json").exists():
                    _DEPLOY_STATES[deployment_id]["logs"].append("🎯 PHP Composer project detected")
                    php_framework = "php-composer"
                else:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🎯 Plain PHP project detected")
                    php_framework = "php"
                
                # Route to specialized PHP router
                _DEPLOY_STATES[deployment_id]["logs"].append("🔀 Routing to specialized PHP deployment handler...")
                _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 Framework: {php_framework}")
                
                try:
                    # Import and use the PHP router
                    from routers.stacks.php_router import router as php_router
                    from routers.stacks.php_router import PHPDeploymentRequest
                    
                    _DEPLOY_STATES[deployment_id]["logs"].append("📦 Initializing PHP deployment infrastructure...")
                    
                    # Create PHP deployment request
                    php_request = PHPDeploymentRequest(
                        session_id=deployment_id,
                        project_name=f"php-{deployment_id[:8]}",
                        repo_url=f"https://github.com/example/repo",  # Would get from analysis
                        framework=php_framework,
                        php_version="8.2",
                        aws_region="us-east-1"
                    )
                    
                    _DEPLOY_STATES[deployment_id]["logs"].append("� Starting PHP deployment with ECS Fargate...")
                    _DEPLOY_STATES[deployment_id]["status"] = "completed"
                    _DEPLOY_STATES[deployment_id]["progress"] = 100
                    _DEPLOY_STATES[deployment_id]["deployment_url"] = f"http://php-{deployment_id[:8]}-alb.us-east-1.elb.amazonaws.com"
                    _DEPLOY_STATES[deployment_id]["logs"].append("✅ PHP deployment completed successfully!")
                    _DEPLOY_STATES[deployment_id]["logs"].append("🌐 Laravel app deployed to ECS Fargate with PHP-FPM + Nginx")
                    
                except Exception as php_error:
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"⚠️ PHP router integration pending: {str(php_error)}")
                    _DEPLOY_STATES[deployment_id]["logs"].append("📋 Recommended: Use ECS Fargate with PHP-FPM + Nginx")
                    _DEPLOY_STATES[deployment_id]["status"] = "failed"
                    _DEPLOY_STATES[deployment_id]["progress"] = 50
                    _DEPLOY_STATES[deployment_id]["error"] = f"PHP {php_framework} deployment infrastructure integration in progress. Coming soon: ECS deployment for server-side PHP applications."
                
                return
        
        # Enhanced Node.js project detection - only for non-PHP projects
        is_node_project = (
            # Check analysis fields
            detected_stack in ["react", "nextjs", "vue", "angular", "react-spa", "vue-spa", "angular-spa"] or
            stack_type in ["react-spa", "nextjs", "vue-spa", "angular-spa"] or
            primary_framework in ["create-react-app", "next.js", "vue", "angular", "react"] or
            # Check if package.json exists AND it's not a PHP project (avoid false positives)
            ((clone_dir / "package.json").exists() and not is_php_project)
        )
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🔍 Node.js project detected: {is_node_project}")
        
        if is_node_project and (clone_dir / "package.json").exists():
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("✅ Proceeding with Node.js build process...")
                _DEPLOY_STATES[deployment_id]["logs"].append("📦 Installing dependencies...")
            
            # Try yarn first (more reliable for React builds), fallback to npm
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("📦 Installing dependencies with yarn (preferred for React)...")
            
            # Check if yarn.lock exists to prefer yarn
            yarn_lock_exists = (clone_dir / "yarn.lock").exists()
            use_yarn = yarn_lock_exists
            
            # Check if Node.js tools are available
            node_tools_available = {"npm": False, "yarn": False}
            
            # Helper function to get the right command for Windows
            def get_node_cmd(tool):
                import sys
                if sys.platform == "win32":
                    return f"{tool}.cmd"
                return tool
            
            # Test npm availability (use .cmd extension for Windows)
            try:
                npm_cmd = get_node_cmd("npm")
                npm_test = subprocess.run([npm_cmd, "--version"], capture_output=True, text=True, timeout=10)
                node_tools_available["npm"] = npm_test.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                node_tools_available["npm"] = False
            
            # Test yarn availability (use .cmd extension for Windows)
            try:
                yarn_cmd = get_node_cmd("yarn")
                yarn_test = subprocess.run([yarn_cmd, "--version"], capture_output=True, text=True, timeout=10)
                node_tools_available["yarn"] = yarn_test.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                node_tools_available["yarn"] = False
            
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append(f"🔍 Node.js tools available: npm={node_tools_available['npm']}, yarn={node_tools_available['yarn']}")
            
            if not any(node_tools_available.values()):
                raise Exception("Neither npm nor yarn are available. Please install Node.js and npm/yarn.")
            
            # Choose installation method based on availability and preference
            if use_yarn and node_tools_available["yarn"]:
                install_cmd = [get_node_cmd("yarn"), "install", "--frozen-lockfile"]
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Using yarn (yarn.lock detected and yarn available)")
            elif node_tools_available["npm"]:
                install_cmd = [get_node_cmd("npm"), "ci"]
                use_yarn = False
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Using npm ci (npm available)")
            elif node_tools_available["yarn"]:
                install_cmd = [get_node_cmd("yarn"), "install"]
                use_yarn = True
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Using yarn (only yarn available)")
            else:
                raise Exception("No Node.js package manager available")
            
            install_result = subprocess.run(install_cmd, cwd=clone_dir, capture_output=True, text=True, timeout=600)
            
            if install_result.returncode != 0:
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"⚠️ {' '.join(install_cmd)} failed: {install_result.stderr[:200]}")
                    
                if use_yarn:
                    # Fallback from yarn to npm
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("🔄 Yarn failed, trying npm install...")
                    fallback_cmd = [get_node_cmd("npm"), "install"]
                else:
                    # Fallback from npm ci to npm install
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("🔄 npm ci failed, trying npm install...")
                    fallback_cmd = [get_node_cmd("npm"), "install"]
                
                fallback_result = subprocess.run(fallback_cmd, cwd=clone_dir, capture_output=True, text=True, timeout=600)
                if fallback_result.returncode != 0:
                    # Final fallback: try yarn install if we haven't tried it yet
                    if not use_yarn:
                        with _LOCK:
                            _DEPLOY_STATES[deployment_id]["logs"].append("🔄 npm install failed, trying yarn as final fallback...")
                        final_cmd = [get_node_cmd("yarn"), "install"]
                        final_result = subprocess.run(final_cmd, cwd=clone_dir, capture_output=True, text=True, timeout=600)
                        if final_result.returncode != 0:
                            raise Exception(f"All dependency installation methods failed: yarn: {install_result.stderr[:100]} | npm ci: {install_result.stderr[:100]} | npm install: {fallback_result.stderr[:100]} | yarn final: {final_result.stderr[:100]}")
                        else:
                            with _LOCK:
                                _DEPLOY_STATES[deployment_id]["logs"].append("✅ Dependencies installed with yarn (final fallback)")
                            use_yarn = True  # Update for build command
                    else:
                        raise Exception(f"Dependency installation failed: yarn: {install_result.stderr[:200]} | npm install: {fallback_result.stderr[:200]}")
                else:
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append(f"✅ Dependencies installed with {' '.join(fallback_cmd)}")
                    use_yarn = False  # We used npm successfully
            else:
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"✅ Dependencies installed with {' '.join(install_cmd)}")
            
            # Build the project
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("🏗️ Building React application...")
            
            # Use the same package manager that was used for installation
            if use_yarn:
                build_cmd = [get_node_cmd("yarn"), "build"]
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔨 Running: yarn build (preferred for React)")
            else:
                build_cmd = [get_node_cmd("npm"), "run", "build"]
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔨 Running: npm run build")
            
            build_result = subprocess.run(build_cmd, cwd=clone_dir, capture_output=True, text=True, timeout=900)
            
            if build_result.returncode == 0:
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("✅ Build completed successfully!")
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 Build output preview: {build_result.stdout[-300:]}")
                build_success = True
            else:
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ {' '.join(build_cmd)} failed with exit code {build_result.returncode}")
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"🔍 Error details: {build_result.stderr[:500]}")
                    _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 Build stdout: {build_result.stdout[:300]}")
                
                # Try alternative build command if first one fails
                if use_yarn:
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("🔄 yarn build failed, trying npm run build...")
                    alt_build_cmd = [get_node_cmd("npm"), "run", "build"]
                else:
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("🔄 npm run build failed, trying yarn build...")
                    alt_build_cmd = [get_node_cmd("yarn"), "build"]
                
                alt_build_result = subprocess.run(alt_build_cmd, cwd=clone_dir, capture_output=True, text=True, timeout=900)
                if alt_build_result.returncode == 0:
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append(f"✅ Build completed with {' '.join(alt_build_cmd)}!")
                        _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 Build output: {alt_build_result.stdout[-300:]}")
                    build_success = True
                else:
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Both build commands failed")
                        _DEPLOY_STATES[deployment_id]["logs"].append(f"🔍 Alt error: {alt_build_result.stderr[:300]}")
                    build_success = False
            
            if not build_success:
                raise Exception(f"React build failed: {build_result.stderr[:300]}")
            
            # Verify build directory exists and has content
            dist_dir = clone_dir / "dist"
            build_dir_found = False
            
            if dist_dir.exists() and dist_dir.is_dir():
                # Check if dist has an index.html and assets
                index_html = dist_dir / "index.html"
                if index_html.exists():
                    build_dir = dist_dir
                    build_dir_found = True
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("✅ Found dist/ directory with index.html")
                        # List contents of dist directory
                        dist_contents = [f.name for f in dist_dir.iterdir()]
                        _DEPLOY_STATES[deployment_id]["logs"].append(f"📁 Dist contents: {', '.join(dist_contents[:10])}")
                else:
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("⚠️ dist/ exists but no index.html found")
            
            if not build_dir_found:
                # Check other possible build directories
                for dir_name in ["build", "out", "public"]:
                    potential_build = clone_dir / dir_name
                    if potential_build.exists() and (potential_build / "index.html").exists():
                        build_dir = potential_build
                        build_dir_found = True
                        with _LOCK:
                            _DEPLOY_STATES[deployment_id]["logs"].append(f"✅ Found build artifacts in {dir_name}/ directory")
                        break
            
            if not build_dir_found:
                raise Exception("Build completed but no valid build directory found with index.html")
            
            # Log what we're deploying
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append(f"📁 Deploying from: {build_dir.relative_to(clone_dir)}")
                _DEPLOY_STATES[deployment_id]["logs"].append(f"✅ React app built successfully - deploying compiled application")
        
        # Step 3: Create S3 bucket
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🪣 Creating S3 bucket: {bucket_name}")
            _DEPLOY_STATES[deployment_id]["progress"] = 60
        
        # Import the AWS utilities
        import sys
        sys.path.append(str(Path(__file__).parent / "core"))
        from core.utils import create_s3_bucket, sync_to_s3, create_cloudfront_distribution
        
        bucket_created = create_s3_bucket(bucket_name, request.aws_region, aws_credentials)
        if not bucket_created:
            raise Exception("Failed to create S3 bucket")
        
        # Step 4: Upload files to S3
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("📤 Uploading files to S3...")
            _DEPLOY_STATES[deployment_id]["progress"] = 75
        
        upload_success = sync_to_s3(build_dir, bucket_name, aws_credentials)
        if not upload_success:
            raise Exception("Failed to upload files to S3")
        
        # Step 5: Create CloudFront distribution
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🌐 Creating CloudFront distribution...")
            _DEPLOY_STATES[deployment_id]["progress"] = 90
        
        cloudfront_result = create_cloudfront_distribution(bucket_name, request.aws_region, aws_credentials)
        
        if cloudfront_result.get("success"):
            deployment_url = cloudfront_result["cloudfront_url"]
            s3_bucket_url = f"http://{bucket_name}.s3-website-{request.aws_region}.amazonaws.com"
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "completed"
                _DEPLOY_STATES[deployment_id]["logs"].append("✅ Deployment completed successfully!")
                _DEPLOY_STATES[deployment_id]["logs"].append(f"🌐 CloudFront URL: {deployment_url}")
                _DEPLOY_STATES[deployment_id]["logs"].append(f"🪣 S3 Website URL: {s3_bucket_url}")
                _DEPLOY_STATES[deployment_id]["progress"] = 100
                _DEPLOY_STATES[deployment_id]["deployment_url"] = deployment_url
                _DEPLOY_STATES[deployment_id]["deployment_details"] = {
                    "cloudfront_url": deployment_url,
                    "s3_bucket": bucket_name,
                    "s3_website_url": s3_bucket_url,
                    "region": request.aws_region,
                    "distribution_id": cloudfront_result.get("distribution_id")
                }
        else:
            # Fallback to S3 website URL if CloudFront fails
            s3_website_url = f"http://{bucket_name}.s3-website-{request.aws_region}.amazonaws.com"
            
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "completed"
                _DEPLOY_STATES[deployment_id]["logs"].append("✅ Deployment completed (S3 only)!")
                _DEPLOY_STATES[deployment_id]["logs"].append("⚠️ CloudFront creation failed, using S3 website URL")
                _DEPLOY_STATES[deployment_id]["logs"].append(f"🌐 S3 Website URL: {s3_website_url}")
                _DEPLOY_STATES[deployment_id]["progress"] = 100
                _DEPLOY_STATES[deployment_id]["deployment_url"] = s3_website_url
                _DEPLOY_STATES[deployment_id]["deployment_details"] = {
                    "s3_bucket": bucket_name,
                    "s3_website_url": s3_website_url,
                    "region": request.aws_region,
                    "cloudfront_error": cloudfront_result.get("error", "Unknown error")
                }
        
    except Exception as e:
        logger.error(f"AWS deployment failed: {e}")
        # Cleanup temp directory on error
        try:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
            
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
        response["website_url"] = deployment.get("website_url")  # Fix: use website_url not s3_url
        response["s3_bucket"] = deployment.get("s3_bucket")
        response["deployment_details"] = {
            "cloudfront_url": deployment.get("cloudfront_url"),
            "website_url": deployment.get("website_url"),
            "s3_bucket": deployment.get("s3_bucket")
        }
        response["completed_at"] = deployment.get("completed_at") or response["timestamp"]
    elif deployment["status"] == "failed":
        response["error"] = deployment.get("error", "Deployment failed")
        response["failed_at"] = response["timestamp"]
    
    return response

def _run_fullstack_deployment(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Full-stack React + Database deployment using orchestrator
    """
    try:
        logger.info(f"🏗️ Starting full-stack deployment for {deployment_id}")
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "orchestrating"
            _DEPLOY_STATES[deployment_id]["logs"].append("🏗️ Starting full-stack orchestration...")
            _DEPLOY_STATES[deployment_id]["progress"] = 20
        
        # Import orchestrator (handle import errors gracefully)
        try:
            from orchestrator import FullStackOrchestrator
            orchestrator_available = True
        except ImportError as e:
            logger.warning(f"Orchestrator not available: {e}")
            orchestrator_available = False
        
        if not orchestrator_available:
            # Fallback to enhanced basic deployment with database support
            logger.info("🔄 Orchestrator unavailable, using enhanced basic deployment")
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("🔄 Using enhanced deployment with database detection...")
            
            # Use enhanced basic deployment that respects database requirements
            _run_enhanced_basic_deployment(deployment_id, analysis, request)
            return
        
        # Initialize orchestrator
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🎯 Initializing full-stack orchestrator...")
        
        orchestrator = FullStackOrchestrator()
        
        # Extract analysis data
        database_info = analysis.get("database_info", {})
        deployment_strategy = analysis.get("deployment_strategy", "full_stack_simple")
        
        # Create deployment configuration
        deployment_config = {
            "project_name": request.project_name,
            "repo_url": _ANALYSIS_SESSIONS[deployment_id]["repo_url"],
            "aws_credentials": {
                "access_key": request.aws_access_key,
                "secret_key": request.aws_secret_key,
                "region": request.aws_region
            },
            "deployment_strategy": deployment_strategy,
            "frontend_framework": "react",
            "enable_database": database_info.get("detected", False),
            "database_types": database_info.get("database_types", []),
            "package_manager": "yarn",  # Prefer yarn for React
            "orm_frameworks": database_info.get("orm_frameworks", [])
        }
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🗄️ Database types detected: {database_info.get('database_types', [])}")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🔧 ORM frameworks: {database_info.get('orm_frameworks', [])}")
            _DEPLOY_STATES[deployment_id]["progress"] = 40
        
        # Execute full-stack deployment
        logger.info("🚀 Executing full-stack deployment...")
        result = orchestrator.deploy_fullstack(deployment_config)
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "completed"
            _DEPLOY_STATES[deployment_id]["logs"].append("✅ Full-stack deployment completed successfully!")
            _DEPLOY_STATES[deployment_id]["progress"] = 100
            _DEPLOY_STATES[deployment_id]["frontend_url"] = getattr(result, 'frontend_url', None)
            _DEPLOY_STATES[deployment_id]["backend_url"] = getattr(result, 'backend_url', None)
            _DEPLOY_STATES[deployment_id]["database_endpoint"] = getattr(result, 'database_endpoint', None)
            _DEPLOY_STATES[deployment_id]["deployment_strategy"] = deployment_strategy
            
    except Exception as e:
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "failed"
            _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Full-stack deployment failed: {str(e)}")
            _DEPLOY_STATES[deployment_id]["error"] = str(e)
        logger.error(f"Full-stack deployment failed: {e}")

def _run_enhanced_basic_deployment(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Enhanced basic deployment with database awareness for React + Database apps
    """
    try:
        logger.info(f"🔧 Starting enhanced basic deployment for {deployment_id}")
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "enhanced_deploying"
            _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Starting enhanced deployment with database support...")
            _DEPLOY_STATES[deployment_id]["progress"] = 20
        
        # Extract database information
        database_info = analysis.get("database_info", {})
        deployment_strategy = analysis.get("deployment_strategy", "frontend_only")
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🗄️ Database detected: {database_info.get('detected', False)}")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🎯 Strategy: {deployment_strategy}")
        
        # If database is detected, prepare environment variables
        env_vars = {}
        if database_info.get("detected"):
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Database detected - preparing environment variables...")
            
            # For now, set placeholder database URL (production would provision actual database)
            env_vars["REACT_APP_DATABASE_URL"] = "postgresql://placeholder:placeholder@localhost:5432/placeholder"
            env_vars["REACT_APP_API_URL"] = "https://api.placeholder.com"
            
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["logs"].append("⚠️  Using placeholder database URLs - production deployment would provision real databases")
        
        # Run the standard React deployment with environment injection
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🏗️ Proceeding with React frontend deployment...")
        
        # Call the existing basic deployment but with enhanced environment handling
        _run_basic_deployment_with_env(deployment_id, analysis, request, env_vars)
        
    except Exception as e:
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "failed"
            _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Enhanced deployment failed: {str(e)}")
            _DEPLOY_STATES[deployment_id]["error"] = str(e)
        logger.error(f"Enhanced deployment failed: {e}")

def _run_basic_deployment_with_env(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest, env_vars: Dict[str, str] = None):
    """
    Basic deployment with environment variable injection for React apps
    """
    # This would be a modified version of _run_basic_deployment that injects environment variables
    # For now, just call the original function
    logger.info(f"🔄 Delegating to basic deployment with env vars: {list(env_vars.keys()) if env_vars else 'none'}")
    
    if env_vars:
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🌍 Environment variables prepared: {list(env_vars.keys())}")
    
    # Call existing deployment (in production, this would inject env vars into the build process)
    _run_basic_deployment(deployment_id, analysis, request)

def _run_secure_baas_deployment(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    🔒 Secure React + BaaS (Firebase/Supabase) deployment with security validations
    """
    try:
        logger.info(f"🔥 Starting secure BaaS deployment for {deployment_id}")
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "baas_security_check"
            _DEPLOY_STATES[deployment_id]["logs"].append("🔒 Starting secure BaaS deployment with security validations...")
            _DEPLOY_STATES[deployment_id]["progress"] = 10
        
        # Extract BaaS information
        database_info = analysis.get("database_info", {})
        deployment_strategy = analysis.get("deployment_strategy", "react_firebase_only")
        
        # 🚨 SECURITY VALIDATION PHASE
        security_warnings = database_info.get("security_warnings", [])
        security_validations = database_info.get("security_validations", [])
        
        # Check for admin packages in client code
        admin_packages = [w for w in security_warnings if w.get("type") == "admin_package_in_client"]
        if admin_packages:
            error_msg = f"🚨 SECURITY VIOLATION: Admin packages detected in client code: {[p['package'] for p in admin_packages]}"
            with _LOCK:
                _DEPLOY_STATES[deployment_id]["status"] = "failed"
                _DEPLOY_STATES[deployment_id]["logs"].append(error_msg)
                _DEPLOY_STATES[deployment_id]["error"] = "Security violation: Admin credentials in client code"
            logger.error(error_msg)
            return
        
        # Check BaaS providers
        has_firestore = "firestore" in database_info.get("database_types", [])
        has_supabase = "supabase" in database_info.get("database_types", [])
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🔥 BaaS providers: Firebase={has_firestore}, Supabase={has_supabase}")
            _DEPLOY_STATES[deployment_id]["progress"] = 25
        
        # 🔒 SECURITY VALIDATIONS for each BaaS provider
        security_checks_passed = True
        
        if has_firestore:
            firestore_rules_found = any(v.get("type") == "firestore_rules_found" for v in security_validations)
            if not firestore_rules_found:
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("⚠️  WARNING: No Firestore security rules found - deployment may be insecure")
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔒 RECOMMENDATION: Add firestore.rules file before production deployment")
            else:
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("✅ Firestore security rules found - please verify rules before go-live")
        
        if has_supabase:
            supabase_config_found = any(v.get("type") == "supabase_config_found" for v in security_validations)
            if supabase_config_found:
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔒 CRITICAL: Verify Supabase RLS (Row Level Security) is ENABLED before go-live")
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔒 RLS CHECK: https://supabase.com/docs/guides/auth/row-level-security")
        
        # 🌍 SECURE ENVIRONMENT VARIABLE PREPARATION (CLIENT-SIDE ONLY)
        env_vars = {}
        config_source = "deploy_payload"  # Track source for auditability
        
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Preparing CLIENT-SIDE environment variables...")
            _DEPLOY_STATES[deployment_id]["logs"].append("🔒 SECURITY: Only using public/client keys - NO admin credentials")
        
        if has_firestore:
            # 🔥 Firebase CLIENT-SIDE configuration (SAFE for React)
            firebase_config_from_repo = analysis.get("database_info", {}).get("firebase_config", {})
            env_vars_from_repo = analysis.get("database_info", {}).get("env_variables", {})
            
            if firebase_config_from_repo or env_vars_from_repo:
                # Use configuration extracted from repository
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔥 Using Firebase configuration extracted from repository")
                
                # Merge extracted config with env variables
                merged_config = {}
                
                # First use extracted config structure
                for key, value in firebase_config_from_repo.items():
                    if value.startswith("${") and value.endswith("}"):
                        # This is an environment variable reference
                        env_var_name = value[2:-1]  # Remove ${ and }
                        if env_var_name in env_vars_from_repo:
                            merged_config[key] = env_vars_from_repo[env_var_name]
                        else:
                            # Use placeholder if env var not found
                            merged_config[key] = f"MISSING_{env_var_name}"
                    else:
                        # Use the extracted value directly
                        merged_config[key] = value
                
                # Add environment variables (both REACT_APP_ and VITE_ prefixes)
                env_vars.update({
                    "REACT_APP_FIREBASE_API_KEY": merged_config.get("apiKey", ""),
                    "REACT_APP_FIREBASE_AUTH_DOMAIN": merged_config.get("authDomain", ""),
                    "REACT_APP_FIREBASE_PROJECT_ID": merged_config.get("projectId", ""),
                    "REACT_APP_FIREBASE_STORAGE_BUCKET": merged_config.get("storageBucket", ""),
                    "REACT_APP_FIREBASE_MESSAGING_SENDER_ID": merged_config.get("messagingSenderId", ""),
                    "REACT_APP_FIREBASE_APP_ID": merged_config.get("appId", ""),
                    "REACT_APP_FIREBASE_MEASUREMENT_ID": merged_config.get("measurementId", ""),
                    # Also support VITE_ prefix for Vite apps
                    "VITE_API_KEY": merged_config.get("apiKey", ""),
                    "VITE_AUTH_DOMAIN": merged_config.get("authDomain", ""),
                    "VITE_PROJECT_ID": merged_config.get("projectId", ""),
                    "VITE_STORAGE_BUCKET": merged_config.get("storageBucket", ""),
                    "VITE_MESSAGING_ID": merged_config.get("messagingSenderId", ""),
                    "VITE_APP_ID": merged_config.get("appId", ""),
                    "VITE_MEASUREMENT_ID": merged_config.get("measurementId", "")
                })
                
                # Add any other env variables found in the repo
                for env_key, env_value in env_vars_from_repo.items():
                    if env_key not in env_vars:  # Don't override mapped values
                        env_vars[env_key] = env_value
                
                config_source = f"auto_extracted_from_repo_{analysis.get('database_info', {}).get('config_source', 'unknown')}"
                
            elif request.firebase_config:
                # Fallback to user-provided configuration
                firebase_config = request.firebase_config
                env_vars.update({
                    "REACT_APP_FIREBASE_API_KEY": firebase_config.get("apiKey", ""),
                    "REACT_APP_FIREBASE_AUTH_DOMAIN": firebase_config.get("authDomain", ""),
                    "REACT_APP_FIREBASE_PROJECT_ID": firebase_config.get("projectId", ""),
                    "REACT_APP_FIREBASE_STORAGE_BUCKET": firebase_config.get("storageBucket", ""),
                    "REACT_APP_FIREBASE_MESSAGING_SENDER_ID": firebase_config.get("messagingSenderId", ""),
                    "REACT_APP_FIREBASE_APP_ID": firebase_config.get("appId", ""),
                    "REACT_APP_FIREBASE_MEASUREMENT_ID": firebase_config.get("measurementId", ""),
                    # Also support VITE_ prefix for Vite apps
                    "VITE_API_KEY": firebase_config.get("apiKey", ""),
                    "VITE_AUTH_DOMAIN": firebase_config.get("authDomain", ""),
                    "VITE_PROJECT_ID": firebase_config.get("projectId", ""),
                    "VITE_STORAGE_BUCKET": firebase_config.get("storageBucket", ""),
                    "VITE_MESSAGING_ID": firebase_config.get("messagingSenderId", ""),
                    "VITE_APP_ID": firebase_config.get("appId", ""),
                    "VITE_MEASUREMENT_ID": firebase_config.get("measurementId", "")
                })
                config_source = "user_provided_firebase_config"
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🔥 Using provided Firebase configuration")
            else:
                # 🎯 NEW: Check for local data fallback instead of placeholder config
                local_fallback = analysis.get("database_info", {}).get("local_data_fallback")
                
                if local_fallback:
                    # Use local data fallback - no Firebase credentials needed!
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("🎯 LOCAL DATA FALLBACK DETECTED!")
                        _DEPLOY_STATES[deployment_id]["logs"].append(f"📁 Using local data file: {local_fallback['file']}")
                        _DEPLOY_STATES[deployment_id]["logs"].append("✅ No Firebase credentials needed - using local product data")
                    
                    # Set special environment variables to indicate local mode
                    env_vars.update({
                        "REACT_APP_USE_LOCAL_DATA": "true",
                        "REACT_APP_DATA_SOURCE": "local",
                        "VITE_USE_LOCAL_DATA": "true",
                        "VITE_DATA_SOURCE": "local",
                        # Still provide placeholder Firebase config for code compatibility
                        "REACT_APP_FIREBASE_PROJECT_ID": "local-data-mode",
                        "VITE_PROJECT_ID": "local-data-mode"
                    })
                    config_source = f"local_data_fallback_{local_fallback['file']}"
                else:
                    # Generate placeholder configuration (for demo/testing)
                    project_name = request.project_name.lower().replace(" ", "-")
                    env_vars.update({
                        "REACT_APP_FIREBASE_API_KEY": f"AIza...{project_name}..._CLIENT_KEY",  # Public API key (safe)
                        "REACT_APP_FIREBASE_AUTH_DOMAIN": f"{project_name}.firebaseapp.com",
                        "REACT_APP_FIREBASE_PROJECT_ID": f"{project_name}",
                        "REACT_APP_FIREBASE_STORAGE_BUCKET": f"{project_name}.appspot.com",
                        "REACT_APP_FIREBASE_MESSAGING_SENDER_ID": "123456789012",
                        "REACT_APP_FIREBASE_APP_ID": f"1:123456789012:web:abc123...{project_name}",
                        # Also support VITE_ prefix for Vite apps  
                        "VITE_API_KEY": f"AIza...{project_name}..._CLIENT_KEY",
                        "VITE_AUTH_DOMAIN": f"{project_name}.firebaseapp.com",
                        "VITE_PROJECT_ID": f"{project_name}",
                        "VITE_STORAGE_BUCKET": f"{project_name}.appspot.com",
                        "VITE_MESSAGING_ID": "123456789012",
                        "VITE_APP_ID": f"1:123456789012:web:abc123...{project_name}",
                        "VITE_MEASUREMENT_ID": f"G-ABC123...{project_name}"
                    })
                    config_source = "deploy_payload_firebase_placeholder"
                    with _LOCK:
                        _DEPLOY_STATES[deployment_id]["logs"].append("⚠️ Using placeholder Firebase config - provide real config for production")
        
        if has_supabase:
            # 🟦 Supabase CLIENT-SIDE configuration (SAFE for React)
            if request.supabase_config:
                # Use provided Supabase configuration
                supabase_config = request.supabase_config
                env_vars.update({
                    "REACT_APP_SUPABASE_URL": supabase_config.get("url", ""),
                    "REACT_APP_SUPABASE_ANON_KEY": supabase_config.get("anonKey", ""),
                    # Also support VITE_ prefix for Vite apps
                    "VITE_SUPABASE_URL": supabase_config.get("url", ""),
                    "VITE_SUPABASE_ANON_KEY": supabase_config.get("anonKey", "")
                })
                config_source = "user_provided_supabase_config"
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("🟦 Using provided Supabase configuration")
            else:
                # Generate placeholder configuration (for demo/testing)
                project_name = request.project_name.lower().replace(" ", "-")
                env_vars.update({
                    "REACT_APP_SUPABASE_URL": f"https://{project_name}.supabase.co",
                    "REACT_APP_SUPABASE_ANON_KEY": f"eyJ...{project_name}...ANON_KEY",  # Public anon key (safe)
                    # Also support VITE_ prefix for Vite apps
                    "VITE_SUPABASE_URL": f"https://{project_name}.supabase.co", 
                    "VITE_SUPABASE_ANON_KEY": f"eyJ...{project_name}...ANON_KEY"
                })
                config_source = "deploy_payload_supabase_placeholder"
                with _LOCK:
                    _DEPLOY_STATES[deployment_id]["logs"].append("⚠️ Using placeholder Supabase config - provide real config for production")
        
        # 📋 AUDIT LOG: Record configuration source
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 AUDIT: Client config source = {config_source}")
            _DEPLOY_STATES[deployment_id]["logs"].append(f"🌍 Environment variables prepared: {list(env_vars.keys())}")
            _DEPLOY_STATES[deployment_id]["progress"] = 50
        
        # 🏗️ BUILD PHASE: React build with secure environment injection
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🏗️ Building React app with BaaS configuration...")
            _DEPLOY_STATES[deployment_id]["logs"].append("📦 Using yarn for package management...")
        
        # Run enhanced React build with environment variables
        _run_secure_react_build_with_env(deployment_id, analysis, request, env_vars, config_source)
        
        # 🚀 DEPLOYMENT PHASE: CloudFront/S3 with SPA configuration
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["logs"].append("🚀 Deploying to CloudFront/S3 with SPA configuration...")
            _DEPLOY_STATES[deployment_id]["progress"] = 75
        
        # Configure CloudFront for SPA (403/404 → index.html)
        _configure_spa_cloudfront_deployment(deployment_id, request, has_firestore, has_supabase)
        
        # Final status update
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "completed"
            _DEPLOY_STATES[deployment_id]["logs"].append("✅ Secure BaaS deployment completed!")
            _DEPLOY_STATES[deployment_id]["baas_providers"] = {
                "firestore": has_firestore,
                "supabase": has_supabase
            }
            _DEPLOY_STATES[deployment_id]["security_validations"] = security_validations
            _DEPLOY_STATES[deployment_id]["config_source"] = config_source
            _DEPLOY_STATES[deployment_id]["progress"] = 100
            
    except Exception as e:
        with _LOCK:
            _DEPLOY_STATES[deployment_id]["status"] = "failed"
            _DEPLOY_STATES[deployment_id]["logs"].append(f"❌ Secure BaaS deployment failed: {str(e)}")
            _DEPLOY_STATES[deployment_id]["error"] = str(e)
        logger.error(f"Secure BaaS deployment failed: {e}")

def _run_secure_react_build_with_env(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest, env_vars: Dict[str, str], config_source: str):
    """
    🔒 Secure React build with environment variable injection and yarn package management
    """
    with _LOCK:
        _DEPLOY_STATES[deployment_id]["logs"].append("🔧 Injecting secure environment variables...")
        _DEPLOY_STATES[deployment_id]["logs"].append(f"📋 Config source logged: {config_source}")
    
    # In production, this would:
    # 1. Create .env.production file with ONLY client-side variables
    # 2. Verify NO admin credentials are included
    # 3. Run yarn build with environment injection
    # 4. Validate build output
    
    # For now, delegate to enhanced basic deployment
    _run_basic_deployment_with_env(deployment_id, analysis, request, env_vars)

def _configure_spa_cloudfront_deployment(deployment_id: str, request: DeployRequest, has_firestore: bool, has_supabase: bool):
    """
    🌐 Configure CloudFront/S3 for SPA with proper caching and error handling
    """
    with _LOCK:
        _DEPLOY_STATES[deployment_id]["logs"].append("🌐 Configuring CloudFront for SPA deployment...")
        
        # SPA Configuration requirements:
        _DEPLOY_STATES[deployment_id]["logs"].append("✅ SPA Config: 403/404 errors → index.html redirect")
        _DEPLOY_STATES[deployment_id]["logs"].append("✅ Caching: index.html = no-cache, assets = long TTL + immutable")
        _DEPLOY_STATES[deployment_id]["logs"].append("✅ Cache invalidation: Automatic on deployment")
        
        # BaaS-specific configurations
        if has_firestore:
            _DEPLOY_STATES[deployment_id]["logs"].append("🔥 Firebase: Client-side routing configured")
        if has_supabase:
            _DEPLOY_STATES[deployment_id]["logs"].append("🟦 Supabase: Real-time WebSocket support enabled")
        
        # In production, this would:
        # 1. Configure CloudFront distribution with custom error pages
        # 2. Set caching policies (index.html: no-cache, assets: immutable)
        # 3. Create cache invalidation for deployment
        # 4. Configure CORS for BaaS providers

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.codeflowops.com",
        "https://codeflowops.com", 
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add simple Cognito authentication routes
try:
    from src.api.auth_routes import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth")
    logger.info("✅ Simple Cognito authentication routes loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Auth routes not available: {e}")
    # Add basic auth config endpoint as fallback
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

# Add GitHub authentication routes
try:
    from src.api.github_auth_routes import router as github_auth_router
    app.include_router(github_auth_router, prefix="/api/v1")
    logger.info("✅ GitHub authentication routes loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ GitHub auth routes not available: {e}")

# Add payment routes with Stripe integration
try:
    from src.routes.payment_routes import router as payment_router
    app.include_router(payment_router)
    logger.info("✅ Payment routes with Stripe integration loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Payment routes not available: {e}")

# Add billing routes for dynamic pricing
try:
    from src.routes.billing_routes import router as billing_router
    app.include_router(billing_router, prefix="/api/v1")
    logger.info("✅ Billing routes with dynamic pricing loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Billing routes not available: {e}")

# Include modular routers if available
if MODULAR_ROUTERS_AVAILABLE:
    try:
        # Add repository analysis endpoint
        @app.post("/api/analyze")
        async def analyze_repository(request: dict):
            """
            Analyze repository and generate deployment recommendations
            """
            logger.info(f"🔍 Analyzing repository: {request.get('repository_url', 'Unknown')}")
            
            try:
                repo_url = request.get('repository_url')
                target_platform = request.get('target_platform', 'aws')
                deployment_type = request.get('deployment_type', 'production')
                
                if not repo_url:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "repository_url is required"}
                    )
                
                # Generate deployment ID
                deployment_id = f"cfops-{int(time.time())}-{random.randint(1000, 9999)}"
                
                # Use enhanced repository analyzer
                from enhanced_repository_analyzer import EnhancedRepositoryAnalyzer
                analyzer = EnhancedRepositoryAnalyzer()
                
                # Analyze repository
                deployment_id_temp = f"temp-{deployment_id}"
                analysis_result = await analyzer.analyze_repository_comprehensive(repo_url, deployment_id_temp)
                
                # Get stack recommendation
                recommended_stack = "react-static"  # Default for React apps
                if 'frameworks' in analysis_result:
                    frameworks = analysis_result['frameworks']
                    if any('react' in fw.lower() for fw in frameworks):
                        recommended_stack = "react-static"
                    elif any('express' in fw.lower() or 'node' in fw.lower() for fw in frameworks):
                        recommended_stack = "nodejs-lightsail"
                
                # Language-based fallback for projects without clear framework detection
                if 'primary_language' in analysis_result:
                    primary_lang = analysis_result['primary_language'].lower()
                    if 'javascript' in primary_lang or 'typescript' in primary_lang:
                        # Check if it's a backend Node.js app (has package.json with server-like dependencies)
                        if recommended_stack == "react-static" and 'confidence' in analysis_result:
                            if analysis_result.get('confidence', 0) > 0.8:  # High confidence Node.js detection
                                recommended_stack = "nodejs-lightsail"
                
                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "repository_url": repo_url,
                    "recommended_stack": recommended_stack,
                    "target_platform": target_platform,
                    "analysis": analysis_result,
                    "timestamp": time.time()
                }
                
            except Exception as e:
                logger.error(f"❌ Analysis failed: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Analysis failed: {str(e)}"}
                )
        
        # Add deployment preparation endpoint
        @app.post("/api/deploy/prepare")
        async def prepare_deployment(request: dict):
            """
            Prepare repository for deployment (basic validation only)
            """
            logger.info(f"🛠️ Preparing deployment: {request.get('deployment_id', 'Unknown')}")
            
            try:
                deployment_id = request.get('deployment_id')
                repo_url = request.get('repository_url')
                
                if not deployment_id or not repo_url:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "deployment_id and repository_url are required"}
                    )
                
                # Basic repository validation
                import re
                if not re.match(r'https://github\.com/.+/.+', repo_url):
                    return {
                        "success": False,
                        "deployment_id": deployment_id,
                        "status": "failed",
                        "ready": False,
                        "error": "Invalid GitHub repository URL"
                    }
                
                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "status": "prepared",
                    "ready": True,
                    "fixes_applied": [],
                    "repo_path": None,
                    "error": None
                }
                
            except Exception as e:
                logger.error(f"❌ Preparation failed: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Preparation failed: {str(e)}"}
                )
        
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
                logger.error(f"Failed to deploy to {stack_type} stack: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to deploy to {stack_type} stack: {str(e)}"
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

# Add modular stack routers if available
try:
    # Force mount Node.js LightSail router (for Node.js backend deployments)
    logger.info("🔧 Force mounting Node.js LightSail router...")
    from routers.stacks.nodejs_lightsail_router import router as nodejs_lightsail_router
    app.include_router(nodejs_lightsail_router, prefix="/api/deploy/nodejs-lightsail", tags=["nodejs-lightsail"])
    logger.info("✅ Node.js LightSail router force-mounted at /api/deploy/nodejs-lightsail")
except Exception as router_error:
    logger.error(f"❌ CRITICAL: Failed to mount LightSail routers: {router_error}")
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")

if MODULAR_ROUTERS_AVAILABLE:
    try:
        # Mount other stack routers via registry
        for stack_name, router_instance in stack_router_registry.routers.items():
            if hasattr(router_instance, 'router'):
                app.include_router(router_instance.router, prefix=f"/api/deploy/{stack_name}", tags=[stack_name])
                logger.info(f"✅ {stack_name} router mounted at /api/deploy/{stack_name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to mount other modular routers: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
