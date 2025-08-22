"""
Core Analysis Router
Handles repository analysis endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import tempfile
import os
from pathlib import Path

# Import analysis components
import sys
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

try:
    from enhanced_repository_analyzer import EnhancedRepositoryAnalyzer
    ENHANCED_ANALYZER_AVAILABLE = True
except ImportError:
    ENHANCED_ANALYZER_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()

class AnalysisRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    analysis_type: Optional[str] = "full"

class AnalysisResponse(BaseModel):
    success: bool
    project_type: Optional[str] = None
    detected_stack: Optional[str] = None
    recommended_stack: Optional[str] = None
    confidence: Optional[float] = None
    infrastructure: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/analyze-repo", response_model=AnalysisResponse)
async def analyze_repository(request: AnalysisRequest):
    """
    Analyze repository and detect stack type
    Core analysis endpoint that routes to appropriate stack handler
    """
    logger.info(f"📊 Analyzing repository: {request.repo_url}")
    
    temp_dir = None
    try:
        # Clone repository to temp directory
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "repo"
        
        # Clone repository (simplified for demo)
        import subprocess
        result = subprocess.run([
            "git", "clone", "--depth", "1", 
            "--branch", request.branch,
            request.repo_url, str(repo_path)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            raise Exception(f"Failed to clone repository: {result.stderr}")
        
        # Use enhanced analyzer if available
        if ENHANCED_ANALYZER_AVAILABLE:
            analyzer = EnhancedRepositoryAnalyzer()
            analysis_result = analyzer.analyze_repository_enhanced(str(repo_path))
        else:
            # Fallback to basic analysis
            analysis_result = {
                "success": True,
                "project_type": "unknown",
                "detected_stack": "generic",
                "recommended_stack": "static",
                "confidence": 0.5
            }
        
        return AnalysisResponse(**analysis_result)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return AnalysisResponse(
            success=False,
            error=str(e)
        )
    
    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.get("/health")
async def analysis_health():
    """Health check for analysis service"""
    return {
        "status": "healthy",
        "service": "analysis",
        "enhanced_analyzer": ENHANCED_ANALYZER_AVAILABLE
    }
