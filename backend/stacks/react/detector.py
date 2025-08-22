"""
React detector - identifies React applications
"""
from pathlib import Path
from typing import Optional
from core.models import StackPlan
from core.utils import read_json_file, check_file_exists

class ReactDetector:
    """Detects React applications"""
    
    def detect(self, repo_dir: Path) -> Optional[StackPlan]:
        """
        Detect React applications by analyzing package.json
        
        Looks for:
        - React dependencies
        - React scripts
        - Common React project patterns
        """
        # Must have package.json
        if not check_file_exists(repo_dir, "package.json"):
            return None
            
        package_data = read_json_file(repo_dir / "package.json")
        if not package_data:
            return None
        
        # Get all dependencies
        dependencies = package_data.get("dependencies", {})
        dev_dependencies = package_data.get("devDependencies", {})
        all_deps = {**dependencies, **dev_dependencies}
        
        # Check for React indicators
        react_indicators = ["react", "react-dom", "react-scripts", "@types/react"]
        found_react_deps = [dep for dep in react_indicators if dep in all_deps]
        
        if not found_react_deps:
            return None
            
        # Get scripts
        scripts = package_data.get("scripts", {})
        
        # Determine build command and output directory
        build_cmd = "npm run build"
        output_dir_name = "build"  # Default React output
        
        # Enhanced build tool detection and command setup
        if "vite" in all_deps or any("vite" in str(script) for script in scripts.values()):
            output_dir_name = "dist"
            build_cmd = "npm run build"
        elif "next" in all_deps or "@next/core" in all_deps:
            output_dir_name = "out"  # Next.js static export
            # Next.js needs export for static hosting
            if "build" in scripts:
                build_script = scripts["build"]
                if "export" in build_script:
                    # Already has export in build command
                    build_cmd = "npm run build"
                elif "export" in scripts:
                    # Has separate export script
                    build_cmd = "npm run build && npm run export"
                else:
                    # Need to add export manually
                    build_cmd = "npm run build && npx next export"
            else:
                # No build script, use default
                build_cmd = "npm run build && npx next export"
        elif "gatsby" in all_deps:
            output_dir_name = "public"
            build_cmd = "npm run build"
        elif "nuxt" in all_deps:
            output_dir_name = "dist"
            build_cmd = "npm run generate"  # Nuxt needs generate for static
        else:
            # Standard React app
            build_cmd = "npm run build"
            
        # Check for custom build script configuration
        if "build" in scripts:
            build_script = scripts["build"]
            # Try to detect output directory from build script
            if "BUILD_PATH=" in build_script:
                # Extract custom build path
                for part in build_script.split():
                    if part.startswith("BUILD_PATH="):
                        output_dir_name = part.split("=")[1]
                        break
            # Check for Next.js export
            elif "next build && next export" in build_script or "next export" in build_script:
                output_dir_name = "out"
            # Check for Vite build output customization
            elif "vite build" in build_script and "--outDir" in build_script:
                parts = build_script.split()
                for i, part in enumerate(parts):
                    if part == "--outDir" and i + 1 < len(parts):
                        output_dir_name = parts[i + 1]
                        break
                        break
        
        build_commands = ["npm install", build_cmd]
        
        # Create environment variables for React builds
        env_vars = {
            'NODE_OPTIONS': '--max-old-space-size=4096',
            'GENERATE_SOURCEMAP': 'false',
            'CI': 'true',
            'FORCE_COLOR': '0'
        }
        
        # Add Next.js specific configuration
        if "next" in all_deps:
            env_vars['NEXT_TELEMETRY_DISABLED'] = '1'
            # Ensure static export capability by creating next.config.js first
            if "export" not in scripts.get("build", "") and "export" not in scripts:
                # Create next.config.js with static export configuration BEFORE build
                config_cmd = 'echo "module.exports = { output: \\"export\\", trailingSlash: true, images: { unoptimized: true } }" > next.config.js'
                build_commands.insert(1, config_cmd)  # Insert after npm install, before build
        
        # Detect actual entry point
        entry_point = "src/index.js"  # Default
        if check_file_exists(repo_dir, "src/index.tsx"):
            entry_point = "src/index.tsx"
        elif check_file_exists(repo_dir, "src/index.ts"):
            entry_point = "src/index.ts"  
        elif check_file_exists(repo_dir, "src/main.jsx"):
            entry_point = "src/main.jsx"  # Vite default
        elif check_file_exists(repo_dir, "src/main.tsx"):
            entry_point = "src/main.tsx"  # Vite TypeScript
        elif check_file_exists(repo_dir, "src/App.js"):
            entry_point = "src/App.js"  # If no index, use App
        elif check_file_exists(repo_dir, "public/index.html"):
            entry_point = "public/index.html"  # HTML entry
        
        # Detect package manager
        package_manager = "npm"
        if check_file_exists(repo_dir, "yarn.lock"):
            package_manager = "yarn"
        elif check_file_exists(repo_dir, "pnpm-lock.yaml"):
            package_manager = "pnpm"
        
        return StackPlan(
            stack_key="react",
            build_cmds=build_commands,
            output_dir=repo_dir / output_dir_name,
            env=env_vars,
            config={
                "entry_point": entry_point,
                "package_manager": package_manager,
                "build_tool": "vite" if "vite" in all_deps else "webpack",
                "react_version": all_deps.get("react", "unknown"),
                "typescript": "@types/react" in all_deps or "typescript" in all_deps,
                "dependencies_count": len(all_deps),
                "found_indicators": found_react_deps,
                "build_output_dir": output_dir_name,
                "has_typescript": "@types/react" in all_deps or "typescript" in all_deps,
                "has_next": "next" in all_deps,
                "has_vite": "vite" in all_deps
            }
        )
    
    def get_priority(self) -> int:
        """React has high priority - check before generic static detection"""
        return 50
