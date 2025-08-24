"""
Utility functions shared across the plugin system
"""
import os
import subprocess
import logging
import shutil
import tempfile
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

# File system utilities
def safe_remove_directory(path: Path) -> bool:
    """Safely remove a directory and all its contents"""
    try:
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            logger.debug(f"Removed directory: {path}")
            return True
    except Exception as e:
        logger.error(f"Failed to remove directory {path}: {e}")
    return False

def create_temp_directory(prefix: str = "codeflowops_") -> Path:
    """Create a temporary directory"""
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    logger.debug(f"Created temp directory: {temp_dir}")
    return temp_dir

def copy_directory(src: Path, dst: Path) -> bool:
    """Copy directory from src to dst"""
    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
        logger.debug(f"Copied directory: {src} -> {dst}")
        return True
    except Exception as e:
        logger.error(f"Failed to copy directory {src} to {dst}: {e}")
        return False

# Process execution utilities
def run_command(
    command: List[str], 
    cwd: Path, 
    env: Optional[Dict[str, str]] = None,
    timeout: int = 300,
    capture_output: bool = True
) -> Tuple[bool, str, str]:
    """
    Run a shell command safely
    
    Returns:
        (success, stdout, stderr)
    """
    try:
        # Prepare environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
            
        logger.debug(f"Running command: {' '.join(command)} in {cwd}")
        
        # On Windows, handle npm and other Node.js commands properly
        import platform
        use_shell = False
        if platform.system() == "Windows" and len(command) > 0:
            # For npm, yarn, pnpm on Windows, we need shell=True
            if command[0] in ['npm', 'yarn', 'pnpm', 'node', 'npx']:
                use_shell = True
            elif command[0].endswith('.cmd') or command[0].endswith('.bat'):
                use_shell = True
        
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=run_env,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            shell=use_shell
        )
        
        success = result.returncode == 0
        if not success:
            logger.error(f"Command failed with code {result.returncode}: {' '.join(command)}")
            logger.error(f"Stderr: {result.stderr}")
            
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {' '.join(command)}")
        return False, "", f"Command timed out after {timeout} seconds"
    except FileNotFoundError as e:
        logger.error(f"File not found error (WinError 2): {e}")
        logger.error(f"Command attempted: {' '.join(command)}")
        logger.error(f"Working directory: {cwd}")
        return False, "", f"File not found: {' '.join(command)} - {str(e)}"
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return False, "", str(e)

