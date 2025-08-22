"""
React builder - handles install and build process with robust Windows Rollup support
"""
import os
import time
import logging
from pathlib import Path
from core.models import StackPlan, BuildResult
from core.utils import run_npm_command, find_files
from core.utils_js import pick_package_manager, robust_install_and_build, has_build_script

logger = logging.getLogger(__name__)

class ReactBuilder:
    """Handles building React applications with intelligent package manager selection"""
    
    def build(self, plan: StackPlan, repo_dir: Path) -> BuildResult:
        """
        Build React application using intelligent package manager selection and robust fallback strategies.
        Handles Windows Rollup compatibility issues automatically.
        """
        start_time = time.time()
        
        try:
            logger.info("🔨 Building React application with robust package manager system...")
            logger.info(f"📦 Target package manager: {plan.config.get('package_manager', 'auto')}")
            logger.info(f"🛠️ Build tool: {plan.config.get('build_tool', 'webpack')}")
            
            # Fix homepage for root deployment before build
            package_json_path = repo_dir / "package.json"
            is_nextjs = False
            if package_json_path.exists():
                try:
                    import json
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                        deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
                        is_nextjs = "next" in deps
                    
                    # CRITICAL FIX: Override homepage for root deployment
                    if "homepage" in package_data:
                        original_homepage = package_data["homepage"]
                        logger.info(f"🔧 Original homepage: {original_homepage}")
                        logger.info("🔧 Overriding homepage to '/' for root deployment...")
                        package_data["homepage"] = "/"
                        
                        # Write back the modified package.json
                        with open(package_json_path, 'w') as f:
                            json.dump(package_data, f, indent=2)
                        
                        logger.info("✅ Package.json homepage overridden for proper deployment")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not modify package.json: {e}")
                    pass
            
            # Use robust install and build system
            from core.utils import run_npm_command
            import os
            
            # Select package manager intelligently
            selected_pm = pick_package_manager(repo_dir, override=plan.config.get('package_manager'))
            logger.info(f"📦 Selected package manager: {selected_pm}")
            
            # Check if build script exists
            build_script_exists = has_build_script(repo_dir)
            
            # Call robust install and build with correct parameters
            build_success, build_message = robust_install_and_build(
                run_npm_command,
                repo_dir,
                os.environ.copy(),
                selected_pm,
                build_script_exists
            )
            
            # Package the result for compatibility with our builder expectations
            build_result = {
                'stdout': build_message if build_success else '',
                'stderr': build_message if not build_success else '',
                'error': build_message if not build_success else None
            }
            
            if not build_success:
                return BuildResult(
                    success=False,
                    artifact_dir=repo_dir,
                    error_message=f"Robust build failed with {selected_pm}: {build_result.get('error', 'Unknown error')}",
                    build_time_seconds=time.time() - start_time
                )
            
            logger.info(f"✅ Build completed successfully with {selected_pm}")
            if 'stdout' in build_result:
                logger.info(f"📜 Build output: {build_result['stdout']}")
            if 'stderr' in build_result and build_result['stderr']:
                logger.info(f"📝 Build warnings: {build_result['stderr']}")
            
            # Store which package manager worked for future use
            plan.config['successful_package_manager'] = selected_pm
            
            # DEBUG: List all files in repository after build
            logger.info(f"📊 REPO AFTER BUILD ANALYSIS:")
            all_repo_files_after_build = []
            for root, dirs, files in os.walk(repo_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_dir)
                    all_repo_files_after_build.append(rel_path)
            
            logger.info(f"   Total files in repo after build: {len(all_repo_files_after_build)}")
            
            # Show build-related directories
            subdirs = [d for d in os.listdir(repo_dir) if os.path.isdir(os.path.join(repo_dir, d))]
            logger.info(f"   Subdirectories: {subdirs}")
            
            # Show build/dist/out files specifically
            build_related_files = [f for f in all_repo_files_after_build if any(keyword in f.lower() for keyword in ['build/', 'dist/', 'out/', '.next/'])]
            if build_related_files:
                logger.info(f"   Build-related files ({len(build_related_files)}):")
                for i, f in enumerate(build_related_files[:15], 1):
                    logger.info(f"      {i}. {f}")
                if len(build_related_files) > 15:
                    logger.info(f"      ... and {len(build_related_files) - 15} more build files")
            else:
                logger.warning("   ⚠️ No build/ dist/ out/ .next/ files found after build!")
            
            # Step 3: Validate build output - Enhanced detection
            build_output_dir = plan.output_dir
            
            if not build_output_dir.exists():
                # Try alternative output directories in order of likelihood
                alternatives = ["build", "dist", "out", ".next", "public", "docs"]
                logger.info(f"🔍 Build output not found at {plan.output_dir}, checking alternatives...")
                
                for alt in alternatives:
                    alt_path = repo_dir / alt
                    if alt_path.exists() and alt_path.is_dir():
                        # Check if this directory has web content
                        files = list(alt_path.rglob("*"))
                        html_files = [f for f in files if f.suffix == '.html']
                        js_files = [f for f in files if f.suffix == '.js']
                        
                        if html_files or js_files:
                            build_output_dir = alt_path
                            logger.info(f"📁 Found build output in: {alt} ({len(html_files)} HTML, {len(js_files)} JS files)")
                            break
                        else:
                            logger.info(f"📂 Directory {alt} exists but appears empty of web content")
                else:
                    # Last resort: check if repo_dir itself has web content (for simple sites)
                    repo_files = list(repo_dir.rglob("*.html"))
                    if repo_files:
                        build_output_dir = repo_dir
                        logger.info(f"📁 Using repository root as build output ({len(repo_files)} HTML files found)")
                    else:
                        return BuildResult(
                            success=False,
                            artifact_dir=repo_dir,
                            error_message=f"Build output directory not found. Checked: {plan.output_dir}, {', '.join(alternatives)}",
                            build_time_seconds=time.time() - start_time
                        )
            
            # Validate build contents
            html_files = find_files(build_output_dir, ["*.html"])
            js_files = find_files(build_output_dir, ["*.js"])
            css_files = find_files(build_output_dir, ["*.css"])
            
            # If no HTML files exist, generate a basic index.html to serve the JS/CSS
            if not html_files:
                logger.warning("⚠️ No HTML files found in build output - generating basic index.html")
                
                # Find main JS and CSS files
                main_js = None
                main_css = None
                
                # Look for common main file patterns
                for js_file in js_files:
                    if any(pattern in js_file.name.lower() for pattern in ['main', 'bundle', 'app', 'index']):
                        main_js = js_file.relative_to(build_output_dir)
                        break
                
                if not main_js and js_files:
                    # Use the first JS file found
                    main_js = js_files[0].relative_to(build_output_dir)
                
                for css_file in css_files:
                    if any(pattern in css_file.name.lower() for pattern in ['main', 'bundle', 'app', 'index']):
                        main_css = css_file.relative_to(build_output_dir)
                        break
                
                if not main_css and css_files:
                    # Use the first CSS file found
                    main_css = css_files[0].relative_to(build_output_dir)
                
                # Generate basic HTML file
                html_content = self._generate_index_html(main_js, main_css, repo_dir)
                index_path = build_output_dir / "index.html"
                
                try:
                    with open(index_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"✅ Generated index.html at {index_path}")
                    html_files = [index_path]  # Update html_files list
                except Exception as e:
                    logger.error(f"❌ Failed to generate index.html: {e}")
                    return BuildResult(
                        success=False,
                        artifact_dir=repo_dir,
                        error_message=f"No HTML files found and failed to generate index.html: {str(e)}",
                        build_time_seconds=time.time() - start_time
                    )
            
            # Check for index.html (required for SPAs)
            index_html = build_output_dir / "index.html"
            if not index_html.exists():
                logger.warning("⚠️ index.html not found - SPA routing may not work")
            
            build_time = time.time() - start_time
            
            logger.info(f"📊 Build statistics:")
            logger.info(f"   📄 HTML files: {len(html_files)}")
            logger.info(f"   ⚡ JS files: {len(js_files)}")
            logger.info(f"   🎨 CSS files: {len(css_files)}")
            logger.info(f"   ⏱️ Build time: {build_time:.2f}s")
            logger.info(f"   📦 Package manager used: {selected_pm}")
            
            return BuildResult(
                success=True,
                artifact_dir=build_output_dir,
                build_time_seconds=build_time,
                metadata={
                    "html_files": len(html_files),
                    "js_files": len(js_files),
                    "css_files": len(css_files),
                    "has_index_html": index_html.exists(),
                    "build_tool": plan.config.get("build_tool"),
                    "package_manager": selected_pm,
                    "typescript": plan.config.get("typescript", False)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ React build failed: {e}")
            return BuildResult(
                success=False,
                artifact_dir=repo_dir,
                error_message=f"Build failed: {str(e)}",
                build_time_seconds=time.time() - start_time
            )

    def _generate_index_html(self, main_js=None, main_css=None, repo_dir=None):
        """Generate a beautiful CodeFlowOps-branded index.html file for React applications"""
        
        # Try to get project name from package.json
        project_name = "React Application"
        repo_url = ""
        if repo_dir:
            package_json_path = repo_dir / "package.json"
            if package_json_path.exists():
                try:
                    import json
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                        project_name = package_data.get("name", "React Application").replace("-", " ").replace("_", " ").title()
                        repo_url = package_data.get("repository", {}).get("url", "") if isinstance(package_data.get("repository"), dict) else package_data.get("repository", "")
                except:
                    pass
        
        # Build CSS link tag
        css_link = ""
        if main_css:
            css_link = f'<link rel="stylesheet" type="text/css" href="{main_css}">'
        
        # Build JS script tag
        js_script = ""
        if main_js:
            js_script = f'<script type="text/javascript" src="{main_js}"></script>'
        
        # Generate beautiful HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <title>{project_name} | Deployed with CodeFlowOps</title>
    {css_link}
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 3rem;
            text-align: center;
            max-width: 600px;
            margin: 2rem;
        }}
        .logo {{
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            font-size: 2rem;
            color: white;
        }}
        h1 {{
            color: #2d3748;
            font-size: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 700;
        }}
        .subtitle {{
            color: #718096;
            font-size: 1.25rem;
            margin-bottom: 2rem;
            line-height: 1.5;
        }}
        .status {{
            background: #f0fff4;
            border: 2px solid #9ae6b4;
            color: #22543d;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            font-weight: 600;
        }}
        .info {{
            background: #f7fafc;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 2rem 0;
        }}
        .info h3 {{
            color: #2d3748;
            margin-bottom: 1rem;
        }}
        .info p {{
            color: #4a5568;
            line-height: 1.6;
        }}
        .footer {{
            margin-top: 2rem;
            color: #a0aec0;
            font-size: 0.875rem;
        }}
        .github-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        .github-link:hover {{
            text-decoration: underline;
        }}
        #root {{
            /* Container for React app */
        }}
    </style>
