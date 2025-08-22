"""
Non-Deployable Repository Plugin
"""
import logging
from pathlib import Path
from typing import Dict, Any
from core.interfaces import StackPlugin
from core.registry import register_stack
from core.models import StackPlan
from .detector import NonDeployableDetector

logger = logging.getLogger(__name__)

class NonDeployableBuilder:
    """Builder for non-deployable repositories (returns helpful message)"""
    
    def build(self, repo_dir: Path, plan: StackPlan) -> Dict[str, Any]:
        """Return analysis explaining why repository is not deployable"""
        config = plan.config
        
        return {
            "type": config.get("type", "non_deployable"),
            "deployable": False,
            "analysis_complete": True,
            "explanation": config.get("explanation", ""),
            "usage_instructions": config.get("usage_instructions", []),
            "tool_name": config.get("tool_name", "Unknown Tool"),
            "language": config.get("language", "Mixed")
        }

class NonDeployableDeployer:
    """Deployer for non-deployable repositories (provides guidance)"""
    
    def deploy(self, build_result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Return deployment guidance for non-deployable repositories"""
        
        return {
            "deployment_method": "not_applicable",
            "status": "analysis_complete",
            "message": "Repository analysis complete - not suitable for web deployment",
            "guidance": build_result.get("explanation", ""),
            "next_steps": build_result.get("usage_instructions", [])
        }

class NonDeployablePlugin(StackPlugin):
    """Plugin for handling non-deployable repositories"""
    
    @property
    def stack_key(self) -> str:
        return "non_deployable"
    
    @property 
    def display_name(self) -> str:
        return "Non-Deployable Repository"
    
    @property
    def detector(self) -> NonDeployableDetector:
        return NonDeployableDetector()
    
    @property
    def builder(self) -> NonDeployableBuilder:
        return NonDeployableBuilder()
    
    @property
    def deployer(self) -> NonDeployableDeployer:
        return NonDeployableDeployer()
    
    def health_check(self) -> bool:
        """Health check for non-deployable plugin"""
        try:
            # Test detector instantiation
            detector = self.detector
            builder = self.builder
            deployer = self.deployer
            
            # Basic functionality check
            return (detector is not None and 
                   builder is not None and 
                   deployer is not None)
        except Exception:
            return False

# Register the plugin
def _register_plugin():
    """Register the non-deployable plugin"""
    try:
        plugin = NonDeployablePlugin()
        register_stack(plugin)
        logger.info("✅ Non-Deployable plugin registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register Non-Deployable plugin: {e}")

# Auto-register when module is imported
_register_plugin()
