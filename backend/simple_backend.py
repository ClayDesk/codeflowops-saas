#!/usr/bin/env python3
"""
Simple Backend Server - Main Entry Point
"""

import uvicorn
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main server entry point"""
    try:
        logger.info("🚀 Starting CodeFlowOps Backend Server...")
        
        # Import the FastAPI app
        from simple_api import app
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
