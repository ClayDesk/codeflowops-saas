"""
PHP Stack Provisioner - Universal Infrastructure with Database Support
"""
import logging
import uuid
import secrets
from pathlib import Path
from typing import Dict, Any, Optional
import json
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.interfaces import StackProvisioner  
from core.models import StackPlan, ProvisionResult

logger = logging.getLogger(__name__)

class PHPProvisioner(StackProvisioner):
    """Universal Infrastructure Provisioner for PHP Applications with Database Support"""
    
    def provision(self, plan: StackPlan, build_result: Any, credentials: Dict[str, Any]) -> ProvisionResult:
        """Provision AWS infrastructure for PHP application with intelligent database provisioning"""
        
        app_type = plan.config.get('app_type', plan.config.get('framework', 'php'))
        logger.info(f"🏗️ Provisioning universal PHP infrastructure for {app_type}")
        
        try:
            # 🧬 PHASE 2A: Analyze application requirements
            app_requirements = plan.config.get('requirements', {})
            database_config = self._provision_database(app_requirements, credentials)
            
            # 🏗️ PHASE 2B: Generate enhanced infrastructure configuration
            config = self._generate_infrastructure_config(plan, credentials, database_config)
            
            # 📋 Build provisioning logs
            provisioning_logs = [
                f"Generated universal infrastructure for {app_type} application",
                f"Detected {len(app_requirements.get('extensions', []))} required PHP extensions",
                "ECS Fargate cluster configured with dynamic scaling",
                "Application Load Balancer configured with health checks", 
                "Infrastructure configuration generated"
            ]
            
            if database_config.get('type') != 'none':
                provisioning_logs.append(f"Database infrastructure planned: {database_config['type'].upper()}")
                provisioning_logs.append(f"Database security configured for VPC isolation")
            else:
                provisioning_logs.append("No database required - stateless application")
            
            provisioning_logs.extend([
                "Environment variables configured for application type",
                f"Health check endpoint: {app_requirements.get('health_check', '/health')}",
                "Auto-scaling policies configured",
                "Deployment method selected based on requirements"
            ])
            
            return ProvisionResult(
                success=True,
                infrastructure_config=config,
                provisioning_logs=provisioning_logs,
                endpoints={}  # URLs will be populated after deployment
            )
            
        except Exception as e:
            logger.error(f"Universal PHP provisioning failed: {e}")
            return ProvisionResult(
                success=False,
                infrastructure_config={},
                provisioning_logs=[f"Provisioning failed: {str(e)}"],
                error_message=str(e)
            )
    
    def _provision_database(self, app_requirements: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """🗄️ Dynamically provision required database infrastructure"""
        
        database_req = app_requirements.get('database', {'type': 'optional'})
        
        if database_req.get('type') == 'mysql' and database_req.get('required', False):
            logger.info("🗄️ Provisioning MySQL RDS database")
            return self._provision_mysql_rds(database_req, credentials)
        elif database_req.get('type') == 'postgresql':
            logger.info("🗄️ Provisioning PostgreSQL RDS database")
            return self._provision_postgresql_rds(database_req, credentials)
        else:
            logger.info("🚫 No database provisioning required")
            return {'type': 'none'}
    
    def _provision_mysql_rds(self, db_config: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Create RDS MySQL instance configuration for the application"""
        
        # Generate unique identifiers for multi-tenant isolation
        unique_id = uuid.uuid4().hex[:8]
        secure_password = self._generate_secure_password()
        
        return {
            'type': 'mysql',
            'engine': 'mysql',
            'engine_version': '8.0',
            'instance_class': 'db.t3.micro',  # Cost-effective for thousands of users
            'allocated_storage': 20,
            'storage_type': 'gp2',
            'db_instance_identifier': f"php-app-db-{unique_id}",
            'database_name': f"appdb_{unique_id.replace('-', '_')}",
            'master_username': 'appuser',
            'master_password': secure_password,
            'vpc_security_group_ids': [],  # Will be populated during deployment
            'db_subnet_group_name': 'default',
            'publicly_accessible': False,  # VPC-only access for security
            'multi_az': False,  # Single AZ for cost optimization 
            'backup_retention_period': 7,  # 7 days backup retention
            'storage_encrypted': True,  # Encrypt at rest
            'deletion_protection': False,  # Allow deletion for dev environments
            'skip_final_snapshot': True,  # Skip final snapshot for faster deletion
            'port': 3306,
            'parameter_group': 'default.mysql8.0',
            'monitoring_interval': 0,  # Disable enhanced monitoring for cost
            'auto_minor_version_upgrade': True,
            # Connection details for application
            'connection': {
                'host': f"php-app-db-{unique_id}.{credentials.get('region', 'us-east-1')}.rds.amazonaws.com",
                'port': 3306,
                'database': f"appdb_{unique_id.replace('-', '_')}",
                'username': 'appuser',
                'password': secure_password
            }
        }
    
    def _provision_postgresql_rds(self, db_config: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Create RDS PostgreSQL instance configuration"""
        
        unique_id = uuid.uuid4().hex[:8]
        secure_password = self._generate_secure_password()
        
        return {
            'type': 'postgresql',
            'engine': 'postgres',
            'engine_version': '14.9',
            'instance_class': 'db.t3.micro',
            'allocated_storage': 20,
            'storage_type': 'gp2',
            'db_instance_identifier': f"php-app-pg-{unique_id}",
            'database_name': f"appdb_{unique_id.replace('-', '_')}",
            'master_username': 'appuser',
            'master_password': secure_password,
            'vpc_security_group_ids': [],
            'db_subnet_group_name': 'default',
            'publicly_accessible': False,
            'multi_az': False,
            'backup_retention_period': 7,
            'storage_encrypted': True,
            'deletion_protection': False,
            'skip_final_snapshot': True,
            'port': 5432,
            'parameter_group': 'default.postgres14',
            'monitoring_interval': 0,
            'auto_minor_version_upgrade': True,
            'connection': {
                'host': f"php-app-pg-{unique_id}.{credentials.get('region', 'us-east-1')}.rds.amazonaws.com",
                'port': 5432,
                'database': f"appdb_{unique_id.replace('-', '_')}",
                'username': 'appuser',
                'password': secure_password
            }
        }
    
    def _generate_secure_password(self) -> str:
        """Generate a secure password for database access"""
        # Generate a strong password with letters, digits, and safe special characters
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(16))
    
    def _generate_infrastructure_config(self, plan: StackPlan, credentials: Dict[str, Any], database_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate enhanced infrastructure configuration for PHP application with database support"""
        
        framework = plan.config.get('framework', 'php')
        app_requirements = plan.config.get('requirements', {})
        
        # Generate dynamic app name based on repository or timestamp
        repo_url = plan.config.get('repository_url', '')
        if repo_url:
            # Extract repo name from URL
            import re
            match = re.search(r'/([^/]+?)(?:\.git)?/?$', repo_url)
            base_name = match.group(1) if match else 'php-app'
            # Clean the name to be AWS-compatible
            base_name = re.sub(r'[^a-zA-Z0-9-]', '-', base_name.lower())
            base_name = base_name[:32]  # Limit length
        else:
            base_name = 'php-app'
        
        # Add timestamp for uniqueness across thousands of users
        import time
        unique_suffix = int(time.time()) % 10000
        app_name = f"{base_name}-{unique_suffix}"
        
        region = credentials.get('region', 'us-east-1')
        
        # 🎯 Enhanced container configuration with dynamic extensions
        container_extensions = app_requirements.get('extensions', ['pdo', 'gd'])
        health_check_path = app_requirements.get('health_check', '/health')
        
        # 🗄️ Database environment variables
        database_env_vars = []
        if database_config and database_config.get('type') != 'none':
            db_connection = database_config.get('connection', {})
            if database_config.get('type') == 'mysql':
                database_env_vars = [
                    {'name': 'DB_CONNECTION', 'value': 'mysql'},
                    {'name': 'DB_HOST', 'value': db_connection.get('host', '')},
                    {'name': 'DB_PORT', 'value': str(db_connection.get('port', 3306))},
                    {'name': 'DB_DATABASE', 'value': db_connection.get('database', '')},
                    {'name': 'DB_USERNAME', 'value': db_connection.get('username', '')},
                    {'name': 'DB_PASSWORD', 'value': db_connection.get('password', '')}
                ]
            elif database_config.get('type') == 'postgresql':
                database_env_vars = [
                    {'name': 'DB_CONNECTION', 'value': 'pgsql'},
                    {'name': 'DB_HOST', 'value': db_connection.get('host', '')},
                    {'name': 'DB_PORT', 'value': str(db_connection.get('port', 5432))},
                    {'name': 'DB_DATABASE', 'value': db_connection.get('database', '')},
                    {'name': 'DB_USERNAME', 'value': db_connection.get('username', '')},
                    {'name': 'DB_PASSWORD', 'value': db_connection.get('password', '')}
                ]
        
        # 🧬 Enhanced infrastructure configuration with database integration
        config = {
            # ECS Configuration with universal PHP support
            'cluster_name': f"{app_name}-cluster",
            'service_name': f"{app_name}-service", 
            'task_definition': {
                'family': f"{app_name}-task",
                'cpu': '512',  # Optimized for cost-efficiency
                'memory': '1024',
                'networkMode': 'awsvpc',
                'requiresCompatibilities': ['FARGATE'],
                'containerDefinitions': [{
                    'name': app_name,
                    'image': f"{app_name}:latest",  # Will be updated with ECR URI
                    'memory': 1024,
                    'portMappings': [{
                        'containerPort': 80,
                        'protocol': 'tcp'
                    }],
                    'healthCheck': {
                        'command': [
                            'CMD-SHELL',
                            f"curl -f http://localhost{health_check_path} || exit 1"
                        ],
                        'interval': 30,
                        'timeout': 5,
                        'retries': 3,
                        'startPeriod': 60
                    },
                    'environment': [
                        {'name': 'APP_ENV', 'value': 'production'},
                        {'name': 'APP_DEBUG', 'value': 'false'},
                        {'name': 'PHP_EXTENSIONS', 'value': ','.join(container_extensions)}
                    ] + database_env_vars + self._get_framework_environment_variables(framework),  # Merge all env vars
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-group': f"/ecs/{app_name}",
                            'awslogs-region': region,
                            'awslogs-stream-prefix': 'ecs'
                        }
                    }
                }]
            },
            
            # Load Balancer Configuration with enhanced health checks
            'load_balancer': {
                'name': f"{app_name}-alb",
                'type': 'application',
                'scheme': 'internet-facing',
                'target_group': {
                    'name': f"{app_name}-tg",
                    'protocol': 'HTTP',
                    'port': 80,
                    'health_check': {
                        'enabled': True,
                        'path': health_check_path,
                        'protocol': 'HTTP',
                        'port': 'traffic-port',
                        'healthy_threshold_count': 2,
                        'unhealthy_threshold_count': 5,
                        'timeout': 5,
                        'interval': 30,
                        'matcher': '200'
                    }
                }
            },
            
            # Monitoring Configuration
            'monitoring': {
                'log_group': f"/ecs/{app_name}",
                'retention_days': 7
            },
            
            # 🗄️ Database Configuration
            'database': database_config if database_config else {'type': 'none'},
            
            # 🚀 Application-specific configuration  
            'application': {
                'type': framework,
                'requirements': app_requirements,
                'php_version': app_requirements.get('php_version', '>=8.0'),
                'extensions': container_extensions,
                'health_check': health_check_path,
                'build_process': app_requirements.get('build_process', 'composer'),
                'requires_migrations': app_requirements.get('requires_migrations', False)
            },
            
            # Auto Scaling for thousands of users
            'auto_scaling': {
                'min_capacity': 1,
                'max_capacity': 10,  # Increased for scalability
                'target_cpu_utilization': 70,
                'target_memory_utilization': 80,
                'scale_in_cooldown': 300,
                'scale_out_cooldown': 180  # Faster scale-out for traffic spikes
            },
            
            # App Runner configuration
            'apprunner': {
                'port': 80,
                'health_path': health_check_path
            },
            
            # Standard health check URL
            'health_url': f'http://localhost{health_check_path}'
        }
        
        logger.info(f"🎯 Generated infrastructure for {framework} with database support")
        return config
    
    def _get_framework_environment_variables(self, framework: str) -> list:
        """Get framework-specific environment variables"""
        
        base_vars = []
        
        if framework.startswith('laravel'):
            base_vars = [
                {'name': 'LOG_CHANNEL', 'value': 'stderr'},
                {'name': 'CACHE_DRIVER', 'value': 'file'},
                {'name': 'SESSION_DRIVER', 'value': 'file'}
            ]
        elif framework == 'bookstack':
            base_vars = [
                {'name': 'CACHE_DRIVER', 'value': 'file'},
                {'name': 'SESSION_DRIVER', 'value': 'file'},
                {'name': 'MAIL_DRIVER', 'value': 'smtp'}
            ]
        elif framework == 'wordpress':
            base_vars = [
                {'name': 'WP_DEBUG', 'value': 'false'}
            ]
        
        return base_vars
    
    def _get_environment_variables(self, framework: str) -> list:
        """Get legacy environment variables for backward compatibility"""
        
        base_env = [
            {'name': 'PHP_ENV', 'value': 'production'},
            {'name': 'FRAMEWORK', 'value': framework}
        ]
        
        if framework == 'laravel':
            base_env.extend([
                {'name': 'APP_ENV', 'value': 'production'},
                {'name': 'APP_DEBUG', 'value': 'false'},
                {'name': 'LOG_CHANNEL', 'value': 'stderr'}
            ])
        
        return base_env
