# GitHub OAuth Application Configuration Update

## Current Issue
The GitHub OAuth application is configured with localhost callback URLs which don't work in production.

## Required GitHub OAuth App Settings

### 1. Go to GitHub OAuth App Settings
- Navigate to: https://github.com/settings/applications
- Find your OAuth App (Client ID: Ov23li4xEOeDgSAMz2rg)
- Click "Edit"

### 2. Update Callback URLs
Add these production callback URLs to your GitHub OAuth app:

**Authorization callback URLs:**
```
https://api.codeflowops.com/auth/github/callback
https://codeflowops.com/auth/github/callback
```

Keep the localhost URLs for development:
```
http://localhost:8000/auth/github/callback
http://localhost:3000/auth/github/callback
```

### 3. Update Homepage URL
**Homepage URL:**
```
https://codeflowops.com
```

### 4. Update Application description
**Application name:** CodeFlowOps
**Application description:** Repository analysis and deployment automation platform
**Homepage URL:** https://codeflowops.com

## Complete Configuration Should Look Like:

**Application name:** CodeFlowOps
**Homepage URL:** https://codeflowops.com
**Application description:** Repository analysis and deployment automation platform

**Authorization callback URLs:**
- https://api.codeflowops.com/auth/github/callback
- https://codeflowops.com/auth/github/callback  
- http://localhost:8000/auth/github/callback (for development)
- http://localhost:3000/auth/github/callback (for development)

## After Updating GitHub Settings

Wait for the Elastic Beanstalk environment to finish updating (about 2-3 minutes), then test:

1. Visit: https://codeflowops.com
2. Click "Continue with GitHub" 
3. Should redirect to GitHub OAuth properly
4. After authorization, should redirect back to CodeFlowOps

## Verification Commands

Test the updated configuration:
```bash
# Check if environment variables are updated
curl https://api.codeflowops.com/auth/github/health

# Test GitHub OAuth initiation
curl https://api.codeflowops.com/auth/github
```

The health endpoint should now show:
```json
{
  "status": "healthy",
  "service": "github_auth", 
  "github_client_configured": true,
  "callback_url": "https://api.codeflowops.com/auth/github/callback",
  "cognito_available": true
}
```
