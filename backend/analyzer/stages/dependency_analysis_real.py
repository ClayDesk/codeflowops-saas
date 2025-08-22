"""
Real Dependency Analysis Stage
Simple dependency extraction from common package manager files
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RealDependencyAnalysisStage:
    """
    Real dependency analysis stage that extracts dependencies from package files
    """
    
    def __init__(self):
        self.package_files = {
            "npm": ["package.json"],
            "pip": ["requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py", "*.py"],
            "composer": ["composer.json"],
            "maven": ["pom.xml"],
            "gradle": ["build.gradle", "build.gradle.kts"],
            "cargo": ["Cargo.toml"],
            "go": ["go.mod"],
            "nuget": ["packages.config", "*.csproj"]
        }
    
    async def analyze(self, context) -> Dict[str, Any]:
        """
        Analyze dependencies in the repository
        """
        try:
            logger.info("🔍 Starting dependency analysis")
            
            repo_path = context.repo_path
            if not repo_path or not os.path.exists(repo_path):
                logger.warning("No valid repo path for dependency analysis")
                return {"dependencies": []}

            dependencies = []
            package_managers = []
            
            # Check for each package manager
            for manager, files in self.package_files.items():
                found_files = self._find_package_files(str(repo_path), files)
                if found_files:
                    package_managers.append(manager)
                    deps = await self._extract_dependencies(manager, found_files, str(repo_path))
                    dependencies.extend(deps)
            
            # Deduplicate dependencies by name
            seen = set()
            unique_dependencies = []
            for dep in dependencies:
                dep_key = (dep.get('name', ''), dep.get('manager', ''))
                if dep_key not in seen:
                    seen.add(dep_key)
                    unique_dependencies.append(dep)

            logger.info(f"✅ Found {len(unique_dependencies)} unique dependencies across {len(package_managers)} package managers")
            
            # Store results in the intelligence profile
            context.intelligence_profile["dependencies"] = unique_dependencies
            context.intelligence_profile["package_managers"] = package_managers
            context.intelligence_profile["dependency_analysis"] = {
                "total_dependencies": len(unique_dependencies),
                "dependencies_by_manager": {mgr: len([d for d in unique_dependencies if d.get("manager") == mgr]) for mgr in package_managers},
                "package_managers": package_managers
            }
            
            return {
                "dependencies": unique_dependencies,
                "package_managers": package_managers,
                "total_dependencies": len(unique_dependencies),
                "dependencies_by_manager": {mgr: len([d for d in unique_dependencies if d.get("manager") == mgr]) for mgr in package_managers}
            }
            
        except Exception as e:
            logger.error(f"❌ Dependency analysis failed: {e}")
            # Still store empty results in case of failure
            context.intelligence_profile["dependencies"] = []
            context.intelligence_profile["package_managers"] = []
            return {"dependencies": []}
    
    def _find_package_files(self, repo_path: str, filenames: List[str]) -> List[str]:
        """Find package files in the repository"""
        found_files = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip node_modules, __pycache__, etc.
            dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'venv', 'env']]
            
            for file in files:
                # Check for exact filename matches
                if file in filenames:
                    found_files.append(os.path.join(root, file))
                # Check for pattern matches (like *.py)
                elif "*.py" in filenames and file.endswith('.py'):
                    found_files.append(os.path.join(root, file))
                elif "*.csproj" in filenames and file.endswith('.csproj'):
                    found_files.append(os.path.join(root, file))
        
        return found_files
    
    async def _extract_dependencies(self, manager: str, file_paths: List[str], repo_path: str) -> List[Dict[str, Any]]:
        """Extract dependencies from package files and source code analysis"""
        dependencies = []
        
        # For Python, we need comprehensive dependency detection for file generation
        if manager == "pip":
            requirement_files = [f for f in file_paths if f.endswith(('.txt', '.toml', 'setup.py'))]
            python_files = [f for f in file_paths if f.endswith('.py')]
            
            # Process formal requirements files first (these have priority)
            formal_deps = []
            for file_path in requirement_files:
                deps = self._parse_python_requirements(file_path)
                formal_deps.extend(deps)
            
            # ALWAYS scan Python imports for comprehensive dependency detection
            # This ensures our generated requirements.txt will be complete
            import_deps = []
            if python_files:
                logger.info(f"Scanning Python imports in {len(python_files)} files for complete dependency detection")
                
                # Scan all Python files but prioritize main application files
                main_files = [f for f in python_files if any(name in os.path.basename(f).lower() 
                             for name in ['app.py', 'main.py', 'manage.py', 'run.py', 'server.py', '__init__.py'])]
                other_files = [f for f in python_files if f not in main_files]
                
                # Process main files first, then other files (limited to avoid noise)
                files_to_scan = main_files + other_files[:10]  # Scan up to 10 additional files
                
                for file_path in files_to_scan:
                    if os.path.getsize(file_path) < 512 * 1024:  # Skip files larger than 512KB
                        deps = self._parse_python_imports(file_path)
                        import_deps.extend(deps)
            
            # Combine formal and import dependencies (formal takes priority)
            all_deps = formal_deps + import_deps
            dependencies = self._deduplicate_dependencies_by_name(all_deps)
            
            if formal_deps:
                logger.info(f"Found {len(formal_deps)} formal deps + {len(import_deps)} import deps = {len(dependencies)} unique Python dependencies")
            else:
                logger.info(f"No formal requirements found, detected {len(dependencies)} dependencies from imports (will generate requirements.txt)")
                
        else:
            # For other package managers, process all files
            for file_path in file_paths:
                try:
                    if manager == "npm":
                        deps = self._parse_package_json(file_path)
                    elif manager == "composer":
                        deps = self._parse_composer_json(file_path)
                    else:
                        deps = []
                    
                    dependencies.extend(deps)
                except Exception as e:
                    logger.warning(f"Failed to parse {file_path}: {e}")
        
        return dependencies
    
    def _parse_package_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse package.json file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dependencies = []
            
            # Runtime dependencies
            for name, version in data.get("dependencies", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "runtime",
                    "manager": "npm"
                })
            
            # Dev dependencies
            for name, version in data.get("devDependencies", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "development",
                    "manager": "npm"
                })
            
            return dependencies
        
        except Exception as e:
            logger.warning(f"Failed to parse package.json {file_path}: {e}")
            return []
    
    def _deduplicate_dependencies_by_name(self, dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate dependencies by name, preferring formal package files over imports"""
        seen = {}
        
        for dep in dependencies:
            name = dep.get('name', '').lower()
            if name:
                # Prefer dependencies from formal files over imports
                existing = seen.get(name)
                if not existing:
                    seen[name] = dep
                elif 'requirements.txt' in dep.get('source', '') and 'imported in' in existing.get('source', ''):
                    # Replace import-detected with requirements.txt version
                    seen[name] = dep
                elif dep.get('version', '') != 'detected' and existing.get('version', '') == 'detected':
                    # Prefer version info over "detected"
                    seen[name] = dep
        
        return list(seen.values())

    def _parse_python_imports(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Python file for import statements to detect dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            dependencies = []
            
            # Comprehensive Python package mapping for dependency file generation
            python_packages = {
                # Web frameworks
                'flask': {'name': 'Flask', 'version': '>=2.0.0', 'type': 'runtime'},
                'django': {'name': 'Django', 'version': '>=3.2.0', 'type': 'runtime'},
                'fastapi': {'name': 'FastAPI', 'version': '>=0.65.0', 'type': 'runtime'},
                'starlette': {'name': 'starlette', 'version': '>=0.14.0', 'type': 'runtime'},
                'tornado': {'name': 'tornado', 'version': '>=6.0.0', 'type': 'runtime'},
                'pyramid': {'name': 'pyramid', 'version': '>=1.10.0', 'type': 'runtime'},
                
                # HTTP and networking
                'requests': {'name': 'requests', 'version': '>=2.25.0', 'type': 'runtime'},
                'urllib3': {'name': 'urllib3', 'version': '>=1.26.0', 'type': 'runtime'},
                'httpx': {'name': 'httpx', 'version': '>=0.20.0', 'type': 'runtime'},
                'aiohttp': {'name': 'aiohttp', 'version': '>=3.7.0', 'type': 'runtime'},
                
                # Database
                'sqlalchemy': {'name': 'SQLAlchemy', 'version': '>=1.4.0', 'type': 'runtime'},
                'psycopg2': {'name': 'psycopg2-binary', 'version': '>=2.8.0', 'type': 'runtime'},
                'pymongo': {'name': 'pymongo', 'version': '>=3.11.0', 'type': 'runtime'},
                'redis': {'name': 'redis', 'version': '>=3.5.0', 'type': 'runtime'},
                'mysql': {'name': 'mysql-connector-python', 'version': '>=8.0.0', 'type': 'runtime'},
                'sqlite3': {'name': 'sqlite3', 'version': 'built-in', 'type': 'runtime'},
                
                # Data science
                'numpy': {'name': 'numpy', 'version': '>=1.20.0', 'type': 'runtime'},
                'pandas': {'name': 'pandas', 'version': '>=1.3.0', 'type': 'runtime'},
                'scipy': {'name': 'scipy', 'version': '>=1.7.0', 'type': 'runtime'},
                'matplotlib': {'name': 'matplotlib', 'version': '>=3.4.0', 'type': 'runtime'},
                'seaborn': {'name': 'seaborn', 'version': '>=0.11.0', 'type': 'runtime'},
                'plotly': {'name': 'plotly', 'version': '>=5.0.0', 'type': 'runtime'},
                'sklearn': {'name': 'scikit-learn', 'version': '>=0.24.0', 'type': 'runtime'},
                
                # Utilities
                'click': {'name': 'click', 'version': '>=7.0.0', 'type': 'runtime'},
                'jinja2': {'name': 'Jinja2', 'version': '>=2.11.0', 'type': 'runtime'},
                'werkzeug': {'name': 'Werkzeug', 'version': '>=1.0.0', 'type': 'runtime'},
                'celery': {'name': 'celery', 'version': '>=5.0.0', 'type': 'runtime'},
                'pydantic': {'name': 'pydantic', 'version': '>=1.8.0', 'type': 'runtime'},
                'marshmallow': {'name': 'marshmallow', 'version': '>=3.12.0', 'type': 'runtime'},
                
                # Testing and development
                'pytest': {'name': 'pytest', 'version': '>=6.0.0', 'type': 'development'},
                'unittest': {'name': 'unittest', 'version': 'built-in', 'type': 'development'},
                'black': {'name': 'black', 'version': '>=21.0.0', 'type': 'development'},
                'flake8': {'name': 'flake8', 'version': '>=3.9.0', 'type': 'development'},
                'mypy': {'name': 'mypy', 'version': '>=0.910', 'type': 'development'},
                
                # Deployment
                'gunicorn': {'name': 'gunicorn', 'version': '>=20.1.0', 'type': 'runtime'},
                'uwsgi': {'name': 'uWSGI', 'version': '>=2.0.19', 'type': 'runtime'},
                'waitress': {'name': 'waitress', 'version': '>=2.0.0', 'type': 'runtime'},
            }
            
            # Find import statements with comprehensive patterns
            import re
            
            import_patterns = [
                r'^\s*import\s+(\w+)',              # import module
                r'^\s*from\s+(\w+)\s+import',       # from module import
                r'^\s*import\s+(\w+)\.',            # import module.submodule
                r'^\s*from\s+(\w+)\.',              # from module.submodule import
            ]
            
            found_imports = set()
            for pattern in import_patterns:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    module = match.group(1).lower()
                    if module in python_packages:
                        found_imports.add(module)
            
            # Convert to dependency format
            for module in found_imports:
                pkg_info = python_packages[module]
                dependencies.append({
                    "name": pkg_info['name'],
                    "version": pkg_info['version'],
                    "type": pkg_info['type'],
                    "manager": "pip",
                    "source": f"imported in {os.path.basename(file_path)}",
                    "confidence": "detected"  # Mark as detected for file generation
                })
            
            return dependencies
        
        except Exception as e:
            logger.warning(f"Failed to parse Python imports in {file_path}: {e}")
            return []

    def _parse_python_requirements(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Python requirements.txt file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            dependencies = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Parse package==version or package>=version etc.
                    if '==' in line:
                        name, version = line.split('==', 1)
                    elif '>=' in line:
                        name, version = line.split('>=', 1)
                    elif '<=' in line:
                        name, version = line.split('<=', 1)
                    elif '>' in line:
                        name, version = line.split('>', 1)
                    elif '<' in line:
                        name, version = line.split('<', 1)
                    else:
                        name, version = line, "latest"
                    
                    dependencies.append({
                        "name": name.strip(),
                        "version": version.strip(),
                        "type": "runtime",
                        "manager": "pip",
                        "source": os.path.basename(file_path)
                    })
            
            return dependencies
        
        except Exception as e:
            logger.warning(f"Failed to parse requirements file {file_path}: {e}")
            return []
    
    def _parse_composer_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse composer.json file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            dependencies = []
            
            # Runtime dependencies
            for name, version in data.get("require", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "runtime",
                    "manager": "composer"
                })
            
            # Dev dependencies
            for name, version in data.get("require-dev", {}).items():
                dependencies.append({
                    "name": name,
                    "version": version,
                    "type": "development",
                    "manager": "composer"
                })
            
            return dependencies
        
        except Exception as e:
            logger.warning(f"Failed to parse composer.json {file_path}: {e}")
            return []
