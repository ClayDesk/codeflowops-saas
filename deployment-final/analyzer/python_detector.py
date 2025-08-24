"""
Enhanced Python Dependency Detector
Automatically detects Python dependencies from import statements and creates requirements.txt
"""
import os
import re
import ast
from pathlib import Path
from typing import Set, Dict, List

class PythonDependencyDetector:
    def __init__(self):
        # Map import names to pip package names
        self.import_to_package = {
            'flask_mysqldb': 'Flask-MySQLdb',
            'flask_fontawesome': 'Flask-FontAwesome',
            'flask_sqlalchemy': 'Flask-SQLAlchemy',
            'flask_wtf': 'Flask-WTF',
            'flask_login': 'Flask-Login',
            'flask_mail': 'Flask-Mail',
            'flask_migrate': 'Flask-Migrate',
            'flask_cors': 'Flask-CORS',
            'psycopg2': 'psycopg2-binary',
            'mysqlclient': 'mysqlclient',
            'pymongo': 'pymongo',
            'redis': 'redis',
            'celery': 'celery',
            'requests': 'requests',
            'numpy': 'numpy',
            'pandas': 'pandas',
            'scipy': 'scipy',
            'sklearn': 'scikit-learn',
            'cv2': 'opencv-python',
            'PIL': 'Pillow',
            'jwt': 'PyJWT',
            'bcrypt': 'bcrypt',
            'werkzeug': 'Werkzeug',
            'jinja2': 'Jinja2',
            'click': 'Click',
            'itsdangerous': 'ItsDangerous',
            'blinker': 'blinker'
        }
        
        # Common Python standard library modules (don't need pip install)
        self.stdlib_modules = {
            'os', 'sys', 'json', 'time', 'datetime', 'random', 'math', 'collections',
            'itertools', 'functools', 'operator', 're', 'urllib', 'http', 'html',
            'xml', 'csv', 'sqlite3', 'threading', 'multiprocessing', 'subprocess',
            'pathlib', 'io', 'shutil', 'glob', 'pickle', 'base64', 'hashlib',
            'uuid', 'logging', 'unittest', 'argparse', 'configparser', 'tempfile'
        }

    def detect_dependencies(self, repo_path: str) -> Dict[str, List[str]]:
        """Detect all Python dependencies in the repository"""
        dependencies = set()
        database_type = None
        web_framework = None
        
        # Find all Python files
        python_files = self._find_python_files(repo_path)
        
        for file_path in python_files:
            file_deps, db_type, framework = self._analyze_python_file(file_path)
            dependencies.update(file_deps)
            if db_type:
                database_type = db_type
            if framework:
                web_framework = framework
        
        # Create requirements.txt
        requirements_path = os.path.join(repo_path, 'requirements.txt')
        self._create_requirements_txt(dependencies, requirements_path)
        
        return {
            'dependencies': list(dependencies),
            'database_type': database_type,
            'web_framework': web_framework,
            'requirements_file': requirements_path
        }

    def _find_python_files(self, repo_path: str) -> List[str]:
        """Find all Python files in the repository"""
        python_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 'node_modules'}]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files

    def _analyze_python_file(self, file_path: str) -> tuple:
        """Analyze a single Python file for dependencies"""
        dependencies = set()
        database_type = None
        web_framework = None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse imports using AST
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name.split('.')[0]
                            self._process_import(module_name, dependencies)
                            
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module.split('.')[0]
                            self._process_import(module_name, dependencies)
            except:
                # Fallback to regex parsing if AST fails
                self._parse_imports_regex(content, dependencies)
            
            # Detect database type
            if 'flask_mysqldb' in content.lower() or 'mysqldb' in content.lower():
                database_type = 'mysql'
            elif 'psycopg2' in content.lower() or 'postgresql' in content.lower():
                database_type = 'postgresql'
            elif 'sqlite' in content.lower():
                database_type = 'sqlite'
            elif 'mongodb' in content.lower() or 'pymongo' in content.lower():
                database_type = 'mongodb'
            
            # Detect web framework
            if 'flask' in content.lower():
                web_framework = 'flask'
            elif 'django' in content.lower():
                web_framework = 'django'
            elif 'fastapi' in content.lower():
                web_framework = 'fastapi'
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return dependencies, database_type, web_framework

    def _process_import(self, module_name: str, dependencies: set):
        """Process a single import and add to dependencies if needed"""
        if module_name in self.stdlib_modules:
            return
        
        # Map to pip package name
        package_name = self.import_to_package.get(module_name, module_name)
        dependencies.add(package_name)

    def _parse_imports_regex(self, content: str, dependencies: set):
        """Fallback regex-based import parsing"""
        import_patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    self._process_import(module_name, dependencies)

    def _create_requirements_txt(self, dependencies: set, requirements_path: str):
        """Create requirements.txt file with detected dependencies"""
        # Always include Flask and gunicorn for web apps
        base_requirements = {'flask', 'gunicorn'}
        all_deps = base_requirements.union(dependencies)
        
        # Sort dependencies
        sorted_deps = sorted(all_deps)
        
        with open(requirements_path, 'w') as f:
            for dep in sorted_deps:
                f.write(f"{dep}\n")
        
        print(f"✅ Created requirements.txt with {len(sorted_deps)} dependencies: {requirements_path}")
