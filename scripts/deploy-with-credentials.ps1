# PowerShell Deployment Wrapper
# This script is called by the backend API with dynamic credentials
# and handles the complete deployment process

param(
    [Parameter(Mandatory=$true)]
    [string]$RepositoryUrl,
    
    [Parameter(Mandatory=$true)]
    [string]$ProjectName,
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production",
    
    [Parameter(Mandatory=$true)]
    [string]$AwsAccessKeyId,
    
    [Parameter(Mandatory=$true)]
    [string]$AwsSecretAccessKey,
    
    [Parameter(Mandatory=$false)]
    [string]$AwsSessionToken = "",
    
    [Parameter(Mandatory=$false)]
    [string]$AwsRegion = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$DeploymentId = ""
)

$ErrorActionPreference = "Stop"

# Configuration
$LOG_FILE = "deployment-$DeploymentId-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$STATUS_FILE = "deployment-status-$DeploymentId.json"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry -ForegroundColor $(if($Level -eq "ERROR"){"Red"} elseif($Level -eq "SUCCESS"){"Green"} elseif($Level -eq "WARNING"){"Yellow"} else{"Blue"})
    Add-Content -Path $LOG_FILE -Value $logEntry
}

function Update-DeploymentStatus {
    param(
        [string]$Step,
        [string]$Status,
        [string]$Message,
        [int]$Progress = 0,
        [string[]]$Logs = @()
    )
    
    $statusUpdate = @{
        deployment_id = $DeploymentId
        step = $Step
        status = $Status
        message = $Message
        progress = $Progress
        timestamp = Get-Date -Format 'o'
        logs = $Logs
    }
    
    # Read existing status file or create new
    $allStatuses = @()
    if (Test-Path $STATUS_FILE) {
        $allStatuses = Get-Content $STATUS_FILE | ConvertFrom-Json
    }
    
    # Add new status
    $allStatuses += $statusUpdate
    
    # Save updated status
    $allStatuses | ConvertTo-Json -Depth 3 | Set-Content $STATUS_FILE
    
    Write-Log "$Step`: $Message" -Level $(if($Status -eq "failed"){"ERROR"} elseif($Status -eq "completed"){"SUCCESS"} else{"INFO"})
}

