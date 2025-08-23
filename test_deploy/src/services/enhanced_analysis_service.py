# Enhanced Repository Analysis Service (Claude dependencies removed)
import os
import json
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import yaml

# Claude service removed - now using traditional Terraform templates
from ..controllers.analysisController import AnalysisController

class EnhancedAnalysisService:
    """
    Enhanced repository analysis service for Terraform template selection
    """
    
    def __init__(self):
        self.analysis_controller = AnalysisController()
    
    async def analyze_repository_for_template_selection(
        self, 
        session_id: str, 
        repo_path: str, 
        repo_url: str
    ) -> Dict[str, Any]:
        """
        Perform comprehensive repository analysis for Terraform template selection
        
        Args:
            session_id: Deployment session ID
            repo_path: Local path to downloaded repository
            repo_url: Original GitHub repository URL
            
        Returns:
            Enhanced analysis results for template selection
        """
        
        # Start with existing CodeFlowOps analysis
        base_analysis = await self.analysis_controller.analyze_repository(session_id, repo_url)
        
        # Enhance with additional context for template selection
        enhanced_analysis = {
            **base_analysis,
            "template_context": await self._extract_template_context(repo_path),
            "performance_requirements": await self._analyze_performance_requirements(repo_path),
            "security_requirements": await self._analyze_security_requirements(repo_path),
            "scaling_hints": await self._analyze_scaling_requirements(repo_path),
            "environment_variables": await self._extract_environment_variables(repo_path),
            "external_services": await self._detect_external_services(repo_path),
            "deployment_complexity": await self._assess_deployment_complexity(repo_path, base_analysis)
        }
        
        return enhanced_analysis
    
    async def analyze_for_terraform_template(self, repo_path: str) -> Dict[str, Any]:
        """
        Simplified analysis method for Smart Deploy Terraform template selection
        """
        try:
            # Perform basic repository analysis
            analysis = {
                "project_type": await self._detect_project_type(repo_path),
                "framework": await self._detect_framework(repo_path),
                "languages": await self._detect_languages(repo_path),
                "dependencies": await self._extract_dependencies(repo_path),
                "build_system": await self._detect_build_system(repo_path),
                "environment_vars": await self._extract_environment_variables(repo_path),
                "deployment_hints": await self._get_deployment_hints(repo_path),
                "scaling_requirements": await self._analyze_scaling_requirements(repo_path),
                "estimated_complexity": "medium"
            }
            
            return analysis
        except Exception as e:
            # Return minimal analysis if detailed analysis fails
            return {
                "project_type": "web_application",
                "framework": "unknown",
                "languages": ["JavaScript"],
                "dependencies": [],
                "build_system": "npm",
                "environment_vars": {},
                "deployment_hints": {
                    "port": 3000,
                    "build_command": "npm run build",
                    "start_command": "npm start"
                },
                "scaling_requirements": "standard",
                "estimated_complexity": "medium",
                "analysis_error": str(e)
            }
    
    async def _extract_template_context(self, repo_path: str) -> Dict[str, Any]:
        """Extract detailed context about the repository for template selection"""
        
        context = {
            "file_structure": await self._analyze_file_structure(repo_path),
            "configuration_files": await self._find_configuration_files(repo_path),
            "documentation": await self._extract_documentation_hints(repo_path),
            "ci_cd_present": await self._check_ci_cd_configs(repo_path),
            "testing_setup": await self._analyze_testing_setup(repo_path)
        }
        
        return context
    
    async def _analyze_file_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository file structure in detail"""
        
        structure = {
            "total_files": 0,
            "directories": [],
            "file_types": {},
            "important_files": [],
            "assets_present": False,
            "public_folder": None
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip node_modules and other irrelevant directories
                dirs[:] = [d for d in dirs if d not in [
                    'node_modules', '.git', '__pycache__', '.venv', 
                    'venv', 'dist', 'build', '.next', '.nuxt'
                ]]
                
                rel_root = os.path.relpath(root, repo_path)
                if rel_root != '.':
                    structure["directories"].append(rel_root)
                
                for file in files:
                    structure["total_files"] += 1
                    
                    # Count file types
                    ext = Path(file).suffix.lower()
                    structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                    
                    # Identify important files
                    if file in [
                        'package.json', 'requirements.txt', 'Dockerfile', 
                        'docker-compose.yml', 'README.md', 'next.config.js',
                        'vue.config.js', 'angular.json', 'tsconfig.json'
                    ]:
                        structure["important_files"].append(os.path.join(rel_root, file))
                    
                    # Check for assets
                    if ext in ['.png', '.jpg', '.jpeg', '.svg', '.ico', '.css', '.scss']:
                        structure["assets_present"] = True
                
                # Check for public/static folders
                if any(d in dirs for d in ['public', 'static', 'assets']):
                    structure["public_folder"] = rel_root
        
        except Exception as e:
            structure["error"] = str(e)
        
        return structure
    
    async def _find_configuration_files(self, repo_path: str) -> List[Dict[str, str]]:
        """Find and analyze configuration files"""
        
        config_files = []
        config_patterns = {
            'package.json': 'npm',
            'requirements.txt': 'python',
            'Pipfile': 'python',
            'setup.py': 'python',
            'pyproject.toml': 'python',
            'Dockerfile': 'docker',
            'docker-compose.yml': 'docker',
            'docker-compose.yaml': 'docker',
            'next.config.js': 'react',
            'nuxt.config.js': 'vue',
            'vue.config.js': 'vue',
            'angular.json': 'angular',
            'gatsby-config.js': 'gatsby',
            'svelte.config.js': 'svelte',
            'vite.config.js': 'vite',
            'webpack.config.js': 'webpack',
            'tsconfig.json': 'typescript',
            '.env.example': 'environment',
            '.env.template': 'environment'
        }
        
        for root, dirs, files in os.walk(repo_path):
            # Skip irrelevant directories
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build']]
            
            for file in files:
                if file in config_patterns:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # Read file content for additional analysis
                    content_summary = await self._summarize_config_file(file_path, config_patterns[file])
                    
                    config_files.append({
                        "file": rel_path,
                        "type": config_patterns[file],
                        "summary": content_summary
                    })
        
        return config_files
    
    async def _summarize_config_file(self, file_path: str, file_type: str) -> str:
        """Summarize configuration file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_type == 'npm' and 'package.json' in file_path:
                # Parse package.json for scripts and dependencies
                package_data = json.loads(content)
                scripts = list(package_data.get('scripts', {}).keys())
                deps = len(package_data.get('dependencies', {}))
                dev_deps = len(package_data.get('devDependencies', {}))
                return f"Scripts: {scripts}, Deps: {deps}, DevDeps: {dev_deps}"
            
            elif file_type == 'python' and 'requirements.txt' in file_path:
                # Count Python dependencies
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                return f"Python packages: {len(lines)}"
            
            elif file_type == 'docker':
                # Analyze Dockerfile commands
                if 'Dockerfile' in file_path:
                    commands = [line.split()[0] for line in content.split('\n') if line.strip() and not line.startswith('#')]
                    return f"Docker commands: {set(commands)}"
                else:
                    return "Docker Compose configuration"
            
            elif file_type == 'typescript':
                # Check TypeScript configuration
                ts_config = json.loads(content)
                return f"TS target: {ts_config.get('compilerOptions', {}).get('target', 'unknown')}"
            
            else:
                return f"Configuration file present ({len(content)} chars)"
        
        except Exception:
            return "Configuration file (could not parse)"
    
    async def _extract_documentation_hints(self, repo_path: str) -> Dict[str, str]:
        """Extract hints from documentation files"""
        
        docs = {}
        doc_files = ['README.md', 'README.rst', 'docs/README.md', 'DEPLOYMENT.md', 'INSTALL.md']
        
        for doc_file in doc_files:
            doc_path = os.path.join(repo_path, doc_file)
            if os.path.exists(doc_path):
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()[:1000]  # First 1000 chars
                    
                    # Look for deployment hints
                    hints = []
                    if 'port' in content.lower():
                        hints.append("custom_port")
                    if 'database' in content.lower():
                        hints.append("database_required")
                    if 'redis' in content.lower():
                        hints.append("redis_required")
                    if 'docker' in content.lower():
                        hints.append("docker_ready")
                    if 'environment' in content.lower() or 'env' in content.lower():
                        hints.append("env_vars_required")
                    
                    docs[doc_file] = {
                        "hints": hints,
                        "preview": content[:200] + "..." if len(content) > 200 else content
                    }
                
                except Exception:
                    docs[doc_file] = {"hints": [], "preview": "Could not read file"}
        
        return docs
    
    async def _check_ci_cd_configs(self, repo_path: str) -> Dict[str, bool]:
        """Check for CI/CD configuration files"""
        
        ci_cd_files = {
            '.github/workflows': 'github_actions',
            '.gitlab-ci.yml': 'gitlab_ci',
            'circle.yml': 'circle_ci',
            '.circleci/config.yml': 'circle_ci',
            'travis.yml': 'travis_ci',
            '.travis.yml': 'travis_ci',
            'azure-pipelines.yml': 'azure_pipelines',
            'buildspec.yml': 'aws_codebuild',
            'Jenkinsfile': 'jenkins'
        }
        
        present = {}
        for path, name in ci_cd_files.items():
            full_path = os.path.join(repo_path, path)
            present[name] = os.path.exists(full_path)
        
        return present
    
    async def _analyze_testing_setup(self, repo_path: str) -> Dict[str, Any]:
        """Analyze testing configuration and setup"""
        
        testing = {
            "frameworks": [],
            "test_files_count": 0,
            "coverage_config": False,
            "test_scripts": []
        }
        
        # Check package.json for test scripts and frameworks
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.loads(f.read())
                
                # Check dependencies for testing frameworks
                all_deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                test_frameworks = ['jest', 'mocha', 'jasmine', 'cypress', 'playwright', 'vitest']
                testing["frameworks"] = [fw for fw in test_frameworks if fw in all_deps]
                
                # Check test scripts
                scripts = package_data.get('scripts', {})
                testing["test_scripts"] = [k for k in scripts.keys() if 'test' in k]
            
            except Exception:
                pass
        
        # Count test files
        test_patterns = ['test', 'spec', '__tests__']
        for root, dirs, files in os.walk(repo_path):
            if any(pattern in root for pattern in test_patterns):
                testing["test_files_count"] += len(files)
        
        # Check for coverage configuration
        coverage_files = ['.coveragerc', 'coverage.json', 'jest.config.js']
        testing["coverage_config"] = any(
            os.path.exists(os.path.join(repo_path, cf)) for cf in coverage_files
        )
        
        return testing
    
    async def _analyze_performance_requirements(self, repo_path: str) -> Dict[str, Any]:
        """Analyze performance requirements and optimization hints"""
        
        performance = {
            "bundler": None,
            "optimization_present": False,
            "static_assets": False,
            "lazy_loading": False,
            "caching_hints": [],
            "performance_budget": None
        }
        
        # Check for bundlers and optimization configs
        bundler_configs = {
            'webpack.config.js': 'webpack',
            'vite.config.js': 'vite',
            'rollup.config.js': 'rollup',
            'parcel.json': 'parcel'
        }
        
        for config_file, bundler in bundler_configs.items():
            if os.path.exists(os.path.join(repo_path, config_file)):
                performance["bundler"] = bundler
                performance["optimization_present"] = True
                break
        
        # Check for static assets
        asset_dirs = ['public', 'static', 'assets', 'images']
        for asset_dir in asset_dirs:
            if os.path.exists(os.path.join(repo_path, asset_dir)):
                performance["static_assets"] = True
                break
        
        # Check for performance optimization patterns in code
        js_files = []
        for root, dirs, files in os.walk(repo_path):
            if 'node_modules' not in root:
                js_files.extend([os.path.join(root, f) for f in files if f.endswith(('.js', '.jsx', '.ts', '.tsx'))])
        
        # Sample a few files to check for performance patterns
        for js_file in js_files[:5]:  # Check first 5 JS files
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if 'lazy' in content.lower() or 'dynamic import' in content.lower():
                    performance["lazy_loading"] = True
                
                if 'cache' in content.lower():
                    performance["caching_hints"].append("code_level_caching")
                
            except Exception:
                continue
        
        return performance
    
    async def _analyze_security_requirements(self, repo_path: str) -> Dict[str, Any]:
        """Analyze security requirements and configurations"""
        
        security = {
            "https_required": True,  # Always require HTTPS
            "cors_config": False,
            "auth_present": False,
            "env_vars_used": False,
            "security_headers": [],
            "vulnerability_scanners": []
        }
        
        # Check for authentication libraries
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.loads(f.read())
                
                all_deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                
                # Check for auth libraries
                auth_libs = ['passport', 'jsonwebtoken', 'bcrypt', 'auth0', 'firebase-auth']
                if any(lib in all_deps for lib in auth_libs):
                    security["auth_present"] = True
                
                # Check for CORS libraries
                if 'cors' in all_deps:
                    security["cors_config"] = True
                
                # Check for security scanners
                security_tools = ['helmet', 'express-rate-limit', 'csurf']
                security["vulnerability_scanners"] = [tool for tool in security_tools if tool in all_deps]
            
            except Exception:
                pass
        
        # Check for environment variable usage
        env_files = ['.env.example', '.env.template', '.env.sample']
        if any(os.path.exists(os.path.join(repo_path, env_file)) for env_file in env_files):
            security["env_vars_used"] = True
        
        return security
    
    async def _analyze_scaling_requirements(self, repo_path: str) -> Dict[str, Any]:
        """Analyze scaling requirements and architecture patterns"""
        
        scaling = {
            "microservices": False,
            "database_required": False,
            "cache_recommended": False,
            "load_balancer_needed": False,
            "auto_scaling_candidate": False,
            "cdn_recommended": True  # Always recommend CDN
        }
        
        # Check for database usage
        db_patterns = ['mongoose', 'sequelize', 'prisma', 'typeorm', 'sqlalchemy', 'django.db']
        package_json_path = os.path.join(repo_path, 'package.json')
        
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.loads(f.read())
                
                all_deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                
                if any(db in all_deps for db in db_patterns):
                    scaling["database_required"] = True
                    scaling["auto_scaling_candidate"] = True
                
                # Check for caching libraries
                cache_libs = ['redis', 'memcached', 'node-cache']
                if any(cache in all_deps for cache in cache_libs):
                    scaling["cache_recommended"] = True
            
            except Exception:
                pass
        
        # Check for microservices patterns
        if os.path.exists(os.path.join(repo_path, 'docker-compose.yml')):
            try:
                with open(os.path.join(repo_path, 'docker-compose.yml'), 'r') as f:
                    compose_content = f.read()
                
                # If multiple services defined, likely microservices
                service_count = compose_content.count('services:') + compose_content.count('  ')
                if service_count > 3:  # Multiple services
                    scaling["microservices"] = True
                    scaling["load_balancer_needed"] = True
            
            except Exception:
                pass
        
        return scaling
    
    async def _extract_environment_variables(self, repo_path: str) -> List[str]:
        """Extract environment variable patterns from the repository"""
        
        env_vars = set()
        
        # Check .env.example files
        env_example_files = ['.env.example', '.env.template', '.env.sample']
        for env_file in env_example_files:
            env_path = os.path.join(repo_path, env_file)
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#'):
                                var_name = line.split('=')[0].strip()
                                env_vars.add(var_name)
                except Exception:
                    pass
        
        # Check for common environment variable patterns in code
        common_env_vars = [
            'PORT', 'NODE_ENV', 'DATABASE_URL', 'REDIS_URL', 'API_KEY',
            'SECRET_KEY', 'JWT_SECRET', 'MONGODB_URI', 'POSTGRES_URL'
        ]
        
        # Sample some source files to find env var usage
        source_files = []
        for root, dirs, files in os.walk(repo_path):
            if 'node_modules' not in root and '.git' not in root:
                source_files.extend([
                    os.path.join(root, f) for f in files 
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.rb'))
                ])
        
        for source_file in source_files[:10]:  # Check first 10 source files
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for process.env.VARIABLE patterns
                import re
                env_pattern = r'process\.env\.([A-Z_]+)'
                matches = re.findall(env_pattern, content)
                env_vars.update(matches)
                
                # Check for common environment variables
                for var in common_env_vars:
                    if var in content:
                        env_vars.add(var)
            
            except Exception:
                continue
        
        return list(env_vars)
    
    async def _detect_external_services(self, repo_path: str) -> List[str]:
        """Detect external services and APIs used by the application"""
        
        services = set()
        
        # Check package.json for service-related dependencies
        package_json_path = os.path.join(repo_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.loads(f.read())
                
                all_deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                
                # Map dependencies to services
                service_map = {
                    'stripe': 'Stripe (Payments)',
                    'aws-sdk': 'AWS Services',
                    'firebase': 'Firebase',
                    'sendgrid': 'SendGrid (Email)',
                    'twilio': 'Twilio (SMS)',
                    'cloudinary': 'Cloudinary (Images)',
                    'auth0': 'Auth0 (Authentication)',
                    'mongodb': 'MongoDB',
                    'mysql': 'MySQL',
                    'postgres': 'PostgreSQL',
                    'redis': 'Redis',
                    'elasticsearch': 'Elasticsearch'
                }
                
                for dep, service in service_map.items():
                    if any(dep in d for d in all_deps.keys()):
                        services.add(service)
            
            except Exception:
                pass
        
        # Check for API endpoints in code
        api_patterns = [
            'api.stripe.com', 'api.github.com', 'api.twitter.com',
            'maps.googleapis.com', 'api.sendgrid.com'
        ]
        
        source_files = []
        for root, dirs, files in os.walk(repo_path):
            if 'node_modules' not in root:
                source_files.extend([
                    os.path.join(root, f) for f in files 
                    if f.endswith(('.js', '.jsx', '.ts', '.tsx'))
                ])
        
        for source_file in source_files[:5]:  # Check first 5 files
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in api_patterns:
                    if pattern in content:
                        services.add(pattern.split('.')[1].title() + ' API')
            
            except Exception:
                continue
        
        return list(services)
    
    async def _assess_deployment_complexity(
        self, 
        repo_path: str, 
        base_analysis: Dict[str, Any]
    ) -> str:
        """Assess overall deployment complexity"""
        
        complexity_score = 0
        
        # Check project type complexity
        project_type = base_analysis.get('project_type', 'static')
        if project_type in ['node', 'python', 'java']:
            complexity_score += 3
        elif project_type in ['react', 'vue', 'angular']:
            complexity_score += 2
        else:
            complexity_score += 1
        
        # Check for database
        if os.path.exists(os.path.join(repo_path, 'package.json')):
            try:
                with open(os.path.join(repo_path, 'package.json'), 'r') as f:
                    package_data = json.loads(f.read())
                all_deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                
                db_libs = ['mongoose', 'sequelize', 'prisma', 'typeorm']
                if any(db in all_deps for db in db_libs):
                    complexity_score += 2
            except Exception:
                pass
        
        # Check for Docker
        if os.path.exists(os.path.join(repo_path, 'Dockerfile')):
            complexity_score += 1
        
        # Check for multiple services
        if os.path.exists(os.path.join(repo_path, 'docker-compose.yml')):
            complexity_score += 2
        
        # Determine complexity level
        if complexity_score <= 2:
            return "simple"
        elif complexity_score <= 5:
            return "moderate"
        else:
            return "complex"
    
    async def _detect_project_type(self, repo_path: str) -> str:
        """Detect the type of project"""
        package_json = os.path.join(repo_path, "package.json")
        requirements_txt = os.path.join(repo_path, "requirements.txt")
        pom_xml = os.path.join(repo_path, "pom.xml")
        
        if os.path.exists(package_json):
            return "node"
        elif os.path.exists(requirements_txt):
            return "python"
        elif os.path.exists(pom_xml):
            return "java"
        else:
            return "static"
    
    async def _detect_framework(self, repo_path: str) -> str:
        """Detect the framework used"""
        package_json = os.path.join(repo_path, "package.json")
        
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                    
                    if 'react' in dependencies:
                        return "React"
                    elif 'vue' in dependencies:
                        return "Vue.js"
                    elif 'angular' in dependencies or '@angular/core' in dependencies:
                        return "Angular"
                    elif 'express' in dependencies:
                        return "Express.js"
                    else:
                        return "Node.js"
            except:
                return "Node.js"
        
        return "Unknown"
    
    async def _detect_languages(self, repo_path: str) -> List[str]:
        """Detect programming languages used"""
        languages = []
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', '.venv']]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext == '.js':
                    languages.append('JavaScript')
                elif ext == '.ts':
                    languages.append('TypeScript')
                elif ext == '.py':
                    languages.append('Python')
                elif ext == '.java':
                    languages.append('Java')
                elif ext == '.css':
                    languages.append('CSS')
                elif ext == '.html':
                    languages.append('HTML')
        
        return list(set(languages))
    
    async def _extract_dependencies(self, repo_path: str) -> List[str]:
        """Extract project dependencies"""
        dependencies = []
        
        package_json = os.path.join(repo_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get('dependencies', {})
                    dependencies.extend(list(deps.keys()))
            except:
                pass
        
        return dependencies[:10]  # Return top 10 dependencies
    
    async def _detect_build_system(self, repo_path: str) -> str:
        """Detect build system"""
        if os.path.exists(os.path.join(repo_path, "package.json")):
            return "npm"
        elif os.path.exists(os.path.join(repo_path, "requirements.txt")):
            return "pip"
        elif os.path.exists(os.path.join(repo_path, "pom.xml")):
            return "maven"
        else:
            return "unknown"
    
    async def _get_deployment_hints(self, repo_path: str) -> Dict[str, Any]:
        """Get deployment hints"""
        hints = {
            "port": 3000,
            "build_command": "npm run build",
            "start_command": "npm start"
        }
        
        package_json = os.path.join(repo_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    package_data = json.load(f)
                    scripts = package_data.get('scripts', {})
                    
                    if 'build' in scripts:
                        hints["build_command"] = f"npm run build"
                    if 'start' in scripts:
                        hints["start_command"] = f"npm start"
                    elif 'dev' in scripts:
                        hints["start_command"] = f"npm run dev"
            except:
                pass
        
        return hints

# Global service instance
enhanced_analysis_service = EnhancedAnalysisService()
