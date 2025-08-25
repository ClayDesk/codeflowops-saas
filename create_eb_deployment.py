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
    
    # Copy the working simple_api.py as main.py
    shutil.copy2(backend_dir / "simple_api.py", deployment_dir / "main.py")
    
    # Copy all support files from backend directory
    support_files = [
        "repository_enhancer.py",
        "cleanup_service.py", 
        "enhanced_repository_analyzer.py",
        "react_deployer.py",           # Updated React deployer with CodeBuild
        "aws_codebuild_manager.py"     # New AWS CodeBuild manager
    ]
    
    for file in support_files:
        src_file = backend_dir / file
        if src_file.exists():
            shutil.copy2(src_file, deployment_dir / file)
            print(f"  Copied: {file}")
    
    # Copy requirements.txt
    shutil.copy2(backend_dir / "requirements.txt", deployment_dir / "requirements.txt")
    
    # Copy core utilities if they exist
    core_dir = backend_dir / "core"
    if core_dir.exists():
        shutil.copytree(core_dir, deployment_dir / "core", dirs_exist_ok=True)
        print("  Copied: core/ directory")
    
    # Copy detectors if they exist
    detectors_dir = backend_dir / "detectors"
    if detectors_dir.exists():
        shutil.copytree(detectors_dir, deployment_dir / "detectors", dirs_exist_ok=True)
        print("  Copied: detectors/ directory")
    
    # Copy routers if they exist
    routers_dir = backend_dir / "routers"
    if routers_dir.exists():
        shutil.copytree(routers_dir, deployment_dir / "routers", dirs_exist_ok=True)
        print("  Copied: routers/ directory")
    
    # Copy src directory if it exists
    src_dir = backend_dir / "src"
    if src_dir.exists():
        shutil.copytree(src_dir, deployment_dir / "src", dirs_exist_ok=True)
        print("  Copied: src/ directory")
    
    # Copy analyzer directory if it exists
    analyzer_dir = backend_dir / "analyzer"
    if analyzer_dir.exists():
        shutil.copytree(analyzer_dir, deployment_dir / "analyzer", dirs_exist_ok=True)
        print("  Copied: analyzer/ directory")
    
    # Copy utils directory if it exists
    utils_dir = backend_dir / "utils"
    if utils_dir.exists():
        shutil.copytree(utils_dir, deployment_dir / "utils", dirs_exist_ok=True)
        print("  Copied: utils/ directory")
    
    # Create application.py (EB entry point) - FINAL BULLETPROOF VERSION
    application_py = deployment_dir / "application.py"
    application_py.write_text("""#!/usr/bin/env python3
'''
BULLETPROOF Elastic Beanstalk entry point - NO MORE VARIABLE SCOPE ERRORS
'''
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print("Starting CodeFlowOps Backend - BULLETPROOF VERSION")

# Initialize variables at module level to prevent scope errors
application = None
import_error_msg = None

try:
    from main import app as main_app
    application = main_app
    print("SUCCESS: CodeFlowOps Enhanced API loaded")
    print("Enhanced Repository Analyzer: ACTIVE")
    print("Static Site Detection: ENABLED")
    print("Available endpoints:")
    print("  POST /api/analyze-repo - Repository analysis")
    print("  GET /health - Health check")
    
except Exception as import_error:
    import_error_msg = str(import_error)
    print(f"Main import failed: {import_error_msg}")
    
    # Create fallback app with NO scope issues
    from fastapi import FastAPI
    
    fallback_app = FastAPI(title="CodeFlowOps Backend - Fallback")
    
    @fallback_app.get("/")
    async def fallback_root():
        return {
            "message": "CodeFlowOps Backend - Fallback Mode",
            "status": "degraded", 
            "error": import_error_msg,
            "version": "enhanced-analyzer-fallback"
        }
    
    @fallback_app.get("/health")
    async def fallback_health():
        return {
            "status": "degraded", 
            "error": import_error_msg,
            "message": "Running in fallback mode"
        }
    
    application = fallback_app
    print("Fallback mode activated")

# Final safety check
if application is None:
    from fastapi import FastAPI
    application = FastAPI()
    
    @application.get("/")
    async def emergency():
        return {"message": "Emergency mode - application was None"}

print(f"Application ready: {type(application).__name__}")

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
    GIT_PYTHON_REFRESH: "quiet"
    PATH: "/usr/bin:/bin:/usr/local/bin:$PATH"
    # AWS and Cognito Configuration
    AWS_REGION: "us-east-1"
    COGNITO_USER_POOL_ID: "us-east-1_lWcaQdyeZ"
    COGNITO_CLIENT_ID: "3d0gm6gtv4ia8vonloc38q8nkt"
    # CORS Configuration
    ALLOWED_ORIGINS: "https://www.codeflowops.com,https://codeflowops.com"
    CORS_ALLOW_CREDENTIALS: "true"
  aws:elasticbeanstalk:container:python:
    WSGIPath: "application:application"
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: static

packages:
  yum:
    git: []
    git-all: []

commands:
  01_install_git:
    command: |
      which git || yum install -y git
      git --version
    ignoreErrors: false
  02_configure_git:
    command: |
      git config --global user.email "deploy@codeflowops.com"
      git config --global user.name "CodeFlowOps Deploy" 
      git config --global init.defaultBranch main
      git config --global safe.directory '*'
      git config --global http.sslVerify true
    ignoreErrors: true
  03_verify_git:
    command: |
      echo "Git location: $(which git)"
      echo "Git version: $(git --version)"
      echo "PATH: $PATH"
    ignoreErrors: true
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
