#!/usr/bin/env python3
"""
AWS Elastic Beanstalk Application Entry Point
"""

import sys
import os
from typing import Any

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI application
app: Any = None

try:
    from simple_api import app  # type: ignore
    print("✅ Successfully imported simple_api.app")
except ImportError as e:
    print(f"❌ Failed to import simple_api: {e}")
    # Fallback import
    try:
        from backend.simple_api import app  # type: ignore
        print("✅ Successfully imported backend.simple_api.app")
    except ImportError as e2:
        print(f"❌ Failed to import backend.simple_api: {e2}")
        raise e2

# Elastic Beanstalk expects an 'application' object
application = app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