def run_npm_command(
    command: List[str],
    cwd: Path,
    timeout: int = 600,
    env: Optional[Dict[str, str]] = None
) -> Tuple[bool, str, str]:
    """Run npm command with optimized environment and production fixes"""
    
    # Fix Windows npm execution: use full path to npm executables
    import platform
    import shutil
    logger.debug(f"Running npm command: {' '.join(command)} in directory: {cwd}")
    
    if platform.system() == "Windows":
        if command[0] == "npm":
            # Try to find npm.cmd in PATH first, then check common locations
            npm_path = shutil.which("npm.cmd")
            if not npm_path:
                # Check common Node.js installation paths
                possible_paths = [
                    "C:\\Program Files\\nodejs\\npm.cmd",
                    "C:\\Program Files (x86)\\nodejs\\npm.cmd",
                    "C:\\Users\\%USERNAME%\\AppData\\Roaming\\npm\\npm.cmd"
                ]
                for path in possible_paths:
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        npm_path = expanded_path
                        logger.debug(f"Found npm at: {npm_path}")
                        break
            if npm_path:
                command[0] = npm_path
            else:
                command[0] = "npm.cmd"  # Fallback to npm.cmd
                logger.warning("Could not find npm.cmd, using fallback")
                
        elif command[0] == "npx":
            # Handle npx similarly to npm
            npx_path = shutil.which("npx.cmd")
            if not npx_path:
                # Check common Node.js installation paths for npx
                possible_paths = [
                    "C:\\Program Files\\nodejs\\npx.cmd",
                    "C:\\Program Files (x86)\\nodejs\\npx.cmd",
                    "C:\\Users\\%USERNAME%\\AppData\\Roaming\\npm\\npx.cmd"
                ]
                for path in possible_paths:
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        npx_path = expanded_path
                        logger.debug(f"Found npx at: {npx_path}")
                        break
            if npx_path:
                command[0] = npx_path
            else:
                command[0] = "npx.cmd"  # Fallback to npx.cmd
                logger.warning("Could not find npx.cmd, using fallback")
                
        elif command[0] == "yarn":
            yarn_path = shutil.which("yarn.cmd")
            if not yarn_path:
                # Check common yarn paths
                possible_paths = [
                    "C:\\Program Files\\nodejs\\yarn.cmd",
                    "C:\\Program Files (x86)\\nodejs\\yarn.cmd",
                    "C:\\Users\\%USERNAME%\\AppData\\Roaming\\npm\\yarn.cmd"
                ]
                for path in possible_paths:
                    expanded_path = os.path.expandvars(path)
                    if os.path.exists(expanded_path):
                        yarn_path = expanded_path
                        break
            if yarn_path:
                command[0] = yarn_path
            else:
                command[0] = "yarn.cmd"
                
        elif command[0] == "pnpm":
            pnpm_path = shutil.which("pnpm.cmd")
            if not pnpm_path:
                command[0] = "pnpm.cmd"
            else:
                command[0] = pnpm_path
                
        # Ensure the command executable exists
        if not os.path.exists(command[0]) and not shutil.which(command[0]):
            logger.error(f"Executable not found: {command[0]}")
            return False, "", f"Executable not found: {command[0]}"
            
        logger.debug(f"Resolved command: {command[0]}")
    
    # Production-ready environment variables (defaults)
    npm_env = {
        'NODE_OPTIONS': '--max-old-space-size=4096',
        'GENERATE_SOURCEMAP': 'false',
        'PUBLIC_URL': '/',  # Set root path for React assets
        'HOMEPAGE': '/',  # Override package.json homepage setting
        'CI': 'true',
        'FORCE_COLOR': '0',
        'NPM_CONFIG_PROGRESS': 'false',
        'NPM_CONFIG_LOGLEVEL': 'warn',
        'NPM_CONFIG_FUND': 'false',
        'NPM_CONFIG_AUDIT': 'false',
        'NPM_CONFIG_UPDATE_NOTIFIER': 'false',
        'BROWSERSLIST_IGNORE_OLD_DATA': 'true',  # Ignore browserslist warnings
        'SKIP_PREFLIGHT_CHECK': 'true',  # Skip React preflight checks
        'DISABLE_ESLINT_PLUGIN': 'true',  # Disable ESLint for faster builds
        # Compatibility for old Next.js versions
        'NODE_ENV': 'production',
        'NEXT_TELEMETRY_DISABLED': '1',
    }
    
    # Add Node.js to PATH on Windows
    if platform.system() == "Windows":
        current_path = os.environ.get('PATH', '')
        node_paths = [
            "C:\\Program Files\\nodejs",
            "C:\\Program Files (x86)\\nodejs",
            "C:\\Users\\%USERNAME%\\AppData\\Roaming\\npm"
        ]
        # Find yarn installation path as well
        yarn_paths = [
            "C:\\Program Files (x86)\\Yarn\\bin",
            "C:\\Program Files\\Yarn\\bin",
            "C:\\Users\\%USERNAME%\\AppData\\Local\\Yarn\\bin"
        ]
        
        paths_to_add = []
        for path_list in [node_paths, yarn_paths]:
            for node_path in path_list:
                expanded_path = os.path.expandvars(node_path)
                if os.path.exists(expanded_path) and expanded_path not in current_path:
                    paths_to_add.append(expanded_path)
        
        if paths_to_add:
            new_path = ";".join(paths_to_add) + ";" + current_path
            npm_env['PATH'] = new_path
            logger.debug(f"Added to PATH: {';'.join(paths_to_add)}")
        else:
            # If no custom path added, preserve existing PATH
            npm_env['PATH'] = current_path
    
    # Override with custom environment if provided
    if env:
        npm_env.update(env)
    
    # For npm install, add --no-optional to skip optional dependencies that might fail
    if len(command) >= 2 and command[1] == "install":
        command.extend(["--no-optional", "--no-audit", "--no-fund"])
    
    return run_command(command, cwd, env=npm_env, timeout=timeout)

