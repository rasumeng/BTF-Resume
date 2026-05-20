# BTF Resume Release Script
# Creates a new release with installer, manifest, and GitHub upload

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    [string]$ReleaseNotes = "",
    [string]$GithubToken = "",
    [switch]$SkipGitPush,
    [switch]$SkipGithubUpload,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param([string]$Msg) Write-Host "[STEP] $Msg" -ForegroundColor Cyan }
function Write-Info { param([string]$Msg) Write-Host "  $Msg" -ForegroundColor Gray }
function Write-Success { param([string]$Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "[WARN] $Msg" -ForegroundColor Yellow }
function Write-Err { param([string]$Msg) Write-Host "[ERR] $Msg" -ForegroundColor Red }

# Validate version format (semver)
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Err "Invalid version format. Use: 1.0.0"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  BT Resume Release Script v$Version" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

# Paths
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Get-Location }
$FlutterApp = Join-Path $ProjectRoot "flutter_app"
$InstallerDir = Join-Path $ProjectRoot "installer\windows"
$ReleasesDir = Join-Path $ProjectRoot "releases"
$ScriptsDir = Join-Path $ProjectRoot "scripts"
$GitHubPagesDir = Join-Path $ProjectRoot ".gh-pages"

Write-Step "Version: $Version"
Write-Step "Project: $ProjectRoot"
Write-Host ""

# Check for dry run
if ($DryRun) {
    Write-Warn "DRY RUN MODE - No changes will be made"
    Write-Host ""
}

# Step 1: Verify Flutter is installed
Write-Step "Checking Flutter installation..."
$flutterCmd = Get-Command flutter -ErrorAction SilentlyContinue
if (-not $flutterCmd) {
    Write-Err "Flutter not found. Install from https://flutter.dev"
    exit 1
}
Write-Success "Flutter found: $((flutter --version) 2>&1 | Select-Object -First 1)"

# Step 2: Build Flutter App
Write-Step "Building Flutter Windows release..."
if (-not $DryRun) {
    Set-Location $FlutterApp
    flutter clean -q
    flutter pub get -q
    flutter build windows --release 2>&1 | ForEach-Object { Write-Info $_ }
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Flutter build failed!"
        exit 1
    }
}
Write-Success "Flutter build complete"

