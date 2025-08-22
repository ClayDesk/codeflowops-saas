# Phase 1: Enhanced Stack Detection
# backend/detectors/enhanced_stack_detector_v2.py

"""
Advanced multi-stack detection with runtime analysis
This is a NEW enhanced detector that complements existing detection without replacement
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RuntimeType(Enum):
    NODEJS = "nodejs"
    PYTHON = "python"
    PHP = "php"
    JAVA = "java"
    DOTNET = "dotnet"
    RUBY = "ruby"
    GO = "go"

class StackType(Enum):
    # Frontend stacks
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    STATIC = "static"
    
    # Backend API stacks
    API_NODEJS = "api-nodejs"
    API_PYTHON = "api-python"
    API_PHP = "api-php"
    API_JAVA = "api-java"
    API_DOTNET = "api-dotnet"
    API_RUBY = "api-ruby"
    API_GO = "api-go"
    
    # Database stacks
    DATABASE_MYSQL = "database-mysql"
    DATABASE_POSTGRESQL = "database-postgresql"
    DATABASE_MONGODB = "database-mongodb"
    DATABASE_REDIS = "database-redis"
    
    # Full-stack combinations
    FULLSTACK_REACT_NODEJS_MYSQL = "fullstack-react-nodejs-mysql"
    FULLSTACK_VUE_PYTHON_POSTGRES = "fullstack-vue-python-postgres"

@dataclass
class StackDetectionResult:
    """Enhanced stack detection result"""
    primary_stack: StackType
    runtime: RuntimeType
    secondary_stacks: List[StackType]
    confidence_score: float  # 0.0 to 1.0
    detected_files: List[str]
    package_dependencies: Dict[str, str]
    build_tools: List[str]
    deployment_config: Dict[str, Any]
    database_dependencies: List[str]

class EnhancedStackDetectorV2:
    """
    Advanced multi-stack detection with improved accuracy
    ✅ Detects complex full-stack applications and deployment patterns
    """
    
    def __init__(self):
        # ✅ Enhanced detection patterns with confidence scoring
        self.detection_patterns = {
            StackType.REACT: {
                'package_files': ['package.json'],
                'required_dependencies': ['react', 'react-dom'],
                'optional_dependencies': ['react-scripts', '@craco/craco', 'vite'],
                'file_patterns': ['src/App.js', 'src/App.tsx', 'src/index.js', 'src/index.tsx'],
                'config_files': ['craco.config.js', 'vite.config.js', '.env'],
                'confidence_base': 0.9
            },
            StackType.VUE: {
                'package_files': ['package.json'],
                'required_dependencies': ['vue'],
                'optional_dependencies': ['@vue/cli-service', 'nuxt', 'vite'],
                'file_patterns': ['src/App.vue', 'src/main.js', 'src/main.ts'],
                'config_files': ['vue.config.js', 'nuxt.config.js'],
                'confidence_base': 0.9
            },
            StackType.ANGULAR: {
                'package_files': ['package.json'],
                'required_dependencies': ['@angular/core', '@angular/cli'],
                'optional_dependencies': ['@angular/common', '@angular/platform-browser'],
                'file_patterns': ['src/app/app.component.ts', 'angular.json'],
                'config_files': ['angular.json', 'tsconfig.json'],
                'confidence_base': 0.9
            },
            StackType.API_NODEJS: {
                'package_files': ['package.json'],
                'required_dependencies': ['express', 'fastify', 'koa', 'nestjs'],
                'optional_dependencies': ['cors', 'helmet', 'morgan', 'winston'],
                'file_patterns': ['server.js', 'app.js', 'index.js', 'src/main.ts'],
                'config_files': ['nest-cli.json', 'tsconfig.json'],
                'confidence_base': 0.85
            },
            StackType.API_PYTHON: {
                'package_files': ['requirements.txt', 'pyproject.toml', 'Pipfile'],
                'required_dependencies': ['flask', 'django', 'fastapi', 'tornado'],
                'optional_dependencies': ['gunicorn', 'uvicorn', 'celery', 'redis'],
                'file_patterns': ['app.py', 'main.py', 'manage.py', 'wsgi.py'],
                'config_files': ['settings.py', 'config.py', '.env'],
                'confidence_base': 0.85
            },
            StackType.API_PHP: {
                'package_files': ['composer.json'],
                'required_dependencies': ['laravel/framework', 'symfony/symfony', 'slim/slim'],
                'optional_dependencies': ['doctrine/orm', 'monolog/monolog'],
                'file_patterns': ['index.php', 'artisan', 'app/', 'src/'],
                'config_files': ['.env', 'config/', 'bootstrap/'],
                'confidence_base': 0.8
            },
            StackType.API_JAVA: {
                'package_files': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
                'required_dependencies': ['spring-boot', 'spring-framework', 'javax.servlet'],
                'optional_dependencies': ['spring-security', 'spring-data-jpa'],
                'file_patterns': ['src/main/java/', 'Application.java'],
                'config_files': ['application.yml', 'application.properties'],
                'confidence_base': 0.8
            }
        }
        
        # ✅ Database detection patterns
        self.database_patterns = {
            StackType.DATABASE_MYSQL: {
                'dependencies': ['mysql2', 'mysql-connector-python', 'PyMySQL', 'mysql-connector-java'],
                'config_indicators': ['mysql', 'mariadb'],
                'confidence_base': 0.9
            },
            StackType.DATABASE_POSTGRESQL: {
                'dependencies': ['pg', 'psycopg2', 'postgresql', 'postgres'],
                'config_indicators': ['postgres', 'postgresql'],
                'confidence_base': 0.9
            },
            StackType.DATABASE_MONGODB: {
                'dependencies': ['mongoose', 'pymongo', 'mongodb-driver'],
                'config_indicators': ['mongodb', 'mongo'],
                'confidence_base': 0.85
            },
            StackType.DATABASE_REDIS: {
                'dependencies': ['redis', 'ioredis', 'redis-py', 'jedis'],
                'config_indicators': ['redis'],
                'confidence_base': 0.8
            }
        }
    
    def detect_stack(self, repo_path: str) -> StackDetectionResult:
        """
        Detect stack with enhanced accuracy and full-stack support
        ✅ Analyzes dependencies, files, and configuration for comprehensive detection
        """
        
        repo_path = Path(repo_path)
        logger.info(f"🔍 Starting enhanced stack detection for: {repo_path}")
        
        # Phase 1: Scan repository structure
        file_structure = self._scan_repository_structure(repo_path)
        
        # Phase 2: Analyze dependencies
        dependencies = self._analyze_dependencies(repo_path)
        
        # Phase 3: Detect primary stack
        primary_detection = self._detect_primary_stack(file_structure, dependencies)
        
        # Phase 4: Detect secondary stacks and databases
        secondary_stacks = self._detect_secondary_stacks(file_structure, dependencies)
        database_stacks = self._detect_database_dependencies(dependencies)
        
        # Phase 5: Determine runtime
        runtime = self._determine_runtime(primary_detection['stack'], dependencies)
        
        # Phase 6: Analyze deployment configuration
        deployment_config = self._analyze_deployment_config(repo_path)
        
        # Phase 7: Build comprehensive result
        result = StackDetectionResult(
            primary_stack=primary_detection['stack'],
            runtime=runtime,
            secondary_stacks=secondary_stacks + database_stacks,
            confidence_score=primary_detection['confidence'],
            detected_files=file_structure['significant_files'],
            package_dependencies=dependencies,
            build_tools=self._detect_build_tools(file_structure, dependencies),
            deployment_config=deployment_config,
            database_dependencies=database_stacks
        )
        
        logger.info(f"✅ Stack detection complete: {result.primary_stack.value} (confidence: {result.confidence_score:.2f})")
        return result
    
    def _scan_repository_structure(self, repo_path: Path) -> Dict[str, Any]:
        """Scan repository structure for significant files and patterns"""
        
        structure = {
            'package_files': [],
            'config_files': [],
            'source_directories': [],
            'significant_files': [],
            'total_files': 0
        }
        
        # Files to specifically look for
        significant_files = {
            'package.json', 'requirements.txt', 'composer.json', 'pom.xml', 'build.gradle',
            'Dockerfile', 'docker-compose.yml', 'next.config.js', 'vue.config.js',
            'angular.json', 'tsconfig.json', 'webpack.config.js', 'vite.config.js',
            'manage.py', 'app.py', 'server.js', 'index.php', 'artisan'
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip common ignore directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'vendor', 'target']]
                
                for file in files:
                    structure['total_files'] += 1
                    
                    if file in significant_files:
                        full_path = os.path.join(root, file)
                        relative_path = os.path.relpath(full_path, repo_path)
                        structure['significant_files'].append(relative_path)
                        
                        if file in ['package.json', 'requirements.txt', 'composer.json', 'pom.xml', 'build.gradle']:
                            structure['package_files'].append(relative_path)
                        else:
                            structure['config_files'].append(relative_path)
                
                # Track source directories
                for dir_name in dirs:
                    if dir_name in ['src', 'app', 'pages', 'components', 'lib', 'api']:
                        structure['source_directories'].append(dir_name)
        
        except Exception as e:
            logger.warning(f"Error scanning repository structure: {e}")
        
        return structure
    
    def _analyze_dependencies(self, repo_path: Path) -> Dict[str, str]:
        """Analyze package dependencies from various package files"""
        
        dependencies = {}
        
        # Node.js dependencies
        package_json_path = repo_path / 'package.json'
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    
                    # Merge dependencies and devDependencies
                    deps = package_data.get('dependencies', {})
                    dev_deps = package_data.get('devDependencies', {})
                    dependencies.update(deps)
                    dependencies.update(dev_deps)
                    
            except Exception as e:
                logger.warning(f"Error reading package.json: {e}")
        
        # Python dependencies
        requirements_path = repo_path / 'requirements.txt'
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '==' in line:
                                pkg, version = line.split('==')
                                dependencies[pkg.strip()] = version.strip()
                            elif '>=' in line:
                                pkg, version = line.split('>=')
                                dependencies[pkg.strip()] = f">={version.strip()}"
                            else:
                                dependencies[line] = "latest"
            except Exception as e:
                logger.warning(f"Error reading requirements.txt: {e}")
        
        # PHP dependencies
        composer_json_path = repo_path / 'composer.json'
        if composer_json_path.exists():
            try:
                with open(composer_json_path, 'r') as f:
                    composer_data = json.load(f)
                    
                    deps = composer_data.get('require', {})
                    dev_deps = composer_data.get('require-dev', {})
                    dependencies.update(deps)
                    dependencies.update(dev_deps)
                    
            except Exception as e:
                logger.warning(f"Error reading composer.json: {e}")
        
        # Java dependencies (basic Maven support)
        pom_xml_path = repo_path / 'pom.xml'
        if pom_xml_path.exists():
            try:
                with open(pom_xml_path, 'r') as f:
                    content = f.read()
                    # Simple regex to extract spring dependencies
                    spring_matches = re.findall(r'<groupId>org\.springframework.*?</groupId>', content)
                    for match in spring_matches:
                        dependencies['spring-framework'] = 'detected'
                        
            except Exception as e:
                logger.warning(f"Error reading pom.xml: {e}")
        
        return dependencies
    
    def _detect_primary_stack(self, file_structure: Dict[str, Any], dependencies: Dict[str, str]) -> Dict[str, Any]:
        """Detect primary stack type with confidence scoring"""
        
        scores = {}
        
        for stack_type, patterns in self.detection_patterns.items():
            score = patterns['confidence_base']
            
            # Check required dependencies
            required_deps = patterns['required_dependencies']
            matching_deps = sum(1 for dep in required_deps if any(dep in key.lower() for key in dependencies.keys()))
            
            if matching_deps == 0:
                score = 0  # No required dependencies found
            else:
                score *= (matching_deps / len(required_deps))
            
            # Boost score for optional dependencies
            optional_deps = patterns.get('optional_dependencies', [])
            optional_matches = sum(1 for dep in optional_deps if any(dep in key.lower() for key in dependencies.keys()))
            if optional_matches > 0:
                score *= (1 + (optional_matches * 0.1))
            
            # Boost score for file patterns
            file_patterns = patterns.get('file_patterns', [])
            file_matches = sum(1 for pattern in file_patterns if any(pattern in file for file in file_structure['significant_files']))
            if file_matches > 0:
                score *= (1 + (file_matches * 0.15))
            
            # Boost score for config files
            config_files = patterns.get('config_files', [])
            config_matches = sum(1 for config in config_files if any(config in file for file in file_structure['significant_files']))
            if config_matches > 0:
                score *= (1 + (config_matches * 0.1))
            
            scores[stack_type] = min(score, 1.0)  # Cap at 1.0
        
        # Find stack with highest score
        if scores:
            best_stack = max(scores, key=scores.get)
            return {
                'stack': best_stack,
                'confidence': scores[best_stack]
            }
        else:
            return {
                'stack': StackType.STATIC,
                'confidence': 0.5
            }
    
    def _detect_secondary_stacks(self, file_structure: Dict[str, Any], dependencies: Dict[str, str]) -> List[StackType]:
        """Detect secondary stacks (e.g., API backend for React frontend)"""
        
        secondary_stacks = []
        
        # Look for API indicators
        api_indicators = {
            StackType.API_NODEJS: ['express', 'fastify', 'koa', 'server.js', 'api/'],
            StackType.API_PYTHON: ['flask', 'django', 'fastapi', 'app.py', 'manage.py'],
            StackType.API_PHP: ['laravel', 'symfony', 'index.php', 'artisan'],
            StackType.API_JAVA: ['spring-boot', 'Application.java', 'pom.xml']
        }
        
        for stack_type, indicators in api_indicators.items():
            score = 0
            for indicator in indicators:
                if any(indicator in key.lower() for key in dependencies.keys()):
                    score += 0.3
                if any(indicator in file for file in file_structure['significant_files']):
                    score += 0.2
            
            if score >= 0.3:  # Threshold for secondary stack detection
                secondary_stacks.append(stack_type)
        
        return secondary_stacks
    
    def _detect_database_dependencies(self, dependencies: Dict[str, str]) -> List[StackType]:
        """Detect database dependencies"""
        
        database_stacks = []
        
        for db_type, patterns in self.database_patterns.items():
            score = 0
            for dep_pattern in patterns['dependencies']:
                if any(dep_pattern in key.lower() for key in dependencies.keys()):
                    score += patterns['confidence_base']
                    break  # Found at least one matching dependency
            
            if score >= 0.7:  # Threshold for database detection
                database_stacks.append(db_type)
        
        return database_stacks
    
    def _determine_runtime(self, primary_stack: StackType, dependencies: Dict[str, str]) -> RuntimeType:
        """Determine runtime based on primary stack and dependencies"""
        
        # Stack to runtime mapping
        stack_runtime_map = {
            StackType.REACT: RuntimeType.NODEJS,
            StackType.VUE: RuntimeType.NODEJS,
            StackType.ANGULAR: RuntimeType.NODEJS,
            StackType.API_NODEJS: RuntimeType.NODEJS,
            StackType.API_PYTHON: RuntimeType.PYTHON,
            StackType.API_PHP: RuntimeType.PHP,
            StackType.API_JAVA: RuntimeType.JAVA,
            StackType.API_DOTNET: RuntimeType.DOTNET,
            StackType.API_RUBY: RuntimeType.RUBY,
            StackType.API_GO: RuntimeType.GO,
            StackType.STATIC: RuntimeType.NODEJS  # Default for static sites
        }
        
        return stack_runtime_map.get(primary_stack, RuntimeType.NODEJS)
    
    def _detect_build_tools(self, file_structure: Dict[str, Any], dependencies: Dict[str, str]) -> List[str]:
        """Detect build tools and bundlers"""
        
        build_tools = []
        
        # Build tool indicators
        build_tool_indicators = {
            'webpack': ['webpack', 'webpack.config.js'],
            'vite': ['vite', 'vite.config.js'],
            'rollup': ['rollup', 'rollup.config.js'],
            'parcel': ['parcel'],
            'grunt': ['grunt', 'Gruntfile.js'],
            'gulp': ['gulp', 'gulpfile.js'],
            'maven': ['pom.xml'],
            'gradle': ['build.gradle', 'build.gradle.kts'],
            'npm': ['package.json'],
            'yarn': ['yarn.lock'],
            'composer': ['composer.json']
        }
        
        for tool, indicators in build_tool_indicators.items():
            found = False
            for indicator in indicators:
                if (any(indicator in key.lower() for key in dependencies.keys()) or 
                    any(indicator in file for file in file_structure['significant_files'])):
                    found = True
                    break
            
            if found:
                build_tools.append(tool)
        
        return build_tools
    
    def _analyze_deployment_config(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze deployment configuration files"""
        
        config = {
            'has_dockerfile': False,
            'has_docker_compose': False,
            'has_ci_config': False,
            'deployment_platform': None,
            'environment_files': []
        }
        
        # Check for Docker
        if (repo_path / 'Dockerfile').exists():
            config['has_dockerfile'] = True
        
        if (repo_path / 'docker-compose.yml').exists() or (repo_path / 'docker-compose.yaml').exists():
            config['has_docker_compose'] = True
        
        # Check for CI/CD configurations
        ci_files = [
            '.github/workflows/',
            '.gitlab-ci.yml',
            'azure-pipelines.yml',
            'buildspec.yml',
            'cloudbuild.yaml'
        ]
        
        for ci_file in ci_files:
            if (repo_path / ci_file).exists():
                config['has_ci_config'] = True
                break
        
        # Check for environment files
        env_files = ['.env', '.env.example', '.env.local', '.env.production']
        for env_file in env_files:
            if (repo_path / env_file).exists():
                config['environment_files'].append(env_file)
        
        # Detect deployment platform preferences
        if (repo_path / 'vercel.json').exists():
            config['deployment_platform'] = 'vercel'
        elif (repo_path / 'netlify.toml').exists():
            config['deployment_platform'] = 'netlify'
        elif (repo_path / 'now.json').exists():
            config['deployment_platform'] = 'vercel'  # Legacy Vercel config
        
        return config
