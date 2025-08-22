"""
Protocol interfaces for the plugin architecture
"""
from typing import Protocol, Optional
from pathlib import Path
from .models import AnalysisResult, StackPlan, BuildResult, ProvisionResult, DeployResult

class StackDetector(Protocol):
    """Protocol for detecting if a repository matches a specific stack"""
    
    def detect(self, repo_dir: Path) -> Optional[StackPlan]:
        """
        Analyze repository and return StackPlan if this detector can handle it.
        Returns None if this stack doesn't apply to the repository.
        """
        ...
    
    def get_priority(self) -> int:
        """
        Return priority level for this detector (higher = checked first).
        Useful when multiple detectors might match.
        """
        ...

class StackBuilder(Protocol):
    """Protocol for building projects of a specific stack"""
    
    def build(self, plan: StackPlan, repo_dir: Path) -> BuildResult:
        """
        Build the project according to the StackPlan.
        Should handle all build steps and return build artifacts location.
        """
        ...
    
    def validate_build_requirements(self, repo_dir: Path) -> bool:
        """
        Check if all required tools/dependencies are available for building.
        """
        ...

class StackProvisioner(Protocol):
    """Protocol for provisioning AWS infrastructure for a specific stack"""
    
    def provision(self, plan: StackPlan, build: BuildResult, credentials: dict) -> ProvisionResult:
        """
        Create AWS infrastructure needed for this stack.
        Should return infrastructure details needed for deployment.
        """
        ...
    
    def destroy(self, provision: ProvisionResult, credentials: dict) -> bool:
        """
        Clean up/destroy the provisioned infrastructure.
        """
        ...

class StackDeployer(Protocol):
    """Protocol for deploying built applications to provisioned infrastructure"""
    
    def deploy(self, plan: StackPlan, build: BuildResult, provision: ProvisionResult, credentials: dict) -> DeployResult:
        """
        Deploy the built application to the provisioned infrastructure.
        Should return live URL and deployment details.
        """
        ...
    
    def validate_deployment(self, deploy: DeployResult) -> bool:
        """
        Validate that the deployment is working correctly.
        """
        ...
    
    def rollback(self, deploy: DeployResult, credentials: dict) -> bool:
        """
        Rollback a deployment if possible.
        """
        ...

class StackPlugin(Protocol):
    """Protocol for complete stack plugin"""
    
    @property
    def stack_key(self) -> str:
        """Unique identifier for this stack (e.g., 'react', 'static', 'vue')"""
        ...
    
    @property
    def display_name(self) -> str:
        """Human-readable name for this stack"""
        ...
    
    @property
    def description(self) -> str:
        """Description of what this stack handles"""
        ...
    
    @property
    def detector(self) -> StackDetector:
        """Stack detector instance"""
        ...
    
    @property
    def builder(self) -> StackBuilder:
        """Stack builder instance"""
        ...
    
    @property
    def provisioner(self) -> StackProvisioner:
        """Stack provisioner instance"""
        ...
    
    @property
    def deployer(self) -> StackDeployer:
        """Stack deployer instance"""
        ...
    
    def health_check(self) -> bool:
        """Check if this plugin is healthy and ready to use"""
        ...

# Utility protocols for shared services
class CredentialValidator(Protocol):
    """Protocol for validating AWS credentials"""
    
    def validate(self, credentials: dict) -> dict:
        """Validate AWS credentials and return permissions info"""
        ...

class RepositoryManager(Protocol):
    """Protocol for managing repository operations"""
    
    def clone_repository(self, repo_url: str) -> Path:
        """Clone repository and return local path"""
        ...
    
    def cleanup_repository(self, repo_path: Path) -> bool:
        """Clean up cloned repository"""
        ...

class ArtifactManager(Protocol):
    """Protocol for managing build artifacts"""
    
    def store_artifact(self, artifact_path: Path, metadata: dict) -> str:
        """Store build artifact and return storage ID"""
        ...
    
    def retrieve_artifact(self, storage_id: str) -> Path:
        """Retrieve stored artifact"""
        ...
    
    def cleanup_artifact(self, storage_id: str) -> bool:
        """Clean up stored artifact"""
        ...
