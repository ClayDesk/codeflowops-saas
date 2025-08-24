"""
Intelligence Profile Contracts and Type Definitions
Complete schema for exhaustive repository analysis
"""
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Core Analysis Results
class FileMetadata(TypedDict):
    path: str
    name: str  
    extension: str
    size: int
    hash: str
    lines: int
    language: str
    is_binary: bool
    encoding: str
    mtime: str

class Evidence(TypedDict):
    name: str
    confidence: float
    evidence: List[str]
    location: Optional[str]

class SecretMatch(TypedDict):
    type: str  # "AWS_ACCESS_KEY_ID", "STRIPE_SECRET_KEY", etc.
    location: str  # "file:line"
    preview: str  # Redacted preview
    risk: str  # "low", "medium", "high"
    pattern_matched: str

class DatabaseInfo(TypedDict):
    kind: Optional[str]  # "postgresql", "mysql", "sqlite", etc.
    sources: List[str]   # Where we found evidence
    entities: int        # Number of models/tables detected
    relations: int       # Number of relationships
    migrations: Dict[str, Any]  # Migration status and info
    orm: Optional[str]   # "prisma", "sequelize", "laravel", etc.

class AuthInfo(TypedDict):
    method: str          # "nextauth", "laravel-sanctum", "jwt", etc.
    providers: List[str] # ["google", "github", "credentials"]
    confidence: float
    evidence: List[str]

class IntegrationInfo(TypedDict):
    name: str           # "stripe", "sendgrid", "aws-s3", etc.
    evidence: List[str] # How we detected it
    config_found: bool
    env_vars: List[str] # Related environment variables

class StackService(TypedDict):
    id: str
    role: str  # "web-frontend", "backend-api", "database", "worker", etc.
    framework: Evidence
    build: Optional[Dict[str, Any]]
    runtime: Optional[Dict[str, Any]]
    database: Optional[DatabaseInfo]
    cache: Optional[Dict[str, Any]]
    integrations: List[IntegrationInfo]
    depends_on: List[str]

class SharedResources(TypedDict):
    object_storage: Optional[Dict[str, Any]]
    cdn: Optional[Dict[str, Any]]
    auth: Optional[AuthInfo]
    message_queue: Optional[Dict[str, Any]]
    search_engine: Optional[Dict[str, Any]]

class SecurityRisk(TypedDict):
    type: str
    severity: str  # "low", "medium", "high"
    locations: List[str]
    note: str

class StackBlueprint(TypedDict):
    stack_blueprint_version: str
    analysis_id: str
    repository_url: str
    analyzed_at: str
    
    # Project Structure
    project_kind: str  # "monolith", "monorepo", "microservice"
    services: List[StackService]
    shared_resources: SharedResources
    
    # Deployment Info
    deployment_targets: Dict[str, Any]
    security_risks: List[SecurityRisk]
    
    # Final Recommendation
    final_recommendation: Dict[str, Any]
    
    # Raw Intelligence (for debugging)
    intelligence_profile: Dict[str, Any]

# Intelligence Profile (Complete Repository Analysis)
class IntelligenceProfile(TypedDict):
    # Summary Stats
    summary: Dict[str, Any]
    
    # Framework Detection
    frameworks: List[Evidence]
    runtimes: List[str]
    
    # Dependencies
    dependencies: Dict[str, Dict[str, str]]  # {"npm": {"react": "18.2.0"}}
    
    # Environment & Secrets
    env: Dict[str, Any]
    
    # Database Analysis
    database: DatabaseInfo
    
    # Third-party Integrations
    integrations: List[IntegrationInfo]
    
    # Authentication
    auth: AuthInfo
    
    # CI/CD
    cicd: Dict[str, Any]
    
    # Infrastructure as Code
    infrastructure: Dict[str, Any]
    
    # Security Analysis
    risk: Dict[str, Any]
    
    # File Analysis
    file_intelligence: Dict[str, Any]

@dataclass
class AnalysisContext:
    """Context passed between analysis stages"""
    repo_path: Path
    repo_url: str
    analysis_id: str
    files: List[FileMetadata] = field(default_factory=list)
    raw_analysis: Dict[str, Any] = field(default_factory=dict)
    intelligence_profile: Dict[str, Any] = field(default_factory=dict)
    stack_blueprint: Optional[StackBlueprint] = None
    
    def add_evidence(self, category: str, evidence: Evidence):
        """Add evidence to intelligence profile"""
        if category not in self.intelligence_profile:
            self.intelligence_profile[category] = []
        self.intelligence_profile[category].append(evidence)
    
    def add_integration(self, integration: IntegrationInfo):
        """Add detected integration"""
        if "integrations" not in self.intelligence_profile:
            self.intelligence_profile["integrations"] = []
        self.intelligence_profile["integrations"].append(integration)
    
    def add_security_risk(self, risk: SecurityRisk):
        """Add security risk"""
        if "security_risks" not in self.intelligence_profile:
            self.intelligence_profile["security_risks"] = []
        self.intelligence_profile["security_risks"].append(risk)

# Stack Detection Priorities
STACK_PRIORITIES = [
    "php_laravel",
    "nextjs_ssr", 
    "nextjs_static",
    "react_spa",
    "vue_spa", 
    "django",
    "flask_fastapi",
    "rails",
    "express_api",
    "static_site"
]

# Stack Variants Map
STACK_VARIANTS = {
    # PHP Variants
    "php_laravel": {
        "api_only": {"description": "Laravel API-only", "deployment": "aws.ecs.laravel_api.mysql.redis"},
        "blade_ssr": {"description": "Laravel Blade SSR", "deployment": "aws.ec2.laravel_web.mysql.redis"},
        "spa_split": {"description": "Laravel API + SPA Frontend", "deployment": "aws.ecs.laravel_api.mysql + aws.s3.spa"}
    },
    
    # React Variants  
    "react_spa": {
        "standalone": {"description": "Pure React SPA", "deployment": "aws.s3.cloudfront"},
        "with_api": {"description": "React SPA + API Backend", "deployment": "aws.s3.cloudfront + aws.ecs.api"}
    },
    
    # Next.js Variants
    "nextjs": {
        "ssr": {"description": "Next.js SSR", "deployment": "aws.ecs.nextjs_ssr"},
        "static": {"description": "Next.js Static Export", "deployment": "aws.s3.cloudfront"}
    }
}
