# Enhanced Stack Detection System (Post-Implementation)
# backend/detectors/enhanced_stack_detector.py

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import our documentation detector
from .documentation_detector import DocumentationDetector

logger = logging.getLogger(__name__)

@dataclass
class StackRecommendation:
    """Comprehensive stack recommendation with deployment strategy"""
    primary_stack: str
    secondary_stacks: List[str]
    deployment_strategy: str
    confidence_score: float
    reasoning: str
    warnings: List[str]
    recommended_resources: Dict[str, str]

class EnhancedStackDetector:
    """
    Advanced multi-stack detection system that automatically recommends
    optimal deployment strategies based on comprehensive repository analysis
    """
    
    def __init__(self):
        self.detectors = {
            'frontend': self._detect_frontend_stack,
            'backend': self._detect_backend_stack,
            'database': self._detect_database_requirements,
            'infrastructure': self._detect_infrastructure_needs
        }
        # Initialize documentation detector
        self.documentation_detector = DocumentationDetector()
    
    def analyze_repository(self, repo_path: str) -> StackRecommendation:
        """
        Comprehensive repository analysis with automatic stack recommendation
        
        This is the main entry point that will automatically:
        1. Detect all stack components (frontend, backend, database)
        2. Recommend optimal deployment strategy
        3. Suggest resource configurations
        4. Provide confidence scoring
        """
        repo = Path(repo_path)
        
        # First, check if this is a documentation-only repository
        # This needs to be done before other detection to avoid false positives
        file_analysis = self._analyze_files(repo)
        documentation_result = self.documentation_detector.detect(file_analysis)
        
        if documentation_result:
            logger.info("📄 Detected documentation-only repository")
            return StackRecommendation(
                primary_stack="documentation_only",
                secondary_stacks=[],
                deployment_strategy="github_pages",
                confidence_score=documentation_result["confidence"],
                reasoning=documentation_result["detection_reason"],
                warnings=["This repository contains only documentation files - not deployable as an application"],
                recommended_resources={"hosting": "GitHub Pages, GitBook, or documentation generator"}
            )
        
        # Multi-layer detection for deployable applications
        frontend_analysis = self._detect_frontend_stack(repo)
        backend_analysis = self._detect_backend_stack(repo)
        database_analysis = self._detect_database_requirements(repo)
        infrastructure_analysis = self._detect_infrastructure_needs(repo)
        
        # Determine primary stack and deployment strategy
        recommendation = self._generate_recommendation(
            frontend_analysis,
            backend_analysis, 
            database_analysis,
            infrastructure_analysis
        )
        
        logger.info(f"Auto-detected stack recommendation: {recommendation.primary_stack} "
                   f"with {recommendation.confidence_score:.1%} confidence")
        
        return recommendation
    
    def _detect_frontend_stack(self, repo: Path) -> Dict:
        """Enhanced frontend detection with framework-specific optimizations"""
        pkg = self._read_package_json(repo)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        frontend_indicators = {
            'nextjs': {
                'dependencies': ['next'],
                'files': ['next.config.js', 'next.config.mjs', 'next-env.d.ts'],
                'directories': ['pages', 'app'],
                'confidence': 0.95
            },
            'react': {
                'dependencies': ['react', 'react-dom'],
                'files': ['src/App.js', 'src/App.tsx', 'public/index.html'],
                'directories': ['src'],
                'confidence': 0.90
            },
            'vue': {
                'dependencies': ['vue', '@vue/core'],
                'files': ['vue.config.js', 'src/main.js'],
                'directories': ['src'],
                'confidence': 0.90
            },
            'angular': {
                'dependencies': ['@angular/core', '@angular/cli'],
                'files': ['angular.json', 'src/main.ts'],
                'directories': ['src/app'],
                'confidence': 0.90
            },
            'static': {
                'dependencies': [],
                'files': ['index.html'],
                'directories': [],
                'confidence': 0.80
            }
        }
        
        detected_frameworks = []
        
        for framework, indicators in frontend_indicators.items():
            score = 0
            matches = []
            
            # Check dependencies
            for dep in indicators['dependencies']:
                if dep in deps:
                    score += 0.4
                    matches.append(f"dependency: {dep}")
            
            # Check files
            for file in indicators['files']:
                if (repo / file).exists():
                    score += 0.3
                    matches.append(f"file: {file}")
            
            # Check directories
            for directory in indicators['directories']:
                if (repo / directory).exists():
                    score += 0.3
                    matches.append(f"directory: {directory}")
            
            if score > 0:
                detected_frameworks.append({
                    'framework': framework,
                    'confidence': min(score * indicators['confidence'], 1.0),
                    'matches': matches
                })
        
        # Sort by confidence and return the best match
        detected_frameworks.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'detected': detected_frameworks,
            'primary': detected_frameworks[0] if detected_frameworks else None
        }
    
    def _detect_backend_stack(self, repo: Path) -> Dict:
        """Backend API detection with runtime-specific analysis"""
        
        backend_indicators = {
            'nodejs': {
                'files': ['package.json', 'server.js', 'app.js', 'index.js'],
                'dependencies': ['express', 'fastify', 'koa', '@nestjs/core'],
                'directories': ['routes', 'controllers', 'middleware'],
                'deployment': 'lambda'  # or 'ec2' for complex apps
            },
            'python': {
                'files': ['requirements.txt', 'app.py', 'main.py', 'manage.py'],
                'dependencies': ['flask', 'django', 'fastapi', 'tornado'],
                'directories': ['app', 'api', 'views'],
                'deployment': 'lambda'  # or 'ecs' for Django
            },
            'php': {
                'files': ['composer.json', 'index.php', 'app.php'],
                'dependencies': ['laravel/framework', 'symfony/symfony'],
                'directories': ['app', 'public', 'routes'],
                'deployment': 'ec2'  # PHP typically needs EC2
            },
            'java': {
                'files': ['pom.xml', 'build.gradle', 'src/main/java'],
                'dependencies': ['spring-boot', 'spring-framework'],
                'directories': ['src/main/java', 'src/main/resources'],
                'deployment': 'ecs'  # Java containers
            }
        }
        
        detected_backends = []
        
        for runtime, indicators in backend_indicators.items():
            score = 0
            matches = []
            
            # Check for key files
            for file in indicators['files']:
                if (repo / file).exists():
                    score += 0.4
                    matches.append(f"file: {file}")
            
            # Check dependencies in respective files
            if runtime == 'nodejs':
                pkg = self._read_package_json(repo)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                for dep in indicators['dependencies']:
                    if dep in deps:
                        score += 0.3
                        matches.append(f"dependency: {dep}")
            
            # Check directories
            for directory in indicators['directories']:
                if (repo / directory).exists():
                    score += 0.2
                    matches.append(f"directory: {directory}")
            
            if score > 0:
                detected_backends.append({
                    'runtime': runtime,
                    'confidence': min(score, 1.0),
                    'matches': matches,
                    'recommended_deployment': indicators['deployment']
                })
        
        detected_backends.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'detected': detected_backends,
            'primary': detected_backends[0] if detected_backends else None
        }
    
    def _detect_database_requirements(self, repo: Path) -> Dict:
        """Database requirement detection with connection analysis"""
        
        database_indicators = {
            'mysql': ['mysql2', 'mysql', 'pymysql', 'PDO', 'jdbc:mysql'],
            'postgresql': ['pg', 'psycopg2', 'PostgreSQL', 'jdbc:postgresql'],
            'mongodb': ['mongodb', 'mongoose', 'pymongo', 'MongoDB\\Client'],
            'sqlite': ['sqlite3', 'better-sqlite3', 'pysqlite'],
            'redis': ['redis', 'ioredis', 'redis-py']
        }
        
        detected_databases = []
        
        # Check package.json for Node.js dependencies
        pkg = self._read_package_json(repo)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        for db_type, indicators in database_indicators.items():
            matches = []
            score = 0
            
            for indicator in indicators:
                if indicator in deps:
                    matches.append(f"dependency: {indicator}")
                    score += 0.5
            
            # Check for config files
            config_files = [
                f"{db_type}.conf", f"config/{db_type}.js", 
                f".env" # Check for database URLs in .env
            ]
            
            for config_file in config_files:
                if (repo / config_file).exists():
                    # For .env files, check content for database URLs
                    if config_file == '.env':
                        try:
                            env_content = (repo / config_file).read_text()
                            if f"{db_type.upper()}_URL" in env_content or f"DATABASE_URL" in env_content:
                                matches.append(f"config: {config_file}")
                                score += 0.3
                        except:
                            pass
                    else:
                        matches.append(f"config: {config_file}")
                        score += 0.3
            
            if score > 0:
                detected_databases.append({
                    'database': db_type,
                    'confidence': min(score, 1.0),
                    'matches': matches
                })
        
        detected_databases.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'detected': detected_databases,
            'primary': detected_databases[0] if detected_databases else None
        }
    
    def _detect_infrastructure_needs(self, repo: Path) -> Dict:
        """Infrastructure requirement detection"""
        
        infrastructure_needs = {
            'containers': False,
            'load_balancer': False,
            'cdn': True,  # Always beneficial for static assets
            'caching': False,
            'background_jobs': False
        }
        
        # Check for containerization
        if any((repo / f).exists() for f in ['Dockerfile', 'docker-compose.yml', '.dockerignore']):
            infrastructure_needs['containers'] = True
        
        # Check for load balancing needs (multiple services)
        service_indicators = ['docker-compose.yml', 'kubernetes/', 'microservices/']
        if any((repo / f).exists() for f in service_indicators):
            infrastructure_needs['load_balancer'] = True
        
        # Check for caching needs
        pkg = self._read_package_json(repo)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        if any(cache_dep in deps for cache_dep in ['redis', 'memcached', 'node-cache']):
            infrastructure_needs['caching'] = True
        
        # Check for background job processing
        job_indicators = ['bull', 'agenda', 'celery', 'sidekiq', 'rq']
        if any(job_dep in deps for job_dep in job_indicators):
            infrastructure_needs['background_jobs'] = True
        
        return infrastructure_needs
    
    def _generate_recommendation(self, frontend, backend, database, infrastructure) -> StackRecommendation:
        """Generate comprehensive deployment recommendation"""
        
        # Determine primary stack
        if backend['primary'] and database['primary']:
            # Full-stack application
            primary_stack = 'fullstack'
            deployment_strategy = 'multi-tier'
            
            secondary_stacks = []
            if frontend['primary']:
                secondary_stacks.append(frontend['primary']['framework'])
            if backend['primary']:
                secondary_stacks.append(f"api-{backend['primary']['runtime']}")
            if database['primary']:
                secondary_stacks.append(f"db-{database['primary']['database']}")
                
        elif backend['primary']:
            # API-only application
            primary_stack = f"api-{backend['primary']['runtime']}"
            deployment_strategy = backend['primary']['recommended_deployment']
            secondary_stacks = []
            
        elif frontend['primary']:
            # Frontend-only application
            primary_stack = frontend['primary']['framework']
            deployment_strategy = 'static' if primary_stack in ['static'] else 'spa'
            secondary_stacks = []
            
        else:
            # Fallback to static
            primary_stack = 'static'
            deployment_strategy = 'static'
            secondary_stacks = []
        
        # Calculate confidence score
        confidence_scores = []
        if frontend['primary']:
            confidence_scores.append(frontend['primary']['confidence'])
        if backend['primary']:
            confidence_scores.append(backend['primary']['confidence'])
        if database['primary']:
            confidence_scores.append(database['primary']['confidence'])
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Generate reasoning
        reasoning_parts = []
        if frontend['primary']:
            reasoning_parts.append(f"Frontend: {frontend['primary']['framework']} ({frontend['primary']['confidence']:.1%} confidence)")
        if backend['primary']:
            reasoning_parts.append(f"Backend: {backend['primary']['runtime']} ({backend['primary']['confidence']:.1%} confidence)")
        if database['primary']:
            reasoning_parts.append(f"Database: {database['primary']['database']} ({database['primary']['confidence']:.1%} confidence)")
        
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Basic static site detection"
        
        # Generate resource recommendations
        recommended_resources = self._generate_resource_recommendations(
            primary_stack, secondary_stacks, infrastructure
        )
        
        # Generate warnings
        warnings = []
        if primary_stack == 'fullstack' and not infrastructure['load_balancer']:
            warnings.append("Consider load balancer for production full-stack deployment")
        
        if database['primary'] and not infrastructure['caching']:
            warnings.append("Consider Redis caching for database-backed applications")
        
        return StackRecommendation(
            primary_stack=primary_stack,
            secondary_stacks=secondary_stacks,
            deployment_strategy=deployment_strategy,
            confidence_score=overall_confidence,
            reasoning=reasoning,
            warnings=warnings,
            recommended_resources=recommended_resources
        )
    
    def _generate_resource_recommendations(self, primary_stack: str, secondary_stacks: List[str], infrastructure: Dict) -> Dict[str, str]:
        """Generate AWS resource recommendations based on detected stack"""
        
        resources = {}
        
        # Base resources for all deployments
        resources['iam'] = 'Least-privilege IAM roles and policies'
        resources['cloudwatch'] = 'Comprehensive logging and monitoring'
        
        if primary_stack == 'fullstack':
            # Full-stack applications need comprehensive infrastructure
            resources.update({
                'vpc': 'Isolated VPC with public/private subnets',
                'rds': 'Multi-AZ RDS instance with automated backups',
                'ecs': 'ECS Fargate for containerized backend services',
                'alb': 'Application Load Balancer for traffic distribution',
                's3': 'S3 + CloudFront for frontend static assets',
                'elasticache': 'Redis for session storage and caching'
            })
            
        elif primary_stack.startswith('api-'):
            # API-only deployments
            runtime = primary_stack.split('-')[1]
            if runtime in ['nodejs', 'python']:
                resources['lambda'] = f'AWS Lambda for {runtime} API'
                resources['apigateway'] = 'API Gateway for REST endpoints'
            else:
                resources['ecs'] = f'ECS Fargate for {runtime} containers'
                resources['alb'] = 'Application Load Balancer'
            
        elif primary_stack in ['nextjs', 'react', 'vue', 'angular']:
            # SPA deployments
            resources.update({
                's3': 'S3 for static hosting',
                'cloudfront': 'CloudFront CDN for global distribution'
            })
            
        elif primary_stack == 'static':
            # Pure static sites
            resources.update({
                's3': 'S3 for static file hosting',
                'cloudfront': 'CloudFront for performance optimization'
            })
        
        return resources
    
    def _read_package_json(self, repo: Path) -> Dict:
        """Safely read package.json"""
        try:
            pkg_file = repo / "package.json"
            if pkg_file.exists():
                return json.loads(pkg_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to read package.json from {repo}: {e}")
        return {}
    
    def _analyze_files(self, repo: Path) -> Dict:
        """Basic file analysis for documentation detection"""
        file_types = {}
        total_files = 0
        source_files_count = 0
        
        # Define source code extensions
        source_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs',
            '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
            '.vue', '.svelte', '.html', '.css', '.scss', '.less'
        }
        
        try:
            for file_path in repo.rglob('*'):
                if file_path.is_file() and not any(part.startswith('.git') for part in file_path.parts):
                    total_files += 1
                    ext = file_path.suffix.lower()
                    
                    # Count file types
                    if ext not in file_types:
                        file_types[ext] = 0
                    file_types[ext] += 1
                    
                    # Count source files
                    if ext in source_extensions:
                        source_files_count += 1
                        
        except Exception as e:
            logger.warning(f"Failed to analyze files in {repo}: {e}")
        
        return {
            'file_types': file_types,
            'total_files': total_files,
            'source_files_count': source_files_count
        }

# Usage example - this will be integrated into the main analysis endpoint
def analyze_and_recommend(repo_path: str) -> StackRecommendation:
    """
    Main function that will be called by the API to automatically detect
    and recommend the best deployment strategy
    """
    detector = EnhancedStackDetector()
    recommendation = detector.analyze_repository(repo_path)
    
    logger.info(f"Repository analysis complete:")
    logger.info(f"  Primary Stack: {recommendation.primary_stack}")
    logger.info(f"  Strategy: {recommendation.deployment_strategy}")
    logger.info(f"  Confidence: {recommendation.confidence_score:.1%}")
    logger.info(f"  Reasoning: {recommendation.reasoning}")
    
    return recommendation
