"""
CodeFlowOps Enhanced Analysis Engine
Core Services Package
"""

from .analysis.repository_analyzer import RepositoryAnalyzer
from .analysis.project_type_detector import ProjectTypeDetector
from .analysis.dependency_analyzer import DependencyAnalyzer
from .analysis.analysis_reporter import AnalysisReporter

# Deployment services removed - using simplified Terraform templates
# (Deployment orchestrator removed due to Claude dependencies)

# Import WebSocket service
from .websocket_service import get_websocket_service, WebSocketService

# Import project state manager
from .project_state_manager import (
    ProjectStateManager,
    ProjectState,
    EnvironmentDeployment,
    DeploymentStatus as PSMDeploymentStatus
)

__all__ = [
    "RepositoryAnalyzer",
    "ProjectTypeDetector", 
    "DependencyAnalyzer",
    "AnalysisReporter",
    # Deployment services removed due to Claude dependencies
    # WebSocket service
    "get_websocket_service",
    "WebSocketService",
    # Project state management
    "ProjectStateManager",
    "ProjectState",
    "EnvironmentDeployment",
    "PSMDeploymentStatus"
]

__version__ = "1.0.0"
__phase__ = "Phase 2: Real AWS Deployment Integration"
