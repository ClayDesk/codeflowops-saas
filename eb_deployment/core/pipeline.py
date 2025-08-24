"""
Pipeline orchestrator - coordinates the full deployment process
"""
import time
import logging
from pathlib import Path
from typing import Optional
from .registry import get_stack, detect_stack
from .models import AnalysisResult, StackPlan, BuildResult, ProvisionResult, DeployResult, DeploymentSession

logger = logging.getLogger(__name__)

class Pipeline:
    """Orchestrates the complete deployment pipeline"""
    
    def __init__(self, stack_key: Optional[str] = None):
        """
        Initialize pipeline for a specific stack or auto-detect
        
        Args:
            stack_key: Force specific stack, or None for auto-detection
        """
        self.stack_key = stack_key
        self.session: Optional[DeploymentSession] = None
        
    def run_full_deployment(
        self, 
        analysis: AnalysisResult, 
        credentials: dict,
        stack_override: Optional[str] = None
    ) -> DeployResult:
        """
        Run the complete deployment pipeline: detect → build → provision → deploy
        
        Args:
            analysis: Repository analysis result
            credentials: AWS credentials
            stack_override: Override auto-detected stack
            
        Returns:
            Final deployment result
        """
        start_time = time.time()
        
        # Create deployment session
        self.session = DeploymentSession(analysis=analysis, status="starting")
        
        try:
            # Phase 1: Stack Detection
            logger.info("🔍 Phase 1: Stack Detection")
            self.session.status = "detecting"
            
            stack_key = stack_override or self.stack_key
            if stack_key:
                # Use specified stack
                stack_components = get_stack(stack_key)
                if not stack_components:
                    raise ValueError(f"Stack '{stack_key}' not found")
                    
                # Create context with repository URL and analysis
                context = {
                    'repo_url': analysis.repo_url,
                    'analysis': analysis
                }
                
                # Create plan for specified stack
                plan = stack_components.detector.detect(analysis.repo_dir, context)
                if not plan:
                    # Create default plan if detector doesn't match
                    plan = StackPlan(
                        stack_key=stack_key,
                        build_cmds=["echo 'no-op'"],
                        output_dir=analysis.repo_dir,
                        config={'repository_url': analysis.repo_url}
                    )
            else:
                # Auto-detect stack with context
                context = {
                    'repo_url': analysis.repo_url,
                    'analysis': analysis
                }
                plan = detect_stack(analysis.repo_dir, context)
                if not plan:
                    raise ValueError("No suitable stack detected for repository")
                    
                # Add repository URL to plan config if not present
                if 'repository_url' not in plan.config:
                    plan.config['repository_url'] = analysis.repo_url
                    
                stack_components = get_stack(plan.stack_key)
                if not stack_components:
                    raise ValueError(f"Stack '{plan.stack_key}' not registered")
            
            self.session.plan = plan
            logger.info(f"✅ Using stack: {plan.stack_key}")
            
            # Phase 2: Build
            logger.info("🔨 Phase 2: Building Application")
            self.session.status = "building"
            
            build_start = time.time()
            build_result = stack_components.builder.build(plan, analysis.repo_dir)
            build_result.build_time_seconds = time.time() - build_start
            
            if not build_result.success:
                self.session.status = "build_failed"
                return DeployResult(
                    success=False,
                    live_url="",
                    error_message=f"Build failed: {build_result.error_message}",
                    deploy_time_seconds=time.time() - start_time
                )
                
            self.session.build_result = build_result
            logger.info(f"✅ Build completed in {build_result.build_time_seconds:.2f}s")
            
            # Phase 3: Provision Infrastructure
            logger.info("☁️ Phase 3: Provisioning Infrastructure")
            self.session.status = "provisioning"
            
            provision_start = time.time()
            provision_result = stack_components.provisioner.provision(plan, build_result, credentials)
            provision_result.provision_time_seconds = time.time() - provision_start
            
            if not provision_result.success:
                self.session.status = "provision_failed"
                return DeployResult(
                    success=False,
                    live_url="",
                    error_message=f"Provisioning failed: {provision_result.error_message}",
                    deploy_time_seconds=time.time() - start_time
                )
                
            self.session.provision_result = provision_result
            logger.info(f"✅ Infrastructure provisioned in {provision_result.provision_time_seconds:.2f}s")
            
            # Phase 4: Deploy Application
            logger.info("🚀 Phase 4: Deploying Application")
            self.session.status = "deploying"
            
            deploy_start = time.time()
            deploy_result = stack_components.deployer.deploy(plan, build_result, provision_result, credentials)
            deploy_result.deploy_time_seconds = time.time() - deploy_start
            
            if not deploy_result.success:
                self.session.status = "deploy_failed"
                return DeployResult(
                    success=False,
                    live_url="",
                    error_message=f"Deployment failed: {deploy_result.error_message}",
                    deploy_time_seconds=time.time() - start_time
                )
            
            # Success!
            self.session.deploy_result = deploy_result
            self.session.status = "completed"
            
            total_time = time.time() - start_time
            deploy_result.deploy_time_seconds = total_time
            
            logger.info(f"🎉 Deployment completed successfully in {total_time:.2f}s")
            logger.info(f"🌐 Live URL: {deploy_result.live_url}")
            
            return deploy_result
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            self.session.status = "failed"
            return DeployResult(
                success=False,
                live_url="",
                error_message=str(e),
                deploy_time_seconds=time.time() - start_time
            )
    
    def get_session(self) -> Optional[DeploymentSession]:
        """Get the current deployment session"""
        return self.session
        
    def run_analysis_only(self, repo_dir: Path) -> Optional[StackPlan]:
        """Run only the analysis/detection phase"""
        logger.info("🔍 Running analysis only")
        return detect_stack(repo_dir)
        
    def run_build_only(self, plan: StackPlan, repo_dir: Path) -> BuildResult:
        """Run only the build phase"""
        logger.info(f"🔨 Running build only for stack: {plan.stack_key}")
        
        stack_components = get_stack(plan.stack_key)
        if not stack_components:
            return BuildResult(
                success=False,
                artifact_dir=repo_dir,
                error_message=f"Stack '{plan.stack_key}' not found"
            )
            
        return stack_components.builder.build(plan, repo_dir)

class PipelineFactory:
    """Factory for creating pipeline instances"""
    
    @staticmethod
    def create_pipeline(stack_key: Optional[str] = None) -> Pipeline:
        """Create a new pipeline instance"""
        return Pipeline(stack_key)
        
    @staticmethod
    def create_for_stack(stack_key: str) -> Pipeline:
        """Create pipeline for specific stack"""
        return Pipeline(stack_key)
        
    @staticmethod
    def create_auto_detect() -> Pipeline:
        """Create pipeline with auto-detection"""
        return Pipeline(None)

# Default pipeline instance for easy importing
pipeline = PipelineFactory.create_auto_detect()