function Start-Deployment {
    try {
        Write-Log "Starting deployment for repository: $RepositoryUrl"
        Update-DeploymentStatus -Step "Initialization" -Status "running" -Message "Starting deployment process" -Progress 5

        # Validate inputs
        if (-not $RepositoryUrl -or -not $RepositoryUrl.StartsWith("https://github.com/")) {
            throw "Invalid repository URL. Must be a GitHub HTTPS URL."
        }

        if (-not $AwsAccessKeyId -or -not $AwsSecretAccessKey) {
            throw "AWS credentials are required for deployment."
        }

        Update-DeploymentStatus -Step "Initialization" -Status "completed" -Message "Initial validation completed" -Progress 10

        # Step 1: Repository Analysis
        Update-DeploymentStatus -Step "Repository Analysis" -Status "running" -Message "Analyzing repository structure and dependencies" -Progress 15

        if (!(Test-Path "scripts\analyze-repo.js")) {
            throw "Repository analysis script not found at scripts\analyze-repo.js"
        }

        node scripts\analyze-repo.js $RepositoryUrl | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "Repository analysis failed with exit code $LASTEXITCODE"
        }

        Update-DeploymentStatus -Step "Repository Analysis" -Status "completed" -Message "Repository analysis completed successfully" -Progress 25

        # Step 2: Infrastructure Provisioning
        Update-DeploymentStatus -Step "Infrastructure Provisioning" -Status "running" -Message "Provisioning AWS infrastructure based on analysis" -Progress 30

        $provisionArgs = @{
            ProjectName = $ProjectName
            Environment = $Environment
            AwsRegion = $AwsRegion
            AwsAccessKeyId = $AwsAccessKeyId
            AwsSecretAccessKey = $AwsSecretAccessKey
            RepositoryUrl = $RepositoryUrl
        }

        if ($AwsSessionToken) {
            $provisionArgs.AwsSessionToken = $AwsSessionToken
        }

        # Call the main provisioning script
        & "$PSScriptRoot\provision-infrastructure.ps1" @provisionArgs | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            throw "Infrastructure provisioning failed with exit code $LASTEXITCODE"
        }

        Update-DeploymentStatus -Step "Infrastructure Provisioning" -Status "completed" -Message "AWS infrastructure provisioned successfully" -Progress 70

        # Step 3: Application Deployment
        Update-DeploymentStatus -Step "Application Deployment" -Status "running" -Message "Deploying application to provisioned infrastructure" -Progress 75

        # Read deployment info from provision script
        $deploymentInfoFile = "deployment-info.json"
        if (Test-Path $deploymentInfoFile) {
            $deploymentInfo = Get-Content $deploymentInfoFile | ConvertFrom-Json
            
            # Trigger CodeBuild if it's a serverless deployment
            if ($deploymentInfo.build_project_name) {
                Update-DeploymentStatus -Step "Application Deployment" -Status "running" -Message "Starting CodeBuild for application build and deployment" -Progress 80

                $buildResult = aws codebuild start-build --project-name $deploymentInfo.build_project_name --output json
                if ($LASTEXITCODE -eq 0) {
                    $build = $buildResult | ConvertFrom-Json
                    $buildId = $build.build.id
                    
                    # Wait for build to complete
                    do {
                        Start-Sleep -Seconds 15
                        $buildStatus = aws codebuild batch-get-builds --ids $buildId --output json | ConvertFrom-Json
                        $currentBuild = $buildStatus.builds[0]
                        
                        Update-DeploymentStatus -Step "Application Deployment" -Status "running" -Message "CodeBuild in progress: $($currentBuild.buildStatus)" -Progress 85
                        
                    } while ($currentBuild.buildStatus -eq "IN_PROGRESS")
                    
                    if ($currentBuild.buildStatus -eq "SUCCEEDED") {
                        Update-DeploymentStatus -Step "Application Deployment" -Status "completed" -Message "Application deployed successfully via CodeBuild" -Progress 95
                    } else {
                        throw "CodeBuild failed with status: $($currentBuild.buildStatus)"
                    }
                }
            }
            
            # Final deployment URL
            $deploymentUrl = $deploymentInfo.deployment_url
            if ($deploymentUrl) {
                Update-DeploymentStatus -Step "Deployment Complete" -Status "completed" -Message "Application successfully deployed and accessible at: $deploymentUrl" -Progress 100 -Logs @("Deployment URL: $deploymentUrl")
            } else {
                Update-DeploymentStatus -Step "Deployment Complete" -Status "completed" -Message "Infrastructure provisioned successfully. Manual deployment may be required." -Progress 100
            }
        } else {
            Update-DeploymentStatus -Step "Application Deployment" -Status "completed" -Message "Infrastructure provisioned. Check AWS console for deployment details." -Progress 95
            Update-DeploymentStatus -Step "Deployment Complete" -Status "completed" -Message "Deployment process completed" -Progress 100
        }

        Write-Log "Deployment completed successfully!" -Level "SUCCESS"
        return $true

    } catch {
        $errorMessage = $_.Exception.Message
        Write-Log "Deployment failed: $errorMessage" -Level "ERROR"
        Update-DeploymentStatus -Step "Deployment Failed" -Status "failed" -Message $errorMessage -Progress 0 -Logs @($_.Exception.ToString())
        return $false
    }
}

# Main execution
function Main {
    Write-Log "========================================="
    Write-Log "Starting CodeFlowOps Deployment Process"
    Write-Log "========================================="
    Write-Log "Repository: $RepositoryUrl"
    Write-Log "Project: $ProjectName"
    Write-Log "Environment: $Environment"
    Write-Log "Region: $AwsRegion"
    Write-Log "Deployment ID: $DeploymentId"
    Write-Log "========================================="

    $success = Start-Deployment

    if ($success) {
        Write-Log "🎉 Deployment completed successfully!" -Level "SUCCESS"
        exit 0
    } else {
        Write-Log "❌ Deployment failed. Check logs for details." -Level "ERROR"
        exit 1
    }
}

# Run main function
Main
