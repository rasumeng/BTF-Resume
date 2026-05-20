# Download script for bundling Ollama and Model
# Run this locally to prepare assets for the installer

param(
    [string]$OutputDir = "..\flutter_app\assets"
)

$ErrorActionPreference = "Stop"
$OutputDir = Join-Path $PSScriptRoot $OutputDir

Write-Host "Downloading Ollama v0.24.0 for Windows..." -ForegroundColor Cyan

$ollamaDir = Join-Path $OutputDir "ollama"
if (!(Test-Path $ollamaDir)) { New-Item -ItemType Directory -Path $ollamaDir -Force | Out-Null }

# Download Ollama
$ollamaZip = Join-Path $ollamaDir "ollama-windows-amd64.zip"
$url = "https://github.com/ollama/ollama/releases/download/v0.24.0/ollama-windows-amd64.zip"

Write-Host "This is ~1.3GB, please wait..."
Invoke-WebRequest -Uri $url -OutFile $ollamaZip -UseBasicParsing

# Extract
Write-Host "Extracting..."
Expand-Archive -Path $ollamaZip -DestinationPath $ollamaDir -Force
Remove-Item $ollamaZip -Force

Write-Host "Ollama ready at: $ollamaDir" -ForegroundColor Green

Write-Host "`nDownloading llama3.2 model..." -ForegroundColor Cyan

$modelsDir = Join-Path $OutputDir "models"
if (!(Test-Path $modelsDir)) { New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null }

# For the model, we need Ollama to pull it
# The model will be downloaded at runtime or we can create a placeholder
Write-Host "Model downloading requires Ollama to be set up first." -ForegroundColor Yellow
Write-Host "The app will download the model on first run if not bundled." -ForegroundColor Yellow

Write-Host "`nAssets prepared!" -ForegroundColor Green