# detectors/stack_detector.py
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def _read_package_json(repo: Path):
    """Read package.json safely"""
    p = repo / "package.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Failed to read package.json from {repo}: {e}")
        return {}

def is_php_repo(repo: Path) -> bool:
    """
    Detect PHP repositories using reliable signals:
    1. composer.json exists
    2. PHP files exist (.php extension)
    3. Laravel/Symfony specific files
    """
    # Signal 1: composer.json (most reliable for modern PHP)
    if (repo / "composer.json").exists():
        logger.info("Detected PHP: composer.json found")
        return True
    
    # Signal 2: Check for PHP files
    php_files = list(repo.glob("*.php")) + list(repo.glob("**/*.php"))
    if php_files:
        logger.info(f"Detected PHP: Found {len(php_files)} PHP files")
        return True
    
    # Signal 3: Laravel specific files
    laravel_indicators = ["artisan", "bootstrap/app.php", "config/app.php"]
    if any((repo / indicator).exists() for indicator in laravel_indicators):
        logger.info("Detected PHP: Laravel framework files found")
        return True
    
    return False

def classify_laravel_type(repo: Path) -> str:
    """
    Classify Laravel application type based on priority rules:
    1. composer.json && artisan → Laravel detected
    2. /frontend|/client has .vue + package.json → spa_split
    3. vite.config.* or webpack.mix.js || .vue under resources/js → blade_or_inertia_ssr
    4. Inertia detection: @inertiajs/* deps or HandleInertiaRequests middleware
    5. Else → api_only
    """
    composer_json = repo / "composer.json"
    artisan = repo / "artisan"
    
    # Must be Laravel first
    if not (composer_json.exists() and artisan.exists()):
        return "generic_php"
    
    logger.info("Laravel detected - classifying type...")
    
    # Check for SPA split architecture
    spa_dirs = [repo / "frontend", repo / "client"]
    for spa_dir in spa_dirs:
        if spa_dir.exists():
            vue_files = list(spa_dir.glob("**/*.vue"))
            package_json = spa_dir / "package.json"
            if vue_files and package_json.exists():
                logger.info("Laravel SPA Split: Frontend/client directory with Vue files and package.json")
                return "spa_split"
    
    # Check for Inertia.js indicators
    inertia_detected = False
    if composer_json.exists():
        try:
            with open(composer_json, 'r') as f:
                composer_data = json.load(f)
            require = {**composer_data.get('require', {}), **composer_data.get('require-dev', {})}
            
            # Check for Inertia dependencies
            if any('@inertiajs' in dep for dep in require.keys()):
                inertia_detected = True
                logger.info("Inertia.js detected via composer dependencies")
        except:
            pass
    
    # Check for HandleInertiaRequests middleware
    middleware_files = list(repo.glob("app/Http/Middleware/**/*.php"))
    for middleware_file in middleware_files:
        try:
            content = middleware_file.read_text(encoding='utf-8', errors='ignore')
            if 'HandleInertiaRequests' in content:
                inertia_detected = True
                logger.info("Inertia.js detected via HandleInertiaRequests middleware")
                break
        except:
            continue
    
    # Check for build tools and Vue files in resources
    package_json = repo / "package.json"
    has_package_json = package_json.exists()
    
    # Build tool detection
    vite_config = any((repo / f"vite.config.{ext}").exists() for ext in ['js', 'ts', 'mjs'])
    webpack_mix = (repo / "webpack.mix.js").exists()
    
    # Vue files in resources
    resources_vue = list((repo / "resources/js").glob("**/*.vue")) if (repo / "resources/js").exists() else []
    
    # Check package.json for Vue/Inertia dependencies
    vue_in_package = False
    if has_package_json:
        try:
            with open(package_json, 'r') as f:
                pkg_data = json.load(f)
            deps = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
            
            if any('@inertiajs' in dep for dep in deps.keys()):
                inertia_detected = True
                logger.info("Inertia.js detected via package.json dependencies")
            
            if 'vue' in deps or any('vue' in dep for dep in deps.keys()):
                vue_in_package = True
        except:
            pass
    
    # Decision logic
    if inertia_detected:
        logger.info("Laravel type: blade_or_inertia_ssr (Inertia.js detected)")
        return "blade_or_inertia_ssr"
    
    if vite_config or webpack_mix or resources_vue or vue_in_package:
        if vite_config:
            logger.info("Laravel type: blade_or_inertia_ssr (Vite config found)")
        elif webpack_mix:
            logger.info("Laravel type: blade_or_inertia_ssr (Webpack Mix found)")
        elif resources_vue:
            logger.info(f"Laravel type: blade_or_inertia_ssr ({len(resources_vue)} Vue files in resources/js)")
        else:
            logger.info("Laravel type: blade_or_inertia_ssr (Vue in package.json)")
        return "blade_or_inertia_ssr"
    
    # Default to API only if no frontend indicators
    logger.info("Laravel type: api_only (no frontend build tools or Vue files found)")
    return "api_only"

