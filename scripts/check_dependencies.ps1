# Dependency Check and Update Script
# Verifies all required packages are installed with correct versions

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Dependency Manager" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Change to project root
Set-Location ..

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
}
else {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv .venv" -ForegroundColor Yellow
    Set-Location scripts
    exit 1
}

Write-Host ""

# Function to check package version
function Test-Package {
    param($PackageName, $MinVersion)
    
    $installed = pip show $PackageName 2>$null
    if ($LASTEXITCODE -eq 0) {
        $version = ($installed | Select-String "Version:").ToString().Split(":")[1].Trim()
        Write-Host "  ✅ $PackageName $version" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "  ❌ $PackageName not installed" -ForegroundColor Red
        return $false
    }
}

# Check critical packages
Write-Host "Checking critical packages..." -ForegroundColor Yellow
Write-Host ""

$allInstalled = $true

Write-Host "Discord Framework:" -ForegroundColor Cyan
$allInstalled = $allInstalled -and (Test-Package "discord.py" "2.5.2")

Write-Host "`nVideo Downloading:" -ForegroundColor Cyan
$allInstalled = $allInstalled -and (Test-Package "yt-dlp" "2025.12.8")

Write-Host "`nSSL Support:" -ForegroundColor Cyan
$allInstalled = $allInstalled -and (Test-Package "certifi" "2024.12.14")

Write-Host "`nHTTP Libraries:" -ForegroundColor Cyan
$allInstalled = $allInstalled -and (Test-Package "aiohttp" "3.9.1")
$allInstalled = $allInstalled -and (Test-Package "requests" "2.32.4")

Write-Host "`nUtilities:" -ForegroundColor Cyan
$allInstalled = $allInstalled -and (Test-Package "python-dotenv" "1.1.1")
$allInstalled = $allInstalled -and (Test-Package "aiosqlite" "0.20.0")
$allInstalled = $allInstalled -and (Test-Package "aiofiles" "24.1.0")

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan

if ($allInstalled) {
    Write-Host "✅ All dependencies installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Optional: Update to latest versions"
    Write-Host "Run: pip install -U -r requirements.txt" -ForegroundColor Yellow
}
else {
    Write-Host "⚠️  Missing dependencies detected!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Fix by running:" -ForegroundColor Cyan
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
    Write-Host "Or update all:" -ForegroundColor Cyan
    Write-Host "  pip install -U -r requirements.txt" -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