# Git utilities
def clone_repository(repo_url: str, target_dir: Path, depth: int = 1) -> bool:
    """Clone a git repository"""
    try:
        command = ["git", "clone", "--depth", str(depth), repo_url, str(target_dir)]
        success, stdout, stderr = run_command(command, Path.cwd(), timeout=120)
        
        if success:
            logger.info(f"✅ Repository cloned: {repo_url}")
        else:
            logger.error(f"❌ Failed to clone repository: {stderr}")
            
        return success
    except Exception as e:
        logger.error(f"Repository clone failed: {e}")
        return False

# AWS utilities
def validate_aws_credentials(credentials: Dict[str, str]) -> Dict[str, Any]:
    """Validate AWS credentials and check permissions"""
    try:
        # Create session with provided credentials
        session = boto3.Session(
            aws_access_key_id=credentials.get("aws_access_key_id"),
            aws_secret_access_key=credentials.get("aws_secret_access_key"),
            region_name=credentials.get("aws_region", "us-east-1")
        )
        
        # Test basic AWS access
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        # Test required service permissions
        permissions = []
        
        # Test S3 permissions
        try:
            s3 = session.client('s3')
            s3.list_buckets()
            permissions.append("s3:ListBucket")
        except ClientError:
            pass
            
        # Test CloudFront permissions
        try:
            cf = session.client('cloudfront')
            cf.list_distributions()
            permissions.append("cloudfront:ListDistributions")
        except ClientError:
            pass
            
        return {
            "valid": True,
            "account_id": identity.get("Account"),
            "user_id": identity.get("UserId"),
            "permissions": permissions,
            "region": credentials.get("aws_region", "us-east-1")
        }
        
    except NoCredentialsError:
        return {"valid": False, "error": "Invalid AWS credentials"}
    except ClientError as e:
        return {"valid": False, "error": f"AWS error: {e}"}
    except Exception as e:
        return {"valid": False, "error": f"Validation failed: {e}"}

