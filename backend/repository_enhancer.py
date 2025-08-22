"""
Repository Enhancement Service
Clones repositories, analyzes files thoroughly, and generates missing files
"""
import os
import shutil
import tempfile
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import git
import subprocess
from datetime import datetime

# ---- Robust guard loader (module scope) ----
import importlib.util

logger = logging.getLogger(__name__)

def _load_backend_prebuild_guard():
    """Return None since comprehensive Next.js system was removed."""
    return None

_PREBUILD_GUARD = _load_backend_prebuild_guard()

# --- Preflight report system (user-facing) ---
def _detect_provider(repo: Path) -> str:
    """Detect the commerce/API provider used by the project"""
    if (repo / "lib" / "shopify").exists():
        return "shopify"
    if (repo / "lib" / "commerce").exists():
        return "commerce"
    if (repo / "src" / "lib" / "shopify").exists():
        return "shopify"
    if any(repo.rglob("*shopify*")):
        return "shopify"
    if any(repo.rglob("*strapi*")):
        return "strapi"
    if any(repo.rglob("*contentful*")):
        return "contentful"
    return os.getenv("COMMERCE_PROVIDER") or "unknown"

def _required_env_for(provider: str) -> list[str]:
    """Return required environment variables for a given provider"""
    if provider == "shopify":
        return [
            "NEXT_PUBLIC_SHOPIFY_STORE_DOMAIN",
            "NEXT_PUBLIC_SHOPIFY_STOREFRONT_ACCESS_TOKEN",
        ]
    elif provider == "strapi":
        return [
            "NEXT_PUBLIC_STRAPI_URL",
            "STRAPI_API_TOKEN",
        ]
    elif provider == "contentful":
        return [
            "CONTENTFUL_SPACE_ID",
            "CONTENTFUL_ACCESS_TOKEN",
        ]
    return []

def _read_env_files(repo: Path, env_files: list[str]) -> dict:
    """Read environment variables from .env files"""
    out = {}
    for name in env_files:
        p = repo / name
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        key = k.strip()
                        value = v.strip().strip('"').strip("'")
                        if key and value:  # Only count non-empty values
                            out[key] = value
            except Exception as e:
                logger.debug(f"Failed to read {p}: {e}")
    return out

def build_preflight_report(repo: Path, ssr_required: bool) -> dict:
    """Build a preflight report for user-facing deployment guidance"""
    provider = _detect_provider(repo)
    required = _required_env_for(provider)

    # Collect present env from process + .env files
    env_files = [".env", ".env.local", ".env.production", "site/.env", "site/.env.local"]
    file_env = _read_env_files(repo, env_files)
    
    present = set()
    for k in required:
        # Check if env var has a non-empty value in either process env or files
        process_val = os.environ.get(k, "").strip()
        file_val = file_env.get(k, "").strip()
        if process_val or file_val:
            present.add(k)
    
    missing = [k for k in required if k not in present]
    demo_fallback = os.getenv("CFOPS_DEFAULT_LOCAL_PROVIDER") == "1"

    return {
        "provider": provider,
        "ssrRequired": bool(ssr_required),
        "requiredEnv": required,
        "missingEnv": missing,
        "demoFallbackEnabled": demo_fallback,
        "tips": [
            "Add missing keys to .env.local or pass via environment/secrets.",
            "Or set CFOPS_DEFAULT_LOCAL_PROVIDER=1 to use COMMERCE_PROVIDER=local (demo only)."
        ],
        "foundEnvFiles": [f for f in env_files if (repo / f).exists()]
    }

def print_preflight_message(pf: dict):
    """Print user-friendly preflight summary"""
    print("\n🔎 Preflight Summary")
    print("--------------------------------------------------")
    print(f"Provider: {pf['provider']}")
    print(f"SSR Required: {pf['ssrRequired']}")
    if pf["requiredEnv"]:
        print(f"Required Env: {', '.join(pf['requiredEnv'])}")
    if pf["foundEnvFiles"]:
        print(f"Found Env Files: {', '.join(pf['foundEnvFiles'])}")
    if pf["missingEnv"]:
        print(f"❗ Missing Env: {', '.join(pf['missingEnv'])}")
        if not pf["demoFallbackEnabled"]:
            print("👉 Fix: add these to .env.local or environment,")
            print("   or set CFOPS_DEFAULT_LOCAL_PROVIDER=1 for demo mode.")
        else:
            print("👍 Demo fallback enabled - deployment will continue")
    else:
        print("✅ All provider env present.")
    print("--------------------------------------------------\n")

def _get_primary_language(file_types: Dict[str, int]) -> str:
    """Determine primary language from file types"""
    language_map = {
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.py': 'Python',
        '.php': 'PHP',
        '.html': 'HTML',
        '.css': 'CSS',
        '.vue': 'Vue',
        '.go': 'Go',
        '.rs': 'Rust',
        '.java': 'Java'
    }
    
    max_count = 0
    primary_language = 'Unknown'
    
    for ext, count in file_types.items():
        if ext in language_map and count > max_count:
            max_count = count
            primary_language = language_map[ext]
    
    return primary_language

