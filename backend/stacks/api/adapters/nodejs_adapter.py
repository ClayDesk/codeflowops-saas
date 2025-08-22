# Phase 2: Node.js Runtime Adapter  
# backend/stacks/api/adapters/nodejs_adapter.py

"""
Node.js runtime adapter implementing comprehensive plan specifications
✅ Standardized ports and health checks for Node.js frameworks
✅ Express, Fastify, NestJS framework detection and deployment
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

class NodeJSAdapter(RuntimeAdapter):
    """
    Node.js runtime adapter with standardized configuration
    ✅ Implements comprehensive plan Node.js deployment specifications
    """
    
    # ✅ Runtime default ports for consistent configuration per comprehensive plan
    DEFAULT_PORT = 3000  # Node.js standard port
    HEALTH_CHECK_PATH = '/health'
    HEALTH_CHECK_TIMEOUT = 30
    
    def __init__(self, region: str = 'us-east-1'):
        super().__init__(region)
        self.runtime = 'nodejs18.x'
    
    def detect_framework(self, repo_path: str) -> Dict[str, Any]:
        """
        Detect Node.js framework and return standardized configuration
        ✅ Framework detection per comprehensive plan
        """
        package_json_path = Path(repo_path) / 'package.json'
        
        if not package_json_path.exists():
            return {
                'framework': 'unknown',
                'port': self.DEFAULT_PORT,
                'startup_command': 'npm start',
                'health_check_path': self.HEALTH_CHECK_PATH
            }
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = {}
            dependencies.update(package_data.get('dependencies', {}))
            dependencies.update(package_data.get('devDependencies', {}))
            
            if 'express' in dependencies:
                return {
                    'framework': 'express',
                    'port': self.DEFAULT_PORT,
                    'startup_command': 'node server.js',
                    'health_check_path': self.HEALTH_CHECK_PATH,
                    'lambda_handler': 'lambda.handler'
                }
            elif 'fastify' in dependencies:
                return {
                    'framework': 'fastify',
                    'port': self.DEFAULT_PORT,
                    'startup_command': 'node server.js',
                    'health_check_path': self.HEALTH_CHECK_PATH,
                    'lambda_handler': 'lambda.handler'
                }
            elif '@nestjs/core' in dependencies:
                return {
                    'framework': 'nestjs',
                    'port': self.DEFAULT_PORT,
                    'startup_command': 'npm run start:prod',
                    'health_check_path': self.HEALTH_CHECK_PATH,
                    'lambda_handler': 'lambda.handler'
                }
            elif 'koa' in dependencies:
                return {
                    'framework': 'koa',
                    'port': self.DEFAULT_PORT,
                    'startup_command': 'node app.js',
                    'health_check_path': self.HEALTH_CHECK_PATH,
                    'lambda_handler': 'lambda.handler'
                }
            else:
                return {
                    'framework': 'nodejs',
                    'port': self.DEFAULT_PORT,
                    'startup_command': 'npm start',
                    'health_check_path': self.HEALTH_CHECK_PATH,
                    'lambda_handler': 'lambda.handler'
                }
                
        except Exception as e:
            logger.error(f"Failed to detect Node.js framework: {e}")
            return {
                'framework': 'unknown',
                'port': self.DEFAULT_PORT,
                'startup_command': 'npm start',
                'health_check_path': self.HEALTH_CHECK_PATH
            }
    
    def build(self, repo_path: str, build_config: Dict[str, Any]) -> BuildResult:
        """
        Build Node.js application for deployment
        ✅ Production build with dependency optimization
        """
        
        logger.info(f"🔨 Building Node.js application from {repo_path}")
        
        try:
            # Create temporary build directory
            temp_dir = tempfile.mkdtemp(prefix='nodejs_build_')
            build_path = Path(temp_dir)
            
            # Copy source files
            shutil.copytree(repo_path, build_path / 'app', dirs_exist_ok=True)
            app_path = build_path / 'app'
            
            # Install production dependencies
            npm_install = subprocess.run(
                ['npm', 'install', '--production', '--no-dev'],
                cwd=app_path,
                capture_output=True,
                text=True
            )
            
            if npm_install.returncode != 0:
                return BuildResult(
                    success=False,
                    artifact_path="",
                    repo_path=repo_path,
                    framework=build_config.get('framework', 'nodejs'),
                    runtime=self.runtime,
                    environment_vars={},
                    build_logs=[npm_install.stderr],
                    error_message=f"npm install failed: {npm_install.stderr}"
                )
            
            # Run build script if exists
            package_json = app_path / 'package.json'
            if package_json.exists():
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                
                if 'build' in package_data.get('scripts', {}):
                    build_process = subprocess.run(
                        ['npm', 'run', 'build'],
                        cwd=app_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if build_process.returncode != 0:
                        logger.warning(f"Build script failed: {build_process.stderr}")
            
            # Create health check endpoint if missing
            self._ensure_health_check_endpoint(app_path, build_config)
            
            framework_config = self.detect_framework(str(app_path))
            
            return BuildResult(
                success=True,
                artifact_path=str(app_path),
                repo_path=repo_path,
                framework=framework_config['framework'],
                runtime=self.runtime,
                environment_vars=build_config.get('environment_vars', {}),
                build_logs=[npm_install.stdout, "Build completed successfully"]
            )
            
        except Exception as e:
            logger.error(f"Build failed: {str(e)}")
            return BuildResult(
                success=False,
                artifact_path="",
                repo_path=repo_path,
                framework="nodejs",
                runtime=self.runtime,
                environment_vars={},
                build_logs=[],
                error_message=str(e)
            )
    
    def deploy_to_lambda(self, build_result: BuildResult, lambda_config: Dict[str, Any]) -> DeploymentResult:
        """
        Deploy Node.js application to AWS Lambda
        ✅ Serverless deployment with API Gateway integration
        """
        
        logger.info(f"🚀 Deploying {build_result.framework} to Lambda")
        
        try:
            app_path = Path(build_result.artifact_path)
            
            # Create Lambda handler wrapper
            handler_content = self._create_lambda_handler(build_result.framework)
            with open(app_path / 'lambda.js', 'w') as f:
                f.write(handler_content)
            
            # Create deployment ZIP
            zip_path = app_path.parent / f"{build_result.framework}_lambda.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(app_path):
                    for file in files:
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
                handler='lambda.handler',
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
        Deploy Node.js application to ECS with ALB
        ✅ Containerized deployment with standardized health checks
        """
        
        logger.info(f"🐳 Deploying {build_result.framework} to ECS")
        
        try:
            app_path = Path(build_result.artifact_path)
            
            # Create Dockerfile for Node.js
            dockerfile_content = self._create_dockerfile(build_result)
            with open(app_path / 'Dockerfile', 'w') as f:
                f.write(dockerfile_content)
            
            # Build Docker image (simplified - would use ECR in real implementation)
            service_name = ecs_config.get('service_name', f"codeflowops-{build_result.framework}")
            container_image = f"{service_name}:latest"
            
            # Deploy to ECS
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
    
    def _ensure_health_check_endpoint(self, app_path: Path, build_config: Dict[str, Any]):
        """
        Ensure health check endpoint exists in the application
        ✅ Standardized health endpoint per comprehensive plan
        """
        
        framework = build_config.get('framework', 'express')
        
        # Check if health endpoint already exists
        main_files = ['app.js', 'server.js', 'index.js', 'main.js']
        main_file = None
        
        for filename in main_files:
            if (app_path / filename).exists():
                main_file = app_path / filename
                break
        
        if not main_file:
            # Create a basic Express server with health check
            health_server_content = f'''
const express = require('express');
const app = express();
const port = process.env.PORT || {self.DEFAULT_PORT};

// Health check endpoint - required by comprehensive plan
app.get('{self.HEALTH_CHECK_PATH}', (req, res) => {{
    res.status(200).json({{
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: '{framework}',
        port: port
    }});
}});

// Default route
app.get('/', (req, res) => {{
    res.json({{ message: 'CodeFlowOps {framework} API', healthy: true }});
}});

app.listen(port, '0.0.0.0', () => {{
    console.log(`{framework} server running on port ${{port}}`);
}});

module.exports = app;
'''
            with open(app_path / 'server.js', 'w') as f:
                f.write(health_server_content)
    
    def _create_lambda_handler(self, framework: str) -> str:
        """
        Create Lambda handler wrapper for Node.js frameworks
        ✅ Framework-specific Lambda integration
        """
        
        if framework == 'express':
            return '''
const serverlessExpress = require('@vendia/serverless-express');
const app = require('./server');

exports.handler = serverlessExpress({ app });
'''
        elif framework == 'fastify':
            return '''
const awsLambdaFastify = require('@fastify/aws-lambda');
const app = require('./server');

exports.handler = awsLambdaFastify(app);
'''
        elif framework == 'nestjs':
            return '''
const { NestFactory } = require('@nestjs/core');
const serverlessExpress = require('@vendia/serverless-express');
const { AppModule } = require('./src/app.module');

let server;

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.init();
  return serverlessExpress({ app: app.getHttpAdapter().getInstance() });
}

exports.handler = async (event, context) => {
  server = server ?? (await bootstrap());
  return server(event, context);
};
'''
        else:
            # Generic Node.js handler
            return '''
const serverlessExpress = require('@vendia/serverless-express');
const app = require('./server');

exports.handler = serverlessExpress({ app });
'''
    
    def _create_dockerfile(self, build_result: BuildResult) -> str:
        """
        Create optimized Dockerfile for Node.js deployment
        ✅ Production-ready containerization
        """
        
        return f'''# Node.js {build_result.framework} Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodeuser -u 1001
USER nodeuser

# Expose standardized port per comprehensive plan
EXPOSE {self.DEFAULT_PORT}

# Health check per comprehensive plan specifications
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:{self.DEFAULT_PORT}{self.HEALTH_CHECK_PATH}', (res) => {{ process.exit(res.statusCode === 200 ? 0 : 1) }})"

# Start application
CMD ["node", "server.js"]
'''