def create_s3_bucket(bucket_name: str, region: str, credentials: Dict[str, str]) -> bool:
    """Create S3 bucket for static hosting with proper public access configuration"""
    try:
        logger.info(f"🔍 Debug: create_s3_bucket called with bucket={bucket_name}, region={region}")
        logger.info(f"🔍 Debug: credentials keys: {list(credentials.keys())}")
        
        session = boto3.Session(
            aws_access_key_id=credentials["aws_access_key_id"],
            aws_secret_access_key=credentials["aws_secret_access_key"],
            region_name=region
        )
        
        logger.info(f"🔍 Debug: boto3 session created successfully")
        
        s3 = session.client('s3')
        logger.info(f"🔍 Debug: S3 client created successfully")
        
        # Create bucket (only once!)
        logger.info(f"🔍 Debug: About to create bucket...")
        try:
            if region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            logger.info(f"🔍 Debug: Bucket created successfully")
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"🔍 Debug: Bucket already exists and owned by us")
            else:
                raise
        
        # Remove public access block FIRST to allow public policies
        logger.info(f"🔍 Debug: Removing public access block...")
        try:
            s3.delete_public_access_block(Bucket=bucket_name)
            logger.info(f"🔍 Debug: Public access block removed")
        except ClientError as e:
            logger.warning(f"🔍 Debug: Could not remove public access block: {e}")
        
        # Configure for static website hosting
        logger.info(f"🔍 Debug: Configuring website hosting...")
        s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
        )
        logger.info(f"🔍 Debug: Website hosting configured")
        
        # Set bucket policy for public read access AFTER removing access block
        logger.info(f"🔍 Debug: Setting up public read access...")
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        logger.info(f"🔍 Debug: Public bucket policy applied")
        
        # Note: Bucket ACL removed as modern S3 buckets rely on bucket policies instead of ACLs
        logger.info(f"🔍 Debug: Using bucket policy for public access (ACLs disabled for security)")
        
        logger.info(f"✅ S3 bucket created with public read access: {bucket_name}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"❌ AWS S3 Error {error_code}: {error_message}")
        return False
    except NoCredentialsError:
        logger.error("❌ AWS credentials not found or invalid")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to create S3 bucket: {e}")
        return False

def sync_to_s3(local_dir: Path, bucket_name: str, credentials: Dict[str, str]) -> bool:
    """Sync local directory to S3 bucket with proper content types and public read access"""
    try:
        logger.info(f"🔄 Starting S3 sync from {local_dir} to s3://{bucket_name}")
        
        # Validate local directory exists and has files
        if not local_dir.exists():
            logger.error(f"❌ Local directory does not exist: {local_dir}")
            return False
        
        # Count files to upload
        all_files = list(local_dir.rglob("*"))
        files_to_upload = [f for f in all_files if f.is_file() and not any(excluded in str(f) for excluded in ['.git', '.DS_Store', 'Thumbs.db'])]
        
        logger.info(f"📊 Found {len(files_to_upload)} files to upload:")
        for f in files_to_upload[:10]:  # Show first 10 files
            relative_path = f.relative_to(local_dir)
            logger.info(f"   📄 {relative_path} ({f.stat().st_size} bytes)")
        if len(files_to_upload) > 10:
            logger.info(f"   ... and {len(files_to_upload) - 10} more files")
        
        # Set AWS credentials in environment
        env = {
            "AWS_ACCESS_KEY_ID": credentials["aws_access_key_id"],
            "AWS_SECRET_ACCESS_KEY": credentials["aws_secret_access_key"],
            "AWS_DEFAULT_REGION": credentials.get("aws_region", "us-east-1")
        }
        
        # Simplified AWS S3 sync command - removing potential timeout issues
        command = [
            "aws", "s3", "sync", 
            str(local_dir), 
            f"s3://{bucket_name}",
            "--delete"
        ]
        
        logger.info(f"🚀 Executing S3 sync command...")
        logger.info(f"   Command: {' '.join(command[:6])}... (credentials hidden)")
        
        success, stdout, stderr = run_command(command, Path.cwd(), env=env, timeout=600)  # 10 minute timeout
        
        if success:
            logger.info(f"✅ S3 sync completed successfully!")
            logger.info(f"📝 Sync output: {stdout}")
            
            # Verify upload by listing S3 bucket contents
            logger.info("🔍 Verifying S3 upload...")
            verify_command = ["aws", "s3", "ls", f"s3://{bucket_name}/", "--recursive"]
            
            verify_success, verify_stdout, verify_stderr = run_command(verify_command, Path.cwd(), env=env, timeout=60)
            
            if verify_success:
                # Count uploaded files
                s3_lines = [line for line in verify_stdout.split('\n') if line.strip()]
                logger.info(f"✅ Verification: {len(s3_lines)} files confirmed in S3:")
                
                # Show some uploaded files for confirmation
                for line in s3_lines[:10]:
                    logger.info(f"   📄 {line.split()[-1] if line.split() else 'unknown'}")
                if len(s3_lines) > 10:
                    logger.info(f"   ... and {len(s3_lines) - 10} more files in S3")
                    
                # Check if we uploaded the expected number of files
                if len(s3_lines) >= len(files_to_upload) * 0.9:  # Allow 10% tolerance
                    logger.info("✅ File count verification passed!")
                else:
                    logger.warning(f"⚠️ File count mismatch: Expected ~{len(files_to_upload)}, found {len(s3_lines)} in S3")
            else:
                logger.warning(f"⚠️ Could not verify S3 upload: {verify_stderr}")
                
        else:
            logger.error(f"❌ S3 sync failed!")
            logger.error(f"   Error output: {stderr}")
            logger.error(f"   Standard output: {stdout}")
            
            # Try to provide helpful error messages
            if "NoCredentialsError" in stderr:
                logger.error("🔑 AWS credentials issue - check your access key and secret key")
            elif "AccessDenied" in stderr:
                logger.error("🚫 AWS access denied - check your IAM permissions for S3")
            elif "NoSuchBucket" in stderr:
                logger.error(f"🪣 Bucket {bucket_name} does not exist or is not accessible")
            elif "timeout" in stderr.lower():
                logger.error("⏰ Upload timeout - files may be too large or connection too slow")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ S3 sync failed with exception: {e}")
        logger.error(f"   Local dir: {local_dir}")
        logger.error(f"   Bucket: {bucket_name}")
        return False

# JSON utilities
def read_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely read JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON file {file_path}: {e}")
        return None

def write_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Safely write JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to write JSON file {file_path}: {e}")
        return False

# Detection utilities
def find_files(directory: Path, patterns: List[str]) -> List[Path]:
    """Find files matching any of the given patterns"""
    found = []
    for pattern in patterns:
        found.extend(directory.glob(pattern))
    return found

def check_file_exists(directory: Path, filename: str) -> bool:
    """Check if a file exists in directory"""
    return (directory / filename).exists()

def get_file_content(file_path: Path, max_size: int = 10000) -> Optional[str]:
    """Get file content safely with size limit"""
    try:
        if file_path.stat().st_size > max_size:
            return None
            
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return None

def create_cloudfront_distribution(bucket_name: str, region: str, credentials: Dict[str, str]) -> Dict[str, str]:
    """Create CloudFront distribution for S3 bucket"""
    try:
        session = boto3.Session(
            aws_access_key_id=credentials["aws_access_key_id"],
            aws_secret_access_key=credentials["aws_secret_access_key"],
            region_name=region
        )
        
        cloudfront = session.client('cloudfront')
        
        # CloudFront distribution configuration
        distribution_config = {
            'CallerReference': str(uuid.uuid4()),
            'Comment': f'Static site distribution for {bucket_name}',
            'DefaultRootObject': 'index.html',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': f'{bucket_name}-origin',
                        'DomainName': f'{bucket_name}.s3-website-{region}.amazonaws.com',
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'http-only'
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': f'{bucket_name}-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': False,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0
            },
            'Enabled': True,
            'PriceClass': 'PriceClass_100'  # Use only US, Canada and Europe
        }
        
        logger.info(f"🌐 Creating CloudFront distribution for {bucket_name}")
        response = cloudfront.create_distribution(DistributionConfig=distribution_config)
        
        distribution_id = response['Distribution']['Id']
        cloudfront_url = response['Distribution']['DomainName']
        
        logger.info(f"✅ CloudFront distribution created: {distribution_id}")
        logger.info(f"🌐 CloudFront URL: https://{cloudfront_url}")
        
        return {
            "success": True,
            "distribution_id": distribution_id,
            "cloudfront_url": f"https://{cloudfront_url}",
            "status": "deploying"
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"❌ CloudFront Error {error_code}: {error_message}")
        return {"success": False, "error": f"CloudFront creation failed: {error_code} - {error_message}"}
    except Exception as e:
        logger.error(f"❌ Failed to create CloudFront distribution: {e}")
        return {"success": False, "error": f"CloudFront creation failed: {str(e)}"}

