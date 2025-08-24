# CodeFlowOps Backend Deployment Guide

## 🎯 Deployment Package Ready!

Your backend deployment package `codeflowops-backend-eb.zip` is ready for AWS Elastic Beanstalk.

## 📋 Deployment Steps

### 1. AWS Elastic Beanstalk Setup

1. **Go to AWS Elastic Beanstalk Console**
   - Open https://console.aws.amazon.com/elasticbeanstalk/
   - Select the appropriate region (e.g., us-east-1)

2. **Create New Application (if needed)**
   - Click "Create Application"
   - Application name: `codeflowops-backend`
   - Platform: `Python`
   - Platform version: `Python 3.11 running on 64bit Amazon Linux 2023`

3. **Deploy the Package**
   - Upload: `codeflowops-backend-eb.zip`
   - Version label: `v1.0-production`

### 2. Environment Configuration

Set these environment variables in EB:

```
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://www.codeflowops.com,https://codeflowops.com
CORS_ALLOW_CREDENTIALS=true
AWS_REGION=us-east-1
```

### 3. Domain Configuration

1. **Add Custom Domain**
   - Go to EB Console → Configuration → Load Balancer
   - Add listener for HTTPS (443)
   - Add SSL certificate for `api.codeflowops.com`

2. **Route 53 DNS**
   - Create CNAME record: `api.codeflowops.com` → `[your-eb-environment].region.elasticbeanstalk.com`

### 4. Frontend Integration

Your frontend at https://www.codeflowops.com expects these API endpoints:

✅ **Analysis Endpoints:**
- `POST /api/v1/smart-deploy/analyze-repository`
- `POST /api/v1/smart-deploy/upload-repository`
- `GET /api/v1/smart-deploy/infrastructure/preview`

✅ **Deployment Endpoints:**
- `POST /api/v1/smart-deploy/deployments`
- `GET /api/v1/smart-deploy/deployment/{id}`
- `POST /api/v1/smart-deploy/deployment/{id}/deploy`
- `GET /api/v1/smart-deploy/deployment/{id}/logs`

✅ **Status & Monitoring:**
- `GET /api/v1/smart-deploy/status/{id}`
- `GET /api/v1/smart-deploy/stats`
- `WebSocket: /api/v1/smart-deploy/ws/realtime`

✅ **Core API:**
- `GET /` (root endpoint)
- `GET /health` (health check)
- `GET /docs` (API documentation)

## 🔧 Configuration Included

### CORS Configuration
- ✅ `https://www.codeflowops.com`
- ✅ `https://codeflowops.com`
- ✅ Development localhost origins

### Production Settings
- ✅ Compression middleware (GZip)
- ✅ Trusted host middleware
- ✅ Error handling and logging
- ✅ Performance monitoring

### Elastic Beanstalk Optimizations
- ✅ Python path configuration
- ✅ WSGI application setup
- ✅ Process management (Procfile)
- ✅ Static file handling

## 🚀 Deployment Verification

After deployment, test these URLs:

1. **Health Check:** `https://api.codeflowops.com/health`
2. **API Docs:** `https://api.codeflowops.com/docs`
3. **Root Endpoint:** `https://api.codeflowops.com/`

Expected response from health endpoint:
```json
{
  "status": "healthy",
  "service": "codeflowops-enhanced-analysis-engine",
  "version": "1.0.0",
  "phase": "Phase 1: Enhanced Repository Analysis Engine",
  "components": {
    "api": "operational",
    "analysis_engine": "operational",
    "repository_analyzer": "operational",
    "project_detector": "operational",
    "dependency_analyzer": "operational"
  }
}
```

## 🔗 Frontend-Backend Connectivity

Your frontend will automatically connect to the backend once:

1. ✅ Backend is deployed to `api.codeflowops.com`
2. ✅ DNS is configured correctly
3. ✅ SSL certificate is active
4. ✅ CORS is properly configured

## 📊 Monitoring & Logs

1. **EB Console Logs**
   - Go to EB Environment → Logs → Request Logs

2. **CloudWatch Logs**
   - Application logs: `/aws/elasticbeanstalk/[env-name]/var/log/eb-engine.log`
   - Access logs: `/aws/elasticbeanstalk/[env-name]/var/log/nginx/access.log`

## 🆘 Troubleshooting

### Common Issues:

1. **CORS Errors**
   - Verify ALLOWED_ORIGINS environment variable
   - Check frontend domain matches exactly

2. **404 on API Endpoints**
   - Verify application.py is loading correctly
   - Check EB logs for import errors

3. **500 Internal Server Error**
   - Check dependency imports in logs
   - Verify all required packages in requirements.txt

### Debug Commands:
```bash
# Check EB logs
eb logs

# Check environment status
eb status

# Deploy new version
eb deploy
```

## ✅ Ready for Production!

Your deployment package includes:
- ✅ Complete FastAPI application
- ✅ All API routes and endpoints
- ✅ Production CORS configuration
- ✅ Error handling and logging
- ✅ Performance optimizations
- ✅ EB-specific configurations

**File:** `codeflowops-backend-eb.zip` (0.3 MB)
**Ready for:** AWS Elastic Beanstalk deployment
**Target Domain:** api.codeflowops.com
