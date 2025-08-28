"""
Main entry point for CodeFlowOps SaaS Backend
This file imports the main FastAPI application from simple_api.py
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import the FastAPI app from simple_api.py
    from simple_api import app
    
    print("✅ Successfully imported FastAPI app from simple_api")
    
except ImportError as e:
    print(f"❌ Failed to import from simple_api: {e}")
    
    # Fallback: create a basic FastAPI app
    from fastapi import FastAPI
    app = FastAPI(title="CodeFlowOps SaaS Backend - Fallback", version="1.0.0")
    
    @app.get("/")
    async def root():
        return {
            "message": "CodeFlowOps Backend - Fallback Mode",
            "status": "degraded",
            "error": f"Failed to load main application: {e}"
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "degraded", 
            "error": f"Failed to initialize: {e}"
        }
    
    print("✅ Fallback: Created basic FastAPI app")

# For WSGI compatibility (used by Elastic Beanstalk)
application = app

# For local development/testing
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CodeFlowOps API server locally...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
