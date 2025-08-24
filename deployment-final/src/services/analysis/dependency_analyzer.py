"""
Dependency Analyzer
Advanced dependency analysis for multiple package managers and languages
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict

try:
    import semver
except ImportError:
    # Fallback if semver is not available
    class MockSemver:
        @staticmethod
        def VersionInfo(major=0, minor=0, patch=0):
            return {"major": major, "minor": minor, "patch": patch}
        
        @staticmethod
        def compare(v1, v2):
            return 0
    
    semver = MockSemver()

logger = logging.getLogger(__name__)

@dataclass
class Dependency:
    """Information about a single dependency"""
    name: str
    version: str
    type: str  # 'runtime', 'development', 'peer', 'optional'
    manager: str  # 'npm', 'pip', 'composer', etc.
    is_vulnerable: bool = False
    is_outdated: bool = False
    latest_version: Optional[str] = None
    security_advisory: Optional[str] = None

@dataclass
class DependencyAnalysis:
    """Complete dependency analysis result"""
    total_dependencies: int
    runtime_dependencies: int
    development_dependencies: int
    dependencies_by_manager: Dict[str, int]
    outdated_count: int
    vulnerable_count: int
    package_managers: List[str]
    dependencies: List[Dependency]
    scripts: Dict[str, str]
    engines: Dict[str, str]
    analysis_warnings: List[str]
    recommendations: List[str]

class DependencyAnalyzer:
    """
    Advanced dependency analyzer supporting multiple package managers
    """
    
    def __init__(self):
        self.supported_managers = {
            'npm': {
                'files': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'],
                'parser': self._parse_npm_dependencies
            },
            'pip': {
                'files': ['requirements.txt', 'pyproject.toml', 'Pipfile', 'setup.py'],
                'parser': self._parse_python_dependencies
            },
            'composer': {
                'files': ['composer.json', 'composer.lock'],
                'parser': self._parse_composer_dependencies
            },
            'go': {
                'files': ['go.mod', 'go.sum'],
                'parser': self._parse_go_dependencies
            },
            'cargo': {
                'files': ['Cargo.toml', 'Cargo.lock'],
                'parser': self._parse_cargo_dependencies
            },
            'maven': {
                'files': ['pom.xml'],
                'parser': self._parse_maven_dependencies
            },
            'gradle': {
                'files': ['build.gradle', 'build.gradle.kts'],
                'parser': self._parse_gradle_dependencies
            }
        }
        
        # Known vulnerability patterns (simplified - in production, use proper vulnerability databases)
        self.vulnerability_patterns = {
            'lodash': ['4.17.20', '4.17.19'],
            'axios': ['0.21.0'],
            'minimist': ['1.2.5']
        }
    
    def _get_filename_from_path(self, file_path: str) -> str:
        """Extract filename from path"""
        return file_path.split('/')[-1].split('\\')[-1]
    
    def _find_files_by_name(self, file_tree: List[Dict], filenames: List[str]) -> List[Dict]:
        """Find files in tree by filename"""
        return [f for f in file_tree if self._get_filename_from_path(f['path']) in filenames]
    
    def _find_file_by_name(self, file_tree: List[Dict], filename: str) -> Optional[Dict]:
        """Find single file in tree by filename"""
        return next((f for f in file_tree if self._get_filename_from_path(f['path']) == filename), None)

    async def analyze_dependencies(self, file_tree: List[Dict], file_contents: Dict[str, str]) -> DependencyAnalysis:
        """
        Analyze all dependencies in the repository
        """
        logger.info("Starting dependency analysis")
        
        all_dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        package_managers = []
        
        # Detect and analyze each package manager
        for manager, config in self.supported_managers.items():
            manager_files = self._find_files_by_name(file_tree, config['files'])
            
            if manager_files:
                package_managers.append(manager)
                logger.info(f"Found {manager} package manager")
                
                try:
                    deps, mgr_scripts, mgr_engines, mgr_warnings, mgr_recommendations = await config['parser'](
                        manager_files, file_contents, manager
                    )
                    all_dependencies.extend(deps)
                    scripts.update(mgr_scripts)
                    engines.update(mgr_engines)
                    warnings.extend(mgr_warnings)
                    recommendations.extend(mgr_recommendations)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze {manager} dependencies: {str(e)}")
                    warnings.append(f"Failed to analyze {manager} dependencies: {str(e)}")
        
        # Check for dependency conflicts
        conflict_warnings = self._check_dependency_conflicts(all_dependencies)
        warnings.extend(conflict_warnings)
        
        # Generate security recommendations
        security_recommendations = self._generate_security_recommendations(all_dependencies)
        recommendations.extend(security_recommendations)
        
        # Calculate statistics
        stats = self._calculate_dependency_stats(all_dependencies, package_managers)
        
        return DependencyAnalysis(
            total_dependencies=stats['total'],
            runtime_dependencies=stats['runtime'],
            development_dependencies=stats['development'],
            dependencies_by_manager=stats['by_manager'],
            outdated_count=stats['outdated'],
            vulnerable_count=stats['vulnerable'],
            package_managers=package_managers,
            dependencies=all_dependencies,
            scripts=scripts,
            engines=engines,
            analysis_warnings=warnings,
            recommendations=recommendations
        )

    async def _parse_npm_dependencies(self, files: List[Dict], file_contents: Dict[str, str], manager: str) -> Tuple[List[Dependency], Dict, Dict, List[str], List[str]]:
        """Parse NPM/Node.js dependencies"""
        dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        
        # Find package.json
        package_json_file = self._find_file_by_name(files, 'package.json')
        if not package_json_file:
            return dependencies, scripts, engines, warnings, recommendations
        
        # Get file path safely
        file_path = package_json_file.get('path', '')
        if not file_path:
            warnings.append("package.json found but path is missing")
            return dependencies, scripts, engines, warnings, recommendations
        
        try:
            package_content = file_contents.get(file_path, '{}')
            if not package_content.strip():
                warnings.append("package.json is empty")
                return dependencies, scripts, engines, warnings, recommendations
                
            package_data = json.loads(package_content)
        except json.JSONDecodeError as e:
            warnings.append(f"Invalid package.json format: {str(e)}")
            return dependencies, scripts, engines, warnings, recommendations
        except Exception as e:
            warnings.append(f"Error reading package.json: {str(e)}")
            return dependencies, scripts, engines, warnings, recommendations
        
        # Extract scripts and engines
        scripts = package_data.get('scripts', {})
        engines = package_data.get('engines', {})
        
        # Parse dependencies
        dep_sections = {
            'dependencies': 'runtime',
            'devDependencies': 'development',
            'peerDependencies': 'peer',
            'optionalDependencies': 'optional'
        }
        
        for section, dep_type in dep_sections.items():
            deps = package_data.get(section, {})
            for name, version in deps.items():
                dep = Dependency(
                    name=name,
                    version=version,
                    type=dep_type,
                    manager=manager
                )
                
                # Check for vulnerabilities
                dep.is_vulnerable = self._check_vulnerability(name, version)
                if dep.is_vulnerable:
                    dep.security_advisory = f"Known vulnerability in {name}@{version}"
                
                # Check if outdated (simplified check)
                dep.is_outdated = self._is_version_outdated(version)
                
                dependencies.append(dep)
        
        # Generate NPM-specific recommendations
        if not scripts.get('build'):
            recommendations.append("Consider adding a 'build' script for production builds")
        
        if not scripts.get('test'):
            recommendations.append("Consider adding a 'test' script for automated testing")
        
        if not engines:
            recommendations.append("Consider specifying Node.js version in 'engines' field")
        
        # Check for common issues
        if 'react' in package_data.get('dependencies', {}) and 'react-dom' not in package_data.get('dependencies', {}):
            warnings.append("React project missing react-dom dependency")
        
        # Check for TypeScript configuration
        if 'typescript' in package_data.get('devDependencies', {}):
            # Check if tsconfig.json exists in the file tree
            has_tsconfig = any(
                f.get('name', self._get_filename_from_path(f.get('path', ''))) == 'tsconfig.json' 
                for f in files if isinstance(f, dict)
            )
            if not has_tsconfig:
                warnings.append("TypeScript dependency found but no tsconfig.json")
        
        return dependencies, scripts, engines, warnings, recommendations

    async def _parse_python_dependencies(self, files: List[Dict], file_contents: Dict[str, str], manager: str) -> Tuple[List[Dependency], Dict, Dict, List[str], List[str]]:
        """Parse Python dependencies"""
        dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        
        # Parse requirements.txt
        requirements_file = self._find_file_by_name(files, 'requirements.txt')
        if requirements_file:
            file_path = requirements_file.get('path', '')
            if file_path:
                content = file_contents.get(file_path, '')
                if content.strip():
                    deps = self._parse_requirements_txt(content)
                    dependencies.extend([
                        Dependency(name=name, version=version, type='runtime', manager=manager)
                        for name, version in deps.items()
                    ])
        
        # Parse pyproject.toml
        pyproject_file = self._find_file_by_name(files, 'pyproject.toml')
        if pyproject_file:
            file_path = pyproject_file.get('path', '')
            if file_path:
                content = file_contents.get(file_path, '')
                if '[tool.poetry.dependencies]' in content:
                    recommendations.append("Poetry project detected - consider using Poetry for dependency management")
        
        # Parse Pipfile
        pipfile = self._find_file_by_name(files, 'Pipfile')
        if pipfile:
            file_path = pipfile.get('path', '')
            if file_path:
                content = file_contents.get(file_path, '')
                if '[packages]' in content:
                    recommendations.append("Pipenv project detected - consider generating requirements.txt for deployment")
        
        # Python-specific recommendations
        if not any(dep.name == 'pytest' for dep in dependencies):
            recommendations.append("Consider adding pytest for testing")
        
        if not requirements_file and not pyproject_file:
            warnings.append("No Python dependency file found - consider adding requirements.txt")
        
        return dependencies, scripts, engines, warnings, recommendations

    async def _parse_composer_dependencies(self, files: List[Dict], file_contents: Dict[str, str], manager: str) -> Tuple[List[Dependency], Dict, Dict, List[str], List[str]]:
        """Parse PHP Composer dependencies"""
        dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        
        composer_json = self._find_file_by_name(files, 'composer.json')
        if not composer_json:
            return dependencies, scripts, engines, warnings, recommendations
        
        file_path = composer_json.get('path', '')
        if not file_path:
            warnings.append("composer.json found but path is missing")
            return dependencies, scripts, engines, warnings, recommendations
        
        try:
            content = file_contents.get(file_path, '{}')
            if not content.strip():
                warnings.append("composer.json is empty")
                return dependencies, scripts, engines, warnings, recommendations
                
            composer_data = json.loads(content)
        except json.JSONDecodeError as e:
            warnings.append(f"Invalid composer.json format: {str(e)}")
            return dependencies, scripts, engines, warnings, recommendations
        except Exception as e:
            warnings.append(f"Error reading composer.json: {str(e)}")
            return dependencies, scripts, engines, warnings, recommendations
        
        # Parse dependencies
        require = composer_data.get('require', {})
        require_dev = composer_data.get('require-dev', {})
        
        for name, version in require.items():
            dependencies.append(Dependency(
                name=name,
                version=version,
                type='runtime',
                manager=manager
            ))
        
        for name, version in require_dev.items():
            dependencies.append(Dependency(
                name=name,
                version=version,
                type='development',
                manager=manager
            ))
        
        scripts = composer_data.get('scripts', {})
        
        return dependencies, scripts, engines, warnings, recommendations

    async def _parse_go_dependencies(self, files: List[Dict], file_contents: Dict[str, str], manager: str) -> Tuple[List[Dependency], Dict, Dict, List[str], List[str]]:
        """Parse Go module dependencies"""
        dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        
        go_mod = self._find_file_by_name(files, 'go.mod')
        if not go_mod:
            return dependencies, scripts, engines, warnings, recommendations
        
        file_path = go_mod.get('path', '')
        if not file_path:
            return dependencies, scripts, engines, warnings, recommendations
        
        content = file_contents.get(file_path, '')
        if not content.strip():
            return dependencies, scripts, engines, warnings, recommendations
        
        # Parse go.mod file
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('require '):
                # Simple parsing - would need more robust parser in production
                parts = line.replace('require ', '').split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        type='runtime',
                        manager=manager
                    ))
        
        return dependencies, scripts, engines, warnings, recommendations

    async def _parse_cargo_dependencies(self, files: List[Dict], file_contents: Dict[str, str], manager: str) -> Tuple[List[Dependency], Dict, Dict, List[str], List[str]]:
        """Parse Rust Cargo dependencies"""
        dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        
        cargo_toml = self._find_file_by_name(files, 'Cargo.toml')
        if not cargo_toml:
            return dependencies, scripts, engines, warnings, recommendations
        
        file_path = cargo_toml.get('path', '')
        if not file_path:
            return dependencies, scripts, engines, warnings, recommendations
        
        content = file_contents.get(file_path, '')
        if not content.strip():
            return dependencies, scripts, engines, warnings, recommendations
        
        # Basic TOML parsing for dependencies section
        # In production, would use proper TOML parser
        in_dependencies = False
        in_dev_dependencies = False
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line == '[dependencies]':
                in_dependencies = True
                in_dev_dependencies = False
                continue
            elif line == '[dev-dependencies]':
                in_dependencies = False
                in_dev_dependencies = True
                continue
            elif line.startswith('[') and line.endswith(']'):
                in_dependencies = False
                in_dev_dependencies = False
                continue
            
            if (in_dependencies or in_dev_dependencies) and '=' in line:
                parts = line.split('=', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    version = parts[1].strip().strip('"')
                    dep_type = 'development' if in_dev_dependencies else 'runtime'
                    
                    dependencies.append(Dependency(
                        name=name,
                        version=version,
                        type=dep_type,
                        manager=manager
                    ))
        
        return dependencies, scripts, engines, warnings, recommendations

    async def _parse_maven_dependencies(self, files: List[Dict], file_contents: Dict[str, str], manager: str) -> Tuple[List[Dependency], Dict, Dict, List[str], List[str]]:
        """Parse Maven dependencies (basic XML parsing)"""
        dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        
        pom_xml = self._find_file_by_name(files, 'pom.xml')
        if not pom_xml:
            return dependencies, scripts, engines, warnings, recommendations
        
        file_path = pom_xml.get('path', '')
        if not file_path:
            return dependencies, scripts, engines, warnings, recommendations
        
        content = file_contents.get(file_path, '')
        if not content.strip():
            return dependencies, scripts, engines, warnings, recommendations
        
        # Basic XML parsing for dependencies
        # In production, would use proper XML parser
        if '<dependencies>' in content:
            recommendations.append("Maven project detected - ensure proper dependency management")
        
        return dependencies, scripts, engines, warnings, recommendations

    async def _parse_gradle_dependencies(self, files: List[Dict], file_contents: Dict[str, str], manager: str) -> Tuple[List[Dependency], Dict, Dict, List[str], List[str]]:
        """Parse Gradle dependencies"""
        dependencies = []
        scripts = {}
        engines = {}
        warnings = []
        recommendations = []
        
        # Find gradle build file
        gradle_file = None
        gradle_filenames = ['build.gradle', 'build.gradle.kts']
        
        for f in files:
            if not isinstance(f, dict):
                continue
            filename = f.get('name', self._get_filename_from_path(f.get('path', '')))
            if filename in gradle_filenames:
                gradle_file = f
                break
        
        if not gradle_file:
            return dependencies, scripts, engines, warnings, recommendations
        
        content = file_contents.get(gradle_file.get('path', ''), '')
        
        if 'dependencies {' in content:
            recommendations.append("Gradle project detected - ensure proper dependency management")
        
        return dependencies, scripts, engines, warnings, recommendations

    def _parse_requirements_txt(self, content: str) -> Dict[str, str]:
        """Parse requirements.txt file"""
        dependencies = {}
        
        if not content or not content.strip():
            return dependencies
        
        try:
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    try:
                        if '==' in line:
                            name, version = line.split('==', 1)
                            dependencies[name.strip()] = version.strip()
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            dependencies[name.strip()] = f">={version.strip()}"
                        elif '>=' in line:
                            name, version = line.split('>=', 1)
                            dependencies[name.strip()] = f">={version.strip()}"
                        elif '~=' in line:
                            name, version = line.split('~=', 1)
                            dependencies[name.strip()] = f"~={version.strip()}"
                        elif '!=' in line:
                            name, version = line.split('!=', 1)
                            dependencies[name.strip()] = f"!={version.strip()}"
                        elif '<=' in line:
                            name, version = line.split('<=', 1)
                            dependencies[name.strip()] = f"<={version.strip()}"
                        elif '<' in line:
                            name, version = line.split('<', 1)
                            dependencies[name.strip()] = f"<{version.strip()}"
                        elif '>' in line:
                            name, version = line.split('>', 1)
                            dependencies[name.strip()] = f">{version.strip()}"
                        else:
                            # Just package name, no version specified
                            clean_name = line.split('[')[0].strip()  # Remove extras like [dev]
                            if clean_name:
                                dependencies[clean_name] = '*'
                    except ValueError:
                        # Skip malformed lines
                        continue
        except Exception:
            # Return what we have parsed so far
            pass
        
        return dependencies

    def _check_vulnerability(self, name: str, version: str) -> bool:
        """Check if a dependency version has known vulnerabilities"""
        if name in self.vulnerability_patterns:
            vulnerable_versions = self.vulnerability_patterns[name]
            return version in vulnerable_versions
        return False

    def _is_version_outdated(self, version: str) -> bool:
        """Simple check if version might be outdated (simplified logic)"""
        # Remove version specifiers
        clean_version = version.lstrip('^~>=<')
        
        # Very basic check - in production, would compare with registry
        try:
            if '.' in clean_version:
                parts = clean_version.split('.')
                if len(parts) >= 2:
                    major = int(parts[0])
                    minor = int(parts[1])
                    # Arbitrary rule: consider outdated if major version is < 1 or very old
                    return major == 0 or (major == 1 and minor < 5)
        except (ValueError, IndexError):
            pass
        
        return False

    def _check_dependency_conflicts(self, dependencies: List[Dependency]) -> List[str]:
        """Check for potential dependency conflicts"""
        warnings = []
        
        # Group dependencies by name
        dep_groups = {}
        for dep in dependencies:
            if dep.name not in dep_groups:
                dep_groups[dep.name] = []
            dep_groups[dep.name].append(dep)
        
        # Check for version conflicts
        for name, deps in dep_groups.items():
            if len(deps) > 1:
                versions = [dep.version for dep in deps]
                if len(set(versions)) > 1:
                    warnings.append(f"Version conflict for {name}: {', '.join(versions)}")
        
        return warnings

    def _generate_security_recommendations(self, dependencies: List[Dependency]) -> List[str]:
        """Generate security-related recommendations"""
        recommendations = []
        
        vulnerable_deps = [dep for dep in dependencies if dep.is_vulnerable]
        if vulnerable_deps:
            recommendations.append(f"Update {len(vulnerable_deps)} vulnerable dependencies")
        
        outdated_deps = [dep for dep in dependencies if dep.is_outdated]
        if len(outdated_deps) > 5:
            recommendations.append(f"Consider updating {len(outdated_deps)} outdated dependencies")
        
        return recommendations

    def _calculate_dependency_stats(self, dependencies: List[Dependency], package_managers: List[str]) -> Dict[str, Any]:
        """Calculate dependency statistics"""
        total = len(dependencies)
        runtime = len([dep for dep in dependencies if dep.type == 'runtime'])
        development = len([dep for dep in dependencies if dep.type == 'development'])
        outdated = len([dep for dep in dependencies if dep.is_outdated])
        vulnerable = len([dep for dep in dependencies if dep.is_vulnerable])
        
        by_manager = {}
        for manager in package_managers:
            by_manager[manager] = len([dep for dep in dependencies if dep.manager == manager])
        
        return {
            'total': total,
            'runtime': runtime,
            'development': development,
            'outdated': outdated,
            'vulnerable': vulnerable,
            'by_manager': by_manager
        }

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_analyzer():
        analyzer = DependencyAnalyzer()
        
        # Test with sample files
        sample_files = [
            {'name': 'package.json', 'path': 'package.json', 'type': 'file'},
            {'name': 'requirements.txt', 'path': 'requirements.txt', 'type': 'file'}
        ]
        
        sample_contents = {
            'package.json': '''
            {
                "dependencies": {
                    "react": "^18.0.0",
                    "lodash": "4.17.19"
                },
                "devDependencies": {
                    "typescript": "^4.0.0"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build"
                }
            }
            ''',
            'requirements.txt': '''
            django==4.0.0
            requests>=2.28.0
            pytest==6.2.0
            '''
        }
        
        result = await analyzer.analyze_dependencies(sample_files, sample_contents)
        print(json.dumps(asdict(result), indent=2, default=str))
    
    asyncio.run(test_analyzer())
