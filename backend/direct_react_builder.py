"""
Direct React Builder - Python-based React building in the cloud
Replaces AWS CodeBuild with our own Python implementation using yarn first, npm fallback
Production-ready for Elastic Beanstalk deployment (Linux/Windows compatible)
"""

import os
import shutil
import subprocess
import tempfile
import logging
import uuid
import zipfile
import platform
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DirectReactBuilder:
    """
    Direct Python-based React builder that clones and builds React apps in the cloud
    No AWS CodeBuild required - we handle everything with Python
    Features: yarn-first with npm fallback, cross-platform compatibility
    Production-ready for Elastic Beanstalk (Linux) and local development (Windows)
    """
    
    def __init__(self):
        self.temp_dir = None
        self.platform = platform.system().lower()
        logger.info(f"🔧 DirectReactBuilder initialized on {self.platform}")
        
    def _get_node_paths(self) -> List[str]:
        """Get Node.js executable paths for the current platform"""
        node_paths = []
        
        if self.platform == 'windows':
            # Windows paths
            node_paths = [
                r"C:\Program Files\nodejs",
                r"C:\Program Files (x86)\nodejs", 
                os.path.expanduser(r"~\AppData\Roaming\npm"),
                os.path.expanduser(r"~\AppData\Local\Yarn\bin")
            ]
        elif self.platform == 'linux':
            # Linux paths for Elastic Beanstalk and general Linux
            node_paths = [
                "/usr/bin",
                "/usr/local/bin", 
                "/opt/nodejs/bin",
                "/home/webapp/node_modules/.bin",  # Elastic Beanstalk
                "/var/app/current/node_modules/.bin",  # Elastic Beanstalk
                os.path.expanduser("~/.npm-global/bin"),
                os.path.expanduser("~/.yarn/bin"),
                os.path.expanduser("~/node_modules/.bin")
            ]
        elif self.platform == 'darwin':
            # macOS paths
            node_paths = [
                "/usr/local/bin",
                "/opt/homebrew/bin",
                os.path.expanduser("~/.npm-global/bin"),
                os.path.expanduser("~/.yarn/bin")
            ]
        
        # Filter to only existing paths
        existing_paths = [path for path in node_paths if os.path.exists(path)]
        logger.debug(f"🔍 Found Node.js paths: {existing_paths}")
        return existing_paths
    
    def _setup_environment(self) -> tuple[dict, bool]:
        """Setup environment variables and shell settings for subprocess calls"""
        env = os.environ.copy()
        shell = False
        
        if self.platform == 'windows':
            # Windows requires shell=True for npm.ps1/yarn.ps1
            shell = True
            # Add Node.js paths to PATH
            node_paths = self._get_node_paths()
            current_path = env.get('PATH', '')
            for path in node_paths:
                if path not in current_path:
                    env['PATH'] = f"{path};{current_path}"
        else:
            # Linux/macOS - use shell=False for better security
            shell = False
            # Add Node.js paths to PATH
            node_paths = self._get_node_paths()
            current_path = env.get('PATH', '')
            for path in node_paths:
                if path not in current_path:
                    env['PATH'] = f"{path}:{current_path}"
                    
        logger.debug(f"🔧 Environment configured for {self.platform} (shell={shell})")
        return env, shell
        
    def clone_repository(self, repo_url: str, target_dir: str) -> bool:
        """Clone GitHub repository to target directory"""
        try:
            logger.info(f"🔄 Cloning repository: {repo_url}")
            
            # Clean target directory if exists
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            # Clone repository
            result = subprocess.run([
                'git', 'clone', repo_url, target_dir
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info(f"✅ Repository cloned successfully to {target_dir}")
                return True
            else:
                logger.error(f"❌ Git clone failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Git clone timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Clone error: {str(e)}")
            return False
    
    def detect_package_manager(self, project_dir: str) -> str:
        """Detect which package manager the project uses - yarn first, npm fallback"""
        package_json_path = os.path.join(project_dir, 'package.json')
        yarn_lock_path = os.path.join(project_dir, 'yarn.lock')
        package_lock_path = os.path.join(project_dir, 'package-lock.json')
        pnpm_lock_path = os.path.join(project_dir, 'pnpm-lock.yaml')
        
        if not os.path.exists(package_json_path):
            raise Exception("No package.json found - not a Node.js project")
        
        logger.info(f"🔍 Analyzing package manager files...")
        logger.info(f"   yarn.lock: {'✅' if os.path.exists(yarn_lock_path) else '❌'}")
        logger.info(f"   package-lock.json: {'✅' if os.path.exists(package_lock_path) else '❌'}")
        logger.info(f"   pnpm-lock.yaml: {'✅' if os.path.exists(pnpm_lock_path) else '❌'}")
        
        # Priority order: yarn first (preferred), then pnpm, then npm
        if os.path.exists(yarn_lock_path):
            logger.info("📦 Detected: yarn (preferred)")
            return 'yarn'
        elif os.path.exists(pnpm_lock_path):
            logger.info("📦 Detected: pnpm")
            return 'pnpm'
        elif os.path.exists(package_lock_path):
            logger.info("📦 Detected: npm")
            return 'npm'
        else:
            # Default to yarn first, fallback to npm
            logger.info("📦 No lock file found - defaulting to yarn with npm fallback")
            return 'yarn'
    
    def detect_build_tool(self, project_dir: str) -> Dict[str, str]:
        """Detect build tool and output directory"""
        package_json_path = os.path.join(project_dir, 'package.json')
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            scripts = package_data.get('scripts', {})
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            # Check for build tool
            build_tool = 'unknown'
            output_dir = 'build'  # default
            
            if 'vite' in dependencies or 'vite' in dev_dependencies:
                build_tool = 'vite'
                output_dir = 'dist'
            elif 'react-scripts' in dependencies or 'react-scripts' in dev_dependencies:
                build_tool = 'create-react-app'
                output_dir = 'build'
            elif 'next' in dependencies or 'next' in dev_dependencies:
                build_tool = 'nextjs'
                output_dir = '.next'
            elif 'webpack' in dependencies or 'webpack' in dev_dependencies:
                build_tool = 'webpack'
                output_dir = 'dist'
            
            # Check if build script exists
            build_script = scripts.get('build', 'npm run build')
            
            return {
                'build_tool': build_tool,
                'output_dir': output_dir,
                'build_script': build_script,
                'scripts': scripts
            }
            
        except Exception as e:
            logger.warning(f"Could not analyze package.json: {e}")
            return {
                'build_tool': 'unknown',
                'output_dir': 'build',
                'build_script': 'npm run build',
                'scripts': {}
            }
    
    def install_dependencies(self, project_dir: str, package_manager: str) -> Tuple[bool, str]:
        """Install project dependencies using yarn first, npm fallback - cross-platform"""
        try:
            logger.info(f"📦 Installing dependencies with {package_manager}...")
            logger.info(f"🔧 Platform: {self.platform}")
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_dir)
            
            # Get platform-specific environment setup
            env, shell = self._setup_environment()
            
            try:
                # Try yarn first (preferred)
                if package_manager == 'yarn' or package_manager == 'auto':
                    try:
                        # Check if yarn is available
                        logger.debug("🧶 Checking yarn availability...")
                        subprocess.run(['yarn', '--version'], capture_output=True, check=True, timeout=10, env=env, shell=shell)
                        logger.info("🧶 Using yarn (preferred package manager)")
                        
                        # Use yarn install with frozen lockfile if yarn.lock exists
                        if os.path.exists('yarn.lock'):
                            logger.info("📦 Installing with yarn (yarn.lock found)")
                            result = subprocess.run(['yarn', 'install', '--frozen-lockfile'], 
                                                  capture_output=True, text=True, timeout=300, env=env, shell=shell)
                        else:
                            logger.info("📦 Installing with yarn (no lock file)")
                            result = subprocess.run(['yarn', 'install'], 
                                                  capture_output=True, text=True, timeout=300, env=env, shell=shell)
                        
                        if result.returncode == 0:
                            logger.info("✅ Dependencies installed successfully with yarn")
                            return True, 'yarn'
                        else:
                            logger.warning(f"⚠️ Yarn install failed: {result.stderr}")
                            logger.info("🔄 Falling back to npm...")
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                        logger.warning(f"⚠️ Yarn not available: {e}")
                        logger.info("🔄 Falling back to npm...")
                
                # Try npm (fallback or primary choice)
                try:
                    logger.debug("📦 Checking npm availability...")
                    subprocess.run(['npm', '--version'], capture_output=True, check=True, timeout=10, env=env, shell=shell)
                    logger.info("📦 Using npm")
                    
                    # Use npm ci if package-lock.json exists, otherwise npm install
                    if os.path.exists('package-lock.json'):
                        logger.info("📦 Installing with npm ci (package-lock.json found)")
                        result = subprocess.run(['npm', 'ci'], 
                                              capture_output=True, text=True, timeout=300, env=env, shell=shell)
                    else:
                        logger.info("📦 Installing with npm install")
                        result = subprocess.run(['npm', 'install'], 
                                              capture_output=True, text=True, timeout=300, env=env, shell=shell)
                    
                    if result.returncode == 0:
                        logger.info("✅ Dependencies installed successfully with npm")
                        return True, 'npm'
                    else:
                        logger.error(f"❌ npm install failed: {result.stderr}")
                        
                        # Final fallback: try npm install without ci
                        if os.path.exists('package-lock.json'):
                            logger.info("🔄 Trying npm install as final fallback...")
                            result = subprocess.run(['npm', 'install'], 
                                                  capture_output=True, text=True, timeout=300)
                            if result.returncode == 0:
                                logger.info("✅ Final fallback npm install succeeded")
                                return True, 'npm'
                        
                        return False, 'failed'
                        
                except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                    logger.error(f"❌ npm not available: {e}")
                    return False, 'failed'
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"❌ Dependency installation error: {str(e)}")
            return False, 'failed'
    
    def build_react_app(self, project_dir: str, used_package_manager: str, build_info: Dict[str, str]) -> Tuple[bool, str]:
        """Build the React application using the package manager that successfully installed deps - cross-platform"""
        try:
            logger.info(f"🔨 Building React app with {build_info['build_tool']} using {used_package_manager}...")
            logger.info(f"📁 Expected output directory: {build_info['output_dir']}")
            logger.info(f"🔧 Platform: {self.platform}")
            
            original_cwd = os.getcwd()
            os.chdir(project_dir)
            
            # Get platform-specific environment setup
            env, shell = self._setup_environment()
            
            try:
                # Use the package manager that successfully installed dependencies
                if used_package_manager == 'yarn':
                    logger.info("🧶 Building with yarn...")
                    result = subprocess.run(['yarn', 'build'], 
                                          capture_output=True, text=True, timeout=600, env=env, shell=shell)
                elif used_package_manager == 'pnpm':
                    logger.info("📦 Building with pnpm...")
                    result = subprocess.run(['pnpm', 'run', 'build'], 
                                          capture_output=True, text=True, timeout=600, env=env, shell=shell)
                else:  # npm
                    logger.info("📦 Building with npm...")
                    result = subprocess.run(['npm', 'run', 'build'], 
                                          capture_output=True, text=True, timeout=600, env=env, shell=shell)
                
                if result.returncode == 0:
                    logger.info(f"✅ React app built successfully with {used_package_manager}")
                    
                    # Verify build output directory exists
                    expected_output = build_info['output_dir']
                    if os.path.exists(expected_output):
                        logger.info(f"✅ Build output found in {expected_output}/")
                        
                        # List contents for verification
                        files = os.listdir(expected_output)
                        logger.info(f"📁 Build contains {len(files)} files/folders")
                        
                        return True, expected_output
                    else:
                        # Check for alternative output directories
                        alternative_dirs = ['build', 'dist', '.next', 'out']
                        for alt_dir in alternative_dirs:
                            if os.path.exists(alt_dir) and alt_dir != expected_output:
                                logger.info(f"✅ Build output found in alternative directory: {alt_dir}/")
                                return True, alt_dir
                        
                        logger.warning(f"⚠️ Build succeeded but no output directory found. Expected: {expected_output}")
                        logger.info("📁 Current directory contents:")
                        for item in os.listdir('.'):
                            logger.info(f"   {item}")
                        return False, ""
                else:
                    logger.error(f"❌ Build failed with {used_package_manager}: {result.stderr}")
                    return False, ""
                    
            finally:
                os.chdir(original_cwd)
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Build timeout (10 minutes)")
            return False, ""
        except Exception as e:
            logger.error(f"❌ Build error: {str(e)}")
            return False, ""
    
    def create_build_archive(self, project_dir: str, output_dir: str, archive_path: str) -> bool:
        """Create a zip archive of the build output"""
        try:
            build_path = os.path.join(project_dir, output_dir)
            
            if not os.path.exists(build_path):
                logger.error(f"❌ Build output directory not found: {build_path}")
                return False
            
            logger.info(f"📦 Creating build archive: {archive_path}")
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(build_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, build_path)
                        zipf.write(file_path, arc_name)
            
            logger.info(f"✅ Build archive created: {archive_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Archive creation failed: {str(e)}")
            return False

    def build_react_from_repo(self, repo_url: str, deployment_id: str = None) -> Dict[str, Any]:
        """
        Complete workflow: Clone repo -> Analyze -> Install deps -> Build -> Create archive
        This replaces AWS CodeBuild with our own Python implementation
        """
        try:
            if not deployment_id:
                deployment_id = str(uuid.uuid4())[:8]
            
            logger.info(f"🚀 Starting direct React build for: {repo_url}")
            logger.info(f"🆔 Deployment ID: {deployment_id}")
            
            # Step 1: Create temporary directory for this build
            self.temp_dir = tempfile.mkdtemp(prefix=f'react_build_{deployment_id}_')
            project_dir = os.path.join(self.temp_dir, 'repo')
            
            logger.info(f"📁 Temp directory: {self.temp_dir}")
            
            # Step 2: Clone repository to temp directory
            if not self.clone_repository(repo_url, project_dir):
                return {
                    'status': 'error',
                    'error': 'Failed to clone repository',
                    'stage': 'clone'
                }
            
            # Step 3: Analyze the project (after cloning)
            logger.info("🔍 Analyzing cloned React project...")
            
            # Detect package manager (yarn first, npm fallback)
            try:
                detected_pm = self.detect_package_manager(project_dir)
                logger.info(f"📦 Package manager strategy: {detected_pm}")
            except Exception as e:
                logger.error(f"❌ Package manager detection failed: {e}")
                return {
                    'status': 'error',
                    'error': f'Package manager detection failed: {e}',
                    'stage': 'analysis'
                }
            
            # Detect build tool and configuration
            try:
                build_info = self.detect_build_tool(project_dir)
                logger.info(f"🔧 Build tool: {build_info['build_tool']}")
                logger.info(f"📁 Expected output: {build_info['output_dir']}")
            except Exception as e:
                logger.error(f"❌ Build tool detection failed: {e}")
                return {
                    'status': 'error',
                    'error': f'Build tool detection failed: {e}',
                    'stage': 'analysis'
                }
            
            # Step 4: Install dependencies (yarn first, npm fallback)
            logger.info("📦 Installing dependencies...")
            install_success, used_package_manager = self.install_dependencies(project_dir, detected_pm)
            
            if not install_success:
                return {
                    'status': 'error',
                    'error': 'Failed to install dependencies with both yarn and npm',
                    'stage': 'dependencies'
                }
            
            logger.info(f"✅ Dependencies installed successfully with {used_package_manager}")
            
            # Step 5: Build the React application
            logger.info("🔨 Building React application...")
            build_success, actual_output_dir = self.build_react_app(project_dir, used_package_manager, build_info)
            
            if not build_success:
                return {
                    'status': 'error',
                    'error': 'Failed to build React application',
                    'stage': 'build'
                }
            
            # Update build info with actual output directory
            if actual_output_dir:
                build_info['output_dir'] = actual_output_dir
            
            # Step 6: Create build archive
            archive_path = os.path.join(self.temp_dir, f'build_{deployment_id}.zip')
            build_output_path = os.path.join(project_dir, build_info['output_dir'])
            
            if not self.create_build_archive(project_dir, build_info['output_dir'], archive_path):
                return {
                    'status': 'error',
                    'error': 'Failed to create build archive',
                    'stage': 'archive'
                }
            
            # Success!
            logger.info("🎉 React build completed successfully!")
            
            return {
                'status': 'success',
                'deployment_id': deployment_id,
                'project_dir': project_dir,
                'build_output_path': build_output_path,
                'archive_path': archive_path,
                'package_manager_used': used_package_manager,
                'package_manager_detected': detected_pm,
                'build_tool': build_info['build_tool'],
                'output_directory': build_info['output_dir'],
                'temp_dir': self.temp_dir,
                'repo_url': repo_url
            }
            
        except Exception as e:
            logger.error(f"❌ Unexpected build error: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'stage': 'unexpected'
            }

    def cleanup(self):
        """Clean up temporary directories"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"🧹 Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"⚠️  Could not clean up {self.temp_dir}: {e}")

# Test function for the DirectReactBuilder - Production Ready
def test_direct_react_builder(repo_url: str = None):
    """
    Test the DirectReactBuilder with configurable repository
    For production: pass repo_url parameter
    For development: defaults to UXpert test repository
    """
    builder = DirectReactBuilder()
    
    try:
        # Use provided repo_url or default for testing
        test_repo_url = repo_url or os.getenv('TEST_REPO_URL', "https://github.com/Alkaison/UXpert")
        
        print("🚀 Testing DirectReactBuilder...")
        print(f"📦 Repository: {test_repo_url}")
        print("🧶 Using yarn-first strategy with npm fallback")
        print(f"🔧 Platform: {builder.platform}")
        print("")
        
        result = builder.build_react_from_repo(test_repo_url)
        
        if result['status'] == 'success':
            print("🎉 BUILD SUCCESSFUL!")
            print(f"📁 Build output: {result['build_output_path']}")
            print(f"📦 Archive: {result['archive_path']}")
            print(f"🔧 Package manager used: {result['package_manager_used']}")
            print(f"🛠️  Build tool: {result['build_tool']}")
            print(f"📂 Output directory: {result['output_directory']}")
            print("✅ Ready for deployment!")
            return True
        else:
            print(f"❌ BUILD FAILED: {result['error']}")
            print(f"🔍 Stage: {result['stage']}")
            return False
            
    finally:
        # Always cleanup
        builder.cleanup()

def create_production_builder(config: Dict[str, Any] = None) -> DirectReactBuilder:
    """
    Create a DirectReactBuilder instance for production use
    
    Args:
        config: Optional configuration dictionary for future extensibility
        
    Returns:
        DirectReactBuilder: Ready-to-use builder instance
    """
    builder = DirectReactBuilder()
    
    # Apply any configuration if provided
    if config:
        logger.info(f"🔧 Applying production configuration: {list(config.keys())}")
        # Future: apply configuration settings here
    
    logger.info("✅ Production DirectReactBuilder ready")
    return builder

if __name__ == "__main__":
    # Development testing
    test_direct_react_builder()
