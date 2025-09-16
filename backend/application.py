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
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(title="CodeFlowOps SaaS Backend - Emergency Fallback", version="1.0.0")
        
        # Add CORS middleware to emergency fallback
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
                "error": f"Failed to initialize: {e}. Fallback error: {fallback_error}",
                "message": "Running in fallback mode"
            }
        
        # Try to add emergency auth functionality
        try:
            from emergency_auth import router as emergency_auth_router
            app.include_router(emergency_auth_router)
            print("✅ Emergency auth service loaded")
        except Exception as auth_error:
            print(f"⚠️ Emergency auth also failed: {auth_error}")
            
            # Basic fallback endpoints
            @app.get("/api/v1/auth/status")
            async def auth_status():
                return {
                    "service": "authentication",
                    "status": "unavailable",
                    "provider": "aws_cognito",
                    "message": "Backend in emergency fallback mode - auth not available"
                }
            
            @app.post("/api/v1/auth/login")
            async def login_fallback():
                raise HTTPException(
                    status_code=503,
                    detail="Authentication service unavailable - backend in emergency fallback mode"
                )
        
        application = app
        print("✅ Emergency fallback: Created basic FastAPI app")

# For local development/testing
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CodeFlowOps API server locally...")
    uvicorn.run(application, host="0.0.0.0", port=8000, reload=False)
