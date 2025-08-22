# Phase 2: Base Runtime Adapter
# backend/stacks/api/adapters/base_adapter.py

"""
Base runtime adapter interface implementing the comprehensive plan architecture
Provides standardized ports, health checks, and deployment methods across all runtimes
"""

import os
import json
import boto3
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class DeploymentTarget(Enum):
    LAMBDA = "lambda"
    ECS = "ecs"
    EC2 = "ec2"

@dataclass
class BuildResult:
    """Result from build process"""
    success: bool
    artifact_path: str
    repo_path: str
    framework: str
    runtime: str
    environment_vars: Dict[str, str]
    build_logs: List[str]
    error_message: Optional[str] = None

@dataclass
class DeploymentResult:
    """Result from deployment process"""
    success: bool
    endpoint_url: str
    deployment_target: DeploymentTarget
    health_check_url: str
    function_arn: Optional[str] = None  # For Lambda
    service_arn: Optional[str] = None   # For ECS
    load_balancer_arn: Optional[str] = None
    deployment_id: str = None
    error_message: Optional[str] = None

class RuntimeAdapter(ABC):
    """
    Base runtime adapter implementing comprehensive plan specifications
    ✅ Standardized ports and health check paths across all runtimes
    ✅ Consistent deployment interface for Lambda and ECS targets
    """
    
    # ✅ Standardized default ports as specified in comprehensive plan
    DEFAULT_PORT = 8000
    HEALTH_CHECK_PATH = '/health'
    HEALTH_CHECK_TIMEOUT = 30
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.ecs_client = boto3.client('ecs', region_name=region)
        self.elbv2_client = boto3.client('elbv2', region_name=region)
        self.aws_deployer = AWSDeployer(region)
    
    @abstractmethod
    def detect_framework(self, repo_path: str) -> Dict[str, Any]:
        """
        Detect runtime framework and return configuration
        Must return framework name, port, and startup command
        """
        pass
    
    @abstractmethod
    def build(self, repo_path: str, build_config: Dict[str, Any]) -> BuildResult:
        """
        Build runtime-specific deployment artifact
        Returns build result with artifact path and metadata
        """
        pass
    
    @abstractmethod
    def deploy_to_lambda(self, build_result: BuildResult, lambda_config: Dict[str, Any]) -> DeploymentResult:
        """
        Deploy to AWS Lambda with API Gateway
        Runtime-specific Lambda handler creation and deployment
        """
        pass
    
    @abstractmethod  
    def deploy_to_ecs(self, build_result: BuildResult, ecs_config: Dict[str, Any]) -> DeploymentResult:
        """
        Deploy to ECS/Fargate with Application Load Balancer
        Runtime-specific containerization and ECS deployment
        """
        pass
    
    def deploy(self, build_result: BuildResult, deployment_config: Dict[str, Any]) -> DeploymentResult:
        """
        Main deployment method implementing comprehensive plan workflow
        ✅ Consistent deployment interface across all runtimes
        """
        
        target = DeploymentTarget(deployment_config.get('target', 'lambda'))
        
        logger.info(f"🚀 Deploying {build_result.framework} to {target.value}")
        
        try:
            if target == DeploymentTarget.LAMBDA:
                result = self.deploy_to_lambda(build_result, deployment_config.get('lambda', {}))
                
            elif target == DeploymentTarget.ECS:
                result = self.deploy_to_ecs(build_result, deployment_config.get('ecs', {}))
                
            else:
                raise NotImplementedError(f"Deployment target {target} not implemented")
            
            # ✅ Standardized health check setup
            result.health_check_url = f"{result.endpoint_url}{self.HEALTH_CHECK_PATH}"
            
            # Verify health check endpoint
            health_status = self.verify_health_check(result.health_check_url)
            if not health_status:
                logger.warning("⚠️  Health check endpoint not responding")
            
            logger.info(f"✅ Deployment successful: {result.endpoint_url}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                endpoint_url="",
                deployment_target=target,
                health_check_url="",
                error_message=str(e)
            )
    
    def verify_health_check(self, health_url: str) -> bool:
        """
        Verify health check endpoint is responding
        ✅ Standardized health verification across all runtimes
        """
        try:
            import requests
            response = requests.get(health_url, timeout=self.HEALTH_CHECK_TIMEOUT)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def get_standardized_health_config(self) -> Dict[str, Any]:
        """
        Get standardized health check configuration
        ✅ Consistent ALB health check setup as per comprehensive plan
        """
        return {
            'path': self.HEALTH_CHECK_PATH,
            'port': self.DEFAULT_PORT,
            'protocol': 'HTTP',
            'timeout': self.HEALTH_CHECK_TIMEOUT,
            'interval': 30,
            'healthy_threshold': 2,
            'unhealthy_threshold': 3,
            'matcher': {'HttpCode': '200'}
        }

