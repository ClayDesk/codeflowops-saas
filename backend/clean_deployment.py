"""
Clean Dynamic Deployment System
100% Plugin-Driven - No Hardcoded Logic
"""
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class CleanDeploymentPipeline:
    """
    Pure plugin-driven deployment pipeline
    Uses detected stack type directly without any overrides
    """
    
    def __init__(self):
        self.pipeline = None
        self._init_pipeline()
    
    def _init_pipeline(self):
        """Initialize the plugin pipeline"""
        try:
            from core.pipeline import Pipeline
            self.pipeline = Pipeline()
            logger.info("✅ Plugin pipeline initialized")
        except ImportError as e:
            logger.error(f"Failed to initialize pipeline: {e}")
    
    async def deploy_with_detected_stack(self, deployment_id: str, analysis: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy using the exact stack type detected during analysis
        NO hardcoded mappings or overrides
        """
        try:
            # Extract the detected stack directly from analysis
            detected_stack = (
                analysis.get("project_type") or
                analysis.get("detected_stack") or 
                analysis.get("plugin_detection", {}).get("recommended_stack") or
                analysis.get("recommended_stack", {}).get("stack_type")
            )
            
            if not detected_stack:
                raise ValueError("No stack detected in analysis")
            
            logger.info(f"🎯 Deploying with detected stack: {detected_stack}")
            
            # Create analysis result for pipeline
            from core.models import AnalysisResult
            
            analysis_result = AnalysisResult(
                repo_url=analysis.get("repository_url"),
                repo_dir=Path(analysis.get("local_repo_path")),
                primary_lang=analysis.get("detected_framework", "Unknown"),
                framework=analysis.get("detected_framework"),
                findings={
                    "project_type": detected_stack,
                    "stack_detected": True,
                    "recommended_stack": detected_stack,
                    "build_ready": analysis.get("is_build_ready", True),
                    "plugin_detection": analysis.get("plugin_detection", {})
                }
            )
            
            # Execute deployment with detected stack (no mapping)
            result = self.pipeline.run_full_deployment(
                analysis=analysis_result,
                credentials=credentials,
                stack_override=detected_stack  # Use detected stack exactly
            )
            
            return {
                "success": result.success,
                "live_url": result.live_url if result.success else None,
                "error": result.error_message if not result.success else None,
                "details": result.details,
                "deployed_stack": detected_stack
            }
            
        except Exception as e:
            logger.error(f"❌ Clean deployment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "deployed_stack": detected_stack if 'detected_stack' in locals() else "unknown"
            }

# Global instance
clean_pipeline = CleanDeploymentPipeline()
