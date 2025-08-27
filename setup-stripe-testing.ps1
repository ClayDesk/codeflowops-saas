# Stripe Configuration for CodeFlowOps Trial Management Testing
# This file shows how to set up environment variables for live Stripe testing

# FOR LIVE TESTING - Set these environment variables:
# $env:STRIPE_SECRET_KEY = "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"
# $env:STRIPE_WEBHOOK_SECRET = "whsec_your_webhook_secret_here"

# USAGE EXAMPLES:

# 1. Test with live Stripe keys (PowerShell):
#    $env:STRIPE_SECRET_KEY = "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"
#    python -m uvicorn simple_api:app --host 0.0.0.0 --port 8000

# 2. Test trial endpoints with live data:
#    Invoke-RestMethod -Uri "http://localhost:8000/api/trial/status?user_id=live_user" -Method GET

# 3. Test quota with real subscription data:
#    Invoke-RestMethod -Uri "http://localhost:8000/api/quota/status?plan=starter" -Method GET

# DEPLOYMENT NOTES:
# - In AWS Elastic Beanstalk, set environment variables in configuration
# - The code automatically detects production environment and requires proper env vars
# - For local development, it falls back to test keys

Write-Host "🔧 Stripe Configuration Helper"
Write-Host ""
Write-Host "To test with LIVE Stripe functionality:"
Write-Host "1. Set environment variable:"
Write-Host '   $env:STRIPE_SECRET_KEY = "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"'
Write-Host ""
Write-Host "2. Start the API server:"
Write-Host "   cd backend"
Write-Host "   python -m uvicorn simple_api:app --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "3. Test trial management:"
Write-Host '   Invoke-RestMethod -Uri "http://localhost:8000/api/trial/status" -Method GET'
Write-Host ""
Write-Host "🚀 Then your trial management will work with LIVE Stripe data!"
