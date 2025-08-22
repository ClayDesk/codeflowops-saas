"""
Dynamic Router Registry for Stack-Specific Endpoints
Routes requests to appropriate stack routers based on detection
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Optional, Any
import logging
import importlib
from pathlib import Path

logger = logging.getLogger(__name__)

class StackRouterRegistry:
    """Registry for stack-specific routers"""
    
    def __init__(self):
        self.routers: Dict[str, APIRouter] = {}
        self.loaded_stacks: set = set()
        self._load_base_routers()
    
    def _load_base_routers(self):
        """Load core routers that are always available"""
        try:
            # Analysis router (always loaded)
            try:
                from .analysis_router import router as analysis_router
                self.routers["analysis"] = analysis_router
            except ImportError:
                try:
                    # Try absolute import if relative fails
                    from routers.analysis_router import router as analysis_router
                    self.routers["analysis"] = analysis_router
                except ImportError:
                    logger.warning("Analysis router not available")
            
            # Skip auth router for now - not implemented yet
            logger.info(f"✅ Base routers loaded: {list(self.routers.keys())}")
        except Exception as e:
            logger.error(f"Failed to load base routers: {e}")
            # Continue without base routers if they fail to load
    
    def load_stack_router(self, stack_type: str) -> Optional[APIRouter]:
        """Dynamically load router for specific stack type"""
        if stack_type in self.loaded_stacks:
            return self.routers.get(stack_type)
        
        try:
            # Try to import stack-specific router
            try:
                router_module = importlib.import_module(f".stacks.{stack_type}_router", package="routers")
            except ImportError:
                # Try absolute import if relative fails
                router_module = importlib.import_module(f"routers.stacks.{stack_type}_router")
                
            stack_router = getattr(router_module, "router")
            
            self.routers[stack_type] = stack_router
            self.loaded_stacks.add(stack_type)
            
            logger.info(f"✅ Loaded {stack_type} router dynamically")
            return stack_router
            
        except ImportError as e:
            logger.warning(f"No specific router found for {stack_type}, using generic router")
            
            # Fallback to generic stack router
            try:
                try:
                    from .stacks.generic_router import router as generic_router
                except ImportError:
                    try:
                        from routers.stacks.generic_router import router as generic_router
                    except ImportError:
                        # Create a minimal fallback router
                        from fastapi import APIRouter
                        generic_router = APIRouter()
                        
                        @generic_router.post("/deploy")
                        async def fallback_deploy():
                            return {
                                "success": False,
                                "status": "unsupported",
                                "message": f"Stack type '{stack_type}' is not supported yet"
                            }
                        
                        logger.warning(f"Using minimal fallback router for {stack_type}")
                        
                self.routers[stack_type] = generic_router
                self.loaded_stacks.add(stack_type)
                return generic_router
            except ImportError:
                logger.error(f"Failed to load any router for {stack_type}: {e}")
                return None
    
    def get_router_for_stack(self, stack_type: str) -> APIRouter:
        """Get appropriate router for stack type"""
        if stack_type in self.routers:
            return self.routers[stack_type]
        
        router = self.load_stack_router(stack_type)
        if not router:
            raise HTTPException(
                status_code=500,
                detail=f"No router available for stack type: {stack_type}"
            )
        return router
    
    def get_available_stacks(self) -> list:
        """Get list of available stack types"""
        return list(self.loaded_stacks)

# Global registry instance
stack_router_registry = StackRouterRegistry()
