# PowerShell script to run the bot with proper SSL configuration
# This sets environment variables to use certifi's CA bundle

# Activate virtual environment
& .venv\bin\activate

# Get certifi path
$certifiPath = python -c "import certifi; print(certifi.where())"

# Set SSL environment variables
$env:SSL_CERT_FILE = $certifiPath
$env:REQUESTS_CA_BUNDLE = $certifiPath

Write-Host "SSL Certificate Bundle: $certifiPath" -ForegroundColor Green
Write-Host "Starting LesterDownloader Bot..." -ForegroundColor Cyan

# Run the bot
python main.py
