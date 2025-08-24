#!/usr/bin/env python3
"""
AWS Elastic Beanstalk Entry Point - FIXED VERSION
No more variable scope errors!
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Starting CodeFlowOps Backend - FIXED VERSION")

# Initialize application variable
application = None
error_details = ""

try:
    # Import the main application
    from main import app
    application = app
    print("Successfully loaded CodeFlowOps Enhanced API")
    print("Enhanced Repository Analyzer: ACTIVE")
    print("Static Site Detection: ENABLED")
    
except Exception as main_error:
    error_details = str(main_error)
    print(f"Failed to import main application: {error_details}")
    
    # Create fallback app with proper error handling
    try:
        from fastapi import FastAPI
        application = FastAPI(title="CodeFlowOps Backend - Fallback")
        
        @application.get("/")
        async def root():
            return {
                "message": "CodeFlowOps Backend - Fallback Mode",
                "status": "limited_functionality",
                "error": error_details,
                "note": "Main application failed to load"
            }
        
        @application.get("/health")
        async def health():
            return {
                "status": "degraded", 
                "mode": "fallback",
                "error": error_details
            }
        
        print("Fallback mode activated")
        
    except Exception as fallback_error:
        print(f"Fallback failed: {fallback_error}")
        
        # Create minimal emergency app
        from fastapi import FastAPI
        application = FastAPI()
        
        @application.get("/")
        async def emergency():
            return {"message": "Emergency mode", "error": str(fallback_error)}

# Ensure application is never None
if application is None:
    from fastapi import FastAPI
    application = FastAPI()
    
    @application.get("/")
    async def default():
        return {"message": "Default emergency mode"}

print(f"Application ready: {type(application).__name__}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
