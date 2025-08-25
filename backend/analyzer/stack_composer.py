"""
🎯 Stack Blueprint Composer - Full Stack Recommendation Engine
================================================================================
Converts Intelligence Profiles into complete deployment-ready Stack Blueprints
with precise service topology, dependencies, and deployment recipes.

Core Philosophy:
- No guesswork at deployment time
- Evidence-based confidence scoring  
- Deterministic recipe selection
- Support for monoliths, monorepos, and microservices
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ProjectKind(Enum):
    MONOLITH = "monolith"
    MONOREPO = "monorepo" 
    MICROSERVICES = "microservices"

class ServiceRole(Enum):
    WEB_FRONTEND = "web-frontend"
    BACKEND_API = "backend-api"
    WORKER = "worker"
    DATABASE = "database"
    QUEUE = "queue"
    SEARCH = "search"
    CACHE = "cache"

class RuntimeKind(Enum):
    STATIC = "static"
    NODEJS = "nodejs"
    PHP_FPM = "php-fpm"
    PYTHON = "python"
    RUBY = "ruby"
    JAVA = "java"

@dataclass
class FrameworkInfo:
    name: str
    variant: Optional[str] = None
    confidence: float = 0.0
    rationale: List[str] = None
    
    def __post_init__(self):
        if self.rationale is None:
            self.rationale = []

@dataclass
class BuildConfig:
    tool: str
    commands: List[str]
    artifact: Optional[str] = None

@dataclass
class RuntimeConfig:
    kind: str
    entry: Optional[str] = None
    process_manager: Optional[str] = None
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}

@dataclass
class DatabaseConfig:
    kind: str
    orm: Optional[str] = None
    migrations: Optional[Dict[str, Any]] = None
    required: bool = True

@dataclass
class CacheConfig:
    kind: str
    detected: bool = False
    recommended: bool = False
    reason: Optional[str] = None

@dataclass
class ServiceBlueprint:
    id: str
    role: str
    framework: FrameworkInfo
    build: Optional[BuildConfig] = None
    runtime: Optional[RuntimeConfig] = None
    database: Optional[DatabaseConfig] = None
    cache: Optional[CacheConfig] = None
    integrations: List[Dict[str, Any]] = None
    depends_on: List[str] = None
    
    def __post_init__(self):
        if self.integrations is None:
            self.integrations = []
        if self.depends_on is None:
            self.depends_on = []

@dataclass
class SharedResources:
    object_storage: Optional[Dict[str, Any]] = None
    cdn: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None

@dataclass
class SecurityRisk:
    type: str
    severity: str
    locations: List[str] = None
    note: Optional[str] = None
    
    def __post_init__(self):
        if self.locations is None:
            self.locations = []

@dataclass
@dataclass
class FinalRecommendation:
    stack_id: str
    confidence: float
    why: List[str]
    fallbacks: List[Dict[str, str]] = None
    deployment_recipe_id: Optional[str] = None
    
    def __post_init__(self):
        if self.fallbacks is None:
            self.fallbacks = []

@dataclass
class StackBlueprint:
    stack_blueprint_version: str = "1.0.0"
    project_kind: str = "monolith"
    services: List[ServiceBlueprint] = None
    shared_resources: Optional[SharedResources] = None
    deployment_targets: Dict[str, Any] = None
    security_risks: List[SecurityRisk] = None
    final_recommendation: Optional[FinalRecommendation] = None
    
    def __post_init__(self):
        if self.services is None:
            self.services = []
        if self.deployment_targets is None:
            self.deployment_targets = {}
        if self.security_risks is None:
            self.security_risks = []

class StackComposer:
    """🎯 Converts Intelligence Profiles into Complete Stack Blueprints"""
    
    def __init__(self):
        self.stack_variants = self._load_stack_variants()
        self.deployment_recipes = self._load_deployment_recipes()
    
    def compose_stack_blueprint(self, intelligence_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 Main entry point: Convert Intelligence Profile to Stack Blueprint
        
        Args:
            intelligence_profile: Complete repo analysis from Intelligence Pipeline
            
        Returns:
            Complete Stack Blueprint with deployment recipe
        """
        logger.info("🎯 Composing Stack Blueprint from Intelligence Profile")
        
        # 🛑 SPECIAL HANDLING FOR TOOLKITS/LIBRARIES
        project_kind = intelligence_profile.get("project_kind", "app")
        if project_kind in ["toolkit", "monorepo+toolkit", "library"]:
            logger.info(f"🔧 Detected {project_kind} - creating non-deployable blueprint")
            
            # Create minimal blueprint for toolkits
            blueprint = StackBlueprint(
                project_kind="toolkit",
                services=[],  # No services for toolkits
                shared_resources=SharedResources(),  # No shared resources
                deployment_targets={
                    "preferred": "none",
                    "evidence": ["toolkit repository"],
                    "iac": []
                },
                security_risks=[],  # Minimal security concerns for toolkits
                final_recommendation=FinalRecommendation(
                    stack_id="",  # No stack ID for non-deployable
                    confidence=0.0,
                    why=["Toolkit repository (not a deployable application). Use a template to generate an app."],
                    fallbacks=[],
                    deployment_recipe_id="none"
                )
            )
            
            result = self._dataclass_to_dict(blueprint)
            logger.info(f"✅ Toolkit blueprint created - non-deployable")
            return result
        
        # 1. Determine project topology
        project_kind_enum = self._determine_project_kind(intelligence_profile)
        logger.info(f"📊 Project Kind: {project_kind_enum}")
        
        # 2. Map frameworks to service blueprints
        services = self._compose_services(intelligence_profile, project_kind_enum)
        logger.info(f"🔧 Composed {len(services)} services")
        
        # 3. Determine shared resources
        shared_resources = self._compose_shared_resources(intelligence_profile, services)
        
        # 4. Extract deployment targets
        deployment_targets = self._determine_deployment_targets(intelligence_profile)
        
        # 5. Convert security findings
        security_risks = self._convert_security_risks(intelligence_profile)
        
        # 6. Score and pick final recommendation
        final_recommendation = self._score_and_recommend(intelligence_profile, services, shared_resources)
        
        # 7. Build complete blueprint
        blueprint = StackBlueprint(
            project_kind=project_kind_enum,
            services=services,
            shared_resources=shared_resources,
            deployment_targets=deployment_targets,
            security_risks=security_risks,
            final_recommendation=final_recommendation
        )
        
        # Convert to dict for JSON serialization
        result = self._dataclass_to_dict(blueprint)
        
        logger.info(f"✅ Stack Blueprint completed - Stack ID: {final_recommendation.stack_id}")
        return result
    
    def _determine_project_kind(self, profile: Dict[str, Any]) -> str:
        """🔍 Determine if monolith, monorepo, or microservices"""
        
        frameworks = profile.get('frameworks', [])
        summary = profile.get('summary', {})
        
        # Multiple high-confidence frameworks suggest monorepo
        high_confidence_frameworks = [f for f in frameworks if f.get('confidence', 0) > 0.7]
        
        if len(high_confidence_frameworks) > 2:
            return ProjectKind.MONOREPO.value
        
        # Check for microservices indicators
        infra = profile.get('infrastructure', {})
        if infra.get('docker', {}).get('compose') or infra.get('kubernetes'):
            return ProjectKind.MICROSERVICES.value
        
        # Default to monolith
        return ProjectKind.MONOLITH.value
    
    def _compose_services(self, profile: Dict[str, Any], project_kind: str) -> List[ServiceBlueprint]:
        """🔧 Convert framework detections into service blueprints"""
        
        services = []
        frameworks = profile.get('frameworks', [])
        dependencies = profile.get('dependencies', {})
        database = profile.get('database', {})
        
        # Sort frameworks by confidence
        frameworks.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        for idx, framework in enumerate(frameworks):
            if framework.get('confidence', 0) < 0.5:
                continue  # Skip low-confidence detections
                
            service = self._framework_to_service(framework, dependencies, database, idx)
            if service:
                services.append(service)
        
        # Add database service if detected
        if database.get('kind') and database.get('required'):
            db_service = self._create_database_service(database)
            services.append(db_service)
        
        return services
    
    def _framework_to_service(self, framework: Dict[str, Any], dependencies: Dict[str, Any], 
                            database: Dict[str, Any], index: int) -> Optional[ServiceBlueprint]:
        """🎯 Convert framework detection to service blueprint"""
        
        name = framework.get('name', '').lower()
        confidence = framework.get('confidence', 0)
        evidence = framework.get('evidence', [])
        
        # Static Sites
        if name == 'static-site':
            return ServiceBlueprint(
                id="static-site",
                role=ServiceRole.WEB_FRONTEND.value,
                framework=FrameworkInfo(
                    name="static-site",
                    variant="html",
                    confidence=confidence,
                    rationale=evidence
                ),
                build=BuildConfig(
                    tool="none",
                    commands=[],
                    artifact="."
                ),
                runtime=RuntimeConfig(
                    kind=RuntimeKind.STATIC.value,
                    options={"spa_routing": False}
                )
            )
        
        # PHP/Laravel Services
        elif name == 'laravel':
            return ServiceBlueprint(
                id="laravel-app",
                role=ServiceRole.BACKEND_API.value,
                framework=FrameworkInfo(
                    name="laravel",      # ✅ FIXED: Use "laravel" as framework name
                    variant="php",       # ✅ FIXED: Use "php" as variant/runtime
                    confidence=confidence,
                    rationale=evidence
                ),
                build=BuildConfig(
                    tool="composer",
                    commands=[
                        "composer install --optimize-autoloader --no-dev",
                        "php artisan key:generate --force",
                        "php artisan config:cache",
                        "php artisan route:cache"
                    ],
                    artifact="public/"
                ),
                runtime=RuntimeConfig(
                    kind=RuntimeKind.PHP_FPM.value,
                    entry="public/index.php",
                    process_manager="supervisord"
                ),
                database=DatabaseConfig(
                    kind=database.get('kind', 'mysql'),
                    orm="eloquent",
                    migrations={
                        "tool": "artisan",
                        "commands": ["php artisan migrate --force"]
                    }
                ) if database.get('required') else None
            )
        
        # Next.js Services
        elif name == 'nextjs':
            # Determine if SSR or static export
            is_ssr = self._detect_nextjs_ssr(evidence, dependencies)
            
            return ServiceBlueprint(
                id="nextjs-app",
                role=ServiceRole.WEB_FRONTEND.value,
                framework=FrameworkInfo(
                    name="nextjs",
                    variant="ssr" if is_ssr else "static",
                    confidence=confidence,
                    rationale=evidence
                ),
                build=BuildConfig(
                    tool=self._detect_node_package_manager(dependencies),
                    commands=[
                        "npm ci",
                        "npm run build"
                    ] if not is_ssr else [
                        "npm ci", 
                        "npm run build",
                        "npm run export"
                    ],
                    artifact="out/" if not is_ssr else ".next/"
                ),
                runtime=RuntimeConfig(
                    kind=RuntimeKind.STATIC.value if not is_ssr else RuntimeKind.NODEJS.value,
                    entry="server.js" if is_ssr else None,
                    options={"spa_routing": True} if not is_ssr else {}
                )
            )
        
        # React SPA Services (including Create React App)
        elif name in ['react', 'create-react-app']:
            return ServiceBlueprint(
                id="react-spa",
                role=ServiceRole.WEB_FRONTEND.value,
                framework=FrameworkInfo(
                    name="react",
                    variant="spa",
                    confidence=confidence,
                    rationale=evidence
                ),
                build=BuildConfig(
                    tool=self._detect_node_package_manager(dependencies),
                    commands=["npm ci", "npm run build"],
                    artifact="build/"
                ),
                runtime=RuntimeConfig(
                    kind=RuntimeKind.STATIC.value,
                    options={"spa_routing": True}
                )
            )
        
        # Node.js/Express API Services  
        elif name in ['express', 'node', 'nodejs', 'fastify']:
            return ServiceBlueprint(
                id="node-api",
                role=ServiceRole.BACKEND_API.value,
                framework=FrameworkInfo(
                    name="node",
                    variant=name if name != 'nodejs' else 'node',
                    confidence=confidence,
                    rationale=evidence
                ),
                build=BuildConfig(
                    tool=self._detect_node_package_manager(dependencies),
                    commands=["npm ci", "npm run build"],
                    artifact="dist/"
                ),
                runtime=RuntimeConfig(
                    kind=RuntimeKind.NODEJS.value,
                    entry="dist/server.js",
                    process_manager="pm2"
                ),
                database=DatabaseConfig(
                    kind=database.get('kind', 'postgresql'),
                    orm=self._detect_node_orm(dependencies),
                    migrations={
                        "tool": "npm",
                        "commands": ["npm run migrate"]
                    }
                ) if database.get('required') else None
            )
        
        # Python Services
        elif name in ['django', 'flask', 'fastapi']:
            return ServiceBlueprint(
                id=f"{name}-app",
                role=ServiceRole.BACKEND_API.value,
                framework=FrameworkInfo(
                    name="python",
                    variant=name,
                    confidence=confidence,
                    rationale=evidence
                ),
                build=BuildConfig(
                    tool="pip",
                    commands=[
                        "pip install -r requirements.txt",
                        "python manage.py collectstatic --noinput" if name == 'django' else "echo 'No static collection needed'"
                    ]
                ),
                runtime=RuntimeConfig(
                    kind=RuntimeKind.PYTHON.value,
                    entry=f"wsgi.py" if name in ['django', 'flask'] else "main.py",
                    process_manager="gunicorn"
                ),
                database=DatabaseConfig(
                    kind=database.get('kind', 'postgresql'),
                    orm="django-orm" if name == 'django' else "sqlalchemy",
                    migrations={
                        "tool": "django" if name == 'django' else "alembic",
                        "commands": ["python manage.py migrate"] if name == 'django' else ["alembic upgrade head"]
                    }
                ) if database.get('required') else None
            )
        
        return None
    
    def _create_database_service(self, database: Dict[str, Any]) -> ServiceBlueprint:
        """🗄️ Create database service blueprint"""
        
        kind = database.get('kind', 'postgresql')
        
        return ServiceBlueprint(
            id=f"{kind}-db",
            role=ServiceRole.DATABASE.value,
            framework=FrameworkInfo(
                name=kind,
                variant="managed",
                confidence=0.9,
                rationale=["Database requirement detected from analysis"]
            ),
            runtime=RuntimeConfig(
                kind=kind,
                options={
                    "version": database.get('version', 'latest'),
                    "managed": True
                }
            )
        )
    
    def _compose_shared_resources(self, profile: Dict[str, Any], services: List[ServiceBlueprint]) -> SharedResources:
        """🔗 Determine shared resources needed"""
        
        integrations = profile.get('integrations', [])
        env = profile.get('env', {})
        
        # Object Storage
        object_storage = None
        storage_evidence = []
        for integration in integrations:
            if integration.get('name') in ['s3', 'aws-s3', 'gcs', 'azure-blob']:
                storage_evidence.extend(integration.get('evidence', []))
        
        if storage_evidence or any('upload' in str(ev).lower() for ev in env.get('variables', [])):
            object_storage = {
                "provider": "aws-s3",
                "required": True,
                "use_cases": ["uploads", "static-assets"]
            }
        
        # CDN
        cdn = None
        has_static_content = any(s.runtime and s.runtime.kind == RuntimeKind.STATIC.value for s in services)
        if has_static_content or object_storage:
            cdn = {
                "provider": "cloudfront",
                "required": True
            }
        
        # Auth
        auth = profile.get('auth', {})
        auth_config = None
        if auth.get('method'):
            auth_config = {
                "method": auth.get('method'),
                "providers": auth.get('providers', []),
                "confidence": auth.get('confidence', 0.5),
                "evidence": auth.get('evidence', [])
            }
        
        return SharedResources(
            object_storage=object_storage,
            cdn=cdn,
            auth=auth_config
        )
    
    def _determine_deployment_targets(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """🎯 Determine preferred deployment targets"""
        
        infra = profile.get('infrastructure', {})
        
        # Default to AWS
        preferred = "aws"
        evidence = []
        iac = []
        
        if infra.get('terraform', {}).get('providers'):
            providers = infra['terraform']['providers']
            if 'aws' in providers:
                preferred = "aws"
                evidence.append("terraform aws provider")
            elif 'gcp' in providers:
                preferred = "gcp"
                evidence.append("terraform gcp provider")
            elif 'azure' in providers:
                preferred = "azure"
                evidence.append("terraform azure provider")
            iac.append("terraform")
        
        if infra.get('docker'):
            evidence.append("docker present")
            iac.append("docker")
        
        return {
            "preferred": preferred,
            "evidence": evidence,
            "iac": iac
        }
    
    def _convert_security_risks(self, profile: Dict[str, Any]) -> List[SecurityRisk]:
        """🔒 Convert security findings to risk objects"""
        
        risks = []
        env = profile.get('env', {})
        
        if env.get('secrets'):
            for secret in env['secrets']:
                risks.append(SecurityRisk(
                    type="secrets_exposed",
                    severity=secret.get('risk', 'medium'),
                    locations=[secret.get('location', '')],
                    note="Secret values redacted in analysis"
                ))
        
        risk_flags = profile.get('risk', {})
        if risk_flags.get('secrets_exposed'):
            risks.append(SecurityRisk(
                type="secrets_exposed",
                severity="high",
                note="High-risk secrets detected; values redacted"
            ))
        
        return risks
    
    def _score_and_recommend(self, profile: Dict[str, Any], services: List[ServiceBlueprint], 
                           shared_resources: SharedResources) -> FinalRecommendation:
        """🎯 Score all evidence and pick final stack recommendation"""
        
        # Build stack ID from services
        service_parts = []
        for service in services:
            if service.framework.variant:
                service_parts.append(f"{service.framework.name}-{service.framework.variant}")
            else:
                service_parts.append(service.framework.name)
        
        # Add shared resources
        if shared_resources.object_storage:
            service_parts.append("s3")
        if shared_resources.cdn:
            service_parts.append("cloudfront")
        
        stack_id = " + ".join(service_parts)
        
        # Calculate confidence (weighted average)
        total_confidence = 0
        total_weight = 0
        rationale = []
        
        for service in services:
            weight = 1.0
            if service.role == ServiceRole.WEB_FRONTEND.value:
                weight = 0.8
            elif service.role == ServiceRole.BACKEND_API.value:
                weight = 1.0
            
            total_confidence += service.framework.confidence * weight
            total_weight += weight
            rationale.extend(service.framework.rationale[:2])  # Top 2 reasons per service
        
        final_confidence = total_confidence / total_weight if total_weight > 0 else 0.5
        
        # Generate deployment recipe ID
        deployment_recipe_id = self._generate_recipe_id(services, shared_resources, profile)
        
        # Generate fallbacks
        fallbacks = self._generate_fallbacks(services, shared_resources)
        
        return FinalRecommendation(
            stack_id=stack_id,
            confidence=final_confidence,
            why=rationale[:5],  # Top 5 reasons
            fallbacks=fallbacks,
            deployment_recipe_id=deployment_recipe_id
        )
    
    def _generate_recipe_id(self, services: List[ServiceBlueprint], 
                          shared_resources: SharedResources, profile: Dict[str, Any]) -> Optional[str]:
        """🎯 Generate deployment recipe ID"""
        
        deployment_targets = profile.get('deployment_targets', {})
        cloud = deployment_targets.get('preferred', 'aws')
        
        # Primary service determines recipe base
        primary_service = next((s for s in services if s.role == ServiceRole.BACKEND_API.value), 
                             next((s for s in services if s.role == ServiceRole.WEB_FRONTEND.value), None))
        
        # For library/tooling repositories, return None instead of hardcoded fallback
        if not primary_service:
            return None
        
        framework = primary_service.framework
        recipe_parts = [cloud]
        
        # Add compute layer
        if framework.name == "static-site":
            recipe_parts.extend(["s3", "cloudfront", "static-site"])
        elif framework.name == "php" and framework.variant == "laravel":
            recipe_parts.extend(["ecs", "fargate", "php", "laravel"])
        elif framework.name == "nextjs":
            if framework.variant == "ssr":
                recipe_parts.extend(["ec2", "nextjs", "ssr"])
            else:
                recipe_parts.extend(["s3", "cloudfront", "nextjs", "static"])
        elif framework.name == "react":
            recipe_parts.extend(["s3", "cloudfront", "react", "spa"])
        elif framework.name == "node":
            recipe_parts.extend(["ec2", "node", framework.variant or "express"])
        elif framework.name == "python":
            recipe_parts.extend(["ec2", "python", framework.variant or "django"])
        
        # Add database
        db_service = next((s for s in services if s.role == ServiceRole.DATABASE.value), None)
        if db_service:
            recipe_parts.append(f"rds.{db_service.framework.name}")
        
        recipe_parts.append("v1")
        return ".".join(recipe_parts)
    
    def _generate_fallbacks(self, services: List[ServiceBlueprint], 
                          shared_resources: SharedResources) -> List[Dict[str, str]]:
        """🔄 Generate fallback deployment options"""
        
        fallbacks = []
        
        # If SSR detected, add static export fallback
        for service in services:
            if (service.framework.name == "nextjs" and 
                service.framework.variant == "ssr"):
                fallbacks.append({
                    "stack_id": "nextjs-static + s3 + cloudfront",
                    "when": "SSR server fails health checks or runtime errors"
                })
        
        # If complex stack, add simplified fallback
        if len(services) > 2:
            fallbacks.append({
                "stack_id": "static + s3 + cloudfront",
                "when": "Complex services fail; fallback to static hosting"
            })
        
        return fallbacks
    
    # Helper Methods
    def _detect_nextjs_ssr(self, evidence: List[str], dependencies: Dict[str, Any]) -> bool:
        """Detect if Next.js should use SSR or static export"""
        ssr_indicators = ['middleware.ts', 'api routes', 'getServerSideProps', 'dynamic routes']
        return any(indicator in str(evidence).lower() for indicator in ssr_indicators)
    
    def _detect_node_package_manager(self, dependencies: Dict[str, Any]) -> str:
        """Detect Node.js package manager"""
        if 'pnpm' in dependencies:
            return "pnpm"
        elif 'yarn' in dependencies:
            return "yarn"
        return "npm"
    
    def _detect_node_orm(self, dependencies: Dict[str, Any]) -> str:
        """Detect Node.js ORM"""
        npm_deps = dependencies.get('npm', {})
        if 'prisma' in npm_deps:
            return "prisma"
        elif 'sequelize' in npm_deps:
            return "sequelize"
        elif 'typeorm' in npm_deps:
            return "typeorm"
        return "unknown"
    
    def _load_stack_variants(self) -> Dict[str, Any]:
        """Load predefined stack variants"""
        return {
            "php_laravel_mysql": {
                "services": ["php-laravel", "mysql", "nginx"],
                "deployment": "ec2"
            },
            "react_spa_static": {
                "services": ["react-spa", "s3", "cloudfront"],
                "deployment": "static"
            },
            "nextjs_ssr_postgres": {
                "services": ["nextjs-ssr", "postgresql", "s3"],
                "deployment": "ec2"
            }
            # Add more variants as needed
        }
    
    def _load_deployment_recipes(self) -> Dict[str, Any]:
        """Load deployment recipe templates"""
        return {
            "aws.ec2.laravel.mysql": {
                "compute": "ec2",
                "database": "rds-mysql",
                "storage": "s3",
                "load_balancer": "alb"
            }
            # Add more recipes as needed
        }
    
    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """Convert dataclass to dict, handling nested objects"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_value in asdict(obj).items():
                if field_value is not None:
                    result[field_name] = field_value
            return result
        return obj

# Factory function for easy import
def create_stack_composer() -> StackComposer:
    """🏭 Factory function to create Stack Composer instance"""
    return StackComposer()
