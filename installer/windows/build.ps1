# BTF Resume - NSIS Installer Build Script
# Run this from the project root directory

param(
    [string]$Version = "1.0.0",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

Write-Host "Building BTF Resume Installer v$Version" -ForegroundColor Cyan

# Paths
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Get-Location }
$FlutterApp = Join-Path $ProjectRoot "flutter_app"
$InstallerDir = Join-Path $ProjectRoot "installer\windows"
$OutputDir = Join-Path $ProjectRoot "releases"

# Clean if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Path (Join-Path $FlutterApp "build") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $OutputDir "*.exe") -Force -ErrorAction SilentlyContinue
}

# Ensure output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Step 1: Build Flutter app
Write-Host "Building Flutter Windows release..." -ForegroundColor Yellow
Set-Location $FlutterApp
flutter clean
flutter pub get
flutter build windows --release

if ($LASTEXITCODE -ne 0) {
    Write-Host "Flutter build failed!" -ForegroundColor Red
    exit 1
}

# Step 2: Build NSIS installer
Write-Host "Building NSIS installer..." -ForegroundColor Yellow
Set-Location $InstallerDir

# Update version in NSIS script
$nsisScript = Get-Content "installer.nsi" -Raw
$nsisScript = $nsisScript -replace 'VERSIONMAJOR \d+', "VERSIONMAJOR $($Version.Split('.')[0])"
$nsisScript = $nsisScript -replace 'VERSIONMINOR \d+', "VERSIONMINOR $($Version.Split('.')[1])"
$nsisScript = $nsisScript -replace 'VERSIONBUILD \d+', "VERSIONBUILD $($Version.Split('.')[2])"
$nsisScript = $nsisScript -replace 'OutFile "BTFResume-Setup-.*\.exe"', "OutFile `"BTFResume-Setup-$Version.exe`""
Set-Content "installer.nsi" -Value $nsisScript -NoNewline

# Run NSIS
$makensis = Get-Command makensis -ErrorAction SilentlyContinue
if (-not $makensis) {
    # Try via choco
    & choco install nsis -y
    $makensis = Get-Command makensis -ErrorAction Stop
}

& makensis "installer.nsi"

if ($LASTEXITCODE -ne 0) {
    Write-Host "NSIS build failed!" -ForegroundColor Red
    exit 1
}

# Step 3: Copy installer to releases
Write-Host "Copying installer to releases..." -ForegroundColor Yellow
$installer = Get-Item "BTFResume-Setup-$Version.exe" -ErrorAction SilentlyContinue
if ($installer) {
    Copy-Item $installer.FullName -Destination $OutputDir
    Write-Host "Installer created: $($OutputDir)\$($installer.Name)" -ForegroundColor Green
} else {
    Write-Host "Warning: Installer not found in expected location" -ForegroundColor Yellow
}

Set-Location $ProjectRoot
Write-Host "Build complete!" -ForegroundColor Green