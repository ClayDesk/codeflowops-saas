# Phase 2: Base API Plugin
# backend/stacks/api/base_api_plugin.py

"""
Base API plugin interface for Phase 2 implementation
Common interface for all API deployments (Node.js, Python, PHP, Java)
"""

import os
import boto3
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class DeploymentMethod(Enum):
    LAMBDA = "lambda"  # AWS Lambda for serverless
    ECS = "ecs"        # AWS ECS/Fargate for containers
    EC2 = "ec2"        # AWS EC2 for traditional deployment

class ApiFramework(Enum):
    # Node.js frameworks
    EXPRESS = "express"
    FASTIFY = "fastify"
    NESTJS = "nestjs"
    KOA = "koa"
    
    # Python frameworks
    FLASK = "flask"
    DJANGO = "django"
    FASTAPI = "fastapi"
    TORNADO = "tornado"
    
    # PHP frameworks
    LARAVEL = "laravel"
    SYMFONY = "symfony"
    SLIM = "slim"
    
    # Java frameworks
    SPRING_BOOT = "spring-boot"
    QUARKUS = "quarkus"

@dataclass
class ApiDeploymentConfig:
    """API deployment configuration"""
    app_name: str
    runtime: str
    framework: ApiFramework
    deployment_method: DeploymentMethod
    environment_variables: Dict[str, str] = None
    memory_size: int = 512  # MB for Lambda, or base memory for containers
    timeout: int = 30  # seconds for Lambda
    vpc_config: Dict[str, Any] = None
    database_connections: List[str] = None
    custom_domain: Optional[str] = None
    health_check_path: str = "/health"
    auto_scaling: Dict[str, Any] = None
    tags: Dict[str, str] = None

@dataclass
class ApiDeploymentResult:
    """API deployment result"""
    app_name: str
    deployment_method: DeploymentMethod
    endpoint_url: str
    function_arn: Optional[str] = None  # For Lambda
    service_arn: Optional[str] = None   # For ECS
    load_balancer_arn: Optional[str] = None  # For ECS/EC2
    health_check_url: str = None
    custom_domain_url: Optional[str] = None
    deployment_id: str = None
    status: str = "deploying"

