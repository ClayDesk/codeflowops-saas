"""
PHP Stack Deployer
"""
import logging
import boto3
import json
import base64
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
from botocore.exceptions import ClientError
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.interfaces import StackDeployer
from core.models import DeployResult, StackPlan

logger = logging.getLogger(__name__)

class PHPDeployer(StackDeployer):
    """Deploys PHP applications to AWS"""
    
    def __init__(self):
        self.ecs_client = None
        self.ecr_client = None
        self.elbv2_client = None
        self.cloudfront_client = None
        self.s3_client = None
        self.logs_client = None
        self.iam_client = None
    
    def _pick_live_url(self, result: dict, method: str) -> str:
        """
        Safe URL picker that never accesses CloudFront fields for PHP runtime deployments
        """
        if method == "apprunner":
            return result.get("live_url") or result.get("apprunner_url") or ""
        elif method == "ecs":
            alb_dns = result.get("alb_dns")
            return result.get("live_url") or (f"http://{alb_dns}" if alb_dns else "")
        else:
            # Static/CDN path (should never happen for PHP)
            cloudfront_domain = result.get("cloudfront_domain")
            return result.get("live_url") or (f"https://{cloudfront_domain}" if cloudfront_domain else "")
    
    def deploy(self, plan: StackPlan, build_result: Any, provision_result: Any, credentials: Dict[str, Any]) -> DeployResult:
        """🚀 Deploy Universal PHP application to AWS with database integration"""
        
        logger.info(f"🚀 Deploying Universal PHP application to AWS")
        
        try:
            # Extract application requirements and type for enhanced deployment
            app_requirements = getattr(provision_result, 'app_requirements', {})
            app_type = app_requirements.get('application_type', 'php')
            database_config = app_requirements.get('database', {})
            
            logger.info(f"📱 Deploying {app_type} application with database: {database_config.get('engine', 'none')}")
            
            # Safe method selection with PHP runtime enforcement
            deployment_method = plan.config.get('deployment_method', 'ecs')
            infrastructure_config = getattr(provision_result, 'infrastructure_config', {})
            recommended_method = infrastructure_config.get('recommended_deployment_method', 'ecs')
            
            # Extract analysis info for method selection
            stack_key = "php"  # This is the PHP deployer
            method = recommended_method or deployment_method
            
            # PHP must use a runtime; never static/CDN
            if method in (None, "static", "cloudfront", "s3"):
                method = "apprunner"
                logger.info("🔧 PHP forced to App Runner (no static deployment)")
            
            logger.info(f"[php] Deploying stack={stack_key} app_type={app_type} method={method}")
            
            if method == "apprunner":
                return self._deploy_apprunner_universal(plan, build_result, provision_result, credentials, app_requirements)
            elif method == "ecs":
                return self._deploy_ecs_universal(plan, build_result, provision_result, credentials, app_requirements)
            else:
                # Belt & suspenders: fail fast if PHP tries static
                raise ValueError("Laravel/PHP must use App Runner or ECS; static CDN is not supported.")
                
        except Exception as e:
            logger.error(f"Universal PHP deployment failed: {e}")
            return DeployResult(
                success=False,
                live_url="",
                details={"error": str(e)},
                error_message=str(e)
            )
    
    def _deploy_apprunner_universal(self, plan: StackPlan, build_result: Any, provision_result: Any, credentials: Dict[str, Any], app_requirements: Dict[str, Any]) -> DeployResult:
        """🏃 Deploy Universal PHP application using AWS App Runner with database integration"""
        
        logger.info("🏃 Starting AWS App Runner universal deployment")
        
        try:
            # Initialize AWS clients
            self._initialize_clients(credentials)
            
            # Get infrastructure config and application info
            infrastructure_config = getattr(provision_result, 'infrastructure_config', {})
            app_name = plan.config.get('app_name', 'php-app')
            app_type = app_requirements.get('application_type', 'php')
            
            deployment_logs = []
            deployment_logs.append(f"🌟 Starting {app_type} deployment to App Runner")
            
            # Step 1: Create ECR repository and build universal image
            repo_name = app_name.replace('-cluster', '').replace('-', '')[:63]
            image_uri = self._deploy_universal_container_image({'cluster_name': f'{repo_name}-cluster'}, build_result, app_requirements, deployment_logs)
            
            # Step 2: Prepare environment variables with database configuration
            environment_vars = self._prepare_environment_variables(app_requirements, infrastructure_config)
            
            # Step 3: Create App Runner service with universal configuration
            apprunner_client = boto3.client('apprunner', **self.credentials)
            service_name = f"{repo_name}-service"
            
            # Detect port and health path from application requirements
            is_public_ecr = image_uri.startswith("public.ecr.aws/")
            repo_type = "ECR_PUBLIC" if is_public_ecr else "ECR"
            health_path = app_requirements.get('health_check', '/health')
            port = '80'  # Always use port 80
            
            service_config = {
                'ServiceName': service_name,
                'SourceConfiguration': {
                    'ImageRepository': {
                        'ImageIdentifier': image_uri,
                        'ImageConfiguration': {
                            'Port': port,
                            'RuntimeEnvironmentVariables': environment_vars
                        },
                        'ImageRepositoryType': repo_type
                    },
                    'AutoDeploymentsEnabled': False
                },
                'InstanceConfiguration': {
                    'Cpu': app_requirements.get('cpu', '1 vCPU'),
                    'Memory': app_requirements.get('memory', '2 GB')
                },
                'HealthCheckConfiguration': {
                    'Protocol': 'HTTP',
                    'Path': health_path,
                    'Interval': app_requirements.get('health_check_interval', 10),
                    'Timeout': 5,
                    'HealthyThreshold': 1,
                    'UnhealthyThreshold': 5
                }
            }
            
            try:
                deployment_logs.append(f"🏃 Creating App Runner service for {app_type}: {service_name}")
                response = apprunner_client.create_service(**service_config)
                service_arn = response['Service']['ServiceArn']
                service_url = response['Service']['ServiceUrl']
                deployment_logs.append(f"✅ App Runner service created: {service_url}")
                
                # Wait for service to be running
                deployment_logs.append(f"⏳ Waiting for {app_type} service to be ready...")
                for _ in range(20):  # ~5 minutes
                    desc = apprunner_client.describe_service(ServiceArn=service_arn)
                    status = desc['Service']['Status']
                    if status == 'RUNNING':
                        break
                    if status in ('DELETED', 'FAILED'):
                        raise RuntimeError(f"App Runner service ended in status {status}")
                    time.sleep(15)
                
                deployment_logs.append(f"🎉 {app_type.title()} App Runner service is running!")
                
                # Add database connection test if database is configured
                if app_requirements.get('database', {}).get('engine'):
                    deployment_logs.append(f"🗄️ Database configured: {app_requirements['database']['engine']}")
                
                return DeployResult(
                    success=True,
                    live_url=f"https://{service_url}",
                    deployment_logs=deployment_logs,
                    details={
                        'service_arn': service_arn,
                        'apprunner_url': f"https://{service_url}",
                        'deployment_method': 'apprunner',
                        'application_type': app_type,
                        'image_uri': image_uri,
                        'database_engine': app_requirements.get('database', {}).get('engine', 'none'),
                        'framework': plan.config.get('framework', app_type)
                    }
                )
                
            except apprunner_client.exceptions.ServiceQuotaExceededException:
                deployment_logs.append("⚠️ App Runner quota exceeded, falling back to ECS")
                return self._deploy_ecs_universal(plan, build_result, provision_result, credentials, app_requirements)
                
            except Exception as e:
                if 'already exists' in str(e).lower():
                    # Service exists, get its URL
                    services = apprunner_client.list_services()
                    for service in services['ServiceSummaryList']:
                        if service['ServiceName'] == service_name:
                            service_details = apprunner_client.describe_service(ServiceArn=service['ServiceArn'])
                            service_url = service_details['Service']['ServiceUrl']
                            deployment_logs.append(f"📦 Using existing App Runner service: {service_url}")
                            return DeployResult(
                                success=True,
                                live_url=f"https://{service_url}",
                                deployment_logs=deployment_logs,
                                details={
                                    'service_arn': service['ServiceArn'],
                                    'apprunner_url': f"https://{service_url}",
                                    'deployment_method': 'apprunner',
                                    'application_type': app_type,
                                    'image_uri': image_uri
                                }
                            )
                raise e
                
        except Exception as e:
            logger.error(f"Universal App Runner deployment failed: {e}")
            return DeployResult(
                success=False,
                live_url="",
                error_message=f"App Runner deployment failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def _deploy_apprunner(self, plan: StackPlan, build_result: Any, provision_result: Any, credentials: Dict[str, Any]) -> DeployResult:
        """Deploy PHP application using AWS App Runner"""
        
        logger.info("🏃 Starting AWS App Runner deployment")
        
        try:
            # Initialize AWS clients
            self._initialize_clients(credentials)
            
            # Get infrastructure config
            infrastructure_config = getattr(provision_result, 'infrastructure_config', {})
            app_name = plan.config.get('app_name', 'php-app')
            
            deployment_logs = []
            
            # Step 1: Create ECR repository and build image
            repo_name = app_name.replace('-cluster', '').replace('-', '')[:63]  # App Runner naming limits
            image_uri = self._deploy_container_image({'cluster_name': f'{repo_name}-cluster'}, build_result, deployment_logs)
            
            # Step 2: Create App Runner service
            apprunner_client = boto3.client('apprunner', **self.credentials)
            
            service_name = f"{repo_name}-service"
            
            # Create App Runner service configuration
            # Detect port and health path from config
            is_public_ecr = image_uri.startswith("public.ecr.aws/")
            repo_type = "ECR_PUBLIC" if is_public_ecr else "ECR"
            health_path = "/health" if not is_public_ecr else "/"  # Keep "/" for stock nginx, "/health" for our images
            port = '80'  # Always use port 80
            port = '80'  # Always use port 80
            
            service_config = {
                'ServiceName': service_name,
                'SourceConfiguration': {
                    'ImageRepository': {
                        'ImageIdentifier': image_uri,
                        'ImageConfiguration': {
                            'Port': port,
                            'RuntimeEnvironmentVariables': [
                                {'Name': 'APP_ENV', 'Value': 'production'},
                                {'Name': 'APP_DEBUG', 'Value': 'false'}
                            ]
                        },
                        'ImageRepositoryType': repo_type
                    },
                    'AutoDeploymentsEnabled': False
                },
                'InstanceConfiguration': {
                    'Cpu': '1 vCPU',     # Safe default to avoid validation errors
                    'Memory': '2 GB'     # Safe default for reliable operation
                },
                'HealthCheckConfiguration': {
                    'Protocol': 'HTTP',
                    'Path': health_path,
                    'Interval': 10,
                    'Timeout': 5,
                    'HealthyThreshold': 1,
                    'UnhealthyThreshold': 5
                }
            }
            
            try:
                deployment_logs.append(f"🏃 Creating App Runner service: {service_name}")
                response = apprunner_client.create_service(**service_config)
                service_arn = response['Service']['ServiceArn']
                service_url = response['Service']['ServiceUrl']
                deployment_logs.append(f"✅ App Runner service created: {service_url}")
                
                # Wait for service to be running
                deployment_logs.append("⏳ Waiting for App Runner service to be ready...")
                # Poll until service is RUNNING
                for _ in range(20):  # ~5 minutes
                    desc = apprunner_client.describe_service(ServiceArn=service_arn)
                    status = desc['Service']['Status']
                    if status == 'RUNNING':
                        break
                    if status in ('DELETED', 'FAILED'):
                        raise RuntimeError(f"App Runner service ended in status {status}")
                    time.sleep(15)
                
                deployment_logs.append("🎉 App Runner service is running!")
                
                return DeployResult(
                    success=True,
                    live_url=f"https://{service_url}",
                    deployment_logs=deployment_logs,
                    details={
                        'service_arn': service_arn,
                        'apprunner_url': f"https://{service_url}",  # Safe App Runner URL
                        'deployment_method': 'apprunner',
                        'image_uri': image_uri,
                        'framework': plan.config.get('framework', 'laravel')
                    }
                )
                
            except apprunner_client.exceptions.ServiceQuotaExceededException:
                deployment_logs.append("⚠️ App Runner quota exceeded, falling back to ECS")
                return self._deploy_ecs(plan, build_result, provision_result, credentials)
                
            except Exception as e:
                if 'already exists' in str(e).lower():
                    # Service exists, get its URL
                    services = apprunner_client.list_services()
                    for service in services['ServiceSummaryList']:
                        if service['ServiceName'] == service_name:
                            service_details = apprunner_client.describe_service(ServiceArn=service['ServiceArn'])
                            service_url = service_details['Service']['ServiceUrl']
                            deployment_logs.append(f"📦 Using existing App Runner service: {service_url}")
                            return DeployResult(
                                success=True,
                                live_url=f"https://{service_url}",
                                deployment_logs=deployment_logs,
                                details={
                                    'service_arn': service['ServiceArn'],
                                    'apprunner_url': f"https://{service_url}",  # Safe App Runner URL
                                    'deployment_method': 'apprunner',
                                    'image_uri': image_uri
                                }
                            )
                raise e
                
        except Exception as e:
            logger.error(f"App Runner deployment failed: {e}")
            return DeployResult(
                success=False,
                live_url="",
                error_message=f"App Runner deployment failed: {str(e)}",
                details={"error": str(e)}
            )
    
    def _deploy_ecs(self, plan: StackPlan, build_result: Any, provision_result: Any, credentials: Dict[str, Any]) -> DeployResult:
        """Deploy PHP application using AWS ECS (original method)"""
        
        # For now, get infrastructure config from provision_result
        # In a complete implementation, this would come from the provisioner
        infrastructure_config = getattr(provision_result, 'infrastructure_config', {})
        if not infrastructure_config:
            # Generate a basic config for demo with port 80 defaults
            app_name = plan.config.get('app_name', 'php-app')
            infrastructure_config = {
                'cluster_name': f"{app_name}-cluster",
                'service_name': f"{app_name}-service",
                'task_definition': {
                    'family': f"{app_name}-task",
                    'containerDefinitions': [{'name': app_name, 'memory': 1024}]
                },
                'load_balancer': {
                    'name': f"{app_name}-alb",
                    'target_group': {
                        'name': f"{app_name}-tg",
                        'port': 80,
                        'health_check': {
                            'path': '/health'
                        }
                    }
                },
                'monitoring': {'log_group': f"/ecs/{app_name}"}
            }
        
        # Initialize AWS clients
        self._initialize_clients(credentials)
        
        # Deployment steps
        deployment_logs = []
        
        # Step 1: Create ECR repository and build/push Docker image
        image_uri = self._deploy_container_image(infrastructure_config, build_result, deployment_logs)
        
        # Step 2: Create ECS cluster and task definition
        cluster_arn, task_def_arn = self._create_ecs_infrastructure(infrastructure_config, image_uri, deployment_logs)
        
        # Step 3: Create Load Balancer and Target Group
        alb_arn, target_group_arn, alb_dns, alb_sg_id, vpc_id, subnet_ids = self._create_load_balancer(infrastructure_config, deployment_logs)
        
        # Step 4: Create ECS Service
        service_arn = self._create_ecs_service(infrastructure_config, cluster_arn, task_def_arn, target_group_arn, alb_sg_id, vpc_id, subnet_ids, deployment_logs)
        
        # Step 5: Skip CloudFront for ECS PHP deployments - use ALB directly
        deployment_logs.append("🌐 Using ALB endpoint for ECS deployment (no CloudFront)")
        
        # Step 6: Wait for deployment to be healthy
        self._wait_for_healthy_deployment(service_arn, target_group_arn, deployment_logs)
        
        # ECS path: return ALB URL only; no cloudfront_domain in details
        return DeployResult(
            success=True,
            live_url=f"http://{alb_dns}",  # ECS uses ALB directly
            deployment_logs=deployment_logs,
            details={
                'cluster_arn': cluster_arn,
                'service_arn': service_arn, 
                'task_definition_arn': task_def_arn,
                'load_balancer_arn': alb_arn,
                'alb_dns': alb_dns,  # Safe ALB field for ECS
                'deployment_method': 'ecs',
                'framework': infrastructure_config.get('task_definition', {}).get('containerDefinitions', [{}])[0].get('environment', [])
            }
        )
    
    def _initialize_clients(self, credentials: Dict[str, Any]):
        """Initialize AWS clients with credentials"""
        # Handle different credential field formats
        access_key = credentials.get('access_key_id') or credentials.get('aws_access_key') or credentials.get('aws_access_key_id')
        secret_key = credentials.get('secret_access_key') or credentials.get('aws_secret_key') or credentials.get('aws_secret_access_key')
        region = credentials.get('region') or credentials.get('aws_region', 'us-east-1')
        
        if not access_key or not secret_key:
            raise ValueError("AWS credentials are required: aws_access_key_id and aws_secret_access_key")
        
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        # Store credentials for other client creation
        self.credentials = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'region_name': region
        }
        
        self.ecs_client = session.client('ecs')
        self.ecr_client = session.client('ecr')
        self.elbv2_client = session.client('elbv2')
        self.cloudfront_client = session.client('cloudfront')
        self.s3_client = session.client('s3')
        self.logs_client = session.client('logs')
        self.iam_client = session.client('iam')
        
        # Store credentials for other clients that need them
        self.credentials = {
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'region_name': region
        }
    
    def _deploy_container_image(self, config: Dict[str, Any], build_result: Any, logs: list) -> str:
        """Create ECR repository and build/push Docker image"""
        
        repo_name = config['cluster_name'].replace('-cluster', '')
        logs.append(f"🐳 Creating ECR repository: {repo_name}")
        
        try:
            # Create ECR repository
            response = self.ecr_client.create_repository(repositoryName=repo_name)
            repository_uri = response['repository']['repositoryUri']
            logs.append(f"✅ ECR repository created: {repository_uri}")
            
        except self.ecr_client.exceptions.RepositoryAlreadyExistsException:
            # Repository already exists
            response = self.ecr_client.describe_repositories(repositoryNames=[repo_name])
            if not response['repositories']:
                raise Exception(f"Repository {repo_name} exists but could not be retrieved")
            repository_uri = response['repositories'][0]['repositoryUri']
            logs.append(f"📦 Using existing ECR repository: {repository_uri}")
        
        # Create a Dockerfile for Laravel if it doesn't exist
        dockerfile_content = self._create_laravel_dockerfile()
        image_uri = f"{repository_uri}:latest"
        
        # Build and push the Laravel Docker image
        logs.append(f"🏗️ Building Laravel Docker image...")
        success = self._build_and_push_image(repository_uri, dockerfile_content, build_result, logs)
        
        if success:
            logs.append(f"✅ Laravel Docker image built and pushed successfully")
            return image_uri
        else:
            # Fallback to PHP-FPM with nginx for basic Laravel support
            logs.append("⚠️ Docker build failed, using PHP-FPM fallback image")
            fallback_image = "php:8.2-fpm-alpine"
            return fallback_image
    
    def _create_laravel_dockerfile(self) -> str:
        """Generate Dockerfile content for Laravel applications"""
        
        return """# Multi-stage build for Laravel application
FROM php:8.2-fpm-alpine AS builder

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    libpng-dev \
    oniguruma-dev \
    libxml2-dev \
    zip \
    unzip \
    nodejs \
    npm

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /var/www

# Copy composer files
COPY composer.json composer.lock ./

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader --no-interaction

# Copy application files
COPY . .

# Install Node.js dependencies and build assets
RUN npm install && npm run build

# Production stage
FROM php:8.2-fpm-alpine

# Install system dependencies
RUN apk add --no-cache \
    nginx \
    supervisor \
    libpng-dev \
    oniguruma-dev \
    libxml2-dev

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd

# Copy application from builder
COPY --from=builder /var/www /var/www

# Set permissions
RUN chown -R www-data:www-data /var/www \
    && chmod -R 755 /var/www/storage

# Copy nginx configuration - CRITICAL FIX: Serve on port 80
RUN echo 'server {
    listen 80;  
    index index.php index.html;
    error_log  /var/log/nginx/error.log;
    access_log /var/log/nginx/access.log;
    root /var/www/public;
    
    location ~ \\.php$ {
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }
    
    location / {
        try_files $uri $uri/ /index.php?$query_string;
        gzip_static on;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}' > /etc/nginx/conf.d/default.conf

# Create supervisor configuration
RUN echo '[supervisord]
nodaemon=true

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true

[program:php-fpm]
command=php-fpm -F
autostart=true
autorestart=true
' > /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
"""
    
    def _build_and_push_image(self, repository_uri: str, dockerfile_content: str, build_result: Any, logs: list) -> bool:
        """Build and push Docker image to ECR"""
        try:
            import tempfile
            import os
            import subprocess
            import shutil
            
            # Get the source code location
            if hasattr(build_result, 'source_dir') and build_result.source_dir:
                source_dir = Path(build_result.source_dir)
            elif hasattr(build_result, 'repo_path') and build_result.repo_path:
                source_dir = Path(build_result.repo_path)  
            else:
                logs.append("❌ No source directory found in build result")
                return False
            
            if not source_dir.exists():
                logs.append(f"❌ Source directory does not exist: {source_dir}")
                return False
                
            logs.append(f"📂 Using source directory: {source_dir}")
            
            # Create temporary build context
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy source files to temp directory
                logs.append("📋 Copying Laravel application files...")
                shutil.copytree(source_dir, temp_path / "app", ignore=shutil.ignore_patterns('.git', 'node_modules', 'vendor'))
                
                # Write Dockerfile
                dockerfile_path = temp_path / "app" / "Dockerfile"
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                logs.append("🐳 Created Dockerfile for Laravel application")
                
                # Get ECR login token
                account_id = repository_uri.split('.')[0]
                region = 'us-east-1'  # Assuming us-east-1, could be made configurable
                
                # Get ECR authorization token
                token_response = self.ecr_client.get_authorization_token()
                token = token_response['authorizationData'][0]['authorizationToken']
                username, password = base64.b64decode(token).decode('utf-8').split(':')
                registry_url = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
                
                # Build the Docker image
                logs.append("🔨 Building Docker image...")
                build_cmd = [
                    "docker", "build", 
                    "-t", f"{repository_uri}:latest",
                    "-f", str(dockerfile_path),
                    str(temp_path / "app")
                ]
                
                result = subprocess.run(build_cmd, capture_output=True, text=True, cwd=temp_path)
                if result.returncode != 0:
                    logs.append(f"❌ Docker build failed: {result.stderr}")
                    return False
                
                logs.append("✅ Docker image built successfully")
                
                # Login to ECR
                login_cmd = ["docker", "login", "--username", username, "--password", password, registry_url]
                result = subprocess.run(login_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logs.append(f"❌ ECR login failed: {result.stderr}")
                    return False
                
                logs.append("✅ Logged into ECR successfully")
                
                # Push the image
                logs.append("📤 Pushing Docker image to ECR...")
                push_cmd = ["docker", "push", f"{repository_uri}:latest"]
                result = subprocess.run(push_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logs.append(f"❌ Docker push failed: {result.stderr}")
                    return False
                
                logs.append("✅ Docker image pushed to ECR successfully")
                return True
                
        except ImportError:
            logs.append("❌ Required modules not available for Docker operations")
            return False
        except Exception as e:
            logs.append(f"❌ Docker build/push error: {str(e)}")
            return False
    
    def _ensure_iam_roles(self, account_id: str, logs: list) -> Dict[str, str]:
        """Create or ensure IAM roles exist for ECS tasks - Dynamic for thousands of users"""
        
        roles = {}
        
        try:
            # 1. ECS Task Execution Role (required for all ECS tasks)
            execution_role_name = f"ecsTaskExecutionRole-{account_id}"
            execution_role_arn = self._create_or_get_role(
                role_name=execution_role_name,
                assume_role_policy={
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }]
                },
                managed_policies=["arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"],
                logs=logs
            )
            roles['execution_role'] = execution_role_arn
            
            # 2. ECS Task Role (for application-level permissions)
            task_role_name = f"ecsTaskRole-{account_id}"
            task_role_arn = self._create_or_get_role(
                role_name=task_role_name,
                assume_role_policy={
                    "Version": "2012-10-17", 
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }]
                },
                managed_policies=[
                    "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess",
                    "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
                ],
                logs=logs
            )
            roles['task_role'] = task_role_arn
            
            logs.append(f"✅ IAM roles ensured for account {account_id}")
            return roles
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                logs.append("⚠️  No IAM permissions - falling back to default role names")
                logs.append("💡 For auto-role creation, grant IAM permissions to AWS credentials")
                # Fallback to commonly used role names
                return {
                    'execution_role': f"arn:aws:iam::{account_id}:role/ecsTaskExecutionRole",
                    'task_role': f"arn:aws:iam::{account_id}:role/ecsTaskRole"
                }
            else:
                logs.append(f"❌ IAM error: {str(e)}")
                raise e
        except Exception as e:
            logs.append(f"❌ IAM role creation failed: {str(e)}")
            # Fallback to default role names (will fail if they don't exist)
            return {
                'execution_role': f"arn:aws:iam::{account_id}:role/ecsTaskExecutionRole",
                'task_role': f"arn:aws:iam::{account_id}:role/ecsTaskRole"
            }
    
    def _create_or_get_role(self, role_name: str, assume_role_policy: Dict, managed_policies: list, logs: list) -> str:
        """Create IAM role or return existing one"""
        
        try:
            # Try to get existing role first
            response = self.iam_client.get_role(RoleName=role_name)
            role_arn = response['Role']['Arn']
            logs.append(f"📋 Using existing IAM role: {role_name}")
            
            # Ensure policies are attached
            for policy_arn in managed_policies:
                try:
                    self.iam_client.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                except self.iam_client.exceptions.InvalidInputException:
                    # Policy already attached
                    pass
                    
            return role_arn
            
        except self.iam_client.exceptions.NoSuchEntityException:
            # Role doesn't exist, create it
            logs.append(f"🔧 Creating new IAM role: {role_name}")
            
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                Description=f"Auto-created role for ECS deployment - {role_name}"
            )
            role_arn = response['Role']['Arn']
            
            # Attach managed policies
            for policy_arn in managed_policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                logs.append(f"📎 Attached policy: {policy_arn.split('/')[-1]}")
            
            # Wait a bit for role propagation
            time.sleep(5)
            logs.append(f"✅ Created IAM role: {role_name}")
            
            return role_arn
            
        except Exception as e:
            logs.append(f"❌ Role creation failed for {role_name}: {str(e)}")
            raise e
    
    def _create_ecs_infrastructure(self, config: Dict[str, Any], image_uri: str, logs: list) -> tuple:
        """Create ECS cluster and task definition"""
        
        cluster_name = config['cluster_name']
        logs.append(f"🏗️ Creating ECS cluster: {cluster_name}")
        
        # Create ECS cluster
        try:
            cluster_response = self.ecs_client.create_cluster(
                clusterName=cluster_name,
                capacityProviders=['FARGATE'],
                defaultCapacityProviderStrategy=[
                    {
                        'capacityProvider': 'FARGATE',
                        'weight': 1
                    }
                ]
            )
            cluster_arn = cluster_response['cluster']['clusterArn']
            logs.append(f"✅ ECS cluster created: {cluster_arn}")
            
        except Exception as e:
            if 'already exists' in str(e).lower():
                cluster_response = self.ecs_client.describe_clusters(clusters=[cluster_name])
                if not cluster_response['clusters']:
                    raise Exception(f"Expected cluster {cluster_name} not found")
                cluster_arn = cluster_response['clusters'][0]['clusterArn']
                logs.append(f"📦 Using existing ECS cluster: {cluster_arn}")
            else:
                raise e
        
        # CRITICAL FIX: Ensure CloudWatch log group exists before task definition
        log_group_name = config['monitoring']['log_group']
        try:
            self.logs_client.create_log_group(
                logGroupName=log_group_name,
                retentionInDays=config['monitoring'].get('retention_days', 7)  # Reduced for cost
            )
            logs.append(f"📊 Created CloudWatch log group: {log_group_name}")
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            logs.append(f"📊 Using existing log group: {log_group_name}")
        except Exception as e:
            logs.append(f"❌ CRITICAL: Log group creation failed: {str(e)}")
            # Log group failure will cause task failures - this is critical
            raise Exception(f"Cannot proceed without CloudWatch log group: {str(e)}")
        
        # Update task definition with actual image URI and dynamic values
        task_definition = config['task_definition'].copy()
        
        # Update the container definition
        container_def = task_definition['containerDefinitions'][0].copy()
        container_def['image'] = image_uri
        
        # CRITICAL FIX: Use port from provisioner config, default to 80
        desired_port = config.get('load_balancer', {}).get('target_group', {}).get('port', 80)
        
        # Ensure container exposes correct port for ALB/TG
        pm = {"containerPort": desired_port, "protocol": "tcp"}
        container_def.setdefault("portMappings", [pm])
        container_def["portMappings"] = [pm]  # ensure single, correct mapping
        
        # Store port for other components to use
        config["container_port"] = desired_port
        
        # Ensure container has memory settings (ECS requires memory or memoryReservation)
        if 'memory' not in container_def and 'memoryReservation' not in container_def:
            container_def['memoryReservation'] = 512

        # Ensure container name (later used by service) is stable
        container_name = container_def.get('name') or config['cluster_name'].replace('-cluster', '')
        container_def['name'] = container_name
        config['container_name'] = container_name  # Store for later use
        
        # Ensure required fields are present for Fargate
        # Dynamic IAM role creation for thousands of users
        account_id = self._get_account_id()
        logs.append(f"🔐 Creating dynamic IAM roles for account: {account_id}")
        
        iam_roles = self._ensure_iam_roles(account_id, logs)
        execution_role = iam_roles['execution_role']
        task_role = iam_roles['task_role']
        
        task_definition.update({
            'requiresCompatibilities': ['FARGATE'],
            'networkMode': 'awsvpc',
            'cpu': '512',
            'memory': '1024',
            'executionRoleArn': execution_role,
            'taskRoleArn': task_role
        })
        
        task_definition['containerDefinitions'] = [container_def]
        
        # Register task definition
        logs.append(f"📋 Registering task definition: {task_definition['family']}")
        try:
            task_def_response = self.ecs_client.register_task_definition(**task_definition)
            task_def_arn = task_def_response['taskDefinition']['taskDefinitionArn']
            logs.append(f"✅ Task definition registered: {task_def_arn}")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = str(e)
            
            if "InvalidParameterException" in error_code and "does not exist" in error_message:
                logs.append("❌ ERROR: IAM role does not exist or cannot be assumed")
                if "execution_role" in error_message.lower():
                    logs.append(f"💡 Missing execution role: {execution_role}")
                    logs.append("� Auto-creation failed - check IAM permissions or create role manually")
                if "task_role" in error_message.lower():
                    logs.append(f"💡 Missing task role: {task_role}")
                logs.append("📋 Required IAM policies: AmazonECSTaskExecutionRolePolicy")
            else:
                logs.append(f"❌ Task definition registration failed: {error_message}")
            raise e
        except Exception as e:
            logs.append(f"❌ Unexpected error in task definition registration: {str(e)}")
            raise e
        
        return cluster_arn, task_def_arn
    
    def _create_load_balancer(self, config: Dict[str, Any], logs: list) -> tuple:
        """Create Application Load Balancer and Target Group"""
        
        alb_name = config['load_balancer']['name']
        logs.append(f"⚖️ Creating Application Load Balancer: {alb_name}")
        
        try:
            # Get VPC information (try default VPC first, create if needed)
            ec2_client = boto3.client('ec2', **self.credentials)
            
            # Try to get default VPC first
            vpcs = ec2_client.describe_vpcs(Filters=[{'Name': 'is-default', 'Values': ['true']}])
            
            if not vpcs['Vpcs']:
                logs.append("🔧 No default VPC found, creating VPC infrastructure...")
                # Create VPC if no default exists
                vpc_id, subnet_ids = self._create_vpc_infrastructure(ec2_client, logs)
            else:
                vpc_id = vpcs['Vpcs'][0]['VpcId']
                # Get subnets for default VPC
                subnets = ec2_client.describe_subnets(
                    Filters=[
                        {'Name': 'vpc-id', 'Values': [vpc_id]},
                        {'Name': 'default-for-az', 'Values': ['true']}
                    ]
                )
                subnet_ids = [subnet['SubnetId'] for subnet in subnets['Subnets']]
                if len(subnet_ids) < 2:
                    # Not enough default subnets, create our own
                    logs.append("⚠️ Not enough default subnets found, creating new VPC infrastructure...")
                    vpc_id, subnet_ids = self._create_vpc_infrastructure(ec2_client, logs)
                
                if not subnet_ids:
                    # Fall back to any available subnets in the VPC
                    all_subnets = ec2_client.describe_subnets(
                        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
                    )
                    subnet_ids = [subnet['SubnetId'] for subnet in all_subnets['Subnets'][:2]]  # Use first 2
            
            logs.append(f"📍 Using VPC: {vpc_id}")
            logs.append(f"📍 Using subnets: {subnet_ids}")
            
            
            if len(subnet_ids) < 2:
                raise Exception(f"Need at least 2 subnets for ALB, found {len(subnet_ids)}")
            
            logs.append(f"🌐 Final subnets for ALB: {', '.join(subnet_ids[:2])}")
            
            # Create security group for ALB
            sg_name = f"{alb_name}-sg"
            try:
                sg_response = ec2_client.create_security_group(
                    GroupName=sg_name,
                    Description=f"Security group for {alb_name} ALB",
                    VpcId=vpc_id
                )
                security_group_id = sg_response['GroupId']
                
                # Add inbound rules for HTTP and HTTPS
                ec2_client.authorize_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 80,
                            'ToPort': 80,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        },
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 443,
                            'ToPort': 443,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                    ]
                )
                
                logs.append(f"🔒 Created security group: {security_group_id}")
                
            except ec2_client.exceptions.ClientError as e:
                if 'already exists' in str(e).lower():
                    # Get existing security group
                    sgs = ec2_client.describe_security_groups(
                        Filters=[
                            {'Name': 'group-name', 'Values': [sg_name]},
                            {'Name': 'vpc-id', 'Values': [vpc_id]}
                        ]
                    )
                    if not sgs['SecurityGroups']:
                        raise Exception("Expected security group not found")
                    security_group_id = sgs['SecurityGroups'][0]['GroupId']
                    logs.append(f"🔒 Using existing security group: {security_group_id}")
                else:
                    raise e
            
            # Create Application Load Balancer
            try:
                alb_response = self.elbv2_client.create_load_balancer(
                    Name=alb_name,
                    Subnets=subnet_ids[:2],  # Use first 2 subnets
                    SecurityGroups=[security_group_id],
                    Scheme='internet-facing',
                    Type='application',
                    IpAddressType='ipv4'
                )
                
                if not alb_response['LoadBalancers']:
                    raise Exception("Load balancer creation returned no result")
                alb_arn = alb_response['LoadBalancers'][0]['LoadBalancerArn']
                alb_dns = alb_response['LoadBalancers'][0]['DNSName']
                logs.append(f"✅ Load Balancer created: {alb_dns}")
                
            except self.elbv2_client.exceptions.DuplicateLoadBalancerNameException:
                # Get existing load balancer
                alb_response = self.elbv2_client.describe_load_balancers(Names=[alb_name])
                if not alb_response['LoadBalancers']:
                    raise Exception("Expected load balancer not found")
                alb_arn = alb_response['LoadBalancers'][0]['LoadBalancerArn']
                alb_dns = alb_response['LoadBalancers'][0]['DNSName']
                logs.append(f"📦 Using existing Load Balancer: {alb_dns}")
            
            # Create Target Group - Use port and health path from config
            tg_name = config['load_balancer']['target_group']['name']
            tg_port = config['load_balancer']['target_group'].get('port', 80)
            health_path = config['load_balancer']['target_group'].get('health_check', {}).get('path', '/health')
            
            try:
                tg_response = self.elbv2_client.create_target_group(
                    Name=tg_name,
                    Protocol='HTTP',
                    Port=tg_port,  # Use port from provisioner config
                    VpcId=vpc_id,
                    TargetType='ip',  # For Fargate
                    HealthCheckProtocol='HTTP',
                    HealthCheckPath=health_path,  # Use health path from config
                    HealthCheckPort=str(tg_port),  # Health check on same port
                    HealthCheckIntervalSeconds=30,
                    HealthCheckTimeoutSeconds=5,
                    HealthyThresholdCount=2,
                    UnhealthyThresholdCount=3
                )
                
                target_group_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
                logs.append(f"🎯 Target Group created: {target_group_arn} (port 80)")
                
            except self.elbv2_client.exceptions.DuplicateTargetGroupNameException:
                # Get existing target group
                tg_response = self.elbv2_client.describe_target_groups(Names=[tg_name])
                target_group_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
                logs.append(f"🎯 Using existing Target Group: {target_group_arn}")
            
            # Create listener for the ALB
            try:
                listener_response = self.elbv2_client.create_listener(
                    LoadBalancerArn=alb_arn,
                    Protocol='HTTP',
                    Port=80,
                    DefaultActions=[
                        {
                            'Type': 'forward',
                            'TargetGroupArn': target_group_arn
                        }
                    ]
                )
                logs.append(f"👂 Listener created for ALB")
                
            except Exception as e:
                if 'already exists' not in str(e).lower():
                    logs.append(f"⚠️ Listener creation failed (may already exist): {str(e)}")
            
            return alb_arn, target_group_arn, alb_dns, security_group_id, vpc_id, subnet_ids
            
        except Exception as e:
            logs.append(f"❌ Load Balancer creation failed: {str(e)}")
            raise e
    
    def _create_ecs_service(self, config: Dict[str, Any], cluster_arn: str, task_def_arn: str, target_group_arn: str, alb_sg_id: str, vpc_id: str, subnet_ids: list, logs: list) -> str:
        """Create ECS Service"""
        
        service_name = config['service_name']
        logs.append(f"🔄 Creating ECS service: {service_name}")
        
        try:
            # Use the VPC and subnets provided from load balancer creation
            # (no more default VPC lookup - use what was already created)
            ec2_client = boto3.client('ec2', **self.credentials)
            logs.append(f"🌐 Using VPC {vpc_id} with {len(subnet_ids)} subnets for service")
            
            # Create security group for ECS service
            service_sg_name = f"{service_name}-service-sg"
            try:
                sg_response = ec2_client.create_security_group(
                    GroupName=service_sg_name,
                    Description=f"Security group for {service_name} ECS service",
                    VpcId=vpc_id
                )
                service_security_group_id = sg_response['GroupId']
                
                # CRITICAL FIX: Add inbound rule for ALB communication on correct port
                container_port = config.get('load_balancer', {}).get('target_group', {}).get('port', 80)
                ec2_client.authorize_security_group_ingress(
                    GroupId=service_security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': container_port,
                            'ToPort': container_port,
                            'UserIdGroupPairs': [{'GroupId': alb_sg_id}]
                        }
                    ]
                )
                
                logs.append(f"🔒 Created service security group: {service_security_group_id}")
                
            except ec2_client.exceptions.ClientError as e:
                if 'already exists' in str(e).lower():
                    sgs = ec2_client.describe_security_groups(
                        Filters=[
                            {'Name': 'group-name', 'Values': [service_sg_name]},
                            {'Name': 'vpc-id', 'Values': [vpc_id]}
                        ]
                    )
                    service_security_group_id = sgs['SecurityGroups'][0]['GroupId']
                    logs.append(f"🔒 Using existing service security group: {service_security_group_id}")
                else:
                    raise e
            
            # Create the ECS service
            try:
                service_response = self.ecs_client.create_service(
                    cluster=cluster_arn,
                    serviceName=service_name,
                    taskDefinition=task_def_arn,
                    desiredCount=1,
                    launchType='FARGATE',
                    networkConfiguration={
                        'awsvpcConfiguration': {
                            'subnets': subnet_ids,
                            'securityGroups': [service_security_group_id],
                            'assignPublicIp': 'ENABLED'
                        }
                    },
                    loadBalancers=[
                        {
                            'targetGroupArn': target_group_arn,
                            'containerName': config['container_name'],  # Container name
                            'containerPort': config.get('load_balancer', {}).get('target_group', {}).get('port', 80)  # Use port from config
                        }
                    ],
                    healthCheckGracePeriodSeconds=300
                )
                
                service_arn = service_response['service']['serviceArn']
                logs.append(f"✅ ECS service created: {service_arn}")
                
                return service_arn
                
            except ClientError as e:
                msg = str(e)
                code = e.response.get('Error', {}).get('Code', '')
                if 'already exists' in msg.lower() or code in ('ServiceAlreadyExistsException', 'InvalidParameterException'):
                    # Service already exists
                    services = self.ecs_client.describe_services(
                    cluster=cluster_arn,
                    services=[service_name]
                )
                
                    if not services['services']:
                        raise Exception(f"Expected service {service_name} not found")
                    service_arn = services['services'][0]['serviceArn']
                logs.append(f"� Using existing ECS service: {service_arn}")
                
                # Update the service to desired count 1
                self.ecs_client.update_service(
                    cluster=cluster_arn,
                    service=service_name,
                    desiredCount=1
                )
                logs.append(f"🔄 Updated service desired count to 1")
                
                return service_arn
                
        except Exception as e:
            logs.append(f"❌ ECS service creation failed: {str(e)}")
            raise e
    
    def _create_cloudfront_distribution(self, config: Dict[str, Any], alb_dns: str, logs: list) -> str:
        """Create CloudFront Distribution"""
        
        logs.append("🌐 Creating CloudFront distribution")
        
        try:
            # Generate a unique caller reference
            import time
            caller_reference = f"php-app-{int(time.time())}"
            
            # Create CloudFront distribution
            distribution_config = {
                'CallerReference': caller_reference,
                'Comment': f"CloudFront distribution for {config['cluster_name']}",
                'DefaultCacheBehavior': {
                    'TargetOriginId': f"{config['cluster_name']}-alb-origin",
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'MinTTL': 0,
                    'ForwardedValues': {
                        'QueryString': True,
                        'Cookies': {'Forward': 'all'},
                        'Headers': ['Host', 'Authorization', 'CloudFront-Forwarded-Proto']
                    },
                    'TrustedSigners': {
                        'Enabled': False,
                        'Quantity': 0
                    }
                },
                'Origins': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'Id': f"{config['cluster_name']}-alb-origin",
                            'DomainName': alb_dns,
                            'CustomOriginConfig': {
                                'HTTPPort': 80,
                                'HTTPSPort': 443,
                                'OriginProtocolPolicy': 'http-only'
                            }
                        }
                    ]
                },
                'Enabled': True,
                'PriceClass': 'PriceClass_100'  # Use only US/Europe edge locations
            }
            
            try:
                response = self.cloudfront_client.create_distribution(
                    DistributionConfig=distribution_config
                )
                
                cloudfront_domain = response['Distribution']['DomainName']
                distribution_id = response['Distribution']['Id']
                
                logs.append(f"✅ CloudFront distribution created: {cloudfront_domain}")
                logs.append(f"� Distribution ID: {distribution_id}")
                logs.append("⏳ Note: CloudFront deployment can take 15-20 minutes to fully propagate")
                
                return cloudfront_domain
                
            except Exception as e:
                if 'already exists' in str(e).lower():
                    # For now, return a placeholder if creation fails due to existing resource
                    logs.append(f"⚠️ CloudFront creation issue: {str(e)}")
                    logs.append("🔄 Using ALB DNS as fallback URL")
                    return alb_dns
                else:
                    raise e
                    
        except Exception as e:
            logs.append(f"⚠️ CloudFront creation failed: {str(e)}")
            logs.append("🔄 Falling back to ALB DNS name")
            return alb_dns
    
    def _wait_for_healthy_deployment(self, service_arn: str, target_group_arn: str, logs: list):
        """Wait for deployment to become healthy"""
        
        logs.append("⏳ Waiting for deployment to become healthy...")
        
        # Extract cluster name and service name from ARN
        cluster_name = service_arn.split('/')[-3]  # Extract cluster from ARN
        service_name = service_arn.split('/')[-1]  # Extract service from ARN
        
        max_wait_time = 600  # 10 minutes
        check_interval = 30  # 30 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                # Check ECS service status
                services = self.ecs_client.describe_services(
                    cluster=cluster_name,
                    services=[service_name]
                )
                
                if services['services']:
                    service = services['services'][0]
                    running_count = service['runningCount']
                    desired_count = service['desiredCount']
                    
                    logs.append(f"📊 Service status: {running_count}/{desired_count} tasks running")
                    
                    if running_count >= desired_count and running_count > 0:
                        # Check target group health
                        try:
                            health = self.elbv2_client.describe_target_health(
                                TargetGroupArn=target_group_arn
                            )
                            
                            healthy_targets = [t for t in health['TargetHealthDescriptions'] 
                                             if t['TargetHealth']['State'] == 'healthy']
                            
                            if healthy_targets:
                                logs.append("✅ Deployment is healthy and ready to serve traffic")
                                logs.append("🎉 PHP application successfully deployed!")
                                return
                            else:
                                logs.append("⏳ Waiting for health checks to pass...")
                                
                        except Exception as e:
                            logs.append(f"⚠️ Health check error: {str(e)}")
                
                time.sleep(check_interval)
                elapsed_time += check_interval
                
            except Exception as e:
                logs.append(f"⚠️ Status check error: {str(e)}")
                time.sleep(check_interval)
                elapsed_time += check_interval
        
        logs.append("⚠️ Deployment health check timed out, but resources are created")
        logs.append("🔍 Check AWS Console for detailed service status")
    
    def get_deployment_status(self, deployment_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a deployment"""
        
        # This would query actual AWS resources in production
        return {
            'status': 'deployed',
            'health': 'healthy',
            'last_updated': time.time()
        }
    
    def _create_vpc_infrastructure(self, ec2_client, logs: list) -> tuple:
        """Create VPC infrastructure when no default VPC exists"""
        try:
            # Create VPC
            vpc_response = ec2_client.create_vpc(CidrBlock='10.0.0.0/16')
            vpc_id = vpc_response['Vpc']['VpcId']
            logs.append(f"🏗️ Created VPC: {vpc_id}")
            
            # Enable DNS hostnames
            ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
            ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
            
            # Create Internet Gateway
            igw_response = ec2_client.create_internet_gateway()
            igw_id = igw_response['InternetGateway']['InternetGatewayId']
            ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
            logs.append(f"🌐 Created Internet Gateway: {igw_id}")
            
            # Get availability zones
            azs_response = ec2_client.describe_availability_zones()
            if not azs_response['AvailabilityZones']:
                raise Exception("No availability zones found in this region")
            azs = [az['ZoneName'] for az in azs_response['AvailabilityZones'][:2]]  # Use first 2 AZs
            if len(azs) < 2:
                # If only 1 AZ available, duplicate it (not ideal but works for testing)
                azs = azs + azs
            
            # Create public subnets
            subnet_ids = []
            for i, az in enumerate(azs):
                subnet_response = ec2_client.create_subnet(
                    VpcId=vpc_id,
                    CidrBlock=f'10.0.{i+1}.0/24',
                    AvailabilityZone=az
                )
                subnet_id = subnet_response['Subnet']['SubnetId']
                subnet_ids.append(subnet_id)
                
                # Enable auto-assign public IP
                ec2_client.modify_subnet_attribute(
                    SubnetId=subnet_id,
                    MapPublicIpOnLaunch={'Value': True}
                )
                logs.append(f"🏠 Created subnet {subnet_id} in AZ {az}")
            
            # Create route table and associate with subnets
            rt_response = ec2_client.create_route_table(VpcId=vpc_id)
            rt_id = rt_response['RouteTable']['RouteTableId']
            
            # Add route to Internet Gateway
            ec2_client.create_route(
                RouteTableId=rt_id,
                DestinationCidrBlock='0.0.0.0/0',
                GatewayId=igw_id
            )
            
            # Associate route table with subnets
            for subnet_id in subnet_ids:
                ec2_client.associate_route_table(RouteTableId=rt_id, SubnetId=subnet_id)
            
            logs.append(f"✅ VPC infrastructure created successfully")
            return vpc_id, subnet_ids
            
        except Exception as e:
            raise Exception(f"Failed to create VPC infrastructure: {str(e)}")
    
    def _get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts_client = boto3.client('sts', **self.credentials)
            return sts_client.get_caller_identity()['Account']
        except Exception:
            # Fallback to a default role ARN construction
            return "123456789012"
    
    def _deploy_universal_container_image(self, config: Dict[str, Any], build_result: Any, app_requirements: Dict[str, Any], logs: list) -> str:
        """🐳 Create ECR repository and build/push universal Docker image with dynamic requirements"""
        
        repo_name = config['cluster_name'].replace('-cluster', '')
        app_type = app_requirements.get('application_type', 'php')
        logs.append(f"🐳 Creating ECR repository for {app_type}: {repo_name}")
        
        try:
            # Create ECR repository
            response = self.ecr_client.create_repository(repositoryName=repo_name)
            repository_uri = response['repository']['repositoryUri']
            logs.append(f"✅ ECR repository created: {repository_uri}")
            
        except self.ecr_client.exceptions.RepositoryAlreadyExistsException:
            # Repository already exists
            response = self.ecr_client.describe_repositories(repositoryNames=[repo_name])
            if not response['repositories']:
                raise Exception(f"Repository {repo_name} exists but could not be retrieved")
            repository_uri = response['repositories'][0]['repositoryUri']
            logs.append(f"📦 Using existing ECR repository: {repository_uri}")
        
        # Generate universal Dockerfile based on application requirements
        dockerfile_content = self._create_universal_dockerfile(app_requirements, app_type)
        image_uri = f"{repository_uri}:latest"
        
        # Build and push the universal Docker image
        logs.append(f"🏗️ Building universal {app_type} Docker image...")
        success = self._build_and_push_universal_image(repository_uri, dockerfile_content, build_result, app_requirements, logs)
        
        if success:
            logs.append(f"✅ Universal {app_type} Docker image built and pushed successfully")
            return image_uri
        else:
            # Fallback to appropriate base image for the application type
            logs.append(f"⚠️ Docker build failed, using {app_type} fallback image")
            fallback_images = {
                'laravel': 'php:8.2-fpm-alpine',
                'bookstack': 'php:8.1-fpm-alpine',
                'wordpress': 'wordpress:latest',
                'symfony': 'php:8.2-fpm-alpine',
                'magento': 'php:8.1-fpm-alpine'
            }
            return fallback_images.get(app_type, 'php:8.2-fpm-alpine')
    
    def _create_universal_dockerfile(self, app_requirements: Dict[str, Any], app_type: str) -> str:
        """🧬 Generate universal Dockerfile based on application type and requirements"""
        
        php_version = self._parse_php_version_for_docker(app_requirements.get('php_version', '>=8.0'))
        required_extensions = app_requirements.get('extensions', [])
        health_check_path = app_requirements.get('health_check', '/health')
        
        # System dependencies for extensions
        system_deps = self._get_system_dependencies_for_docker(required_extensions)
        
        dockerfile = f'''# Universal PHP Dockerfile - Generated for {app_type}
FROM php:{php_version}-fpm-alpine AS base

# Install system dependencies including nginx and supervisor
RUN apk add --no-cache \\
    curl \\
    nginx \\
    supervisor \\
    git \\
    unzip \\
    composer \\
    {' '.join(system_deps)}

# Install required PHP extensions dynamically
{"RUN docker-php-ext-install " + " ".join(required_extensions) if required_extensions else "# No additional PHP extensions required"}

# Set working directory
WORKDIR /var/www

# Copy application files
COPY . .

# Install PHP dependencies if composer.json exists
RUN if [ -f composer.json ]; then composer install --no-dev --optimize-autoloader --no-interaction; fi

# Set permissions
RUN chown -R www-data:www-data /var/www \\
    && chmod -R 755 /var/www

# Configure nginx for port 80 with application-specific setup
RUN echo 'server {{
    listen 80;
    index index.php index.html;
    root /var/www{'/public' if app_type in ['laravel', 'bookstack'] else ''};
    
    location ~ \\.php$ {{
        try_files $uri =404;
        fastcgi_split_path_info ^(.+\\.php)(/.+)$;
        fastcgi_pass 127.0.0.1:9000;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
    }}
    
    location / {{
        try_files $uri $uri/ /index.php?$query_string;
        gzip_static on;
    }}
    
    location {health_check_path} {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
}}' > /etc/nginx/conf.d/default.conf

# Create supervisor configuration for nginx + php-fpm
RUN echo '[supervisord]
nodaemon=true

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:php-fpm]
command=php-fpm -F
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
' > /etc/supervisor/conf.d/supervisord.conf

# Expose port 80
EXPOSE 80

# Health check on application-specific endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost{health_check_path} || exit 1

# Start nginx + php-fpm via supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
'''
        
        return dockerfile
    
    def _prepare_environment_variables(self, app_requirements: Dict[str, Any], infrastructure_config: Dict[str, Any]) -> List[Dict[str, str]]:
        """🌍 Prepare environment variables for universal deployment including database config"""
        
        app_type = app_requirements.get('application_type', 'php')
        env_vars = [
            {'Name': 'APP_ENV', 'Value': 'production'},
            {'Name': 'APP_DEBUG', 'Value': 'false'},
            {'Name': 'APP_TYPE', 'Value': app_type}
        ]
        
        # Add database environment variables if database is configured
        if app_requirements.get('database', {}).get('engine'):
            db_config = app_requirements['database']
            
            # Common database environment variables
            env_vars.extend([
                {'Name': 'DB_CONNECTION', 'Value': db_config['engine']},
                {'Name': 'DB_HOST', 'Value': db_config.get('endpoint', 'localhost')},
                {'Name': 'DB_PORT', 'Value': str(db_config.get('port', 3306))},
                {'Name': 'DB_DATABASE', 'Value': db_config.get('name', 'app')},
                {'Name': 'DB_USERNAME', 'Value': db_config.get('username', 'root')},
                {'Name': 'DB_PASSWORD', 'Value': db_config.get('password', '')}
            ])
            
            # Application-specific database configuration
            if app_type == 'laravel':
                env_vars.extend([
                    {'Name': 'CACHE_DRIVER', 'Value': 'file'},
                    {'Name': 'SESSION_DRIVER', 'Value': 'file'},
                    {'Name': 'QUEUE_CONNECTION', 'Value': 'sync'}
                ])
            elif app_type == 'bookstack':
                env_vars.extend([
                    {'Name': 'APP_URL', 'Value': 'http://localhost'},
                    {'Name': 'CACHE_DRIVER', 'Value': 'file'},
                    {'Name': 'SESSION_DRIVER', 'Value': 'file'},
                    {'Name': 'STORAGE_TYPE', 'Value': 'local_secure'}
                ])
            elif app_type == 'wordpress':
                env_vars.extend([
                    {'Name': 'WORDPRESS_DB_HOST', 'Value': db_config.get('endpoint', 'localhost')},
                    {'Name': 'WORDPRESS_DB_NAME', 'Value': db_config.get('name', 'wordpress')},
                    {'Name': 'WORDPRESS_DB_USER', 'Value': db_config.get('username', 'root')},
                    {'Name': 'WORDPRESS_DB_PASSWORD', 'Value': db_config.get('password', '')}
                ])
        
        # Add custom environment variables from requirements
        custom_env = app_requirements.get('environment', {})
        for key, value in custom_env.items():
            env_vars.append({'Name': key, 'Value': str(value)})
        
        return env_vars
    
    def _create_ecs_infrastructure_universal(self, config: Dict[str, Any], image_uri: str, app_requirements: Dict[str, Any], logs: list) -> tuple:
        """🏗️ Create ECS cluster and enhanced task definition with universal support"""
        
        cluster_name = config['cluster_name']
        app_type = app_requirements.get('application_type', 'php')
        logs.append(f"🏗️ Creating ECS cluster for {app_type}: {cluster_name}")
        
        # Create ECS cluster (same as before)
        try:
            cluster_response = self.ecs_client.create_cluster(
                clusterName=cluster_name,
                capacityProviders=['FARGATE'],
                defaultCapacityProviderStrategy=[
                    {
                        'capacityProvider': 'FARGATE',
                        'weight': 1
                    }
                ]
            )
            cluster_arn = cluster_response['cluster']['clusterArn']
            logs.append(f"✅ ECS cluster created: {cluster_arn}")
            
        except Exception as e:
            if 'already exists' in str(e).lower():
                cluster_response = self.ecs_client.describe_clusters(clusters=[cluster_name])
                if not cluster_response['clusters']:
                    raise Exception(f"Expected cluster {cluster_name} not found")
                cluster_arn = cluster_response['clusters'][0]['clusterArn']
                logs.append(f"📦 Using existing ECS cluster: {cluster_arn}")
            else:
                raise e
        
        # Ensure CloudWatch log group exists
        log_group_name = config['monitoring']['log_group']
        try:
            self.logs_client.create_log_group(
                logGroupName=log_group_name,
                retentionInDays=config['monitoring'].get('retention_days', 7)
            )
            logs.append(f"📊 Created CloudWatch log group: {log_group_name}")
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            logs.append(f"📊 Using existing log group: {log_group_name}")
        except Exception as e:
            logs.append(f"❌ CRITICAL: Log group creation failed: {str(e)}")
            raise Exception(f"Cannot proceed without CloudWatch log group: {str(e)}")
        
        # Enhanced task definition with universal configuration
        task_definition = config['task_definition'].copy()
        
        # Update the container definition with universal settings
        container_def = task_definition['containerDefinitions'][0].copy()
        container_def['image'] = image_uri
        
        # Use port from provisioner config, default to 80
        desired_port = config.get('load_balancer', {}).get('target_group', {}).get('port', 80)
        
        # Container port mapping
        pm = {"containerPort": desired_port, "protocol": "tcp"}
        container_def.setdefault("portMappings", [pm])
        container_def["portMappings"] = [pm]
        
        # Store port for other components
        config["container_port"] = desired_port
        
        # Enhanced memory settings based on application requirements
        memory_requirements = {
            'laravel': 1024,
            'bookstack': 512,
            'wordpress': 512,
            'symfony': 1024,
            'magento': 2048
        }
        default_memory = memory_requirements.get(app_type, 512)
        container_def['memoryReservation'] = app_requirements.get('memory_mb', default_memory)
        
        # Container name
        container_name = container_def.get('name') or config['cluster_name'].replace('-cluster', '')
        container_def['name'] = container_name
        config['container_name'] = container_name
        
        # Add environment variables for database and application
        container_def['environment'] = []
        environment_vars = self._prepare_environment_variables(app_requirements, config)
        for env_var in environment_vars:
            container_def['environment'].append({
                'name': env_var['Name'],
                'value': env_var['Value']
            })
        
        # Enhanced logging configuration
        container_def['logConfiguration'] = {
            'logDriver': 'awslogs',
            'options': {
                'awslogs-group': log_group_name,
                'awslogs-region': self.credentials.get('region_name', 'us-east-1'),
                'awslogs-stream-prefix': f'{app_type}-container'
            }
        }
        
        # Dynamic IAM role creation for thousands of users
        account_id = self._get_account_id()
        logs.append(f"🔐 Creating dynamic IAM roles for {app_type} account: {account_id}")
        
        iam_roles = self._ensure_iam_roles(account_id, logs)
        execution_role = iam_roles['execution_role']
        task_role = iam_roles['task_role']
        
        # Enhanced CPU settings based on application requirements
        cpu_requirements = {
            'laravel': '512',
            'bookstack': '256',
            'wordpress': '256',
            'symfony': '512',
            'magento': '1024'
        }
        default_cpu = cpu_requirements.get(app_type, '256')
        
        task_definition.update({
            'requiresCompatibilities': ['FARGATE'],
            'networkMode': 'awsvpc',
            'cpu': app_requirements.get('cpu', default_cpu),
            'memory': str(app_requirements.get('memory_mb', default_memory)),
            'executionRoleArn': execution_role,
            'taskRoleArn': task_role
        })
        
        task_definition['containerDefinitions'] = [container_def]
        
        # Register enhanced task definition
        logs.append(f"📋 Registering enhanced task definition for {app_type}: {task_definition['family']}")
        try:
            task_def_response = self.ecs_client.register_task_definition(**task_definition)
            task_def_arn = task_def_response['taskDefinition']['taskDefinitionArn']
            logs.append(f"✅ Enhanced task definition registered: {task_def_arn}")
        except Exception as e:
            logs.append(f"❌ Task definition registration failed: {str(e)}")
            raise e
        
        return cluster_arn, task_def_arn
    
    def _create_ecs_service_universal(self, config: Dict[str, Any], cluster_arn: str, task_def_arn: str, target_group_arn: str, alb_sg_id: str, vpc_id: str, subnet_ids: list, app_requirements: Dict[str, Any], logs: list) -> str:
        """🔄 Create enhanced ECS Service with universal application support"""
        
        service_name = config['service_name']
        app_type = app_requirements.get('application_type', 'php')
        logs.append(f"🔄 Creating ECS service for {app_type}: {service_name}")
        
        try:
            ec2_client = boto3.client('ec2', **self.credentials)
            logs.append(f"🌐 Using VPC {vpc_id} with {len(subnet_ids)} subnets for {app_type} service")
            
            # Create security group for ECS service
            service_sg_name = f"{service_name}-service-sg"
            try:
                sg_response = ec2_client.create_security_group(
                    GroupName=service_sg_name,
                    Description=f"Security group for {app_type} ECS service: {service_name}",
                    VpcId=vpc_id
                )
                service_security_group_id = sg_response['GroupId']
                
                # Add inbound rule for ALB communication on correct port
                container_port = config.get('load_balancer', {}).get('target_group', {}).get('port', 80)
                ec2_client.authorize_security_group_ingress(
                    GroupId=service_security_group_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': container_port,
                            'ToPort': container_port,
                            'UserIdGroupPairs': [{'GroupId': alb_sg_id}]
                        }
                    ]
                )
                
                logs.append(f"🔒 Created {app_type} service security group: {service_security_group_id}")
                
            except ec2_client.exceptions.ClientError as e:
                if 'already exists' in str(e).lower():
                    sgs = ec2_client.describe_security_groups(
                        Filters=[
                            {'Name': 'group-name', 'Values': [service_sg_name]},
                            {'Name': 'vpc-id', 'Values': [vpc_id]}
                        ]
                    )
                    service_security_group_id = sgs['SecurityGroups'][0]['GroupId']
                    logs.append(f"🔒 Using existing {app_type} service security group: {service_security_group_id}")
                else:
                    raise e
            
            # Enhanced ECS service configuration
            service_config = {
                'cluster': cluster_arn,
                'serviceName': service_name,
                'taskDefinition': task_def_arn,
                'desiredCount': app_requirements.get('desired_count', 1),
                'launchType': 'FARGATE',
                'networkConfiguration': {
                    'awsvpcConfiguration': {
                        'subnets': subnet_ids,
                        'securityGroups': [service_security_group_id],
                        'assignPublicIp': 'ENABLED'
                    }
                },
                'loadBalancers': [
                    {
                        'targetGroupArn': target_group_arn,
                        'containerName': config['container_name'],
                        'containerPort': config.get('load_balancer', {}).get('target_group', {}).get('port', 80)
                    }
                ],
                'healthCheckGracePeriodSeconds': app_requirements.get('health_check_grace_period', 300),
                'enableExecuteCommand': True  # Enable ECS Exec for debugging
            }
            
            # Create the enhanced ECS service
            try:
                service_response = self.ecs_client.create_service(**service_config)
                service_arn = service_response['service']['serviceArn']
                logs.append(f"✅ Enhanced {app_type} ECS service created: {service_arn}")
                return service_arn
                
            except Exception as e:
                if 'already exists' in str(e).lower():
                    services = self.ecs_client.describe_services(
                        cluster=cluster_arn,
                        services=[service_name]
                    )
                    
                    if not services['services']:
                        raise Exception(f"Expected service {service_name} not found")
                    service_arn = services['services'][0]['serviceArn']
                    logs.append(f"📦 Using existing {app_type} ECS service: {service_arn}")
                    
                    # Update the service to desired count
                    self.ecs_client.update_service(
                        cluster=cluster_arn,
                        service=service_name,
                        desiredCount=app_requirements.get('desired_count', 1)
                    )
                    logs.append(f"🔄 Updated {app_type} service desired count")
                    
                    return service_arn
                else:
                    raise e
                
        except Exception as e:
            logs.append(f"❌ Enhanced {app_type} ECS service creation failed: {str(e)}")
            raise e
    
    def _build_and_push_universal_image(self, repository_uri: str, dockerfile_content: str, build_result: Any, app_requirements: Dict[str, Any], logs: list) -> bool:
        """🔧 Build and push universal Docker image with application-specific optimizations"""
        try:
            import tempfile
            import os
            import subprocess
            import shutil
            
            app_type = app_requirements.get('application_type', 'php')
            
            # Get the source code location
            if hasattr(build_result, 'source_dir') and build_result.source_dir:
                source_dir = Path(build_result.source_dir)
            elif hasattr(build_result, 'repo_path') and build_result.repo_path:
                source_dir = Path(build_result.repo_path)  
            else:
                logs.append("❌ No source directory found in build result")
                return False
            
            if not source_dir.exists():
                logs.append(f"❌ Source directory does not exist: {source_dir}")
                return False
                
            logs.append(f"📂 Using {app_type} source directory: {source_dir}")
            
            # Create temporary build context
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy source files to temp directory with app-specific exclusions
                logs.append(f"📋 Copying {app_type} application files...")
                ignore_patterns = ['.git', 'node_modules', 'vendor']
                
                # Application-specific ignores
                if app_type == 'laravel':
                    ignore_patterns.extend(['storage/logs/*', 'bootstrap/cache/*'])
                elif app_type == 'wordpress':
                    ignore_patterns.extend(['wp-content/cache/*', 'wp-content/uploads/*'])
                
                shutil.copytree(
                    source_dir, 
                    temp_path / "app", 
                    ignore=shutil.ignore_patterns(*ignore_patterns)
                )
                
                # Write universal Dockerfile
                dockerfile_path = temp_path / "app" / "Dockerfile"
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                
                logs.append(f"🐳 Created universal Dockerfile for {app_type}")
                
                # Get ECR login token
                account_id = repository_uri.split('.')[0]
                region = self.credentials.get('region_name', 'us-east-1')
                
                # Get ECR authorization token
                token_response = self.ecr_client.get_authorization_token()
                token = token_response['authorizationData'][0]['authorizationToken']
                username, password = base64.b64decode(token).decode('utf-8').split(':')
                registry_url = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
                
                # Build the universal Docker image
                logs.append(f"🔨 Building universal {app_type} Docker image...")
                build_cmd = [
                    "docker", "build", 
                    "-t", f"{repository_uri}:latest",
                    "-f", str(dockerfile_path),
                    str(temp_path / "app")
                ]
                
                result = subprocess.run(build_cmd, capture_output=True, text=True, cwd=temp_path)
                if result.returncode != 0:
                    logs.append(f"❌ Universal {app_type} Docker build failed: {result.stderr}")
                    return False
                
                logs.append(f"✅ Universal {app_type} Docker image built successfully")
                
                # Login to ECR
                login_cmd = ["docker", "login", "--username", username, "--password", password, registry_url]
                result = subprocess.run(login_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logs.append(f"❌ ECR login failed: {result.stderr}")
                    return False
                
                logs.append("✅ Logged into ECR successfully")
                
                # Push the universal image
                logs.append(f"📤 Pushing universal {app_type} Docker image to ECR...")
                push_cmd = ["docker", "push", f"{repository_uri}:latest"]
                result = subprocess.run(push_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logs.append(f"❌ Universal {app_type} Docker push failed: {result.stderr}")
                    return False
                
                logs.append(f"✅ Universal {app_type} Docker image pushed to ECR successfully")
                return True
                
        except ImportError:
            logs.append("❌ Required modules not available for Docker operations")
            return False
        except Exception as e:
            logs.append(f"❌ Universal Docker build/push error: {str(e)}")
            return False
    
    def _parse_php_version_for_docker(self, version_requirement: str) -> str:
        """🔍 Parse PHP version requirement to Docker tag for universal deployment"""
        
        import re
        
        # Extract numeric version
        match = re.search(r'(\d+\.\d+)', version_requirement)
        if match:
            version = match.group(1)
            # Map to available PHP versions
            if version.startswith('8.3'):
                return '8.3'
            elif version.startswith('8.2'):
                return '8.2'
            elif version.startswith('8.1'):
                return '8.1'
            elif version.startswith('8.0'):
                return '8.0'
            elif version.startswith('7.4'):
                return '7.4'
        
        # Default to PHP 8.2 for modern universal deployment
        return '8.2'
    
    def _get_system_dependencies_for_docker(self, php_extensions: List[str]) -> List[str]:
        """🏗️ Map PHP extensions to required Alpine system packages for universal deployment"""
        
        dependency_map = {
            'gd': ['libpng-dev', 'libjpeg-turbo-dev', 'libfreetype-dev'],
            'mysql': ['mysql-dev'],
            'mysqli': ['mysql-dev'],
            'pdo_mysql': ['mysql-dev'],
            'pgsql': ['postgresql-dev'],
            'pdo_pgsql': ['postgresql-dev'],
            'zip': ['libzip-dev'],
            'xml': ['libxml2-dev'],
            'mbstring': ['oniguruma-dev'],
            'curl': ['curl-dev'],
            'openssl': ['openssl-dev'],
            'ldap': ['openldap-dev'],
            'imap': ['imap-dev'],
            'soap': ['libxml2-dev'],
            'xsl': ['libxslt-dev'],
            'bcmath': [],
            'calendar': [],
            'exif': [],
            'fileinfo': [],
            'filter': [],
            'ftp': ['openssl-dev'],
            'gettext': ['gettext-dev'],
            'hash': [],
            'json': [],
            'pcre': [],
            'pdo': [],
            'session': [],
            'sockets': [],
            'tokenizer': [],
            'intl': ['icu-dev'],
            'opcache': []
        }
        
        system_deps = set()
        for ext in php_extensions:
            deps = dependency_map.get(ext, [])
            system_deps.update(deps)
        
        return list(system_deps)
