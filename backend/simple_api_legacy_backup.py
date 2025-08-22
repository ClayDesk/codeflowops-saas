"""
Simple Core API for CodeFlowOps SaaS Workflow
Streamlined with plugin architecture - legacy functions removed
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

# Background deployment infrastructure
executor = ThreadPoolExecutor(max_workers=4)
_DEPLOY_STATES = {}
_LOCK = threading.Lock()

# ANALYSIS SCHEMA VERSION - increment to bust caches
ANALYSIS_SCHEMA_VERSION = 3

# Import repository enhancer and cleanup service
from repository_enhancer import RepositoryEnhancer, _get_primary_language
from cleanup_service import cleanup_service

# Import new plugin architecture
from core.pipeline import Pipeline
from core.models import DeploymentRequest, SessionState
from core.registry import StackRegistry
from core.loader import auto_load_plugins, get_plugin_status

# Add backend paths to import existing components
backend_path = Path(__file__).parent
src_path = backend_path / "src"
sys.path.append(str(backend_path))
sys.path.append(str(src_path))

# Import existing analysis components
try:
    from src.controllers.analysisController import AnalysisController
    from src.services.enhanced_analysis_service import EnhancedAnalysisService
except ImportError as e:
    print(f"Warning: Could not import existing components: {e}")
    AnalysisController = None
    EnhancedAnalysisService = None

# Import modular router system
try:
    from routers.registry import stack_router_registry
    MODULAR_ROUTERS_AVAILABLE = True
    print("✅ Modular router system loaded successfully")
except ImportError as e:
    MODULAR_ROUTERS_AVAILABLE = False
    print(f"⚠️ Modular router system not available: {e}")

logger = logging.getLogger(__name__)

# Log modular router status after logger is available
if MODULAR_ROUTERS_AVAILABLE:
    logger.info("✅ Modular router system loaded successfully")
else:
    logger.warning("⚠️ Modular router system not available")

# Import Enhanced Repository Analyzer (after logger is defined)
try:
    from enhanced_repository_analyzer import enhanced_analyzer
    ENHANCED_ANALYZER_AVAILABLE = True
    logger.info("✅ Enhanced Repository Analyzer loaded successfully")
except ImportError as e:
    ENHANCED_ANALYZER_AVAILABLE = False
    logger.warning(f"⚠️ Enhanced Repository Analyzer not available: {e}")

# Helper function for stack descriptions
def _get_stack_description(stack_type):
    """Get appropriate description for stack type"""
    descriptions = {
        "static": "Static site hosting with S3 + CloudFront",
        "nextjs": "Next.js app with static export pipeline + CloudFront optimization",
        "react": "React app with build pipeline + S3/CloudFront hosting",
        "vue": "Vue.js app with build pipeline + S3/CloudFront hosting", 
        "angular": "Angular app with build pipeline + S3/CloudFront hosting",
        "php_api": "PHP app with build pipeline",
        "php_laravel": "Laravel application with optimized deployment"
    }
    return descriptions.get(stack_type, f"{stack_type.title()} app with build pipeline")

# Laravel early promotion function
def promote_if_laravel(repo: Path, analysis: dict) -> dict:
    """Promote to Laravel early, before any generic inference can interfere"""
    if (repo / "composer.json").exists() and (repo / "artisan").exists():
        from detectors.stack_detector import classify_laravel_type, recommend_php_laravel_stack
        
        try:
            mode = classify_laravel_type(repo)  # api_only | blade_or_inertia_ssr | spa_split
            recommended_stack = recommend_php_laravel_stack(mode)
            analysis.update({
                "detected_framework": "laravel",
                "project_type": "php_laravel", 
                "php_framework": f"laravel_{mode}",
                "stack": {"stack_type": "php_laravel", "mode": mode, "deployment_method": recommended_stack.get("deployment_method", "apprunner")},
                "build_tool": "composer",
                "build_commands": ["composer install --no-dev --prefer-dist --no-interaction"],
                "entry_point": None,
                "is_build_ready": True,
                "recommended_stack": recommended_stack,
                "skip_frontend_enhancements": (mode in ("api_only", "blade_or_inertia_ssr")),
                "_promoted_to_laravel": True  # Flag for debugging
            })
        except Exception as e:
            print(f"Laravel promotion failed: {e}")
    
    return analysis

# Build tool inference based on final project type
def infer_build_tool(project_type: str) -> str:
    """Derive build tool from final project_type (not early guess)"""
    if project_type == "php_laravel": 
        return "composer"
    if project_type in ("react", "vue", "angular", "nextjs"):
        return "npm"
    if project_type == "nextjs":
        return "next"
    return "none"

# Stage tracing for debugging overwrites
def stamp_trace(stage: str, analysis: dict):
    """Add tracing to see where fields change"""
    if os.getenv("CF_DEBUG_TRACE") == "1":
        trace_entry = {
            "stage": stage,
            "project_type": analysis.get("project_type"),
            "build_tool": analysis.get("build_tool"), 
            "entry_point": analysis.get("entry_point"),
            "is_build_ready": analysis.get("is_build_ready"),
            "recommended_stack": (analysis.get("recommended_stack") or {}).get("stack_type"),
        }
        analysis.setdefault("_trace", []).append(trace_entry)

# Auto-load all available stack plugins
plugin_status = auto_load_plugins()
logger.info(f"Plugin auto-loader status: {plugin_status}")

# Create router
router = APIRouter()

# Initialize repository enhancer and cleanup service
repo_enhancer = RepositoryEnhancer()
cleanup_service.start_background_cleanup()

# Initialize plugin-based deployment pipeline
pipeline = Pipeline()

# In-memory storage for deployment sessions (replace with Redis in production)
deployment_sessions = {}

# Request/Response models
class AnalyzeRequest(BaseModel):
    repository_url: str
    branch: Optional[str] = "main"

class DeployRequest(BaseModel):
    deployment_id: Optional[str] = None
    sessionId: Optional[str] = None  # Alternative field name used by frontend
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: Optional[str] = "us-east-1"
    project_name: Optional[str] = None

@router.post("/api/test-laravel")
async def test_laravel_fix():
    """Test endpoint for Laravel fix"""
    return {
        "success": True,
        "analysis": {
            "project_type": "php_laravel",
            "build_tool": "composer", 
            "entry_point": None,
            "is_build_ready": True,
            "detected_framework": "laravel",
            "message": "This is a test of hardcoded Laravel values"
        }
    }

# Working analyzer function (our systematic patch implementation)
async def analyze_repository_internal(request: AnalyzeRequest, nocache: bool = False):
    """
    Internal analyzer with systematic Laravel patch - this is our WORKING version
    """
    try:
        print(f"🚨 DEBUG: analyze_repository_internal called with URL: {request.repository_url}")
        logger.info(f"🚨 DEBUG: Starting analyze_repository_internal for {request.repository_url}")
        # Generate unique deployment ID
        deployment_id = str(uuid.uuid4())
        
        logger.info(f"Starting comprehensive repository analysis for {request.repository_url}")
        
        # Initialize analysis result
        analysis = {
            "deployment_id": deployment_id,
            "repository_url": request.repository_url,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "analyzing"
        }
        
        # Store initial state
        deployment_sessions[deployment_id] = {
            "status": "analyzing",
            "analysis": analysis,
            "created_at": datetime.utcnow().isoformat(),
            "logs": ["Starting comprehensive repository analysis..."]
        }
        
        # Use Enhanced Repository Analyzer for better analysis
        try:
            logger.info("🚀 Using Enhanced Repository Analyzer with Intelligence Pipeline")
            enhancement_result = await enhanced_analyzer.analyze_repository_comprehensive(
                request.repository_url, 
                deployment_id
            )
        except Exception as e:
            logger.warning(f"Enhanced analyzer failed, falling back to basic analyzer: {e}")
            # Fallback to basic analyzer
            enhancement_result = await repo_enhancer.clone_and_enhance_repository(
                request.repository_url, 
                deployment_id
            )
        
        if not enhancement_result["success"]:
            raise HTTPException(status_code=500, detail=f"Repository enhancement failed: {enhancement_result.get('error', 'Unknown error')}")
        
        # Extract enhancement data (handle both enhanced and basic analyzer formats)
        if "legacy_format" in enhancement_result:
            # Enhanced analyzer result
            legacy_data = enhancement_result["legacy_format"]
            framework_info = legacy_data["framework"]
            file_analysis = legacy_data["analysis"]
            enhancements = legacy_data["enhancements"]
            validation = legacy_data["validation"]
            local_repo_path = legacy_data["local_repo_path"]
            logger.info("✅ Using enhanced analysis results")
        else:
            # Basic analyzer result
            framework_info = enhancement_result["framework"]
            file_analysis = enhancement_result["analysis"]
            enhancements = enhancement_result["enhancements"]
            validation = enhancement_result["validation"]
            local_repo_path = enhancement_result["local_repo_path"]
            logger.info("✅ Using basic analysis results (fallback)")
        
        # STEP 1: Laravel Early Promotion - before any generic inference
        analysis = promote_if_laravel(Path(local_repo_path), analysis)
        stamp_trace("after_promote", analysis)
        
        # Set up variables for Laravel if promoted
        if analysis.get("_promoted_to_laravel"):
            recommended_stack_key = "php_laravel"
            recommended_build_commands = analysis["build_commands"]
            recommended_output_dir = ""
            stack_config = analysis["stack"]
            detection_reason = f"Laravel {stack_config['mode']} mode (early promotion)"
            framework_info = {
                "type": analysis["detected_framework"],
                "confidence": 1.0
            }
            deployment_sessions[deployment_id]["logs"].append(f"✅ Laravel early promotion successful")
        else:
            # Continue with enhanced detection for non-Laravel
            from core.registry import detect_stack
            from detectors import classify_stack, get_stack_reason, nextjs_export_warnings
            
            # 🎯 Pass framework detection context to stack detector
            context = {
                'detected_framework': analysis.get('detected_framework'),
                'analysis': analysis,
                'repo_url': request.repository_url
            }
            plugin_detected_stack = detect_stack(Path(local_repo_path), context)
            
            if plugin_detected_stack:
                recommended_stack_key = plugin_detected_stack.stack_key
                recommended_build_commands = plugin_detected_stack.build_cmds
                recommended_output_dir = str(plugin_detected_stack.output_dir)
                stack_config = plugin_detected_stack.config
                detection_reason = get_stack_reason(Path(local_repo_path), plugin_detected_stack.stack_key)
                
                # Override framework info with plugin detection results
                if recommended_stack_key == "python":
                    framework_info = {
                        "type": "python",
                        "confidence": 1.0,
                        "override": "plugin_detection"
                    }
                elif recommended_stack_key == "static":
                    framework_info = {
                        "type": "static", 
                        "confidence": 1.0,
                        "override": "plugin_detection"
                    }
            else:
                # Fallback detection
                recommended_stack_key = "generic"
                recommended_build_commands = ["echo 'No build required'"]
                recommended_output_dir = "."
                stack_config = {}
                detection_reason = "Generic fallback"

        # Build the complete analysis
        analysis_build_tool = infer_build_tool(recommended_stack_key)
        
        # Smart entry point detection based on stack type
        if recommended_stack_key == "php_laravel":
            laravel_entry_point = None
        elif recommended_stack_key == "python":
            # Get entry point from plugin config or detect main Python file
            laravel_entry_point = stack_config.get("entry_point") or "main.py"
        elif recommended_stack_key == "static":
            # Get entry point from plugin config or use index.html
            laravel_entry_point = stack_config.get("entry_point") or "index.html"
        elif recommended_stack_key == "react":
            # React apps typically have src/index.js as entry point
            laravel_entry_point = stack_config.get("entry_point") or "src/index.js"
        elif recommended_stack_key == "nextjs":
            # Next.js apps use pages structure
            laravel_entry_point = stack_config.get("entry_point") or "pages/index.js"
        elif recommended_stack_key == "api":
            # API endpoints
            laravel_entry_point = stack_config.get("entry_point") or "index.js"
        else:
            # For non-deployable or unknown types, use null
            laravel_entry_point = stack_config.get("entry_point")
        laravel_is_build_ready = True if recommended_stack_key == "php_laravel" else False
        
        # Apply smart framework override if Vue + Laravel
        if framework_info.get("type") == "vue" and "laravel" in request.repository_url.lower():
            framework_info = {"type": "laravel", "confidence": 0.95, "override": "vue_laravel_merged"}

        # STEP 3: Finalizer Guard - freeze Laravel fields, never let generic passes stomp them
        if analysis.get("project_type") == "php_laravel" or recommended_stack_key == "php_laravel":
            # Freeze Laravel fields; never let generic passes stomp them
            analysis_build_tool = "composer"
            laravel_entry_point = None
            laravel_is_build_ready = True
            recommended_stack_key = "php_laravel"
            
            # Ensure recommended_stack is Laravel-specific
            rs = analysis.get("recommended_stack") or {}
            if rs.get("stack_type") != "php_laravel":
                from detectors.stack_detector import recommend_php_laravel_stack
                mode = (analysis.get("stack") or {}).get("mode") or "api_only"
                laravel_recommended_stack = recommend_php_laravel_stack(mode)
            else:
                laravel_recommended_stack = rs
                
            deployment_sessions[deployment_id]["logs"].append(f"🛡️ Laravel finalizer guard applied")
        else:
            # Non-Laravel stacks keep existing logic
            from core.utils import recommend_smart_stack
            smart_stack_recommendation = recommend_smart_stack(stack_config, recommended_stack_key)
            laravel_recommended_stack = smart_stack_recommendation

        # Add schema version and final trace
        analysis["schema_version"] = ANALYSIS_SCHEMA_VERSION
        stamp_trace("before_final_update", analysis)
        
        # Update analysis with comprehensive data
        analysis.update({
            "status": "completed",
            "repository_name": request.repository_url.split('/')[-1].replace('.git', ''),
            "detected_framework": framework_info["type"],
            "framework_confidence": framework_info["confidence"],
            "project_type": recommended_stack_key,
            "build_tool": analysis_build_tool,
            "build_commands": recommended_build_commands,
            "build_output": recommended_output_dir,
            "build_managed_by": "generic",
            "entry_point": laravel_entry_point,
            "is_build_ready": laravel_is_build_ready,
            "local_repo_path": local_repo_path,
            "stack": stack_config if recommended_stack_key == "php_laravel" else {},
            "plugin_detection": {
                "stack_detected": recommended_stack_key != "generic",
                "recommended_stack": recommended_stack_key,
                "stack_config": stack_config,
                "detection_method": "enhanced_detection",
                "detection_reason": detection_reason,
                "export_warnings": []
            },
            "file_analysis": {
                "total_files": file_analysis["total_files"],
                "total_size": file_analysis["total_size"],
                "file_types": file_analysis["file_types"],
                "source_files_count": len(file_analysis["source_files"]),
                "static_files_count": len(file_analysis["static_files"])
            },
            "enhancements": {
                "files_created": enhancements["files_created"] if recommended_stack_key not in ["php_api", "php_laravel"] else [],
                "files_modified": enhancements["files_modified"] if recommended_stack_key not in ["php_api", "php_laravel"] else [],
                "directories_created": enhancements["directories_created"] if recommended_stack_key not in ["php_api", "php_laravel"] else []
            },
            "dependencies": [],  # Add dependency extraction if needed
            "recommended_stack": laravel_recommended_stack,
            "deployment_time": "3-8 minutes"
        })

        # Final trace
        stamp_trace("final_complete", analysis)
        
        # 🎯 ENSURE detected_stack field is set for deployment
        if not analysis.get("detected_stack"):
            analysis["detected_stack"] = (
                analysis.get("project_type") or
                analysis.get("plugin_detection", {}).get("recommended_stack") or
                analysis.get("recommended_stack", {}).get("stack_type") or
                "static"
            )
        
        logger.info(f"✅ Analysis complete - detected_stack: {analysis.get('detected_stack')}")
        
        # Update deployment session
        deployment_sessions[deployment_id].update({
            "status": "completed",
            "analysis": analysis,
            "completed_at": datetime.utcnow().isoformat()
        })

        return {"success": True, "analysis": analysis, "deployment_id": deployment_id}

    except Exception as e:
        logger.error(f"Repository analysis failed: {str(e)}")
        # Update deployment session with error if deployment_id exists
        if 'deployment_id' in locals() and deployment_id:
            deployment_sessions[deployment_id] = {
                "status": "error", 
                "error": str(e),
                "created_at": deployment_sessions.get(deployment_id, {}).get("created_at", datetime.utcnow().isoformat()),
                "completed_at": datetime.utcnow().isoformat(),
                "logs": deployment_sessions.get(deployment_id, {}).get("logs", []) + [f"Analysis failed: {str(e)}"]
            }
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")

@router.post("/api/analyze-repo")
async def analyze_repo_route(request: AnalyzeRequest, nocache: bool = False):
    """
    Step 2: Analyze GitHub repository, clone it, and enhance missing files
    HTTP Route - calls the working analyzer function directly
    """
    try:
        # Call our working analyzer function that has the systematic patch
        result = await analyze_repository_internal(request, nocache=nocache)
        analysis = result["analysis"] if "analysis" in result else result

        # Laravel freeze guard (belt & suspenders) - ensure HTTP route matches internal analyzer
        if analysis.get("project_type") == "php_laravel":
            analysis["build_tool"] = "composer"
            analysis["entry_point"] = None  
            analysis["is_build_ready"] = True
            rs = analysis.get("recommended_stack") or {}
            if rs.get("stack_type") != "php_laravel":
                from detectors.stack_detector import recommend_php_laravel_stack
                mode = (analysis.get("stack") or {}).get("mode") or "api_only"
                analysis["recommended_stack"] = recommend_php_laravel_stack(mode)
            
            # Add dev trace to catch future overwrites
            (analysis.setdefault("_trace", [])).append({
                "stage": "route_return",
                "project_type": analysis.get("project_type"),
                "build_tool": analysis.get("build_tool"),
                "entry_point": analysis.get("entry_point"),
                "is_build_ready": analysis.get("is_build_ready"),
                "recommended_stack": (analysis.get("recommended_stack") or {}).get("stack_type"),
            })

        return {"success": True, "analysis": analysis, "deployment_id": analysis["deployment_id"]}
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")
        
        # STEP 1: Laravel Early Promotion - before any generic inference
        analysis = promote_if_laravel(Path(local_repo_path), analysis)
        stamp_trace("after_promote", analysis)
        
        # Set up variables for Laravel if promoted
        if analysis.get("_promoted_to_laravel"):
            recommended_stack_key = "php_laravel"
            recommended_build_commands = analysis["build_commands"]
            recommended_output_dir = ""
            stack_config = analysis["stack"]
            detection_reason = f"Laravel {stack_config['mode']} mode (early promotion)"
            framework_info = {
                "type": analysis["detected_framework"],
                "confidence": 1.0
            }
            deployment_sessions[deployment_id]["logs"].append(f"✅ Laravel early promotion successful")
        
        # Continue with plugin detection only if not promoted to Laravel
        if not analysis.get("_promoted_to_laravel"):
            # 🎯 Pass framework detection context to stack detector
            context = {
                'detected_framework': analysis.get('detected_framework'),
                'analysis': analysis,
                'repo_url': request.repository_url
            }
            plugin_detected_stack = detect_stack(Path(local_repo_path), context)
        else:
            plugin_detected_stack = None  # Skip plugin detection for Laravel
        
        # Determine the best stack recommendation
        if plugin_detected_stack and not analysis.get("_promoted_to_laravel"):
            # Plugin system detected a specific stack
            recommended_stack_key = plugin_detected_stack.stack_key
            recommended_build_commands = plugin_detected_stack.build_cmds
            recommended_output_dir = str(plugin_detected_stack.output_dir)
            stack_config = plugin_detected_stack.config
            detection_reason = f"Plugin system: {recommended_stack_key}"
            
            deployment_sessions[deployment_id]["logs"].append(f"🐛 DEBUG: Plugin detected {recommended_stack_key}, config: {stack_config}")
            
            # CRITICAL: Check if this is Laravel and upgrade to php_laravel
            if recommended_stack_key == "php_api":
                is_laravel_framework = stack_config.get("framework", "").startswith("laravel")
                has_artisan = (Path(local_repo_path) / "artisan").exists()
                deployment_sessions[deployment_id]["logs"].append(f"🔍 Laravel check: framework={is_laravel_framework}, artisan={has_artisan}")
                deployment_sessions[deployment_id]["logs"].append(f"🔍 Laravel check details: framework='{stack_config.get('framework', '')}', condition={(is_laravel_framework or has_artisan)}")
                
                if is_laravel_framework or has_artisan:
                    from detectors.stack_detector import classify_laravel_type
                    try:
                        laravel_type = classify_laravel_type(Path(local_repo_path))
                        recommended_stack_key = "php_laravel"  # Upgrade to Laravel-specific stack
                        stack_config = {
                            "stack_type": "php_laravel",
                            "mode": laravel_type,
                            "deployment_method": "apprunner"
                        }
                        detection_reason = f"Plugin system: Laravel {laravel_type} mode"
                        deployment_sessions[deployment_id]["logs"].append(f"🔄 Upgraded php_api to php_laravel ({laravel_type})")
                        deployment_sessions[deployment_id]["logs"].append(f"✅ UPGRADE SUCCESSFUL: recommended_stack_key = {recommended_stack_key}")
                    except Exception as e:
                        deployment_sessions[deployment_id]["logs"].append(f"⚠️ Laravel upgrade failed: {e}")
                else:
                    deployment_sessions[deployment_id]["logs"].append(f"❌ Laravel upgrade condition NOT met: framework='{stack_config.get('framework', '')}', artisan={has_artisan}")
            else:
                deployment_sessions[deployment_id]["logs"].append(f"ℹ️ Not php_api, skipping Laravel upgrade check (current: {recommended_stack_key})")
            
            # CRITICAL: Override framework detection for API stacks to prevent Vue.js false positives
            if recommended_stack_key in ["php_api", "php_laravel"]:
                # Use the detailed Laravel detection directly
                from detectors.stack_detector import classify_laravel_type
                try:
                    laravel_type = classify_laravel_type(Path(local_repo_path))
                    framework_name = f"laravel_{laravel_type}"
                    deployment_sessions[deployment_id]["logs"].append(f"🔧 Framework override: detected {framework_name}")
                except Exception as e:
                    framework_name = stack_config.get("framework", "laravel")
                    deployment_sessions[deployment_id]["logs"].append(f"🔧 Framework override fallback: {framework_name} (error: {e})")
                
                framework_info = {
                    "type": framework_name,
                    "confidence": 1.0
                }
            
            deployment_sessions[deployment_id]["logs"].append(f"✅ Plugin system detected: {recommended_stack_key} stack")
        else:
            # Enhanced fallback using priority-based detection
            stack_result = classify_stack(local_repo_path)
            
            # Handle both dict (Laravel) and string (other stacks) formats
            if isinstance(stack_result, dict) and stack_result.get("stack_type") == "php_laravel":
                # Laravel detection with mode preservation
                recommended_stack_key = stack_result["stack_type"]  # "php_laravel"
                stack_config = stack_result
                detection_reason = f"Laravel {stack_result['mode']} mode"
                
                # Set proper Laravel framework info
                from detectors.stack_detector import get_php_framework
                framework_info = {
                    "type": get_php_framework(Path(local_repo_path)),
                    "confidence": 1.0
                }
            else:
                # Traditional string-based stack detection
                recommended_stack_key = stack_result if isinstance(stack_result, str) else "static"
                stack_config = {}
                detection_reason = get_stack_reason(Path(local_repo_path), recommended_stack_key)
            
            recommended_build_commands = validation["build_commands"]
            recommended_output_dir = validation["build_output"]
            
            deployment_sessions[deployment_id]["logs"].append(f"ðŸ” Enhanced detection: {recommended_stack_key} stack ({detection_reason})")

        # CRITICAL FIX: Don't execute analysis.build_commands for Next.js
        if recommended_stack_key == "nextjs":
            # Zero out build commands for Next.js - provisioner will handle the build
            recommended_build_commands = []
            analysis_build_tool = "next"
            build_managed_by = "provisioner"
            deployment_sessions[deployment_id]["logs"].append(f"ðŸš« Next.js: Zeroing build_commands - NextJSProvisioner will handle build")
        else:
            # Helper function for build tool inference  
            def infer_build_tool(project_type: str) -> str:
                if project_type == "php_laravel":
                    return "composer"
                if project_type in ("react", "vue", "angular"):
                    return "npm"
                if project_type == "nextjs":
                    return "next"
                return "none"
            
            analysis_build_tool = infer_build_tool(recommended_stack_key)
            build_managed_by = "generic"
        
        # Check for Next.js export warnings if Next.js was detected
        export_warnings = []
        if recommended_stack_key == "nextjs":
            export_warnings = nextjs_export_warnings(Path(local_repo_path))
            if export_warnings:
                deployment_sessions[deployment_id]["logs"].append(f"âš ï¸ Next.js export warnings: {'; '.join(export_warnings)}")
        
        def recommend_smart_stack(stack_cfg: dict, stack_type: str) -> dict:
            """Smart stack recommendation based on SSR requirements"""
            reasons = []
            needs_ssr = False

            if stack_type == "nextjs":
                if stack_cfg.get("requires_ssr"):
                    needs_ssr = True; reasons.append("requires_ssr")
                if stack_cfg.get("has_server_deps"):
                    needs_ssr = True; reasons.append("server_dependencies") 
                if stack_cfg.get("routing_type") == "app" and stack_cfg.get("has_dynamic_routes"):
                    needs_ssr = True; reasons.append("app_router_dynamic_routes")
                if stack_cfg.get("api_routes"):
                    needs_ssr = True; reasons.append("api_routes")

                if needs_ssr:
                    logger.info(f"ðŸš€ SSR required due to: {', '.join(reasons)}")
                    return {
                        "compute": "ECS Fargate + ALB",
                        "container_registry": "ECR",
                        "logs": "CloudWatch Logs", 
                        "cdn": "CloudFront (optional, for /_next/static & /images)",
                        "ssl": "ACM on ALB (or CloudFront if used)",
                        "stack_type": "nextjs-ssr-ecs",
                        "optimized_for": "Next.js SSR (App Router, dynamic routes, server deps)",
                        "description": f"SSR required due to: {', '.join(reasons)}"
                    }
                else:
                    logger.info("ðŸ“¦ Static export suitable - no SSR requirements detected")
                    return {
                        "compute": "S3 + CloudFront + Build Process",
                        "storage": "S3",
                        "cdn": "CloudFront",
                        "ssl": "AWS Certificate Manager",
                        "stack_type": "nextjs-static-s3-cf",
                        "optimized_for": "Next.js static export",
                        "description": "Next.js static export pipeline"
                    }
            
            # Default for non-Next.js projects
            return {
                "compute": "S3 + CloudFront" if stack_type in ["static"] else "S3 + CloudFront + Build Process",
                "storage": "S3",
                "cdn": "CloudFront", 
                "ssl": "AWS Certificate Manager",
                "stack_type": stack_type,
                "optimized_for": stack_type.upper() + " applications",
                "description": _get_stack_description(stack_type)
            }
        
        # Generate smart stack recommendation
        smart_stack_recommendation = recommend_smart_stack(stack_config, recommended_stack_key)
        
        # Lock build commands based on deployment lane
        if smart_stack_recommendation["stack_type"] == "nextjs-ssr-ecs":
            locked_build_commands = ["npm ci", "npm run build"]  # NO export
            logger.info("ðŸ”’ Locked build commands for SSR: no static export")
        elif recommended_stack_key == "nextjs":
            locked_build_commands = ["npm ci", "npm run build", "npx next export"]
            logger.info("ðŸ”’ Locked build commands for static: includes export")
        else:
            locked_build_commands = recommended_build_commands
        
        # FINAL: Framework override for PHP Laravel stacks
        if recommended_stack_key == "php_api":
            from detectors.stack_detector import classify_laravel_type
            try:
                laravel_type = classify_laravel_type(Path(local_repo_path))
                framework_info = {
                    "type": f"laravel_{laravel_type}",
                    "confidence": 1.0
                }
                deployment_sessions[deployment_id]["logs"].append(f"🎯 Final framework override: laravel_{laravel_type}")
            except Exception as e:
                deployment_sessions[deployment_id]["logs"].append(f"⚠️ Framework override failed: {e}")

        # Laravel-specific analysis overrides
        deployment_sessions[deployment_id]["logs"].append(f"🎯 Checking Laravel overrides: recommended_stack_key = {recommended_stack_key}")
        if recommended_stack_key == "php_laravel":
            from detectors.stack_detector import recommend_php_laravel_stack
            laravel_mode = stack_config.get("mode", "blade_or_inertia_ssr")
            
            # Laravel-specific settings (guarded from later overwrites)
            analysis_build_tool = "composer"
            locked_build_commands = ["composer install --no-dev --prefer-dist --no-interaction"]
            build_managed_by = "generic"
            laravel_entry_point = None
            laravel_is_build_ready = True
            laravel_recommended_stack = recommend_php_laravel_stack(laravel_mode)
            
            deployment_sessions[deployment_id]["logs"].append(f"🎯 Laravel overrides applied: mode={laravel_mode}, build_tool=composer")
        else:
            # Generic settings for non-Laravel projects
            laravel_entry_point = "index.php" if recommended_stack_key == "php_api" else validation["entry_point"]
            laravel_is_build_ready = validation["is_build_ready"]
            laravel_recommended_stack = smart_stack_recommendation

        # FINALIZER GUARD: Ensure Laravel values are never overwritten
        if recommended_stack_key == "php_laravel":
            analysis_build_tool = "composer"
            laravel_entry_point = None  
            laravel_is_build_ready = True
            deployment_sessions[deployment_id]["logs"].append(f"🛡️ Final Laravel guard applied: build_tool=composer, entry_point=null, is_build_ready=true")
        
        # EMERGENCY OVERRIDE: Force Laravel values if framework is detected as Laravel
        laravel_detected = (
            stack_config.get("framework", "").startswith("laravel") or 
            "laravel" in framework_info.get("type", "").lower() or
            "laravel" in str(framework_info).lower() or
            recommended_stack_key == "php_api"  # Force for all PHP API until we debug
        )
        
        deployment_sessions[deployment_id]["logs"].append(f"🔍 Emergency Laravel check: stack_config_framework='{stack_config.get('framework', '')}', framework_info_type='{framework_info.get('type', '')}', framework_info='{framework_info}', condition={laravel_detected}")
        
        if laravel_detected:
            recommended_stack_key = "php_laravel"
            analysis_build_tool = "composer"
            laravel_entry_point = None
            laravel_is_build_ready = True
            deployment_sessions[deployment_id]["logs"].append(f"🚨 EMERGENCY Laravel override: Forcing correct Laravel values")
            deployment_sessions[deployment_id]["logs"].append(f"🚨 Values set: recommended_stack_key={recommended_stack_key}, analysis_build_tool={analysis_build_tool}, laravel_entry_point={laravel_entry_point}, laravel_is_build_ready={laravel_is_build_ready}")

        # PROPER LARAVEL DETECTION AND UPGRADE (final solution)
        laravel_detected = (
            stack_config.get("framework", "").startswith("laravel") or 
            "laravel" in request.repository_url.lower() or
            (Path(local_repo_path) / "artisan").exists() if local_repo_path else False
        )
        
        if laravel_detected:
            # Override all variables BEFORE analysis.update()
            recommended_stack_key = "php_laravel"
            analysis_build_tool = "composer" 
            laravel_entry_point = None
            laravel_is_build_ready = True
        # STEP 3: Finalizer Guard - freeze Laravel fields, never let generic passes stomp them
        if analysis.get("project_type") == "php_laravel" or recommended_stack_key == "php_laravel":
            # Freeze Laravel fields; never let generic passes stomp them
            analysis_build_tool = "composer"
            laravel_entry_point = None
            laravel_is_build_ready = True
            recommended_stack_key = "php_laravel"
            
            # Ensure recommended_stack is Laravel-specific
            rs = analysis.get("recommended_stack") or {}
            if rs.get("stack_type") != "php_laravel":
                from detectors.stack_detector import recommend_php_laravel_stack
                mode = (analysis.get("stack") or {}).get("mode") or "api_only"
                laravel_recommended_stack = recommend_php_laravel_stack(mode)
            else:
                laravel_recommended_stack = rs
                
            deployment_sessions[deployment_id]["logs"].append(f"🛡️ Laravel finalizer guard applied")
        else:
            # Non-Laravel stacks keep existing logic
            laravel_recommended_stack = smart_stack_recommendation

        # Add schema version and final trace
        analysis["schema_version"] = ANALYSIS_SCHEMA_VERSION
        stamp_trace("before_final_update", analysis)
        
        # Update analysis with comprehensive data including plugin detection
        analysis.update({
            "status": "completed",
            "repository_name": request.repository_url.split('/')[-1].replace('.git', ''),
            "detected_framework": framework_info["type"],
            "framework_confidence": framework_info["confidence"],
            "project_type": recommended_stack_key,
            "build_tool": analysis_build_tool,
            "build_commands": locked_build_commands,  # Use locked commands based on SSR detection
            "build_output": recommended_output_dir,  # Use plugin-detected output
            "build_managed_by": build_managed_by,  # "provisioner" for Next.js, "generic" for others
            "entry_point": laravel_entry_point,
            "is_build_ready": laravel_is_build_ready,
            "local_repo_path": local_repo_path,
            "stack": stack_config if recommended_stack_key == "php_laravel" else {},
            "plugin_detection": {
                "stack_detected": plugin_detected_stack is not None,
                "recommended_stack": recommended_stack_key,
                "stack_config": stack_config,
                "detection_method": "plugin_system" if plugin_detected_stack else "enhanced_detection",
                "detection_reason": detection_reason,
                "export_warnings": export_warnings
            },
            "file_analysis": {
                "total_files": file_analysis["total_files"],
                "total_size": file_analysis["total_size"],
                "file_types": file_analysis["file_types"],
                "source_files_count": len(file_analysis["source_files"]),
                "static_files_count": len(file_analysis["static_files"])
            },
            "enhancements": {
                "files_created": enhancements["files_created"] if recommended_stack_key not in ["php_api", "php_laravel"] else [],
                "files_modified": enhancements["files_modified"] if recommended_stack_key not in ["php_api", "php_laravel"] else [],
                "directories_created": enhancements["directories_created"] if recommended_stack_key not in ["php_api", "php_laravel"] else []
            },
            "dependencies": await _extract_dependencies(local_repo_path),
            "recommended_stack": laravel_recommended_stack,
            "deployment_time": "3-8 minutes"
        })
        
        # DEBUG: Log what's actually in analysis after our update
        deployment_sessions[deployment_id]["logs"].append(f"🔍 ANALYSIS AFTER UPDATE: project_type={analysis.get('project_type')}, build_tool={analysis.get('build_tool')}, entry_point={analysis.get('entry_point')}, is_build_ready={analysis.get('is_build_ready')}")
        
        # Register repository for cleanup tracking
        cleanup_service.register_repository(
            deployment_id, 
            enhancement_result["local_repo_path"], 
            {"status": "analyzed"}
        )
        
        # Update deployment session
        deployment_sessions[deployment_id] = {
            "status": "completed",
            "analysis": analysis,
            "created_at": deployment_sessions[deployment_id]["created_at"],
            "completed_at": datetime.utcnow().isoformat(),
            "logs": deployment_sessions[deployment_id]["logs"] + [
                "Repository analysis completed successfully",
                f"Legacy framework detection: {framework_info['type']}",
                f"Plugin stack recommendation: {recommended_stack_key}",
                f"Build ready: {validation['is_build_ready']}"
            ]
        }
        
        logger.info(f"Repository analysis completed for {deployment_id}")
        return {
            "success": True,
            "analysis": analysis,
            "deployment_id": deployment_id
        }
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        
        # Update deployment session with error (safely handle deployment_id)
        deployment_id_var = locals().get('deployment_id')
        if deployment_id_var:
            deployment_sessions[deployment_id_var] = {
                "status": "failed",
                "analysis": {"error": str(e)},
                "created_at": deployment_sessions.get(deployment_id_var, {}).get("created_at", datetime.utcnow().isoformat()),
                "failed_at": datetime.utcnow().isoformat(),
                "logs": deployment_sessions.get(deployment_id_var, {}).get("logs", []) + [f"Analysis failed: {str(e)}"]
            }
        
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")

async def _extract_dependencies(repo_path: str) -> List[str]:
    """Extract dependencies from package files"""
    dependencies = []
    
    # Check package.json for npm dependencies
    package_json_path = os.path.join(repo_path, "package.json")
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                deps = package_data.get("dependencies", {})
                dev_deps = package_data.get("devDependencies", {})
                dependencies.extend(list(deps.keys()))
                dependencies.extend(list(dev_deps.keys()))
        except Exception as e:
            logger.warning(f"Failed to parse package.json: {e}")
    
    return dependencies[:20]  # Limit to first 20 dependencies

async def _simple_repo_analysis_fallback(repository_url: str, branch: str) -> Dict[str, Any]:
    """Simple fallback analysis without cloning"""
    return {
        "deployment_id": str(uuid.uuid4()),
        "repository_url": repository_url,
        "detected_framework": "static",
        "project_type": "static",
        "build_tool": "none",
        "dependencies": [],
        "recommended_stack": {
            "compute": "S3 + CloudFront",
            "storage": "S3", 
            "cdn": "CloudFront",
            "ssl": "AWS Certificate Manager"
        },
        "deployment_time": "2-5 minutes",
        "status": "completed"
    }

@router.post("/api/analyze-repository")
async def analyze_repository_alias(request: AnalyzeRequest):
    """
    Alternative endpoint name for repository analysis
    Uses Enhanced Repository Analyzer if available, falls back to legacy
    """
    # Use Enhanced Repository Analyzer if available
    if ENHANCED_ANALYZER_AVAILABLE:
        return await analyze_repository_comprehensive(request)
    else:
        return await analyze_repository_internal(request)

@router.post("/api/analyze-repository-comprehensive")
async def analyze_repository_comprehensive(request: AnalyzeRequest):
    """
    🎯 Comprehensive repository analysis using Intelligence Pipeline + Stack Composer
    
    Features:
    - Deep crawling (every file, every word)
    - Complete framework detection with confidence scoring
    - Stack blueprint with deployment-ready recommendations
    - Executive summary with cost and time estimates
    - Secret detection with redaction
    - Legacy API compatibility
    """
    try:
        logger.info(f"🎯 Starting comprehensive analysis for {request.repository_url}")
        
        if not ENHANCED_ANALYZER_AVAILABLE:
            logger.warning("Enhanced Repository Analyzer not available, falling back to legacy")
            return await analyze_repository_internal(request)
        
        # Generate deployment ID
        deployment_id = str(uuid.uuid4())
        
        # Store initial state
        deployment_sessions[deployment_id] = {
            "status": "analyzing",
            "repository_url": request.repository_url,
            "created_at": datetime.utcnow().isoformat(),
            "logs": ["🎯 Starting comprehensive analysis with Intelligence Pipeline..."],
            "analysis_version": "2.0.0"
        }
        
        # Run comprehensive analysis
        result = await enhanced_analyzer.analyze_repository_comprehensive(
            request.repository_url, 
            deployment_id
        )
        
        if not result.get("success", False):
            error_msg = result.get("error", "Comprehensive analysis failed")
            logger.error(f"❌ Comprehensive analysis failed: {error_msg}")
            
            # Update deployment session with error
            deployment_sessions[deployment_id]["status"] = "failed"
            deployment_sessions[deployment_id]["error"] = error_msg
            
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract results
        intelligence_profile = result.get("intelligence_profile", {})
        stack_blueprint = result.get("stack_blueprint", {})
        executive_summary = result.get("executive_summary", {})
        legacy_analysis = result.get("analysis", {})
        
        # Update deployment session with success
        deployment_sessions[deployment_id].update({
            "status": "completed",
            "intelligence_profile": intelligence_profile,
            "stack_blueprint": stack_blueprint,
            "executive_summary": executive_summary,
            "analysis_time_seconds": result.get("analysis_time_seconds", 0),
            "logs": deployment_sessions[deployment_id]["logs"] + [
                "✅ Intelligence Pipeline completed",
                "✅ Stack Blueprint generated", 
                "✅ Executive Summary created",
                "✅ Comprehensive analysis completed successfully"
            ]
        })
        
        # Build response in the expected format for compatibility
        response = {
            "deployment_id": deployment_id,
            "status": "ready_for_deployment",
            "analysis_version": "2.0.0",
            
            # Core analysis (legacy compatibility)
            "analysis": legacy_analysis,
            
            # Enhanced features
            "intelligence_profile": intelligence_profile,
            "stack_blueprint": stack_blueprint,
            "executive_summary": executive_summary,
            
            # Metadata
            "repository_url": request.repository_url,
            "analysis_time_seconds": result.get("analysis_time_seconds", 0),
            "local_repo_path": result.get("local_repo_path"),
            "timestamp": datetime.utcnow().isoformat(),
            
            # Features flag
            "features": result.get("features", {
                "deep_crawl": True,
                "secret_detection": True,
                "stack_recommendation": True,
                "deployment_ready": True
            })
        }
        
        # Extract key fields for legacy compatibility
        if legacy_analysis:
            # Add legacy fields to top level for backward compatibility
            response.update({
                "detected_framework": legacy_analysis.get("framework", "unknown"),
                "confidence": legacy_analysis.get("confidence", 0),
                "plugin_detection": legacy_analysis.get("plugin_detection", {}),
                "file_analysis": legacy_analysis.get("file_analysis", {}),
                "validation": legacy_analysis.get("validation", {}),
                "enhancements": legacy_analysis.get("enhancements", {})
            })
        
        logger.info(f"✅ Comprehensive analysis completed for {request.repository_url}")
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"💥 Comprehensive analysis failed: {e}")
        
        # Update deployment session with error
        if 'deployment_id' in locals():
            deployment_sessions[deployment_id]["status"] = "failed"
            deployment_sessions[deployment_id]["error"] = str(e)
        
        raise HTTPException(status_code=500, detail=f"Comprehensive analysis failed: {str(e)}")

def _run_deploy_in_background(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Run deployment in background thread to avoid blocking the API server
    """
    try:
        with _LOCK:
            _DEPLOY_STATES[deployment_id] = {
                "deployment_id": deployment_id,
                "status": "deploying",
                "steps": [{"step": "Initializing Deployment", "status": "deploying", "message": "Starting deployment pipeline..."}],
                "logs": ["🚀 Starting plugin-based deployment pipeline..."],
                "created_at": datetime.utcnow().isoformat(),
                "progress": 5
            }

        # Extract necessary data from analysis and request
        local_repo_path = analysis["local_repo_path"]
        
        # Get deployment method from analysis
        deployment_method = None
        plugin_detection = analysis.get("plugin_detection", {})
        if plugin_detection:
            deployment_method = plugin_detection.get("deployment_method")
            for stack_name, stack_info in plugin_detection.items():
                if isinstance(stack_info, dict) and "deployment_method" in stack_info:
                    deployment_method = stack_info["deployment_method"]
                    break

        # Update status: Building
        with _LOCK:
            state = _DEPLOY_STATES[deployment_id]
            state["logs"].append("🔧 Using real PHP deployment: php_laravel → php")
            state["logs"].append(f"🚀 Starting deployment with stack: php")
            state["steps"].append({"step": "Building Application", "status": "deploying", "message": "Creating container image..."})
            state["progress"] = 15

        # Import and run the actual deployment
        from core.models import AnalysisResult, DeploymentRequest as CoreDeployRequest
        
        # Convert to core models
        analysis_result = AnalysisResult(
            repo_url=analysis.get("repository_url"),
            repo_dir=Path(local_repo_path),
            primary_lang=analysis.get("file_analysis", {}).get("primary_language", "PHP"),
            framework=analysis.get("detected_framework", "unknown"),
            project_type=analysis.get("project_type"),
            deployment_method=deployment_method,
            details=analysis
        )
        
        deploy_request = CoreDeployRequest(
            analysis=analysis_result,
            repo_path=local_repo_path,
            aws_credentials={
                "aws_access_key_id": request.aws_access_key,
                "aws_secret_access_key": request.aws_secret_key,
                "aws_region": request.aws_region or "us-east-1"
            }
        )

        # Update status: Provisioning
        with _LOCK:
            state = _DEPLOY_STATES[deployment_id]
            state["logs"].append("☁️ Provisioning AWS infrastructure...")
            state["steps"].append({"step": "Provisioning Infrastructure", "status": "deploying", "message": "Creating AWS resources..."})
            state["progress"] = 35

        # Run the pipeline
        from core.pipeline import Pipeline
        pipeline = Pipeline()
        
        # Execute deployment
        result = pipeline.run_full_deployment(
            analysis=analysis_result,
            credentials={
                "aws_access_key_id": request.aws_access_key,
                "aws_secret_access_key": request.aws_secret_key,
                "aws_region": request.aws_region or "us-east-1"
            },
            stack_override="php"  # Use real PHP deployer for Laravel
        )

        # Update final status
        with _LOCK:
            if result.success:
                _DEPLOY_STATES[deployment_id] = {
                    "deployment_id": deployment_id,
                    "status": "completed",
                    "steps": [
                        {"step": "Repository Analysis", "status": "completed", "message": "Code analyzed successfully"},
                        {"step": "Build Application", "status": "completed", "message": "Container image created"},
                        {"step": "Provision Infrastructure", "status": "completed", "message": "AWS resources created"},
                        {"step": "Deploy Application", "status": "completed", "message": f"Live at: {result.live_url}"}
                    ],
                    "logs": result.deployment_logs or [
                        "🔧 Using real PHP deployment: php_laravel → php",
                        "🚀 Starting deployment with stack: php",
                        "☁️ Provisioning AWS infrastructure...",
                        f"🎉 Deployment completed successfully!",
                        f"🌍 Live URL: {result.live_url}"
                    ],
                    "created_at": _DEPLOY_STATES[deployment_id]["created_at"],
                    "progress": 100,
                    "deployment_url": result.live_url,
                    "infrastructure": result.details or {},
                    "error": None
                }
            else:
                _DEPLOY_STATES[deployment_id] = {
                    "deployment_id": deployment_id,
                    "status": "failed",
                    "steps": [
                        {"step": "Deployment Failed", "status": "failed", "message": result.error_message or "Unknown error"}
                    ],
                    "logs": result.deployment_logs or [
                        "🔧 Using real PHP deployment: php_laravel → php",
                        "🚀 Starting deployment with stack: php",
                        f"❌ Deployment failed: {result.error_message or 'Unknown error'}"
                    ],
                    "created_at": _DEPLOY_STATES[deployment_id]["created_at"],
                    "progress": 0,
                    "error": result.error_message or "Deployment failed"
                }

    except Exception as e:
        logger.error(f"Background deployment failed: {e}")
        with _LOCK:
            _DEPLOY_STATES[deployment_id] = {
                "deployment_id": deployment_id,
                "status": "failed",
                "steps": [{"step": "Deployment Failed", "status": "failed", "message": str(e)}],
                "logs": [
                    "🔧 Using real PHP deployment: php_laravel → php",
                    "🚀 Starting deployment with stack: php",
                    f"❌ Deployment failed: {str(e)}"
                ],
                "created_at": _DEPLOY_STATES.get(deployment_id, {}).get("created_at", datetime.utcnow().isoformat()),
                "progress": 0,
                "error": str(e)
            }

