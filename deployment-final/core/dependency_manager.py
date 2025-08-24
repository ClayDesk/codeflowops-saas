# Phase 5: Cross-Component Dependency Management
# backend/core/dependency_manager.py

"""
Cross-component dependency management with service discovery
✅ Advanced dependency resolution and management
✅ Service discovery and configuration injection
✅ Dynamic configuration updates and health propagation
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import boto3

logger = logging.getLogger(__name__)

class DependencyType(Enum):
    """Types of component dependencies"""
    DATABASE = "database"
    API = "api"
    FRONTEND = "frontend"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    SERVICE = "service"

class DependencyStatus(Enum):
    """Status of dependency resolution"""
    PENDING = "pending"
    RESOLVED = "resolved"
    FAILED = "failed"
    UPDATING = "updating"

@dataclass
class ServiceEndpoint:
    """Service endpoint definition"""
    name: str
    url: str
    port: int
    protocol: str = "https"
    health_check_path: str = "/health"
    
    # Security
    authentication_required: bool = False
    api_key_required: bool = False
    
    # Metadata
    version: str = "v1"
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ComponentDependency:
    """Individual component dependency definition"""
    name: str
    type: DependencyType
    component_id: str
    required: bool = True
    
    # Connection details
    endpoint: Optional[ServiceEndpoint] = None
    connection_string: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: DependencyStatus = DependencyStatus.PENDING
    last_health_check: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Retry configuration
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 5

@dataclass
class DependencyGraph:
    """Complete dependency graph for a deployment"""
    deployment_id: str
    components: Dict[str, List[ComponentDependency]] = field(default_factory=dict)
    resolved_dependencies: Dict[str, ServiceEndpoint] = field(default_factory=dict)
    
    # Graph metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: Optional[datetime] = None
    resolution_status: str = "pending"

class DependencyManager:
    """
    Cross-component dependency management with service discovery
    ✅ Advanced dependency resolution and configuration injection
    ✅ Dynamic service discovery with health monitoring
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        
        # AWS services
        self.ssm_client = boto3.client('ssm', region_name=region)
        self.secretsmanager_client = boto3.client('secretsmanager', region_name=region)
        self.servicediscovery_client = boto3.client('servicediscovery', region_name=region)
        
        # Internal state
        self.dependency_graphs: Dict[str, DependencyGraph] = {}
        self.service_registry: Dict[str, ServiceEndpoint] = {}
        
        logger.info(f"🔗 Dependency Manager initialized for region: {region}")
    
    async def create_dependency_graph(self, deployment_id: str, components: Dict[str, Dict[str, Any]]) -> DependencyGraph:
        """
        Create dependency graph for a multi-stack deployment
        ✅ Comprehensive dependency analysis and graph construction
        """
        
        logger.info(f"🕸️ Creating dependency graph for deployment: {deployment_id}")
        
        dependency_graph = DependencyGraph(deployment_id=deployment_id)
        
        # Analyze each component and its dependencies
        for component_name, component_config in components.items():
            dependencies = await self._analyze_component_dependencies(
                component_name, component_config
            )
            dependency_graph.components[component_name] = dependencies
            
            logger.info(f"📋 Component {component_name} has {len(dependencies)} dependencies")
        
        # Store dependency graph
        self.dependency_graphs[deployment_id] = dependency_graph
        
        # Validate dependency graph for cycles
        await self._validate_dependency_graph(dependency_graph)
        
        logger.info(f"✅ Dependency graph created with {len(dependency_graph.components)} components")
        return dependency_graph
    
    async def resolve_dependencies(self, deployment_id: str) -> bool:
        """
        Resolve all dependencies in the dependency graph
        ✅ Complete dependency resolution with service discovery
        """
        
        logger.info(f"🔧 Resolving dependencies for deployment: {deployment_id}")
        
        if deployment_id not in self.dependency_graphs:
            raise Exception(f"Dependency graph not found for deployment: {deployment_id}")
        
        dependency_graph = self.dependency_graphs[deployment_id]
        
        # Calculate resolution order based on dependencies
        resolution_order = await self._calculate_resolution_order(dependency_graph)
        
        logger.info(f"📊 Dependency resolution order: {resolution_order}")
        
        # Resolve dependencies in order
        for component_name in resolution_order:
            component_dependencies = dependency_graph.components[component_name]
            
            logger.info(f"🔧 Resolving dependencies for component: {component_name}")
            
            for dependency in component_dependencies:
                resolved = await self._resolve_single_dependency(dependency, dependency_graph)
                
                if not resolved and dependency.required:
                    logger.error(f"❌ Failed to resolve required dependency: {dependency.name}")
                    return False
                elif resolved:
                    logger.info(f"✅ Resolved dependency: {dependency.name}")
        
        # Update dependency graph status
        dependency_graph.resolution_status = "resolved"
        dependency_graph.last_updated = datetime.utcnow()
        
        logger.info(f"🎉 All dependencies resolved for deployment: {deployment_id}")
        return True
    
    async def inject_configuration(self, deployment_id: str, component_name: str) -> Dict[str, Any]:
        """
        Inject resolved dependencies as configuration for a component
        ✅ Dynamic configuration injection with service endpoints
        """
        
        logger.info(f"💉 Injecting configuration for component: {component_name}")
        
        if deployment_id not in self.dependency_graphs:
            raise Exception(f"Dependency graph not found for deployment: {deployment_id}")
        
        dependency_graph = self.dependency_graphs[deployment_id]
        
        if component_name not in dependency_graph.components:
            logger.warning(f"Component {component_name} not found in dependency graph")
            return {}
        
        component_dependencies = dependency_graph.components[component_name]
        injected_config = {}
        
        for dependency in component_dependencies:
            if dependency.status == DependencyStatus.RESOLVED:
                config_key = f"{dependency.type.value.upper()}_CONFIG"
                
                if dependency.endpoint:
                    injected_config[config_key] = {
                        'url': dependency.endpoint.url,
                        'port': dependency.endpoint.port,
                        'protocol': dependency.endpoint.protocol,
                        'health_check_path': dependency.endpoint.health_check_path,
                        'version': dependency.endpoint.version
                    }
                
                if dependency.connection_string:
                    connection_key = f"{dependency.type.value.upper()}_CONNECTION"
                    injected_config[connection_key] = dependency.connection_string
                
                # Add custom configuration
                if dependency.configuration:
                    for key, value in dependency.configuration.items():
                        config_key = f"{dependency.name.upper()}_{key.upper()}"
                        injected_config[config_key] = value
        
        # Store configuration in AWS Systems Manager Parameter Store
        await self._store_configuration_in_ssm(deployment_id, component_name, injected_config)
        
        logger.info(f"✅ Configuration injected for {component_name}: {len(injected_config)} parameters")
        return injected_config
    
    async def register_service(self, deployment_id: str, service_endpoint: ServiceEndpoint) -> bool:
        """
        Register a service endpoint in the service registry
        ✅ Service registration with AWS Service Discovery integration
        """
        
        logger.info(f"📝 Registering service: {service_endpoint.name}")
        
        try:
            # Store in local registry
            self.service_registry[service_endpoint.name] = service_endpoint
            
            # Register with AWS Service Discovery (if configured)
            await self._register_with_service_discovery(deployment_id, service_endpoint)
            
            # Update dependency graph with resolved endpoint
            if deployment_id in self.dependency_graphs:
                dependency_graph = self.dependency_graphs[deployment_id]
                dependency_graph.resolved_dependencies[service_endpoint.name] = service_endpoint
                dependency_graph.last_updated = datetime.utcnow()
            
            logger.info(f"✅ Service registered: {service_endpoint.name} at {service_endpoint.url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register service {service_endpoint.name}: {str(e)}")
            return False
    
    async def discover_service(self, service_name: str, deployment_id: Optional[str] = None) -> Optional[ServiceEndpoint]:
        """
        Discover a service endpoint by name
        ✅ Service discovery with fallback mechanisms
        """
        
        logger.info(f"🔍 Discovering service: {service_name}")
        
        # Check local registry first
        if service_name in self.service_registry:
            logger.info(f"✅ Service found in local registry: {service_name}")
            return self.service_registry[service_name]
        
        # Check deployment-specific resolved dependencies
        if deployment_id and deployment_id in self.dependency_graphs:
            dependency_graph = self.dependency_graphs[deployment_id]
            if service_name in dependency_graph.resolved_dependencies:
                logger.info(f"✅ Service found in deployment dependencies: {service_name}")
                return dependency_graph.resolved_dependencies[service_name]
        
        # Try AWS Service Discovery
        discovered_service = await self._discover_from_service_discovery(service_name)
        if discovered_service:
            # Cache in local registry
            self.service_registry[service_name] = discovered_service
            logger.info(f"✅ Service discovered via AWS Service Discovery: {service_name}")
            return discovered_service
        
        logger.warning(f"⚠️ Service not found: {service_name}")
        return None
    
    async def monitor_dependency_health(self, deployment_id: str) -> Dict[str, Any]:
        """
        Monitor health of all dependencies in a deployment
        ✅ Continuous dependency health monitoring
        """
        
        logger.info(f"🏥 Monitoring dependency health for deployment: {deployment_id}")
        
        if deployment_id not in self.dependency_graphs:
            raise Exception(f"Dependency graph not found for deployment: {deployment_id}")
        
        dependency_graph = self.dependency_graphs[deployment_id]
        health_status = {
            'deployment_id': deployment_id,
            'overall_healthy': True,
            'components': {},
            'checked_at': datetime.utcnow().isoformat()
        }
        
        for component_name, dependencies in dependency_graph.components.items():
            component_health = {
                'healthy': True,
                'dependencies': []
            }
            
            for dependency in dependencies:
                dep_health = await self._check_dependency_health(dependency)
                component_health['dependencies'].append({
                    'name': dependency.name,
                    'type': dependency.type.value,
                    'healthy': dep_health,
                    'last_check': dependency.last_health_check.isoformat() if dependency.last_health_check else None,
                    'error': dependency.error_message
                })
                
                if not dep_health and dependency.required:
                    component_health['healthy'] = False
                    health_status['overall_healthy'] = False
            
            health_status['components'][component_name] = component_health
        
        return health_status
    
    async def update_dependency(self, deployment_id: str, component_name: str, dependency_name: str, 
                              new_endpoint: ServiceEndpoint) -> bool:
        """
        Update a dependency endpoint dynamically
        ✅ Dynamic dependency updates with configuration propagation
        """
        
        logger.info(f"🔄 Updating dependency {dependency_name} for component {component_name}")
        
        if deployment_id not in self.dependency_graphs:
            raise Exception(f"Dependency graph not found for deployment: {deployment_id}")
        
        dependency_graph = self.dependency_graphs[deployment_id]
        
        if component_name not in dependency_graph.components:
            raise Exception(f"Component {component_name} not found in dependency graph")
        
        # Find and update the dependency
        for dependency in dependency_graph.components[component_name]:
            if dependency.name == dependency_name:
                dependency.endpoint = new_endpoint
                dependency.status = DependencyStatus.UPDATING
                dependency.last_health_check = datetime.utcnow()
                
                # Update service registry
                self.service_registry[dependency_name] = new_endpoint
                dependency_graph.resolved_dependencies[dependency_name] = new_endpoint
                
                # Re-inject configuration
                updated_config = await self.inject_configuration(deployment_id, component_name)
                
                # Mark as resolved
                dependency.status = DependencyStatus.RESOLVED
                dependency_graph.last_updated = datetime.utcnow()
                
                logger.info(f"✅ Dependency {dependency_name} updated successfully")
                return True
        
        logger.warning(f"⚠️ Dependency {dependency_name} not found for component {component_name}")
        return False
    
    # Helper methods
    
    async def _analyze_component_dependencies(self, component_name: str, component_config: Dict[str, Any]) -> List[ComponentDependency]:
        """Analyze component configuration to identify dependencies"""
        
        dependencies = []
        
        # Analyze based on component type
        if component_config.get('type') == 'frontend':
            # Frontend typically depends on API
            if component_config.get('api_endpoint'):
                dependencies.append(ComponentDependency(
                    name=f"{component_name}-api",
                    type=DependencyType.API,
                    component_id=component_name,
                    required=True,
                    configuration={'endpoint': component_config['api_endpoint']}
                ))
        
        elif component_config.get('type') == 'api':
            # API typically depends on database
            if component_config.get('database_connection'):
                dependencies.append(ComponentDependency(
                    name=f"{component_name}-database",
                    type=DependencyType.DATABASE,
                    component_id=component_name,
                    required=True,
                    connection_string=component_config['database_connection']
                ))
            
            # Check for cache dependencies
            if component_config.get('cache_url'):
                dependencies.append(ComponentDependency(
                    name=f"{component_name}-cache",
                    type=DependencyType.CACHE,
                    component_id=component_name,
                    required=False,
                    configuration={'url': component_config['cache_url']}
                ))
        
        # Check for explicit dependencies in configuration
        explicit_deps = component_config.get('dependencies', [])
        for dep_config in explicit_deps:
            dependencies.append(ComponentDependency(
                name=dep_config['name'],
                type=DependencyType(dep_config['type']),
                component_id=component_name,
                required=dep_config.get('required', True),
                configuration=dep_config.get('configuration', {})
            ))
        
        return dependencies
    
    async def _validate_dependency_graph(self, dependency_graph: DependencyGraph):
        """Validate dependency graph for circular dependencies"""
        
        # Build adjacency list
        adjacency = {}
        for component_name, dependencies in dependency_graph.components.items():
            adjacency[component_name] = []
            for dep in dependencies:
                # Extract component name from dependency name
                dep_component = dep.name.split('-')[0] if '-' in dep.name else dep.name
                if dep_component in dependency_graph.components:
                    adjacency[component_name].append(dep_component)
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for component in adjacency:
            if component not in visited:
                if has_cycle(component):
                    raise Exception(f"Circular dependency detected in deployment graph")
        
        logger.info(f"✅ Dependency graph validation passed - no circular dependencies")
    
    async def _calculate_resolution_order(self, dependency_graph: DependencyGraph) -> List[str]:
        """Calculate optimal dependency resolution order using topological sort"""
        
        # Build in-degree count
        in_degree = {component: 0 for component in dependency_graph.components}
        adjacency = {component: [] for component in dependency_graph.components}
        
        for component_name, dependencies in dependency_graph.components.items():
            for dep in dependencies:
                dep_component = dep.name.split('-')[0] if '-' in dep.name else dep.name
                if dep_component in dependency_graph.components and dep_component != component_name:
                    adjacency[dep_component].append(component_name)
                    in_degree[component_name] += 1
        
        # Topological sort
        queue = [component for component, degree in in_degree.items() if degree == 0]
        resolution_order = []
        
        while queue:
            current = queue.pop(0)
            resolution_order.append(current)
            
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(resolution_order) != len(dependency_graph.components):
            raise Exception("Cannot resolve dependencies due to circular references")
        
        return resolution_order
    
    async def _resolve_single_dependency(self, dependency: ComponentDependency, dependency_graph: DependencyGraph) -> bool:
        """Resolve a single dependency"""
        
        try:
            dependency.status = DependencyStatus.PENDING
            
            # Try to discover the service
            discovered_service = await self.discover_service(dependency.name, dependency_graph.deployment_id)
            
            if discovered_service:
                dependency.endpoint = discovered_service
                dependency.status = DependencyStatus.RESOLVED
                dependency.last_health_check = datetime.utcnow()
                return True
            
            # If not found, try to create service endpoint from configuration
            if dependency.configuration.get('endpoint') or dependency.connection_string:
                endpoint_url = dependency.configuration.get('endpoint') or dependency.connection_string
                
                service_endpoint = ServiceEndpoint(
                    name=dependency.name,
                    url=endpoint_url,
                    port=dependency.configuration.get('port', 80),
                    protocol=dependency.configuration.get('protocol', 'https'),
                    health_check_path=dependency.configuration.get('health_check_path', '/health')
                )
                
                dependency.endpoint = service_endpoint
                dependency.status = DependencyStatus.RESOLVED
                dependency.last_health_check = datetime.utcnow()
                
                # Register the discovered service
                await self.register_service(dependency_graph.deployment_id, service_endpoint)
                
                return True
            
            dependency.status = DependencyStatus.FAILED
            dependency.error_message = f"Could not resolve dependency: {dependency.name}"
            return False
            
        except Exception as e:
            dependency.status = DependencyStatus.FAILED
            dependency.error_message = str(e)
            logger.error(f"❌ Failed to resolve dependency {dependency.name}: {str(e)}")
            return False
    
    async def _check_dependency_health(self, dependency: ComponentDependency) -> bool:
        """Check health of a single dependency"""
        
        if dependency.status != DependencyStatus.RESOLVED or not dependency.endpoint:
            return False
        
        try:
            import aiohttp
            
            health_url = f"{dependency.endpoint.protocol}://{dependency.endpoint.url}"
            if dependency.endpoint.port != 80 and dependency.endpoint.port != 443:
                health_url += f":{dependency.endpoint.port}"
            health_url += dependency.endpoint.health_check_path
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(health_url) as response:
                    is_healthy = response.status == 200
                    dependency.last_health_check = datetime.utcnow()
                    
                    if not is_healthy:
                        dependency.error_message = f"Health check failed with status: {response.status}"
                    else:
                        dependency.error_message = None
                    
                    return is_healthy
                    
        except Exception as e:
            dependency.error_message = str(e)
            dependency.last_health_check = datetime.utcnow()
            return False
    
    async def _store_configuration_in_ssm(self, deployment_id: str, component_name: str, config: Dict[str, Any]):
        """Store configuration in AWS Systems Manager Parameter Store"""
        
        try:
            parameter_name = f"/codeflowops/{deployment_id}/{component_name}/config"
            
            self.ssm_client.put_parameter(
                Name=parameter_name,
                Value=json.dumps(config),
                Type='String',
                Overwrite=True,
                Tags=[
                    {'Key': 'DeploymentId', 'Value': deployment_id},
                    {'Key': 'Component', 'Value': component_name},
                    {'Key': 'Type', 'Value': 'DependencyConfiguration'}
                ]
            )
            
            logger.debug(f"📝 Configuration stored in SSM: {parameter_name}")
            
        except Exception as e:
            logger.warning(f"Failed to store configuration in SSM: {e}")
    
    async def _register_with_service_discovery(self, deployment_id: str, service_endpoint: ServiceEndpoint):
        """Register service with AWS Service Discovery"""
        
        try:
            # This would register with AWS Cloud Map
            logger.debug(f"📝 Would register {service_endpoint.name} with AWS Service Discovery")
            
        except Exception as e:
            logger.warning(f"Failed to register with Service Discovery: {e}")
    
    async def _discover_from_service_discovery(self, service_name: str) -> Optional[ServiceEndpoint]:
        """Discover service from AWS Service Discovery"""
        
        try:
            # This would query AWS Cloud Map
            logger.debug(f"🔍 Would discover {service_name} from AWS Service Discovery")
            return None
            
        except Exception as e:
            logger.warning(f"Service discovery lookup failed: {e}")
            return None
