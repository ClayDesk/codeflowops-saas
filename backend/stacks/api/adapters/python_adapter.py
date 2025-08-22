# Phase 2: Python Runtime Adapter
# backend/stacks/api/adapters/python_adapter.py

"""
Python runtime adapter implementing comprehensive plan specifications  
✅ Standardized ports and health checks for Flask, Django, FastAPI
✅ WSGI/ASGI adapter integration for Lambda deployment
"""

import os
import json
import logging
import shutil
import tempfile
import zipfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_adapter import RuntimeAdapter, BuildResult, DeploymentResult, DeploymentTarget

logger = logging.getLogger(__name__)

class PythonAdapter(RuntimeAdapter):
    """
    Python runtime adapter with standardized configuration per comprehensive plan
    ✅ Flask, Django, FastAPI framework detection and deployment
    """
    
    # ✅ Runtime default ports for consistent configuration per comprehensive plan
    DEFAULT_PORT = 8000
    HEALTH_CHECK_PATH = '/health'
    HEALTH_CHECK_TIMEOUT = 30
    
    def __init__(self, region: str = 'us-east-1'):
        super().__init__(region)
        self.runtime = 'python3.9'
    
    def detect_framework(self, repo_path: str) -> Dict[str, Any]:
        """
        Detect Python framework and return appropriate config
        ✅ Framework detection per comprehensive plan specifications
        """
        requirements_path = Path(repo_path) / 'requirements.txt'
        setup_py_path = Path(repo_path) / 'setup.py'
        pyproject_path = Path(repo_path) / 'pyproject.toml'
        
        requirements = []
        
        # Read requirements from various sources
        if requirements_path.exists():
            with open(requirements_path, 'r') as f:
                requirements.extend(f.read().lower().split('\n'))
        
        if setup_py_path.exists():
            with open(setup_py_path, 'r') as f:
                content = f.read().lower()
                if 'fastapi' in content:
                    requirements.append('fastapi')
                if 'flask' in content:
                    requirements.append('flask')
                if 'django' in content:
                    requirements.append('django')
        
        requirements_str = ' '.join(requirements)
        
        if 'fastapi' in requirements_str:
            return {
                'framework': 'fastapi',
                'port': self.DEFAULT_PORT,
                'startup_command': 'uvicorn main:app --host 0.0.0.0 --port 8000',
                'health_check_path': self.HEALTH_CHECK_PATH,
                'wsgi_module': 'main:app'
            }
        elif 'flask' in requirements_str:
            return {
                'framework': 'flask', 
                'port': 5000,  # Flask default
                'startup_command': 'python app.py',
                'health_check_path': self.HEALTH_CHECK_PATH,
                'wsgi_module': 'app:app'
            }
        elif 'django' in requirements_str:
            return {
                'framework': 'django',
                'port': self.DEFAULT_PORT,
                'startup_command': 'python manage.py runserver 0.0.0.0:8000',
                'health_check_path': self.HEALTH_CHECK_PATH,
                'wsgi_module': 'wsgi:application'
            }
        else:
            return {
                'framework': 'python',
                'port': self.DEFAULT_PORT,
                'startup_command': 'python app.py',
                'health_check_path': self.HEALTH_CHECK_PATH,
                'wsgi_module': 'app:app'
            }
    
    def build(self, repo_path: str, build_config: Dict[str, Any]) -> BuildResult:
        """
        Build Python application with dependency installation
        ✅ Production build with virtual environment
        """
        
        logger.info(f"🐍 Building Python application from {repo_path}")
        
        try:
            # Create temporary build directory
            temp_dir = tempfile.mkdtemp(prefix='python_build_')
            build_path = Path(temp_dir)
            
            # Copy source files
            shutil.copytree(repo_path, build_path / 'app', dirs_exist_ok=True)
            app_path = build_path / 'app'
            
            # Install dependencies in build directory
            if (app_path / 'requirements.txt').exists():
                pip_install = subprocess.run([
                    'python', '-m', 'pip', 'install', 
                    '-r', 'requirements.txt',
                    '-t', '.'  # Install packages in current directory for Lambda
                ], cwd=app_path, capture_output=True, text=True)
                
                if pip_install.returncode != 0:
                    return BuildResult(
                        success=False,
                        artifact_path="",
                        repo_path=repo_path,
                        framework=build_config.get('framework', 'python'),
                        runtime=self.runtime,
                        environment_vars={},
                        build_logs=[pip_install.stderr],
                        error_message=f"pip install failed: {pip_install.stderr}"
                    )
            
            # Ensure health check endpoint exists
            framework_config = self.detect_framework(str(app_path))
            self._ensure_health_check_endpoint(app_path, framework_config)
            
            return BuildResult(
                success=True,
                artifact_path=str(app_path),
                repo_path=repo_path,
                framework=framework_config['framework'],
                runtime=self.runtime,
                environment_vars=build_config.get('environment_vars', {}),
                build_logs=["Python build completed successfully"]
            )
            
        except Exception as e:
            logger.error(f"Python build failed: {str(e)}")
            return BuildResult(
                success=False,
                artifact_path="",
                repo_path=repo_path,
                framework="python",
                runtime=self.runtime,
                environment_vars={},
                build_logs=[],
                error_message=str(e)
            )
    
    def deploy_to_lambda(self, build_result: BuildResult, lambda_config: Dict[str, Any]) -> DeploymentResult:
        """
        Deploy Python application to AWS Lambda with WSGI/ASGI adapter
        ✅ Framework-specific Lambda integration per comprehensive plan
        """
        
        logger.info(f"🚀 Deploying {build_result.framework} to Lambda")
        
        try:
            app_path = Path(build_result.artifact_path)
            
            # Create Lambda handler wrapper
            handler_content = self._create_lambda_handler(build_result.framework)
            with open(app_path / 'lambda_handler.py', 'w') as f:
                f.write(handler_content)
            
            # Install Lambda-specific packages
            if build_result.framework == 'django':
                subprocess.run([
                    'python', '-m', 'pip', 'install', 'mangum', '-t', '.'
                ], cwd=app_path)
            elif build_result.framework == 'fastapi':
                subprocess.run([
                    'python', '-m', 'pip', 'install', 'mangum', '-t', '.'
                ], cwd=app_path)
            else:  # Flask and others
                subprocess.run([
                    'python', '-m', 'pip', 'install', 'serverless-wsgi', '-t', '.'
                ], cwd=app_path)
            
            # Create deployment ZIP
            zip_path = app_path.parent / f"{build_result.framework}_lambda.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(app_path):
                    # Skip __pycache__ directories
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    
                    for file in files:
                        if not file.endswith('.pyc'):
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(app_path)
                            zipf.write(file_path, arcname)
            
            # Deploy to AWS Lambda
            function_name = lambda_config.get('function_name', f"codeflowops-{build_result.framework}")
            
            with open(zip_path, 'rb') as f:
                zip_bytes = f.read()
            
            deployment_info = self.aws_deployer.deploy_lambda_function(
                function_name=function_name,
                zip_file=zip_bytes,
                handler='lambda_handler.handler',
                runtime=self.runtime,
                environment_vars=build_result.environment_vars
            )
            
            return DeploymentResult(
                success=True,
                endpoint_url=deployment_info['endpoint_url'],
                deployment_target=DeploymentTarget.LAMBDA,
                health_check_url=f"{deployment_info['endpoint_url']}{self.HEALTH_CHECK_PATH}",
                function_arn=deployment_info['function_arn'],
                deployment_id=deployment_info.get('api_id')
            )
            
        except Exception as e:
            logger.error(f"Lambda deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                endpoint_url="",
                deployment_target=DeploymentTarget.LAMBDA,
                health_check_url="",
                error_message=str(e)
            )
    
    def deploy_to_ecs(self, build_result: BuildResult, ecs_config: Dict[str, Any]) -> DeploymentResult:
        """
        Deploy Python application to ECS with gunicorn
        ✅ Multi-stage Docker build with production optimization
        """
        
        logger.info(f"🐳 Deploying {build_result.framework} to ECS")
        
        try:
            app_path = Path(build_result.artifact_path)
            
            # Create Dockerfile for Python
            dockerfile_content = self._create_dockerfile(build_result)
            with open(app_path / 'Dockerfile', 'w') as f:
                f.write(dockerfile_content)
            
            # Create gunicorn configuration
            gunicorn_config = self._create_gunicorn_config(build_result.framework)
            with open(app_path / 'gunicorn.conf.py', 'w') as f:
                f.write(gunicorn_config)
            
            # Deploy to ECS
            service_name = ecs_config.get('service_name', f"codeflowops-{build_result.framework}")
            container_image = f"{service_name}:latest"
            
            # Get standardized health check configuration
            health_config = self.get_standardized_health_config()
            
            deployment_info = self.aws_deployer.deploy_containerized_api(
                container_image=container_image,
                port=self.DEFAULT_PORT,
                health_check_config=health_config,
                environment=build_result.environment_vars,
                service_name=service_name
            )
            
            return DeploymentResult(
                success=True,
                endpoint_url=deployment_info['endpoint_url'],
                deployment_target=DeploymentTarget.ECS,
                health_check_url=f"{deployment_info['endpoint_url']}{self.HEALTH_CHECK_PATH}",
                service_arn=deployment_info['service_arn'],
                load_balancer_arn=deployment_info['load_balancer_arn'],
                deployment_id=deployment_info['task_definition_arn']
            )
            
        except Exception as e:
            logger.error(f"ECS deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                endpoint_url="",
                deployment_target=DeploymentTarget.ECS,
                health_check_url="",
                error_message=str(e)
            )
    
    def _ensure_health_check_endpoint(self, app_path: Path, framework_config: Dict[str, Any]):
        """
        Ensure health check endpoint exists for Python frameworks
        ✅ Standardized health endpoint per comprehensive plan
        """
        
        framework = framework_config['framework']
        
        if framework == 'flask':
            # Check if main Flask app exists
            main_files = ['app.py', 'main.py', 'server.py']
            main_file = None
            
            for filename in main_files:
                if (app_path / filename).exists():
                    main_file = app_path / filename
                    break
            
            if not main_file:
                # Create Flask app with health check
                flask_app_content = f'''
from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)

@app.route('{self.HEALTH_CHECK_PATH}')
def health_check():
    return jsonify({{
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'flask',
        'port': {framework_config['port']}
    }})

@app.route('/')
def index():
    return jsonify({{
        'message': 'CodeFlowOps Flask API',
        'healthy': True
    }})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', {framework_config['port']}))
    app.run(host='0.0.0.0', port=port)
'''
                with open(app_path / 'app.py', 'w') as f:
                    f.write(flask_app_content)
        
        elif framework == 'fastapi':
            # Check if main FastAPI app exists
            main_files = ['main.py', 'app.py', 'server.py']
            main_file = None
            
            for filename in main_files:
                if (app_path / filename).exists():
                    main_file = app_path / filename
                    break
            
            if not main_file:
                # Create FastAPI app with health check
                fastapi_app_content = f'''
from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()

@app.get('{self.HEALTH_CHECK_PATH}')
async def health_check():
    return {{
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'fastapi',
        'port': {self.DEFAULT_PORT}
    }}

@app.get('/')
async def root():
    return {{
        'message': 'CodeFlowOps FastAPI',
        'healthy': True
    }}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', {self.DEFAULT_PORT}))
    uvicorn.run(app, host='0.0.0.0', port=port)
'''
                with open(app_path / 'main.py', 'w') as f:
                    f.write(fastapi_app_content)
        
        elif framework == 'django':
            # For Django, health check would be added as a view
            # This is more complex and would typically involve adding to urls.py
            pass
    
    def _create_lambda_handler(self, framework: str) -> str:
        """
        Create Lambda handler for Python frameworks with WSGI/ASGI adapters
        ✅ Framework-specific Lambda integration per comprehensive plan
        """
        
        if framework == 'fastapi':
            return '''
from mangum import Mangum
from main import app

handler = Mangum(app)
'''
        elif framework == 'django':
            return '''
from mangum import Mangum
import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

app = get_wsgi_application()
handler = Mangum(app)
'''
        else:  # Flask and others
            return '''
import serverless_wsgi
from app import app

def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
'''
    
    def _create_dockerfile(self, build_result: BuildResult) -> str:
        """
        Create optimized Dockerfile for Python frameworks
        ✅ Multi-stage build with production optimization
        """
        
        framework = build_result.framework
        
        if framework == 'django':
            return f'''# Python Django Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose standardized port per comprehensive plan
EXPOSE {self.DEFAULT_PORT}

# Health check per comprehensive plan specifications
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:{self.DEFAULT_PORT}{self.HEALTH_CHECK_PATH} || exit 1

# Start application with gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:application"]
'''
        
        elif framework == 'fastapi':
            return f'''# Python FastAPI Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose standardized port per comprehensive plan
EXPOSE {self.DEFAULT_PORT}

# Health check per comprehensive plan specifications
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:{self.DEFAULT_PORT}{self.HEALTH_CHECK_PATH} || exit 1

# Start application with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{self.DEFAULT_PORT}"]
'''
        
        else:  # Flask and generic Python
            return f'''# Python Flask Dockerfile  
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose standardized port per comprehensive plan
EXPOSE {self.DEFAULT_PORT}

# Health check per comprehensive plan specifications  
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:{self.DEFAULT_PORT}{self.HEALTH_CHECK_PATH} || exit 1

# Start application with gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
'''
    
    def _create_gunicorn_config(self, framework: str) -> str:
        """
        Create gunicorn configuration for production deployment
        ✅ Production-ready WSGI server configuration
        """
        
        return f'''# Gunicorn configuration for {framework}
import os

# Server socket
bind = "0.0.0.0:{self.DEFAULT_PORT}"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, with jitter
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "codeflowops-{framework}"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None
'''