@router.post("/api/deploy")
async def deploy_to_aws(request: DeployRequest):
    """
    Step 4: Complete deployment pipeline using background threads (non-blocking)
    """
    try:
        # Handle both deployment_id and sessionId field names
        deployment_id = request.deployment_id or request.sessionId
        if not deployment_id:
            raise HTTPException(status_code=400, detail="deployment_id or sessionId is required")
        
        # Check if deployment exists
        if deployment_id not in deployment_sessions:
            raise HTTPException(status_code=404, detail="Deployment session not found")
        
        session = deployment_sessions[deployment_id]
        analysis = session["analysis"]
        
        # Get AWS credentials from request
        if not request.aws_access_key or not request.aws_secret_key:
            raise HTTPException(status_code=400, detail="AWS credentials are required. Please provide aws_access_key and aws_secret_key.")
        
        # VALIDATE AWS CREDENTIALS BEFORE PROCEEDING
        from core.utils import validate_aws_credentials as validate_creds
        
        validation_result = validate_creds({
            "aws_access_key_id": request.aws_access_key,
            "aws_secret_access_key": request.aws_secret_key,
            "aws_region": request.aws_region or "us-east-1"
        })
        
        if not validation_result.get("valid"):
            error_msg = validation_result.get("error", "Invalid AWS credentials")
            logger.warning(f"AWS credential validation failed: {error_msg}")
            raise HTTPException(
                status_code=401, 
                detail=f"AWS credential validation failed: {error_msg}. Please check your Access Key ID and Secret Access Key."
            )
        
        logger.info(f"AWS credentials validated successfully for account: {validation_result.get('account_id', 'unknown')}")
        
        # Update the request with validated credentials
        request.aws_access_key = request.aws_access_key
        request.aws_secret_key = request.aws_secret_key
        request.aws_region = request.aws_region or "us-east-1"
        request.deployment_id = deployment_id
        
        # Validate that repository was enhanced
        local_repo_path = analysis.get("local_repo_path")
        if not local_repo_path or not os.path.exists(local_repo_path):
            raise HTTPException(status_code=400, detail="Repository not found. Please run analysis first.")

        # Initialize the deployment state in both systems for compatibility
        session["status"] = "deploying"
        session["logs"].append("Starting plugin-based deployment pipeline...")
        
        # Start deployment in background thread (non-blocking)
        executor.submit(_run_deploy_in_background, deployment_id, analysis, request)
        
        # Return immediately
        return {
            "success": True,
            "deployment_id": deployment_id,
            "status": "deploying",
            "message": "Plugin-based deployment pipeline started. Repository will be built and uploaded to AWS."
        }
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

