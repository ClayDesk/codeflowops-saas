"""
Test application.py that imports the minimal test app
"""

try:
    # Import the minimal test app
    from test_minimal import app
    
    # This is the WSGI/ASGI application that Elastic Beanstalk will use
    application = app
    
    print("✅ Successfully imported minimal test app")
    
except ImportError as e:
    print(f"❌ Failed to import test_minimal: {e}")
    
    # Create a basic fallback app
    from fastapi import FastAPI
    
    fallback_app = FastAPI()
    
    @fallback_app.get("/health")
    async def health():
        return {"status": "error", "message": f"Import failed: {str(e)}"}
    
    application = fallback_app
    print("✅ Created fallback test app")

# For local development/testing
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting test API server...")
    uvicorn.run(application, host="0.0.0.0", port=8000, reload=False)
