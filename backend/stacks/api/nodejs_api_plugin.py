# Phase 2: Node.js API Plugin
# backend/stacks/api/nodejs_api_plugin.py

"""
Node.js API plugin for Express, Fastify, NestJS, and Koa deployments
Production-ready Node.js API deployment with Lambda and ECS support
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

from .base_api_plugin import (
    BaseApiPlugin, ApiFramework, DeploymentMethod, 
    ApiDeploymentConfig, ApiDeploymentResult
)

logger = logging.getLogger(__name__)

class NodeJSApiPlugin(BaseApiPlugin):
    """
    Node.js API plugin with framework-specific support
    ✅ Production-ready Node.js deployment for Lambda and ECS
    """
    
    def __init__(self, region: str = 'us-east-1'):
        super().__init__(region)
        self.runtime = 'nodejs18.x'  # Latest supported Node.js runtime
        
        # Framework detection patterns
        self.framework_patterns = {
            ApiFramework.EXPRESS: ['express'],
            ApiFramework.FASTIFY: ['fastify'],
            ApiFramework.NESTJS: ['@nestjs/core', '@nestjs/common'],
            ApiFramework.KOA: ['koa']
        }
    
    def detect_framework(self, repo_path: str) -> ApiFramework:
        """
        Detect Node.js framework from package.json
        ✅ Automatic framework detection
        """
        
        package_json_path = Path(repo_path) / 'package.json'
        
        if not package_json_path.exists():
            logger.warning("package.json not found, defaulting to Express")
            return ApiFramework.EXPRESS
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = {}
            dependencies.update(package_data.get('dependencies', {}))
            dependencies.update(package_data.get('devDependencies', {}))
            
            # Check for framework-specific dependencies
            for framework, patterns in self.framework_patterns.items():
                for pattern in patterns:
                    if pattern in dependencies:
                        logger.info(f"🔍 Detected Node.js framework: {framework.value}")
                        return framework
            
            # Default to Express if no specific framework detected
            logger.info("🔍 No specific framework detected, defaulting to Express")
            return ApiFramework.EXPRESS
            
        except Exception as e:
            logger.error(f"Failed to detect Node.js framework: {e}")
            return ApiFramework.EXPRESS
    
    def prepare_deployment_package(self, repo_path: str, config: ApiDeploymentConfig) -> str:
        """
        Prepare Node.js deployment package for Lambda
        ✅ Optimized Lambda deployment package
        """
        
        logger.info(f"📦 Preparing Node.js deployment package for {config.app_name}")
        
        # Create temporary directory for package
        temp_dir = tempfile.mkdtemp(prefix='nodejs_api_')
        package_dir = Path(temp_dir)
        
        try:
            # Copy source code
            self._copy_source_files(repo_path, package_dir)
            
            # Install production dependencies
            self._install_dependencies(package_dir)
            
            # Create Lambda handler if needed
            self._create_lambda_handler(package_dir, config)
            
            # Create deployment ZIP
            zip_path = str(package_dir.parent / f"{config.app_name}.zip")
            self._create_zip_package(package_dir, zip_path)
            
            logger.info(f"✅ Node.js deployment package created: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Failed to prepare deployment package: {e}")
            # Cleanup on failure
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    def _copy_source_files(self, repo_path: str, package_dir: Path):
        """Copy necessary source files excluding node_modules and other artifacts"""
        
        source_path = Path(repo_path)
        
        # Files and directories to exclude
        exclude_patterns = {
            'node_modules', '.git', '.gitignore', '.env', 'tests', 'test', 
            '__tests__', '.nyc_output', 'coverage', '.coverage', 'dist',
            '.next', '.nuxt', 'build', 'public', 'static'
        }
        
        for item in source_path.iterdir():
            if item.name not in exclude_patterns:
                if item.is_file():
                    shutil.copy2(item, package_dir)
                elif item.is_dir():
                    shutil.copytree(item, package_dir / item.name)
        
        logger.info("✅ Source files copied")
    
    def _install_dependencies(self, package_dir: Path):
        """Install production Node.js dependencies"""
        
        package_json_path = package_dir / 'package.json'
        
        if not package_json_path.exists():
            logger.warning("No package.json found, skipping dependency installation")
            return
        
        try:
            # Use npm ci for faster, reliable installation
            subprocess.run([
                'npm', 'ci', '--production', '--silent'
            ], cwd=package_dir, check=True, capture_output=True)
            
            logger.info("✅ Dependencies installed")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"npm ci failed, trying npm install: {e}")
            try:
                subprocess.run([
                    'npm', 'install', '--production', '--silent'
                ], cwd=package_dir, check=True, capture_output=True)
                
                logger.info("✅ Dependencies installed with npm install")
                
            except subprocess.CalledProcessError as e2:
                logger.error(f"Failed to install dependencies: {e2}")
                raise
    
    def _create_lambda_handler(self, package_dir: Path, config: ApiDeploymentConfig):
        """Create Lambda handler based on detected framework"""
        
        handler_content = ""
        
        if config.framework == ApiFramework.EXPRESS:
            handler_content = """
