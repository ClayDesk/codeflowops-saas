Write-Host "Fixing CodeFlowOps Backend Deployment - FINAL FIX" -ForegroundColor Yellow

$backendDir = "C:\ClayDesk.AI\codeflowops-saas\backend"
$deploymentDir = "C:\ClayDesk.AI\codeflowops-saas\deployment-final"
$zipFile = "C:\ClayDesk.AI\codeflowops-saas\codeflowops-backend-FINAL.zip"

# Clean up
if (Test-Path $deploymentDir) { Remove-Item -Recurse -Force $deploymentDir }
if (Test-Path $zipFile) { Remove-Item -Force $zipFile }

# Create deployment directory
New-Item -ItemType Directory -Path $deploymentDir -Force | Out-Null
Write-Host "Created deployment directory" -ForegroundColor Green

# Copy essential files
Copy-Item "$backendDir\simple_api.py" -Destination "$deploymentDir\main.py"
Copy-Item "$backendDir\requirements.txt" -Destination $deploymentDir
Copy-Item "$backendDir\repository_enhancer.py" -Destination $deploymentDir
Copy-Item "$backendDir\enhanced_repository_analyzer.py" -Destination $deploymentDir
Copy-Item "$backendDir\cleanup_service.py" -Destination $deploymentDir

# Copy directories
$dirs = @("core", "detectors", "routers", "src", "analyzer", "utils")
foreach ($dir in $dirs) {
    $sourcePath = Join-Path $backendDir $dir
    if (Test-Path $sourcePath) {
        Copy-Item -Recurse $sourcePath "$deploymentDir\$dir"
        Write-Host "Copied: $dir/" -ForegroundColor Gray
    }
}

Write-Host "Creating FIXED application.py..." -ForegroundColor Cyan
