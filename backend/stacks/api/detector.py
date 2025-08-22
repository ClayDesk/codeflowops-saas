"""
API detector - identifies backend API projects for ECS/Lambda deployment
"""
import json
from pathlib import Path
from typing import Optional
from core.models import StackPlan
from core.utils import find_files, check_file_exists

class ApiDetector:
    """Detects backend API projects that should use ECS/Lambda instead of static hosting"""
    
    def detect(self, repo_dir: Path) -> Optional[StackPlan]:
        """
        Detect if repository contains a backend API project
        
        Looks for API indicators:
        - Node.js: package.json with express/fastify/nestjs/koa
        - Python: requirements.txt with flask/django/fastapi
        - PHP: composer.json with laravel/symfony/slim
        - Java: pom.xml with spring-boot/quarkus
        """
        
        # Node.js API Detection
        nodejs_result = self._detect_nodejs_api(repo_dir)
        if nodejs_result:
            return nodejs_result
        
        # Python API Detection  
        python_result = self._detect_python_api(repo_dir)
        if python_result:
            return python_result
            
        # PHP API Detection
        php_result = self._detect_php_api(repo_dir)
        if php_result:
            return php_result
            
        # Java API Detection
        java_result = self._detect_java_api(repo_dir)
        if java_result:
            return java_result
        
        return None
    
    def _detect_nodejs_api(self, repo_dir: Path) -> Optional[StackPlan]:
        """Detect Node.js API projects"""
        package_json_path = repo_dir / "package.json"
        
        if not package_json_path.exists():
            return None
            
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = {}
            dependencies.update(package_data.get('dependencies', {}))
            dependencies.update(package_data.get('devDependencies', {}))
            
            # API framework indicators
            api_frameworks = {
                'express': 'Express.js REST API',
                'fastify': 'Fastify API',
                '@nestjs/core': 'NestJS API',
                '@nestjs/common': 'NestJS API', 
                'koa': 'Koa API',
                'apollo-server': 'GraphQL API',
                'apollo-server-express': 'GraphQL API'
            }
            
            for framework, description in api_frameworks.items():
                if framework in dependencies:
                    return StackPlan(
                        stack_key="nodejs_api",
                        build_cmds=["npm install", "npm run build"],
                        output_dir=repo_dir,
                        config={
                            "runtime": "nodejs",
                            "framework": framework,
                            "description": description,
                            "type": "api",
                            "deployment_method": "ecs",  # Prefer ECS for APIs
                            "entry_point": self._detect_entry_point(repo_dir, "nodejs", framework)
                        }
                    )
            
            # Check for API-like scripts and patterns
            scripts = package_data.get('scripts', {})
            if any(script in scripts for script in ['start', 'dev', 'server']):
                # Look for common API patterns in main files
                main_file = package_data.get('main', 'index.js')
                entry_files = [main_file, 'server.js', 'app.js', 'index.js']
                
                # Check multiple potential entry files
                for entry_file in entry_files:
                    if self._has_api_patterns(repo_dir, entry_file):
                        return StackPlan(
                            stack_key="nodejs_api",
                            build_cmds=["npm install"],
                            output_dir=repo_dir,
                            config={
                                "runtime": "nodejs",
                                "framework": "node_api",
                                "description": "Node.js API",
                                "type": "api",
                                "deployment_method": "ecs",
                                "entry_point": self._detect_entry_point(repo_dir, "nodejs", "node_api")
                            }
                        )
                
                # Even if no specific API patterns, check for server-like scripts
                start_script = scripts.get('start', '')
                dev_script = scripts.get('dev', '')
                
                # Look for server patterns in scripts
                server_indicators = ['server.js', 'app.js', 'index.js', 'server', 'app']
                if any(indicator in start_script or indicator in dev_script for indicator in server_indicators):
                    return StackPlan(
                        stack_key="nodejs_api",
                        build_cmds=["npm install"],
                        output_dir=repo_dir,
                        config={
                            "runtime": "nodejs",
                            "framework": "vanilla_node",
                            "description": "Vanilla Node.js API",
                            "type": "api",
                            "deployment_method": "ecs",
                            "entry_point": self._detect_entry_point(repo_dir, "nodejs", "vanilla_node")
                        }
                    )
            
        except Exception as e:
            print(f"Error reading package.json: {e}")
        
        return None
    
    def _detect_python_api(self, repo_dir: Path) -> Optional[StackPlan]:
        """Detect Python API projects"""
        requirements_txt = repo_dir / "requirements.txt"
        
        if not requirements_txt.exists():
            return None
            
        try:
            with open(requirements_txt, 'r') as f:
                requirements = f.read().lower()
            
            # API framework indicators
            api_frameworks = {
                'flask': 'Flask REST API',
                'django': 'Django API',
                'fastapi': 'FastAPI',
                'tornado': 'Tornado API',
                'sanic': 'Sanic API',
                'aiohttp': 'aiohttp API'
            }
            
            for framework, description in api_frameworks.items():
                if framework in requirements:
                    return StackPlan(
                        stack_key="python_api",
                        build_cmds=["pip install -r requirements.txt"],
                        output_dir=repo_dir,
                        config={
                            "runtime": "python",
                            "framework": framework,
                            "description": description,
                            "type": "api",
                            "deployment_method": "ecs",
                            "entry_point": self._detect_entry_point(repo_dir, "python", framework)
                        }
                    )
                    
        except Exception as e:
            print(f"Error reading requirements.txt: {e}")
        
        return None
    
    def _detect_php_api(self, repo_dir: Path) -> Optional[StackPlan]:
        """Detect PHP API projects"""
        composer_json = repo_dir / "composer.json"
        
        if not composer_json.exists():
            # Check for PHP files with API patterns
            php_files = find_files(repo_dir, ["*.php"])
            if php_files and self._has_php_api_patterns(repo_dir):
                return StackPlan(
                    stack_key="php_api",
                    build_cmds=["composer install"],
                    output_dir=repo_dir,
                    config={
                        "runtime": "php",
                        "framework": "php_api",
                        "description": "PHP API",
                        "type": "api",
                        "deployment_method": "ecs",
                        "entry_point": self._detect_entry_point(repo_dir, "php")
                    }
                )
            return None
            
        try:
            with open(composer_json, 'r') as f:
                composer_data = json.load(f)
            
            dependencies = {}
            dependencies.update(composer_data.get('require', {}))
            dependencies.update(composer_data.get('require-dev', {}))
            
            # API framework indicators
            api_frameworks = {
                'laravel/framework': 'Laravel API',
                'symfony/symfony': 'Symfony API',
                'slim/slim': 'Slim API',
                'lumen/lumen': 'Lumen API'
            }
            
            for framework, description in api_frameworks.items():
                if framework in dependencies:
                    return StackPlan(
                        stack_key="php_api",
                        build_cmds=["composer install"],
                        output_dir=repo_dir,
                        config={
                            "runtime": "php",
                            "framework": framework.split('/')[0],
                            "description": description,
                            "type": "api",
                            "deployment_method": "ecs",
                            "entry_point": self._detect_entry_point(repo_dir, "php", framework.split('/')[0])
                        }
                    )
                    
        except Exception as e:
            print(f"Error reading composer.json: {e}")
        
        return None
    
    def _detect_java_api(self, repo_dir: Path) -> Optional[StackPlan]:
        """Detect Java API projects"""
        pom_xml = repo_dir / "pom.xml"
        
        if not pom_xml.exists():
            return None
            
        try:
            with open(pom_xml, 'r') as f:
                pom_content = f.read()
            
            # API framework indicators
            if 'spring-boot-starter' in pom_content:
                return StackPlan(
                    stack_key="java_api",
                    build_cmds=["mvn clean package"],
                    output_dir=repo_dir,
                    config={
                        "runtime": "java",
                        "framework": "spring-boot",
                        "description": "Spring Boot API",
                        "type": "api",
                        "deployment_method": "ecs",
                        "entry_point": self._detect_entry_point(repo_dir, "java", "spring-boot")
                    }
                )
            elif 'quarkus' in pom_content:
                return StackPlan(
                    stack_key="java_api",
                    build_cmds=["mvn clean package"],
                    output_dir=repo_dir,
                    config={
                        "runtime": "java",
                        "framework": "quarkus",
                        "description": "Quarkus API",
                        "type": "api",
                        "deployment_method": "ecs",
                        "entry_point": self._detect_entry_point(repo_dir, "java", "quarkus")
                    }
                )
                
        except Exception as e:
            print(f"Error reading pom.xml: {e}")
        
        return None
    
    def _has_api_patterns(self, repo_dir: Path, main_file: str) -> bool:
        """Check if main file contains API patterns"""
        try:
            main_path = repo_dir / main_file
            if not main_path.exists():
                return False
                
            with open(main_path, 'r') as f:
                content = f.read()
            
            # Look for common API patterns - enhanced for vanilla Node.js
            api_patterns = [
                # Express patterns
                'app.listen(',
                'server.listen(',
                '.get(',
                '.post(',
                '.put(',
                '.delete(',
                'express(',
                'fastify(',
                'app.use(',
                'router.',
                'middleware',
                'cors',
                # Vanilla Node.js patterns
                'http.createServer(',
                'require(\'http\')',
                'require("http")',
                '.createServer(',
                'res.writeHead(',
                'res.end(',
                'req.method',
                'req.url',
                'JSON.stringify(',
                'JSON.parse(',
                # General server patterns
                'listen(',
                'port',
                'PORT',
                'server',
                'api',
                'endpoint'
            ]
            
            return any(pattern in content for pattern in api_patterns)
            
        except Exception:
            return False
    
    def _has_php_api_patterns(self, repo_dir: Path) -> bool:
        """Check if PHP files contain API patterns"""
        try:
            php_files = find_files(repo_dir, ["*.php"])
            
            for php_file in php_files[:5]:  # Check first 5 PHP files
                with open(php_file, 'r') as f:
                    content = f.read()
                
                # Look for API patterns
                api_patterns = [
                    'Route::',
                    '$app->',
                    'header(',
                    'json_encode(',
                    '$_GET',
                    '$_POST',
                    'API',
                    'api',
                    'rest'
                ]
                
                if any(pattern in content for pattern in api_patterns):
                    return True
                    
        except Exception:
            pass
        
        return False
    
    def get_priority(self) -> int:
        """API detection should have higher priority than static sites"""
        return 50  # Higher than static sites (10) but lower than specific frameworks like NextJS (80)
    
    def _detect_entry_point(self, repo_dir: Path, runtime: str, framework: str = "") -> str:
        """Detect API entry point based on runtime and framework"""
        if runtime == "nodejs":
            # Check for common Node.js entry points
            if check_file_exists(repo_dir, "app.js"):
                return "app.js"
            elif check_file_exists(repo_dir, "server.js"):
                return "server.js"
            elif check_file_exists(repo_dir, "index.js"):
                return "index.js"
            elif check_file_exists(repo_dir, "main.js"):
                return "main.js"
            elif check_file_exists(repo_dir, "src/app.js"):
                return "src/app.js"
            elif check_file_exists(repo_dir, "src/index.js"):
                return "src/index.js"
            return "index.js"  # Default
            
        elif runtime == "python":
            # Check for common Python entry points
            if check_file_exists(repo_dir, "app.py"):
                return "app.py"
            elif check_file_exists(repo_dir, "main.py"):
                return "main.py"
            elif check_file_exists(repo_dir, "server.py"):
                return "server.py"
            elif check_file_exists(repo_dir, "wsgi.py"):
                return "wsgi.py"
            elif check_file_exists(repo_dir, "asgi.py"):
                return "asgi.py"
            elif framework.lower() == "django" and check_file_exists(repo_dir, "manage.py"):
                return "manage.py"
            return "app.py"  # Default
            
        elif runtime == "php":
            # Check for common PHP entry points
            if check_file_exists(repo_dir, "public/index.php"):
                return "public/index.php"
            elif check_file_exists(repo_dir, "index.php"):
                return "index.php"
            elif check_file_exists(repo_dir, "api/index.php"):
                return "api/index.php"
            return "index.php"  # Default
            
        elif runtime == "java":
            # Check for common Java entry points
            if check_file_exists(repo_dir, "src/main/java/Application.java"):
                return "src/main/java/Application.java"
            elif check_file_exists(repo_dir, "src/main/java/Main.java"):
                return "src/main/java/Main.java"
            return "src/main/java/Application.java"  # Default
            
        return "index.js"  # Fallback
