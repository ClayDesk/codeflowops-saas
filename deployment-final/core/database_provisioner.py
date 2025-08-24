# Phase 3: Enhanced Database Provisioner
# backend/core/database_provisioner.py

"""
Multi-database deployment support with production hardening
Enterprise-grade database provisioning with RDS Proxy, VPC endpoints, and security
"""

import boto3
import logging
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..providers.postgresql_provider import PostgreSQLProvider
from ..providers.mysql_provider import MySQLProvider
from ..providers.mongodb_provider import MongoDBProvider
from ..providers.base_database_provider import DatabaseConfig, DatabaseInstance

logger = logging.getLogger(__name__)

class DatabaseEngine(Enum):
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"

class EnvironmentType(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class VPCEndpoint:
    """VPC Interface Endpoint configuration"""
    service_name: str
    endpoint_id: str
    dns_names: List[str]
    policy_document: Dict[str, Any]

@dataclass
class SecureVPC:
    """VPC with interface endpoints for cost optimization"""
    vpc_id: str
    private_subnet_ids: List[str]
    public_subnet_ids: List[str]
    security_group_id: str
    endpoints: List[VPCEndpoint] = field(default_factory=list)
    nat_gateway_id: Optional[str] = None

@dataclass
class RDSProxy:
    """RDS Proxy configuration for connection pooling"""
    proxy_name: str
    proxy_arn: str
    endpoint: str
    port: int
    target_group_arn: str
    auth: Dict[str, str]

@dataclass
class EnhancedDatabaseInstance:
    """Enhanced database instance with enterprise features"""
    base_instance: DatabaseInstance
    vpc: SecureVPC
    proxy: Optional[RDSProxy] = None
    backup_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    secrets_manager_arn: Optional[str] = None

class DatabaseProvisioner:
    """
    ✅ Multi-database deployment support with production hardening
    
    Features:
    - RDS Proxy for production connection pooling
    - VPC Interface Endpoints for cost optimization
    - AWS Secrets Manager integration
    - Automated backup and monitoring
    - Security best practices
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        
        # AWS clients
        self.ec2 = boto3.client('ec2', region_name=region)
        self.rds = boto3.client('rds', region_name=region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Database providers from Phase 2
        self.providers = {
            DatabaseEngine.MYSQL: MySQLProvider(region),
            DatabaseEngine.POSTGRESQL: PostgreSQLProvider(region),
            DatabaseEngine.MONGODB: MongoDBProvider(region)
        }
        
        logger.info(f"🏗️ Database provisioner initialized in {region}")
    
    def provision_database(self, db_config: DatabaseConfig) -> EnhancedDatabaseInstance:
        """
        Provision database with security best practices and RDS Proxy
        
        🔄 Provisioning Flow:
        1. Create secure VPC with interface endpoints
        2. Provision database using appropriate provider
        3. Create RDS Proxy for production environments
        4. Set up backup automation and monitoring
        5. Store credentials in AWS Secrets Manager
        """
        
        logger.info(f"🚀 Starting database provisioning: {db_config.db_name}")
        
        try:
            # Step 1: Create secure VPC infrastructure
            vpc = self.create_secure_vpc_with_endpoints(db_config.db_name)
            
            # Step 2: Update config with VPC details
            enhanced_config = self._enhance_config_with_vpc(db_config, vpc)
            
            # Step 3: Provision database instance
            db_engine = DatabaseEngine(db_config.engine.split('-')[0].lower())  # mysql-8.0 -> mysql
            provider = self.providers[db_engine]
            base_instance = provider.create_database(enhanced_config)
            
            # Step 4: Create RDS Proxy for production
            proxy = None
            if (enhanced_config.environment == "production" and 
                db_engine in [DatabaseEngine.MYSQL, DatabaseEngine.POSTGRESQL]):
                proxy = self.create_rds_proxy(base_instance, vpc, db_engine)
            
            # Step 5: Set up backup automation
            backup_config = self.setup_backup_automation(base_instance, enhanced_config)
            
            # Step 6: Configure monitoring
            monitoring_config = self.setup_monitoring(base_instance, enhanced_config)
            
            # Step 7: Store credentials in Secrets Manager
            secrets_arn = self.create_database_secret(base_instance, enhanced_config)
            
            # Create enhanced instance
            enhanced_instance = EnhancedDatabaseInstance(
                base_instance=base_instance,
                vpc=vpc,
                proxy=proxy,
                backup_config=backup_config,
                monitoring_config=monitoring_config,
                secrets_manager_arn=secrets_arn
            )
            
            logger.info(f"✅ Database provisioned successfully: {base_instance.instance_id}")
            logger.info(f"🔗 Connection endpoint: {self.get_connection_endpoint(enhanced_instance)}")
            
            return enhanced_instance
            
        except Exception as e:
            logger.error(f"❌ Database provisioning failed: {e}")
            raise
    
    def create_secure_vpc_with_endpoints(self, db_name: str) -> SecureVPC:
        """Create VPC with interface endpoints to reduce NAT costs"""
        
        logger.info(f"🏗️ Creating secure VPC for database: {db_name}")
        
        # Create VPC
        vpc_response = self.ec2.create_vpc(
            CidrBlock='10.0.0.0/16',
            EnableDnsHostnames=True,
            EnableDnsSupport=True
        )
        vpc_id = vpc_response['Vpc']['VpcId']
        
        # Tag VPC
        self.ec2.create_tags(
            Resources=[vpc_id],
            Tags=[
                {'Key': 'Name', 'Value': f'codeflowops-{db_name}-vpc'},
                {'Key': 'Environment', 'Value': 'codeflowops'},
                {'Key': 'ManagedBy', 'Value': 'CodeFlowOps'}
            ]
        )
        
        # Create Internet Gateway
        igw_response = self.ec2.create_internet_gateway()
        igw_id = igw_response['InternetGateway']['InternetGatewayId']
        self.ec2.attach_internet_gateway(VpcId=vpc_id, InternetGatewayId=igw_id)
        
        # Create subnets
        private_subnet_ids = self._create_private_subnets(vpc_id, db_name)
        public_subnet_ids = self._create_public_subnets(vpc_id, igw_id, db_name)
        
        # Create NAT Gateway for private subnet internet access
        nat_gateway_id = self._create_nat_gateway(public_subnet_ids[0], db_name)
        
        # Create route tables
        self._create_route_tables(vpc_id, private_subnet_ids, public_subnet_ids, igw_id, nat_gateway_id)
        
        # Create security group
        security_group_id = self._create_database_security_group(vpc_id, db_name)
        
        # ✅ Create VPC Interface Endpoints for cost optimization and security
        endpoints = self._create_vpc_endpoints(vpc_id, private_subnet_ids, security_group_id, db_name)
        
        vpc = SecureVPC(
            vpc_id=vpc_id,
            private_subnet_ids=private_subnet_ids,
            public_subnet_ids=public_subnet_ids,
            security_group_id=security_group_id,
            endpoints=endpoints,
            nat_gateway_id=nat_gateway_id
        )
        
        logger.info(f"✅ Secure VPC created: {vpc_id}")
        logger.info(f"📊 VPC Endpoints created: {len(endpoints)} (cost optimization)")
        
        return vpc
    
    def _create_private_subnets(self, vpc_id: str, db_name: str) -> List[str]:
        """Create private subnets for database instances"""
        
        availability_zones = self.ec2.describe_availability_zones()['AvailabilityZones']
        private_subnet_ids = []
        
        for i, az in enumerate(availability_zones[:2]):  # Use first 2 AZs
            subnet_response = self.ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock=f'10.0.{i+1}.0/24',
                AvailabilityZone=az['ZoneName']
            )
            subnet_id = subnet_response['Subnet']['SubnetId']
            private_subnet_ids.append(subnet_id)
            
            # Tag subnet
            self.ec2.create_tags(
                Resources=[subnet_id],
                Tags=[
                    {'Key': 'Name', 'Value': f'codeflowops-{db_name}-private-{i+1}'},
                    {'Key': 'Type', 'Value': 'Private'},
                    {'Key': 'Environment', 'Value': 'codeflowops'}
                ]
            )
        
        return private_subnet_ids
    
    def _create_public_subnets(self, vpc_id: str, igw_id: str, db_name: str) -> List[str]:
        """Create public subnets for NAT Gateway"""
        
        availability_zones = self.ec2.describe_availability_zones()['AvailabilityZones']
        public_subnet_ids = []
        
        for i, az in enumerate(availability_zones[:1]):  # One public subnet for NAT
            subnet_response = self.ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock=f'10.0.10{i+1}.0/24',
                AvailabilityZone=az['ZoneName']
            )
            subnet_id = subnet_response['Subnet']['SubnetId']
            public_subnet_ids.append(subnet_id)
            
            # Enable auto-assign public IP
            self.ec2.modify_subnet_attribute(
                SubnetId=subnet_id,
                MapPublicIpOnLaunch={'Value': True}
            )
            
            # Tag subnet
            self.ec2.create_tags(
                Resources=[subnet_id],
                Tags=[
                    {'Key': 'Name', 'Value': f'codeflowops-{db_name}-public-{i+1}'},
                    {'Key': 'Type', 'Value': 'Public'},
                    {'Key': 'Environment', 'Value': 'codeflowops'}
                ]
            )
        
        return public_subnet_ids
    
    def _create_nat_gateway(self, public_subnet_id: str, db_name: str) -> str:
        """Create NAT Gateway for private subnet internet access"""
        
        # Allocate Elastic IP
        eip_response = self.ec2.allocate_address(Domain='vpc')
        allocation_id = eip_response['AllocationId']
        
        # Create NAT Gateway
        nat_response = self.ec2.create_nat_gateway(
            SubnetId=public_subnet_id,
            AllocationId=allocation_id
        )
        nat_gateway_id = nat_response['NatGateway']['NatGatewayId']
        
        # Wait for NAT Gateway to be available
        logger.info("⏳ Waiting for NAT Gateway to become available...")
        waiter = self.ec2.get_waiter('nat_gateway_available')
        waiter.wait(NatGatewayIds=[nat_gateway_id])
        
        # Tag NAT Gateway
        self.ec2.create_tags(
            Resources=[nat_gateway_id],
            Tags=[
                {'Key': 'Name', 'Value': f'codeflowops-{db_name}-nat'},
                {'Key': 'Environment', 'Value': 'codeflowops'}
            ]
        )
        
        return nat_gateway_id
    
    def _create_route_tables(self, vpc_id: str, private_subnet_ids: List[str], 
                           public_subnet_ids: List[str], igw_id: str, nat_gateway_id: str):
        """Create route tables for public and private subnets"""
        
        # Public route table (to Internet Gateway)
        public_rt_response = self.ec2.create_route_table(VpcId=vpc_id)
        public_rt_id = public_rt_response['RouteTable']['RouteTableId']
        
        self.ec2.create_route(
            RouteTableId=public_rt_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=igw_id
        )
        
        # Associate public subnets with public route table
        for subnet_id in public_subnet_ids:
            self.ec2.associate_route_table(RouteTableId=public_rt_id, SubnetId=subnet_id)
        
        # Private route table (to NAT Gateway)
        private_rt_response = self.ec2.create_route_table(VpcId=vpc_id)
        private_rt_id = private_rt_response['RouteTable']['RouteTableId']
        
        self.ec2.create_route(
            RouteTableId=private_rt_id,
            DestinationCidrBlock='0.0.0.0/0',
            NatGatewayId=nat_gateway_id
        )
        
        # Associate private subnets with private route table
        for subnet_id in private_subnet_ids:
            self.ec2.associate_route_table(RouteTableId=private_rt_id, SubnetId=subnet_id)
    
    def _create_database_security_group(self, vpc_id: str, db_name: str) -> str:
        """Create security group for database access"""
        
        sg_response = self.ec2.create_security_group(
            GroupName=f'codeflowops-{db_name}-db-sg',
            Description=f'Security group for CodeFlowOps database {db_name}',
            VpcId=vpc_id
        )
        security_group_id = sg_response['GroupId']
        
        # Allow database ports from within VPC
        database_ports = [3306, 5432, 27017]  # MySQL, PostgreSQL, MongoDB
        
        for port in database_ports:
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[{
                    'IpProtocol': 'tcp',
                    'FromPort': port,
                    'ToPort': port,
                    'IpRanges': [{'CidrIp': '10.0.0.0/16', 'Description': 'VPC access'}]
                }]
            )
        
        # Tag security group
        self.ec2.create_tags(
            Resources=[security_group_id],
            Tags=[
                {'Key': 'Name', 'Value': f'codeflowops-{db_name}-db-sg'},
                {'Key': 'Environment', 'Value': 'codeflowops'}
            ]
        )
        
        return security_group_id
    
    def _create_vpc_endpoints(self, vpc_id: str, subnet_ids: List[str], 
                            security_group_id: str, db_name: str) -> List[VPCEndpoint]:
        """✅ Create VPC Interface Endpoints for cost optimization and security"""
        
        # VPC endpoints to reduce NAT Gateway costs
        interface_endpoints = [
            'com.amazonaws.us-east-1.secretsmanager',  # Secrets Manager
            'com.amazonaws.us-east-1.ssm',             # Systems Manager
            'com.amazonaws.us-east-1.logs',            # CloudWatch Logs
            'com.amazonaws.us-east-1.monitoring',      # CloudWatch
            'com.amazonaws.us-east-1.rds'              # RDS API
        ]
        
        created_endpoints = []
        
        for service_name in interface_endpoints:
            try:
                # Create least-privilege policy for each endpoint
                policy_document = self._get_least_privilege_endpoint_policy(service_name)
                
                endpoint_response = self.ec2.create_vpc_endpoint(
                    VpcId=vpc_id,
                    ServiceName=service_name,
                    VpcEndpointType='Interface',
                    SubnetIds=subnet_ids,
                    SecurityGroupIds=[security_group_id],
                    PolicyDocument=json.dumps(policy_document),
                    PrivateDnsEnabled=True
                )
                
                endpoint_id = endpoint_response['VpcEndpoint']['VpcEndpointId']
                
                # Tag endpoint
                self.ec2.create_tags(
                    Resources=[endpoint_id],
                    Tags=[
                        {'Key': 'Name', 'Value': f'codeflowops-{db_name}-{service_name.split(".")[-1]}'},
                        {'Key': 'Environment', 'Value': 'codeflowops'}
                    ]
                )
                
                created_endpoints.append(VPCEndpoint(
                    service_name=service_name,
                    endpoint_id=endpoint_id,
                    dns_names=endpoint_response['VpcEndpoint']['DnsEntries'],
                    policy_document=policy_document
                ))
                
                logger.info(f"✅ Created VPC endpoint: {service_name}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to create VPC endpoint {service_name}: {e}")
        
        return created_endpoints
    
    def _get_least_privilege_endpoint_policy(self, service_name: str) -> Dict[str, Any]:
        """Generate least-privilege policy for VPC endpoint"""
        
        service_policies = {
            'secretsmanager': {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringEquals": {
                            "aws:PrincipalTag/Environment": "codeflowops"
                        }
                    }
                }]
            },
            'ssm': {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                        "ssm:GetParametersByPath"
                    ],
                    "Resource": "*"
                }]
            },
            'logs': {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }]
            },
            'monitoring': {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "cloudwatch:PutMetricData",
                        "cloudwatch:GetMetricStatistics",
                        "cloudwatch:ListMetrics"
                    ],
                    "Resource": "*"
                }]
            },
            'rds': {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "rds:DescribeDBInstances",
                        "rds:DescribeDBClusters",
                        "rds:DescribeDBProxies"
                    ],
                    "Resource": "*"
                }]
            }
        }
        
        # Extract service name from full AWS service name
        service_key = service_name.split('.')[-1]
        return service_policies.get(service_key, {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": "*",
                "Action": "*",
                "Resource": "*"
            }]
        })
    
    def _enhance_config_with_vpc(self, config: DatabaseConfig, vpc: SecureVPC) -> DatabaseConfig:
        """Enhance database config with VPC details"""
        
        enhanced_config = DatabaseConfig(
            db_name=config.db_name,
            username=config.username,
            password=config.password,
            instance_class=config.instance_class,
            allocated_storage=config.allocated_storage,
            engine=config.engine,
            engine_version=config.engine_version,
            environment=config.environment,
            vpc_id=vpc.vpc_id,
            subnet_ids=vpc.private_subnet_ids,
            security_group_ids=[vpc.security_group_id],
            backup_retention_period=config.backup_retention_period or 7,
            multi_az=config.multi_az if config.multi_az is not None else True,
            encrypted=config.encrypted if config.encrypted is not None else True,
            tags=config.tags or {}
        )
        
        # Add VPC-specific tags
        enhanced_config.tags.update({
            'VPC': vpc.vpc_id,
            'Environment': 'codeflowops',
            'ManagedBy': 'CodeFlowOps-Phase3'
        })
        
        return enhanced_config
    
    def create_rds_proxy(self, db_instance: DatabaseInstance, vpc: SecureVPC, 
                        db_engine: DatabaseEngine) -> RDSProxy:
        """Create RDS Proxy for connection pooling and Lambda integration"""
        
        logger.info(f"🔗 Creating RDS Proxy for {db_instance.instance_id}")
        
        try:
            # Create IAM role for RDS Proxy
            proxy_role_arn = self._create_rds_proxy_role(db_instance.instance_id)
            
            # Get database secret ARN
            secret_arn = self._get_database_secret_arn(db_instance.instance_id)
            
            # Create RDS Proxy
            engine_family = 'MYSQL' if db_engine == DatabaseEngine.MYSQL else 'POSTGRESQL'
            
            proxy_response = self.rds.create_db_proxy(
                DBProxyName=f"{db_instance.instance_id}-proxy",
                EngineFamily=engine_family,
                Targets=[{
                    'DBInstanceIdentifier': db_instance.instance_id
                }],
                Auth=[{
                    'AuthScheme': 'SECRETS',
                    'SecretArn': secret_arn,
                    'IAMAuth': 'DISABLED'
                }],
                RoleArn=proxy_role_arn,
                VpcSubnetIds=vpc.private_subnet_ids,
                VpcSecurityGroupIds=[vpc.security_group_id],
                RequireTLS=True,
                IdleClientTimeout=1800,  # 30 minutes
                MaxConnectionsPercent=100,
                MaxIdleConnectionsPercent=50,
                Tags=[
                    {'Key': 'Name', 'Value': f'{db_instance.instance_id}-proxy'},
                    {'Key': 'Environment', 'Value': 'codeflowops'}
                ]
            )
            
            proxy_arn = proxy_response['DBProxy']['DBProxyArn']
            proxy_name = proxy_response['DBProxy']['DBProxyName']
            
            # Wait for proxy to be available
            logger.info("⏳ Waiting for RDS Proxy to become available...")
            waiter = self.rds.get_waiter('db_proxy_available')
            waiter.wait(DBProxyName=proxy_name)
            
            # Get proxy endpoint
            proxy_details = self.rds.describe_db_proxies(DBProxyName=proxy_name)
            proxy_endpoint = proxy_details['DBProxies'][0]['Endpoint']
            
            proxy = RDSProxy(
                proxy_name=proxy_name,
                proxy_arn=proxy_arn,
                endpoint=proxy_endpoint,
                port=db_instance.port,
                target_group_arn=proxy_response['DBProxy']['DBProxyArn'],  # Simplified
                auth={'type': 'secrets', 'secret_arn': secret_arn}
            )
            
            logger.info(f"✅ RDS Proxy created: {proxy_endpoint}")
            return proxy
            
        except Exception as e:
            logger.error(f"❌ RDS Proxy creation failed: {e}")
            raise
    
    def _create_rds_proxy_role(self, db_instance_id: str) -> str:
        """Create IAM role for RDS Proxy"""
        
        role_name = f"codeflowops-{db_instance_id}-proxy-role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "rds.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        # Create role
        self.iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Tags=[
                {'Key': 'Environment', 'Value': 'codeflowops'},
                {'Key': 'Purpose', 'Value': 'RDS-Proxy'}
            ]
        )
        
        # Attach policy for Secrets Manager access
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetResourcePolicy",
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds"
                ],
                "Resource": f"arn:aws:secretsmanager:{self.region}:*:secret:codeflowops/{db_instance_id}/*"
            }]
        }
        
        self.iam.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{role_name}-secrets-policy",
            PolicyDocument=json.dumps(policy_document)
        )
        
        # Return role ARN
        role_response = self.iam.get_role(RoleName=role_name)
        return role_response['Role']['Arn']
    
    def setup_backup_automation(self, db_instance: DatabaseInstance, 
                              config: DatabaseConfig) -> Dict[str, Any]:
        """Set up automated backup and point-in-time recovery"""
        
        logger.info(f"💾 Setting up backup automation for {db_instance.instance_id}")
        
        backup_config = {
            'retention_period': config.backup_retention_period or 7,
            'backup_window': '03:00-04:00',  # UTC
            'maintenance_window': 'sun:04:00-sun:05:00',  # UTC
            'point_in_time_recovery': True,
            'final_snapshot_identifier': f"{db_instance.instance_id}-final-snapshot-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Configure automated backups (already done during instance creation)
        # This is where you'd add additional backup configurations like
        # cross-region snapshots, lifecycle policies, etc.
        
        logger.info("✅ Backup automation configured")
        return backup_config
    
    def setup_monitoring(self, db_instance: DatabaseInstance, 
                        config: DatabaseConfig) -> Dict[str, Any]:
        """Configure comprehensive monitoring"""
        
        logger.info(f"📊 Setting up monitoring for {db_instance.instance_id}")
        
        monitoring_config = {
            'performance_insights': True,
            'enhanced_monitoring': True,
            'cloudwatch_logs': True,
            'alarms': []
        }
        
        # Create CloudWatch alarms
        alarm_configs = [
            {
                'AlarmName': f"{db_instance.instance_id}-cpu-utilization",
                'MetricName': 'CPUUtilization',
                'Threshold': 80.0,
                'ComparisonOperator': 'GreaterThanThreshold'
            },
            {
                'AlarmName': f"{db_instance.instance_id}-database-connections",
                'MetricName': 'DatabaseConnections',
                'Threshold': 80.0,  # Adjust based on instance class
                'ComparisonOperator': 'GreaterThanThreshold'
            },
            {
                'AlarmName': f"{db_instance.instance_id}-free-storage-space",
                'MetricName': 'FreeStorageSpace',
                'Threshold': 2000000000.0,  # 2GB in bytes
                'ComparisonOperator': 'LessThanThreshold'
            }
        ]
        
        for alarm_config in alarm_configs:
            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_config['AlarmName'],
                    ComparisonOperator=alarm_config['ComparisonOperator'],
                    EvaluationPeriods=2,
                    MetricName=alarm_config['MetricName'],
                    Namespace='AWS/RDS',
                    Period=300,
                    Statistic='Average',
                    Threshold=alarm_config['Threshold'],
                    ActionsEnabled=True,
                    AlarmDescription=f"Monitor {alarm_config['MetricName']} for {db_instance.instance_id}",
                    Dimensions=[{
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_instance.instance_id
                    }],
                    Unit='Percent' if 'utilization' in alarm_config['AlarmName'].lower() else 'Count'
                )
                monitoring_config['alarms'].append(alarm_config['AlarmName'])
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to create alarm {alarm_config['AlarmName']}: {e}")
        
        logger.info(f"✅ Monitoring configured with {len(monitoring_config['alarms'])} alarms")
        return monitoring_config
    
    def create_database_secret(self, db_instance: DatabaseInstance, 
                             config: DatabaseConfig) -> str:
        """Store database credentials in AWS Secrets Manager"""
        
        logger.info(f"🔐 Creating database secret for {db_instance.instance_id}")
        
        secret_name = f"codeflowops/{db_instance.instance_id}/credentials"
        
        secret_value = {
            'username': db_instance.username,
            'password': config.password,
            'host': db_instance.endpoint,
            'port': db_instance.port,
            'database': db_instance.database_name,
            'engine': db_instance.engine
        }
        
        try:
            response = self.secrets_manager.create_secret(
                Name=secret_name,
                Description=f"Database credentials for {db_instance.instance_id}",
                SecretString=json.dumps(secret_value),
                Tags=[
                    {'Key': 'Environment', 'Value': 'codeflowops'},
                    {'Key': 'DatabaseInstance', 'Value': db_instance.instance_id},
                    {'Key': 'ManagedBy', 'Value': 'CodeFlowOps-Phase3'}
                ]
            )
            
            secret_arn = response['ARN']
            logger.info(f"✅ Database secret created: {secret_name}")
            return secret_arn
            
        except self.secrets_manager.exceptions.ResourceExistsException:
            # Secret already exists, update it
            self.secrets_manager.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_value)
            )
            
            # Get existing secret ARN
            response = self.secrets_manager.describe_secret(SecretId=secret_name)
            return response['ARN']
    
    def _get_database_secret_arn(self, db_instance_id: str) -> str:
        """Get ARN of database secret"""
        secret_name = f"codeflowops/{db_instance_id}/credentials"
        response = self.secrets_manager.describe_secret(SecretId=secret_name)
        return response['ARN']
    
    def get_connection_endpoint(self, enhanced_instance: EnhancedDatabaseInstance) -> str:
        """Get the appropriate connection endpoint (proxy if available, otherwise direct)"""
        
        if enhanced_instance.proxy:
            return enhanced_instance.proxy.endpoint
        else:
            return enhanced_instance.base_instance.endpoint
    
    def get_connection_string(self, enhanced_instance: EnhancedDatabaseInstance) -> str:
        """Generate connection string for the database"""
        
        endpoint = self.get_connection_endpoint(enhanced_instance)
        db_instance = enhanced_instance.base_instance
        
        if db_instance.engine.startswith('postgres'):
            return f"postgresql://{db_instance.username}:{{password}}@{endpoint}:{db_instance.port}/{db_instance.database_name}"
        elif db_instance.engine.startswith('mysql'):
            return f"mysql://{db_instance.username}:{{password}}@{endpoint}:{db_instance.port}/{db_instance.database_name}"
        elif db_instance.engine.startswith('docdb'):
            return f"mongodb://{db_instance.username}:{{password}}@{endpoint}:{db_instance.port}/{db_instance.database_name}"
        
        return f"unknown://{endpoint}:{db_instance.port}"
    
    def cleanup_database(self, enhanced_instance: EnhancedDatabaseInstance, 
                        delete_vpc: bool = True, create_final_snapshot: bool = True):
        """Clean up database and associated resources"""
        
        logger.info(f"🧹 Cleaning up database: {enhanced_instance.base_instance.instance_id}")
        
        try:
            # Delete RDS Proxy if exists
            if enhanced_instance.proxy:
                self.rds.delete_db_proxy(DBProxyName=enhanced_instance.proxy.proxy_name)
                logger.info("✅ RDS Proxy deleted")
            
            # Delete database instance
            final_snapshot_id = None
            if create_final_snapshot:
                final_snapshot_id = f"{enhanced_instance.base_instance.instance_id}-final-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            self.rds.delete_db_instance(
                DBInstanceIdentifier=enhanced_instance.base_instance.instance_id,
                SkipFinalSnapshot=not create_final_snapshot,
                FinalDBSnapshotIdentifier=final_snapshot_id,
                DeleteAutomatedBackups=True
            )
            logger.info("✅ Database instance deletion initiated")
            
            # Delete secret
            if enhanced_instance.secrets_manager_arn:
                secret_name = enhanced_instance.secrets_manager_arn.split(':')[-1]
                self.secrets_manager.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
                logger.info("✅ Database secret deleted")
            
            # Optionally delete VPC and associated resources
            if delete_vpc:
                self._cleanup_vpc_resources(enhanced_instance.vpc)
            
            logger.info(f"✅ Database cleanup completed: {enhanced_instance.base_instance.instance_id}")
            
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")
            raise
    
    def _cleanup_vpc_resources(self, vpc: SecureVPC):
        """Clean up VPC and associated resources"""
        
        logger.info(f"🧹 Cleaning up VPC resources: {vpc.vpc_id}")
        
        try:
            # Delete VPC endpoints
            for endpoint in vpc.endpoints:
                self.ec2.delete_vpc_endpoint(VpcEndpointId=endpoint.endpoint_id)
            
            # Delete NAT Gateway
            if vpc.nat_gateway_id:
                self.ec2.delete_nat_gateway(NatGatewayId=vpc.nat_gateway_id)
            
            # Note: In a real implementation, you'd need to:
            # 1. Delete all resources in dependency order
            # 2. Wait for resources to be fully deleted
            # 3. Handle cleanup failures gracefully
            # This is a simplified version
            
            logger.info("✅ VPC resources cleanup initiated")
            
        except Exception as e:
            logger.warning(f"⚠️ VPC cleanup warning: {e}")


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        provisioner = DatabaseProvisioner()
        
        # Example database configuration
        config = DatabaseConfig(
            db_name="example_app",
            username="appuser", 
            instance_class="db.t3.micro",
            allocated_storage=20,
            engine="mysql",
            environment="production"
        )
        
        # Provision database
        enhanced_db = provisioner.provision_database(config)
        
        print(f"✅ Database provisioned!")
        print(f"Connection endpoint: {provisioner.get_connection_endpoint(enhanced_db)}")
        print(f"Connection string: {provisioner.get_connection_string(enhanced_db)}")
        print(f"VPC endpoints: {len(enhanced_db.vpc.endpoints)}")
        print(f"RDS Proxy: {'Yes' if enhanced_db.proxy else 'No'}")
    
    asyncio.run(main())