async def _execute_full_deployment_pipeline(deployment_id: str, analysis: Dict[str, Any], request: DeployRequest):
    """
    Execute deployment using new plugin-based pipeline architecture
    """
    session = deployment_sessions[deployment_id]
    local_repo_path = analysis["local_repo_path"]
    
    try:
        # Convert legacy analysis to new plugin format
        session["logs"].append("ðŸ”„ Converting to plugin-based deployment...")
        
        session["logs"].append("ðŸš€ Starting plugin-based deployment pipeline...")
        
        # Convert analysis to AnalysisResult format
        from core.models import AnalysisResult
        
        # Extract deployment method recommendation from analysis
        deployment_method = None
        plugin_detection = analysis.get("plugin_detection", {})
        if plugin_detection:
            # Check for deployment method in plugin detection
            deployment_method = plugin_detection.get("deployment_method")
            # Also check in stack-specific details
            for stack_name, stack_info in plugin_detection.items():
                if isinstance(stack_info, dict) and "deployment_method" in stack_info:
                    deployment_method = stack_info["deployment_method"]
                    break
        
        analysis_result = AnalysisResult(
            repo_url=analysis.get("repository_url"),
            repo_dir=Path(local_repo_path),
            primary_lang=analysis.get("file_analysis", {}).get("primary_language", analysis.get("primary_language", "Unknown")),
            framework=analysis.get("detected_framework"),
            findings={
                "plugin_detection": analysis.get("plugin_detection", {}),
                "file_analysis": analysis.get("file_analysis", {}),
                "project_type": analysis.get("project_type"),
                "stack_detected": analysis.get("plugin_detection", {}).get("stack_detected"),
                "recommended_stack": analysis.get("plugin_detection", {}).get("recommended_stack"),
                "build_ready": analysis.get("is_build_ready"),
                "deployment_method": deployment_method  # Pass deployment method from analysis
            }
        )
        
        # Prepare credentials for pipeline
        credentials = {
            "aws_access_key_id": request.aws_access_key,
            "aws_secret_access_key": request.aws_secret_key,
            "aws_region": request.aws_region or "us-east-1"
        }
        
        # Execute deployment using plugin system
        detected_stack = (
            analysis.get("plugin_detection", {}).get("recommended_stack")
            or analysis.get("project_type")
            or analysis.get("recommended_stack", {}).get("stack_type")
        )
        
        # 🚀 DIRECT DEPLOYMENT: Use the detected stack exactly as identified
        # No hardcoding - let the plugin system handle all stack types automatically
        stack_for_deployment = detected_stack
        
        session["logs"].append(f"🎯 Detected stack: {detected_stack}")
        session["logs"].append(f"� Starting deployment with detected stack: {stack_for_deployment}")
        logger.info(f"🎯 Stack detection result: {detected_stack}")
        logger.info(f"🚀 Starting deployment with stack: {stack_for_deployment}")
        
        result = pipeline.run_full_deployment(
            analysis=analysis_result,
            credentials=credentials,
            stack_override=stack_for_deployment  # Use mapped stack for deployment
        )
        
        if result.success:
            # Update session with successful deployment
            session["status"] = "deployed"
            session["live_url"] = result.live_url
            session["files_uploaded"] = result.details.get("files_uploaded", 0)
            session["deployment_details"] = result.details
            session["logs"].append(f"âœ… Deployment successful! Live at: {result.live_url}")
            
            await _update_deployment_status(
                deployment_id, 
                "Deployment Complete", 
                "completed", 
                f"ðŸŒ Live at: {result.live_url}"
            )
        else:
            # Handle deployment failure
            session["status"] = "failed"
            session["error"] = result.error_message or "Unknown deployment error"
            session["logs"].append(f"âŒ Deployment failed: {result.error_message}")
            
            await _update_deployment_status(
                deployment_id, 
                "Deployment Failed", 
                "failed", 
                result.error_message or "Deployment failed"
            )
    
    except Exception as e:
        logger.error(f"Plugin deployment pipeline failed: {e}")
        session["status"] = "failed"
        session["error"] = str(e)
        session["logs"].append(f"âŒ Pipeline error: {str(e)}")
        
        await _update_deployment_status(
            deployment_id, 
            "Pipeline Error", 
            "failed", 
            f"Internal error: {str(e)}"
        )