# Step 3: Update NSIS Script Version
Write-Step "Updating installer version..."
if (-not $DryRun) {
    $nsisScript = Join-Path $InstallerDir "installer.nsi"
    $content = Get-Content $nsisScript -Raw
    $parts = $Version.Split('.')
    $content = $content -replace 'VERSIONMAJOR \d+', "VERSIONMAJOR $($parts[0])"
    $content = $content -replace 'VERSIONMINOR \d+', "VERSIONMINOR $($parts[1])"
    $content = $content -replace 'VERSIONBUILD \d+', "VERSIONBUILD $($parts[2])"
    $content = $content -replace 'OutFile "BT-Resume-Setup\.exe"', "OutFile `"BTFResume-$Version-Setup.exe`""
    Set-Content $nsisScript -Value $content -NoNewline
    Write-Info "Updated NSIS script with version $Version"
}
Write-Success "Installer version updated"

# Step 4: Build NSIS Installer
Write-Step "Building NSIS installer..."
if (-not $DryRun) {
    Set-Location $InstallerDir
    $makensis = Get-Command makensis -ErrorAction SilentlyContinue
    if (-not $makensis) {
        Write-Info "NSIS not found, attempting install via Chocolatey..."
        choco install nsis -y -q
        $makensis = Get-Command makensis -ErrorAction SilentlyContinue
    }
    if (-not $makensis) {
        Write-Err "NSIS not available. Install from https://nsis.sourceforge.io/"
        exit 1
    }
    & makensis "installer.nsi" 2>&1 | ForEach-Object { Write-Info $_ }
    if ($LASTEXITCODE -ne 0) {
        Write-Err "NSIS build failed!"
        exit 1
    }
    # Rename to include version
    $setupFile = Join-Path $InstallerDir "BT-Resume-Setup.exe"
    if (Test-Path $setupFile) {
        Move-Item $setupFile (Join-Path $ReleasesDir "BTFResume-$Version-Setup.exe") -Force
    }
}
Write-Success "Installer built: BTFResume-$Version-Setup.exe"

# Step 5: Generate app-archive.json for flutter_desktop_updater
Write-Step "Generating update manifest..."
$archiveJson = @{
    appName = "BT-Resume"
    description = "Local AI Resume Helper - Polish, Tailor, and Format your resume privately"
    items = @(
        @{
            version = $Version
            shortVersion = [int]$Version.Split('.')[1]
            changes = @(
                @{ type = "feat"; message = "New release" }
            )
            date = (Get-Date -Format "yyyy-MM-dd")
            mandatory = $false
            url = "https://github.com/rasumeng/BT-Resume/releases/download/v$Version/"
            platform = "windows"
        }
    )
} | ConvertTo-Json -Depth 3

if (-not $DryRun) {
    $archivePath = Join-Path $ReleasesDir "app-archive.json"
    Set-Content $archivePath -Value $archiveJson
    Write-Info "Created app-archive.json"
}
Write-Success "Update manifest ready"

# Step 6: Update pubspec.yaml version
Write-Step "Updating Flutter version..."
if (-not $DryRun) {
    $pubspec = Join-Path $FlutterApp "pubspec.yaml"
    $content = Get-Content $pubspec -Raw
    $content = $content -replace 'version: \d+\.\d+\.\d+\+\d+', "version: $Version+1"
    Set-Content $pubspec -Value $content -NoNewline
    Write-Info "Updated pubspec.yaml to $Version+1"
}
Write-Success "pubspec.yaml updated"

# Step 7: Git operations
if (-not $SkipGitPush -and -not $DryRun) {
    Write-Step "Git operations..."
    Set-Location $ProjectRoot

    # Stage changes
    git add releases/*.exe releases/*.json flutter_app/pubspec.yaml installer/windows/installer.nsi

    # Create release commit
    $commitMsg = "Release v$Version`n`n$ReleaseNotes"
    git commit -m $commitMsg

    # Create and push tag
    git tag -a "v$Version" -m "Release v$Version"
    Write-Info "Created tag: v$Version"

    if ([string]::IsNullOrEmpty($GithubToken)) {
        Write-Warn "GITHUB_TOKEN not provided - skipping git push"
        Write-Warn "Run manually: git push && git push --tags"
    } else {
        git push https://x-access-token:$GithubToken@github.com/rasumeng/BT-Resume.git main
        git push https://x-access-token:$GithubToken@github.com/rasumeng/BT-Resume.git --tags
        Write-Info "Pushed to GitHub"
    }
}
Write-Success "Git operations complete"

# Step 8: GitHub Release (if token provided)
if (-not $SkipGithubUpload -and -not $DryRun -and -not [string]::IsNullOrEmpty($GithubToken)) {
    Write-Step "Creating GitHub release..."
    $installerPath = Join-Path $ReleasesDir "BTFResume-$Version-Setup.exe"

    # Use GitHub CLI if available, otherwise API
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if ($gh) {
        $body = if ($ReleaseNotes) { $ReleaseNotes } else { "Release v$Version" }
        gh release create "v$Version" $installerPath --title "v$Version" --notes $body
    } else {
        Write-Warn "GitHub CLI not found. Upload manually or set GH_TOKEN"
        Write-Info "Download URL: https://github.com/rasumeng/BT-Resume/releases/download/v$Version/BTFResume-$Version-Setup.exe"
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Release v$Version Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Files created:"
Write-Info "  releases/BTFResume-$Version-Setup.exe"
Write-Info "  releases/app-archive.json"
Write-Host ""
Write-Host "Next steps:"
Write-Info "  1. Verify GitHub release at: https://github.com/rasumeng/BT-Resume/releases"
Write-Info "  2. Upload app-archive.json to GitHub Pages or update gh-pages branch"
Write-Info "  3. Update beyondtheframe-site to point to new installer URL"
Write-Host ""