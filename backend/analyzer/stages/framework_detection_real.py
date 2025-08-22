"""
🎯 Framework Detection Stage - Crash-Proof Laravel Detection with Stack Blueprint Generation
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import re

# Import crash-proof utilities and detectors
from utils.composer import read_composer, composer_packages
from detectors.laravel import detect_laravel
from detectors.react import detect_react
from detectors.nodejs import detect_nodejs, should_skip_static_detection
from analyzer.detectors.php_laravel import is_laravel
from detectors.react import detect_react
from detectors.python import detect_python
from detectors.angular import detect_angular
from detectors.unity import detect_unity
from detectors.mobile import detect_mobile

def classify_static_vs_app(repo_path: Path) -> str:
    """
    Classify repository as static site vs application
    
    Static site criteria:
    - ≥5 HTML files
    - No composer.json (PHP dependency manager)
    - No index.php at root or public/index.php (PHP entrypoint)
    - No PHP files in code directories (app/, src/, routes/, server/, backend/)
    """
    html_files = list(repo_path.rglob("*.html"))
    composer_json = (repo_path / "composer.json").exists()
    index_php = (repo_path / "index.php").exists() or (repo_path / "public" / "index.php").exists()
    
    # Check for PHP files in code directories (not assets)
    code_dirs = {"app", "src", "routes", "server", "backend"}
    php_in_code_dirs = any(
        p.suffix == ".php" and any(part.lower() in code_dirs for part in p.parts)
        for p in repo_path.rglob("*.php")
    )
    
    # Static site: many HTML files, no PHP app structure
    if len(html_files) >= 5 and not composer_json and not index_php and not php_in_code_dirs:
        return "static-site"
    else:
        return "app"
from detectors.python import detect_python

logger = logging.getLogger(__name__)

def run_framework_detection(repo_root: Path) -> dict:
    """🎯 Crash-proof framework detection with proper Node.js/static gating"""
    composer = read_composer(repo_root)
    
    # Read package.json for React/Node.js detection
    package_json = None
    package_path = repo_root / "package.json"
    if package_path.exists():
        try:
            import json
            with open(package_path) as f:
                package_json = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read package.json: {e}")
    
    # Gather file statistics for better detection
    file_stats = {}
    for ext in ['.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.php']:
        files = list(repo_root.glob(f"**/*{ext}"))
        if files:
            file_stats[ext] = len(files)
    
    candidates = []

    def safe_run(detector, name):
        try:
            if name == "react":
                res = detector(repo_root, package_json)
            elif name == "angular":
                res = detector(repo_root, package_json)
            elif name in ["nodejs", "unity", "mobile"]:
                res = detector(repo_root, file_stats)
            elif name == "python":
                res = detector(repo_root, file_stats, None)  # Pass None for dependencies for now
            else:
                res = detector(repo_root, composer)
            if res: 
                if isinstance(res, list):
                    candidates.extend(res)
                else:
                    candidates.append(res)
        except Exception as e:
            logger.warning("Detector %s failed: %s", name, e)

    # Run detectors in priority order - mobile detection early to avoid misclassification
    safe_run(detect_mobile, "mobile")     # Mobile apps (Android, iOS, React Native, Flutter)
    safe_run(detect_laravel, "laravel")
    safe_run(detect_python, "python")    # Python frameworks (Django, Flask, FastAPI)
    safe_run(detect_unity, "unity")      # Unity game engine projects
    safe_run(detect_angular, "angular")  # Angular applications
    safe_run(detect_nodejs, "nodejs")    # This includes React variants
    safe_run(detect_react, "react")      # Fallback React detection

    if not candidates:
        # Heuristic: the files alone look like Laravel
        laravel_hints = any((repo_root / p).exists() for p in [
            "artisan", "bootstrap/app.php", "public/index.php", "routes/web.php", "routes/api.php"
        ])
        if laravel_hints:
            candidates.append({"framework":"laravel","runtime":"php","confidence":0.72,"evidence":["filesystem-heuristic"]})
        
        # Heuristic: Static HTML/CSS/JS site detection - ONLY if not Node.js/complex project
        if not should_skip_static_detection(repo_root, file_stats) and not laravel_hints:
            # Use proper static vs app classification
            classification = classify_static_vs_app(repo_root)
            if classification == "static-site":
                html_files = list(repo_root.rglob("*.html"))
                css_files = list(repo_root.rglob("*.css"))
                js_files = list(repo_root.rglob("*.js"))
                
                static_hints = []
                if len(html_files) >= 5:
                    static_hints.append(f"{len(html_files)}_html_files")
                if css_files:
                    static_hints.append(f"{len(css_files)}_css_files") 
                if js_files:
                    static_hints.append(f"{len(js_files)}_js_files")
                
                candidates.append({
                    "framework": "static-basic", 
                    "runtime": "none",
                    "confidence": 0.9,
                    "evidence": static_hints + [
                        f"{len(html_files)} HTML files",
                        f"{len(css_files)} CSS files", 
                        f"{len(js_files)} JS files",
                        "No PHP application structure"
                    ],
                    "intent": "webapp",
                    "is_deployable": True
                })

    return max(candidates, key=lambda c: c.get("confidence", 0.0)) if candidates else {
        "framework":"unknown","runtime":"unknown","confidence":0.0,"evidence":[]
    }

def build_blueprint(repo_root, detection: dict) -> dict:
    """🏗️ Build deployment blueprint - emit Laravel or static blueprint when detected"""
    fw = (detection.get("framework") or "").lower()

    if fw == "laravel":
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "monolith-webapp",
            "services": [{
                "id": "webapp",
                "role": "laravel-app",
                "framework": {"name":"laravel","variant":"php","confidence":detection.get("confidence",0.85)},
                "build": {
                    "tool": "composer+node",
                    "commands": [
                        "composer install --no-dev --prefer-dist --optimize-autoloader",
                        "php artisan config:cache && php artisan route:cache && php artisan view:cache",
                        "npm ci && npm run prod"
                    ]
                },
                "runtime": {
                    "kind": "ecs-fargate",
                    "containers": [
                        {"name":"php-fpm","image":"php:8.2-fpm","port":9000},
                        {"name":"nginx","image":"nginx:stable","port":80,"depends_on":["php-fpm"]}
                    ]
                },
                "health_path": "/",
                "env_example": ".env.example"
            }],
            "shared_resources": {
                "database": {"type":"rds-mysql"},
                "cache": {"type":"elasticache-redis"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id":"aws.ecs.fargate.php.laravel.v1",
                "confidence": max(0.85, detection.get("confidence", 0.85)),
                "deployment_recipe_id":"aws.ecs.fargate.php.laravel.v1"
            }
        }
    
    elif fw == "django":
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "monolith-webapp",
            "services": [{
                "id": "django-app",
                "role": "backend-api",
                "framework": {"name":"django","variant":"python","confidence":detection.get("confidence",0.9)},
                "build": {
                    "tool": "python",
                    "commands": [
                        "pip install -r requirements.txt",
                        "python manage.py collectstatic --noinput",
                        "python manage.py migrate"
                    ],
                    "artifact": "."
                },
                "runtime": {
                    "kind": "lightsail",
                    "containers": [
                        {"name":"django","image":"python:3.11","port":8000,"command":"gunicorn --bind 0.0.0.0:8000 wsgi:application"}
                    ]
                },
                "health_path": "/health/",
                "env_example": ".env.example"
            }],
            "shared_resources": {
                "database": {"type":"lightsail-postgresql"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id": "aws.lightsail.python.django.v1",
                "confidence": detection.get("confidence", 0.9),
                "deployment_recipe_id": "aws.lightsail.python.django.v1"
            }
        }
    
    elif fw == "flask":
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "backend-api",
            "services": [{
                "id": "flask-api",
                "role": "backend-api",
                "framework": {"name":"flask","variant":"python","confidence":detection.get("confidence",0.85)},
                "build": {
                    "tool": "python",
                    "commands": [
                        "pip install -r requirements.txt"
                    ],
                    "artifact": "."
                },
                "runtime": {
                    "kind": "lightsail",
                    "containers": [{"name":"flask","image":"python:3.11","port":5000,"command":"gunicorn --bind 0.0.0.0:5000 app:app"}]
                },
                "health_path": "/health"
            }],
            "shared_resources": {
                "database": {"type":"lightsail-postgresql"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id": "aws.lightsail.python.flask.v1",
                "confidence": detection.get("confidence", 0.85),
                "deployment_recipe_id": "aws.lightsail.python.flask.v1"
            }
        }
        
    elif fw == "fastapi":
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "backend-api",
            "services": [{
                "id": "fastapi-api",
                "role": "backend-api",
                "framework": {"name":"fastapi","variant":"python","confidence":detection.get("confidence",0.9)},
                "build": {
                    "tool": "python",
                    "commands": [
                        "pip install -r requirements.txt"
                    ],
                    "artifact": "."
                },
                "runtime": {
                    "kind": "lightsail",
                    "containers": [{"name":"fastapi","image":"python:3.11","port":8000,"command":"uvicorn main:app --host 0.0.0.0 --port 8000"}]
                },
                "health_path": "/health"
            }],
            "shared_resources": {
                "database": {"type":"lightsail-postgresql"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id": "aws.lightsail.python.fastapi.v1",
                "confidence": detection.get("confidence", 0.9),
                "deployment_recipe_id": "aws.lightsail.python.fastapi.v1"
            }
        }

    elif fw in ["nodejs-monorepo", "nodejs"]:
        # Non-deployable Node.js projects (monorepos, libraries, tooling)
        intent = detection.get("intent", "unknown")
        is_deployable = detection.get("is_deployable", False)
        
        if not is_deployable or intent in ["library", "tooling"]:
            return {
                "stack_blueprint_version": "1.0.0",
                "project_kind": "library" if intent == "tooling" else "monorepo",
                "services": [],
                "shared_resources": {},
                "deployment_targets": {},
                "final_recommendation": {
                    "stack_id": None,
                    "confidence": detection.get("confidence", 0.8),
                    "deployment_recipe_id": None,
                    "reason": f"This is a {intent} repository, not a deployable application",
                    "verdict": f"Not a deployable app ({intent} repo)"
                }
            }
        else:
            # Generic Node.js app
            build_commands = detection.get("build_commands", ["npm ci", "npm start"])
            return {
                "stack_blueprint_version": "1.0.0", 
                "project_kind": "nodejs-app",
                "services": [{
                    "id": "nodejs-app",
                    "role": "backend-api",
                    "framework": {"name":"nodejs","variant":"generic","confidence":detection.get("confidence",0.7)},
                    "build": {
                        "tool": "npm",
                        "commands": build_commands,
                        "artifact": "."
                    },
                    "runtime": {
                        "kind": "ecs-fargate",
                        "containers": [{"name":"nodejs","image":"node:18","port":3000}]
                    },
                    "health_path": "/health"
                }],
                "shared_resources": {},
                "deployment_targets": {"preferred":"aws"},
                "final_recommendation": {
                    "stack_id": "aws.ecs.fargate.nodejs.v1",
                    "confidence": detection.get("confidence", 0.7),
                    "deployment_recipe_id": "aws.ecs.fargate.nodejs.v1"
                }
            }
    
    elif fw in ["create-react-app", "react-vite", "react-custom", "nextjs"]:
        # Deployable React/Next.js apps
        build_commands = detection.get("build_commands", ["npm ci", "npm run build"])
        output_dir = detection.get("output_dir", "build")
        
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "frontend-app",
            "services": [{
                "id": f"{fw}-app",
                "role": "frontend-spa", 
                "framework": {"name":fw,"variant":"nodejs","confidence":detection.get("confidence",0.9)},
                "build": {
                    "tool": "npm",
                    "commands": build_commands,
                    "artifact": output_dir
                },
                "runtime": {
                    "kind": "s3+cloudfront",
                    "static_hosting": True,
                    "spa_routing": True if fw != "nextjs" else False
                },
                "health_path": "/"
            }],
            "shared_resources": {
                "cdn": {"type":"cloudfront"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id": f"aws.s3.cloudfront.{fw}.v1",
                "confidence": detection.get("confidence", 0.9),
                "deployment_recipe_id": f"aws.s3.cloudfront.{fw}.v1"
            }
        }
    
    elif fw == "react":
        # Determine build commands based on variant
        variant = detection.get("variant", "unknown")
        build_tool = detection.get("build_tool", "unknown")
        
        if variant == "vite":
            build_commands = ["npm ci", "npm run build"]
            build_output = "dist"
        elif variant == "create-react-app":
            build_commands = ["npm ci", "npm run build"] 
            build_output = "build"
        elif variant == "nextjs":
            build_commands = ["npm ci", "npm run build"]
            build_output = ".next"
        else:
            build_commands = ["npm ci", "npm run build"]
            build_output = "build"
            
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "frontend-app", 
            "services": [{
                "id": "react-app",
                "role": "frontend-spa",
                "framework": {"name":"react","variant":variant,"confidence":detection.get("confidence",0.85)},
                "build": {
                    "tool": build_tool,
                    "commands": build_commands,
                    "artifact": build_output
                },
                "runtime": {
                    "kind": "s3+cloudfront",
                    "static_hosting": True,
                    "spa_routing": True
                },
                "health_path": "/",
                "env_example": ".env.example" if (Path(".env.example")).exists() else None
            }],
            "shared_resources": {
                "cdn": {"type":"cloudfront"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id": f"aws.s3.cloudfront.react.{variant}.v1",
                "confidence": detection.get("confidence", 0.85),
                "deployment_recipe_id": f"aws.s3.cloudfront.react.{variant}.v1"
            }
        }
    
    elif fw == "angular":
        # Determine Angular variant
        variant = detection.get("variant", "angular")
        version = detection.get("version", "unknown")
        
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "frontend-spa",
            "services": [{
                "id": "angular-app",
                "role": "frontend-spa",
                "framework": {"name":"angular","variant":variant,"confidence":detection.get("confidence",0.85)},
                "build": {
                    "tool": "angular-cli",
                    "commands": ["npm ci", "ng build"],
                    "artifact": "dist"
                },
                "runtime": {
                    "kind": "s3+cloudfront",
                    "static_hosting": True,
                    "spa_routing": True
                },
                "health_path": "/",
                "version": version
            }],
            "shared_resources": {
                "cdn": {"type":"cloudfront"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id": f"aws.s3.cloudfront.angular.{version}.v1",
                "confidence": detection.get("confidence", 0.85),
                "deployment_recipe_id": f"aws.s3.cloudfront.angular.{version}.v1"
            }
        }
    
    elif fw == "static-basic":
        return {
            "stack_blueprint_version": "1.0.0", 
            "project_kind": "static-website",
            "services": [{
                "id": "static-site",
                "role": "web-frontend",
                "framework": {"name":"static","variant":"basic","confidence":detection.get("confidence",0.8)},
                "build": {
                    "tool": "none",
                    "commands": [],
                    "artifact": "."
                },
                "runtime": {
                    "kind": "s3+cloudfront",
                    "static_hosting": True
                },
                "health_path": "/index.html"
            }],
            "shared_resources": {},
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id":"aws.s3.cloudfront.static.v1",
                "confidence": detection.get("confidence", 0.8),
                "deployment_recipe_id":"aws.s3.cloudfront.static.v1"
            }
        }
    
    elif fw == "unity":
        # Unity project with WebGL deployment
        unity_version = detection.get("unity_version", "unknown")
        networking_backend = detection.get("networking_backend")
        webgl_present = detection.get("webgl_build_present", False)
        
        build_commands = [
            "unity -batchmode -nographics -quit",
            "-projectPath \"$PROJECT\"", 
            "-executeMethod BuildScript.BuildWebGL",
            "-logFile -"
        ] if not webgl_present else []
        
        deployment_recipe = detection.get("deployment_recipe", "aws.s3.cloudfront.unity.webgl.v1")
        
        service_notes = []
        if networking_backend == "coherence":
            service_notes.append("Multiplayer backend provided by Coherence")
        if not webgl_present:
            service_notes.append("Requires WebGL build for deployment")
            
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "game-project",
            "services": [{
                "id": "unity-game",
                "role": "game-client",
                "framework": {"name":"unity","variant":"webgl","confidence":detection.get("confidence",0.9)},
                "build": {
                    "tool": "unity-editor",
                    "commands": build_commands,
                    "artifact": "Build/WebGL" if not webgl_present else "."
                },
                "runtime": {
                    "kind": "s3+cloudfront",
                    "static_hosting": True,
                    "webgl_game": True
                },
                "health_path": "/",
                "unity_version": unity_version,
                "networking_backend": networking_backend,
                "notes": service_notes
            }],
            "shared_resources": {
                "cdn": {"type":"cloudfront","webgl_optimized": True},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id": deployment_recipe,
                "confidence": detection.get("confidence", 0.9),
                "deployment_recipe_id": deployment_recipe
            }
        }
    
    elif fw in ["android", "ios", "react-native", "flutter", "xamarin"]:
        # Mobile applications - not web deployable
        language = detection.get("language", "unknown")
        framework_type = detection.get("framework_type", "mobile")
        distribution_method = detection.get("distribution_method", "app-stores")
        
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "mobile-app",
            "services": [{
                "id": f"{fw}-app",
                "role": "mobile-client",
                "framework": {"name": fw, "variant": framework_type, "confidence": detection.get("confidence", 0.8)},
                "build": {
                    "tool": detection.get("build_tool", "gradle" if fw == "android" else "xcode"),
                    "commands": [],  # Mobile builds require platform-specific tooling
                    "artifact": "app-bundle"
                },
                "runtime": {
                    "kind": "mobile-device",
                    "platform": fw,
                    "distribution": distribution_method
                },
                "language": language
            }],
            "shared_resources": {},
            "deployment_targets": {"preferred": "mobile-stores"},
            "final_recommendation": {
                "stack_id": None,
                "confidence": detection.get("confidence", 0.8),
                "deployment_recipe_id": None,
                "reason": f"Mobile application - distribute via {distribution_method}",
                "verdict": f"📱 {fw.title()} app → Not web deployable, use mobile distribution"
            }
        }

    # 🎯 DYNAMIC FALLBACK - No hardcoded recommendations
    return {
        "stack_blueprint_version":"1.0.0",
        "project_kind":"unknown",
        "services":[],
        "shared_resources":{"object_storage":None,"cdn":None,"auth":None},
        "deployment_targets":{"preferred":"aws"},
        "final_recommendation":{
            "stack_id": None,
            "confidence": 0.1,
            "deployment_recipe_id": None,
            "reason": "Framework not recognized - manual configuration required",
            "verdict": "❓ Unknown project type - consider manual setup"
        }
    }

class FrameworkDetectionStage:
    """🔍 Crash-Proof Framework Detection with Laravel Blueprint Generation"""

    def _classify_static_vs_app(self, repo_path: Path) -> str:
        """
        Surgical classification to distinguish static templates from dynamic applications
        Returns: 'static-site' or 'dynamic-app'
        """
        # Check for clear dynamic app indicators first
        if (repo_path / "composer.json").exists():
            return "dynamic-app"
        if (repo_path / "index.php").exists() or (repo_path / "public" / "index.php").exists():
            return "dynamic-app"
        if (repo_path / "app").is_dir() and (repo_path / "bootstrap").is_dir():
            return "dynamic-app"
        
        # Count HTML files vs total code files
        html_files = list(repo_path.glob("**/*.html"))
        css_files = list(repo_path.glob("**/*.css")) 
        js_files = list(repo_path.glob("**/*.js"))
        php_files = list(repo_path.glob("**/*.php"))
        
        # Filter out minified/vendor files for accurate counting
        code_js_files = [f for f in js_files if not ('.min.js' in str(f) or 'vendor' in str(f) or 'node_modules' in str(f))]
        
        # Static site indicators: lots of HTML, CSS, minimal server-side code
        total_frontend_files = len(html_files) + len(css_files) + len(code_js_files)
        total_backend_files = len(php_files)
        
        # If predominantly HTML/CSS/JS with minimal server-side files = static site
        if total_frontend_files > 5 and total_backend_files <= 2:
            return "static-site"
        elif len(html_files) > 0 and total_backend_files == 0:
            return "static-site"  
        else:
            return "dynamic-app"

    async def analyze(self, context) -> None:
        """🔍 Main analysis method with comprehensive error handling"""
        try:
            await self._safe_analyze(context)
        except Exception as e:
            logger.error(f"❌ Framework detection failed: {e}")
            # Ensure intelligence_profile is valid even on total failure
            if not hasattr(context, "intelligence_profile") or not isinstance(getattr(context, "intelligence_profile"), dict):
                context.intelligence_profile = {}
            
            context.intelligence_profile["frameworks"] = []
            context.intelligence_profile["stack_classification"] = {"type": "unknown", "confidence": 0.1, "error": str(e)}
            context.intelligence_profile["project_kind"] = "app"
            
    async def _safe_analyze(self, context) -> None:
        """🔍 Safe analysis implementation"""
        repo_path = getattr(context, "repo_path", None)
        if not repo_path or not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            if not hasattr(context, "intelligence_profile") or not isinstance(getattr(context, "intelligence_profile"), dict):
                context.intelligence_profile = {}
            context.intelligence_profile["frameworks"] = []
            context.intelligence_profile["stack_classification"] = {"type": "unknown", "confidence": 0.1}
            context.intelligence_profile["project_kind"] = "app"
            return

        logger.info(f"🔍 Analyzing frameworks in: {repo_path}")

        # 🛡️ Defensive: Ensure intelligence_profile is always a dict
        if not hasattr(context, "intelligence_profile") or context.intelligence_profile is None:
            context.intelligence_profile = {}
        elif not isinstance(context.intelligence_profile, dict):
            context.intelligence_profile = {}

        # 🎯 STEP 1: Run crash-proof framework detection
        detection = run_framework_detection(repo_path)
        
        # 🎯 STEP 2: Create frameworks list for compatibility
        frameworks = []
        if detection["framework"] != "unknown":
            # Determine framework type and deployment target correctly
            runtime = detection["runtime"]
            framework_name = detection["framework"]
            
            # Backend frameworks (server-side)
            backend_frameworks = ["flask", "django", "fastapi", "laravel", "nodejs", "express"]
            is_backend = (
                runtime in ["php", "python", "node"] or 
                framework_name in backend_frameworks
            )
            
            # Deployment target based on framework type
            if framework_name == "laravel":
                deployment_target = "ecs-fargate"
            elif framework_name in ["flask", "django", "fastapi"]:
                deployment_target = "lightsail"
            elif framework_name in ["nodejs", "express"]:
                deployment_target = "lightsail"
            else:
                deployment_target = "s3+cloudfront"
            
            frameworks.append({
                "name": detection["framework"],
                "confidence": detection["confidence"],
                "evidence": detection["evidence"],
                "framework_type": "backend" if is_backend else "frontend",
                "language": detection["runtime"],
                "requires_server": is_backend,
                "deployment_target": deployment_target
            })

        # 🎯 STEP 3: Dynamic stack classification - scales for all frameworks
        framework = detection["framework"]
        intent = detection.get("intent", "app")
        is_deployable = detection.get("is_deployable", True)
        
        # Dynamic stack classification mapping
        stack_configs = {
            "laravel": {
                "type": "php-laravel", 
                "rendering_mode": "server",
                "required_runtimes": ["php-fpm"],
            },
            "django": {
                "type": "python-django",
                "rendering_mode": "server",
                "required_runtimes": ["python"],
            },
            "flask": {
                "type": "python-flask",
                "rendering_mode": "server", 
                "required_runtimes": ["python"],
            },
            "fastapi": {
                "type": "python-fastapi",
                "rendering_mode": "server",
                "required_runtimes": ["python"],
            },
            "nodejs-monorepo": {
                "type": "node-monorepo",
                "rendering_mode": "n/a", 
                "required_runtimes": [],
            },
            "nodejs": {
                "type": "node-server",
                "rendering_mode": "server",
                "required_runtimes": ["nodejs"],
            },
            "create-react-app": {
                "type": "react-spa",
                "rendering_mode": "static",
                "required_runtimes": [],
            },
            "react-vite": {
                "type": "react-spa", 
                "rendering_mode": "static",
                "required_runtimes": [],
            },
            "nextjs": {
                "type": "nextjs-fullstack",
                "rendering_mode": "hybrid",
                "required_runtimes": ["nodejs"],
            },
            "react": {
                "type": "react-spa",
                "rendering_mode": "static", 
                "required_runtimes": [],
            },
            "angular": {
                "type": "angular-spa",
                "rendering_mode": "static",
                "required_runtimes": [],
            },
            "static-basic": {
                "type": "static-site",
                "rendering_mode": "static",
                "required_runtimes": [],
            },
            "unity": {
                "type": "unity-project",
                "rendering_mode": "client",
                "required_runtimes": [],
            },
            "android": {
                "type": "mobile-app",
                "rendering_mode": "native-mobile",
                "required_runtimes": [],
            },
            "ios": {
                "type": "mobile-app", 
                "rendering_mode": "native-mobile",
                "required_runtimes": [],
            },
            "react-native": {
                "type": "mobile-app",
                "rendering_mode": "hybrid-mobile",
                "required_runtimes": [],
            },
            "flutter": {
                "type": "mobile-app",
                "rendering_mode": "cross-platform",
                "required_runtimes": [],
            },
            "xamarin": {
                "type": "mobile-app",
                "rendering_mode": "cross-platform", 
                "required_runtimes": [],
            }
        }
        
        # Get configuration or generate defaults
        if framework in stack_configs:
            stack_config = stack_configs[framework]
        else:
            # Check if this is a static site vs dynamic app using surgical classification
            static_classification = self._classify_static_vs_app(context.repo_path)
            
            # Dynamic defaults for unknown frameworks
            if intent in ["library", "tooling"]:
                stack_config = {
                    "type": f"{framework}-library",
                    "rendering_mode": "n/a",
                    "required_runtimes": [],
                }
            elif static_classification == "static-site":
                stack_config = {
                    "type": "static-site",
                    "rendering_mode": "static",
                    "required_runtimes": [],
                }
            elif "node" in framework.lower() or "react" in framework.lower() or "js" in framework.lower():
                stack_config = {
                    "type": "javascript-app", 
                    "rendering_mode": "static",
                    "required_runtimes": [],
                }
            elif detection.get("runtime") == "php":
                stack_config = {
                    "type": "php-app",
                    "rendering_mode": "server", 
                    "required_runtimes": ["php-fpm"],
                }
            elif detection.get("runtime") == "python" or "python" in framework.lower():
                stack_config = {
                    "type": "python-app",
                    "rendering_mode": "server",
                    "required_runtimes": ["python"],
                }
            else:
                # Use static classification result instead of generic "unknown-app"
                if static_classification == "static-site":
                    stack_config = {
                        "type": "static-site",
                        "rendering_mode": "static",
                        "required_runtimes": [],
                    }
                else:
                    stack_config = {
                        "type": "unknown-app",
                        "rendering_mode": "static",
                        "required_runtimes": [],
                    }
        
        # Override for non-deployable projects
        if not is_deployable or intent in ["library", "tooling"]:
            stack_config["rendering_mode"] = "n/a"
            stack_config["required_runtimes"] = []
        
        # Build final classification
        stack_classification = {
            "type": stack_config["type"],
            "confidence": detection["confidence"],
            "rendering_mode": stack_config["rendering_mode"],
            "required_runtimes": stack_config["required_runtimes"],
            "evidence": detection.get("evidence", [])
        }

        # 🎯 STEP 4: Build stack blueprint
        blueprint = build_blueprint(repo_path, detection)

        # 🎯 STEP 5: Set all context properties
        context.intelligence_profile["frameworks"] = frameworks
        context.intelligence_profile["stack_classification"] = stack_classification
        # Use project_kind from blueprint if available, otherwise default to "app"
        context.intelligence_profile["project_kind"] = blueprint.get("project_kind", "app")
        context.stack_blueprint = blueprint
        
        # Set detected framework for legacy compatibility
        context.detected_framework = detection["framework"]
        context.confidence = detection["confidence"]
        
        # Set final recommendation
        context.intelligence_profile["final_recommendation"] = {
            "stack_id": blueprint["final_recommendation"]["stack_id"],
            "blueprint_id": blueprint["final_recommendation"]["deployment_recipe_id"], 
            "confidence": blueprint["final_recommendation"]["confidence"]
        }
        
        # 🎯 DYNAMIC DEPLOYMENT ANALYSIS - Scales for thousands of users and frameworks
        framework = detection.get("framework", "unknown")
        intent = detection.get("intent", "unknown")
        is_deployable = detection.get("is_deployable", True)
        confidence = detection.get("confidence", 0.0)
        
        # Define deployment characteristics dynamically - easily extensible
        deployment_configs = {
            "laravel": {
                "ready": True, "complexity": "medium", 
                "cost": "$80-200 for Laravel ECS Fargate + RDS + ElastiCache",
                "verdict": "✅ Deployable: Laravel → AWS ECS Fargate (Nginx + PHP-FPM) + RDS MySQL"
            },
            "django": {
                "ready": True, "complexity": "medium",
                "cost": "$35/month for Django LightSail + PostgreSQL database",
                "verdict": "✅ Deployable: Django → AWS LightSail (Gunicorn) + LightSail PostgreSQL"
            },
            "flask": {
                "ready": True, "complexity": "low",
                "cost": "$10-25/month for Flask LightSail + optional database",
                "verdict": "✅ Deployable: Flask → AWS LightSail (Gunicorn) + optional database"
            },
            "fastapi": {
                "ready": True, "complexity": "low",
                "cost": "$10-25/month for FastAPI LightSail + optional database",
                "verdict": "✅ Deployable: FastAPI → AWS LightSail (Uvicorn) + optional database"
            },
            "nodejs-monorepo": {
                "ready": False, "complexity": "n/a", "cost": "n/a",
                "verdict": "📦 Not a deployable app (Node.js monorepo for libraries/tooling)"
            },
            "nodejs": {
                "ready": True, "complexity": "medium", 
                "cost": "$50-150 for Node.js ECS Fargate + optional database",
                "verdict": "✅ Deployable: Node.js → AWS ECS Fargate + optional database"
            },
            "create-react-app": {
                "ready": True, "complexity": "low",
                "cost": "$10-30/month for S3 + CloudFront", 
                "verdict": "✅ Deployable: Create React App → AWS S3 + CloudFront (static hosting)"
            },
            "react-vite": {
                "ready": True, "complexity": "low",
                "cost": "$10-30/month for S3 + CloudFront",
                "verdict": "✅ Deployable: React Vite → AWS S3 + CloudFront (static hosting)"
            },
            "nextjs": {
                "ready": True, "complexity": "medium",
                "cost": "$50-150 for Next.js ECS Fargate or Vercel", 
                "verdict": "✅ Deployable: Next.js → AWS ECS Fargate or Vercel"
            },
            "react": {
                "ready": True, "complexity": "low",
                "cost": "$10-30/month for S3 + CloudFront",
                "verdict": "✅ Deployable: React SPA → AWS S3 + CloudFront (static hosting)"
            },
            "static-basic": {
                "ready": True, "complexity": "low", 
                "cost": "$10-30/month for S3 + CloudFront",
                "verdict": "✅ Deployable: Static website → AWS S3 + CloudFront"
            },
            "unity": {
                "ready": True, "complexity": "low",
                "cost": "$1-10/month for WebGL S3 + CloudFront",
                "verdict": "✅ Deployable: Unity WebGL → AWS S3 + CloudFront (game hosting)"
            },
            "android": {
                "ready": False, "complexity": "n/a", "cost": "n/a",
                "verdict": "📱 Mobile app → Distribute via Google Play Store (not web deployable)"
            },
            "ios": {
                "ready": False, "complexity": "n/a", "cost": "n/a", 
                "verdict": "📱 Mobile app → Distribute via Apple App Store (not web deployable)"
            },
            "react-native": {
                "ready": False, "complexity": "n/a", "cost": "n/a",
                "verdict": "📱 Mobile app → Distribute via App Stores (not web deployable)"
            },
            "flutter": {
                "ready": False, "complexity": "n/a", "cost": "n/a",
                "verdict": "📱 Mobile app → Distribute via App Stores (not web deployable)"
            },
            "xamarin": {
                "ready": False, "complexity": "n/a", "cost": "n/a",
                "verdict": "📱 Mobile app → Distribute via App Stores (not web deployable)"
            }
        }
        
        # Get config or generate dynamic defaults for unknown frameworks
        if framework in deployment_configs:
            config = deployment_configs[framework].copy()
        else:
            # Dynamic handling for any framework not in our list
            if intent in ["library", "tooling"]:
                config = {
                    "ready": False, "complexity": "n/a", "cost": "n/a",
                    "verdict": f"📦 Not a deployable app ({framework} {intent} repository)"
                }
            elif confidence > 0.7:
                config = {
                    "ready": True, "complexity": "medium",
                    "cost": "$30-100/month (requires custom configuration)",
                    "verdict": f"⚠️ {framework.title()} detected → may require custom deployment setup"
                }
            else:
                config = {
                    "ready": False, "complexity": "unknown",
                    "cost": "$10-30/month (fallback options available)",
                    "verdict": f"❓ {framework.title()} uncertain → consider manual review"
                }
        
        # Override based on specific detection results
        if not is_deployable:
            config["ready"] = False
            if intent == "tooling":
                config["verdict"] = f"📦 Not a deployable app ({intent} repository) - contains development tools"
            elif intent in ["library", "monorepo"]:
                config["verdict"] = f"📦 Not a deployable app ({framework} {intent} repository)"
        
        # Apply the configuration
        context.intelligence_profile["ready_to_deploy"] = config["ready"]
        context.intelligence_profile["deployment_complexity"] = config["complexity"]
        context.intelligence_profile["estimated_monthly_cost"] = config["cost"]
        context.intelligence_profile["_prose_verdict_line"] = config["verdict"]
        
        logger.info(f"✅ Framework detection complete: framework={detection['framework']}, confidence={detection['confidence']}")
