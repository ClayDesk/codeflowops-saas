"""
Analysis API Endpoints
FastAPI endpoints for repository analysis services
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional, List
import logging
from dataclasses import asdict

from ..services.analysis.analysis_reporter import AnalysisReporter, ComprehensiveAnalysisResult
from ..services.analysis.repository_analyzer import RepositoryAnalyzer
from ..services.analysis.project_type_detector import ProjectTypeDetector
from ..services.analysis.dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Initialize analysis components
analysis_reporter = AnalysisReporter()
repository_analyzer = RepositoryAnalyzer()
project_type_detector = ProjectTypeDetector()
dependency_analyzer = DependencyAnalyzer()

# Request/Response Models
class AnalysisRequest(BaseModel):
    repository_url: HttpUrl
    deep_analysis: Optional[bool] = True
    include_dependencies: Optional[bool] = True
    include_security_scan: Optional[bool] = True

class AnalysisResponse(BaseModel):
    session_id: str
    message: str
    status: str

class StatusResponse(BaseModel):
    session_id: str
    status: str
    progress: float
    current_phase: str
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

class QuickAnalysisRequest(BaseModel):
    repository_url: HttpUrl
    branch: Optional[str] = "main"

class QuickAnalysisResponse(BaseModel):
    repository_url: str
    project_types: List[Dict[str, Any]]
    primary_type: Optional[Dict[str, Any]]
    file_count: int
    confidence_score: float
    basic_info: Dict[str, Any]

# Endpoints

@router.post("/start", response_model=AnalysisResponse)
async def start_comprehensive_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a comprehensive repository analysis
    """
    try:
        # Start analysis session
        session_id = await analysis_reporter.start_analysis(str(request.repository_url))
        
        # Schedule background analysis
        background_tasks.add_task(
            run_background_analysis,
            session_id,
            request.deep_analysis,
            request.include_dependencies,
            request.include_security_scan
        )
        
        return AnalysisResponse(
            session_id=session_id,
            message="Analysis started successfully",
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {str(e)}"
        )

@router.get("/status/{session_id}", response_model=StatusResponse)
async def get_analysis_status(session_id: str):
    """
    Get the status of an ongoing analysis
    """
    try:
        status_info = await analysis_reporter.get_analysis_status(session_id)
        
        if "error" in status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis session not found"
            )
        
        return StatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )

