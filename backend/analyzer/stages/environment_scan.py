"""
Stage 4: Environment & Secrets Scan
Comprehensive environment variable and secret detection with redaction
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Pattern
import logging
import json

from ..contracts import AnalysisContext, SecretMatch

logger = logging.getLogger(__name__)

class EnvironmentScanStage:
    """
    Environment and secrets scanning stage
    
    Responsibilities:
    - Scan .env* files for environment variables
    - Detect and redact secrets (AWS keys, API tokens, etc.)
    - Analyze configuration files
    - Build environment requirements map
    """
    
    # Secret detection patterns
    SECRET_PATTERNS = {
        "AWS_ACCESS_KEY_ID": re.compile(r'\b(AKIA|ASIA)[A-Z0-9]{16}\b'),
        "AWS_SECRET_ACCESS_KEY": re.compile(r'(?i)aws(.{0,20})?(secret|key).{0,10}[:=]\s*["\']?([A-Za-z0-9/+=]{40,})["\']?'),
        "GITHUB_TOKEN": re.compile(r'ghp_[A-Za-z0-9]{36,}'),
        "GITHUB_PAT": re.compile(r'github_pat_[A-Za-z0-9_]{82}'),
        "STRIPE_SECRET_KEY": re.compile(r'sk_(live|test)_[A-Za-z0-9]{20,}'),
        "STRIPE_PUBLISHABLE_KEY": re.compile(r'pk_(live|test)_[A-Za-z0-9]{20,}'),
        "TWILIO_ACCOUNT_SID": re.compile(r'\bAC[a-f0-9]{32}\b', re.I),  # Twilio Account SID
        "TWILIO_AUTH_TOKEN": re.compile(r'(?i)(?:twilio.{0,10}(?:auth.{0,5})?token|auth.{0,5}token).{0,10}[:=]\s*["\']?([a-f0-9]{32})["\']?'),  # Context-dependent with literal value
        "SENDGRID_API_KEY": re.compile(r'SG\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{40,}'),
        "JWT_SECRET": re.compile(r'(?i)jwt.{0,10}(secret|key).{0,10}[:=]\s*["\']?([A-Za-z0-9+/=]{20,})["\']?'),
        "DATABASE_URL": re.compile(r'(?i)(postgres|mysql|mongodb)://[^\\s"\']+'),
        "REDIS_URL": re.compile(r'redis://[^\\s"\']+'),
        "FIREBASE_PRIVATE_KEY": re.compile(r'-----BEGIN PRIVATE KEY-----[\\s\\S]*-----END PRIVATE KEY-----'),
        "GOOGLE_CLIENT_SECRET": re.compile(r'GOCSPX-[A-Za-z0-9_-]{28}'),
        "SLACK_BOT_TOKEN": re.compile(r'xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+'),
        "FACEBOOK_APP_SECRET": re.compile(r'[0-9a-f]{32}'),  # Context-dependent
        "TWITTER_API_SECRET": re.compile(r'[A-Za-z0-9]{50}'),  # Context-dependent
        "PRIVATE_KEY": re.compile(r'-----BEGIN (?:RSA )?PRIVATE KEY-----[\\s\\S]*-----END (?:RSA )?PRIVATE KEY-----'),
        "API_KEY_GENERIC": re.compile(r'(?i)(api.{0,10}key|key).{0,10}[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?'),
        "PASSWORD": re.compile(r'(?i)(password|pwd).{0,10}[:=]\s*["\']?([^\\s"\']{8,})["\']?'),
        "TOKEN_GENERIC": re.compile(r'(?i)token.{0,10}[:=]\s*["\']?([A-Za-z0-9_-]{20,})["\']?')
    }
    
    # Environment file patterns
    ENV_FILE_PATTERNS = [
        '.env',
        '.env.local',
        '.env.development', 
        '.env.production',
        '.env.staging',
        '.env.test',
        '.env.example',
        '.env.sample',
        '.env.template',
        'config/.env*',
        'site/.env*'
    ]
    
    # Configuration files that might contain secrets
    CONFIG_FILES = [
        'config.json',
        'config.js',
        'config.ts',
        'app.json',
        'app.config.js',
        'next.config.js',
        'nuxt.config.js',
        'gatsby-config.js',
        'serverless.yml',
        'serverless.yaml',
        'docker-compose.yml',
        'docker-compose.yaml'
    ]
    
    async def analyze(self, context: AnalysisContext):
        """Run environment and secrets analysis"""
        logger.info(f"🔒 Scanning for environment variables and secrets...")
        
        env_analysis = {
            "env_files": [],
            "variables": {},
            "secrets": [],
            "config_files": [],
            "integrations_detected": [],
            "security_risks": []
        }
        
        # 1. Find and analyze environment files
        await self._scan_env_files(context, env_analysis)
        
        # 2. Scan configuration files
        await self._scan_config_files(context, env_analysis)
        
        # 3. Scan source code for hardcoded secrets
        await self._scan_source_code_secrets(context, env_analysis)
        
        # 4. Analyze integrations from environment variables
        self._analyze_integrations_from_env(env_analysis)
        
        # 5. Assess security risks
        self._assess_security_risks(env_analysis)
        
        # Store results
        context.intelligence_profile["env"] = env_analysis
        
        logger.info(f"✅ Environment scan complete: {len(env_analysis['env_files'])} env files, {len(env_analysis['secrets'])} secrets found")
    
    async def _scan_env_files(self, context: AnalysisContext, env_analysis: Dict[str, Any]):
        """Scan .env files for variables and secrets"""
        for file_metadata in context.files:
            file_path = context.repo_path / file_metadata["path"]
            
            # Check if this looks like an env file
            if (file_metadata["name"].startswith('.env') or 
                'env' in file_metadata["path"].lower() and file_metadata["extension"] in ['.env', '']):
                
                await self._analyze_env_file(file_path, file_metadata, env_analysis)
    
    async def _analyze_env_file(self, file_path: Path, file_metadata: Dict, env_analysis: Dict[str, Any]):
        """Analyze individual environment file"""
        try:
            with open(file_path, 'r', encoding=file_metadata.get('encoding', 'utf-8'), errors='ignore') as f:
                content = f.read()
            
            env_file_info = {
                "path": file_metadata["path"],
                "variables": {},
                "secrets": [],
                "lines": content.count('\n') + 1
            }
            
            # Parse environment variables
            for line_num, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if key and value:
                        # Store variable (without value for privacy)
                        env_file_info["variables"][key] = {
                            "has_value": bool(value.strip()),
                            "line": line_num,
                            "type": self._classify_env_variable(key, value)
                        }
                        
                        # Check for secrets
                        secret_matches = self._scan_line_for_secrets(line, file_metadata["path"], line_num)
                        if secret_matches:
                            env_file_info["secrets"].extend(secret_matches)
                            env_analysis["secrets"].extend(secret_matches)
            
            env_analysis["env_files"].append(env_file_info)
            
        except Exception as e:
            logger.warning(f"Failed to analyze env file {file_path}: {e}")
    
    async def _scan_config_files(self, context: AnalysisContext, env_analysis: Dict[str, Any]):
        """Scan configuration files for secrets"""
        for file_metadata in context.files:
            if (file_metadata["name"] in self.CONFIG_FILES or 
                any(pattern in file_metadata["path"] for pattern in ['config/', 'settings/'])):
                
                file_path = context.repo_path / file_metadata["path"]
                await self._analyze_config_file(file_path, file_metadata, env_analysis)
    
    async def _analyze_config_file(self, file_path: Path, file_metadata: Dict, env_analysis: Dict[str, Any]):
        """Analyze configuration file for secrets"""
        try:
            with open(file_path, 'r', encoding=file_metadata.get('encoding', 'utf-8'), errors='ignore') as f:
                content = f.read()
            
            config_info = {
                "path": file_metadata["path"],
                "type": file_metadata["extension"],
                "secrets": [],
                "env_references": []
            }
            
            # Scan for secrets
            for line_num, line in enumerate(content.splitlines(), 1):
                secret_matches = self._scan_line_for_secrets(line, file_metadata["path"], line_num)
                if secret_matches:
                    config_info["secrets"].extend(secret_matches)
                    env_analysis["secrets"].extend(secret_matches)
                
                # Look for environment variable references
                env_refs = re.findall(r'process\.env\.([A-Z_][A-Z0-9_]*)', line)
                env_refs.extend(re.findall(r'\\$\\{?([A-Z_][A-Z0-9_]*)\\}?', line))
                if env_refs:
                    config_info["env_references"].extend(env_refs)
            
            if config_info["secrets"] or config_info["env_references"]:
                env_analysis["config_files"].append(config_info)
                
        except Exception as e:
            logger.warning(f"Failed to analyze config file {file_path}: {e}")
    
    async def _scan_source_code_secrets(self, context: AnalysisContext, env_analysis: Dict[str, Any]):
        """Scan source code files for hardcoded secrets"""
        source_extensions = {'.js', '.jsx', '.ts', '.tsx', '.py', '.php', '.rb', '.go', '.java', '.cs'}
        
        for file_metadata in context.files:
            if (file_metadata["extension"] in source_extensions and 
                not file_metadata["is_binary"] and 
                file_metadata["size"] < 1024 * 1024):  # Skip files > 1MB
                
                file_path = context.repo_path / file_metadata["path"]
                await self._scan_source_file_secrets(file_path, file_metadata, env_analysis)
    
    async def _scan_source_file_secrets(self, file_path: Path, file_metadata: Dict, env_analysis: Dict[str, Any]):
        """Scan individual source file for secrets"""
        try:
            with open(file_path, 'r', encoding=file_metadata.get('encoding', 'utf-8'), errors='ignore') as f:
                content = f.read()
            
            # Skip if file is too large or seems minified
            if len(content) > 500000 or (len(content.splitlines()) == 1 and len(content) > 10000):
                return
            
            for line_num, line in enumerate(content.splitlines(), 1):
                secret_matches = self._scan_line_for_secrets(line, file_metadata["path"], line_num)
                if secret_matches:
                    env_analysis["secrets"].extend(secret_matches)
                    
        except Exception as e:
            logger.debug(f"Failed to scan source file {file_path}: {e}")
    
    def _scan_line_for_secrets(self, line: str, file_path: str, line_num: int) -> List[SecretMatch]:
        """Scan a line for secret patterns"""
        secrets = []
        
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            matches = pattern.finditer(line)
            for match in matches:
                secret_value = match.group(0)
                
                # Skip obvious false positives
                if self._is_false_positive(secret_type, secret_value, line):
                    continue
                
                secrets.append({
                    "type": secret_type,
                    "location": f"{file_path}:{line_num}",
                    "preview": self._redact_secret(secret_value),
                    "risk": self._assess_secret_risk(secret_type, secret_value),
                    "pattern_matched": pattern.pattern[:50]  # First 50 chars of pattern
                })
        
        return secrets
    
    def _redact_secret(self, secret: str) -> str:
        """Redact secret value for safe storage"""
        if len(secret) <= 8:
            return "****"
        elif len(secret) <= 16:
            return secret[:4] + "****"
        else:
            return secret[:6] + "****" + secret[-4:]
    
    def _assess_secret_risk(self, secret_type: str, secret_value: str) -> str:
        """Assess risk level of detected secret"""
        high_risk_types = {
            "AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN", "GITHUB_PAT", 
            "STRIPE_SECRET_KEY", "PRIVATE_KEY", "FIREBASE_PRIVATE_KEY"
        }
        
        medium_risk_types = {
            "AWS_ACCESS_KEY_ID", "STRIPE_PUBLISHABLE_KEY", "JWT_SECRET",
            "SENDGRID_API_KEY", "TWILIO_AUTH_TOKEN"
        }
        
        if secret_type in high_risk_types:
            return "high"
        elif secret_type in medium_risk_types:
            return "medium"
        else:
            return "low"
    
    def _is_false_positive(self, secret_type: str, secret_value: str, line: str) -> bool:
        """Check if detected secret is likely a false positive"""
        
        # Skip comments and README content
        line_stripped = line.strip()
        if (line_stripped.startswith('//') or 
            line_stripped.startswith('#') or 
            line_stripped.startswith('/*') or
            '/*' in line_stripped and '*/' in line_stripped):
            return True
        
        # Skip examples, placeholders, and test data
        false_positive_indicators = [
            'example', 'placeholder', 'test', 'fake', 'dummy', 'sample',
            'your_key_here', 'insert_key', 'add_your', 'replace_with',
            'todo', 'fixme', 'xxx', 'change_me'
        ]
        
        line_lower = line.lower()
        secret_lower = secret_value.lower()
        
        # General false positive check
        if any(indicator in line_lower or indicator in secret_lower 
               for indicator in false_positive_indicators):
            return True
        
        # Twilio-specific false positive detection
        if secret_type in ['TWILIO_AUTH_TOKEN', 'TWILIO_ACCOUNT_SID']:
            # Skip if it's just a variable name without a real token value
            if not re.search(r'[:=]\s*["\']?([a-f0-9]{32}|AC[a-f0-9]{32})["\']?', line):
                return True
            
            # Skip obvious placeholders
            twilio_placeholders = [
                'your_twilio_auth_token', 'twilio_auth_token', 'your_auth_token',
                'your_account_sid', 'your_twilio_sid', 'twilio_account_sid'
            ]
            if any(placeholder in secret_lower for placeholder in twilio_placeholders):
                return True
        
        # Must have a string literal assignment, not just identifier
        if secret_type in ['TWILIO_AUTH_TOKEN', 'PASSWORD', 'API_KEY_GENERIC', 'TOKEN_GENERIC']:
            # Require actual assignment with quotes or equals
            if not re.search(r'[:=]\s*["\']([^"\']+)["\']', line):
                return True
        
        return False
    
    def _classify_env_variable(self, key: str, value: str) -> str:
        """Classify environment variable by type"""
        key_lower = key.lower()
        
        if 'database' in key_lower or 'db_' in key_lower or key_lower.endswith('_url') and 'postgres' in value.lower():
            return "database"
        elif 'api' in key_lower and 'key' in key_lower:
            return "api_key"
        elif 'secret' in key_lower or 'token' in key_lower:
            return "secret"
        elif key_lower.startswith('next_public_') or key_lower.startswith('react_app_'):
            return "public"
        elif 'port' in key_lower or key_lower.endswith('_port'):
            return "port"
        elif 'host' in key_lower or key_lower.endswith('_host'):
            return "host"
        else:
            return "config"
    
    def _analyze_integrations_from_env(self, env_analysis: Dict[str, Any]):
        """Detect integrations from environment variables"""
        integrations = set()
        
        # Collect all environment variable keys
        all_env_keys = []
        for env_file in env_analysis["env_files"]:
            all_env_keys.extend(env_file["variables"].keys())
        
        # Pattern matching for known integrations
        integration_patterns = {
            "stripe": ["STRIPE_", "NEXT_PUBLIC_STRIPE"],
            "aws": ["AWS_", "S3_", "LAMBDA_"],
            "sendgrid": ["SENDGRID_"],
            "twilio": ["TWILIO_"],
            "google": ["GOOGLE_", "GMAIL_", "GCLOUD_"],
            "firebase": ["FIREBASE_"],
            "auth0": ["AUTH0_"],
            "clerk": ["CLERK_"],
            "supabase": ["SUPABASE_"],
            "vercel": ["VERCEL_"],
            "netlify": ["NETLIFY_"],
            "mongodb": ["MONGO_", "MONGODB_"],
            "redis": ["REDIS_"],
            "elasticsearch": ["ELASTIC_"],
            "sentry": ["SENTRY_"],
            "segment": ["SEGMENT_"],
            "mixpanel": ["MIXPANEL_"],
            "mailgun": ["MAILGUN_"],
            "slack": ["SLACK_"]
        }
        
        for key in all_env_keys:
            for integration, patterns in integration_patterns.items():
                if any(pattern in key for pattern in patterns):
                    integrations.add(integration)
                    break
        
        env_analysis["integrations_detected"] = list(integrations)
    
    def _assess_security_risks(self, env_analysis: Dict[str, Any]):
        """Assess security risks from environment analysis"""
        risks = []
        
        # High-risk secrets exposed
        high_risk_secrets = [s for s in env_analysis["secrets"] if s["risk"] == "high"]
        if high_risk_secrets:
            risks.append({
                "type": "high_risk_secrets_exposed",
                "severity": "high",
                "count": len(high_risk_secrets),
                "locations": [s["location"] for s in high_risk_secrets[:5]],  # First 5
                "note": f"Found {len(high_risk_secrets)} high-risk secrets in code"
            })
        
        # Missing environment files
        env_example_exists = any('.env.example' in f["path"] for f in env_analysis["env_files"])
        env_files_exist = any(not f["path"].endswith('.example') for f in env_analysis["env_files"])
        
        if not env_example_exists and env_files_exist:
            risks.append({
                "type": "missing_env_example",
                "severity": "medium",
                "note": "No .env.example file found - developers won't know required variables"
            })
        
        env_analysis["security_risks"] = risks
