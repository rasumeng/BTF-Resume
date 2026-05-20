# Setup GitHub Pages for BT Resume Update System
# Run this once to initialize the gh-pages branch

param(
    [string]$RepoUrl = "https://github.com/rasumeng/BT-Resume.git"
)

$ErrorActionPreference = "Stop"

Write-Host "Setting up GitHub Pages for BT Resume updates..." -ForegroundColor Cyan
Write-Host ""

# Check if gh-pages branch exists locally
$hasGhPages = git rev-parse --verify gh-pages 2>$null

if ($hasGhPages) {
    Write-Host "gh-pages branch already exists locally" -ForegroundColor Yellow
} else {
    Write-Host "Creating gh-pages branch..." -ForegroundColor Yellow

    # Check if it exists on remote
    $remoteGhPages = git ls-remote --heads origin gh-pages 2>$null
    if ($remoteGhPages) {
        Write-Host "Checkout existing remote gh-pages..."
        git checkout -b gh-pages origin/gh-pages
    } else {
        Write-Host "Creating new gh-pages branch..."
        git checkout --orphan gh-pages
        git rm -rf . 2>$null
    }
}

# Create releases directory structure
if (-not (Test-Path "releases")) { New-Item -ItemType Directory -Path "releases" | Out-Null }

# Create placeholder README
@"
# BT Resume Update Server

This branch hosts the update manifest for BT Resume auto-updates.

## Files
- `app-archive.json` - Update manifest for flutter_desktop_updater

## How It Works
1. When a new release is created (via tag), GitHub Actions updates this branch
2. The Flutter app checks `app-archive.json` for new versions
3. Updates are downloaded from GitHub Releases

## Manual Setup (if GitHub Actions fails)
1. Copy `app-archive.json` from the release to this branch
2. Push to gh-pages: `git push origin gh-pages`
"@ | Set-Content "releases/README.md"

# Create initial app-archive.json
@"
{
  "appName": "BT-Resume",
  "description": "Local AI Resume Helper",
  "items": []
}
"@ | Set-Content "releases/app-archive.json"

# Create index.html for visual verification
@"
<!DOCTYPE html>
<html>
<head>
    <title>BT Resume Updates</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        .update { background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>BT Resume Update Server</h1>
    <p>Update manifest is available at: <code>/releases/app-archive.json</code></p>
    <div class="update">
        <h3>Current Version: 1.0.0</h3>
        <p>Initial release</p>
    </div>
</body>
</html>
"@ | Set-Content "index.html"

# Commit and push
git add .
git commit -m "Initialize GitHub Pages for BT Resume updates"

Write-Host ""
Write-Host "GitHub Pages setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Push to remote: git push origin gh-pages"
Write-Host "  2. Enable GitHub Pages in repo settings -> Pages -> gh-pages branch"
Write-Host "  3. Your update manifest will be at: https://rasumeng.github.io/BT-Resume/releases/app-archive.json"
Write-Host ""