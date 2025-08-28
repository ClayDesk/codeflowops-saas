"""
AWS Elastic Beanstalk Entry Point for CodeFlowOps SaaS Backend
This file imports the main FastAPI application from simple_api.py
"""

import sys
import os

# Fix GitPython issue BEFORE any other imports
os.environ['GIT_PYTHON_REFRESH'] = 'quiet'

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print(f"🔍 Current working directory: {os.getcwd()}")
print(f"🔍 Python path: {sys.path[:3]}...")
print(f"🔍 GIT_PYTHON_REFRESH: {os.environ.get('GIT_PYTHON_REFRESH', 'NOT SET')}")

try:
    # Import the FastAPI app from simple_api.py
    print("🔄 Attempting to import from simple_api...")
    from simple_api import app
    
    # This is the WSGI/ASGI application that Elastic Beanstalk will use
    application = app
    
    print("✅ Successfully imported FastAPI app from simple_api")
    
except ImportError as e:
    print(f"❌ Failed to import from simple_api: {e}")
    
    # Fallback: try to import from src.main
    try:
        print("🔄 Attempting fallback import from src.main...")
        from src.main import app
        application = app
        print("✅ Fallback: Successfully imported FastAPI app from src.main")
    except ImportError as fallback_error:
        print(f"❌ Fallback also failed: {fallback_error}")
        
        # Last resort: create a basic FastAPI app
        print("🔄 Creating basic fallback FastAPI app...")
        from fastapi import FastAPI
        app = FastAPI(title="CodeFlowOps SaaS Backend - Emergency Fallback", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {
                "message": "CodeFlowOps Backend - Emergency Fallback Mode",
                "status": "degraded",
                "error": f"Failed to load main application: {e}. Fallback error: {fallback_error}"
            }
        
        @app.get("/health")
        async def health():
            return {
                "status": "degraded", 
                "error": f"Failed to initialize: {e}. Fallback error: {fallback_error}"
            }
        
        application = app
        print("✅ Emergency fallback: Created basic FastAPI app")

# For local development/testing
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CodeFlowOps API server locally...")
    uvicorn.run(application, host="0.0.0.0", port=8000, reload=False)