class RepositoryEnhancer:
    """
    Comprehensive repository analysis and enhancement service
    """
    
    def __init__(self):
        self.framework_templates = {
            "react": {
                "required_files": ["package.json", "public/index.html", "src/index.js"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "build",
                "entry_point": "src/index.js"
            },
            "vue": {
                "required_files": ["package.json", "public/index.html", "src/main.js"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "dist",
                "entry_point": "src/main.js"
            },
            "angular": {
                "required_files": ["package.json", "angular.json", "src/main.ts"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "dist",
                "entry_point": "src/main.ts"
            },
            "nextjs": {
                "required_files": ["package.json", "next.config.js"],
                "build_commands": ["npm install", "npm run build", "npm run export"],
                "build_output": "out",
                "entry_point": "pages/index.js"
            },
            "nextjs_turborepo": {
                "required_files": ["package.json", "turbo.json"],
                "build_commands": ["pnpm install", "pnpm run build"],
                "build_output": "apps/*/dist,apps/*/out,packages/*/dist",
                "entry_point": "apps/*/src/index.js",
                "package_manager": "pnpm",
                "monorepo": True,
                "build_system": "turborepo"
            },
            "laravel": {
                "required_files": ["artisan", "composer.json", "bootstrap/app.php", "public/index.php"],
                "build_commands": ["composer install --no-dev --prefer-dist --no-interaction", "php artisan key:generate --force", "php artisan config:cache", "php artisan route:cache", "php artisan view:cache"],
                "build_output": "public",
                "entry_point": "public/index.php",
                "runtime": "php",
                "php_version": ">=7.2"
            },
            "static": {
                "required_files": ["index.html"],
                "build_commands": [],
                "build_output": ".",
                "entry_point": "index.html"
            }
        }

    async def clone_and_enhance_repository(self, github_url: str, deployment_id: str) -> Dict[str, Any]:
        """
        Clone repository and perform comprehensive enhancement
        """
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=f"repo_{deployment_id}_")
            logger.info(f"Cloning repository {github_url} to {temp_dir}")
            
            # Clone repository
            repo = git.Repo.clone_from(github_url, temp_dir)
            logger.info(f"Repository cloned successfully")
            
            # Note: Pre-build guard system removed (comprehensive Next.js system cleanup)
            logger.info(f"🔎 [enhancer] processing repository: {temp_dir}")
            
            # DEBUG: List all files in repository clone directory
            all_repo_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    all_repo_files.append(rel_path)
            
            logger.info(f"📊 REPO CLONE ANALYSIS: Found {len(all_repo_files)} files in repository:")
            for i, f in enumerate(all_repo_files[:15], 1):  # Show first 15 files
                logger.info(f"   {i}. {f}")
            if len(all_repo_files) > 15:
                logger.info(f"   ... and {len(all_repo_files) - 15} more files")
            logger.info(f"📂 Repository location: {temp_dir}")
            
            # Check for key React files
            key_files = ['package.json', 'src/App.js', 'src/index.js', 'public/index.html', 'src/App.tsx']
            found_key_files = []
            for key_file in key_files:
                if os.path.exists(os.path.join(temp_dir, key_file)):
                    found_key_files.append(key_file)
            logger.info(f"🔑 Key React files found: {found_key_files}")
            
            # Note: Pre-build guard system removed (comprehensive Next.js system cleanup)
            logger.info(f"🔎 [backend] processing backend clone: {temp_dir}")
            
            # --- PREFLIGHT REPORT: Analyze provider dependencies before build ---
            logger.info("🔎 Building preflight report...")
            preflight = build_preflight_report(Path(temp_dir), ssr_required=True)  # Assume SSR for now
            
            # Create user-friendly preflight message
            preflight_msg = f"""
🔎 Preflight Summary
--------------------------------------------------
Provider: {preflight['provider']}
SSR Required: {preflight['ssrRequired']}"""
            
            if preflight["requiredEnv"]:
                preflight_msg += f"\nRequired Env: {', '.join(preflight['requiredEnv'])}"
            if preflight["foundEnvFiles"]:
                preflight_msg += f"\nFound Env Files: {', '.join(preflight['foundEnvFiles'])}"
            if preflight["missingEnv"]:
                preflight_msg += f"\n❗ Missing Env: {', '.join(preflight['missingEnv'])}"
                if not preflight["demoFallbackEnabled"]:
                    preflight_msg += "\n👉 Fix: add these to .env.local or environment,"
                    preflight_msg += "\n   or set CFOPS_DEFAULT_LOCAL_PROVIDER=1 for demo mode."
                else:
                    preflight_msg += "\n👍 Demo fallback enabled - deployment will continue"
            else:
                preflight_msg += "\n✅ All provider env present."
            
            preflight_msg += "\n--------------------------------------------------"
            
            # Check if we should fail fast for missing provider env
            if preflight["missingEnv"] and not preflight["demoFallbackEnabled"]:
                missing_str = ", ".join(preflight["missingEnv"])
                user_message = (
                    f"Provider env missing: {missing_str}. "
                    f"Add them to .env.local or environment, or set CFOPS_DEFAULT_LOCAL_PROVIDER=1 for demo mode."
                )
                logger.error(f"❌ {user_message}")
                return {
                    "success": False,
                    "error": "MISSING_PROVIDER_ENV",
                    "userMessage": preflight_msg + f"\n\n❌ {user_message}",
                    "preflight": preflight,
                    "repository_path": temp_dir
                }
            else:
                # Success case - include preflight message for info
                logger.info("✅ Preflight check passed - proceeding with analysis")
                preflight["userMessage"] = preflight_msg
                print(f"🐛 BACKEND DEBUG: Set preflight userMessage length: {len(preflight_msg)}")
                logger.info(f"🐛 DEBUG: Set preflight userMessage length: {len(preflight_msg)}")
            
            # Perform deep analysis
            analysis = await self._deep_file_analysis(temp_dir)
            
            # Detect framework
            framework_info = await self._detect_framework(temp_dir, analysis)
            
            # Generate missing files
            enhancement_result = await self._enhance_repository(temp_dir, framework_info, analysis)
            
            # Validate final structure
            validation_result = await self._validate_repository_structure(temp_dir, framework_info)
            # Store preflight info for successful response
            preflight_summary_msg = preflight_msg
            
            logger.info(f"🐛 DEBUG: About to return - preflight has userMessage: {'userMessage' in preflight}")
            if 'userMessage' in preflight:
                logger.info(f"🐛 DEBUG: userMessage length: {len(preflight['userMessage'])}")

            return {
                "success": True,
                "local_repo_path": temp_dir,
                "framework": framework_info,
                "analysis": analysis,
                "enhancements": enhancement_result,
                "validation": validation_result,
                "preflight": preflight,
                "userMessage": preflight_summary_msg,  # Direct reference instead of dict lookup
                "build_ready": validation_result["is_build_ready"]
            }
            
        except Exception as e:
            logger.error(f"Repository enhancement failed: {e}")
            if temp_dir and os.path.exists(temp_dir):
                if os.getenv("CFOPS_KEEP_REPO") == "1":
                    logger.info(f"🧷 CFOPS_KEEP_REPO=1 — keeping {temp_dir}")
                else:
                    shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "success": False,
                "error": str(e)
            }

    async def _deep_file_analysis(self, repo_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive file and folder analysis
        """
        analysis = {
            "files": [],
            "directories": [],
            "file_types": {},
            "package_managers": [],
            "config_files": [],
            "source_files": [],
            "static_files": [],
            "documentation": [],
            "total_files": 0,
            "total_size": 0
        }
        
        # Walk through all files and directories
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common build/cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'build', 'dist', '.git', '__pycache__']]
            
            relative_root = os.path.relpath(root, repo_path)
            if relative_root != '.':
                analysis["directories"].append(relative_root)
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Get file stats
                try:
                    stat = os.stat(file_path)
                    file_size = stat.st_size
                    analysis["total_size"] += file_size
                except:
                    file_size = 0
                
                # Categorize file
                file_ext = Path(file).suffix.lower()
                if file_ext not in analysis["file_types"]:
                    analysis["file_types"][file_ext] = 0
                analysis["file_types"][file_ext] += 1
                
                file_info = {
                    "path": relative_path,
                    "name": file,
                    "extension": file_ext,
                    "size": file_size,
                    "directory": relative_root if relative_root != '.' else ""
                }
                
                # Categorize by type
                if file in ['package.json', 'composer.json', 'requirements.txt', 'Pipfile', 'Gemfile', 'go.mod', 'Cargo.toml']:
                    analysis["package_managers"].append(file_info)
                elif file in ['webpack.config.js', 'vite.config.js', 'next.config.js', 'angular.json', 'vue.config.js', 'rollup.config.js']:
                    analysis["config_files"].append(file_info)
                elif file_ext in ['.js', '.jsx', '.ts', '.tsx', '.vue', '.py', '.php', '.go', '.rs', '.java', '.cs']:
                    analysis["source_files"].append(file_info)
                elif file_ext in ['.html', '.css', '.scss', '.sass', '.less', '.jpg', '.png', '.gif', '.svg', '.ico']:
                    analysis["static_files"].append(file_info)
                elif file.lower() in ['readme.md', 'readme.txt', 'readme', 'license', 'license.txt', 'changelog.md']:
                    analysis["documentation"].append(file_info)
                
                analysis["files"].append(file_info)
                analysis["total_files"] += 1
        
        return analysis

    async def _detect_framework(self, repo_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligent framework detection based on file analysis
        """
        framework_scores = {
            "react": 0,
            "vue": 0,
            "angular": 0,
            "nextjs": 0,
            "nextjs_turborepo": 0,
            "laravel": 0,  # 🎯 ADD LARAVEL SUPPORT
            "static": 0
        }
        
        # Check package.json for framework indicators
        package_json_path = os.path.join(repo_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    
                dependencies = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                
                # Score based on dependencies
                if 'react' in dependencies:
                    framework_scores["react"] += 3
                if 'next' in dependencies or '@next/core' in dependencies:
                    framework_scores["nextjs"] += 4
                if 'vue' in dependencies or '@vue/core' in dependencies:
                    framework_scores["vue"] += 3
                if '@angular/core' in dependencies:
                    framework_scores["angular"] += 3
                    
                # Check for Turborepo indicators
                scripts = package_data.get('scripts', {})
                if any('turbo' in str(cmd) for cmd in scripts.values()):
                    framework_scores["nextjs_turborepo"] += 5
                if 'turbo' in dependencies:
                    framework_scores["nextjs_turborepo"] += 4
                if package_data.get('workspaces') and ('turbo' in dependencies or any('turbo' in str(cmd) for cmd in scripts.values())):
                    framework_scores["nextjs_turborepo"] += 6
                    
            except json.JSONDecodeError:
                logger.warning("Could not parse package.json")
        
        # Check for framework-specific files
        for file_info in analysis["files"]:
            file_path = file_info["path"]
            file_name = file_info["name"]
            
            # React indicators
            if "App.js" in file_name or "App.jsx" in file_name or "App.tsx" in file_name:
                framework_scores["react"] += 2
            if "src/index.js" in file_path or "src/index.tsx" in file_path:
                framework_scores["react"] += 2
                
            # Next.js indicators
            if file_path.startswith("pages/") or file_path.startswith("app/"):
                framework_scores["nextjs"] += 2
            if "next.config.js" in file_name:
                framework_scores["nextjs"] += 3
                
            # Turborepo indicators
            if "turbo.json" in file_name:
                framework_scores["nextjs_turborepo"] += 5
            if file_path.startswith("apps/") or file_path.startswith("packages/"):
                framework_scores["nextjs_turborepo"] += 3
            if "pnpm-workspace.yaml" in file_name or "pnpm-lock.yaml" in file_name:
                framework_scores["nextjs_turborepo"] += 4
            if "lerna.json" in file_name:
                framework_scores["nextjs_turborepo"] += 3
                
            # Vue indicators
            if file_info["extension"] == ".vue":
                framework_scores["vue"] += 2
            if "main.js" in file_name and "src/" in file_path:
                framework_scores["vue"] += 1
                
            # Angular indicators
            if "angular.json" in file_name:
                framework_scores["angular"] += 3
            if file_name.endswith(".component.ts") or file_name.endswith(".service.ts"):
                framework_scores["angular"] += 2
                
            # Static site indicators
            if file_name == "index.html" and file_info["directory"] == "":
                framework_scores["static"] += 2
        
        # 🎯 LARAVEL DETECTION LOGIC
        composer_json_path = os.path.join(repo_path, "composer.json")
        laravel_indicators = ["artisan", "bootstrap/app.php", "routes/web.php", "routes/api.php", "public/index.php", "config/app.php"]
        
        # Check for composer.json with Laravel dependencies
        if os.path.exists(composer_json_path):
            try:
                with open(composer_json_path, 'r') as f:
                    composer_data = json.load(f)
                    require = composer_data.get('require', {})
                    if 'laravel/framework' in require:
                        framework_scores["laravel"] += 100  # Ensure Laravel wins definitively when laravel/framework is present
                        logger.info(f"🎨 Laravel framework detected in composer.json - definitive Laravel project")
                    elif any(pkg.startswith('laravel/') or pkg.startswith('illuminate/') for pkg in require.keys()):
                        framework_scores["laravel"] += 50  # Strong boost for other Laravel packages
            except json.JSONDecodeError:
                pass
        
        # Check for Laravel files (including subdirectories like LaraBook/)
        laravel_file_count = 0
        for file_info in analysis["files"]:
            file_path = file_info["path"]
            # Check for Laravel indicators at root or in subdirectories
            if any(indicator in file_path for indicator in laravel_indicators):
                laravel_file_count += 1
        
        if laravel_file_count >= 3:  # At least 3 Laravel indicators
            framework_scores["laravel"] += laravel_file_count * 5  # Increase multiplier for Laravel files
            logger.info(f"🎨 Laravel detection: Found {laravel_file_count} Laravel indicators")
        
        # Check for specific Laravel subdirectory patterns
        for possible_subdir in ['LaraBook', 'laravel', 'app', 'backend']:
            subdir_path = os.path.join(repo_path, possible_subdir)
            if os.path.exists(os.path.join(subdir_path, "artisan")):
                framework_scores["laravel"] += 30  # Very strong indicator for Laravel subdirectory
                logger.info(f"🎨 Laravel detected in subdirectory: {possible_subdir}")
                break
        
        # If no framework detected, default to static
        if all(score == 0 for score in framework_scores.values()):
            framework_scores["static"] = 1
        
        # Determine primary framework
        primary_framework = max(framework_scores, key=framework_scores.get)
        confidence = framework_scores[primary_framework] / sum(framework_scores.values()) if sum(framework_scores.values()) > 0 else 0
        
        return {
            "type": primary_framework,
            "confidence": confidence,
            "scores": framework_scores,
            "config": self.framework_templates.get(primary_framework, self.framework_templates["static"])
        }

    async def _enhance_repository(self, repo_path: str, framework_info: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate missing files and enhance repository structure
        INTELLIGENT REPOSITORY ORGANIZER - Auto-fixes deployment issues
        """
        enhancements = {
            "files_created": [],
            "files_modified": [],
            "directories_created": [],
            "smart_fixes": []
        }
        
        framework_type = framework_info["type"]
        config = framework_info["config"]
        
        try:
            # 🧠 SMART DEPLOYMENT PREPARATION
            await self._smart_deployment_preparation(repo_path, framework_type, analysis, enhancements)
            
            # Create missing directories
            if framework_type in ["react", "vue", "angular"]:
                await self._ensure_directory(repo_path, "src", enhancements)
                await self._ensure_directory(repo_path, "public", enhancements)
            
            # Generate missing files based on framework
            if framework_type == "react":
                await self._enhance_react_project(repo_path, analysis, enhancements)
            elif framework_type == "vue":
                await self._enhance_vue_project(repo_path, analysis, enhancements)
            elif framework_type == "angular":
                await self._enhance_angular_project(repo_path, analysis, enhancements)
            elif framework_type == "nextjs":
                await self._enhance_nextjs_project(repo_path, analysis, enhancements)
            elif framework_type == "nextjs_turborepo":
                await self._enhance_turborepo_project(repo_path, analysis, enhancements)
            else:  # static
                await self._enhance_static_project(repo_path, analysis, enhancements)
            
            # Always ensure package.json for npm-based projects
            if framework_type != "static":
                await self._ensure_package_json(repo_path, framework_type, enhancements)
            
            # 🎯 INTELLIGENT FILE ORGANIZATION
            await self._organize_for_web_serving(repo_path, framework_type, analysis, enhancements)
            
            logger.info(f"Repository enhancement completed: {enhancements}")
            return enhancements
            
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            return {"error": str(e), **enhancements}

    async def _enhance_react_project(self, repo_path: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Generate missing React project files"""
        
        # Create public/index.html if missing
        index_html_path = os.path.join(repo_path, "public", "index.html")
        if not os.path.exists(index_html_path):
            await self._create_file(index_html_path, self._get_react_index_template(), enhancements)
        
        # Create src/index.js if missing
        index_js_path = os.path.join(repo_path, "src", "index.js")
        index_jsx_path = os.path.join(repo_path, "src", "index.jsx")
        if not os.path.exists(index_js_path) and not os.path.exists(index_jsx_path):
            await self._create_file(index_js_path, self._get_react_index_js_template(), enhancements)
        
        # Create src/App.js if missing
        app_js_path = os.path.join(repo_path, "src", "App.js")
        app_jsx_path = os.path.join(repo_path, "src", "App.jsx")
        if not os.path.exists(app_js_path) and not os.path.exists(app_jsx_path):
            await self._create_file(app_js_path, self._get_react_app_template(), enhancements)

    async def _enhance_static_project(self, repo_path: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Generate missing static site files or detect documentation-only repositories"""
        
        # First, check if this is a documentation-only repository
        file_analysis = analysis.get('file_analysis', {})
        file_types = file_analysis.get('file_types', {})
        total_files = file_analysis.get('total_files', 0)
        
        # Count documentation files
        doc_files = file_types.get('.md', 0) + file_types.get('.txt', 0) + file_types.get('.rst', 0)
        doc_percentage = (doc_files / total_files * 100) if total_files > 0 else 0
        
        # If repository is primarily documentation files, don't create index.html
        if doc_percentage >= 80 and file_analysis.get('source_files_count', 0) == 0:
            logger.info(f"📄 Repository is {doc_percentage:.1f}% documentation files - not creating index.html")
            enhancements["suggestions"].append(
                f"This repository contains primarily documentation files ({doc_files} .md/.txt/.rst files). "
                "Consider using GitHub Pages, GitBook, or a documentation generator like Docusaurus instead of deploying as a web application."
            )
            # Don't create index.html for documentation repositories
            return
        
        # Create index.html if missing (only for actual web projects)
        index_html_path = os.path.join(repo_path, "index.html")
        if not os.path.exists(index_html_path):
            await self._create_file(index_html_path, self._get_static_index_template(), enhancements)

    async def _enhance_turborepo_project(self, repo_path: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Enhanced validation for Turborepo monorepos"""
        
        # Check if turbo.json exists
        turbo_config_path = os.path.join(repo_path, "turbo.json")
        if not os.path.exists(turbo_config_path):
            await self._create_file(turbo_config_path, self._get_turbo_config_template(), enhancements)
            
        # Check for pnpm-workspace.yaml
        pnpm_workspace_path = os.path.join(repo_path, "pnpm-workspace.yaml")
        if not os.path.exists(pnpm_workspace_path):
            await self._create_file(pnpm_workspace_path, self._get_pnpm_workspace_template(), enhancements)
            
        # Ensure apps and packages directories exist
        await self._ensure_directory(repo_path, "apps", enhancements)
        await self._ensure_directory(repo_path, "packages", enhancements)
        
        logger.info("Turborepo project validation completed")

    async def _ensure_directory(self, repo_path: str, dir_name: str, enhancements: Dict[str, Any]):
        """Ensure directory exists"""
        dir_path = os.path.join(repo_path, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            enhancements["directories_created"].append(dir_name)

    async def _create_file(self, file_path: str, content: str, enhancements: Dict[str, Any]):
        """Create file with content"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        relative_path = os.path.relpath(file_path, os.path.dirname(file_path))
        enhancements["files_created"].append(relative_path)

    async def _ensure_package_json(self, repo_path: str, framework_type: str, enhancements: Dict[str, Any]):
        """Ensure package.json exists with proper configuration"""
        package_json_path = os.path.join(repo_path, "package.json")
        
        if not os.path.exists(package_json_path):
            package_content = self._get_package_json_template(framework_type)
            await self._create_file(package_json_path, package_content, enhancements)
        else:
            # Validate and enhance existing package.json
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                modified = False
                
                # Ensure build script exists
                if 'scripts' not in package_data:
                    package_data['scripts'] = {}
                
                if 'build' not in package_data['scripts']:
                    if framework_type == "react":
                        package_data['scripts']['build'] = "react-scripts build"
                    elif framework_type == "vue":
                        package_data['scripts']['build'] = "vue-cli-service build"
                    elif framework_type == "nextjs":
                        package_data['scripts']['build'] = "next build && next export"
                    modified = True
                
                if modified:
                    with open(package_json_path, 'w') as f:
                        json.dump(package_data, f, indent=2)
                    enhancements["files_modified"].append("package.json")
                    
            except json.JSONDecodeError:
                logger.warning("Could not parse existing package.json")

    async def _validate_repository_structure(self, repo_path: str, framework_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that repository has all required files for deployment"""
        
        framework_type = framework_info["type"]
        config = framework_info["config"]
        required_files = config["required_files"]
        
        validation = {
            "is_build_ready": True,
            "missing_files": [],
            "present_files": [],
            "build_commands": config["build_commands"],
            "build_output": config["build_output"],
            "entry_point": config["entry_point"]
        }
        
        # Check required files
        for required_file in required_files:
            file_path = os.path.join(repo_path, required_file)
            if os.path.exists(file_path):
                validation["present_files"].append(required_file)
            else:
                validation["missing_files"].append(required_file)
                validation["is_build_ready"] = False
        
        return validation

    async def _smart_deployment_preparation(self, repo_path: str, framework_type: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """
        🧠 INTELLIGENT DEPLOYMENT PREPARATION
        Auto-detects and fixes common deployment issues
        """
        
        # 1. FIX GITHUB PAGES HOMEPAGE ISSUE (like we just solved!)
        if framework_type in ["react", "vue", "angular", "nextjs"]:
            await self._fix_homepage_paths(repo_path, enhancements)
        
        # 2. DETECT AND FIX BUILD OUTPUT PATHS
        await self._fix_build_output_paths(repo_path, framework_type, enhancements)
        
        # 3. ENSURE PROPER INDEX FILE STRUCTURE
        await self._ensure_proper_index_structure(repo_path, framework_type, analysis, enhancements)
        
        # 4. FIX ASSET PATH ISSUES
        await self._fix_asset_paths(repo_path, framework_type, enhancements)
        
        logger.info("Smart deployment preparation completed")

    async def _fix_homepage_paths(self, repo_path: str, enhancements: Dict[str, Any]):
        """Fix GitHub Pages homepage paths for root deployment"""
        package_json_path = os.path.join(repo_path, "package.json")
        
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                original_homepage = package_data.get("homepage", "")
                
                # Detect GitHub Pages homepage patterns
                if ("github.io" in original_homepage or 
                    original_homepage.endswith("/") or
                    original_homepage.startswith("https://") and "/" in original_homepage.split("//")[1]):
                    
                    # Fix for root deployment
                    package_data["homepage"] = "."
                    
                    with open(package_json_path, 'w') as f:
                        json.dump(package_data, f, indent=2)
                    
                    enhancements["files_modified"].append("package.json")
                    enhancements["smart_fixes"].append({
                        "type": "homepage_path_fix",
                        "original": original_homepage,
                        "fixed": ".",
                        "reason": "Converted GitHub Pages path to root deployment path"
                    })
                    
            except Exception as e:
                logger.warning(f"Could not fix homepage path: {e}")

    async def _fix_build_output_paths(self, repo_path: str, framework_type: str, enhancements: Dict[str, Any]):
        """Ensure build outputs are configured for web serving"""
        
        if framework_type == "nextjs":
            # Check if Next.js is configured for static export
            next_config_path = os.path.join(repo_path, "next.config.js")
            
            if os.path.exists(next_config_path):
                try:
                    with open(next_config_path, 'r') as f:
                        content = f.read()
                    
                    # Check if static export is enabled
                    if "output: 'export'" not in content and "trailingSlash: true" not in content:
                        # Add static export configuration
                        if "module.exports = {" in content:
                            content = content.replace(
                                "module.exports = {",
                                "module.exports = {\n  output: 'export',\n  trailingSlash: true,\n  images: { unoptimized: true },"
                            )
                        else:
                            content = """/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true }
}

module.exports = nextConfig
"""
                        
                        with open(next_config_path, 'w') as f:
                            f.write(content)
                        
                        enhancements["files_modified"].append("next.config.js")
                        enhancements["smart_fixes"].append({
                            "type": "nextjs_static_export",
                            "reason": "Enabled static export for deployment compatibility"
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not modify next.config.js: {e}")

    async def _ensure_proper_index_structure(self, repo_path: str, framework_type: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Ensure proper index file structure for web serving"""
        
        # For static sites, ensure index.html exists in root
        if framework_type == "static":
            index_html_path = os.path.join(repo_path, "index.html")
            if not os.path.exists(index_html_path):
                # Look for other HTML files that could be the main page
                html_files = [f for f in analysis["files"] if f["extension"] == ".html"]
                
                if html_files:
                    # Use the first HTML file as index
                    main_html = html_files[0]
                    original_path = os.path.join(repo_path, main_html["path"])
                    
                    if main_html["name"] != "index.html":
                        # Copy/rename to index.html
                        with open(original_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        with open(index_html_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        enhancements["files_created"].append("index.html")
                        enhancements["smart_fixes"].append({
                            "type": "index_html_creation",
                            "source": main_html["path"],
                            "reason": f"Created index.html from {main_html['name']} for web serving"
                        })

    async def _fix_asset_paths(self, repo_path: str, framework_type: str, enhancements: Dict[str, Any]):
        """Fix asset path references for proper serving"""
        
        # This would scan HTML/CSS/JS files and fix relative paths
        # For now, we'll focus on the most common issues
        
        if framework_type == "static":
            # Scan HTML files for common path issues
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.html'):
                        file_path = os.path.join(root, file)
                        await self._fix_html_asset_paths(file_path, enhancements)

    async def _fix_html_asset_paths(self, file_path: str, enhancements: Dict[str, Any]):
        """Fix asset paths in HTML files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix common path issues
            # Convert absolute paths to relative where appropriate
            content = content.replace('src="/', 'src="./')
            content = content.replace('href="/', 'href="./')
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                relative_path = os.path.relpath(file_path)
                enhancements["files_modified"].append(relative_path)
                enhancements["smart_fixes"].append({
                    "type": "asset_path_fix",
                    "file": relative_path,
                    "reason": "Fixed absolute paths to relative paths for better serving"
                })
                
        except Exception as e:
            logger.warning(f"Could not fix asset paths in {file_path}: {e}")

    async def _organize_for_web_serving(self, repo_path: str, framework_type: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """
        🎯 INTELLIGENT FILE ORGANIZATION
        Reorganize files for optimal web serving
        """
        
        # For static sites, ensure all web assets are accessible
        if framework_type == "static":
            await self._organize_static_assets(repo_path, analysis, enhancements)
        
        # For all projects, create a deployment manifest
        await self._create_deployment_manifest(repo_path, framework_type, analysis, enhancements)

    async def _organize_static_assets(self, repo_path: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Organize static assets for better web serving"""
        
        # Create assets directory if we have many static files scattered
        static_files = [f for f in analysis["files"] if f["extension"] in ['.css', '.js', '.jpg', '.png', '.gif', '.svg', '.ico']]
        
        # If we have static files in subdirectories, consider creating symlinks or organizing them
        assets_dir = os.path.join(repo_path, "assets")
        
        scattered_assets = [f for f in static_files if f["directory"] != "" and not f["directory"].startswith("assets")]
        
        if len(scattered_assets) > 5:  # Arbitrary threshold
            # Create assets directory
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir, exist_ok=True)
                enhancements["directories_created"].append("assets")
                enhancements["smart_fixes"].append({
                    "type": "assets_organization",
                    "reason": f"Created assets directory to organize {len(scattered_assets)} scattered files"
                })

    async def _create_deployment_manifest(self, repo_path: str, framework_type: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Create a deployment manifest with intelligent analysis"""
        
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "framework_type": framework_type,
            "deployment_ready": True,
            "statistics": {
                "total_files": analysis["total_files"],
                "total_size_bytes": analysis["total_size"],
                "source_files": len(analysis["source_files"]),
                "static_files": len(analysis["static_files"]),
                "config_files": len(analysis["config_files"])
            },
            "smart_fixes_applied": enhancements.get("smart_fixes", []),
            "build_recommendation": self._get_build_recommendation(framework_type, analysis),
            "serving_recommendation": self._get_serving_recommendation(framework_type, analysis)
        }
        
        manifest_path = os.path.join(repo_path, ".codeflowops-manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        enhancements["files_created"].append(".codeflowops-manifest.json")

    def _get_build_recommendation(self, framework_type: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent build recommendations"""
        
        if framework_type == "react":
            return {
                "commands": ["npm install", "npm run build"],
                "output_directory": "build",
                "estimated_build_time": "2-5 minutes",
                "optimization_suggestions": [
                    "Consider enabling production optimizations",
                    "Minimize bundle size with tree shaking"
                ]
            }
        elif framework_type == "static":
            return {
                "commands": [],
                "output_directory": ".",
                "estimated_build_time": "immediate",
                "optimization_suggestions": [
                    "Compress images for faster loading",
                    "Minify CSS and JavaScript files"
                ]
            }
        
        return {"commands": ["npm install", "npm run build"], "output_directory": "dist"}

    def _get_serving_recommendation(self, framework_type: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent serving recommendations"""
        
        return {
            "cdn_enabled": True,
            "compression": "gzip, br",
            "caching_strategy": "aggressive for assets, standard for HTML",
            "ssl_required": True,
            "performance_optimizations": [
                "Enable CloudFront caching",
                "Use appropriate MIME types",
                "Enable browser caching headers"
            ]
        }

    async def _validate_repository_structure(self, repo_path: str, framework_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that repository has all required files for deployment"""
        
        framework_type = framework_info["type"]
        config = framework_info["config"]
        required_files = config["required_files"]
        
        validation = {
            "is_build_ready": True,
            "missing_files": [],
            "present_files": [],
            "build_commands": config["build_commands"],
            "build_output": config["build_output"],
            "entry_point": config["entry_point"]
        }
        
        # Check required files
        for required_file in required_files:
            file_path = os.path.join(repo_path, required_file)
            if os.path.exists(file_path):
                validation["present_files"].append(required_file)
            else:
                validation["missing_files"].append(required_file)
                validation["is_build_ready"] = False
        
        return validation

    async def _enhance_vue_project(self, repo_path: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Generate missing Vue project files"""
        # Placeholder for Vue enhancement
        pass

    async def _enhance_angular_project(self, repo_path: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Generate missing Angular project files"""
        # Placeholder for Angular enhancement  
        pass

    async def _enhance_nextjs_project(self, repo_path: str, analysis: Dict[str, Any], enhancements: Dict[str, Any]):
        """Generate missing Next.js project files"""
        # Placeholder for Next.js enhancement
        pass

    # Template methods
    def _get_react_index_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Web app created by CodeFlowOps" />
    <title>React App</title>
</head>
<body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
</body>
</html>'''

    def _get_react_index_js_template(self) -> str:
        return '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);'''

    def _get_react_app_template(self) -> str:
        return '''import React from 'react';

function App() {
  return (
    <div style={{ textAlign: 'center', padding: '50px' }}>
      <h1>Welcome to Your React App</h1>
      <p>This app was enhanced and deployed by CodeFlowOps</p>
      <p>Edit src/App.js to get started!</p>
    </div>
  );
}

export default App;'''

    def _get_static_index_template(self) -> str:
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Your Website</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 50px;
            text-align: center;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        p { color: #666; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Your Website</h1>
        <p>This static site was enhanced and deployed by CodeFlowOps</p>
        <p>Edit index.html to customize your site!</p>
    </div>
</body>
</html>'''

    def _get_package_json_template(self, framework_type: str) -> str:
        if framework_type == "react":
            return json.dumps({
                "name": "react-app",
                "version": "0.1.0",
                "private": True,
                "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-scripts": "5.0.1"
                },
                "scripts": {
                    "start": "react-scripts start",
                    "build": "react-scripts build",
                    "test": "react-scripts test",
                    "eject": "react-scripts eject"
                },
                "browserslist": {
                    "production": [">0.2%", "not dead", "not op_mini all"],
                    "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
                }
            }, indent=2)
        elif framework_type == "nextjs_turborepo":
            return json.dumps({
                "name": "turborepo-monorepo",
                "version": "0.0.0",
                "private": True,
                "workspaces": ["apps/*", "packages/*"],
                "scripts": {
                    "build": "turbo run build",
                    "dev": "turbo run dev",
                    "lint": "turbo run lint",
                    "test": "turbo run test"
                },
                "devDependencies": {
                    "turbo": "latest"
                },
                "packageManager": "pnpm@8.0.0"
            }, indent=2)
        
        # Add other framework templates as needed
        return json.dumps({"name": "app", "version": "1.0.0"}, indent=2)

    def _get_turbo_config_template(self) -> str:
        """Generate turbo.json configuration"""
        return json.dumps({
            "$schema": "https://turbo.build/schema.json",
            "globalDependencies": ["**/.env.*local"],
            "pipeline": {
                "build": {
                    "dependsOn": ["^build"],
                    "outputs": ["dist/**", "out/**", ".next/**", "!.next/cache/**"]
                },
                "lint": {
                    "dependsOn": ["^lint"]
                },
                "test": {
                    "dependsOn": ["^test"]
                },
                "dev": {
                    "cache": False,
                    "persistent": True
                }
            }
        }, indent=2)

    def _get_pnpm_workspace_template(self) -> str:
        """Generate pnpm-workspace.yaml configuration"""
        return '''packages:
  - 'apps/*'
  - 'packages/*'
'''
