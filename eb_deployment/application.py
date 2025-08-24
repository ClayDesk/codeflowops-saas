#!/usr/bin/env python3
'''
Elastic Beanstalk entry point for CodeFlowOps Backend
Uses the working simple_api.py with full endpoint support
'''
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI app from main.py (which is simple_api.py)
try:
    from main import app as application
    print("✅ CodeFlowOps Simple API loaded successfully")
    print("Available endpoints:")
    print("  POST /api/analyze-repo - Repository analysis")
    print("  POST /api/validate-credentials - AWS credential validation")
    print("  POST /api/deploy - Full deployment pipeline")
    print("  GET /api/deployment/{id}/status - Deployment status")
    print("  GET /api/deployment/{id}/result - Deployment results")
    print("  POST /api/v1/auth/login - Authentication")
    print("  GET /api/stacks/available - Available stacks")
except ImportError as e:
    print(f"❌ Failed to import application: {e}")
    # Create a minimal fallback app
    from fastapi import FastAPI
    application = FastAPI(title="CodeFlowOps Backend - Fallback")
    
    @application.get("/")
    async def root():
        return {
            "message": "CodeFlowOps Backend - Import Failed",
            "status": "error", 
            "error": f"Failed to load main application: {e}"
        }
    
    @application.get("/health")
    async def health():
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
