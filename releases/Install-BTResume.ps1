# BT Resume Installer Script
param(
    [string]$InstallPath = "$env:LOCALAPPDATA\BTResume",
    [switch]$CreateDesktop,
    [switch]$CreateStartMenu
)

$ErrorActionPreference = "Stop"

Write-Host "Installing BT Resume..." -ForegroundColor Cyan

# Get the script's directory (where this installer is located)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourcePath = Join-Path $ScriptDir "BT-Resume-1.0.0.7z"

if (-not (Test-Path $SourcePath)) {
    Write-Host "Error: Cannot find BT-Resume-1.0.0.7z in the same folder." -ForegroundColor Red
    Write-Host "Please extract the installer first." -ForegroundColor Yellow
    exit 1
}

# Create installation directory
if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
}

# Extract 7z archive
Write-Host "Extracting files..." -ForegroundColor Yellow
$7zPath = Get-Command 7z -ErrorAction SilentlyContinue
if ($7zPath) {
    & 7z x "-o$InstallPath" "$SourcePath" -y | Out-Null
} else {
    # Fallback: try to find 7z in common locations
    $7zLocations = @(
        "C:\Users\$env:USERNAME\scoop\shims\7z.exe",
        "C:\Program Files\7-Zip\7z.exe",
        "C:\Program Files (x86)\7-Zip\7z.exe"
    )
    foreach ($loc in $7zLocations) {
        if (Test-Path $loc) {
            & $loc x "-o$InstallPath" "$SourcePath" -y | Out-Null
            break
        }
    }
}

# Find the executable
$exePath = Get-ChildItem -Path $InstallPath -Filter "btf_resume.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $exePath) {
    Write-Host "Error: Could not find btf_resume.exe in extracted files." -ForegroundColor Red
    exit 1
}

$exePath = $exePath.FullName

# Create Desktop shortcut
if ($CreateDesktop) {
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$DesktopPath\BT Resume.lnk")
    $Shortcut.TargetPath = $exePath
    $Shortcut.WorkingDirectory = (Split-Path $exePath -Parent)
    $Shortcut.Save()
    Write-Host "Created Desktop shortcut" -ForegroundColor Green
}

# Create Start Menu shortcut
if ($CreateStartMenu) {
    $StartMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\BT Resume"
    if (-not (Test-Path $StartMenuPath)) {
        New-Item -ItemType Directory -Path $StartMenuPath -Force | Out-Null
    }
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$StartMenuPath\BT Resume.lnk")
    $Shortcut.TargetPath = $exePath
    $Shortcut.WorkingDirectory = (Split-Path $exePath -Parent)
    $Shortcut.Save()
    
    # Create Uninstall shortcut
    $UninstallScript = Join-Path $StartMenuPath "Uninstall.ps1"
    @"
`$InstallPath = "$InstallPath"
Remove-Item -Path `$InstallPath -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "$StartMenuPath" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "BT Resume uninstalled." -ForegroundColor Green
"@ | Set-Content $UninstallScript
    
    Write-Host "Created Start Menu shortcuts" -ForegroundColor Green
}

# Register with Windows (Add/Remove Programs)
$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\BTResume"
if (-not (Test-Path $UninstallKey)) {
    New-Item -Path $UninstallKey -Force | Out-Null
}
Set-ItemProperty -Path $UninstallKey -Name "DisplayName" -Value "BT Resume"
Set-ItemProperty -Path $UninstallKey -Name "UninstallString" -Value "powershell -ExecutionPolicy Bypass -File `"$StartMenuPath\Uninstall.ps1`""
Set-ItemProperty -Path $UninstallKey -Name "InstallLocation" -Value $InstallPath
Set-ItemProperty -Path $UninstallKey -Name "DisplayIcon" -Value $exePath
Set-ItemProperty -Path $UninstallKey -Name "Publisher" -Value "BTF"
Set-ItemProperty -Path $UninstallKey -Name "DisplayVersion" -Value "1.0.0"

Write-Host ""
Write-Host "BT Resume installed successfully!" -ForegroundColor Green
Write-Host "Location: $InstallPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: On first run, the app will download the AI model (500MB-1GB)" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to launch
$launch = Read-Host "Do you want to launch BT Resume now? (Y/N)"
if ($launch -eq "Y" -or $launch -eq "y") {
    Start-Process $exePath
}
