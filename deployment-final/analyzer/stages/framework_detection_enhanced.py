"""
🎯 Framework Detection Stage - Enhanced with Monorepo & Toolkit Support
Intelligent detection of web frameworks, static sites, monorepos, and toolkits
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import re

logger = logging.getLogger(__name__)

class FrameworkDetectionStage:
    """🔍 Intelligent Framework Detection with High-Signal Rules + Monorepo Support"""

    async def analyze(self, context) -> None:
        repo_path = getattr(context, "repo_path", None)
        if not repo_path or not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            if not hasattr(context, "intelligence_profile") or not isinstance(getattr(context, "intelligence_profile"), dict):
                context.intelligence_profile = {}
            context.intelligence_profile["frameworks"] = []
            context.intelligence_profile["stack_classification"] = {"type": "unknown", "confidence": 0.1}
            return

        logger.info(f"🔍 Analyzing frameworks in: {repo_path}")

        if not hasattr(context, "intelligence_profile") or not isinstance(context.intelligence_profile, dict):
            context.intelligence_profile = {}
        files_analyzed = getattr(context, "files", []) or []

        frameworks: List[Dict[str, Any]] = []
        
        # 🔍 FIRST: Check for monorepos and toolkits
        monorepo_info = self._detect_monorepo(repo_path)
        toolkit_info = self._detect_toolkit(repo_path, monorepo_info)
        
        if toolkit_info:
            # This is a toolkit/library - handle differently
            context.intelligence_profile["project_kind"] = toolkit_info["kind"]
            context.intelligence_profile["frameworks"] = [toolkit_info["framework"]]
            context.intelligence_profile["stack_classification"] = {
                "type": "toolkit", 
                "confidence": toolkit_info["framework"]["confidence"],
                "reason": "toolkit repo; not a deployable app"
            }
            context.intelligence_profile["monorepo"] = monorepo_info
            context.intelligence_profile["templates"] = toolkit_info.get("templates", [])
            context.intelligence_profile["ready_to_deploy"] = False
            logger.info(f"✅ Detected toolkit: {toolkit_info['framework']['name']}")
            return
        elif monorepo_info["is_monorepo"]:
            # Handle monorepo with multiple apps
            context.intelligence_profile["project_kind"] = "monorepo"
            context.intelligence_profile["monorepo"] = monorepo_info
            # Detect frameworks in each package/app
            for package in monorepo_info["packages"]:
                package_path = repo_path / package["path"]
                if package_path.exists():
                    package_frameworks = self._detect_frameworks_in_path(package_path)
                    for fw in package_frameworks:
                        fw["package"] = package["name"]
                        frameworks.append(fw)
        else:
            # Regular single-app repo
            context.intelligence_profile["project_kind"] = "app"

        # Regular framework detection for apps
        if not toolkit_info:
            # 1) Static first (tolerant of incidental PHP)
            static_result = self._detect_static_site(repo_path)
            if static_result:
                frameworks.append(static_result)

            # 2) PHP (requires strong PHP signals)
            php_result = self._detect_php_frameworks(repo_path)
            if php_result:
                frameworks.append(php_result)

            # 3) JS frameworks
            frameworks.extend(self._detect_js_frameworks(repo_path))

            # 4) Python frameworks
            py = self._detect_python_frameworks(repo_path)
            if py:
                frameworks.append(py)

        # ✅ Always sort by confidence before classifying
        frameworks.sort(key=lambda f: f.get("confidence", 0), reverse=True)

        stack_classification = self._classify_primary_stack(frameworks)

        context.intelligence_profile["frameworks"] = frameworks
        context.intelligence_profile["stack_classification"] = stack_classification
        logger.info(f"✅ Framework detection complete: {len(frameworks)} frameworks, primary stack: {stack_classification['type']}")

    def _detect_monorepo(self, repo_path: Path) -> Dict[str, Any]:
        """🔍 Detect monorepo structure and packages"""
        monorepo_info = {
            "is_monorepo": False,
            "workspaces": False,
            "packages": [],
            "tool": None
        }
        
        package_json_path = repo_path / "package.json"
        if package_json_path.exists():
            try:
                package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
                
                # Check for workspaces
                if "workspaces" in package_data:
                    monorepo_info["workspaces"] = True
                    monorepo_info["is_monorepo"] = True
                    monorepo_info["tool"] = "npm"
                    
                    # Find packages
                    workspaces = package_data["workspaces"]
                    if isinstance(workspaces, list):
                        for pattern in workspaces:
                            self._find_workspace_packages(repo_path, pattern, monorepo_info["packages"])
                    elif isinstance(workspaces, dict) and "packages" in workspaces:
                        for pattern in workspaces["packages"]:
                            self._find_workspace_packages(repo_path, pattern, monorepo_info["packages"])
            except Exception as e:
                logger.debug(f"Could not parse package.json: {e}")
        
        # Check for pnpm workspaces
        pnpm_workspace = repo_path / "pnpm-workspace.yaml"
        if pnpm_workspace.exists():
            monorepo_info["is_monorepo"] = True
            monorepo_info["tool"] = "pnpm"
        
        # Check for lerna
        lerna_json = repo_path / "lerna.json"
        if lerna_json.exists():
            monorepo_info["is_monorepo"] = True
            monorepo_info["tool"] = "lerna"
        
        # Fallback: check for common package patterns
        if not monorepo_info["is_monorepo"]:
            common_patterns = ["packages/*", "apps/*", "services/*"]
            for pattern in common_patterns:
                self._find_workspace_packages(repo_path, pattern, monorepo_info["packages"])
            if monorepo_info["packages"]:
                monorepo_info["is_monorepo"] = True
                monorepo_info["tool"] = "manual"
        
        return monorepo_info
    
    def _find_workspace_packages(self, repo_path: Path, pattern: str, packages: List[Dict]):
        """Find packages matching a workspace pattern"""
        try:
            if "*" in pattern:
                parent_dir = repo_path / pattern.replace("/*", "")
                if parent_dir.exists():
                    for pkg_dir in parent_dir.iterdir():
                        if pkg_dir.is_dir() and (pkg_dir / "package.json").exists():
                            rel_path = pkg_dir.relative_to(repo_path)
                            packages.append({
                                "name": pkg_dir.name,
                                "path": str(rel_path),
                                "type": self._guess_package_type(pkg_dir)
                            })
            else:
                pkg_dir = repo_path / pattern
                if pkg_dir.exists() and (pkg_dir / "package.json").exists():
                    rel_path = pkg_dir.relative_to(repo_path)
                    packages.append({
                        "name": pkg_dir.name,
                        "path": str(rel_path),
                        "type": self._guess_package_type(pkg_dir)
                    })
        except Exception as e:
            logger.debug(f"Error finding packages for pattern {pattern}: {e}")
    
    def _guess_package_type(self, pkg_path: Path) -> str:
        """Guess if a package is an app, library, or toolkit"""
        if (pkg_path / "public" / "index.html").exists() and (pkg_path / "src" / "index.js").exists():
            return "app"
        elif any(pkg_path.glob("bin/*")) or (pkg_path / "bin").exists():
            return "toolkit"
        elif pkg_path.name.startswith("create-") or pkg_path.name.endswith("-template"):
            return "template"
        else:
            return "library"
    
    def _detect_toolkit(self, repo_path: Path, monorepo_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🔍 Detect if this is a toolkit/generator like Create React App"""
        
        # CRA Detection
        packages_dir = repo_path / "packages"
        if packages_dir.exists():
            cra_signals = [
                (packages_dir / "react-scripts").exists(),
                (packages_dir / "create-react-app").exists(),
                len(list(packages_dir.glob("cra-template*"))) > 0,
                len(list(packages_dir.glob("babel-preset-react-app"))) > 0,
            ]
            
            if any(cra_signals):
                # This is Create React App toolkit
                templates = []
                
                # Find CRA templates
                for template_dir in packages_dir.glob("cra-template*"):
                    template_info = self._analyze_cra_template(template_dir)
                    if template_info:
                        templates.append(template_info)
                
                evidence = []
                for pkg in packages_dir.iterdir():
                    if pkg.name in ["react-scripts", "create-react-app"] or pkg.name.startswith("cra-template"):
                        evidence.append(f"packages/{pkg.name}")
                
                return {
                    "kind": "monorepo+toolkit",
                    "framework": {
                        "name": "cra-tooling",
                        "confidence": 0.99,
                        "evidence": evidence
                    },
                    "templates": templates
                }
        
        # Check for other toolkit patterns
        package_json_path = repo_path / "package.json"
        if package_json_path.exists():
            try:
                package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
                name = package_data.get("name", "")
                
                toolkit_patterns = ["create-", "-cli", "-generator", "yeoman-"]
                for pattern in toolkit_patterns:
                    if pattern in name:
                        return {
                            "kind": "toolkit",
                            "framework": {
                                "name": f"{name}-tooling",
                                "confidence": 0.85,
                                "evidence": [f"package name: {name}"]
                            },
                            "templates": []
                        }
            except Exception as e:
                logger.debug(f"Could not parse package.json: {e}")
        
        return None
    
    def _analyze_cra_template(self, template_dir: Path) -> Optional[Dict[str, Any]]:
        """Analyze a CRA template and create app contract"""
        template_path = template_dir / "template"
        if not template_path.exists():
            return None
        
        # Check for template structure
        has_public_index = (template_path / "public" / "index.html").exists()
        has_src_index = (template_path / "src" / "index.js").exists() or (template_path / "src" / "index.tsx").exists()
        has_package_json = (template_path / "package.json").exists()
        
        if not (has_public_index and has_src_index and has_package_json):
            return None
        
        return {
            "id": template_dir.name,
            "app_contract": {
                "stack_id": "react-cra-spa",
                "rendering_mode": "static",
                "build": {
                    "commands": ["npm ci", "npm run build"],
                    "artifact": {"path": "build", "type": "static"}
                },
                "routing": {"spa_fallback": True},
                "env": {
                    "build_time": ["REACT_APP_*"],
                    "runtime": []
                }
            }
        }
    
    def _detect_frameworks_in_path(self, path: Path) -> List[Dict[str, Any]]:
        """Detect frameworks in a specific package path"""
        frameworks = []
        
        # Static site detection
        static_result = self._detect_static_site(path)
        if static_result:
            frameworks.append(static_result)
        
        # PHP detection
        php_result = self._detect_php_frameworks(path)
        if php_result:
            frameworks.append(php_result)
        
        # JS frameworks
        frameworks.extend(self._detect_js_frameworks(path))
        
        # Python frameworks
        py = self._detect_python_frameworks(path)
        if py:
            frameworks.append(py)
        
        return frameworks

    def _detect_static_site(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Detect static sites with tolerance for incidental PHP"""
        logger.debug("🔍 Checking for static site...")

        has_index_html = (repo_path / "index.html").exists()
        if not has_index_html:
            return None

        # --- Disqualify only if STRONG server signals exist ---
        php_files = [p for p in repo_path.glob("**/*.php") if "vendor" not in p.parts]
        has_root_php_index = (repo_path / "index.php").exists() or (repo_path / "public" / "index.php").exists()
        has_composer = (repo_path / "composer.json").exists()
        has_artisan = (repo_path / "artisan").exists()

        strong_php_signals = has_root_php_index or has_composer or has_artisan or (len(php_files) >= 3)
        if strong_php_signals:
            logger.debug("❌ Strong PHP signals present; not a static site")
            return None

        # Count assets (no brace globs in pathlib)
        html_files = list(repo_path.glob("**/*.html"))
        css_files = list(repo_path.glob("**/*.css"))
        js_files  = list(repo_path.glob("**/*.js"))
        img_exts = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp")
        image_files = [p for p in repo_path.rglob("*") if p.suffix.lower() in img_exts]

        evidence = [
            "index.html in root",
            f"{len(html_files)} HTML files",
            f"{len(css_files)} CSS files",
            f"{len(js_files)} JS files",
            f"{len(image_files)} image files"
        ]

        # If there is incidental PHP (e.g., a contact form), note it but don't disqualify
        if 0 < len(php_files) < 3 and not (has_root_php_index or has_composer or has_artisan):
            evidence.append(f"incidental PHP files present ({len(php_files)}), likely contact form(s)")

        return {
            "name": "static-basic",
            "confidence": 0.97,
            "evidence": evidence,
            "framework_type": "static",
            "rendering_mode": "static",
            "build_required": False,
            "deployment_target": "s3+cloudfront"
        }

    def _detect_php_frameworks(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Detect PHP frameworks with high-signal requirements"""
        php_files = [p for p in repo_path.glob("**/*.php") if "vendor" not in p.parts]
        has_root_php_index = (repo_path / "index.php").exists() or (repo_path / "public" / "index.php").exists()
        has_composer = (repo_path / "composer.json").exists()
        has_vendor = (repo_path / "vendor").exists()
        has_artisan = (repo_path / "artisan").exists()

        # ✅ Require strong PHP signals; otherwise treat as static-with-php
        if not (has_root_php_index or has_composer or has_artisan or len(php_files) >= 3):
            return None

        evidence = []
        if php_files:
            evidence.append(f"{len(php_files)} PHP files")
        if has_root_php_index:
            evidence.append("public/index.php or index.php present")
        if has_composer:
            evidence.append("composer.json")
        if has_vendor or has_artisan:
            evidence.append("vendor/ or artisan detected")

        framework_name = "php"
        confidence = 0.70

        # Try composer.json to refine (laravel/symfony/codeigniter)
        if has_composer:
            try:
                composer_data = json.loads((repo_path / "composer.json").read_text(encoding="utf-8"))
                require = composer_data.get("require", {})
                if "laravel/framework" in require:
                    framework_name, confidence = "laravel", 0.95
                    evidence.append("Laravel framework in composer.json")
                elif any(k.startswith("symfony/") for k in require):
                    framework_name, confidence = "symfony", 0.90
                    evidence.append("Symfony packages in composer.json")
                elif "codeigniter/framework" in require or "codeigniter4/framework" in require:
                    framework_name, confidence = "codeigniter", 0.90
                    evidence.append("CodeIgniter framework in composer.json")
            except Exception as e:
                logger.debug(f"Could not parse composer.json: {e}")

        return {
            "name": framework_name,
            "confidence": confidence,
            "evidence": evidence,
            "framework_type": "backend",
            "language": "php",
            "requires_server": True,
            "deployment_target": "ec2"
        }

    def _detect_js_frameworks(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Detect JavaScript frameworks"""
        results: List[Dict[str, Any]] = []
        package_json_path = repo_path / "package.json"
        if not package_json_path.exists():
            return results

        try:
            package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
            deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}

            if "next" in deps:
                evidence = ["next in package.json"]
                has_api_routes = (repo_path / "pages" / "api").exists() or (repo_path / "app" / "api").exists()
                has_middleware = (repo_path / "middleware.ts").exists() or (repo_path / "middleware.js").exists()
                variant = "ssr" if (has_api_routes or has_middleware) else "static"
                if has_api_routes: evidence.append("API routes detected")
                if has_middleware: evidence.append("middleware detected")
                results.append({
                    "name": "nextjs",
                    "confidence": 0.95,
                    "evidence": evidence,
                    "framework_type": "frontend",
                    "variant": variant,
                    "language": "javascript",
                    "requires_server": variant == "ssr",
                    "deployment_target": "s3+cloudfront" if variant == "static" else "ec2"
                })
            elif "react" in deps:
                bundlers = []
                if (repo_path / "vite.config.js").exists() or (repo_path / "vite.config.ts").exists():
                    bundlers.append("vite")
                if (repo_path / "webpack.config.js").exists():
                    bundlers.append("webpack")
                if (repo_path / "craco.config.js").exists():
                    bundlers.append("craco")

                evidence = ["react in package.json"] + ([f"{b} config" for b in bundlers] if bundlers else [])
                results.append({
                    "name": "react",
                    "confidence": 0.90,
                    "evidence": evidence,
                    "framework_type": "frontend",
                    "variant": "spa",
                    "language": "javascript",
                    "requires_server": False,
                    "deployment_target": "s3+cloudfront"
                })
            elif "vue" in deps:
                results.append({
                    "name": "vue",
                    "confidence": 0.90,
                    "evidence": ["vue in package.json"],
                    "framework_type": "frontend",
                    "variant": "spa",
                    "language": "javascript",
                    "requires_server": False,
                    "deployment_target": "s3+cloudfront"
                })

        except Exception as e:
            logger.debug(f"Could not parse package.json: {e}")

        return results

    def _detect_python_frameworks(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Detect Python frameworks"""
        has_requirements = (repo_path / "requirements.txt").exists()
        has_pyproject = (repo_path / "pyproject.toml").exists()
        if not (has_requirements or has_pyproject):
            return None

        python_files = list(repo_path.glob("**/*.py"))
        if not python_files:
            return None

        evidence = [f"{len(python_files)} Python files"]
        framework_name, confidence = "python", 0.60

        if (repo_path / "manage.py").exists():
            evidence.append("manage.py (Django)")
            framework_name, confidence = "django", 0.95
        else:
            for py_file in python_files[:10]:
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r'app\s*=\s*Flask\(', content):
                        evidence.append("Flask app detected")
                        framework_name, confidence = "flask", 0.90
                        break
                    if re.search(r'FastAPI\(', content):
                        evidence.append("FastAPI app detected")
                        framework_name, confidence = "fastapi", 0.90
                        break
                except Exception:
                    continue

        if has_requirements: evidence.append("requirements.txt")
        if has_pyproject: evidence.append("pyproject.toml")

        return {
            "name": framework_name,
            "confidence": confidence,
            "evidence": evidence,
            "framework_type": "backend",
            "language": "python",
            "requires_server": True,
            "deployment_target": "ec2"
        }

    def _classify_primary_stack(self, frameworks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify the primary stack from detected frameworks"""
        if not frameworks:
            return {"type": "unknown", "confidence": 0.1}

        primary = frameworks[0]
        name = primary.get("name", "unknown")
        conf = primary.get("confidence", 0.0)

        if name == "static-basic":
            return {"type": "static-basic", "confidence": conf, "rendering_mode": "static",
                    "required_runtimes": [], "evidence": primary.get("evidence", [])}
        if name == "laravel":
            return {"type": "php-laravel", "confidence": conf, "rendering_mode": "server",
                    "required_runtimes": ["php-fpm"], "evidence": primary.get("evidence", [])}
        if name == "nextjs":
            variant = primary.get("variant", "static")
            return {"type": f"nextjs-{variant}", "confidence": conf,
                    "rendering_mode": "server" if variant == "ssr" else "static",
                    "required_runtimes": ["nodejs"] if variant == "ssr" else [],
                    "evidence": primary.get("evidence", [])}
        if name == "react":
            return {"type": "react-spa", "confidence": conf, "rendering_mode": "static",
                    "required_runtimes": [], "evidence": primary.get("evidence", [])}

        return {"type": name, "confidence": conf,
                "rendering_mode": "server" if primary.get("requires_server") else "static",
                "required_runtimes": [primary.get("language", "unknown")] if primary.get("requires_server") else [],
                "evidence": primary.get("evidence", [])}
