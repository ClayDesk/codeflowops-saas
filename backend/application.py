"""
AWS Elastic Beanstalk Entry Point for CodeFlowOps SaaS Backend
This file imports the main FastAPI application from simple_api.py
"""

try:
    # Import the FastAPI app from simple_api.py
    from simple_api import app
    
    # This is the WSGI/ASGI application that Elastic Beanstalk will use
    application = app
    
    print("✅ Successfully imported FastAPI app from simple_api")
    
except ImportError as e:
    print(f"❌ Failed to import from simple_api: {e}")
    
    # Fallback: try to import from src.main
    try:
        from src.main import app
        application = app
        print("✅ Fallback: Successfully imported FastAPI app from simple_api")
    except ImportError as fallback_error:
        print(f"❌ Fallback also failed: {fallback_error}")
        raise ImportError("Could not import FastAPI app from either src.main or simple_api")

# For local development/testing
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CodeFlowOps API server locally...")
    uvicorn.run(application, host="0.0.0.0", port=8000, reload=False)
