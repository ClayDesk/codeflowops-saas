"""
Dedicated React API Server
==========================

Simple FastAPI server specifically for React deployments.
Uses the dedicated ReactDeployer class for clean, focused React deployment handling.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import Dict, Any
import uvicorn

from react_deployer import ReactDeployer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="React Deployment API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class RepositoryAnalysisRequest(BaseModel):
    repository_url: str

class ReactDeploymentRequest(BaseModel):
    analysis_id: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"

# Global storage for analysis sessions (in production, use a proper database)
analysis_sessions: Dict[str, Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "react-deployment-api"}

@app.post("/api/analyze-repository")
async def analyze_repository(request: RepositoryAnalysisRequest):
    """Analyze a GitHub repository for React deployment"""
    try:
        logger.info(f"🔍 Analyzing repository: {request.repository_url}")
        
        deployer = ReactDeployer()
        analysis = deployer.analyze_react_repository(request.repository_url)
        
        if analysis.get("status") == "error":
            raise HTTPException(status_code=400, detail=analysis.get("error"))
        
        # Store analysis session
        analysis_id = analysis["analysis_id"]
        analysis_sessions[analysis_id] = {
            "analysis": analysis,
            "deployer": deployer,  # Keep the deployer instance with the cloned repo
            "status": "analyzed"
        }
        
        logger.info(f"✅ Analysis completed: {analysis_id}")
        
        return {
            "analysis_id": analysis_id,
            "framework": analysis["framework"],
            "language": analysis["language"],
            "build_tool": analysis["build_tool"],
            "dependencies": analysis["dependencies"],
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Repository analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deploy")
async def deploy_react_app(request: ReactDeploymentRequest):
    """Deploy a React application to AWS"""
    try:
        logger.info(f"🚀 Starting React deployment: {request.analysis_id}")
        
        # Get analysis session
        if request.analysis_id not in analysis_sessions:
            raise HTTPException(status_code=404, detail="Analysis session not found")
        
        session = analysis_sessions[request.analysis_id]
        deployer = session["deployer"]
        
        # Prepare AWS credentials
        aws_credentials = {
            "aws_access_key_id": request.aws_access_key_id,
            "aws_secret_access_key": request.aws_secret_access_key,
            "aws_region": request.aws_region
        }
        
        # Deploy the React app
        deployment_result = deployer.deploy_react_app(request.analysis_id, aws_credentials)
        
        if deployment_result.get("status") == "error":
            raise HTTPException(status_code=500, detail={
                "stage": deployment_result.get("stage", "unknown"),
                "error": deployment_result.get("error")
            })
        
        # Update session
        session["deployment"] = deployment_result
        session["status"] = "deployed"
        
        logger.info(f"✅ React deployment successful: {deployment_result['deployment_id']}")
        
        return {
            "deployment_id": deployment_result["deployment_id"],
            "website_url": deployment_result["website_url"],
            "s3_bucket": deployment_result["s3_bucket"],
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ React deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deployment-status")
async def get_deployment_status(request: dict):
    """Get deployment status"""
    deployment_id = request.get("deployment_id")
    
    if not deployment_id:
        raise HTTPException(status_code=400, detail="deployment_id required")
    
    # Find deployment in sessions
    for session in analysis_sessions.values():
        if (session.get("deployment") and 
            session["deployment"].get("deployment_id") == deployment_id):
            return {
                "deployment_id": deployment_id,
                "status": session["status"],
                "website_url": session["deployment"].get("website_url")
            }
    
    raise HTTPException(status_code=404, detail="Deployment not found")

@app.get("/api/sessions")
async def get_active_sessions():
    """Get active analysis and deployment sessions (for debugging)"""
    return {
        "active_sessions": len(analysis_sessions),
        "sessions": {
            session_id: {
                "framework": session["analysis"].get("framework"),
                "status": session["status"],
                "has_deployment": "deployment" in session
            }
            for session_id, session in analysis_sessions.items()
        }
    }

if __name__ == "__main__":
    print("🚀 Starting React Deployment API Server")
    print("=" * 50)
    print("URL: http://localhost:8001")
    print("Health: http://localhost:8001/health")
    print("Docs: http://localhost:8001/docs")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
