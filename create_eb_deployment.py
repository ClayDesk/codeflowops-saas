#!/usr/bin/env python3
"""
Create Elastic Beanstalk deployment package for CodeFlowOps Backend
"""
import os
import zipfile
import shutil
from pathlib import Path
import json

def create_eb_deployment_package():
    """Create a deployment package optimized for Elastic Beanstalk"""
    
    # Paths
    backend_dir = Path(__file__).parent / "backend"
    deployment_dir = Path(__file__).parent / "eb_deployment"
    zip_path = Path(__file__).parent / "codeflowops-backend-eb.zip"
    
    print(f"Creating Elastic Beanstalk deployment package...")
    print(f"Backend source: {backend_dir}")
    print(f"Output: {zip_path}")
    
    # Clean up previous deployment directory
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    
    # Create deployment directory
    deployment_dir.mkdir(exist_ok=True)
    
    # Copy backend source files
    shutil.copytree(backend_dir / "src", deployment_dir, dirs_exist_ok=True)
    
    # Copy requirements.txt
    shutil.copy2(backend_dir / "requirements.txt", deployment_dir / "requirements.txt")
    
    # Create application.py (EB entry point)
    application_py = deployment_dir / "application.py"
    application_py.write_text("""#!/usr/bin/env python3
'''
Elastic Beanstalk entry point for CodeFlowOps Backend
'''
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI app from main.py
try:
    from main import app as application
    print("CodeFlowOps backend loaded successfully")
except ImportError as e:
    print(f"Failed to import application: {e}")
    # Create a minimal fallback app
    from fastapi import FastAPI
    application = FastAPI(title="CodeFlowOps Backend - Fallback")
    
    @application.get("/")
    async def root():
        return {
            "message": "CodeFlowOps Backend - Fallback Mode",
            "status": "error",
            "error": f"Failed to load main application: {e}"
        }
    
    @application.get("/health")
    async def health():
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
""", encoding='utf-8')
    
    # Create .ebextensions directory for EB configuration
    ebextensions_dir = deployment_dir / ".ebextensions"
    ebextensions_dir.mkdir(exist_ok=True)
    
    # Create 01_python.config for EB Python configuration
    python_config = ebextensions_dir / "01_python.config"
    python_config.write_text("""option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
    ENVIRONMENT: "production"
    LOG_LEVEL: "INFO"
  aws:elasticbeanstalk:container:python:
    WSGIPath: "application:application"
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: static
""")
    
    # Create 02_cors.config for CORS configuration
    cors_config = ebextensions_dir / "02_cors.config"
    cors_config.write_text("""option_settings:
  aws:elasticbeanstalk:application:environment:
    ALLOWED_ORIGINS: "https://www.codeflowops.com,https://codeflowops.com"
    CORS_ALLOW_CREDENTIALS: "true"
""")
    
    # Create Procfile for process management
    procfile = deployment_dir / "Procfile"
    procfile.write_text("web: uvicorn application:application --host 0.0.0.0 --port 8000\n")
    
    # Update requirements.txt for production
    requirements_path = deployment_dir / "requirements.txt"
    requirements_content = requirements_path.read_text()
    
    # Add production-specific dependencies
    production_deps = """
# Production dependencies
gunicorn==21.2.0
uvicorn[standard]==0.24.0
"""
    
    if "gunicorn" not in requirements_content:
        requirements_content += production_deps
    
    requirements_path.write_text(requirements_content)
    
    # Create .env file for production
    env_file = deployment_dir / ".env"
    env_file.write_text("""# Production Environment Variables
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://www.codeflowops.com,https://codeflowops.com
CORS_ALLOW_CREDENTIALS=true
AWS_REGION=us-east-1
""")
    
    # Create the zip file
    print(f"Creating zip file: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deployment_dir):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.pyc'):
                    continue
                    
                file_path = Path(root) / file
                arcname = file_path.relative_to(deployment_dir)
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")
    
    # Clean up deployment directory
    shutil.rmtree(deployment_dir)
    
    file_size = zip_path.stat().st_size / 1024 / 1024
    print(f"Deployment package created successfully!")
    print(f"File: {zip_path}")
    print(f"Size: {file_size:.1f} MB")
    print(f"\nReady for Elastic Beanstalk deployment!")
    print(f"   1. Go to AWS Elastic Beanstalk Console")
    print(f"   2. Create new application or update existing")
    print(f"   3. Upload: {zip_path.name}")
    print(f"   4. Configure domain: api.codeflowops.com")
    
    return zip_path

if __name__ == "__main__":
    create_eb_deployment_package()
