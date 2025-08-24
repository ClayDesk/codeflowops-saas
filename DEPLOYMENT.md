# CodeFlowOps SaaS Deployment Guide

## 🚀 Quick Deployment

### Backend Deployment (Manual)
```powershell
# Run from project root
.\deploy-backend.ps1
```

### Frontend Deployment (Automatic)
- Frontend automatically deploys via AWS Amplify when you push to GitHub
- Live at: https://www.codeflowops.com

## 🔧 Backend API Endpoints

**Base URL**: https://api.codeflowops.com

### Available Endpoints:
- `GET /health` - API health check
- `POST /api/analyze-repo` - Analyze repository structure
- `POST /api/deploy` - Deploy application  
- `GET /api/deployment/{id}/status` - Check deployment status
- `POST /api/validate-credentials` - Validate AWS credentials

### Test the API:
```powershell
# Health check
Invoke-WebRequest -Uri "https://api.codeflowops.com/health"

# Get all endpoints
Invoke-WebRequest -Uri "https://api.codeflowops.com/" | Select-Object -ExpandProperty Content
```

## 📝 Configuration

### Frontend Environment Variables
Production environment is configured in `frontend/.env.production`:
```
NEXT_PUBLIC_API_URL=https://api.codeflowops.com
NEXT_PUBLIC_WS_URL=wss://api.codeflowops.com
```

### Backend Configuration
- **Platform**: AWS Elastic Beanstalk
- **Runtime**: Python 3.13
- **Framework**: FastAPI + Uvicorn
- **CORS**: Configured for https://www.codeflowops.com

## 🔒 Security

### AWS Credentials
For manual deployments, the PowerShell script will prompt for AWS credentials securely.

### HTTPS Configuration
- Frontend: HTTPS enforced via AWS Amplify
- Backend: HTTPS enforced via AWS Elastic Beanstalk
- API calls: All communication uses HTTPS (Mixed Content issues resolved)

## 📊 Monitoring

### Health Checks
```powershell
# Backend health
Invoke-WebRequest -Uri "https://api.codeflowops.com/health"

# Frontend status  
Invoke-WebRequest -Uri "https://www.codeflowops.com"
```

### Logs
- Frontend logs: AWS Amplify Console
- Backend logs: AWS Elastic Beanstalk Console → Logs

## 🛠️ Troubleshooting

### Common Issues:

1. **Mixed Content Errors**
   - ✅ **RESOLVED**: All API calls now use HTTPS

2. **CORS Errors**
   - Backend configured for `https://www.codeflowops.com`
   - Check backend logs if issues persist

3. **Deployment Failures**
   - Verify AWS credentials
   - Check `deploy-backend.ps1` script output
   - Review Elastic Beanstalk environment health

### Manual Backend Update:
```powershell
# From project root
cd backend
# Make your changes
cd ..
.\deploy-backend.ps1
```

---

**Status**: ✅ Production Ready  
**Last Updated**: August 24, 2025  
**Frontend**: https://www.codeflowops.com  
**Backend**: https://api.codeflowops.com
