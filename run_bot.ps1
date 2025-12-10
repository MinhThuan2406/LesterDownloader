# PowerShell script to run the Discord bot
# This script handles the virtual environment activation and bot startup

Write-Host "Starting Lester the Downloader Discord Bot..." -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Please run 'python -m venv .venv' first." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Check if activation was successful
if ($env:VIRTUAL_ENV) {
    Write-Host "Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
    
    # Install/update dependencies
    Write-Host "Checking dependencies..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    
    # Run the bot
    Write-Host "Starting bot..." -ForegroundColor Green
    python main.py
} else {
    Write-Host "Failed to activate virtual environment." -ForegroundColor Red
    exit 1
} 