def ensure_static_website_ready(bucket_name: str, region: str, credentials: dict) -> None:
    """
    Idempotently turns an S3 bucket into a public static-website bucket:
    - Disables Block Public Access
    - Adds website configuration (index.html / error.html)
    - Attaches public-read bucket policy
    - Ensures placeholder index.html and error.html exist
    """

def create_nextjs_cloudfront_distribution(bucket_name: str, region: str, credentials: Dict[str, str]) -> Dict[str, str]:
    """Create CloudFront distribution optimized for Next.js apps with _next/* behavior"""
    try:
        session = boto3.Session(
            aws_access_key_id=credentials["aws_access_key_id"],
            aws_secret_access_key=credentials["aws_secret_access_key"],
            region_name=region
        )
        
        cloudfront = session.client('cloudfront')
        
        # S3 website endpoint format
        website_domain = f"{bucket_name}.s3-website-{region}.amazonaws.com"
        
        # Next.js optimized CloudFront distribution configuration
        distribution_config = {
            'CallerReference': f'codeflowops-nextjs-{bucket_name}-{str(uuid.uuid4())}',
            'Origins': {
                'Quantity': 1,
                'Items': [
                    {
                        'Id': 's3-website-origin',
                        'DomainName': website_domain,
                        'CustomOriginConfig': {
                            'HTTPPort': 80,
                            'HTTPSPort': 443,
                            'OriginProtocolPolicy': 'http-only',
                            'OriginSSLProtocols': {
                                'Quantity': 3,
                                'Items': ['TLSv1', 'TLSv1.1', 'TLSv1.2']
                            }
                        }
                    }
                ]
            },
            'DefaultCacheBehavior': {
                'TargetOriginId': 's3-website-origin',
                'ViewerProtocolPolicy': 'redirect-to-https',
                'TrustedSigners': {
                    'Enabled': False,
                    'Quantity': 0
                },
                'ForwardedValues': {
                    'QueryString': True,
                    'Cookies': {'Forward': 'none'}
                },
                'MinTTL': 0,
                'DefaultTTL': 60,
                'MaxTTL': 86400
            },
            'CacheBehaviors': {
                'Quantity': 1,
                'Items': [
                    {
                        'PathPattern': '/_next/*',
                        'TargetOriginId': 's3-website-origin',
                        'ViewerProtocolPolicy': 'redirect-to-https',
                        'TrustedSigners': {
                            'Enabled': False,
                            'Quantity': 0
                        },
                        'ForwardedValues': {
                            'QueryString': True,
                            'Cookies': {'Forward': 'none'}
                        },
                        'MinTTL': 0,
                        'DefaultTTL': 31536000,  # 1 year
                        'MaxTTL': 31536000
                    }
                ]
            },
            'CustomErrorResponses': {
                'Quantity': 2,
                'Items': [
                    {
                        'ErrorCode': 403,
                        'ResponsePagePath': '/index.html',
                        'ResponseCode': '200',
                        'ErrorCachingMinTTL': 10
                    },
                    {
                        'ErrorCode': 404,
                        'ResponsePagePath': '/index.html',
                        'ResponseCode': '200',
                        'ErrorCachingMinTTL': 10
                    }
                ]
            },
            'DefaultRootObject': 'index.html',
            'Comment': f'CodeFlowOps Next.js distribution for {bucket_name}',
            'Enabled': True,
            'PriceClass': 'PriceClass_100'  # Use only US, Canada and Europe
        }
        
        logger.info(f"🌐 Creating Next.js optimized CloudFront distribution for {bucket_name}")
        response = cloudfront.create_distribution(DistributionConfig=distribution_config)
        
        distribution_id = response['Distribution']['Id']
        cloudfront_url = response['Distribution']['DomainName']
        
        logger.info(f"✅ Next.js CloudFront distribution created: {distribution_id}")
        logger.info(f"🌐 Next.js CloudFront URL: https://{cloudfront_url}")
        
        return {
            "success": True,
            "distribution_id": distribution_id,
            "cloudfront_url": f"https://{cloudfront_url}",
            "status": "deploying"
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"❌ Next.js CloudFront Error {error_code}: {error_message}")
        return {"success": False, "error": f"Next.js CloudFront creation failed: {error_code} - {error_message}"}
    except Exception as e:
        logger.error(f"❌ Failed to create Next.js CloudFront distribution: {e}")
        return {"success": False, "error": f"Next.js CloudFront creation failed: {str(e)}"}

