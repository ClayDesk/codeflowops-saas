"""
Enhanced Repository Analyzer - Git Clone + Local Scan Approach
Deep analysis of repository structure using local git clone for robust analysis
"""

import os
import json
import re
import logging
import subprocess
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Information about a file in the repository"""
    name: str
    path: str
    type: str  # 'file' or 'dir'
    size: Optional[int] = None
    extension: Optional[str] = None
    is_config: bool = False
    is_source: bool = False
    is_test: bool = False
    content: Optional[str] = None  # Store actual file content for analysis

@dataclass
class ProjectTypeResult:
    """Result of project type detection"""
    type: str
    confidence: float
    evidence: List[str]
    subtype: Optional[str] = None
    build_command: Optional[str] = None
    output_directory: Optional[str] = None
    development_server: Optional[str] = None

@dataclass
class DependencyInfo:
    """Information about project dependencies"""
    manager: str  # 'npm', 'pip', 'composer', etc.
    dependencies: Dict[str, str]
    dev_dependencies: Dict[str, str] = None
    scripts: Dict[str, str] = None

@dataclass
class AnalysisResult:
    """Complete analysis result"""
    repository_url: str
    session_id: str
    total_files: int
    total_directories: int
    file_tree: List[FileInfo]
    project_types: List[ProjectTypeResult]
    primary_project_type: Optional[ProjectTypeResult]
    dependencies: Dict[str, Any]
    missing_files: List[str]
    config_files: List[str]
    build_tools: List[str]
    frameworks: List[str]
    languages: Dict[str, int]  # language -> file count
    analysis_timestamp: str
    confidence_score: float

class RepositoryAnalyzer:
    """
    Enhanced Repository Analyzer with Git Clone + Local Scan approach
    """
    
    def __init__(self):
        self.supported_languages = {
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript', 
            '.tsx': 'TypeScript',
            '.py': 'Python',
            '.php': 'PHP',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'SASS',
            '.html': 'HTML',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.c': 'C',
            '.cpp': 'C++',
            '.cs': 'C#',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        self.config_files = {
            'package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
            'requirements.txt', 'Pipfile', 'poetry.lock', 'pyproject.toml',
            'composer.json', 'composer.lock',
            'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
            '.gitignore', '.gitattributes',
            'webpack.config.js', 'vite.config.js', 'rollup.config.js',
            'tsconfig.json', 'jsconfig.json',
            'next.config.js', 'nuxt.config.js', 'vue.config.js',
            'angular.json', '.angular-cli.json',
            'gatsby-config.js', 'gatsby-node.js',
            'svelte.config.js',
            'tailwind.config.js', 'postcss.config.js',
            '.eslintrc', '.eslintrc.js', '.eslintrc.json',
            '.prettierrc', 'prettier.config.js',
            'babel.config.js', '.babelrc',
            'jest.config.js', 'vitest.config.js',
            'Makefile', 'CMakeLists.txt',
            'go.mod', 'go.sum',
            'Cargo.toml', 'Cargo.lock',
            'Gemfile', 'Gemfile.lock'
        }
        
        # Temporary directory management
        self.temp_dirs = []

    async def analyze_repository(self, repo_url: str, session_id: str) -> AnalysisResult:
        """
        Perform comprehensive repository analysis using git clone + local scan
        """
        logger.info(f"🚀 Starting git clone + local scan analysis for repository: {repo_url}")
        
        temp_dir = None
        try:
            # Clone the repository locally
            temp_dir = await self._clone_repository(repo_url)
            
            # Scan the local repository
            file_tree = await self._scan_local_repository(temp_dir)
            
            # Analyze file structure
            analysis = self._analyze_file_structure(file_tree)
            
            # Detect project types
            project_types = self._detect_project_types(file_tree, analysis)
            
            # Analyze dependencies locally
            dependencies = await self._analyze_dependencies_locally(temp_dir, file_tree)
            
            # Detect missing files
            missing_files = self._detect_missing_files(file_tree, project_types[0] if project_types else None)
            
            # Calculate overall confidence
            confidence_score = self._calculate_confidence_score(project_types, dependencies, file_tree)
            
            result = AnalysisResult(
                repository_url=repo_url,
                session_id=session_id,
                total_files=analysis['total_files'],
                total_directories=analysis['total_directories'],
                file_tree=file_tree,
                project_types=project_types,
                primary_project_type=project_types[0] if project_types else None,
                dependencies=dependencies,
                missing_files=missing_files,
                config_files=analysis['config_files'],
                build_tools=analysis['build_tools'],
                frameworks=analysis['frameworks'],
                languages=analysis['languages'],
                analysis_timestamp=self._get_timestamp(),
                confidence_score=confidence_score
            )
            
            logger.info(f"✅ Local analysis completed for {repo_url} with confidence: {confidence_score}%")
            logger.info(f"📊 Found {result.total_files} files, {len(result.languages)} languages, {len(result.project_types)} project types")
            return result
            
        except Exception as e:
            logger.error(f"❌ Local analysis failed for {repo_url}: {str(e)}")
            raise
        finally:
            # Cleanup temporary directory
            if temp_dir:
                await self._cleanup_temp_dir(temp_dir)

    async def _clone_repository(self, repo_url: str) -> str:
        """
        Clone repository to temporary directory using shallow clone
        """
        logger.info(f"📥 Cloning repository: {repo_url}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"repo_analysis_{uuid.uuid4().hex[:8]}_")
        self.temp_dirs.append(temp_dir)
        
        try:
            # Use shallow clone for efficiency (only latest commit)
            clone_cmd = [
                'git', 'clone', 
                '--depth=1',  # Shallow clone
                '--single-branch',  # Only main branch
                '--no-tags',  # Skip tags
                repo_url,
                temp_dir
            ]
            
            logger.info(f"🔧 Running: {' '.join(clone_cmd)}")
            
            result = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            logger.info(f"✅ Successfully cloned repository to: {temp_dir}")
            return temp_dir
            
        except subprocess.TimeoutExpired:
            raise Exception("Git clone timed out after 5 minutes")
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository: {str(e)}")

    async def _scan_local_repository(self, repo_path: str) -> List[FileInfo]:
        """
        Scan the local repository and build file tree with content analysis
        """
        logger.info(f"🔍 Scanning local repository: {repo_path}")
        
        file_tree = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            # Skip node_modules and other large directories
            skip_dirs = {'node_modules', '.next', 'dist', 'build', '__pycache__', '.venv', 'venv', 'vendor'}
            for skip_dir in skip_dirs:
                if skip_dir in dirs:
                    dirs.remove(skip_dir)
            
            # Get relative path from repo root
            rel_root = os.path.relpath(root, repo_path)
            if rel_root == '.':
                rel_root = ''
            
            # Add directories
            for dir_name in dirs:
                dir_path = os.path.join(rel_root, dir_name) if rel_root else dir_name
                file_tree.append(FileInfo(
                    name=dir_name,
                    path=dir_path.replace('\\', '/'),  # Normalize path separators
                    type='dir'
                ))
            
            # Add files
            for file_name in files:
                file_path = os.path.join(rel_root, file_name) if rel_root else file_name
                file_path = file_path.replace('\\', '/')  # Normalize path separators
                full_file_path = os.path.join(root, file_name)
                
                try:
                    file_size = os.path.getsize(full_file_path)
                    file_ext = Path(file_name).suffix.lower()
                    
                    # Read file content for important files
                    content = None
                    if self._should_read_file_content(file_name, file_size):
                        content = self._read_file_content(full_file_path)
                    
                    file_info = FileInfo(
                        name=file_name,
                        path=file_path,
                        type='file',
                        size=file_size,
                        extension=file_ext,
                        is_config=file_name in self.config_files,
                        is_source=file_ext in self.supported_languages,
                        is_test=self._is_test_file(file_name, file_path),
                        content=content
                    )
                    
                    file_tree.append(file_info)
                    
                except (OSError, IOError) as e:
                    logger.warning(f"Could not read file {full_file_path}: {e}")
                    continue
        
        logger.info(f"📂 Scanned {len(file_tree)} items from local repository")
        return file_tree

    def _should_read_file_content(self, file_name: str, file_size: int) -> bool:
        """
        Determine if we should read the full content of a file
        """
        # Always read config files
        if file_name in self.config_files:
            return True
        
        # Read small text files
        if file_size < 10000:  # 10KB limit
            ext = Path(file_name).suffix.lower()
            text_extensions = {'.txt', '.md', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'}
            if ext in text_extensions:
                return True
        
        # Read important files
        important_files = {'README.md', 'README.txt', 'LICENSE', 'CHANGELOG.md'}
        if file_name in important_files:
            return True
        
        return False

    def _read_file_content(self, file_path: str) -> Optional[str]:
        """
        Safely read file content
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read content of {file_path}: {e}")
            return None

    def _is_test_file(self, file_name: str, file_path: str) -> bool:
        """
        Determine if a file is a test file
        """
        test_indicators = [
            'test', 'spec', '__test__', '__tests__',
            '.test.', '.spec.', '_test.', '_spec.'
        ]
        
        lower_name = file_name.lower()
        lower_path = file_path.lower()
        
        return any(indicator in lower_name or indicator in lower_path 
                  for indicator in test_indicators)

    async def _analyze_dependencies_locally(self, repo_path: str, file_tree: List[FileInfo]) -> Dict[str, Any]:
        """
        Analyze dependencies from local files
        """
        logger.info("📦 Analyzing dependencies from local files")
        
        dependencies = {
            'npm': {},
            'pip': {},
            'composer': {},
            'go': {},
            'cargo': {},
            'package_managers': [],
            'total_dependencies': 0,
            'security_warnings': []
        }
        
        # Analyze package.json (npm/yarn)
        package_json_file = next((f for f in file_tree if f.name == 'package.json' and f.content), None)
        if package_json_file:
            try:
                package_data = json.loads(package_json_file.content)
                npm_deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})
                npm_deps.update(dev_deps)
                dependencies['npm'] = npm_deps
                dependencies['package_managers'].append('npm')
                dependencies['total_dependencies'] += len(npm_deps)
                logger.info(f"📦 Found {len(npm_deps)} npm dependencies")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse package.json: {e}")
        
        # Analyze requirements.txt (pip)
        requirements_file = next((f for f in file_tree if f.name == 'requirements.txt' and f.content), None)
        if requirements_file:
            pip_deps = {}
            for line in requirements_file.content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse requirement line (package==version, package>=version, etc.)
                    match = re.match(r'^([a-zA-Z0-9_-]+)([><=!~]+)?(.*)?', line)
                    if match:
                        package = match.group(1)
                        version = match.group(3) if match.group(3) else 'latest'
                        pip_deps[package] = version
            
            dependencies['pip'] = pip_deps
            dependencies['package_managers'].append('pip')
            dependencies['total_dependencies'] += len(pip_deps)
            logger.info(f"🐍 Found {len(pip_deps)} pip dependencies")
        
        # Analyze composer.json (PHP)
        composer_file = next((f for f in file_tree if f.name == 'composer.json' and f.content), None)
        if composer_file:
            try:
                composer_data = json.loads(composer_file.content)
                php_deps = composer_data.get('require', {})
                php_dev_deps = composer_data.get('require-dev', {})
                php_deps.update(php_dev_deps)
                dependencies['composer'] = php_deps
                dependencies['package_managers'].append('composer')
                dependencies['total_dependencies'] += len(php_deps)
                logger.info(f"🐘 Found {len(php_deps)} composer dependencies")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse composer.json: {e}")
        
        return dependencies

    def _analyze_file_structure(self, file_tree: List[FileInfo]) -> Dict[str, Any]:
        """
        Analyze the overall file structure
        """
        analysis = {
            'total_files': len([f for f in file_tree if f.type == 'file']),
            'total_directories': len([f for f in file_tree if f.type == 'dir']),
            'config_files': [f.name for f in file_tree if f.is_config],
            'build_tools': [],
            'frameworks': [],
            'languages': {}
        }
        
        # Count languages
        for file in file_tree:
            if file.extension and file.extension in self.supported_languages:
                lang = self.supported_languages[file.extension]
                analysis['languages'][lang] = analysis['languages'].get(lang, 0) + 1
        
        # Detect build tools
        build_tool_indicators = {
            'webpack': ['webpack.config.js', 'webpack.config.ts'],
            'vite': ['vite.config.js', 'vite.config.ts'],
            'rollup': ['rollup.config.js'],
            'parcel': ['.parcelrc'],
            'grunt': ['Gruntfile.js'],
            'gulp': ['gulpfile.js'],
            'make': ['Makefile'],
            'cmake': ['CMakeLists.txt']
        }
        
        config_file_names = [f.name for f in file_tree if f.is_config]
        for tool, indicators in build_tool_indicators.items():
            if any(indicator in config_file_names for indicator in indicators):
                analysis['build_tools'].append(tool)
        
        return analysis

    def _detect_project_types(self, file_tree: List[FileInfo], analysis: Dict) -> List[ProjectTypeResult]:
        """
        Detect project types with confidence scoring
        """
        project_types = []
        
        # Get all file names for pattern matching
        file_names = [f.name for f in file_tree if f.type == 'file']
        file_paths = [f.path for f in file_tree if f.type == 'file']
        
        # React Detection
        react_result = self._detect_react_project(file_names, file_paths, analysis)
        if react_result:
            project_types.append(react_result)
        
        # Vue.js Detection
        vue_result = self._detect_vue_project(file_names, file_paths, analysis)
        if vue_result:
            project_types.append(vue_result)
        
        # Static Site Detection
        static_result = self._detect_static_site(file_names, file_paths, analysis)
        if static_result:
            project_types.append(static_result)
        
        # Python Detection
        python_result = self._detect_python_project(file_names, file_paths, analysis)
        if python_result:
            project_types.append(python_result)
        
        # Sort by confidence score
        project_types.sort(key=lambda x: x.confidence, reverse=True)
        
        return project_types

    def _detect_react_project(self, file_names: List[str], file_paths: List[str], analysis: Dict) -> Optional[ProjectTypeResult]:
        """Detect React projects"""
        evidence = []
        confidence = 0.0
        
        # Check for package.json with React dependencies
        if 'package.json' in file_names:
            evidence.append('package.json found')
            confidence += 20
        
        # Check for React-specific files
        react_indicators = [
            'src/App.js', 'src/App.jsx', 'src/App.ts', 'src/App.tsx',
            'src/index.js', 'src/index.jsx', 'src/index.ts', 'src/index.tsx',
            'public/index.html'
        ]
        
        found_indicators = [indicator for indicator in react_indicators if indicator in file_paths]
        if found_indicators:
            evidence.extend(found_indicators)
            confidence += len(found_indicators) * 15
        
        # Check for JSX/TSX files
        jsx_files = [path for path in file_paths if path.endswith(('.jsx', '.tsx'))]
        if jsx_files:
            evidence.append(f'{len(jsx_files)} JSX/TSX files found')
            confidence += min(len(jsx_files) * 5, 25)
        
        if confidence >= 30:
            return ProjectTypeResult(
                type='React',
                confidence=min(confidence, 100),
                evidence=evidence,
                subtype='react-app',
                build_command='npm run build',
                output_directory='build',
                development_server='npm start'
            )
        
        return None

    def _detect_vue_project(self, file_names: List[str], file_paths: List[str], analysis: Dict) -> Optional[ProjectTypeResult]:
        """Detect Vue.js projects"""
        evidence = []
        confidence = 0.0
        
        if 'vue.config.js' in file_names:
            evidence.append('Vue config found')
            confidence += 40
        
        vue_files = [path for path in file_paths if path.endswith('.vue')]
        if vue_files:
            evidence.append(f'{len(vue_files)} Vue component files found')
            confidence += min(len(vue_files) * 8, 40)
        
        if confidence >= 30:
            return ProjectTypeResult(
                type='Vue.js',
                confidence=min(confidence, 100),
                evidence=evidence
            )
        
        return None

    def _detect_static_site(self, file_names: List[str], file_paths: List[str], analysis: Dict) -> Optional[ProjectTypeResult]:
        """Detect static HTML sites"""
        evidence = []
        confidence = 0.0
        
        html_files = [path for path in file_paths if path.endswith('.html')]
        if html_files:
            evidence.append(f'{len(html_files)} HTML files found')
            confidence += min(len(html_files) * 10, 40)
        
        if 'index.html' in file_names:
            evidence.append('Root index.html found')
            confidence += 30
        
        # Add more confidence for CSS and JS files
        css_files = [path for path in file_paths if path.endswith(('.css', '.scss', '.sass'))]
        js_files = [path for path in file_paths if path.endswith('.js') and not any(path.endswith(config) for config in ['config.js', 'webpack.config.js'])]
        
        if css_files:
            evidence.append(f'{len(css_files)} CSS files found')
            confidence += min(len(css_files) * 5, 15)
        
        if js_files:
            evidence.append(f'{len(js_files)} JavaScript files found')
            confidence += min(len(js_files) * 5, 15)
        
        if confidence >= 25:
            return ProjectTypeResult(
                type='Static Site',
                confidence=min(confidence, 100),
                evidence=evidence,
                subtype='html-css-js',
                build_command='none',
                output_directory='.',
                development_server='Live Server or static file server'
            )
        
        return None

    def _detect_python_project(self, file_names: List[str], file_paths: List[str], analysis: Dict) -> Optional[ProjectTypeResult]:
        """Detect Python projects"""
        evidence = []
        confidence = 0.0
        
        python_indicators = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']
        found_indicators = [ind for ind in python_indicators if ind in file_names]
        if found_indicators:
            evidence.extend(found_indicators)
            confidence += len(found_indicators) * 20
        
        python_count = analysis['languages'].get('Python', 0)
        if python_count > 0:
            evidence.append(f'{python_count} Python files found')
            confidence += min(python_count * 5, 30)
        
        if confidence >= 30:
            return ProjectTypeResult(
                type='Python',
                confidence=min(confidence, 100),
                evidence=evidence
            )
        
        return None

    def _detect_missing_files(self, file_tree: List[FileInfo], primary_type: Optional[ProjectTypeResult]) -> List[str]:
        """Detect missing critical files based on project type"""
        missing_files = []
        file_names = [f.name for f in file_tree if f.type == 'file']
        
        if not primary_type:
            return missing_files
        
        # Basic missing files for any project
        if 'README.md' not in file_names and 'README.txt' not in file_names:
            missing_files.append('README.md - Project documentation')
        
        if primary_type.type == 'React':
            if 'package.json' not in file_names:
                missing_files.append('package.json - Package configuration')
        
        return missing_files

    def _calculate_confidence_score(self, project_types: List[ProjectTypeResult], dependencies: Dict[str, Any], file_tree: List[FileInfo]) -> float:
        """Calculate overall analysis confidence"""
        if not project_types:
            return 25.0
        
        base_confidence = project_types[0].confidence
        
        # Boost confidence if we have dependency information
        if dependencies and dependencies.get('total_dependencies', 0) > 0:
            base_confidence += 10
        
        # Boost confidence based on repository completeness
        config_files = [f for f in file_tree if f.is_config]
        if len(config_files) >= 3:
            base_confidence += 5
        
        source_files = [f for f in file_tree if f.is_source]
        if len(source_files) >= 5:
            base_confidence += 5
        
        return min(base_confidence, 100.0)

    async def _cleanup_temp_dir(self, temp_dir: str):
        """Clean up temporary directory"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"🧹 Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")
        
        if temp_dir in self.temp_dirs:
            self.temp_dirs.remove(temp_dir)

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.utcnow().isoformat()

    def __del__(self):
        """Cleanup any remaining temp directories on destruction"""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_analyzer():
        analyzer = RepositoryAnalyzer()
        result = await analyzer.analyze_repository(
            "https://github.com/EniolaAdemola/HTML-CV", 
            "test-session-123"
        )
        print(json.dumps(asdict(result), indent=2, default=str))
    
    asyncio.run(test_analyzer())
