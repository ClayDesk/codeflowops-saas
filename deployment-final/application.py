import sys
import os
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Starting CodeFlowOps Backend - FIXED VERSION")

application = None
error_msg = ""

try:
    from main import app
    application = app
    print("Successfully loaded CodeFlowOps Enhanced API")
    print("Enhanced Repository Analyzer: ACTIVE")
    
except Exception as e:
    error_msg = str(e)
    print(f"Failed to import main: {error_msg}")
    
    try:
        from fastapi import FastAPI
        application = FastAPI()
        
        @application.get("/")
        async def root():
            return {"message": "Fallback mode", "error": error_msg}
        
        @application.get("/health")
        async def health():
            return {"status": "degraded", "error": error_msg}
        
        print("Fallback mode activated")
        
    except Exception as fallback_err:
        print(f"Fallback failed: {fallback_err}")
        from fastapi import FastAPI
        application = FastAPI()
        
        @application.get("/")
        async def emergency():
            return {"message": "Emergency mode"}

if application is None:
    from fastapi import FastAPI
    application = FastAPI()
    @application.get("/")
    async def default():
        return {"message": "Default mode"}

print(f"Application ready: {type(application).__name__}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
