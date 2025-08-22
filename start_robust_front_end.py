#!/usr/bin/env python3
"""
🎨 Robust Frontend Startup Script  
Starts the enhanced CodeFlowOps frontend with database UI support
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    print("🎨 Starting CodeFlowOps Robust Frontend Server...")
    print("🔥 Features: Firebase/Supabase UI, Database detection display, Security status indicators")
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    print(f"📁 Working directory: {frontend_dir}")
    print("⚡ Installing dependencies and starting Next.js development server...")
    
    try:
        # Check if node_modules exists, if not install dependencies
        if not (frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            subprocess.run(["npm", "install"], check=True, shell=True)
        
        print("🚀 Starting Next.js development server...")
        # Start the frontend development server
        subprocess.run(["npm", "run", "dev"], check=True, shell=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped by user")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        print("💡 Make sure Node.js and npm are installed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
