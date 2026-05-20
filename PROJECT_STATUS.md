# BT-Resume Project - Development & Release Documentation

## Project Overview

**BT-Resume** is a free, local AI resume helper desktop application that:
- Polishes resume bullets
- Tailors resumes to job descriptions
- Formats new experience
- Runs entirely offline on the user's machine (no API keys, no subscriptions)

### Tech Stack
- **Frontend:** Flutter 3.24.0 (Dart)
- **Backend:** Python Flask REST API
- **AI Engine:** Ollama (local LLM with llama3.2 model)
- **PDF Generation:** ReportLab

---

## Current Status (May 20, 2026)

### ✅ Completed

| Task | Status | Location |
|------|--------|----------|
| Flutter app build | ✅ Ready | `flutter_app/build/windows/x64/runner/Release/` |
| Bundled Ollama | ✅ Included | `flutter_app/assets/ollama/` |
| Bundled Python backend | ✅ Included | `flutter_app/assets/python/` |
| NSIS installer | ✅ Built | `installer/windows/BT-Resume-Setup.exe` (~103 MB) |
| Website download link | ✅ Updated | `beyondtheframe-site/app/projects/btr/page.tsx` |

### ⚠️ Manual Steps Required

| Step | Action |
|------|--------|
| Create GitHub Release | Upload `BT-Resume-Setup.exe` to GitHub Releases |
| Push website | Run git commands to deploy website changes |

---

## Directory Structure

```
D:\Projects\resume-ai\
├── backend/                    # Flask API (original source)
│   ├── app.py
│   ├── routes/
│   └── services/
├── core/                      # Python modules (original source)
│   ├── pdf/
│   └── prompts/
├── flutter_app/               # Flutter desktop app
│   ├── assets/               # Bundled assets
│   │   ├── python/           # Bundled Flask backend
│   │   │   ├── backend/      # app.py, routes, services
│   │   │   └── core/         # pdf_generator, prompts, etc.
│   │   ├── ollama/           # Bundled Ollama binary
│   │   └── icons/            # App icons
│   ├── lib/                  # Dart source code
│   │   ├── config/           # App constants
│   │   ├── core/services/   # API & initialization services
│   │   └── features/         # UI screens
│   └── pubspec.yaml         # Flutter dependencies
├── installer/
│   └── windows/
│       ├── installer.nsi     # NSIS installer script
│       └── BT-Resume-Setup.exe  # Built installer (103 MB)
├── releases/                  # Release artifacts
│   ├── BT-Resume-1.0.0.7z   # 7z archive (99 MB)
│   ├── BTFResume-1.0.0-Portable.zip  # Portable zip (112 MB)
│   └── Install-BTResume.ps1  # PowerShell installer script
├── beyondtheframe-site/       # Website repo (separate repo)
│   ├── app/projects/btr/
│   │   └── page.tsx          # Download button config
│   └── public/downloads/
└── docs/
    └── DEVELOPMENT.md        # Development guide

```

---

## Key Files

### App Initialization Service
**Location:** `flutter_app/lib/core/services/app_initialization_service.dart`

This handles:
1. Extracts bundled Flask backend from assets
2. Extracts bundled Ollama from assets
3. Starts Ollama service (port 11434)
4. Starts Flask backend (port 5000)
5. Downloads llama3.2 model on first run (~500MB-1GB)

### NSIS Installer Script
**Location:** `installer/windows/installer.nsi`

Features:
- Installs to `C:\Program Files\BT Resume`
- Creates Desktop shortcut
- Creates Start Menu shortcuts
- Includes uninstaller with optional user data preservation
- Registers with Add/Remove Programs

### Website Download Link
**Location:** `beyondtheframe-site/app/projects/btr/page.tsx`

Current download URL: `https://github.com/rasumeng/BT-Resume/releases/download/v1.0.0/BT-Resume-Setup.exe`

---

## How to Rebuild Everything

### 1. Rebuild Flutter App

```cmd
cd D:\Projects\resume-ai\flutter_app
flutter clean
flutter pub get
flutter build windows --release
```

Output: `flutter_app/build/windows/x64/runner/Release/`

### 2. Rebuild NSIS Installer

