# Phase 2: PHP API Plugin
# backend/stacks/api/php_api_plugin.py

"""
PHP API plugin for Laravel, Symfony, and Slim deployments
Production-ready PHP API deployment with ECS support
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base_api_plugin import (
    BaseApiPlugin, ApiFramework, DeploymentMethod, 
    ApiDeploymentConfig, ApiDeploymentResult
)

logger = logging.getLogger(__name__)

class PHPApiPlugin(BaseApiPlugin):
    """
    PHP API plugin with framework-specific support
    ✅ Production-ready PHP deployment for ECS (Lambda not supported for PHP)
    """
    
    def __init__(self, region: str = 'us-east-1'):
        super().__init__(region)
        
        self.framework_patterns = {
            ApiFramework.LARAVEL: ['laravel/framework'],
            ApiFramework.SYMFONY: ['symfony/symfony'],
            ApiFramework.SLIM: ['slim/slim']
        }
    
    def detect_framework(self, repo_path: str) -> ApiFramework:
        """Detect PHP framework from composer.json"""
        
        composer_path = Path(repo_path) / 'composer.json'
        
        if composer_path.exists():
            try:
                import json
                with open(composer_path, 'r') as f:
                    composer_data = json.load(f)
                
                dependencies = {}
                dependencies.update(composer_data.get('require', {}))
                
                for framework, patterns in self.framework_patterns.items():
                    for pattern in patterns:
                        if pattern in dependencies:
                            logger.info(f"🔍 Detected PHP framework: {framework.value}")
                            return framework
            except:
                pass
        
        logger.info("🔍 No specific framework detected, defaulting to Laravel")
        return ApiFramework.LARAVEL
    
    def prepare_deployment_package(self, repo_path: str, config: ApiDeploymentConfig) -> str:
        """PHP uses Docker containers, no separate package needed"""
        return repo_path
    
    def deploy_lambda(self, package_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """Lambda not supported for PHP"""
        raise NotImplementedError("Lambda deployment not supported for PHP. Use ECS instead.")
    
    def deploy_ecs(self, repo_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """Deploy PHP API as ECS service with REAL AWS resources"""
        
        logger.info(f"🐳 Deploying PHP API to ECS: {config.app_name}")
        
        try:
            # Import the real PHP deployer
            import sys
            sys.path.append(str(Path(__file__).parent.parent))
            from php.deployer import PHPDeployer
            from php.provisioner import PHPProvisioner
            from core.models import StackPlan, BuildResult, ProvisionResult
            
            # Create a proper stack plan
            plan = StackPlan(
                stack_key="php_api",
                build_cmds=["composer install --no-dev --optimize-autoloader"],
                output_dir=Path(repo_path),
                config={
                    'framework': config.framework.value,
                    'app_name': config.app_name,
                    'repository_url': getattr(config, 'repository_url', ''),
                    'deployment_type': 'container'
                }
            )
            
            # Create AWS credentials dict
            aws_credentials = {
                'aws_access_key_id': getattr(config, 'aws_access_key', ''),
                'aws_secret_access_key': getattr(config, 'aws_secret_key', ''),
                'aws_region': getattr(config, 'aws_region', self.region)
            }
            
            # Use the real PHP provisioner
            provisioner = PHPProvisioner()
            provision_result = provisioner.provision(plan, None, aws_credentials)
            
            if not provision_result.success:
                return ApiDeploymentResult(
                    app_name=config.app_name,
                    deployment_method=DeploymentMethod.ECS,
                    endpoint_url="",
                    status="failed",
                    error=provision_result.error_message
                )
            
            # Use the real PHP deployer
            deployer = PHPDeployer()
            build_result = BuildResult(
                success=True,
                artifact_dir=Path(repo_path),
                build_time_seconds=0.0
            )
            
            deploy_result = deployer.deploy(plan, build_result, provision_result, aws_credentials)
            
            if deploy_result.success:
                return ApiDeploymentResult(
                    app_name=config.app_name,
                    deployment_method=DeploymentMethod.ECS,
                    endpoint_url=deploy_result.live_url,
                    status="deployed",
                    details=deploy_result.details
                )
            else:
                return ApiDeploymentResult(
                    app_name=config.app_name,
                    deployment_method=DeploymentMethod.ECS,
                    endpoint_url="",
                    status="failed",
                    error=deploy_result.error_message
                )
                
        except Exception as e:
            logger.error(f"PHP ECS deployment failed: {e}")
            return ApiDeploymentResult(
                app_name=config.app_name,
                deployment_method=DeploymentMethod.ECS,
                endpoint_url="",
                status="failed",
                error=str(e)
            )
    
    def _ensure_dockerfile(self, repo_path: str, config: ApiDeploymentConfig):
        """Create Dockerfile for PHP application"""
        
        dockerfile_path = Path(repo_path) / 'Dockerfile'
        
        if dockerfile_path.exists():
            return
        
        if config.framework == ApiFramework.LARAVEL:
            dockerfile_content = """
FROM php:8.2-fpm-alpine

RUN apk add --no-cache nginx
COPY . /var/www/html
WORKDIR /var/www/html

RUN composer install --optimize-autoloader --no-dev
EXPOSE 80
CMD ["php-fpm"]
"""
        else:
            dockerfile_content = """
FROM php:8.2-apache

COPY . /var/www/html/
WORKDIR /var/www/html

RUN composer install --optimize-autoloader --no-dev
EXPOSE 80
"""
        
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content.strip())