def get_php_framework(repo: Path) -> str:
    """Detect specific PHP framework with Laravel sub-classification"""
    composer_json = repo / "composer.json"
    
    if composer_json.exists():
        try:
            with open(composer_json, 'r') as f:
                data = json.load(f)
            
            require = data.get('require', {})
            
            if 'laravel/framework' in require or 'laravel/laravel' in require:
                laravel_type = classify_laravel_type(repo)
                return f"laravel_{laravel_type}"
            elif 'symfony/symfony' in require or 'symfony/framework-bundle' in require:
                return "symfony"
            elif 'slim/slim' in require:
                return "slim"
        except:
            pass
    
    # Check for Laravel specific structure
    if (repo / "artisan").exists():
        return "laravel"
    
    return "php"

def is_static_site(repo: Path) -> bool:
    """
    Detect static sites - heuristic: no build tool; pure HTML/CSS/JS
    """
    # If package.json exists, it's likely not a pure static site
    if (repo / "package.json").exists():
        return False
    
    # Look for common static site indicators
    static_indicators = ["index.html", "public/index.html", "src/index.html"]
    if any((repo / f).exists() for f in static_indicators):
        logger.info("Detected static site: HTML files without package.json")
        return True
    
    return False
    """
    Detect static sites - heuristic: no build tool; pure HTML/CSS/JS
    """
    # If package.json exists, it's likely not a pure static site
    if (repo / "package.json").exists():
        return False
    
    # Look for common static site indicators
    static_indicators = ["index.html", "public/index.html", "src/index.html"]
    if any((repo / f).exists() for f in static_indicators):
        logger.info("Detected static site: HTML files without package.json")
        return True
    
    return False

def classify_stack(repo_path: str) -> dict | str:
    """
    Classify the stack type based on repository analysis
    Priority order: Laravel (with mode) -> other PHP -> static -> react (fallback)
    """
    repo = Path(repo_path)
    
    # Priority 1: Laravel detection with mode preservation
    if (repo / "composer.json").exists() and (repo / "artisan").exists():
        laravel_type = classify_laravel_type(repo)  # api_only | blade_or_inertia_ssr | spa_split
        return {
            "stack_type": "php_laravel",
            "mode": laravel_type,
            "deployment_method": "ecs",
        }
    
    # Priority 1b: Other PHP frameworks
    if is_php_repo(repo):
        php_framework = get_php_framework(repo)
        logger.info(f"Detected non-Laravel PHP application: {php_framework}")
        return "php_api"  # Generic PHP API stack
    
    # Priority 2: Static site detection
    if is_static_site(repo):
        return "static"
    
    # Priority 3: JavaScript frameworks
    pkg = _read_package_json(repo)
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    
    if "react" in deps:
        logger.info("Detected React app (fallback detection)")
        return "react"
    elif "vue" in deps or "@vue/core" in deps:
        logger.info("Detected Vue app (fallback detection)")
        return "vue"
    elif "@angular/core" in deps:
        logger.info("Detected Angular app (fallback detection)")
        return "angular"
    
    # Ultimate fallback - assume React for any package.json project
    if (repo / "package.json").exists():
        logger.info("Unknown JS framework, defaulting to React")
        return "react"
    
    # If no package.json and no static indicators, default to static
    logger.info("No clear indicators, defaulting to static")
    return "static"

def get_stack_reason(repo: Path, stack_type: str) -> str:
    """
    Get a human-readable reason for why this stack was detected
    """
    if stack_type == "static":
        if (repo / "index.html").exists():
            return "index.html found, no package.json"
        elif (repo / "public" / "index.html").exists():
            return "public/index.html found, no package.json"
    
    elif stack_type in ["react", "vue", "angular"]:
        pkg = _read_package_json(repo)
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        
        framework_deps = {
            "react": "react",
            "vue": "vue",
            "angular": "@angular/core"
        }
        
        dep_name = framework_deps.get(stack_type)
        if dep_name and dep_name in deps:
            return f"package.json contains {dep_name}@{deps[dep_name]}"
    
    return f"detected as {stack_type} (fallback)"

def recommend_php_laravel_stack(mode: str) -> dict:
    """Recommend appropriate stack configuration for Laravel based on mode"""
    if mode == "spa_split":
        return {
            "stack_type": "php_laravel",
            "mode": mode,
            "deployment_method": "split",   # front=S3+CF, api=ECS/AppRunner
            "frontend": {"compute": "S3+CloudFront"},
            "api": {"compute": "ECS", "runtime": "php", "framework": "laravel"},
            "description": "Vue SPA on S3/CloudFront + Laravel API on ECS",
        }
    # api_only or blade_or_inertia_ssr → single service
    return {
        "stack_type": "php_laravel",
        "mode": mode,
        "deployment_method": "apprunner",  # Using AppRunner for faster deployment
        "compute": "App Runner",
        "runtime": "php",
        "framework": "laravel",
        "description": "Laravel app on App Runner",
    }