@router.get("/result/{session_id}")
async def get_analysis_result(session_id: str):
    """
    Get the complete analysis result
    """
    try:
        # Check if analysis is completed
        status_info = await analysis_reporter.get_analysis_status(session_id)
        
        if "error" in status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis session not found"
            )
        
        if status_info["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail=f"Analysis still in progress. Current status: {status_info['status']}"
            )
        
        # Get the complete result (in a real implementation, this would be stored)
        # For now, we'll return the session info
        return JSONResponse(content={
            "session_id": session_id,
            "status": "completed",
            "message": "Analysis completed successfully. Full result retrieval not yet implemented.",
            "next_steps": [
                "Implement result storage in database",
                "Add comprehensive result serialization",
                "Include detailed recommendations"
            ]
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis result: {str(e)}"
        )

@router.post("/quick")
async def quick_analysis(request: QuickAnalysisRequest):
    """
    Perform a quick repository analysis without full dependency scanning
    """
    try:
        logger.info(f"Starting quick analysis for {request.repository_url}")
        
        # Perform basic repository analysis
        repo_result = await repository_analyzer.analyze_repository(
            str(request.repository_url),
            "quick-analysis"
        )
        
        # Detect project types
        project_types = repo_result.project_types  # Use already detected project types
        
        # Get primary project type
        primary_type = repo_result.primary_project_type
        
        # Build response
        response = QuickAnalysisResponse(
            repository_url=str(request.repository_url),
            project_types=[asdict(pt) for pt in project_types],
            primary_type=asdict(primary_type) if primary_type else None,
            file_count=repo_result.total_files,
            confidence_score=repo_result.confidence_score,
            basic_info={
                "languages": repo_result.languages,
                "frameworks": repo_result.frameworks,
                "build_tools": repo_result.build_tools,
                "config_files": repo_result.config_files,
                "has_tests": any(f.is_test for f in repo_result.file_tree),
                "missing_files": repo_result.missing_files
            }
        )
        
        # Wrap in analysis object for frontend compatibility
        return {
            "analysis": {
                "repository_name": str(request.repository_url).split('/')[-1],
                "project_types": [asdict(pt) for pt in project_types],
                "primary_type": asdict(primary_type) if primary_type else None,
                "total_files": repo_result.total_files,
                "confidence_score": primary_type.confidence if primary_type else 40.0,
                "languages": repo_result.languages,
                "frameworks": repo_result.frameworks,
                "build_tools": repo_result.build_tools,
                "config_files": repo_result.config_files,
                "dependencies": repo_result.dependencies,
                "file_tree": [asdict(f) for f in repo_result.file_tree],
                "missing_files": repo_result.missing_files,
                "has_tests": any(f.is_test for f in repo_result.file_tree),
                "description": f"Repository with {repo_result.total_files} files",
                "primary_language": list(repo_result.languages.keys())[0] if repo_result.languages else "Unknown",
                "key_files": repo_result.config_files,
                "last_updated": repo_result.analysis_timestamp,
                "private": False,
                "default_branch": "main",
                "topics": [],
                "stars": 0,
                "forks": 0,
                "size": sum(f.size or 0 for f in repo_result.file_tree if f.size)
            }
        }
        
    except Exception as e:
        logger.error(f"Quick analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick analysis failed: {str(e)}"
        )

@router.delete("/session/{session_id}")
async def cleanup_analysis_session(session_id: str):
    """
    Clean up an analysis session
    """
    try:
        analysis_reporter.cleanup_session(session_id)
        
        return JSONResponse(content={
            "message": "Session cleaned up successfully",
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Failed to cleanup session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup session: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the analysis service
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "analysis-api",
        "components": {
            "repository_analyzer": "operational",
            "project_type_detector": "operational",
            "dependency_analyzer": "operational",
            "analysis_reporter": "operational"
        }
    })

# Background task function
async def run_background_analysis(
    session_id: str,
    deep_analysis: bool = True,
    include_dependencies: bool = True,
    include_security_scan: bool = True
):
    """
    Run comprehensive analysis in the background
    """
    try:
        logger.info(f"Starting background analysis for session {session_id}")
        
        # Run comprehensive analysis
        result = await analysis_reporter.run_comprehensive_analysis(session_id)
        
        # In a real implementation, we would store the result in a database
        # For now, we'll just log completion
        logger.info(f"Background analysis completed for session {session_id}")
        
        # Store result (mock implementation)
        # await store_analysis_result(session_id, result)
        
    except Exception as e:
        logger.error(f"Background analysis failed for session {session_id}: {str(e)}")
        # Update session status to failed
        # await update_session_status(session_id, "failed", str(e))

# Additional utility endpoints

@router.get("/supported-types")
async def get_supported_project_types():
    """
    Get list of supported project types
    """
    return JSONResponse(content={
        "supported_types": [
            {
                "type": "React",
                "description": "React.js applications with Create React App or custom webpack setup",
                "frameworks": ["React", "Create React App", "Vite"],
                "build_tools": ["webpack", "vite", "parcel"]
            },
            {
                "type": "Next.js",
                "description": "Next.js applications with SSR/SSG capabilities",
                "frameworks": ["Next.js"],
                "build_tools": ["webpack", "turbopack"]
            },
            {
                "type": "Vue.js",
                "description": "Vue.js applications with Vue CLI or Vite",
                "frameworks": ["Vue.js", "Vue CLI", "Nuxt.js"],
                "build_tools": ["webpack", "vite", "rollup"]
            },
            {
                "type": "Angular",
                "description": "Angular applications with Angular CLI",
                "frameworks": ["Angular"],
                "build_tools": ["Angular CLI", "webpack"]
            },
            {
                "type": "Static Site",
                "description": "Static HTML/CSS/JS websites",
                "frameworks": ["None", "Jekyll", "Hugo", "Gatsby"],
                "build_tools": ["None", "Jekyll", "Hugo", "Gatsby"]
            },
            {
                "type": "Python",
                "description": "Python applications (Flask, Django, FastAPI)",
                "frameworks": ["Flask", "Django", "FastAPI", "Streamlit"],
                "build_tools": ["pip", "poetry", "pipenv"]
            }
        ]
    })

@router.get("/analysis-metrics")
async def get_analysis_metrics():
    """
    Get analysis service metrics
    """
    active_sessions = len(analysis_reporter.active_sessions)
    
    return JSONResponse(content={
        "active_sessions": active_sessions,
        "session_details": [
            {
                "session_id": session.session_id,
                "status": session.status,
                "progress": session.progress,
                "started_at": session.started_at.isoformat()
            }
            for session in analysis_reporter.active_sessions.values()
        ]
    })

# Note: Error handlers are registered on the main FastAPI app, not the router
