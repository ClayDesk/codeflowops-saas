# Phase 1: Integration Layer
# backend/core/phase1_integration.py

"""
Integration layer for Phase 1 enhanced components
This demonstrates how new components work together without affecting existing plugins
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .state_manager_v2 import StateManagerV2, DeploymentState, DeploymentStatus
from .security_manager_v2 import SecurityManagerV2, StackType as SecurityStackType
from .health_checker import HealthChecker, HealthStatus
from .config_manager import ConfigManager, Environment
from ..detectors.enhanced_stack_detector_v2 import EnhancedStackDetectorV2, StackDetectionResult

logger = logging.getLogger(__name__)

class Phase1Integration:
    """
    Integration layer for Phase 1 enhanced components
    ✅ Demonstrates new functionality without breaking existing system
    """
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        
        # Initialize Phase 1 components
        self.state_manager = StateManagerV2()
        self.security_manager = SecurityManagerV2()
        self.health_checker = HealthChecker()
        self.config_manager = ConfigManager(environment)
        self.stack_detector = EnhancedStackDetectorV2()
        
        logger.info(f"✅ Phase 1 integration initialized for {environment.value}")
    
    async def enhanced_deployment_workflow(
        self, 
        repository_path: str, 
        deployment_id: str,
        project_name: str
    ) -> Dict[str, Any]:
        """
        Enhanced deployment workflow using Phase 1 components
        ✅ New workflow that coexists with existing ReactPlugin, NextJSPlugin, StaticSitePlugin
        """
        
        workflow_result = {
            'deployment_id': deployment_id,
            'status': 'started',
            'steps_completed': [],
            'errors': [],
            'stack_detection': None,
            'security_config': None,
            'health_status': None
        }
        
        try:
            # Step 1: Enhanced Stack Detection
            logger.info(f"🔍 Step 1: Enhanced stack detection for {repository_path}")
            
            stack_result = self.stack_detector.detect_stack(repository_path)
            workflow_result['stack_detection'] = {
                'primary_stack': stack_result.primary_stack.value,
                'runtime': stack_result.runtime.value,
                'confidence': stack_result.confidence_score,
                'secondary_stacks': [s.value for s in stack_result.secondary_stacks],
                'database_dependencies': [d.value for d in stack_result.database_dependencies]
            }
            workflow_result['steps_completed'].append('stack_detection')
            
            # Step 2: Initialize Enhanced State Management
            logger.info(f"📊 Step 2: Initialize enhanced state management")
            
            initial_state = DeploymentState(
                deployment_id=deployment_id,
                status=DeploymentStatus.DETECTING,
                stack_type=stack_result.primary_stack.value,
                runtime=stack_result.runtime.value,
                metadata={
                    'project_name': project_name,
                    'confidence_score': stack_result.confidence_score,
                    'detected_files': stack_result.detected_files[:10],  # Limit for storage
                    'build_tools': stack_result.build_tools,
                    'database_dependencies': [d.value for d in stack_result.database_dependencies]
                }
            )
            
            await self.state_manager.create_deployment_state(initial_state)
            workflow_result['steps_completed'].append('state_initialization')
            
            # Step 3: Security Policy Generation
            logger.info(f"🔒 Step 3: Generate security policies")
            
            # Map stack type to security stack type
            security_stack = self._map_to_security_stack(stack_result.primary_stack.value)
            
            # Generate least-privilege IAM policy
            security_policy = self.security_manager.generate_least_privilege_policy(
                security_stack, 
                [f"arn:aws:s3:::codeflowops-{project_name}-*"]
            )
            
            workflow_result['security_config'] = {
                'policy_generated': True,
                'stack_type': security_stack.value,
                'actions_count': len(security_policy['Statement'][0]['Action'])
            }
            workflow_result['steps_completed'].append('security_policy')
            
            # Step 4: Configuration Validation
            logger.info(f"⚙️ Step 4: Validate configuration")
            
            config_errors = self.config_manager.validate_configuration()
            if config_errors:
                workflow_result['errors'].extend([f"Config: {error}" for errors in config_errors.values() for error in errors])
            else:
                workflow_result['steps_completed'].append('config_validation')
            
            # Step 5: Update deployment state to building
            await self.state_manager.update_deployment_state(
                deployment_id, 
                DeploymentStatus.BUILDING,
                {'phase1_integration': 'completed', 'security_policy_generated': True}
            )
            
            # Step 6: Health Check Setup (for existing deployments)
            if await self._deployment_has_url(deployment_id):
                logger.info(f"🏥 Step 6: Initial health check")
                
                deployment_url = await self._get_deployment_url(deployment_id)
                if deployment_url:
                    health_results = await self.health_checker.check_application_health(
                        deployment_url, 
                        stack_result.primary_stack.value
                    )
                    
                    overall_health = all(r.status == HealthStatus.HEALTHY for r in health_results)
                    workflow_result['health_status'] = {
                        'overall_healthy': overall_health,
                        'services_checked': len(health_results),
                        'healthy_services': sum(1 for r in health_results if r.status == HealthStatus.HEALTHY)
                    }
                    workflow_result['steps_completed'].append('health_check')
            
            workflow_result['status'] = 'completed'
            logger.info(f"✅ Enhanced deployment workflow completed for {deployment_id}")
            
        except Exception as e:
            logger.error(f"❌ Enhanced deployment workflow failed: {e}")
            workflow_result['status'] = 'failed'
            workflow_result['errors'].append(str(e))
            
            # Update state to failed
            try:
                await self.state_manager.update_deployment_state(
                    deployment_id,
                    DeploymentStatus.FAILED,
                    {'error': str(e), 'phase1_integration': 'failed'}
                )
            except Exception as state_error:
                logger.error(f"Failed to update state: {state_error}")
        
        return workflow_result
    
    async def get_enhanced_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get enhanced deployment status with comprehensive information
        ✅ New API endpoint functionality
        """
        
        try:
            # Get state from enhanced state manager
            state = await self.state_manager.get_deployment_state(deployment_id)
            
            if not state:
                return {
                    'deployment_id': deployment_id,
                    'found': False,
                    'error': 'Deployment not found in enhanced state manager'
                }
            
            result = {
                'deployment_id': deployment_id,
                'found': True,
                'status': state.status.value,
                'stack_type': state.stack_type,
                'runtime': state.runtime,
                'created_at': state.created_at.isoformat(),
                'last_updated': state.last_updated.isoformat(),
                'metadata': state.metadata,
                'health_status': None,
                'security_info': None
            }
            
            # Add health check if deployment has URL
            if await self._deployment_has_url(deployment_id):
                deployment_url = await self._get_deployment_url(deployment_id)
                if deployment_url:
                    try:
                        health_results = await self.health_checker.check_application_health(
                            deployment_url, 
                            state.stack_type
                        )
                        
                        health_report = self.health_checker.generate_health_report(health_results)
                        result['health_status'] = health_report
                        
                    except Exception as e:
                        result['health_status'] = {'error': str(e)}
            
            # Add security information
            try:
                deployment_config = self.config_manager.get_deployment_config()
                security_config = self.config_manager.get_security_config()
                
                result['security_info'] = {
                    'environment': deployment_config.environment.value,
                    'encryption_at_rest': security_config.encryption_at_rest,
                    'encryption_in_transit': security_config.encryption_in_transit,
                    'vpc_enabled': bool(security_config.vpc_id)
                }
                
            except Exception as e:
                result['security_info'] = {'error': str(e)}
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get enhanced deployment status: {e}")
            return {
                'deployment_id': deployment_id,
                'found': False,
                'error': str(e)
            }
    
    async def setup_monitoring_for_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """
        Setup comprehensive monitoring for a deployment
        ✅ Enhanced monitoring without affecting existing systems
        """
        
        try:
            state = await self.state_manager.get_deployment_state(deployment_id)
            if not state:
                return {'success': False, 'error': 'Deployment not found'}
            
            monitoring_config = self.config_manager.get_monitoring_config()
            
            setup_result = {
                'deployment_id': deployment_id,
                'success': True,
                'monitoring_components': []
            }
            
            # Setup CloudWatch metrics
            if monitoring_config.enable_cloudwatch:
                # This would integrate with actual CloudWatch setup
                setup_result['monitoring_components'].append('cloudwatch_metrics')
            
            # Setup health monitoring
            if await self._deployment_has_url(deployment_id):
                deployment_url = await self._get_deployment_url(deployment_id)
                if deployment_url:
                    # Perform initial health check and publish metrics
                    health_results = await self.health_checker.check_application_health(
                        deployment_url,
                        state.stack_type
                    )
                    
                    self.health_checker.publish_metrics_to_cloudwatch(
                        health_results,
                        monitoring_config.custom_metrics_namespace
                    )
                    
                    setup_result['monitoring_components'].append('health_monitoring')
            
            # Update deployment state with monitoring info
            await self.state_manager.update_deployment_state(
                deployment_id,
                state.status,  # Keep current status
                {
                    **state.metadata,
                    'monitoring_enabled': True,
                    'monitoring_components': setup_result['monitoring_components']
                }
            )
            
            logger.info(f"✅ Monitoring setup completed for {deployment_id}")
            return setup_result
            
        except Exception as e:
            logger.error(f"Failed to setup monitoring: {e}")
            return {'success': False, 'error': str(e)}
    
    def _map_to_security_stack(self, stack_type: str) -> SecurityStackType:
        """Map detection stack type to security stack type"""
        
        mapping = {
            'react': SecurityStackType.REACT,
            'nextjs': SecurityStackType.NEXTJS,
            'static': SecurityStackType.STATIC,
            'api-nodejs': SecurityStackType.API_NODEJS,
            'api-python': SecurityStackType.API_PYTHON,
            'api-php': SecurityStackType.API_PHP,
            'api-java': SecurityStackType.API_JAVA,
            'database-mysql': SecurityStackType.DATABASE_MYSQL,
            'database-postgresql': SecurityStackType.DATABASE_POSTGRESQL,
            'database-mongodb': SecurityStackType.DATABASE_MONGODB,
        }
        
        return mapping.get(stack_type, SecurityStackType.STATIC)
    
    async def _deployment_has_url(self, deployment_id: str) -> bool:
        """Check if deployment has an accessible URL (placeholder)"""
        # This would integrate with existing deployment tracking
        # For now, assume all deployments eventually have URLs
        return True
    
    async def _get_deployment_url(self, deployment_id: str) -> Optional[str]:
        """Get deployment URL (placeholder)"""
        # This would integrate with existing deployment URL tracking
        # For demonstration, return a placeholder URL
        return f"https://{deployment_id}.codeflowops-demo.com"