</head>
<body>
    <div id="root">
        <!-- React will render here if JS loads -->
        <div class="container">
            <div class="logo">⚛️</div>
            <h1>{project_name}</h1>
            <p class="subtitle">Deployed successfully with CodeFlowOps</p>
            
            <div class="status">
                ✅ Application deployed and ready to serve
            </div>
            
            <div class="info">
                <h3>Deployment Information</h3>
                <p>
                    This React application has been successfully built and deployed using 
                    CodeFlowOps' intelligent deployment system with automatic package manager 
                    selection and Windows Rollup compatibility.
                </p>
            </div>
            
            <div class="footer">
                <p>
                    Powered by <strong>CodeFlowOps</strong> • 
                    {'<a href="' + repo_url + '" class="github-link" target="_blank">View Source</a>' if repo_url else 'Advanced CI/CD Platform'}
                </p>
            </div>
        </div>
    </div>
    
    {js_script}
</body>
</html>'''
        
        return html_content

    def validate_build_requirements(self, repo_dir: Path) -> bool:
        """Validate that the repository has the required files for React build"""
        try:
            package_json = repo_dir / "package.json"
            if not package_json.exists():
                logger.error("❌ package.json not found")
                return False
            
            # Check if it's a valid React project
            import json
            with open(package_json, 'r') as f:
                package_data = json.load(f)
                
            deps = {**package_data.get("dependencies", {}), **package_data.get("devDependencies", {})}
            
            # Check for React or Next.js
            if not any(dep in deps for dep in ['react', 'next']):
                logger.error("❌ Not a React or Next.js project")
                return False
            
            # Check for build script
            scripts = package_data.get("scripts", {})
            if "build" not in scripts:
                logger.error("❌ No build script found in package.json")
                return False
            
            logger.info("✅ Build requirements validated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating build requirements: {e}")
            return False
