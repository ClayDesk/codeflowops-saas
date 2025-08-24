"""
Production Cognito Configuration Recommendations
For handling thousands of concurrent users
"""

PRODUCTION_COGNITO_SETTINGS = {
    # User Pool Settings
    "user_pool": {
        "policies": {
            "password_policy": {
                "minimum_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_symbols": True,
                "temporary_password_validity_days": 7
            }
        },
        "lambda_config": {
            # Use Lambda triggers for custom authentication flows
            "pre_sign_up": "arn:aws:lambda:us-east-1:ACCOUNT:function:cognito-pre-signup",
            "post_confirmation": "arn:aws:lambda:us-east-1:ACCOUNT:function:cognito-post-confirmation",
            "pre_authentication": "arn:aws:lambda:us-east-1:ACCOUNT:function:cognito-pre-auth"
        },
        "mfa_configuration": "OPTIONAL",  # Enable MFA for enhanced security
        "account_recovery_setting": {
            "recovery_mechanisms": [
                {"name": "verified_email", "priority": 1},
                {"name": "verified_phone_number", "priority": 2}
            ]
        }
    },
    
    # App Client Settings for High Throughput
    "app_client": {
        "client_name": "CodeFlowOps-Production",
        "generate_secret": True,  # Use client secret for enhanced security
        "supported_identity_providers": ["COGNITO", "Google", "GitHub"],
        "callback_urls": [
            "https://codeflowops.com/auth/callback",
            "https://api.codeflowops.com/auth/callback"
        ],
        "logout_urls": [
            "https://codeflowops.com/auth/logout",
            "https://api.codeflowops.com/auth/logout"
        ],
        "oauth_flows": ["code", "implicit"],
        "oauth_scopes": ["openid", "profile", "email"],
        "explicit_auth_flows": [
            "ADMIN_NO_SRP_AUTH",  # Required for server-side authentication
            "USER_SRP_AUTH",      # For client-side authentication
            "ALLOW_REFRESH_TOKEN_AUTH"
        ],
        "token_validity_units": {
            "access_token": "hours",
            "id_token": "hours",
            "refresh_token": "days"
        },
        "token_validity": {
            "access_token": 1,    # 1 hour for security
            "id_token": 1,        # 1 hour for security
            "refresh_token": 30   # 30 days for user convenience
        }
    },
    
    # Domain Configuration
    "domain": {
        "domain_name": "auth-codeflowops",  # Custom domain for better branding
        "certificate_arn": "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID"
    },
    
    # Production Scaling Recommendations
    "scaling": {
        "max_concurrent_sessions": 50000,  # Cognito can handle this scale
        "rate_limits": {
            "sign_in": "100 per minute per IP",
            "sign_up": "20 per minute per IP",
            "password_reset": "5 per minute per IP"
        },
        "monitoring": {
            "cloudwatch_alarms": [
                "SignInSuccessRate < 95%",
                "UserRegistrationErrors > 100/hour",
                "TokenValidationLatency > 500ms"
            ]
        }
    }
}

# AWS CLI Commands to Configure Production Cognito
AWS_CLI_COMMANDS = """
# 1. Create User Pool with Production Settings
aws cognito-idp create-user-pool \
  --pool-name "CodeFlowOps-Production" \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 12,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true,
      "TemporaryPasswordValidityDays": 7
    }
  }' \
  --mfa-configuration "OPTIONAL" \
  --account-recovery-setting '{
    "RecoveryMechanisms": [
      {"Name": "verified_email", "Priority": 1}
    ]
  }' \
  --user-pool-tags '{"Environment": "Production", "Application": "CodeFlowOps"}'

# 2. Create App Client with Production Settings
aws cognito-idp create-user-pool-client \
  --user-pool-id "us-east-1_XXXXXXXXX" \
  --client-name "CodeFlowOps-Production" \
  --generate-secret \
  --supported-identity-providers "COGNITO" "Google" "GitHub" \
  --callback-urls "https://codeflowops.com/auth/callback" \
  --logout-urls "https://codeflowops.com/auth/logout" \
  --allowed-o-auth-flows "code" "implicit" \
  --allowed-o-auth-scopes "openid" "profile" "email" \
  --explicit-auth-flows "ADMIN_NO_SRP_AUTH" "USER_SRP_AUTH" "ALLOW_REFRESH_TOKEN_AUTH" \
  --token-validity-units '{
    "AccessToken": "hours",
    "IdToken": "hours", 
    "RefreshToken": "days"
  }' \
  --access-token-validity 1 \
  --id-token-validity 1 \
  --refresh-token-validity 30

# 3. Create Custom Domain (Optional)
aws cognito-idp create-user-pool-domain \
  --domain "auth-codeflowops" \
  --user-pool-id "us-east-1_XXXXXXXXX" \
  --custom-domain-config '{
    "CertificateArn": "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT_ID"
  }'

# 4. Set up CloudWatch Alarms for Monitoring
aws cloudwatch put-metric-alarm \
  --alarm-name "CognitoHighErrorRate" \
  --alarm-description "High error rate in Cognito authentication" \
  --metric-name "SignInErrors" \
  --namespace "AWS/Cognito" \
  --statistic Sum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
"""

# Environment Variables for Production
PRODUCTION_ENV_VARS = {
    "COGNITO_USER_POOL_ID": "us-east-1_lWcaQdyeZ",  # Your existing pool
    "COGNITO_CLIENT_ID": "3d0gm6gtv4ia8vonloc38q8nkt",  # Your existing client
    "COGNITO_CLIENT_SECRET": "YOUR_CLIENT_SECRET",  # Add client secret for security
    "COGNITO_REGION": "us-east-1",
    "COGNITO_DOMAIN": "auth-codeflowops.auth.us-east-1.amazoncognito.com",
    
    # Production Redis for Caching
    "REDIS_URL": "redis://production-redis-cluster:6379",
    
    # Rate Limiting Settings
    "AUTH_RATE_LIMIT_REQUESTS": "100",  # requests per minute
    "AUTH_RATE_LIMIT_WINDOW": "60",     # seconds
    
    # Monitoring
    "ENABLE_AUTH_METRICS": "true",
    "LOG_LEVEL": "INFO"
}
