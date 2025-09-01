# GitHub OAuth Integration with AWS Cognito

This implementation provides a robust GitHub OAuth authentication system that stores user credentials in AWS Cognito, allowing users to log in easily using their GitHub accounts.

## Features

- ✅ GitHub OAuth 2.0 authentication
- ✅ Automatic user creation in AWS Cognito
- ✅ User profile synchronization
- ✅ JWT token generation
- ✅ Secure credential storage
- ✅ Frontend redirect handling
- ✅ Error handling and logging

## Architecture

```
GitHub OAuth Flow:
1. User clicks "Login with GitHub" on frontend
2. Frontend redirects to /api/v1/auth/github/authorize
3. Backend generates GitHub authorization URL
4. User authorizes on GitHub
5. GitHub redirects to /api/v1/auth/github callback
6. Backend exchanges code for GitHub access token
7. Backend fetches user info from GitHub API
8. Backend creates/updates user in AWS Cognito
9. Backend generates JWT tokens
10. User is redirected to frontend with authentication tokens
```

## Configuration

### 1. Environment Variables

Add these to your `.env` file:

```bash
# GitHub OAuth Settings
GITHUB_CLIENT_ID=Ov23li4xEOeDgSAMz2rg
GITHUB_CLIENT_SECRET=b112410a2cd2fd6c8f395673cfb1f26503edbed7

# AWS Cognito Settings (existing)
AWS_REGION=us-east-1
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id
COGNITO_CLIENT_SECRET=your-client-secret  # Optional

# Frontend URL
FRONTEND_URL=https://codeflowops.com
```

### 2. AWS Cognito Custom Attributes

Ensure your Cognito User Pool has these custom attributes configured:

- `custom:oauth_github_id` (String, Mutable)
- `custom:oauth_github_username` (String, Mutable)
- `custom:auth_provider` (String, Mutable)
- `custom:oauth_profile` (String, Mutable)

### 3. GitHub OAuth App Configuration

In your GitHub OAuth app settings:
- **Application name**: codeflowops local
- **Homepage URL**: https://codeflowops.com
- **Authorization callback URL**: https://api.codeflowops.com/api/v1/auth/github

## API Endpoints

### 1. Get Authorization URL

```http
GET /api/v1/auth/github/authorize?redirect_uri=https://codeflowops.com/auth/callback
```

Response:
```json
{
  "authorization_url": "https://github.com/login/oauth/authorize?client_id=...",
  "state": "uuid-state-value"
}
```

### 2. OAuth Callback (Automatic)

```http
GET /api/v1/auth/github?code=xxx&state=xxx
```

This endpoint automatically handles the GitHub callback and redirects to frontend.

### 3. Manual Code Exchange

```http
POST /api/v1/auth/github/exchange
Content-Type: application/json

{
  "code": "github-authorization-code",
  "redirect_uri": "https://api.codeflowops.com/api/v1/auth/github",
  "state": "optional-state"
}
```

Response:
```json
{
  "success": true,
  "message": "GitHub authentication successful",
  "user": {
    "user_id": "cognito-user-id",
    "email": "user@example.com",
    "username": "github-username",
    "full_name": "User Full Name"
  },
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "expires_in": 3600,
  "cognito_integrated": true
}
```

### 4. Get GitHub User Info

```http
GET /api/v1/auth/github/user?access_token=github-access-token
```

### 5. Link GitHub to Existing User

```http
POST /api/v1/auth/github/link
Content-Type: application/json

{
  "cognito_username": "existing-user@example.com",
  "github_access_token": "github-access-token"
}
```

## Frontend Integration

### React/Next.js Example

```javascript
// 1. Initiate OAuth flow
const initiateGitHubLogin = async () => {
  try {
    const response = await fetch('/api/v1/auth/github/authorize?redirect_uri=' + 
      encodeURIComponent(window.location.origin + '/auth/callback'));
    const data = await response.json();
    
    // Redirect to GitHub
    window.location.href = data.authorization_url;
  } catch (error) {
    console.error('GitHub login error:', error);
  }
};

// 2. Handle callback (in /auth/callback page)
const handleAuthCallback = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const success = urlParams.get('success');
  const error = urlParams.get('error');
  
  if (success === 'true') {
    const accessToken = urlParams.get('access_token');
    const userEmail = urlParams.get('email');
    
    // Store tokens and redirect to dashboard
    localStorage.setItem('authToken', accessToken);
    router.push('/dashboard');
  } else if (error) {
    console.error('Authentication error:', error);
    // Show error message to user
  }
};
```

### Button Component

