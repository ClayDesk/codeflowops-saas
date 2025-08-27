#!/usr/bin/env pwsh
# Quick Stripe Live Testing Script for Trial Management

param(
    [switch]$Live,
    [switch]$Test
)

Write-Host "🧪 CodeFlowOps Trial Management Testing" -ForegroundColor Cyan
Write-Host ""

if ($Live) {
    Write-Host "🔴 Setting up LIVE Stripe environment..." -ForegroundColor Yellow
    $env:STRIPE_SECRET_KEY = "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"
    $env:STRIPE_WEBHOOK_SECRET = "whsec_live_webhook_secret"
    Write-Host "✅ Live Stripe keys configured" -ForegroundColor Green
} elseif ($Test) {
    Write-Host "🟡 Setting up TEST Stripe environment..." -ForegroundColor Yellow
    $env:STRIPE_SECRET_KEY = "sk_test_placeholder"
    $env:STRIPE_WEBHOOK_SECRET = "whsec_test_placeholder"
    Write-Host "✅ Test Stripe keys configured" -ForegroundColor Green
} else {
    Write-Host "🔵 Using default environment configuration" -ForegroundColor Blue
}

Write-Host ""
Write-Host "🚀 Starting API server for testing..."
Write-Host "Available endpoints:"
Write-Host "  GET  /api/trial/status     - Get trial metrics and recommendations"
Write-Host "  GET  /api/quota/status     - Get quota with trial integration"
Write-Host "  POST /api/trial/extend     - Extend trial period"
Write-Host "  POST /api/stripe/webhook   - Handle Stripe webhooks"
Write-Host ""

if ($Live) {
    Write-Host "⚠️  LIVE MODE: Real Stripe data will be used!" -ForegroundColor Red
} else {
    Write-Host "🧪 TEST MODE: Safe for development testing" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

Set-Location "backend"
python -m uvicorn simple_api:app --host 0.0.0.0 --port 8000 --reload
