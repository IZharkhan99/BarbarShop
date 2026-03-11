# BarberShop Manager - EXE Build Automation Script
# This script packages the Python backend and then builds the Electron app.

# 1. Ensure dist_python directory exists
if (!(Test-Path "dist_python")) {
    Write-Host "Creating dist_python directory..." -ForegroundColor Gray
    New-Item -ItemType Directory -Path "dist_python" | Out-Null
}

# 2. Package Python Backend
Write-Host "`n[1/2] Packaging Python Backend (Flask)..." -ForegroundColor Cyan
Write-Host "Installing PyInstaller..." -ForegroundColor Gray
pip install pyinstaller flask gunicorn

Write-Host "Running PyInstaller..." -ForegroundColor Gray
# We include templates, static files, and the logo inside the Python EXE using --add-data
# Syntax: "source;destination" (Windows)
pyinstaller --onefile --noconsole `
    --name barbershop_backend `
    --add-data "templates;templates" `
    --add-data "static;static" `
    --add-data "AlShahidLogo.jpeg;." `
    --distpath dist_python `
    --clean `
    app.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[!] PyInstaller failed. Aborting." -ForegroundColor Red
    exit 1
}

# 3. Build Electron App
Write-Host "`n[2/2] Building Electron Executable..." -ForegroundColor Cyan
Write-Host "Installing Node dependencies..." -ForegroundColor Gray
npm install

Write-Host "Running electron-builder..." -ForegroundColor Gray
npm run dist

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[!] Electron build failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n[SUCCESS] EXE creation complete! Check the 'dist' folder for the installer." -ForegroundColor Green
Write-Host "The Python backend is bundled inside 'dist_python' and will be included in the final app." -ForegroundColor White
