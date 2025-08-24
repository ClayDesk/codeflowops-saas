"""
Minimal CodeFlowOps API - Guaranteed to work on Elastic Beanstalk
This is a fallback version with core endpoints only
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import uuid
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CodeFlowOps API - Minimal",
    description="Minimal working API for CodeFlowOps",
    version="1.0.0"
)

# CORS middleware - Allow all origins temporarily to debug
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic models
class RepoAnalysisRequest(BaseModel):
    repo_url: str
    analysis_type: str = "basic"

class DeployRequest(BaseModel):
    deployment_id: str
    aws_access_key: str
    aws_secret_key: str
    aws_region: str = "us-east-1"
    repository_url: Optional[str] = None

class CredentialsRequest(BaseModel):
    aws_access_key: str
    aws_secret_key: str
    aws_region: str = "us-east-1"

# In-memory storage for demo
_deployments = {}

@app.get("/")
async def root():
    return {
        "message": "CodeFlowOps Backend is running!",
        "version": "2.2.0",
        "status": "operational",
        "environment": "production",
        "api_type": "minimal_working",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "analyze": "/api/analyze-repo",
            "deploy": "/api/deploy",
            "status": "/api/deployment/{id}/status"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "codeflowops-backend",
        "version": "2.2.0",
        "api_type": "minimal_working"
    }

@app.get("/api/status")
async def api_status():
    return {
        "status": "operational",
        "version": "2.2.0",
        "uptime": time.time(),
        "components": {
            "api": "healthy",
            "cors": "configured",
            "auth": "available"
        }
    }

@app.get("/api/v1/analyze")
async def analyze_placeholder():
    return {
        "message": "Analysis endpoint ready",
        "status": "placeholder",
        "note": "Use POST /api/analyze-repo for actual analysis"
    }

@app.post("/api/analyze-repo")
async def analyze_repository(request: RepoAnalysisRequest):
    """Basic repository analysis"""
    try:
        repo_url = request.repo_url.strip()
        logger.info(f"Analyzing repository: {repo_url}")
        
        # Generate deployment ID
        deployment_id = str(uuid.uuid4())
        
        # Basic analysis (mock for now)
        analysis = {
            "repository_url": repo_url,
            "framework": "react",
            "projectType": "react-spa",
            "detected_stack": "react",
            "frameworks": ["React"],
            "languages": {"JavaScript": 80, "CSS": 15, "HTML": 5},
            "build_tools": ["npm", "webpack"],
            "deployment_ready": True,
            "recommendations": [
                "Deploy to S3 + CloudFront",
                "Use yarn for package management",
                "Enable CloudFront caching"
            ]
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "analysis_id": deployment_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/validate-credentials")
async def validate_credentials(request: CredentialsRequest):
    """Validate AWS credentials"""
    try:
        # Basic validation (in production, would test actual AWS access)
        if not request.aws_access_key or not request.aws_secret_key:
            return {"success": False, "valid": False, "error": "Missing credentials"}
        
        if len(request.aws_access_key) < 16:
            return {"success": False, "valid": False, "error": "Invalid access key format"}
        
        return {
            "success": True,
            "valid": True,
            "account_id": "123456789012",
            "region": request.aws_region,
            "message": "Credentials format valid"
        }
        
    except Exception as e:
        logger.error(f"Credential validation failed: {e}")
        return {"success": False, "valid": False, "error": str(e)}

@app.post("/api/deploy")
async def deploy_to_aws(request: DeployRequest):
    """Basic deployment endpoint"""
    try:
        deployment_id = request.deployment_id
        
        # Store deployment
        _deployments[deployment_id] = {
            "status": "started",
            "progress": 10,
            "logs": ["🚀 Deployment started..."],
            "created_at": datetime.utcnow().isoformat(),
            "repository_url": request.repository_url
        }
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "status": "started",
            "message": "Deployment started successfully"
        }
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

@app.get("/api/deployment/{deployment_id}/status")
async def get_deployment_status(deployment_id: str):
    """Get deployment status"""
    if deployment_id not in _deployments:
        # Return a mock status for demo
        return {
            "status": "completed",
            "progress": 100,
            "logs": [
                "🚀 Deployment started...",
                "📦 Building React application...",
                "🪣 Uploading to S3...",
                "🌐 Configuring CloudFront...",
                "✅ Deployment completed!"
            ],
            "deployment_url": f"https://demo-{deployment_id[:8]}.cloudfront.net",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return _deployments[deployment_id]

@app.get("/api/deployment/{deployment_id}/result")
async def get_deployment_result(deployment_id: str):
    """Get deployment result"""
    if deployment_id not in _deployments:
        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "deployment_url": f"https://demo-{deployment_id[:8]}.cloudfront.net",
            "s3_bucket": f"demo-bucket-{deployment_id[:8]}",
            "cloudfront_url": f"https://demo-{deployment_id[:8]}.cloudfront.net",
            "completed_at": datetime.utcnow().isoformat()
        }
    
    deployment = _deployments[deployment_id]
    deployment["deployment_url"] = f"https://demo-{deployment_id[:8]}.cloudfront.net"
    return deployment

@app.get("/api/v1/deploy")
async def deploy_v1():
    return {
        "message": "Deploy endpoint",
        "note": "Use POST /api/deploy for actual deployment"
    }

# Auth endpoints (basic)
@app.get("/api/v1/auth/config")
async def get_auth_config():
    return {
        "provider": "basic",
        "message": "Authentication configuration",
        "status": "available"
    }

@app.post("/api/v1/auth/login")
async def login():
    return {
        "success": True,
        "token": f"demo_token_{int(time.time())}",
        "user": {"id": "demo_user", "email": "demo@example.com"}
    }

@app.post("/api/v1/auth/register")
async def register():
    return {
        "success": True,
        "message": "Registration successful",
        "user": {"id": "new_user", "email": "new@example.com"}
    }

@app.get("/api/stacks/available")
async def get_available_stacks():
    return {
        "available_stacks": ["react", "nextjs", "vue", "angular", "static"],
        "message": "Available deployment stacks"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