def create_cloudfront_invalidation(distribution_id: str, credentials: Dict[str, str], paths: List[str] = None) -> bool:
    """Create CloudFront invalidation for specified paths"""
    try:
        session = boto3.Session(
            aws_access_key_id=credentials["aws_access_key_id"],
            aws_secret_access_key=credentials["aws_secret_access_key"],
        )
        
        cloudfront = session.client('cloudfront')
        
        # Default to invalidating everything if no paths specified
        if paths is None:
            paths = ["/*"]
        
        response = cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': len(paths),
                    'Items': paths
                },
                'CallerReference': str(uuid.uuid4())
            }
        )
        
        invalidation_id = response['Invalidation']['Id']
        logger.info(f"✅ Created CloudFront invalidation: {invalidation_id} for paths: {paths}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create CloudFront invalidation: {e}")
        return False
    import json
    import time
    
    session = boto3.Session(
        aws_access_key_id=credentials["aws_access_key_id"],
        aws_secret_access_key=credentials["aws_secret_access_key"],
        aws_session_token=credentials.get("aws_session_token"),
        region_name=region,
    )
    s3 = session.client("s3")

    logger.info(f"🔧 Configuring S3 bucket for static website hosting: {bucket_name}")

    # 1) Disable Block Public Access (must be OFF before applying public policy)
    logger.info("🔓 Disabling Block Public Access...")
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
    )

    # Small wait to avoid eventual-consistency surprises on next calls
    time.sleep(1.0)

    # 2) Enable static website hosting
    logger.info("🌐 Enabling static website hosting...")
    try:
        s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "error.html"},
            },
        )
    except ClientError as e:
        # Surface useful context
        raise RuntimeError(f"put_bucket_website failed for {bucket_name}: {e}")

    # 3) Public-read bucket policy (objects must be world-readable for the website endpoint)
    logger.info("📝 Applying public-read bucket policy...")
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadForWebsite",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
        }]
    }

    # Retry around policy set in case PublicAccessBlock takes a moment to apply
    for attempt in range(3):
        try:
            s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(policy))
            break
        except ClientError as e:
            if attempt == 2:
                raise RuntimeError(f"put_bucket_policy failed for {bucket_name}: {e}")
            time.sleep(1.0)

    # 4) Ensure placeholder pages exist so site isn't empty
    logger.info("📄 Ensuring placeholder pages exist...")
    def _ensure_obj(key: str, body: bytes):
        try:
            s3.head_object(Bucket=bucket_name, Key=key)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NotFound"):
                s3.put_object(Bucket=bucket_name, Key=key, Body=body, ContentType="text/html")
            else:
                raise

    _ensure_obj("index.html", b"<!doctype html><h1>Static Site Deployed Successfully!</h1><p>This is a placeholder page. Your content will be uploaded here.</p>")
    _ensure_obj("error.html", b"<!doctype html><h1>Page Not Found</h1><p>The requested page could not be found.</p>")
    
    logger.info(f"✅ S3 bucket {bucket_name} is now configured for static website hosting")

