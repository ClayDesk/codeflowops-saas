#!/usr/bin/env python3
"""
AWS Elastic Beanstalk Application Entry Point
"""

# Import the FastAPI application
from backend.simple_api import app

# Elastic Beanstalk expects an 'application' object
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
