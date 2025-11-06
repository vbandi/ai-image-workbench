# PowerShell script to run the WPF Image Generator with integration tests
# This script demonstrates how to run the application and execute tests

Write-Host "WPF Image Generator - Integration Test Runner" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""

# Check if environment variables are set
$falKey = $env:FAL_KEY
$openaiKey = $env:OPENAI_API_KEY

Write-Host "Environment Check:" -ForegroundColor Yellow
Write-Host "FAL_KEY: $(if ($falKey) { "✓ Set" } else { "✗ Not set" })"
Write-Host "OPENAI_API_KEY: $(if ($openaiKey) { "✓ Set" } else { "✗ Not set" })"
Write-Host ""

if (-not $falKey) {
    Write-Host "WARNING: FAL_KEY environment variable is not set." -ForegroundColor Red
    Write-Host "Image generation will fail without this API key." -ForegroundColor Red
    Write-Host "Set it with: `$env:FAL_KEY = 'your-fal-api-key'" -ForegroundColor Yellow
    Write-Host ""
}

if (-not $openaiKey) {
    Write-Host "WARNING: OPENAI_API_KEY environment variable is not set." -ForegroundColor Red
    Write-Host "Prompt enhancement will fail without this API key." -ForegroundColor Red
    Write-Host "Set it with: `$env:OPENAI_API_KEY = 'your-openai-api-key'" -ForegroundColor Yellow
    Write-Host ""
}

# Build the application
Write-Host "Building application..." -ForegroundColor Yellow
dotnet build --configuration Release

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Build successful!" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Starting application..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To run integration tests:" -ForegroundColor Cyan
    Write-Host "1. Use the menu: Tools > Run Integration Tests" -ForegroundColor Cyan
    Write-Host "2. Or press Ctrl+T keyboard shortcut" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The tests will:" -ForegroundColor White
    Write-Host "• Test all features with real API calls" -ForegroundColor White
    Write-Host "• Generate multiple test images" -ForegroundColor White
    Write-Host "• Save test results to your Desktop" -ForegroundColor White
    Write-Host "• Take several minutes to complete" -ForegroundColor White
    Write-Host ""
    
    # Run the application
    dotnet run --configuration Release
} else {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    Write-Host "Please fix build errors before running tests." -ForegroundColor Red
}