def recommend_smart_stack(stack_cfg: dict, stack_type: str) -> dict:
    """Smart stack recommendation based on SSR requirements"""
    reasons = []
    needs_ssr = False

    if stack_type == "nextjs":
        if stack_cfg.get("requires_ssr"):
            needs_ssr = True; reasons.append("requires_ssr")
        if stack_cfg.get("has_server_deps"):
            needs_ssr = True; reasons.append("server_dependencies") 
        if stack_cfg.get("routing_type") == "app" and stack_cfg.get("has_dynamic_routes"):
            needs_ssr = True; reasons.append("app_router_dynamic_routes")
        if stack_cfg.get("api_routes"):
            needs_ssr = True; reasons.append("api_routes")

        if needs_ssr:
            logger.info(f"🚀 SSR required due to: {', '.join(reasons)}")
            return {
                "compute": "ECS Fargate + ALB",
                "container_registry": "ECR",
                "logs": "CloudWatch Logs", 
                "cdn": "CloudFront (optional, for /_next/static & /images)",
                "ssl": "ACM on ALB (or CloudFront if used)",
                "stack_type": "nextjs-ssr-ecs",
                "optimized_for": "Next.js SSR (App Router, dynamic routes, server deps)",
                "description": f"SSR required due to: {', '.join(reasons)}"
            }
        else:
            logger.info("📦 Static export suitable - no SSR requirements detected")
            return {
                "compute": "S3 + CloudFront + Build Process",
                "storage": "S3",
                "cdn": "CloudFront",
                "ssl": "AWS Certificate Manager",
                "stack_type": "nextjs-static-s3-cf",
                "optimized_for": "Next.js static export",
                "description": "Next.js static export pipeline"
            }
    
    # Default for non-Next.js projects
    return {
        "compute": "S3 + CloudFront" if stack_type in ["static"] else "S3 + CloudFront + Build Process",
        "storage": "S3",
        "cdn": "CloudFront", 
        "ssl": "AWS Certificate Manager",
        "stack_type": stack_type,
        "optimized_for": stack_type.upper() + " applications",
        "description": _get_stack_description(stack_type)
    }

def _get_stack_description(stack_type: str) -> str:
    """Get description for stack types"""
    descriptions = {
        "static": "Static site hosting",
        "nextjs": "Next.js application",
        "react": "React application", 
        "vue": "Vue.js application",
        "angular": "Angular application",
        "php": "PHP application",
        "laravel": "Laravel PHP framework",
        "wordpress": "WordPress CMS"
    }
    return descriptions.get(stack_type, f"{stack_type} application")