```jsx
const GitHubLoginButton = () => {
  const handleLogin = async () => {
    try {
      const response = await fetch('/api/v1/auth/github/authorize?redirect_uri=' + 
        encodeURIComponent(window.location.origin + '/auth/callback'));
      const data = await response.json();
      window.location.href = data.authorization_url;
    } catch (error) {
      console.error('GitHub login failed:', error);
    }
  };

  return (
    <button 
      onClick={handleLogin}
      className="flex items-center gap-2 bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800"
    >
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
      </svg>
      Continue with GitHub
    </button>
  );
};
```

## User Data Storage in Cognito

When a user logs in with GitHub, the following data is stored in AWS Cognito:

### Standard Attributes
- `email`: User's GitHub email
- `name`: User's full name from GitHub
- `email_verified`: Set to `true`

### Custom Attributes
- `custom:oauth_github_id`: GitHub user ID
- `custom:oauth_github_username`: GitHub username
- `custom:auth_provider`: Set to `oauth_github`
- `custom:oauth_profile`: JSON string with GitHub profile data

### Example Cognito User Attributes
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "email_verified": "true",
  "custom:oauth_github_id": "12345678",
  "custom:oauth_github_username": "johndoe",
  "custom:auth_provider": "oauth_github",
  "custom:oauth_profile": "{\"id\":12345678,\"login\":\"johndoe\",\"avatar_url\":\"https://avatars.githubusercontent.com/u/12345678\"}"
}
```

## Security Features

1. **State Parameter**: CSRF protection using state parameter
2. **Secure Token Storage**: Proper JWT token generation and validation
3. **Error Handling**: Comprehensive error handling and logging
4. **Redirect Validation**: Secure redirect URI validation
5. **Token Expiration**: Proper token expiration and refresh handling

## Error Handling

The system handles various error scenarios:

- Invalid authorization codes
- GitHub API errors
- Cognito integration failures
- Network timeouts
- Invalid redirect URIs

All errors are logged and appropriate error messages are returned to the frontend.

## Testing

### Test the OAuth Flow

1. **Local Development**:
   ```bash
   # Start the backend server
   python -m uvicorn src.main:app --reload --port 8000
   
   # Test authorization URL generation
   curl "http://localhost:8000/api/v1/auth/github/authorize?redirect_uri=http://localhost:3000/auth/callback"
   ```

2. **Production Testing**:
   - Ensure GitHub OAuth app is configured with production URLs
   - Test complete flow from frontend to callback
   - Verify user creation in Cognito console

### Manual Testing Steps

1. Navigate to `/api/v1/auth/github/authorize?redirect_uri=YOUR_FRONTEND_URL`
2. Complete GitHub authorization
3. Verify redirect to frontend with tokens
4. Check Cognito User Pool for new user
5. Verify user attributes are populated correctly

## Troubleshooting

### Common Issues

1. **Invalid Client ID/Secret**:
   - Verify GitHub OAuth app configuration
   - Check environment variables

2. **Redirect URI Mismatch**:
   - Ensure callback URL matches GitHub app configuration
   - Use exact URL including protocol and port

3. **Cognito Errors**:
   - Verify AWS credentials and permissions
   - Check Cognito User Pool configuration
   - Ensure custom attributes are created

4. **CORS Issues**:
   - Configure CORS settings in backend
   - Verify frontend and backend URLs

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

This will provide detailed logs of the OAuth flow and Cognito integration.

## Production Deployment

### Environment Variables Checklist

- [ ] `GITHUB_CLIENT_ID` - Production GitHub app client ID
- [ ] `GITHUB_CLIENT_SECRET` - Production GitHub app client secret
- [ ] `AWS_REGION` - AWS region for Cognito
- [ ] `COGNITO_USER_POOL_ID` - Production Cognito User Pool ID
- [ ] `COGNITO_CLIENT_ID` - Production Cognito App Client ID
- [ ] `FRONTEND_URL` - Production frontend URL

### Security Considerations

1. **HTTPS Only**: Ensure all URLs use HTTPS in production
2. **Secret Management**: Use AWS Secrets Manager for sensitive values
3. **Token Security**: Implement proper token storage and validation
4. **Rate Limiting**: Add rate limiting to OAuth endpoints
5. **Monitoring**: Set up CloudWatch monitoring for OAuth flows

## Support

For issues or questions regarding the GitHub OAuth integration:

1. Check the logs for detailed error messages
2. Verify configuration settings
3. Test with a simple OAuth flow
4. Check AWS Cognito console for user creation

This implementation provides a complete, production-ready GitHub OAuth integration with AWS Cognito.
