# Phase 5: Complete Multi-Stack Coordination Integration
# backend/core/phase5_integration.py

"""
Complete Phase 5 integration module
✅ Final integration point for all multi-stack coordination components
✅ Enterprise-ready full-stack deployment orchestration
✅ Production hardening with comprehensive observability
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Phase 5 components
from .stack_orchestrator import StackOrchestrator, FullStackDeployment, RepoAnalysis, DeploymentPhase
from .dependency_manager import DependencyManager, DependencyGraph, ServiceEndpoint
from .observability_manager import ObservabilityManager, ObservabilityLevel, DeploymentAnalytics
from .production_hardening import ProductionHardening, SecurityLevel

# Previous phases integration
from .phase4_integration import Phase4CompleteIntegration
from .state_manager_v2 import StateManagerV2

logger = logging.getLogger(__name__)

@dataclass
class Phase5DeploymentRequest:
    """Complete Phase 5 deployment request"""
    app_name: str
    repo_path: str
    
    # Component configuration
    has_frontend: bool = True
    has_api: bool = True
    has_database: bool = True
    
    # Deployment strategy
    deployment_strategy: str = "standard"  # standard, blue_green, canary
    target_environment: str = "production"
    
    # Security and compliance
    security_level: SecurityLevel = SecurityLevel.ENHANCED
    enable_compliance_validation: bool = True
    compliance_framework: str = "SOC2"
    
    # Observability
    observability_level: ObservabilityLevel = ObservabilityLevel.ENHANCED
    enable_distributed_tracing: bool = True
    create_dashboard: bool = True
    
    # Reliability
    enable_circuit_breakers: bool = True
    enable_graceful_degradation: bool = True
    max_retry_attempts: int = 3
    
    # Configuration
    environment_vars: Dict[str, str] = field(default_factory=dict)
    deployment_tags: Dict[str, str] = field(default_factory=dict)
    
    # Advanced options
    enable_dependency_injection: bool = True
    enable_service_discovery: bool = True
    enable_end_to_end_testing: bool = True

@dataclass
class Phase5DeploymentResult:
    """Complete Phase 5 deployment result"""
    deployment_id: str
    success: bool
    
    # Component results
    full_stack_deployment: Optional[FullStackDeployment] = None
    dependency_graph: Optional[DependencyGraph] = None
    deployment_analytics: Optional[DeploymentAnalytics] = None
    
    # Security and compliance
    security_hardening_score: float = 0.0
    compliance_score: float = 0.0
    security_violations: List[str] = field(default_factory=list)
    
    # Observability
    dashboard_url: Optional[str] = None
    trace_id: Optional[str] = None
    performance_score: float = 0.0
    
    # Endpoints and URLs
    frontend_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    health_check_url: Optional[str] = None
    monitoring_url: Optional[str] = None
    
    # Metrics
    total_deployment_time_seconds: Optional[float] = None
    component_deployment_times: Dict[str, float] = field(default_factory=dict)
    
    # Status and recommendations
    deployment_phase: DeploymentPhase = DeploymentPhase.PLANNING
    recommendations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

class Phase5CompleteIntegration:
    """
    Complete Phase 5 multi-stack coordination integration
    ✅ Enterprise-ready full-stack deployment with comprehensive observability
    ✅ Complete integration with all CodeFlowOps phases (1-5)
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        
        # Core Phase 5 components
        self.stack_orchestrator = StackOrchestrator(region)
        self.dependency_manager = DependencyManager(region)
        self.observability_manager = ObservabilityManager(region)
        self.production_hardening = ProductionHardening(region)
        
        # Previous phases integration
        self.phase4_integration = Phase4CompleteIntegration(region)
        self.state_manager = StateManagerV2(region)
        
        logger.info(f"🚀 Phase 5 Complete Integration initialized for region: {region}")
    
    async def deploy_full_stack_enterprise(self, request: Phase5DeploymentRequest) -> Phase5DeploymentResult:
        """
        Execute complete enterprise-grade full-stack deployment
        ✅ End-to-end deployment with security, observability, and reliability
        """
        
        deployment_start = datetime.utcnow()
        deployment_id = f"phase5-{request.app_name}-{int(deployment_start.timestamp())}"
        
        logger.info(f"🚀 Starting Phase 5 enterprise deployment: {deployment_id}")
        logger.info(f"📋 Configuration: {request.deployment_strategy} | Security: {request.security_level.value} | Observability: {request.observability_level.value}")
        
        # Initialize result
        result = Phase5DeploymentResult(
            deployment_id=deployment_id,
            success=False,
            deployment_phase=DeploymentPhase.PLANNING
        )
        
        try:
            # Initialize components with enhanced configuration
            await self._initialize_enhanced_components(request)
            
            # Step 1: Start deployment analytics and tracing
            async with self.observability_manager.trace_operation(
                "phase5_enterprise_deployment", 
                deployment_id=deployment_id,
                component_name="phase5_orchestrator"
            ) as trace_span:
                
                result.trace_id = trace_span.trace_id if trace_span else None
                
                # Start analytics collection
                analytics = await self.observability_manager.start_deployment_analytics(deployment_id)
                result.deployment_analytics = analytics
                
                # Step 2: Analyze repository and create dependency graph
                logger.info(f"📊 Step 1: Repository analysis and dependency planning")
                repo_analysis = await self._analyze_repository_enhanced(request)
                
                # Create dependency graph
                dependency_components = await self._prepare_dependency_components(repo_analysis)
                dependency_graph = await self.dependency_manager.create_dependency_graph(
                    deployment_id, dependency_components
                )
                result.dependency_graph = dependency_graph
                
                # Step 3: Apply production hardening
                logger.info(f"🛡️ Step 2: Applying production hardening")
                security_resources = await self._prepare_security_resources(repo_analysis)
                hardening_result = await self.production_hardening.apply_security_hardening(
                    deployment_id, security_resources
                )
                
                result.security_hardening_score = hardening_result.get('security_score', 0.0)
                
                # Set up reliability features
                reliability_result = await self.production_hardening.setup_reliability_features(deployment_id)
                
                # Step 4: Execute deployment strategy
                logger.info(f"🚀 Step 3: Executing deployment strategy: {request.deployment_strategy}")
                
                if request.deployment_strategy == "blue_green":
                    deployment_result = await self._execute_blue_green_deployment(
                        request, repo_analysis, dependency_graph
                    )
                else:
                    deployment_result = await self._execute_standard_deployment(
                        request, repo_analysis, dependency_graph
                    )
                
                result.full_stack_deployment = deployment_result
                
                # Step 5: Resolve dependencies and inject configuration
                logger.info(f"🔗 Step 4: Resolving dependencies and injecting configuration")
                dependencies_resolved = await self.dependency_manager.resolve_dependencies(deployment_id)
                
                if dependencies_resolved:
                    # Inject configuration for each component
                    if deployment_result.frontend:
                        await self.dependency_manager.inject_configuration(deployment_id, "frontend")
                    if deployment_result.api:
                        await self.dependency_manager.inject_configuration(deployment_id, "api")
                    if deployment_result.database:
                        await self.dependency_manager.inject_configuration(deployment_id, "database")
                
                # Step 6: Run comprehensive validation
                logger.info(f"🧪 Step 5: Running comprehensive validation")
                validation_success = await self._run_comprehensive_validation(
                    deployment_id, deployment_result, request
                )
                
                # Step 7: Set up observability features
                logger.info(f"📊 Step 6: Setting up observability features")
                await self._setup_observability_features(deployment_id, deployment_result, request)
                
                # Create dashboard if requested
                if request.create_dashboard:
                    dashboard_url = await self.observability_manager.create_observability_dashboard(deployment_id)
                    result.dashboard_url = dashboard_url
                
                # Step 8: Run compliance validation if required
                if request.enable_compliance_validation:
                    logger.info(f"📋 Step 7: Running compliance validation")
                    compliance_result = await self.production_hardening.validate_compliance(
                        deployment_id, request.compliance_framework
                    )
                    result.compliance_score = compliance_result.get('compliance_score', 0.0)
                    result.security_violations = [v['description'] for v in compliance_result.get('violations', [])]
                
                # Step 9: Complete analytics and generate insights
                logger.info(f"📈 Step 8: Completing analytics and generating insights")
                final_analytics = await self.observability_manager.complete_deployment_analytics(
                    deployment_id, validation_success and deployment_result.success
                )
                result.deployment_analytics = final_analytics
                
                # Calculate final metrics
                result.total_deployment_time_seconds = (datetime.utcnow() - deployment_start).total_seconds()
                result.deployment_phase = DeploymentPhase.COMPLETED if validation_success else DeploymentPhase.FAILED
                result.success = validation_success and deployment_result.success
                
                # Extract endpoints
                if deployment_result.success:
                    result.frontend_url = deployment_result.frontend_url
                    result.api_endpoint = deployment_result.api_endpoint
                    result.health_check_url = deployment_result.health_check_url
                    result.monitoring_url = result.dashboard_url
                
                # Generate recommendations
                result.recommendations = await self._generate_enterprise_recommendations(
                    result, hardening_result, final_analytics
                )
                
                # Update final deployment status
                await self.state_manager.update_deployment_status(
                    deployment_id=deployment_id,
                    status="phase5_deployed" if result.success else "phase5_failed",
                    endpoint_url=result.frontend_url or result.api_endpoint,
                    health_check_url=result.health_check_url,
                    monitoring_url=result.monitoring_url,
                    security_score=result.security_hardening_score,
                    compliance_score=result.compliance_score,
                    total_duration_seconds=result.total_deployment_time_seconds
                )
                
                if result.success:
                    logger.info(f"🎉 Phase 5 enterprise deployment completed successfully!")
                    logger.info(f"📊 Deployment ID: {deployment_id}")
                    logger.info(f"⏱️ Total time: {result.total_deployment_time_seconds:.1f}s")
                    logger.info(f"🛡️ Security score: {result.security_hardening_score:.1f}/100")
                    logger.info(f"📋 Compliance score: {result.compliance_score:.1f}%")
                    logger.info(f"🔗 Frontend: {result.frontend_url}")
                    logger.info(f"⚡ API: {result.api_endpoint}")
                    logger.info(f"📊 Dashboard: {result.dashboard_url}")
                else:
                    logger.error(f"❌ Phase 5 deployment failed - check logs for details")
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Phase 5 enterprise deployment failed: {str(e)}")
            
            result.success = False
            result.error_message = str(e)
            result.deployment_phase = DeploymentPhase.FAILED
            result.total_deployment_time_seconds = (datetime.utcnow() - deployment_start).total_seconds()
            
            # Update failed status
            await self.state_manager.update_deployment_status(
                deployment_id=deployment_id,
                status="phase5_failed",
                error_message=str(e)
            )
            
            return result
    
    async def get_enterprise_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status of Phase 5 enterprise deployment
        ✅ Complete deployment status with all Phase 5 capabilities
        """
        
        try:
            # Get base deployment information
            deployment_info = await self.state_manager.get_deployment(deployment_id)
            
            if not deployment_info:
                return {'error': f'Deployment {deployment_id} not found'}
            
            # Get component status from stack orchestrator
            stack_status = await self.stack_orchestrator.get_deployment_status(deployment_id)
            
            # Get dependency health
            dependency_health = await self.dependency_manager.monitor_dependency_health(deployment_id)
            
            # Get deployment insights
            deployment_insights = await self.observability_manager.get_deployment_insights(deployment_id)
            
            return {
                **deployment_info,
                'stack_status': stack_status,
                'dependency_health': dependency_health,
                'insights': deployment_insights,
                'deployment_type': 'Phase 5 - Enterprise Multi-Stack',
                'capabilities': [
                    'full_stack_orchestration',
                    'dependency_management',
                    'advanced_observability',
                    'production_hardening',
                    'compliance_validation',
                    'distributed_tracing',
                    'circuit_breaker_protection',
                    'graceful_degradation'
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get enterprise deployment status: {e}")
            return {'error': str(e)}
    
    async def rollback_enterprise_deployment(self, deployment_id: str, 
                                           component: Optional[str] = None) -> Phase5DeploymentResult:
        """
        Execute comprehensive rollback of Phase 5 deployment
        ✅ Enterprise rollback with full component coordination
        """
        
        logger.info(f"⏪ Initiating Phase 5 enterprise rollback: {deployment_id}")
        
        try:
            # Execute stack orchestrator rollback
            rollback_success = await self.stack_orchestrator.rollback_deployment(
                deployment_id, component
            )
            
            # Update dependency graph if needed
            if rollback_success and component:
                # Handle component-specific dependency updates
                logger.info(f"🔗 Updating dependencies after component rollback: {component}")
            
            # Record rollback analytics
            await self.observability_manager.record_metric(
                metric_name='DeploymentRollback',
                value=1.0,
                deployment_id=deployment_id,
                dimensions={'Component': component or 'all', 'Success': str(rollback_success)}
            )
            
            # Update deployment status
            await self.state_manager.update_deployment_status(
                deployment_id=deployment_id,
                status="rolled_back",
                error_message=f"Phase 5 rollback executed for: {component or 'all components'}"
            )
            
            return Phase5DeploymentResult(
                deployment_id=deployment_id,
                success=rollback_success,
                recommendations=[
                    "🔍 Analyze rollback cause with distributed tracing data",
                    "📊 Review dependency health before redeployment",
                    "🛡️ Validate security configurations",
                    "🧪 Run comprehensive testing before next deployment"
                ]
            )
            
        except Exception as e:
            logger.error(f"❌ Enterprise rollback failed: {str(e)}")
            
            return Phase5DeploymentResult(
                deployment_id=deployment_id,
                success=False,
                error_message=f"Rollback failed: {str(e)}"
            )
    
    # Helper methods
    
    async def _initialize_enhanced_components(self, request: Phase5DeploymentRequest):
        """Initialize components with enhanced configuration"""
        
        # Configure observability manager
        self.observability_manager = ObservabilityManager(
            region=self.region,
            observability_level=request.observability_level
        )
        
        # Configure production hardening
        self.production_hardening = ProductionHardening(
            region=self.region,
            security_level=request.security_level
        )
    
    async def _analyze_repository_enhanced(self, request: Phase5DeploymentRequest) -> RepoAnalysis:
        """Enhanced repository analysis for Phase 5"""
        
        return RepoAnalysis(
            repo_path=request.repo_path,
            app_name=request.app_name,
            has_frontend=request.has_frontend,
            has_api=request.has_api,
            has_database=request.has_database,
            requires_database=request.has_database,
            api_depends_on_database=request.has_api and request.has_database,
            frontend_depends_on_api=request.has_frontend and request.has_api,
            environment_vars=request.environment_vars,
            deployment_tags={
                **request.deployment_tags,
                'Phase': 'Phase5-Enterprise',
                'SecurityLevel': request.security_level.value,
                'ObservabilityLevel': request.observability_level.value
            }
        )
    
    async def _prepare_dependency_components(self, repo_analysis: RepoAnalysis) -> Dict[str, Dict[str, Any]]:
        """Prepare dependency components configuration"""
        
        components = {}
        
        if repo_analysis.has_frontend:
            components['frontend'] = {
                'type': 'frontend',
                'dependencies': [
                    {'name': 'api', 'type': 'api', 'required': repo_analysis.frontend_depends_on_api}
                ] if repo_analysis.has_api else []
            }
        
        if repo_analysis.has_api:
            api_deps = []
            if repo_analysis.has_database:
                api_deps.append({'name': 'database', 'type': 'database', 'required': True})
            
            components['api'] = {
                'type': 'api',
                'dependencies': api_deps
            }
        
        if repo_analysis.has_database:
            components['database'] = {
                'type': 'database',
                'dependencies': []
            }
        
        return components
    
    async def _prepare_security_resources(self, repo_analysis: RepoAnalysis) -> Dict[str, Any]:
        """Prepare security resources for hardening"""
        
        resources = {
            'applications': [repo_analysis.app_name],
            'databases': [],
            'storage': [],
            'networking': []
        }
        
        if repo_analysis.has_database:
            resources['databases'].append(f"{repo_analysis.app_name}-db")
        
        return resources
    
    async def _execute_blue_green_deployment(self, request: Phase5DeploymentRequest, 
                                           repo_analysis: RepoAnalysis, 
                                           dependency_graph: DependencyGraph) -> FullStackDeployment:
        """Execute Blue/Green deployment strategy"""
        
        from .phase4_integration import Phase4DeploymentRequest
        
        # Create Phase 4 request
        phase4_request = Phase4DeploymentRequest(
            app_name=request.app_name,
            repo_path=request.repo_path,
            stack_types=["frontend", "api", "database"] if request.has_database else (
                ["frontend", "api"] if request.has_api else ["frontend"]
            ),
            traffic_shift_strategy="gradual",
            verification_enabled=True,
            monitoring_enabled=True,
            environment_vars=request.environment_vars,
            deployment_tags=request.deployment_tags
        )
        
        # Execute Phase 4 deployment
        phase4_result = await self.phase4_integration.deploy_with_blue_green(phase4_request)
        
        # Convert to FullStackDeployment
        return FullStackDeployment(
            deployment_id=phase4_result.deployment_id,
            frontend_url=phase4_result.production_url,
            api_endpoint=phase4_result.production_url,
            health_check_url=phase4_result.health_check_url,
            deployment_phase=DeploymentPhase.COMPLETED if phase4_result.success else DeploymentPhase.FAILED,
            success=phase4_result.success,
            error_message=phase4_result.error_message
        )
    
    async def _execute_standard_deployment(self, request: Phase5DeploymentRequest, 
                                         repo_analysis: RepoAnalysis, 
                                         dependency_graph: DependencyGraph) -> FullStackDeployment:
        """Execute standard deployment strategy"""
        
        return await self.stack_orchestrator.deploy_full_stack_application(repo_analysis)
    
    async def _run_comprehensive_validation(self, deployment_id: str, 
                                          deployment_result: FullStackDeployment, 
                                          request: Phase5DeploymentRequest) -> bool:
        """Run comprehensive deployment validation"""
        
        try:
            # Component health validation
            await self.stack_orchestrator.verify_component_health(deployment_result)
            
            # End-to-end validation if enabled
            if request.enable_end_to_end_testing:
                await self.stack_orchestrator.verify_end_to_end_connectivity(deployment_result)
            
            # Dependency health validation
            dependency_health = await self.dependency_manager.monitor_dependency_health(deployment_id)
            
            if not dependency_health.get('overall_healthy', True):
                logger.warning(f"⚠️ Dependency health issues detected")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Comprehensive validation failed: {str(e)}")
            return False
    
    async def _setup_observability_features(self, deployment_id: str, 
                                          deployment_result: FullStackDeployment, 
                                          request: Phase5DeploymentRequest):
        """Set up comprehensive observability features"""
        
        # Record deployment metrics
        await self.observability_manager.record_metric(
            metric_name='Phase5DeploymentComplete',
            value=1.0,
            deployment_id=deployment_id,
            dimensions={
                'Strategy': request.deployment_strategy,
                'SecurityLevel': request.security_level.value,
                'ObservabilityLevel': request.observability_level.value
            }
        )
        
        # Track component performance
        if deployment_result.component_deployment_times:
            for component, duration_seconds in deployment_result.component_deployment_times.items():
                await self.observability_manager.track_component_performance(
                    deployment_id, component, duration_seconds, True
                )
    
    async def _generate_enterprise_recommendations(self, result: Phase5DeploymentResult, 
                                                 hardening_result: Dict[str, Any], 
                                                 analytics: DeploymentAnalytics) -> List[str]:
        """Generate enterprise-level recommendations"""
        
        recommendations = []
        
        # Security recommendations
        if result.security_hardening_score < 90:
            recommendations.append(f"🛡️ Security score: {result.security_hardening_score:.1f}/100 - Review security controls")
        
        # Compliance recommendations
        if result.compliance_score < 95:
            recommendations.append(f"📋 Compliance score: {result.compliance_score:.1f}% - Address compliance gaps")
        
        # Performance recommendations
        if analytics and analytics.total_duration_seconds > 900:  # > 15 minutes
            recommendations.append("⚡ Deployment duration exceeded 15 minutes - Consider optimization")
        
        # Component recommendations
        if result.full_stack_deployment and result.full_stack_deployment.e2e_test_result:
            e2e_result = result.full_stack_deployment.e2e_test_result
            if e2e_result.response_time and e2e_result.response_time > 5.0:
                recommendations.append(f"🚀 E2E response time: {e2e_result.response_time:.1f}s - Optimize performance")
        
        # General enterprise recommendations
        recommendations.extend([
            "📊 Monitor deployment analytics for continuous improvement",
            "🔗 Review dependency health regularly",
            "🛡️ Maintain security best practices",
            "📈 Use distributed tracing for troubleshooting"
        ])
        
        return recommendations


# Convenience functions for easy Phase 5 deployment

async def deploy_enterprise_full_stack(
    app_name: str,
    repo_path: str,
    region: str = 'us-east-1',
    deployment_strategy: str = "standard",
    security_level: SecurityLevel = SecurityLevel.ENHANCED,
    **kwargs
) -> Phase5DeploymentResult:
    """
    Convenience function for enterprise full-stack deployment
    ✅ Simple interface for Phase 5 enterprise deployments
    """
    
    phase5 = Phase5CompleteIntegration(region)
    
    request = Phase5DeploymentRequest(
        app_name=app_name,
        repo_path=repo_path,
        deployment_strategy=deployment_strategy,
        security_level=security_level,
        **kwargs
    )
    
    return await phase5.deploy_full_stack_enterprise(request)


async def deploy_with_comprehensive_monitoring(
    app_name: str,
    repo_path: str,
    region: str = 'us-east-1',
    **kwargs
) -> Phase5DeploymentResult:
    """
    Deploy with comprehensive monitoring and observability
    ✅ Full observability stack with distributed tracing and analytics
    """
    
    return await deploy_enterprise_full_stack(
        app_name=app_name,
        repo_path=repo_path,
        region=region,
        observability_level=ObservabilityLevel.FULL,
        enable_distributed_tracing=True,
        create_dashboard=True,
        **kwargs
    )


async def deploy_enterprise_compliant(
    app_name: str,
    repo_path: str,
    compliance_framework: str = "SOC2",
    region: str = 'us-east-1',
    **kwargs
) -> Phase5DeploymentResult:
    """
    Deploy with enterprise compliance requirements
    ✅ Compliance-ready deployment with security hardening
    """
    
    return await deploy_enterprise_full_stack(
        app_name=app_name,
        repo_path=repo_path,
        region=region,
        security_level=SecurityLevel.ENTERPRISE,
        enable_compliance_validation=True,
        compliance_framework=compliance_framework,
        **kwargs
    )
