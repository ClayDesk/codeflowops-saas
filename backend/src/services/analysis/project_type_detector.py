"""
Project Type Detector
Advanced project type detection with confidence scoring and evidence collection
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class DetectionRule:
    """A rule for detecting a specific project type"""
    name: str
    patterns: List[str]
    required_files: List[str]
    optional_files: List[str]
    confidence_weight: float
    evidence_description: str

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

class ProjectTypeDetector:
    """
    Advanced project type detection with machine learning-like confidence scoring
    """
    
    def __init__(self):
        self.detection_rules = self._initialize_detection_rules()
        self.framework_signatures = self._initialize_framework_signatures()
        
    def _initialize_detection_rules(self) -> Dict[str, List[DetectionRule]]:
        """Initialize detection rules for different project types"""
        return {
            'react': [
                DetectionRule(
                    name='create-react-app',
                    patterns=['src/App.js', 'src/index.js', 'public/index.html'],
                    required_files=['package.json'],
                    optional_files=['src/App.css', 'src/index.css', 'public/manifest.json'],
                    confidence_weight=0.9,
                    evidence_description='Create React App structure detected'
                ),
                DetectionRule(
                    name='custom-react',
                    patterns=['*.jsx', '*.tsx'],
                    required_files=['package.json'],
                    optional_files=['webpack.config.js', 'babel.config.js'],
                    confidence_weight=0.7,
                    evidence_description='Custom React setup detected'
                ),
                DetectionRule(
                    name='react-vite',
                    patterns=['src/main.jsx', 'src/main.tsx'],
                    required_files=['package.json', 'vite.config.js'],
                    optional_files=['index.html'],
                    confidence_weight=0.85,
                    evidence_description='React with Vite detected'
                )
            ],
            'nextjs': [
                DetectionRule(
                    name='nextjs-pages',
                    patterns=['pages/*.js', 'pages/*.tsx'],
                    required_files=['package.json'],
                    optional_files=['next.config.js', 'pages/_app.js', 'pages/_document.js'],
                    confidence_weight=0.95,
                    evidence_description='Next.js Pages Router detected'
                ),
                DetectionRule(
                    name='nextjs-app',
                    patterns=['app/page.js', 'app/page.tsx', 'app/layout.js'],
                    required_files=['package.json'],
                    optional_files=['next.config.js', 'app/globals.css'],
                    confidence_weight=0.95,
                    evidence_description='Next.js App Router (13+) detected'
                )
            ],
            'vue': [
                DetectionRule(
                    name='vue-cli',
                    patterns=['src/main.js', 'src/App.vue'],
                    required_files=['package.json'],
                    optional_files=['vue.config.js', 'src/components/*'],
                    confidence_weight=0.9,
                    evidence_description='Vue CLI project detected'
                ),
                DetectionRule(
                    name='nuxt',
                    patterns=['pages/*.vue', 'nuxt.config.js'],
                    required_files=['package.json'],
                    optional_files=['layouts/', 'components/', 'plugins/'],
                    confidence_weight=0.95,
                    evidence_description='Nuxt.js project detected'
                ),
                DetectionRule(
                    name='vue-vite',
                    patterns=['src/main.js', 'src/main.ts'],
                    required_files=['package.json', 'vite.config.js'],
                    optional_files=['index.html'],
                    confidence_weight=0.85,
                    evidence_description='Vue with Vite detected'
                )
            ],
            'angular': [
                DetectionRule(
                    name='angular-cli',
                    patterns=['src/main.ts', 'src/app/app.module.ts'],
                    required_files=['angular.json', 'package.json'],
                    optional_files=['src/app/app.component.ts', 'tsconfig.json'],
                    confidence_weight=0.95,
                    evidence_description='Angular CLI project detected'
                )
            ],
            'svelte': [
                DetectionRule(
                    name='sveltekit',
                    patterns=['src/routes/', 'src/app.html'],
                    required_files=['package.json', 'svelte.config.js'],
                    optional_files=['src/lib/', 'static/'],
                    confidence_weight=0.9,
                    evidence_description='SvelteKit project detected'
                ),
                DetectionRule(
                    name='svelte-vite',
                    patterns=['src/main.js', 'src/App.svelte'],
                    required_files=['package.json', 'vite.config.js'],
                    optional_files=['src/lib/'],
                    confidence_weight=0.85,
                    evidence_description='Svelte with Vite detected'
                )
            ],
            'gatsby': [
                DetectionRule(
                    name='gatsby',
                    patterns=['gatsby-config.js', 'src/pages/'],
                    required_files=['package.json'],
                    optional_files=['gatsby-node.js', 'gatsby-browser.js'],
                    confidence_weight=0.95,
                    evidence_description='Gatsby static site detected'
                )
            ],
            'static': [
                DetectionRule(
                    name='html-css-js',
                    patterns=['index.html', '*.html'],
                    required_files=[],
                    optional_files=['style.css', 'styles.css', 'script.js', 'main.js'],
                    confidence_weight=0.6,
                    evidence_description='Static HTML/CSS/JS site detected'
                ),
                DetectionRule(
                    name='jekyll',
                    patterns=['_config.yml', '_posts/', '_layouts/'],
                    required_files=[],
                    optional_files=['Gemfile', '_includes/', '_sass/'],
                    confidence_weight=0.9,
                    evidence_description='Jekyll static site detected'
                ),
                DetectionRule(
                    name='hugo',
                    patterns=['config.toml', 'config.yaml', 'content/'],
                    required_files=[],
                    optional_files=['themes/', 'static/', 'layouts/'],
                    confidence_weight=0.9,
                    evidence_description='Hugo static site detected'
                )
            ],
            'python': [
                DetectionRule(
                    name='django',
                    patterns=['manage.py', '*/settings.py', '*/urls.py'],
                    required_files=['requirements.txt'],
                    optional_files=['*/wsgi.py', '*/asgi.py'],
                    confidence_weight=0.95,
                    evidence_description='Django web application detected'
                ),
                DetectionRule(
                    name='flask',
                    patterns=['app.py', '*/app.py'],
                    required_files=['requirements.txt'],
                    optional_files=['config.py', 'wsgi.py'],
                    confidence_weight=0.85,
                    evidence_description='Flask web application detected'
                ),
                DetectionRule(
                    name='fastapi',
                    patterns=['main.py', '*/main.py'],
                    required_files=['requirements.txt'],
                    optional_files=['uvicorn.py'],
                    confidence_weight=0.85,
                    evidence_description='FastAPI application detected'
                )
            ]
        }
    
    def _initialize_framework_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize framework-specific signatures for package.json analysis"""
        return {
            'react': {
                'dependencies': ['react', 'react-dom'],
                'dev_dependencies': ['@testing-library/react', 'react-scripts'],
                'scripts': ['start', 'build'],
                'build_outputs': {
                    'create-react-app': 'build',
                    'vite': 'dist',
                    'custom': 'build'
                }
            },
            'nextjs': {
                'dependencies': ['next', 'react', 'react-dom'],
                'dev_dependencies': [],
                'scripts': ['dev', 'build', 'start'],
                'build_outputs': {
                    'default': 'out',
                    'static': 'out',
                    'server': '.next'
                }
            },
            'vue': {
                'dependencies': ['vue'],
                'dev_dependencies': ['@vue/cli-service', 'vite'],
                'scripts': ['serve', 'build'],
                'build_outputs': {
                    'vue-cli': 'dist',
                    'vite': 'dist',
                    'nuxt': '.output'
                }
            },
            'angular': {
                'dependencies': ['@angular/core', '@angular/common'],
                'dev_dependencies': ['@angular/cli', '@angular-devkit/build-angular'],
                'scripts': ['ng', 'start', 'build'],
                'build_outputs': {
                    'default': 'dist'
                }
            },
            'svelte': {
                'dependencies': ['svelte'],
                'dev_dependencies': ['@sveltejs/kit', 'vite'],
                'scripts': ['dev', 'build'],
                'build_outputs': {
                    'sveltekit': 'build',
                    'vite': 'dist'
                }
            }
        }

    def detect_project_types(self, file_tree: List[Dict], package_json_content: Optional[str] = None) -> List[ProjectTypeResult]:
        """
        Detect project types with confidence scoring
        """
        file_paths = [f['path'] for f in file_tree if f['type'] == 'file']
        # Extract filenames from paths
        file_names = [f['path'].split('/')[-1] for f in file_tree if f['type'] == 'file']
        
        # Parse package.json if available
        package_data = None
        if package_json_content:
            try:
                package_data = json.loads(package_json_content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse package.json content")
        
        detected_types = []
        
        # Check each project type
        for project_type, rules in self.detection_rules.items():
            for rule in rules:
                result = self._evaluate_rule(rule, file_paths, file_names, package_data, project_type)
                if result and result.confidence >= 30:  # Minimum confidence threshold
                    detected_types.append(result)
        
        # Sort by confidence and remove duplicates
        detected_types.sort(key=lambda x: x.confidence, reverse=True)
        unique_types = []
        seen_types = set()
        
        for detection in detected_types:
            if detection.type not in seen_types:
                unique_types.append(detection)
                seen_types.add(detection.type)
        
        return unique_types[:5]  # Return top 5 matches
    
    def _evaluate_rule(self, rule: DetectionRule, file_paths: List[str], 
                      file_names: List[str], package_data: Optional[Dict], 
                      project_type: str) -> Optional[ProjectTypeResult]:
        """Evaluate a detection rule against the file structure"""
        
        confidence = 0.0
        evidence = []
        subtype = rule.name
        
        # Check required files
        required_score = 0
        for required_file in rule.required_files:
            if required_file in file_names:
                required_score += 1
                evidence.append(f"Required file found: {required_file}")
        
        if rule.required_files and required_score == 0:
            return None  # Must have at least one required file
        
        # Base confidence from required files
        if rule.required_files:
            confidence += (required_score / len(rule.required_files)) * 40
        
        # Check pattern matches
        pattern_matches = 0
        for pattern in rule.patterns:
            matches = self._match_pattern(pattern, file_paths)
            if matches:
                pattern_matches += len(matches)
                evidence.extend([f"Pattern match: {match}" for match in matches[:3]])  # Limit evidence
        
        if pattern_matches > 0:
            confidence += min(pattern_matches * 10, 30)
        
        # Check optional files (bonus points)
        optional_score = 0
        for optional_file in rule.optional_files:
            if optional_file in file_names or any(self._match_pattern(optional_file, file_paths)):
                optional_score += 1
                evidence.append(f"Optional file found: {optional_file}")
        
        if rule.optional_files:
            confidence += (optional_score / len(rule.optional_files)) * 15
        
        # Package.json analysis boost
        if package_data and project_type in self.framework_signatures:
            package_boost, package_evidence = self._analyze_package_json(package_data, project_type, subtype)
            confidence += package_boost
            evidence.extend(package_evidence)
        
        # Apply rule weight
        confidence *= rule.confidence_weight
        
        if confidence >= 30:  # Minimum threshold
            # Determine build configuration
            build_command, output_dir, dev_server = self._determine_build_config(project_type, subtype, package_data)
            
            return ProjectTypeResult(
                type=project_type.title(),
                confidence=min(confidence, 100),
                evidence=evidence,
                subtype=subtype,
                build_command=build_command,
                output_directory=output_dir,
                development_server=dev_server
            )
        
        return None
    
    def _match_pattern(self, pattern: str, file_paths: List[str]) -> List[str]:
        """Match a pattern against file paths"""
        matches = []
        
        # Convert glob pattern to regex
        if '*' in pattern:
            regex_pattern = pattern.replace('*', '.*')
            regex_pattern = regex_pattern.replace('/', r'\/')
            try:
                for path in file_paths:
                    if re.match(regex_pattern, path):
                        matches.append(path)
            except re.error:
                pass
        else:
            # Exact match
            if pattern in file_paths:
                matches.append(pattern)
        
        return matches
    
    def _analyze_package_json(self, package_data: Dict, project_type: str, subtype: str) -> Tuple[float, List[str]]:
        """Analyze package.json for framework-specific dependencies"""
        confidence_boost = 0.0
        evidence = []
        
        if project_type not in self.framework_signatures:
            return confidence_boost, evidence
        
        signature = self.framework_signatures[project_type]
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        scripts = package_data.get('scripts', {})
        
        # Check required dependencies
        required_deps = signature.get('dependencies', [])
        found_deps = [dep for dep in required_deps if dep in dependencies]
        if found_deps:
            confidence_boost += len(found_deps) * 15
            evidence.extend([f"Dependency found: {dep}" for dep in found_deps])
        
        # Check dev dependencies
        dev_deps = signature.get('dev_dependencies', [])
        found_dev_deps = [dep for dep in dev_deps if dep in dev_dependencies]
        if found_dev_deps:
            confidence_boost += len(found_dev_deps) * 10
            evidence.extend([f"Dev dependency found: {dep}" for dep in found_dev_deps])
        
        # Check scripts
        expected_scripts = signature.get('scripts', [])
        found_scripts = [script for script in expected_scripts if script in scripts]
        if found_scripts:
            confidence_boost += len(found_scripts) * 5
            evidence.extend([f"Script found: {script}" for script in found_scripts])
        
        return confidence_boost, evidence
    
    def _determine_build_config(self, project_type: str, subtype: str, package_data: Optional[Dict]) -> Tuple[str, str, str]:
        """Determine build command, output directory, and dev server command"""
        
        build_command = ""
        output_dir = ""
        dev_server = ""
        
        if project_type == 'react':
            if subtype == 'create-react-app':
                build_command = "npm run build"
                output_dir = "build"
                dev_server = "npm start"
            elif subtype == 'react-vite':
                build_command = "npm run build"
                output_dir = "dist"
                dev_server = "npm run dev"
            else:
                build_command = "npm run build"
                output_dir = "build"
                dev_server = "npm start"
        
        elif project_type == 'nextjs':
            if subtype == 'nextjs-app' or subtype == 'nextjs-pages':
                build_command = "npm run build && npm run export"
                output_dir = "out"
                dev_server = "npm run dev"
        
        elif project_type == 'vue':
            if subtype == 'nuxt':
                build_command = "npm run generate"
                output_dir = ".output/public"
                dev_server = "npm run dev"
            elif subtype == 'vue-vite':
                build_command = "npm run build"
                output_dir = "dist"
                dev_server = "npm run dev"
            else:
                build_command = "npm run build"
                output_dir = "dist"
                dev_server = "npm run serve"
        
        elif project_type == 'angular':
            build_command = "npm run build"
            output_dir = "dist"
            dev_server = "npm start"
        
        elif project_type == 'svelte':
            if subtype == 'sveltekit':
                build_command = "npm run build"
                output_dir = "build"
                dev_server = "npm run dev"
            else:
                build_command = "npm run build"
                output_dir = "dist"
                dev_server = "npm run dev"
        
        elif project_type == 'gatsby':
            build_command = "npm run build"
            output_dir = "public"
            dev_server = "npm run develop"
        
        elif project_type == 'static':
            build_command = ""
            output_dir = "."
            dev_server = ""
        
        elif project_type == 'python':
            if subtype == 'django':
                build_command = "python manage.py collectstatic --noinput"
                output_dir = "staticfiles"
                dev_server = "python manage.py runserver"
            elif subtype == 'flask':
                build_command = ""
                output_dir = "."
                dev_server = "python app.py"
            elif subtype == 'fastapi':
                build_command = ""
                output_dir = "."
                dev_server = "uvicorn main:app --reload"
        
        # Override with package.json scripts if available
        if package_data and package_data.get('scripts'):
            scripts = package_data['scripts']
            
            # Try to detect build command
            if 'build' in scripts and not build_command:
                build_command = "npm run build"
            
            # Try to detect dev server
            if 'dev' in scripts and not dev_server:
                dev_server = "npm run dev"
            elif 'start' in scripts and not dev_server:
                dev_server = "npm start"
        
        return build_command, output_dir, dev_server

# Example usage
if __name__ == "__main__":
    detector = ProjectTypeDetector()
    
    # Test with sample file structure
    sample_files = [
        {'name': 'package.json', 'path': 'package.json', 'type': 'file'},
        {'name': 'App.js', 'path': 'src/App.js', 'type': 'file'},
        {'name': 'index.js', 'path': 'src/index.js', 'type': 'file'},
        {'name': 'index.html', 'path': 'public/index.html', 'type': 'file'},
    ]
    
    sample_package_json = """
    {
        "dependencies": {
            "react": "^18.0.0",
            "react-dom": "^18.0.0"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build"
        }
    }
    """
    
    results = detector.detect_project_types(sample_files, sample_package_json)
    for result in results:
        print(json.dumps(asdict(result), indent=2))