Requires NSIS installed on machine (download from https://nsis.sourceforge.io/)

**Method A - Drag & Drop:**
1. Open MakeNSISW from Start Menu
2. Drag `installer/windows/installer.nsi` onto the window

**Method B - Command Line:**
```cmd
"C:\Program Files (x86)\NSIS\makensis.exe" "D:\Projects\resume-ai\installer\windows\installer.nsi"
```

Output: `installer/windows/BT-Resume-Setup.exe`

---

## How to Create a GitHub Release

### 1. Build the Installer (if not already done)

Follow steps above in "How to Rebuild Everything"

### 2. Go to GitHub Releases

**URL:** https://github.com/rasumeng/BT-Resume/releases/new

### 3. Fill in Release Details

| Field | Value |
|-------|-------|
| Tag | `v1.0.0` |
| Target | `main` |
| Title | `BT-Resume v1.0.0` |

### 4. Add Description

```markdown
# BT-Resume v1.0.0

A free, local AI resume helper that polishes your resume bullets, tailors your resume to job descriptions, and formats new experience — all running privately on your own machine.

## Installation

1. Download `BT-Resume-Setup.exe`
2. Double-click to run the installer
3. Follow the on-screen instructions
4. Launch from Desktop or Start Menu

**Note:** On first run, the app will download the AI model (llama3.2) - approximately 500MB-1GB.

## System Requirements

- Windows 10 or later (64-bit)
- 8GB RAM minimum (16GB recommended)
- 2GB free disk space

## What's Included

- Flutter desktop app
- Bundled Ollama AI engine
- Python Flask backend
- All required dependencies
```

### 5. Attach Installer

- Drag `BT-Resume-Setup.exe` to the release page (or click "Attach binaries")

### 6. Publish Release

- Click "Publish release"

---

## How to Update the Website

### 1. Modify the Download Link

**File:** `beyondtheframe-site/app/projects/btr/page.tsx`

```tsx
const handleDownload = () => {
  trackDownload('btr', 'Beyond The Résumé');
  setDownloads(prev => prev + 1);
  window.location.href = 'https://github.com/rasumeng/BT-Resume/releases/download/v1.0.0/BT-Resume-Setup.exe';
};
```

### 2. Commit and Push

```cmd
cd D:\Projects\resume-ai\beyondtheframe-site
git add .
git commit -m "Update download link to v1.0.0 release"
git push origin main
```

Vercel will automatically deploy the changes.

---

## Installation Flow (End User)

1. User downloads `BT-Resume-Setup.exe` from website
2. Double-clicks to run installer
3. Follows installation wizard (accepts defaults)
4. Desktop shortcut created
5. User launches app
6. First run:
   - App extracts bundled Ollama
   - Starts Ollama service
   - Starts Flask backend
   - Downloads llama3.2 model (500MB-1GB, one-time)
   - App ready to use

---

## Model Download at First Run

The llama3.2 model is NOT bundled in the installer. It downloads on first run.

**Why?** Bundling the model would make the installer ~1.5GB, which is too large.

**Alternative (if desired):** Bundle the model by:
1. Downloading the model file first
2. Adding to `flutter_app/assets/models/`
3. Updating `app_initialization_service.dart` to use bundled model

---

## Cross-Platform Builds

The GitHub Actions workflow (`.github/workflows/build.yml`) supports:
- **Windows** (x64) - Built locally or via CI
- **macOS** - Via GitHub Actions (macOS runners)
- **Linux** - Via GitHub Actions (Ubuntu runners)

Note: Windows builds must be done on Windows. macOS/Linux can only be built on their respective platforms or via CI.

---

## Troubleshooting

### App doesn't start
- Check if Ollama is running: `http://localhost:11434`
- Check if Flask is running: `http://localhost:5000/api/health`
- View logs in: `%APPDATA%/BTFResume/`

### Installer fails
- Run as Administrator
- Check disk space (needs ~2GB free)
- Temporarily disable antivirus

### Model download fails
- Check internet connection
- Check disk space in `%APPDATA%` or `Documents`
- Ollama might already have the model: `ollama list`

---

## Future Improvements (TODO)

| Item | Priority | Notes |
|------|----------|-------|
| Bundle llama3.2 model | Medium | Would make installer ~1.5GB |
| Create macOS installer | Medium | Requires macOS to build |
| Create Linux installer | Medium | Requires Linux to build |
| Add auto-update | Low | Already has flutter_desktop_updater package |
| Docker dev environment | Low | For consistent dev setup |

---

## Repository URLs

| Repo | Purpose |
|------|---------|
| https://github.com/rasumeng/BT-Resume | Main app (Flutter + backend) |
| https://github.com/rasumeng/beyondtheframe-site | Website (Next.js on Vercel) |

---

## Contact / Author

BT-Resume is developed by Robert A. Asumeng (rasumeng)

---

*Last Updated: May 20, 2026*