class BaseApiPlugin(ABC):
    """
    Base API plugin interface
    ✅ Common interface for all API deployment methods
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.ecs_client = boto3.client('ecs', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.elbv2_client = boto3.client('elbv2', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.apigateway_client = boto3.client('apigatewayv2', region_name=region)
        self.ecr_client = boto3.client('ecr', region_name=region)
    
    @abstractmethod
    def detect_framework(self, repo_path: str) -> ApiFramework:
        """Detect API framework from repository"""
        pass
    
    @abstractmethod
    def prepare_deployment_package(self, repo_path: str, config: ApiDeploymentConfig) -> str:
        """Prepare deployment package (ZIP for Lambda, Docker for containers)"""
        pass
    
    @abstractmethod
    def deploy_lambda(self, package_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """Deploy API as AWS Lambda function"""
        pass
    
    @abstractmethod
    def deploy_ecs(self, repo_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """Deploy API as ECS/Fargate service"""
        pass
    
    def deploy_api(self, repo_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """
        Deploy API using specified deployment method
        ✅ Main deployment orchestration method
        """
        
        logger.info(f"🚀 Deploying API: {config.app_name} using {config.deployment_method.value}")
        
        try:
            if config.deployment_method == DeploymentMethod.LAMBDA:
                package_path = self.prepare_deployment_package(repo_path, config)
                result = self.deploy_lambda(package_path, config)
                
            elif config.deployment_method == DeploymentMethod.ECS:
                result = self.deploy_ecs(repo_path, config)
                
            else:
                raise NotImplementedError(f"Deployment method {config.deployment_method.value} not implemented")
            
            # Setup API Gateway if needed
            if config.custom_domain or config.deployment_method == DeploymentMethod.LAMBDA:
                result = self._setup_api_gateway(result, config)
            
            # Setup health monitoring
            self._setup_health_monitoring(result, config)
            
            logger.info(f"✅ API deployed successfully: {result.endpoint_url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to deploy API: {e}")
            raise
    
    def _setup_api_gateway(self, deployment_result: ApiDeploymentResult, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """
        Setup API Gateway for Lambda or custom domain routing
        ✅ Unified API management
        """
        
        try:
            api_name = f"{config.app_name}-api"
            
            # Create HTTP API (API Gateway v2)
            api_response = self.apigateway_client.create_api(
                Name=api_name,
                ProtocolType='HTTP',
                Description=f'API Gateway for {config.app_name}',
                Tags={
                    'Project': 'CodeFlowOps',
                    'AppName': config.app_name,
                    'ManagedBy': 'ApiPlugin'
                }
            )
            
            api_id = api_response['ApiId']
            
            if deployment_result.deployment_method == DeploymentMethod.LAMBDA:
                # Lambda integration
                integration_response = self.apigateway_client.create_integration(
                    ApiId=api_id,
                    IntegrationType='AWS_PROXY',
                    IntegrationUri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{deployment_result.function_arn}/invocations",
                    PayloadFormatVersion='2.0'
                )
                
                integration_id = integration_response['IntegrationId']
                
                # Create routes
                self.apigateway_client.create_route(
                    ApiId=api_id,
                    RouteKey='ANY /{proxy+}',
                    Target=f'integrations/{integration_id}'
                )
                
                self.apigateway_client.create_route(
                    ApiId=api_id,
                    RouteKey='ANY /',
                    Target=f'integrations/{integration_id}'
                )
                
                # Grant API Gateway permission to invoke Lambda
                try:
                    self.lambda_client.add_permission(
                        FunctionName=deployment_result.function_arn,
                        StatementId='apigateway-invoke',
                        Action='lambda:InvokeFunction',
                        Principal='apigateway.amazonaws.com',
                        SourceArn=f'arn:aws:execute-api:{self.region}:*:{api_id}/*/*'
                    )
                except Exception as e:
                    logger.warning(f"Permission may already exist: {e}")
            
            # Create stage
            stage_response = self.apigateway_client.create_stage(
                ApiId=api_id,
                StageName='prod',
                AutoDeploy=True,
                Tags={
                    'Environment': 'production',
                    'Project': 'CodeFlowOps'
                }
            )
            
            # Update endpoint URL
            api_endpoint = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod"
            deployment_result.endpoint_url = api_endpoint
            deployment_result.health_check_url = f"{api_endpoint}{config.health_check_path}"
            
            logger.info(f"✅ API Gateway setup complete: {api_endpoint}")
            return deployment_result
            
        except Exception as e:
            logger.error(f"Failed to setup API Gateway: {e}")
            return deployment_result  # Return original result if API Gateway setup fails
    
    def _setup_health_monitoring(self, deployment_result: ApiDeploymentResult, config: ApiDeploymentConfig):
        """
        Setup CloudWatch alarms for API health monitoring
        ✅ Production monitoring setup
        """
        
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=self.region)
            
            alarm_name = f"{config.app_name}-health-alarm"
            
            if deployment_result.deployment_method == DeploymentMethod.LAMBDA:
                # Lambda-specific metrics
                cloudwatch.put_metric_alarm(
                    AlarmName=alarm_name,
                    ComparisonOperator='GreaterThanThreshold',
                    EvaluationPeriods=2,
                    MetricName='Errors',
                    Namespace='AWS/Lambda',
                    Period=60,
                    Statistic='Sum',
                    Threshold=5.0,  # More than 5 errors per minute
                    ActionsEnabled=True,
                    AlarmDescription=f'API errors alarm for {config.app_name}',
                    Dimensions=[
                        {
                            'Name': 'FunctionName',
                            'Value': config.app_name
                        }
                    ],
                    TreatMissingData='notBreaching'
                )
                
            logger.info(f"✅ Health monitoring setup complete for {config.app_name}")
            
        except Exception as e:
            logger.warning(f"Failed to setup health monitoring: {e}")
    
    def create_execution_role(self, app_name: str, additional_policies: List[str] = None) -> str:
        """
        Create IAM execution role for API deployment
        ✅ Least-privilege execution role
        """
        
        role_name = f"{app_name}-execution-role"
        
        # Trust policy
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["lambda.amazonaws.com", "ecs-tasks.amazonaws.com"]
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Create role
            role_response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Tags=[
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'AppName', 'Value': app_name},
                    {'Key': 'ManagedBy', 'Value': 'ApiPlugin'}
                ]
            )
            
            role_arn = role_response['Role']['Arn']
            
            # Attach basic execution policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Attach VPC execution policy if VPC is configured
            if additional_policies and 'vpc' in additional_policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole'
                )
            
            # Attach additional policies
            if additional_policies:
                for policy in additional_policies:
                    if policy.startswith('arn:aws:iam::'):
                        self.iam_client.attach_role_policy(
                            RoleName=role_name,
                            PolicyArn=policy
                        )
            
            logger.info(f"✅ Created execution role: {role_arn}")
            return role_arn
            
        except Exception as e:
            if 'EntityAlreadyExists' in str(e):
                # Role already exists, get ARN
                role_response = self.iam_client.get_role(RoleName=role_name)
                return role_response['Role']['Arn']
            else:
                logger.error(f"Failed to create execution role: {e}")
                raise
    
    def create_ecr_repository(self, app_name: str) -> str:
        """
        Create ECR repository for container images
        ✅ Container registry for ECS deployments
        """
        
        repository_name = f"codeflowops/{app_name}"
        
        try:
            response = self.ecr_client.create_repository(
                repositoryName=repository_name,
                imageScanningConfiguration={'scanOnPush': True},
                encryptionConfiguration={'encryptionType': 'AES256'},
                tags=[
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'AppName', 'Value': app_name},
                    {'Key': 'ManagedBy', 'Value': 'ApiPlugin'}
                ]
            )
            
            repository_uri = response['repository']['repositoryUri']
            logger.info(f"✅ Created ECR repository: {repository_uri}")
            return repository_uri
            
        except Exception as e:
            if 'RepositoryAlreadyExistsException' in str(e):
                # Repository already exists, get URI
                response = self.ecr_client.describe_repositories(
                    repositoryNames=[repository_name]
                )
                return response['repositories'][0]['repositoryUri']
            else:
                logger.error(f"Failed to create ECR repository: {e}")
                raise
    
    def build_and_push_docker_image(self, repo_path: str, repository_uri: str, tag: str = 'latest') -> str:
        """
        Build and push Docker image to ECR
        ✅ Container image management
        """
        
        import subprocess
        import base64
        
        try:
            # Get ECR login token
            token_response = self.ecr_client.get_authorization_token()
            token = token_response['authorizationData'][0]['authorizationToken']
            endpoint = token_response['authorizationData'][0]['proxyEndpoint']
            
            # Decode token
            username, password = base64.b64decode(token).decode().split(':')
            
            # Docker login
            subprocess.run([
                'docker', 'login', '--username', username, '--password', password, endpoint
            ], check=True, capture_output=True)
            
            # Build image
            image_tag = f"{repository_uri}:{tag}"
            subprocess.run([
                'docker', 'build', '-t', image_tag, repo_path
            ], check=True, capture_output=True)
            
            # Push image
            subprocess.run([
                'docker', 'push', image_tag
            ], check=True, capture_output=True)
            
            logger.info(f"✅ Built and pushed Docker image: {image_tag}")
            return image_tag
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker command failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to build and push Docker image: {e}")
            raise
    
    def cleanup_deployment(self, app_name: str, deployment_method: DeploymentMethod) -> bool:
        """
        Clean up deployment resources
        ✅ Resource cleanup for cost management
        """
        
        try:
            logger.info(f"🧹 Cleaning up deployment: {app_name}")
            
            if deployment_method == DeploymentMethod.LAMBDA:
                # Delete Lambda function
                try:
                    self.lambda_client.delete_function(FunctionName=app_name)
                    logger.info(f"✅ Deleted Lambda function: {app_name}")
                except:
                    pass
            
            elif deployment_method == DeploymentMethod.ECS:
                # Delete ECS service and task definition
                try:
                    cluster_name = f"{app_name}-cluster"
                    service_name = f"{app_name}-service"
                    
                    # Scale service to 0
                    self.ecs_client.update_service(
                        cluster=cluster_name,
                        service=service_name,
                        desiredCount=0
                    )
                    
                    # Delete service
                    self.ecs_client.delete_service(
                        cluster=cluster_name,
                        service=service_name
                    )
                    
                    # Delete cluster
                    self.ecs_client.delete_cluster(cluster=cluster_name)
                    
                    logger.info(f"✅ Deleted ECS resources: {app_name}")
                except:
                    pass
            
            # Delete API Gateway (if exists)
            try:
                apis = self.apigateway_client.get_apis()
                for api in apis['Items']:
                    if api['Name'] == f"{app_name}-api":
                        self.apigateway_client.delete_api(ApiId=api['ApiId'])
                        logger.info(f"✅ Deleted API Gateway: {app_name}-api")
                        break
            except:
                pass
            
            # Delete IAM role
            try:
                role_name = f"{app_name}-execution-role"
                
                # Detach policies first
                attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
                for policy in attached_policies['AttachedPolicies']:
                    self.iam_client.detach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy['PolicyArn']
                    )
                
                # Delete role
                self.iam_client.delete_role(RoleName=role_name)
                logger.info(f"✅ Deleted IAM role: {role_name}")
            except:
                pass
            
            logger.info(f"✅ Cleanup completed for {app_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup deployment: {e}")
            return False
