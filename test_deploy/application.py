"""
AWS Elastic Beanstalk entry point for CodeFlowOps FastAPI application
"""
import sys
import os
from typing import Any

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

app: Any = None
application: Any = None

try:
    # Try the simplified version first
    from main_simple import app  # type: ignore
    application = app
    print("✅ Loaded main_simple.py successfully")
    
except ImportError:
    try:
        # Fallback to original main.py
        from main import app  # type: ignore
        application = app
        print("✅ Loaded main.py successfully")
    except ImportError as e:
        # Final fallback minimal app
        from fastapi import FastAPI
        
        app = FastAPI(title="CodeFlowOps Fallback", version="1.0.0")
        
        @app.get("/")
        async def root():
            return {
                "message": "CodeFlowOps Backend - Fallback Mode", 
                "status": "running",
                "error": f"Import error: {str(e)}"
            }
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy", "mode": "fallback"}
        
        application = app
        print("⚠️ Using fallback mode due to import error:", str(e))

print(f"🚀 Application ready: {type(application).__name__}")