# Example usage function
async def demonstrate_phase1_integration():
    """
    Demonstrate Phase 1 integration capabilities
    ✅ Shows how new components work together
    """
    
    print("🚀 Phase 1 Integration Demonstration")
    print("=" * 50)
    
    # Initialize integration layer
    integration = Phase1Integration(Environment.DEVELOPMENT)
    
    # Example repository path (would be actual repo in real usage)
    repo_path = "/path/to/example/react-app"
    deployment_id = "demo-deployment-123"
    project_name = "example-react-app"
    
    # Run enhanced deployment workflow
    print("📋 Running enhanced deployment workflow...")
    workflow_result = await integration.enhanced_deployment_workflow(
        repo_path, deployment_id, project_name
    )
    
    print(f"✅ Workflow Status: {workflow_result['status']}")
    print(f"📊 Steps Completed: {', '.join(workflow_result['steps_completed'])}")
    
    if workflow_result['stack_detection']:
        detection = workflow_result['stack_detection']
        print(f"🔍 Detected Stack: {detection['primary_stack']} ({detection['confidence']:.2f} confidence)")
    
    # Get enhanced status
    print("\n📋 Getting enhanced deployment status...")
    status = await integration.get_enhanced_deployment_status(deployment_id)
    print(f"📊 Status: {status.get('status', 'unknown')}")
    
    # Setup monitoring
    print("\n🏥 Setting up monitoring...")
    monitoring_result = await integration.setup_monitoring_for_deployment(deployment_id)
    print(f"✅ Monitoring Setup: {monitoring_result['success']}")
    
    print("\n🎉 Phase 1 integration demonstration complete!")

if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_phase1_integration())