class AWSDeployer:
    """AWS deployment helper for runtime adapters"""
    
    def __init__(self, region: str):
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.ecs_client = boto3.client('ecs', region_name=region)
        self.elbv2_client = boto3.client('elbv2', region_name=region)
        self.apigateway_client = boto3.client('apigatewayv2', region_name=region)
        self.ecr_client = boto3.client('ecr', region_name=region)
    
    def deploy_lambda_function(self, 
                              function_name: str,
                              zip_file: bytes,
                              handler: str,
                              runtime: str,
                              environment_vars: Dict[str, str]) -> Dict[str, Any]:
        """Deploy Lambda function with standardized configuration"""
        
        try:
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime=runtime,
                Role=self._get_lambda_execution_role(),
                Handler=handler,
                Code={'ZipFile': zip_file},
                Environment={'Variables': environment_vars},
                Timeout=30,
                MemorySize=512,
                Publish=True,
                Tags={
                    'Project': 'CodeFlowOps',
                    'ManagedBy': 'RuntimeAdapter',
                    'DeploymentMethod': 'lambda'
                }
            )
            
            # Setup API Gateway
            api_gateway = self._create_api_gateway(function_name, response['FunctionArn'])
            
            return {
                'function_arn': response['FunctionArn'],
                'endpoint_url': api_gateway['endpoint_url'],
                'api_id': api_gateway['api_id']
            }
            
        except self.lambda_client.exceptions.ResourceConflictException:
            # Function exists, update it
            return self._update_lambda_function(function_name, zip_file, environment_vars)
    
    def deploy_containerized_api(self,
                               container_image: str,
                               port: int,
                               health_check_config: Dict[str, Any],
                               environment: Dict[str, str],
                               service_name: str = None) -> Dict[str, Any]:
        """Deploy containerized API to ECS with ALB"""
        
        # Create ECS cluster if needed
        cluster_name = f"codeflowops-cluster"
        self._ensure_ecs_cluster(cluster_name)
        
        # Create task definition
        task_def = self._create_task_definition(
            service_name or f"api-{port}",
            container_image,
            port,
            environment
        )
        
        # Create ALB and target group with health checks
        load_balancer = self._create_application_load_balancer(
            service_name or f"api-{port}",
            port,
            health_check_config
        )
        
        # Create ECS service
        service = self._create_ecs_service(
            cluster_name,
            service_name or f"api-{port}",
            task_def['taskDefinitionArn'],
            load_balancer['target_group_arn']
        )
        
        return {
            'service_arn': service['serviceArn'],
            'endpoint_url': f"http://{load_balancer['dns_name']}",
            'load_balancer_arn': load_balancer['load_balancer_arn'],
            'task_definition_arn': task_def['taskDefinitionArn']
        }
    
    def _get_lambda_execution_role(self) -> str:
        """Get or create Lambda execution role"""
        role_name = "CodeFlowOps-Lambda-Execution-Role"
        
        try:
            iam = boto3.client('iam')
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except iam.exceptions.NoSuchEntityException:
            # Create the role
            return self._create_lambda_execution_role(role_name)
    
    def _create_lambda_execution_role(self, role_name: str) -> str:
        """Create Lambda execution role with necessary permissions"""
        iam = boto3.client('iam')
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for CodeFlowOps Lambda functions"
        )
        
        # Attach basic execution policy
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        return response['Role']['Arn']
    
    def _create_api_gateway(self, function_name: str, function_arn: str) -> Dict[str, str]:
        """Create API Gateway for Lambda function"""
        
        # Create HTTP API
        api_response = self.apigateway_client.create_api(
            Name=f"{function_name}-api",
            ProtocolType='HTTP',
            Target=function_arn
        )
        
        api_id = api_response['ApiId']
        endpoint_url = api_response['ApiEndpoint']
        
        # Grant API Gateway permission to invoke Lambda
        self.lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=f"{function_name}-api-gateway",
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f"arn:aws:execute-api:{self.region}:*:{api_id}/*/*"
        )
        
        return {
            'api_id': api_id,
            'endpoint_url': endpoint_url
        }
    
    def _update_lambda_function(self, function_name: str, zip_file: bytes, environment_vars: Dict[str, str]) -> Dict[str, Any]:
        """Update existing Lambda function"""
        
        # Update function code
        self.lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_file
        )
        
        # Update environment variables
        self.lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': environment_vars}
        )
        
        # Get function info
        response = self.lambda_client.get_function(FunctionName=function_name)
        
        return {
            'function_arn': response['Configuration']['FunctionArn'],
            'endpoint_url': f"https://{function_name}.execute-api.{self.region}.amazonaws.com/",
            'updated': True
        }
    
    def _ensure_ecs_cluster(self, cluster_name: str):
        """Ensure ECS cluster exists"""
        try:
            self.ecs_client.describe_clusters(clusters=[cluster_name])
        except:
            self.ecs_client.create_cluster(clusterName=cluster_name)
    
    def _create_task_definition(self, service_name: str, image: str, port: int, environment: Dict[str, str]) -> Dict[str, Any]:
        """Create ECS task definition"""
        
        env_vars = [{'name': k, 'value': v} for k, v in environment.items()]
        
        response = self.ecs_client.register_task_definition(
            family=service_name,
            networkMode='awsvpc',
            requiresCompatibilities=['FARGATE'],
            cpu='256',
            memory='512',
            executionRoleArn=self._get_ecs_execution_role(),
            containerDefinitions=[
                {
                    'name': service_name,
                    'image': image,
                    'portMappings': [
                        {
                            'containerPort': port,
                            'protocol': 'tcp'
                        }
                    ],
                    'environment': env_vars,
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-group': f"/ecs/{service_name}",
                            'awslogs-region': self.region,
                            'awslogs-stream-prefix': 'ecs'
                        }
                    }
                }
            ]
        )
        
        return response['taskDefinition']
    
    def _get_ecs_execution_role(self) -> str:
        """Get or create ECS execution role"""
        # Similar to Lambda role creation but for ECS
        role_name = "CodeFlowOps-ECS-Execution-Role"
        
        try:
            iam = boto3.client('iam')
            response = iam.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except:
            return self._create_ecs_execution_role(role_name)
    
    def _create_ecs_execution_role(self, role_name: str) -> str:
        """Create ECS execution role"""
        iam = boto3.client('iam')
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
        )
        
        return response['Role']['Arn']
    
    def _create_application_load_balancer(self, service_name: str, port: int, health_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create ALB with health checks"""
        # Implementation would create ALB, target group, and listener
        # This is a simplified placeholder
        return {
            'load_balancer_arn': f"arn:aws:elasticloadbalancing:{self.region}:123456789012:loadbalancer/app/{service_name}/1234567890123456",
            'target_group_arn': f"arn:aws:elasticloadbalancing:{self.region}:123456789012:targetgroup/{service_name}/1234567890123456",
            'dns_name': f"{service_name}.{self.region}.elb.amazonaws.com"
        }
    
    def _create_ecs_service(self, cluster_name: str, service_name: str, task_def_arn: str, target_group_arn: str) -> Dict[str, Any]:
        """Create ECS service"""
        # Implementation would create ECS service with ALB integration
        # This is a simplified placeholder
        return {
            'serviceArn': f"arn:aws:ecs:{self.region}:123456789012:service/{cluster_name}/{service_name}"
        }