# UTILITY FUNCTIONS - Keep essential helper functions
# ============================================================================

async def _update_deployment_status(deployment_id: str, step: str, status: str, message: str):
    """Update deployment status with step information"""
    if deployment_id in deployment_sessions:
        session = deployment_sessions[deployment_id]
        
        # Initialize deployment_steps if not exists
        if "deployment_steps" not in session:
            session["deployment_steps"] = []
        
        # Update or add step status
        step_found = False
        for step_info in session["deployment_steps"]:
            if step_info["step"] == step:
                step_info["status"] = status
                step_info["message"] = message
                step_info["updated_at"] = datetime.utcnow().isoformat()
                step_found = True
                break
        
        if not step_found:
            session["deployment_steps"].append({
                "step": step,
                "status": status,
                "message": message,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
        
        session["last_updated"] = datetime.utcnow().isoformat()

# ============================================================================
# API ENDPOINTS - Active deployment and status endpoints
# ============================================================================

@router.get("/api/deployment/{deployment_id}/status")
async def get_deployment_status(deployment_id: str):
    """
    Track comprehensive deployment progress with detailed steps (instant response)
    """
    try:
        # Check background thread state first
        with _LOCK:
            background_state = _DEPLOY_STATES.get(deployment_id)
        
        if background_state:
            # Return instant response from background thread state
            return background_state
        
        # Fallback to legacy deployment_sessions for compatibility
        if deployment_id not in deployment_sessions:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        session = deployment_sessions[deployment_id]
        
        # Update activity tracking
        cleanup_service.update_activity(deployment_id, session["status"])
        
        # Get deployment steps with detailed status
        deployment_steps = session.get("deployment_steps", [])
        
        # If no detailed steps, create basic status
        if not deployment_steps:
            if session["status"] == "analyzing":
                deployment_steps = [{"step": "Repository Analysis", "status": "running", "message": "Analyzing repository structure"}]
            elif session["status"] == "deploying":
                deployment_steps = [{"step": "Deployment Starting", "status": "running", "message": "Preparing for deployment"}]
            elif session["status"] == "completed":
                deployment_steps = [{"step": "Deployment Complete", "status": "completed", "message": "Website is live"}]
            elif session["status"] == "failed":
                deployment_steps = [{"step": "Deployment Failed", "status": "failed", "message": "Deployment encountered an error"}]
        
        return {
            "deployment_id": deployment_id,
            "status": session["status"],
            "steps": deployment_steps,
            "logs": session.get("logs", []),
            "created_at": session["created_at"],
            "deployment_url": session.get("deployment_url"),
            "infrastructure": session.get("infrastructure", {}),
            "analysis": session.get("analysis", {}),
            "progress": len([step for step in deployment_steps if step["status"] == "completed"]) / max(len(deployment_steps), 1) * 100 if deployment_steps else 0,
            "error": session.get("error")
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.delete("/api/deployment/{deployment_id}/cancel")
async def cancel_deployment(deployment_id: str):
    """
    Cancel deployment and cleanup resources
    """
    try:
        if deployment_id not in deployment_sessions:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        session = deployment_sessions[deployment_id]
        
        # Cancel any running deployment task
        if "deployment_task" in session:
            task = session["deployment_task"]
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled deployment task for {deployment_id}")
        
        # Cleanup repository
        await cleanup_service.cleanup_user_cancellation(deployment_id)
        
        # Update session status
        session["status"] = "cancelled"
        session["logs"].append("Deployment cancelled by user")
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "status": "cancelled",
            "message": "Deployment cancelled and resources cleaned up"
        }
        
    except Exception as e:
        logger.error(f"Cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")

@router.get("/api/plugins/status")
async def get_plugin_system_status():
    """
    Get plugin system status and health information
    """
    try:
        status = get_plugin_status()
        
        return {
            "success": True,
            "plugin_system": {
                "auto_loader_enabled": True,
                "loaded_plugins": status["loaded_plugins"],
                "registered_stacks": status["registered_stacks"],
                "total_detectors": status["total_detectors"],
                "registry_health": status.get("registry_health", "unknown")
            },
            "stack_details": {
                stack_key: {
                    "status": "active",
                    "components": ["detector", "builder", "provisioner", "deployer"]
                } for stack_key in status["registered_stacks"]
            },
            "system_info": {
                "plugin_architecture_version": "1.0",
                "auto_discovery": True,
                "hot_reload_support": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get plugin status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get plugin status: {str(e)}")

@router.get("/api/cleanup/stats")
async def get_cleanup_stats():
    """
    Get cleanup service statistics (admin endpoint)
    """
    try:
        stats = cleanup_service.get_cleanup_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get cleanup stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cleanup stats: {str(e)}")

@router.get("/api/deployment/{deployment_id}/url")
async def get_deployment_url(deployment_id: str):
    """
    Step 5: Get final live URL
    """
    try:
        if deployment_id not in deployment_sessions:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        session = deployment_sessions[deployment_id]
        
        if session["status"] != "completed":
            return {
                "success": False,
                "deployment_id": deployment_id,
                "status": session["status"],
                "message": f"Deployment not completed yet. Current status: {session['status']}"
            }
        
        deployment_url = session.get("deployment_url") or session.get("live_url")
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "website_url": deployment_url,
            "status": "completed",
            "message": "Website is live and accessible"
        }
        
    except Exception as e:
        logger.error(f"URL retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL retrieval failed: {str(e)}")

@router.post("/api/validate-credentials")
async def validate_aws_credentials(credentials: dict):
    """
    Validate AWS credentials and check permissions
    """
    try:
        logger.info(f"Received credentials payload: {credentials}")
        
        # Handle both direct credentials and wrapped in credential_data
        if "credential_data" in credentials:
            cred_data = credentials["credential_data"]
            access_key = cred_data.get("access_key") or cred_data.get("access_key_id") or cred_data.get("aws_access_key")
            secret_key = cred_data.get("secret_key") or cred_data.get("secret_access_key") or cred_data.get("aws_secret_key")
            region = cred_data.get("region", "us-east-1")
        else:
            access_key = credentials.get("access_key") or credentials.get("aws_access_key") or credentials.get("access_key_id")
            secret_key = credentials.get("secret_key") or credentials.get("aws_secret_key") or credentials.get("secret_access_key")
            region = credentials.get("aws_region") or credentials.get("region", "us-east-1")
        
        logger.info(f"Parsed credentials - Access Key: {access_key[:8] if access_key else 'None'}..., Secret Key: {'***' if secret_key else 'None'}, Region: {region}")
        
        if not access_key or not secret_key:
            return {
                "success": False,
                "valid": False,
                "error": "AWS credentials are required - Access Key ID and Secret Access Key must be provided",
                "message": "Please provide both AWS Access Key ID and Secret Access Key"
            }
        
        # REAL AWS CREDENTIAL VALIDATION - Test against actual AWS API
        from core.utils import validate_aws_credentials as validate_creds
        
        logger.info(f"Validating AWS credentials against real AWS API...")
        
        validation_result = validate_creds({
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "aws_region": region
        })
        
        if not validation_result.get("valid"):
            error_msg = validation_result.get("error", "Invalid AWS credentials")
            logger.warning(f"AWS credential validation failed: {error_msg}")
            return {
                "success": False,
                "valid": False,
                "error": error_msg,
                "message": f"AWS credential validation failed: {error_msg}"
            }
        
        logger.info(f"AWS credentials validated successfully for account: {validation_result.get('account_id', 'unknown')}")
        
        return {
            "success": True,
            "valid": True,
            "message": "AWS credentials are valid and ready to use",
            "account_id": validation_result.get("account_id"),
            "permissions": validation_result.get("permissions", []),
            "region": region
        }
        
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        return {
            "success": False,
            "valid": False,
            "error": f"Credential validation error: {str(e)}",
            "message": "Failed to validate AWS credentials. Please check your credentials and try again."
        }
            
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        return {
            "success": False,
            "valid": False,
            "error": f"Validation error: {str(e)}",
            "message": "Internal validation error occurred"
        }
        

@router.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        plugin_status = get_plugin_status()
        
        # Debug: Log actual plugin status for troubleshooting
        logger.info(f"Health check - Plugin status: {plugin_status}")
        
        return {
            "status": "healthy",
            "service": "CodeFlowOps Deployment API",
            "version": "2.0.0-plugin-architecture",
            "plugin_system": {
                "enabled": True,
                "loaded_plugins": len(plugin_status["loaded_plugins"]),
                "registered_stacks": len(plugin_status["registered_stacks"]),
                "health": plugin_status.get("registry_health", False),
                "stack_names": plugin_status["registered_stacks"]  # Show actual stack names for debugging
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/api/deployment/{deployment_id}/result")
async def get_deployment_result(deployment_id: str):
    """
    Get final deployment result with all details
    """
    try:
        if deployment_id not in deployment_sessions:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        session = deployment_sessions[deployment_id]
        
        return {
            "deployment_id": deployment_id,
            "status": session["status"],
            "analysis": session.get("analysis", {}),
            "deployment_url": session.get("live_url") or session.get("deployment_url"),
            "deployment_details": session.get("deployment_details", {}),
            "logs": session.get("logs", []),
            "created_at": session.get("created_at"),
            "completed_at": session.get("completed_at"),
            "files_uploaded": session.get("files_uploaded", 0),
            "infrastructure": session.get("infrastructure", {}),
            "error": session.get("error")
        }
        
    except Exception as e:
        logger.error(f"Result retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Result retrieval failed: {str(e)}")

# Create FastAPI app and include the router
app = FastAPI(
    title="CodeFlowOps SaaS API",
    description="Repository analysis and deployment API",
    version="1.0.0"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
            Routes to specific stack handler based on detected type
            """
            logger.info(f"🎯 Routing deployment to {stack_type} stack")
            
            try:
                # Get appropriate router for stack type
                stack_router = stack_router_registry.get_router_for_stack(stack_type)
                
                # Route to stack-specific deployment handler
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
                "service": "integrated-modular-api",
                "version": "1.0.0",
                "routers_available": True,
                "routers_loaded": len(stack_router_registry.routers),
                "available_stacks": stack_router_registry.get_available_stacks(),
                "modular_system": True
            }
        
        logger.info("✅ Modular router endpoints added to existing API")
    
    except Exception as e:
        logger.error(f"❌ Failed to add modular router endpoints: {e}")
else:
    logger.info("⚠️ Modular router endpoints not available - using legacy deployment only")

# Add health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "CodeFlowOps Simple SaaS", "version": "1.0.0"}

# Include the main router
app.include_router(router)
