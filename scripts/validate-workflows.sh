#!/bin/bash

# CodeFlowOps Workflow Validation Script
# This script validates that the GitHub Actions workflows are properly configured

echo "🔍 CodeFlowOps CI/CD Workflow Validation"
echo "========================================"

# Check if workflows exist
WORKFLOWS_DIR=".github/workflows"
if [ ! -d "$WORKFLOWS_DIR" ]; then
    echo "❌ Workflows directory not found"
    exit 1
fi

echo "✅ Workflows directory found"

# Check individual workflow files
WORKFLOWS=(
    "ci-cd.yml"
    "deploy-production.yml" 
    "e2e-tests.yml"
)

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f "$WORKFLOWS_DIR/$workflow" ]; then
        echo "✅ $workflow - Found"
        
        # Basic YAML syntax check (if yq is available)
        if command -v yq &> /dev/null; then
            if yq eval . "$WORKFLOWS_DIR/$workflow" > /dev/null 2>&1; then
                echo "  ✅ Valid YAML syntax"
            else
                echo "  ⚠️ YAML syntax issues detected"
            fi
        fi
    else
        echo "❌ $workflow - Missing"
    fi
done

# Check for documentation
DOCS=(
    ".github/SECRETS_SETUP.md"
    ".github/workflows.schema.yml"
)

echo ""
echo "📚 Documentation Check"
echo "----------------------"

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "✅ $doc - Found"
    else
        echo "❌ $doc - Missing"
    fi
done

# Check package.json files
echo ""
echo "📦 Package Configuration Check"
echo "------------------------------"

if [ -f "frontend/package.json" ]; then
    echo "✅ Frontend package.json found"
    
    # Check for required scripts
    if grep -q '"test"' frontend/package.json; then
        echo "  ✅ Test script configured"
    else
        echo "  ⚠️ Test script missing"
    fi
    
    if grep -q '"build"' frontend/package.json; then
        echo "  ✅ Build script configured"
    else
        echo "  ⚠️ Build script missing"
    fi
else
    echo "❌ Frontend package.json missing"
fi

if [ -f "backend/requirements.txt" ]; then
    echo "✅ Backend requirements.txt found"
else
    echo "❌ Backend requirements.txt missing"
fi

# Check for Playwright configuration
if [ -f "playwright.config.ts" ] || [ -f "playwright.config.js" ]; then
    echo "✅ Playwright configuration found"
else
    echo "⚠️ Playwright configuration missing"
fi

echo ""
echo "🎯 Summary"
echo "----------"
echo "Your CodeFlowOps CI/CD pipeline is configured with:"
echo "• Automated testing for frontend and backend"
echo "• End-to-end testing with Playwright"
echo "• Staging and production deployment workflows"
echo "• Comprehensive documentation and setup guides"
echo ""
echo "📋 Next Steps:"
echo "1. Configure secrets in GitHub repository settings"
echo "2. Set up AWS infrastructure (ECS, ECR, S3, CloudFront)"
echo "3. Push to 'develop' branch to test staging deployment"
echo "4. Push to 'main' branch to trigger production deployment"
echo ""
echo "ℹ️ Note: Yellow warnings in workflow files about 'undefined secrets' are normal"
echo "   and will disappear once you configure the secrets in GitHub settings."
