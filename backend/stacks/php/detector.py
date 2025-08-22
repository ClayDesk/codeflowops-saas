"""
PHP Stack Detector - Universal PHP Application Detection
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
import re
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.interfaces import StackDetector
from core.models import StackPlan

logger = logging.getLogger(__name__)

class PHPDetector(StackDetector):
    """Universal PHP Application Detector - Supports Laravel, BookStack, WordPress, and more"""
    
    def detect(self, repo_dir: Path, context: Optional[dict] = None) -> Optional[StackPlan]:
        """Intelligent PHP application detection with requirements analysis"""
        
        # 🛡️ BUG FIX 1: Safe context parsing with error handling
        repo_url = ""
        deployment_method = None
        if context:
            try:
                repo_url = context.get('repo_url', '') if isinstance(context, dict) else ""
                deployment_method = context.get('deployment_method') if isinstance(context, dict) else None
                
                # Safe analysis extraction
                if not deployment_method and isinstance(context, dict) and 'analysis' in context:
                    analysis = context['analysis']
                    try:
                        # Safe dictionary access
                        if isinstance(analysis, dict) and 'recommended_stack' in analysis:
                            recommended = analysis['recommended_stack']
                            if isinstance(recommended, dict):
                                deployment_method = recommended.get('deployment_method')
                        # Safe object attribute access
                        elif hasattr(analysis, 'recommended_stack') and analysis.recommended_stack:
                            if hasattr(analysis.recommended_stack, 'get'):
                                deployment_method = analysis.recommended_stack.get('deployment_method')
                        # Safe findings access
                        elif hasattr(analysis, 'findings') and analysis.findings:
                            if hasattr(analysis.findings, 'get'):
                                deployment_method = analysis.findings.get('deployment_method')
                    except (AttributeError, TypeError, KeyError) as e:
                        logger.debug(f"Safe context parsing handled error: {e}")
            except Exception as e:
                logger.debug(f"Context parsing error handled safely: {e}")
        
        # 🔍 PHASE 1: Check External Framework Detection FIRST
        # If our framework detection stage already detected Laravel, trust it BEFORE any other detection
        external_framework = None
        if context and isinstance(context, dict):
            # Check if context has detected framework info
            if 'detected_framework' in context and context['detected_framework'] == 'laravel':
                external_framework = 'laravel'
                logger.info(f"🎨 External Laravel detection found - prioritizing over local detection")
            elif 'analysis' in context:
                analysis = context['analysis']
                if isinstance(analysis, dict) and analysis.get('detected_framework') == 'laravel':
                    external_framework = 'laravel'
                    logger.info(f"🎨 External Laravel detection found in analysis - prioritizing")
        
        # If Laravel detected externally, create Laravel requirements immediately
        if external_framework == 'laravel':
            logger.info(f"🎨 Creating Laravel requirements based on external detection")
            # Enhanced database detection for Laravel
            database_info = self._detect_database_from_files(repo_dir)
            
            # 🔍 SUBDIRECTORY DETECTION: Check common subdirectories for Laravel
            laravel_subdirs = []
            for possible_subdir in ['LaraBook', 'laravel', 'app', 'src', 'web', 'backend']:
                subdir_path = repo_dir / possible_subdir
                if subdir_path.exists() and (subdir_path / "artisan").exists():
                    laravel_subdirs.append(possible_subdir)
                    logger.info(f"📁 Found Laravel in subdirectory: {possible_subdir}")
            
            # Determine correct build commands based on structure
            if laravel_subdirs:
                # Laravel is in subdirectory
                primary_subdir = laravel_subdirs[0]  # Use first detected
                build_commands = [
                    f"cd {primary_subdir}",
                    "composer install --no-dev --prefer-dist --no-interaction",
                    "php artisan key:generate --force || echo 'Key generation skipped'",
                    "php artisan config:cache || echo 'Config cache skipped'",
                    "php artisan route:cache || echo 'Route cache skipped'",
                    "php artisan view:cache || echo 'View cache skipped'",
                    "npm ci && npm run production || echo 'Frontend build skipped'"
                ]
                logger.info(f"🏗️ Laravel subdirectory build: working in {primary_subdir}/")
            else:
                # Laravel at root (normal case)
                build_commands = [
                    "composer install --no-dev --prefer-dist --no-interaction",
                    "php artisan key:generate --force || echo 'Key generation skipped'",
                    "php artisan config:cache || echo 'Config cache skipped'",
                    "php artisan route:cache || echo 'Route cache skipped'",
                    "php artisan view:cache || echo 'View cache skipped'",
                    "npm ci && npm run production || echo 'Frontend build skipped'"
                ]
            
            app_requirements = {
                "type": "laravel_blade_or_inertia_ssr",
                "php_version": ">=7.2",  # Laravel 5.4 compatibility
                "extensions": ["pdo", "mbstring", "tokenizer", "xml", "gd", "openssl"],
                "database": database_info,
                "build_process": "composer",  # Laravel uses Composer
                "build_commands": build_commands,
                "health_check": "/",
                "requires_migrations": True,
                "laravel_mode": "blade_or_inertia_ssr",
                "laravel_subdirectory": laravel_subdirs[0] if laravel_subdirs else None
            }
        else:
            # 🔍 PHASE 2: Standard Application Type Detection (only if not Laravel)
            app_requirements = self.detect_application_type(repo_dir)
        
        # 🛡️ BUG FIX: Guaranteed fallback detection - never return None
        if not app_requirements:
            logger.info(f"🔄 No specific PHP app detected, using fallback detection")
            # Fallback 1: Check for any PHP files
            php_files = list(repo_dir.glob("*.php")) + list(repo_dir.glob("**/*.php"))
            if php_files:
                logger.info(f"🌐 Fallback: Detected vanilla PHP with {len(php_files)} files")
                app_requirements = {
                    "type": "vanilla_php",
                    "php_version": ">=8.0",
                    "extensions": ["gd", "mbstring"],
                    "database": {"type": "optional"},
                    "build_process": "none", 
                    "build_commands": [],
                    "health_check": "/",
                    "requires_migrations": False
                }
            else:
                # Check if this is a documentation-only repository before PHP fallback
                file_types = {}
                total_files = 0
                for file_path in repo_dir.rglob('*'):
                    if file_path.is_file() and not any(part.startswith('.git') for part in file_path.parts):
                        total_files += 1
                        ext = file_path.suffix.lower()
                        if ext not in file_types:
                            file_types[ext] = 0
                        file_types[ext] += 1
                
                # If repository is primarily markdown files, don't treat as PHP
                md_files = file_types.get('.md', 0)
                if md_files > 0 and (md_files / total_files) >= 0.8:
                    logger.info(f"📄 Repository contains {md_files} markdown files ({md_files/total_files*100:.1f}%) - not a PHP project")
                    return None  # Let other detectors handle documentation repos
                
                # If repository is primarily Python files, don't treat as PHP
                py_files = file_types.get('.py', 0)
                if py_files > 0 and (py_files / total_files) >= 0.3:
                    logger.info(f"🐍 Repository contains {py_files} Python files ({py_files/total_files*100:.1f}%) - not a PHP project")
                    return None  # Let Python detectors handle this
                
                # Check for Python project indicators
                python_indicators = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'environment.yml']
                for indicator in python_indicators:
                    if (repo_dir / indicator).exists():
                        logger.info(f"🐍 Found Python indicator '{indicator}' - not a PHP project")
                        return None
                
                # Fallback 2: Ultimate fallback for any directory (only if not documentation or Python)
                logger.info(f"🔄 Ultimate fallback: Treating as generic PHP project")
                app_requirements = {
                    "type": "generic_php",
                    "php_version": ">=8.0", 
                    "extensions": ["gd", "mbstring"],
                    "database": {"type": "optional"},
                    "build_process": "none",
                    "build_commands": [],
                    "health_check": "/",
                    "requires_migrations": False
                }
            
        logger.info(f"🔍 Final detection: {app_requirements['type']} with {len(app_requirements.get('extensions', []))} PHP extensions")
        
        # 🧬 PHASE 2: Enhanced Requirements Analysis
        composer_requirements = self.scan_composer_requirements(repo_dir)
        
        # Merge detected and composer requirements
        merged_requirements = self._merge_requirements(app_requirements, composer_requirements)
        
        # 🛡️ BUG FIX 2: Framework value normalization for consistency
        framework_name = merged_requirements['type']
        # Normalize Laravel variants to consistent "laravel" for compatibility
        if framework_name.startswith('laravel_'):
            normalized_framework = "laravel"
            laravel_mode = framework_name.split('laravel_', 1)[1]
        else:
            normalized_framework = framework_name
            laravel_mode = None
        
        logger.info(f"🎯 Normalized framework: '{framework_name}' → '{normalized_framework}'" + 
                   (f" (mode: {laravel_mode})" if laravel_mode else ""))
        
        # 🎯 CORRECT STACK KEY: Use php_laravel when Laravel is detected
        if normalized_framework == "laravel":
            stack_key = "php_laravel"  # This will set build_tool=composer and is_build_ready=True
            logger.info(f"🎨 Setting stack_key to 'php_laravel' for proper Laravel build configuration")
        else:
            stack_key = "php"
        
        # Detect PHP entry point
        entry_point = "index.php"  # Default
        if (repo_dir / "public" / "index.php").exists():
            entry_point = "public/index.php"  # Laravel/Symfony structure
        elif (repo_dir / "web" / "index.php").exists():
            entry_point = "web/index.php"  # Symfony
        elif (repo_dir / "www" / "index.php").exists():
            entry_point = "www/index.php"  # Alternative structure
        elif (repo_dir / "app.php").exists():
            entry_point = "app.php"  # Single file app
        
        return StackPlan(
            stack_key=stack_key,
            build_cmds=merged_requirements.get('build_commands', ["composer install --no-dev --optimize-autoloader"]),
            output_dir=repo_dir,
            config={
                'entry_point': entry_point,
                'framework': normalized_framework,  # Use normalized name
                'framework_variant': framework_name,  # Keep original for detailed info
                'laravel_mode': laravel_mode,  # Extract Laravel mode if applicable
                'app_type': normalized_framework,  # For backward compatibility
                'runtime': 'php',
                'deployment_type': 'container',
                'repository_url': repo_url,
                'deployment_method': deployment_method,
                # 🚀 NEW: Application requirements for universal deployment
                'requirements': merged_requirements,
                'php_version': merged_requirements.get('php_version', '>=8.0'),
                'php_extensions': merged_requirements.get('extensions', []),
                'database': merged_requirements.get('database', {'type': 'optional'}),
                'build_process': merged_requirements.get('build_process', 'generic')
            }
        )
    
    def _detect_database_from_files(self, repo_path: Path) -> Dict[str, Any]:
        """🔍 Enhanced database detection from SQL files and config"""
        database_info = {"type": "optional", "required": False}
        
        # Check for SQL files
        sql_files = list(repo_path.glob("**/*.sql"))
        if sql_files:
            logger.info(f"📄 Found {len(sql_files)} SQL files - inferring database requirement")
            database_info = {"type": "mysql", "version": ">=5.7", "required": True}
        
        # Check Laravel database config
        db_config_path = repo_path / "config" / "database.php"
        if db_config_path.exists():
            try:
                with open(db_config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'mysql' in content.lower():
                        database_info = {"type": "mysql", "version": ">=5.7", "required": True}
                    elif 'postgres' in content.lower():
                        database_info = {"type": "postgresql", "version": ">=10", "required": True}
                    elif 'sqlite' in content.lower():
                        database_info = {"type": "sqlite", "required": False}
            except Exception as e:
                logger.debug(f"Failed to read database config: {e}")
        
        # Check for migration files
        migrations_path = repo_path / "database" / "migrations"
        if migrations_path.exists():
            migration_files = list(migrations_path.glob("*.php"))
            if migration_files:
                logger.info(f"📋 Found {len(migration_files)} migration files - database required")
                if database_info["type"] == "optional":
                    database_info = {"type": "mysql", "version": ">=5.7", "required": True}
                else:
                    database_info["required"] = True
        
        return database_info
    
    def detect_application_type(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """🔍 Detect specific PHP application and its requirements"""
        
        # 📚 BookStack Detection
        if (repo_path / "app" / "BookStack.php").exists() or self._is_bookstack_repo(repo_path):
            logger.info("� BookStack application detected")
            return {
                "type": "bookstack",
                "php_version": ">=8.2", 
                "extensions": ["gd", "dom", "iconv", "mbstring", "mysqlnd", "openssl", "pdo", "pdo_mysql", "tokenizer", "xml", "zip"],
                "database": {"type": "mysql", "version": ">=5.7", "required": True},
                "build_process": "bookstack",
                "build_commands": [
                    "composer install --no-dev --optimize-autoloader",
                    "cp .env.example .env || touch .env"
                ],
                "health_check": "/status",
                "requires_migrations": True,
                "file_permissions": ["storage", "bootstrap/cache", "public/uploads"]
            }
        
        # 🎨 Laravel Detection (Enhanced)
        if (repo_path / "artisan").exists() or self._has_laravel_composer(repo_path):
            laravel_type = self._classify_laravel_type(repo_path)
            logger.info(f"🎨 Laravel application detected - type: {laravel_type}")
            
            # Enhanced database detection for Laravel
            database_info = self._detect_database_from_files(repo_path)
            
            return {
                "type": f"laravel_{laravel_type}",
                "php_version": ">=8.1",
                "extensions": ["pdo", "mbstring", "tokenizer", "xml", "gd", "openssl"],
                "database": database_info,
                "build_process": "composer",  # Fixed: Laravel uses Composer as build tool
                "build_commands": [
                    "composer install --optimize-autoloader",
                    "php artisan key:generate --no-interaction --force || echo 'Key generation skipped'",
                    "npm install && npm run build || echo 'Frontend build skipped'"
                ],
                "health_check": "/health",
                "requires_migrations": True,
                "laravel_mode": laravel_type
            }
        
        # 📝 WordPress Detection
        if (repo_path / "wp-config-sample.php").exists() or (repo_path / "wp-config.php").exists():
            logger.info("� WordPress application detected")
            return {
                "type": "wordpress",
                "php_version": ">=7.4",
                "extensions": ["mysqli", "gd", "zip", "mbstring", "xml", "curl"],
                "database": {"type": "mysql", "version": ">=5.6", "required": True},
                "build_process": "wordpress",
                "build_commands": [],  # WordPress doesn't need build process
                "health_check": "/wp-admin/install.php",
                "requires_migrations": False
            }
        
        # 🎼 Symfony Detection
        if self._has_symfony_composer(repo_path) or (repo_path / "bin" / "console").exists():
            logger.info("🎼 Symfony application detected")
            return {
                "type": "symfony",
                "php_version": ">=8.0",
                "extensions": ["pdo", "mbstring", "xml", "tokenizer", "intl"],
                "database": {"type": "mysql", "version": ">=5.7", "required": False},
                "build_process": "symfony",
                "build_commands": [
                    "composer install --no-dev --optimize-autoloader",
                    "php bin/console cache:clear --env=prod || echo 'Cache clear skipped'"
                ],
                "health_check": "/health",
                "requires_migrations": False
            }
        
        # 🛒 Magento Detection
        if (repo_path / "app" / "Mage.php").exists() or (repo_path / "bin" / "magento").exists():
            logger.info("� Magento application detected")
            return {
                "type": "magento",
                "php_version": ">=8.1",
                "extensions": ["pdo", "mbstring", "gd", "zip", "xml", "soap", "intl", "xsl"],
                "database": {"type": "mysql", "version": ">=8.0", "required": True},
                "build_process": "magento",
                "build_commands": [
                    "composer install --no-dev",
                    "php bin/magento setup:di:compile || echo 'DI compile skipped'"
                ],
                "health_check": "/",
                "requires_migrations": False
            }
        
        # 🏪 Generic PHP with Composer
        composer_json = repo_path / "composer.json"
        if composer_json.exists():
            logger.info("🏪 Generic PHP application with Composer detected")
            return {
                "type": "generic_php_composer",
                "php_version": ">=8.0",
                "extensions": ["pdo", "mbstring", "xml", "gd"],
                "database": {"type": "optional"},
                "build_process": "composer",
                "build_commands": ["composer install --no-dev --optimize-autoloader"],
                "health_check": "/",
                "requires_migrations": False
            }
        
        # 🌐 Vanilla PHP Detection
        php_files = list(repo_path.glob("*.php")) + list(repo_path.glob("**/*.php"))
        if php_files:
            logger.info(f"🌐 Vanilla PHP application detected ({len(php_files)} PHP files)")
            return {
                "type": "vanilla_php",
                "php_version": ">=8.0",
                "extensions": ["gd", "mbstring"],
                "database": {"type": "optional"},
                "build_process": "none",
                "build_commands": [],
                "health_check": "/",
                "requires_migrations": False
            }
        
        return None
    
    def scan_composer_requirements(self, repo_path: Path) -> Dict[str, Any]:
        """🧬 Scan composer.json for PHP requirements and dependencies"""
        
        composer_path = repo_path / "composer.json"
        requirements = {
            "php_version": ">=8.0",
            "extensions": [],
            "dependencies": [],
            "dev_dependencies": []
        }
        
        if not composer_path.exists():
            return requirements
            
        try:
            with open(composer_path, 'r', encoding='utf-8') as f:
                composer_data = json.load(f)
            
            # Extract PHP version requirement
            require = composer_data.get('require', {})
            if 'php' in require:
                requirements['php_version'] = require['php']
            
            # Extract extension requirements from composer
            for package, version in require.items():
                if package.startswith('ext-'):
                    extension = package.replace('ext-', '')
                    if extension not in requirements['extensions']:
                        requirements['extensions'].append(extension)
                else:
                    requirements['dependencies'].append(package)
            
            # Extract dev dependencies
            require_dev = composer_data.get('require-dev', {})
            requirements['dev_dependencies'] = list(require_dev.keys())
            
            logger.debug(f"📋 Composer analysis: PHP {requirements['php_version']}, {len(requirements['extensions'])} extensions")
            
        except Exception as e:
            logger.warning(f"Failed to parse composer.json: {e}")
        
        return requirements
    
    def _merge_requirements(self, app_requirements: Dict[str, Any], composer_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """🔀 Merge application-detected and composer-detected requirements"""
        
        # Start with application requirements as base
        merged = app_requirements.copy()
        
        # Merge PHP version (use more restrictive version)
        app_version = app_requirements.get('php_version', '>=8.0')
        composer_version = composer_requirements.get('php_version', '>=8.0')
        merged['php_version'] = self._get_more_restrictive_version(app_version, composer_version)
        
        # Merge extensions (union of both sets)
        app_extensions = set(app_requirements.get('extensions', []))
        composer_extensions = set(composer_requirements.get('extensions', []))
        merged['extensions'] = list(app_extensions.union(composer_extensions))
        
        # Add composer-specific data
        merged['composer_dependencies'] = composer_requirements.get('dependencies', [])
        merged['composer_dev_dependencies'] = composer_requirements.get('dev_dependencies', [])
        
        logger.info(f"🔀 Merged requirements: {len(merged['extensions'])} total extensions")
        
        return merged
    
    def _get_more_restrictive_version(self, version1: str, version2: str) -> str:
        """Compare PHP version constraints and return the more restrictive one"""
        # Simple heuristic: longer constraint is usually more restrictive
        # In production, you'd want proper semantic version comparison
        if len(version1) >= len(version2):
            return version1
        return version2
    
    def _is_bookstack_repo(self, repo_path: Path) -> bool:
        """Check if this is a BookStack repository"""
        # Check for BookStack-specific files and patterns
        bookstack_indicators = [
            repo_path / "app" / "BookStack.php",
            repo_path / "app" / "Book.php",
            repo_path / "app" / "Page.php",
            repo_path / "app" / "Chapter.php"
        ]
        
        # Check composer.json for BookStack specific packages
        composer_path = repo_path / "composer.json"
        if composer_path.exists():
            try:
                with open(composer_path, 'r') as f:
                    data = json.load(f)
                    name = data.get('name', '')
                    if 'bookstack' in name.lower():
                        return True
                        
                    # Check for BookStack-specific dependencies
                    require = data.get('require', {})
                    bookstack_deps = ['intervention/image', 'league/flysystem', 'socialiteproviders']
                    if any(dep in str(require) for dep in bookstack_deps) and len(require) > 15:
                        return True
            except:
                pass
        
        return any(indicator.exists() for indicator in bookstack_indicators)
    
    def _has_laravel_composer(self, repo_path: Path) -> bool:
        """Check if composer.json indicates Laravel"""
        composer_path = repo_path / "composer.json"
        if not composer_path.exists():
            return False
            
        try:
            with open(composer_path, 'r') as f:
                data = json.load(f)
                require = data.get('require', {})
                return any(key in require for key in ['laravel/framework', 'laravel/laravel'])
        except:
            return False
    
    def _has_symfony_composer(self, repo_path: Path) -> bool:
        """Check if composer.json indicates Symfony"""
        composer_path = repo_path / "composer.json"
        if not composer_path.exists():
            return False
            
        try:
            with open(composer_path, 'r') as f:
                data = json.load(f)
                require = data.get('require', {})
                return any(key in require for key in ['symfony/symfony', 'symfony/framework-bundle', 'symfony/console'])
        except:
            return False
    
    def _classify_laravel_type(self, repo_path: Path) -> str:
        """Classify Laravel application type (api, full, etc.)"""
        try:
            # Import the existing classification logic if available
            from detectors.stack_detector import classify_laravel_type
            return classify_laravel_type(repo_path)
        except ImportError:
            # Fallback classification logic
            if (repo_path / "resources" / "views").exists():
                return "full"
            elif (repo_path / "routes" / "api.php").exists():
                return "api" 
            else:
                return "basic"
    
    def get_priority(self) -> int:
        """PHP detection should run after more specific detectors"""
        return 30  # Lower than Next.js (50) but higher than generic React (10)