const serverlessExpress = require('@vendia/serverless-express');
const app = require('./app'); // Assumes main app file is app.js

const serverlessExpressInstance = serverlessExpress({ app });

module.exports.handler = async (event, context) => {
    return serverlessExpressInstance(event, context);
};
"""
        
        elif config.framework == ApiFramework.FASTIFY:
            handler_content = """
const awsLambdaFastify = require('@fastify/aws-lambda');
const app = require('./app'); // Assumes main app file is app.js

const proxy = awsLambdaFastify(app);

module.exports.handler = proxy;
"""
        
        elif config.framework == ApiFramework.NESTJS:
            handler_content = """
const { NestFactory } = require('@nestjs/core');
const { ExpressAdapter } = require('@nestjs/platform-express');
const serverlessExpress = require('@vendia/serverless-express');
const { AppModule } = require('./src/app.module');

let server;

async function bootstrap() {
    const express = require('express');
    const expressApp = express();
    
    const app = await NestFactory.create(AppModule, new ExpressAdapter(expressApp));
    app.enableCors();
    await app.init();
    
    return serverlessExpress({ app: expressApp });
}

module.exports.handler = async (event, context) => {
    server = server ?? await bootstrap();
    return server(event, context);
};
"""
        
        elif config.framework == ApiFramework.KOA:
            handler_content = """
const serverlessKoa = require('serverless-koa');
const app = require('./app'); // Assumes main app file is app.js

