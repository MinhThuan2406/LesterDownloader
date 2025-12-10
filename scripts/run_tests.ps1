# Automated Download Testing Script
# Tests downloads from YouTube, TikTok, and Instagram

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Download Testing Tool" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
Set-Location ..

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Set SSL cert path
$env:SSL_CERT_FILE = ".\.venv\lib\python3.12\site-packages\certifi\cacert.pem"
$env:REQUESTS_CA_BUNDLE = $env:SSL_CERT_FILE

Write-Host "SSL Certificate: $env:SSL_CERT_FILE" -ForegroundColor Gray
Write-Host ""

# Run the test script
Write-Host "Running download tests..." -ForegroundColor Yellow
Write-Host ""

python tests\test_downloads.py

# Capture exit code
$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
}
else {
    Write-Host "❌ Some tests failed. Check the output above for details." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Return to scripts directory
Set-Location scripts

exit $exitCode
