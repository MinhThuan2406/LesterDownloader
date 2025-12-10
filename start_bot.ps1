# LesterDownloader Bot Startup Script
# Production startup with SSL configuration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  LesterDownloader Discord Bot" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Set SSL certificate path
$certPath = ".\.venv\lib\python3.12\site-packages\certifi\cacert.pem"
if (Test-Path $certPath) {
    $env:SSL_CERT_FILE = $certPath
    $env:REQUESTS_CA_BUNDLE = $certPath
    Write-Host "✅ SSL Certificate configured" -ForegroundColor Green
}
else {
    Write-Host "⚠️  SSL Certificate not found, bot may have connection issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting bot..." -ForegroundColor Green
Write-Host ""

# Run the bot
python main.py

# Check exit code
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Bot exited with errors (code: $LASTEXITCODE)" -ForegroundColor Red
    Write-Host "Check bot.log for details" -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "✅ Bot shut down gracefully" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