module.exports.handler = serverlessKoa(app);
"""
        
        # Write handler file
        handler_path = package_dir / 'lambda_handler.js'
        with open(handler_path, 'w') as f:
            f.write(handler_content.strip())
        
        # Update package.json to include required serverless dependencies
        self._add_serverless_dependencies(package_dir, config.framework)
        
        logger.info(f"✅ Lambda handler created for {config.framework.value}")
    
    def _add_serverless_dependencies(self, package_dir: Path, framework: ApiFramework):
        """Add framework-specific serverless dependencies to package.json"""
        
        package_json_path = package_dir / 'package.json'
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.setdefault('dependencies', {})
            
            # Add serverless dependencies based on framework
            if framework == ApiFramework.EXPRESS:
                dependencies['@vendia/serverless-express'] = '^4.10.4'
            elif framework == ApiFramework.FASTIFY:
                dependencies['@fastify/aws-lambda'] = '^4.0.2'
            elif framework == ApiFramework.NESTJS:
                dependencies['@vendia/serverless-express'] = '^4.10.4'
                dependencies['@nestjs/platform-express'] = '^10.0.0'
            elif framework == ApiFramework.KOA:
                dependencies['serverless-koa'] = '^1.0.0'
            
            # Write updated package.json
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            logger.info("✅ Serverless dependencies added")
            
        except Exception as e:
            logger.warning(f"Failed to add serverless dependencies: {e}")
    
    def _create_zip_package(self, package_dir: Path, zip_path: str):
        """Create ZIP package for Lambda deployment"""
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arc_name)
        
        # Check ZIP size (Lambda limit is 50MB for direct upload)
        zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
        if zip_size > 50:
            logger.warning(f"Package size {zip_size:.1f}MB exceeds Lambda direct upload limit")
        
        logger.info(f"✅ ZIP package created: {zip_size:.1f}MB")
    
    def deploy_lambda(self, package_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """
        Deploy Node.js API as AWS Lambda function
        ✅ Serverless Node.js API deployment
        """
        
        logger.info(f"🚀 Deploying Node.js API to Lambda: {config.app_name}")
        
        try:
            # Create execution role
            role_arn = self.create_execution_role(
                config.app_name,
                additional_policies=['vpc'] if config.vpc_config else []
            )
            
            # Prepare function configuration
            function_config = {
                'FunctionName': config.app_name,
                'Runtime': self.runtime,
                'Role': role_arn,
                'Handler': 'lambda_handler.handler',
                'Timeout': config.timeout,
                'MemorySize': config.memory_size,
                'Environment': {
                    'Variables': config.environment_variables or {}
                },
                'Tags': {
                    'Project': 'CodeFlowOps',
                    'Framework': config.framework.value,
                    'Runtime': 'nodejs',
                    **(config.tags or {})
                }
            }
            
            # Add VPC configuration if provided
            if config.vpc_config:
                function_config['VpcConfig'] = {
                    'SubnetIds': config.vpc_config['subnet_ids'],
                    'SecurityGroupIds': config.vpc_config['security_group_ids']
                }
            
            # Read deployment package
            with open(package_path, 'rb') as f:
                zip_content = f.read()
            
            function_config['Code'] = {'ZipFile': zip_content}
            
            # Create or update Lambda function
            try:
                response = self.lambda_client.create_function(**function_config)
                logger.info(f"✅ Lambda function created: {config.app_name}")
            except Exception as e:
                if 'ResourceConflictException' in str(e):
                    # Function exists, update it
                    self.lambda_client.update_function_code(
                        FunctionName=config.app_name,
                        ZipFile=zip_content
                    )
                    
                    # Update configuration
                    config_update = function_config.copy()
                    config_update.pop('Code')
                    config_update.pop('FunctionName')
                    
                    response = self.lambda_client.update_function_configuration(
                        FunctionName=config.app_name,
                        **config_update
                    )
                    logger.info(f"✅ Lambda function updated: {config.app_name}")
                else:
                    raise
            
            function_arn = response['FunctionArn']
            
            # Create deployment result
            result = ApiDeploymentResult(
                app_name=config.app_name,
                deployment_method=DeploymentMethod.LAMBDA,
                endpoint_url=f"https://{self.region}.amazonaws.com/lambda/{config.app_name}",
                function_arn=function_arn,
                health_check_url=None,  # Will be set by API Gateway
                status="deployed"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to deploy Lambda function: {e}")
            raise
        finally:
            # Cleanup deployment package
            try:
                os.unlink(package_path)
            except:
                pass
    
    def deploy_ecs(self, repo_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """
        Deploy Node.js API as ECS/Fargate service
        ✅ Containerized Node.js API deployment
        """
        
        logger.info(f"🐳 Deploying Node.js API to ECS: {config.app_name}")
        
        try:
            # Create ECR repository
            repository_uri = self.create_ecr_repository(config.app_name)
            
            # Create Dockerfile if it doesn't exist
            self._ensure_dockerfile(repo_path, config)
            
            # Build and push Docker image
            image_uri = self.build_and_push_docker_image(repo_path, repository_uri)
            
            # Create ECS cluster
            cluster_name = f"{config.app_name}-cluster"
            self._create_ecs_cluster(cluster_name)
            
            # Create task definition
            task_definition_arn = self._create_task_definition(config, image_uri)
            
            # Create ECS service
            service_arn = self._create_ecs_service(cluster_name, config, task_definition_arn)
            
            # Create Application Load Balancer
            load_balancer_arn, target_group_arn = self._create_load_balancer(config)
            
            # Update service with load balancer
            self._update_service_load_balancer(cluster_name, config.app_name, target_group_arn)
            
            # Get load balancer DNS name
            lb_response = self.elbv2_client.describe_load_balancers(
                LoadBalancerArns=[load_balancer_arn]
            )
            dns_name = lb_response['LoadBalancers'][0]['DNSName']
            endpoint_url = f"http://{dns_name}"
            
            result = ApiDeploymentResult(
                app_name=config.app_name,
                deployment_method=DeploymentMethod.ECS,
                endpoint_url=endpoint_url,
                service_arn=service_arn,
                load_balancer_arn=load_balancer_arn,
                health_check_url=f"{endpoint_url}{config.health_check_path}",
                status="deployed"
            )
            
            logger.info(f"✅ ECS deployment completed: {endpoint_url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to deploy to ECS: {e}")
            raise
    
    def _ensure_dockerfile(self, repo_path: str, config: ApiDeploymentConfig):
        """Create Dockerfile if it doesn't exist"""
        
        dockerfile_path = Path(repo_path) / 'Dockerfile'
        
        if dockerfile_path.exists():
            logger.info("✅ Using existing Dockerfile")
            return
        
        # Create default Dockerfile for Node.js API
        dockerfile_content = f"""
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:3000{config.health_check_path} || exit 1

# Start application
CMD ["npm", "start"]
""".strip()
        
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info("✅ Created default Dockerfile")
    
    def _create_ecs_cluster(self, cluster_name: str) -> str:
        """Create ECS cluster"""
        
        try:
            response = self.ecs_client.create_cluster(
                clusterName=cluster_name,
                capacityProviders=['FARGATE'],
                defaultCapacityProviderStrategy=[
                    {
                        'capacityProvider': 'FARGATE',
                        'weight': 1
                    }
                ],
                tags=[
                    {'key': 'Project', 'value': 'CodeFlowOps'},
                    {'key': 'ManagedBy', 'value': 'NodeJSApiPlugin'}
                ]
            )
            
            logger.info(f"✅ Created ECS cluster: {cluster_name}")
            return response['cluster']['clusterArn']
            
        except Exception as e:
            if 'ClusterAlreadyExistsException' in str(e):
                logger.info(f"ECS cluster already exists: {cluster_name}")
                return f"arn:aws:ecs:{self.region}:*:cluster/{cluster_name}"
            else:
                raise
    
    def _create_task_definition(self, config: ApiDeploymentConfig, image_uri: str) -> str:
        """Create ECS task definition"""
        
        task_name = f"{config.app_name}-task"
        
        # Create execution role
        execution_role_arn = self.create_execution_role(
            f"{config.app_name}-task",
            additional_policies=['arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy']
        )
        
        task_definition = {
            'family': task_name,
            'networkMode': 'awsvpc',
            'requiresCompatibilities': ['FARGATE'],
            'cpu': '256',  # 0.25 vCPU
            'memory': str(config.memory_size or 512),
            'executionRoleArn': execution_role_arn,
            'containerDefinitions': [
                {
                    'name': config.app_name,
                    'image': image_uri,
                    'essential': True,
                    'portMappings': [
                        {
                            'containerPort': 3000,
                            'protocol': 'tcp'
                        }
                    ],
                    'environment': [
                        {'name': k, 'value': v} 
                        for k, v in (config.environment_variables or {}).items()
                    ],
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-group': f'/ecs/{config.app_name}',
                            'awslogs-region': self.region,
                            'awslogs-stream-prefix': 'ecs'
                        }
                    },
                    'healthCheck': {
                        'command': [
                            'CMD-SHELL',
                            f'curl -f http://localhost:3000{config.health_check_path} || exit 1'
                        ],
                        'interval': 30,
                        'timeout': 5,
                        'retries': 3,
                        'startPeriod': 60
                    }
                }
            ],
            'tags': [
                {'key': 'Project', 'value': 'CodeFlowOps'},
                {'key': 'Framework', 'value': config.framework.value}
            ]
        }
        
        # Create CloudWatch log group
        try:
            self.logs_client.create_log_group(
                logGroupName=f'/ecs/{config.app_name}',
                retentionInDays=14
            )
        except Exception as e:
            if 'ResourceAlreadyExistsException' not in str(e):
                logger.warning(f"Failed to create log group: {e}")
        
        response = self.ecs_client.register_task_definition(**task_definition)
        task_definition_arn = response['taskDefinition']['taskDefinitionArn']
        
        logger.info(f"✅ Created task definition: {task_name}")
        return task_definition_arn
    
    def _create_ecs_service(self, cluster_name: str, config: ApiDeploymentConfig, task_definition_arn: str) -> str:
        """Create ECS service"""
        
        service_name = f"{config.app_name}-service"
        
        # Get default VPC and subnets if not provided
        if not config.vpc_config:
            vpc_id, subnet_ids = self._get_default_vpc_config()
            security_group_id = self._create_service_security_group(vpc_id, config.app_name)
        else:
            subnet_ids = config.vpc_config['subnet_ids']
            security_group_id = config.vpc_config['security_group_ids'][0]
        
        service_config = {
            'cluster': cluster_name,
            'serviceName': service_name,
            'taskDefinition': task_definition_arn,
            'desiredCount': 1,
            'launchType': 'FARGATE',
            'networkConfiguration': {
                'awsvpcConfiguration': {
                    'subnets': subnet_ids,
                    'securityGroups': [security_group_id],
                    'assignPublicIp': 'ENABLED'  # Required for Fargate with ALB
                }
            },
            'tags': [
                {'key': 'Project', 'value': 'CodeFlowOps'},
                {'key': 'ManagedBy', 'value': 'NodeJSApiPlugin'}
            ]
        }
        
        response = self.ecs_client.create_service(**service_config)
        service_arn = response['service']['serviceArn']
        
        logger.info(f"✅ Created ECS service: {service_name}")
        return service_arn
    
    def _get_default_vpc_config(self):
        """Get default VPC and subnet configuration"""
        
        # Get default VPC
        vpcs = self.ec2_client.describe_vpcs(
            Filters=[{'Name': 'is-default', 'Values': ['true']}]
        )
        
        if not vpcs['Vpcs']:
            raise Exception("No default VPC found")
        
        vpc_id = vpcs['Vpcs'][0]['VpcId']
        
        # Get public subnets in default VPC
        subnets = self.ec2_client.describe_subnets(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'map-public-ip-on-launch', 'Values': ['true']}
            ]
        )
        
        subnet_ids = [subnet['SubnetId'] for subnet in subnets['Subnets']]
        
        return vpc_id, subnet_ids
    
    def _create_service_security_group(self, vpc_id: str, app_name: str) -> str:
        """Create security group for ECS service"""
        
        sg_name = f"{app_name}-ecs-sg"
        
        try:
            response = self.ec2_client.create_security_group(
                GroupName=sg_name,
                Description=f"Security group for {app_name} ECS service",
                VpcId=vpc_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'security-group',
                        'Tags': [
                            {'Key': 'Name', 'Value': sg_name},
                            {'Key': 'Project', 'Value': 'CodeFlowOps'}
                        ]
                    }
                ]
            )
            
            security_group_id = response['GroupId']
            
            # Add inbound rules
            self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 3000,
                        'ToPort': 3000,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP access'}]
                    }
                ]
            )
            
            logger.info(f"✅ Created security group: {security_group_id}")
            return security_group_id
            
        except Exception as e:
            if 'InvalidGroup.Duplicate' in str(e):
                # Security group exists, find and return it
                sgs = self.ec2_client.describe_security_groups(
                    Filters=[
                        {'Name': 'group-name', 'Values': [sg_name]},
                        {'Name': 'vpc-id', 'Values': [vpc_id]}
                    ]
                )
                return sgs['SecurityGroups'][0]['GroupId']
            else:
                raise
    
    def _create_load_balancer(self, config: ApiDeploymentConfig):
        """Create Application Load Balancer"""
        
        lb_name = f"{config.app_name}-alb"
        tg_name = f"{config.app_name}-tg"
        
        # Get VPC configuration
        if not config.vpc_config:
            vpc_id, subnet_ids = self._get_default_vpc_config()
        else:
            vpc_id = config.vpc_config['vpc_id']
            subnet_ids = config.vpc_config['subnet_ids']
        
        # Create load balancer
        lb_response = self.elbv2_client.create_load_balancer(
            Name=lb_name,
            Subnets=subnet_ids,
            SecurityGroups=[self._create_lb_security_group(vpc_id, config.app_name)],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4',
            Tags=[
                {'Key': 'Project', 'Value': 'CodeFlowOps'},
                {'Key': 'AppName', 'Value': config.app_name}
            ]
        )
        
        lb_arn = lb_response['LoadBalancers'][0]['LoadBalancerArn']
        
        # Create target group
        tg_response = self.elbv2_client.create_target_group(
            Name=tg_name,
            Protocol='HTTP',
            Port=3000,
            VpcId=vpc_id,
            TargetType='ip',
            HealthCheckPath=config.health_check_path,
            HealthCheckProtocol='HTTP',
            HealthCheckIntervalSeconds=30,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=5,
            Tags=[
                {'Key': 'Project', 'Value': 'CodeFlowOps'},
                {'Key': 'AppName', 'Value': config.app_name}
            ]
        )
        
        tg_arn = tg_response['TargetGroups'][0]['TargetGroupArn']
        
        # Create listener
        self.elbv2_client.create_listener(
            LoadBalancerArn=lb_arn,
            Protocol='HTTP',
            Port=80,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': tg_arn
                }
            ]
        )
        
        logger.info(f"✅ Created load balancer: {lb_name}")
        return lb_arn, tg_arn
    
    def _create_lb_security_group(self, vpc_id: str, app_name: str) -> str:
        """Create security group for load balancer"""
        
        sg_name = f"{app_name}-alb-sg"
        
        try:
            response = self.ec2_client.create_security_group(
                GroupName=sg_name,
                Description=f"Security group for {app_name} load balancer",
                VpcId=vpc_id
            )
            
            security_group_id = response['GroupId']
            
            # Add inbound rules
            self.ec2_client.authorize_security_group_ingress(
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
            
            return security_group_id
            
        except Exception as e:
            if 'InvalidGroup.Duplicate' in str(e):
                sgs = self.ec2_client.describe_security_groups(
                    Filters=[
                        {'Name': 'group-name', 'Values': [sg_name]},
                        {'Name': 'vpc-id', 'Values': [vpc_id]}
                    ]
                )
                return sgs['SecurityGroups'][0]['GroupId']
            else:
                raise
    
    def _update_service_load_balancer(self, cluster_name: str, service_name: str, target_group_arn: str):
        """Update ECS service with load balancer configuration"""
        
        try:
            self.ecs_client.update_service(
                cluster=cluster_name,
                service=f"{service_name}-service",
                loadBalancers=[
                    {
                        'targetGroupArn': target_group_arn,
                        'containerName': service_name,
                        'containerPort': 3000
                    }
                ]
            )
            
            logger.info("✅ Updated ECS service with load balancer")
            
        except Exception as e:
            logger.warning(f"Failed to update service with load balancer: {e}")
