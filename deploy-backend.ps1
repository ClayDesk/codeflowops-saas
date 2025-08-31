# PowerShell script to deploy to Elastic Beanstalk
# Run: .\deploy-backend.ps1

param(
    [string]$ApplicationName = "codeflowops-backend",
    [string]$EnvironmentName = "codeflowops-backend-env",
    [string]$Region = "us-east-1"
)

Write-Host "Deploying CodeFlowOps Backend to Elastic Beanstalk..." -ForegroundColor Green

# Step 1: Create deployment package
Write-Host "Creating deployment package..." -ForegroundColor Yellow
python create_eb_deployment.py

if (-not (Test-Path "codeflowops-backend-eb.zip")) {
    Write-Error "Deployment package creation failed!"
    exit 1
}

# Step 2: Upload to S3 (temporary bucket)
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$versionLabel = "deploy-$timestamp"
$bucketName = "codeflowops-deployments-temp"

Write-Host "Uploading to S3..." -ForegroundColor Yellow

# Create S3 bucket if it doesn't exist
aws s3 mb "s3://$bucketName" --region $Region 2>$null

# Upload deployment package
aws s3 cp "codeflowops-backend-eb.zip" "s3://$bucketName/$versionLabel.zip" --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Error "S3 upload failed!"
    exit 1
}

# Step 3: Create application version
Write-Host "Creating application version..." -ForegroundColor Yellow
aws elasticbeanstalk create-application-version `
    --application-name $ApplicationName `
    --version-label $versionLabel `
    --source-bundle "S3Bucket=$bucketName,S3Key=$versionLabel.zip" `
    --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Error "Application version creation failed!"
    exit 1
}

# Step 4: Deploy to environment
Write-Host "Deploying to environment..." -ForegroundColor Yellow
aws elasticbeanstalk update-environment `
    --environment-name $EnvironmentName `
    --version-label $versionLabel `
    --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment initiated successfully!" -ForegroundColor Green
    Write-Host "Monitor deployment at: https://console.aws.amazon.com/elasticbeanstalk/" -ForegroundColor Cyan
    Write-Host "Deployment typically takes 2-5 minutes..." -ForegroundColor Yellow
    
    # Optional: Wait for deployment to complete
    Write-Host "Waiting for deployment to complete..." -ForegroundColor Yellow
    aws elasticbeanstalk wait environment-updated --environment-name $EnvironmentName --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Deployment completed successfully!" -ForegroundColor Green
        Write-Host "Backend URL: https://api.codeflowops.com" -ForegroundColor Green
    } else {
        Write-Warning "Deployment may still be in progress. Check EB console."
    }
} else {
    Write-Error "Deployment failed!"
    exit 1
}

# Clean up temporary S3 file (delayed to allow for configuration updates)
Write-Host "Keeping S3 file for potential configuration updates..." -ForegroundColor Gray
Write-Host "To manually clean up later: aws s3 rm s3://$bucketName/$versionLabel.zip" -ForegroundColor Gray

Write-Host "Deployment completed. S3 file preserved for configuration updates." -ForegroundColor Gray
