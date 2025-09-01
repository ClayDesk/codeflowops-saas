# AWS Parameter Store Configuration Guide

This system eliminates the need to manually set Elastic Beanstalk environment variables by using AWS Systems Manager Parameter Store instead. Much easier to manage!

## 🚀 Quick Setup

### 1. One-time AWS Configuration Setup
```bash
cd backend
python setup_aws_config.py
```

This automatically configures all your production settings in AWS Parameter Store:
- GitHub OAuth credentials
- AWS Cognito settings  
- Frontend/API URLs
- CORS settings
- Environment configuration

### 2. Deploy to Elastic Beanstalk
```bash
.\deploy-backend.ps1
```

The deployment script now automatically:
1. Sets up AWS Parameter Store configuration
2. Creates the deployment package
3. Deploys to Elastic Beanstalk

## 🔧 Management Commands

### List all current parameters:
```bash
python setup_aws_config.py --list
```

### Test configuration:
```bash
python setup_aws_config.py --test
```

### Test OAuth integration:
```bash
python setup_aws_config.py --test-oauth
```

## 🎯 How It Works

### Development Mode
- Uses `.env` files and environment variables
- No AWS Parameter Store needed

### Production Mode (Elastic Beanstalk)
- Automatically detects `ENVIRONMENT=production`
- Loads configuration from AWS Parameter Store
- Falls back to environment variables if AWS unavailable

### Configuration Priority
1. **AWS Parameter Store** (production)
2. **AWS Secrets Manager** (sensitive data)
3. **Environment variables** (fallback)
4. **Default values**

## 📋 AWS Parameter Store Structure

All parameters are stored under:
```
/codeflowops/production/PARAMETER_NAME
```

### Parameters Set:
- `/codeflowops/production/GITHUB_CLIENT_ID`
- `/codeflowops/production/GITHUB_CLIENT_SECRET` (SecureString)
- `/codeflowops/production/COGNITO_USER_POOL_ID`
- `/codeflowops/production/COGNITO_CLIENT_ID`
- `/codeflowops/production/FRONTEND_URL`
- `/codeflowops/production/API_BASE_URL`
- `/codeflowops/production/CORS_ORIGINS`
- `/codeflowops/production/ENVIRONMENT`
- `/codeflowops/production/DEBUG`
- `/codeflowops/production/LOG_LEVEL`

## 🔐 Security Benefits

- **No hardcoded secrets** in deployment packages
- **Encrypted storage** for sensitive values (SecureString)
- **IAM permissions** control access
- **Audit trail** for configuration changes
- **Easy rotation** of secrets

## 🌐 Frontend Integration

Your GitHub OAuth flow will work with these URLs:

### GitHub OAuth App Configuration:
- **Authorization callback URL**: `https://api.codeflowops.com/api/v1/auth/github`

### Frontend OAuth Flow:
1. User clicks "Login with GitHub"
2. Frontend calls: `GET /api/v1/auth/github/authorize?redirect_uri=YOUR_FRONTEND_URL`
3. Backend generates GitHub authorization URL
4. User authorizes on GitHub
5. GitHub redirects to: `https://api.codeflowops.com/api/v1/auth/github`
6. Backend handles OAuth, stores user in Cognito
7. Backend redirects to frontend with tokens

### Example Frontend Code:
```javascript
// Initiate GitHub OAuth
const response = await fetch('/api/v1/auth/github/authorize?redirect_uri=' + 
  encodeURIComponent(window.location.origin + '/auth/callback'));
const { authorization_url } = await response.json();
window.location.href = authorization_url;

// Handle callback (in /auth/callback page)
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('success') === 'true') {
  const accessToken = urlParams.get('access_token');
  // Store token and redirect to dashboard
}
```

## 🚀 Deployment Process

### Before (Complex):
1. Manually set 10+ environment variables in EB console
2. Remember to update them when they change
3. Risk of typos and inconsistencies

### After (Simple):
1. Run `.\deploy-backend.ps1`
2. Everything is automated!

## 📊 Production URLs

- **Backend API**: https://api.codeflowops.com
- **Frontend**: https://main.d3f9i8qr0q8s2a.amplifyapp.com
- **GitHub OAuth Callback**: https://api.codeflowops.com/api/v1/auth/github

## 🔄 Updating Configuration

To update any configuration value:

```bash
# Update a specific parameter
python -c "
from src.config.aws_config import config_manager
config_manager.set_parameter('FRONTEND_URL', 'https://new-frontend-url.com')
"
```

Or modify `setup_aws_config.py` and run it again.

## 🧪 Testing Production Config Locally

Set environment variable to test production config locally:
```bash
$env:ENVIRONMENT = "production"
python test_github_oauth.py
```

This will use AWS Parameter Store instead of local .env files.

---

**No more manual EB environment variable setup! 🎉**
