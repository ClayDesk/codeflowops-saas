# Deploy Frontend Changes to Amplify

Write-Host "🚀 Deploying Frontend Changes..." -ForegroundColor Cyan
Write-Host ""

# Add all changes
Write-Host "📦 Staging changes..." -ForegroundColor Yellow
git add frontend/lib/auth-context.tsx
git add frontend/app/subscriptions/page.tsx
git add frontend/app/auth-test/page.tsx
git add DEPLOYMENT_GUIDE.md
git add SUBSCRIPTION_FIX_SUMMARY.md
git add TESTING_SUBSCRIPTION_PAGE.md

# Commit
Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git commit -m "Fix: Enhanced auth state detection and subscription page redirect issue

- Fixed storeAuthData() to save tokens in localStorage
- Improved auth initialization to check Cognito auth first
- Added 1-second delay before redirect to allow auth initialization
- Added comprehensive console logging for debugging
- Created /auth-test page for visual debugging
- Enhanced subscriptions page with better auth state handling"

# Push
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Yellow
git push origin master

Write-Host ""
Write-Host "✅ Changes pushed to GitHub!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Check AWS Amplify console for deployment status"
Write-Host "2. Wait for build to complete (usually 2-5 minutes)"
Write-Host "3. Visit https://www.codeflowops.com/auth-test to verify auth state"
Write-Host "4. Visit https://www.codeflowops.com/subscriptions to test fix"
Write-Host ""
Write-Host "🔍 If still having issues:" -ForegroundColor Yellow
Write-Host "- Clear browser cache (Ctrl+Shift+R)"
Write-Host "- Login again to ensure new token storage logic runs"
Write-Host "- Check browser console for auth state logs"
Write-Host ""
