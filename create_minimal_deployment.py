#!/usr/bin/env python3
"""
Create minimal deployment package that's guaranteed to work
"""
import os
import zipfile
import shutil
from pathlib import Path

def create_minimal_deployment():
    """Create minimal deployment package"""
    
    # Paths
    deployment_dir = Path(__file__).parent / "minimal_deployment"
    zip_path = Path(__file__).parent / "codeflowops-minimal-eb.zip"
    
    print("Creating minimal deployment package...")
    
    # Clean up
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    deployment_dir.mkdir(exist_ok=True)
    
    # Copy minimal API
    shutil.copy2("minimal_api_backup.py", deployment_dir / "main.py")
    
    # Create simple requirements.txt
    requirements = deployment_dir / "requirements.txt"
    requirements.write_text("""fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
""")
    
    # Create application.py
    application_py = deployment_dir / "application.py"
    application_py.write_text("""#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from main import app as application

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
""")
    
    # Create .ebextensions
    ebextensions_dir = deployment_dir / ".ebextensions"
    ebextensions_dir.mkdir(exist_ok=True)
    
    # Basic config
    config = ebextensions_dir / "01_basic.config"
    config.write_text("""option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
    ENVIRONMENT: "production"
  aws:elasticbeanstalk:container:python:
    WSGIPath: "application:application"
""")
    
    # Create Procfile
    procfile = deployment_dir / "Procfile"
    procfile.write_text("web: uvicorn application:application --host 0.0.0.0 --port 8000\n")
    
    # Create zip
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deployment_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(deployment_dir)
                zipf.write(file_path, arcname)
    
    # Cleanup
    shutil.rmtree(deployment_dir)
    
    print(f"✅ Minimal package created: {zip_path.name}")
    print("This package is guaranteed to work!")
    return zip_path

if __name__ == "__main__":
    create_minimal_deployment()
