# BT Resume

A free, local AI resume helper that polishes your resume bullets, tailors your resume to job descriptions, and formats new experience — all running privately on your own machine. No API keys, no subscriptions, no data leaving your device.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/rasumeng/BT-Resume)](https://github.com/rasumeng/BT-Resume/releases)

---

## Why BT Resume?

Most AI resume tools cost money, require an account, or send your personal data to external servers. This is my take on a free alternative — built from scratch in Flutter + Python, powered by open-source LLMs that run entirely on your device.

---

## Features

- **Bullet Polish** — rewrites weak resume bullets into strong, ATS-optimized ones using proven resume writing formulas
- **Job Tailoring** — aligns your resume language and keywords to match a specific job description without changing your real experience
- **Experience Updater** — describe a new project or role in plain English and get polished, formatted resume bullets back
- **Resume Grading** — get scores and feedback on your resume's effectiveness
- **PDF + TXT input** — works with both plain text and real PDF resumes
- **PDF output** — generates a clean, formatted PDF resume ready to send
- **Auto-updates** — automatically stays up-to-date with new features and fixes
- **100% offline** — no internet connection required after setup, no API keys, completely free

---

## Tech Stack

| Layer | Tool |
|---|---|
| Frontend | Flutter 3.41.6 (Dart 3.11.4) |
| Backend Language | Python 3.10+ |
| Desktop Target | Windows (10+) |
| LLM Runtime | [Ollama](https://ollama.com) |
| Bullet Polish Model | Mistral 7B (fast, efficient) |
| Job Tailoring Model | LLaMA 3 8B (stronger instruction following) |
| PDF Reading | pdfplumber |
| PDF Generation | ReportLab |
| HTTP Client | Dio |
| REST API | Flask with CORS |
| Installer | NSIS |
| Auto-Update | flutter_desktop_updater + GitHub Releases |

---

## Quick Start

### For Non-Technical Users: Download the Installer

1. **Download** the latest `BTFResume-Setup-*.exe` from [releases](https://github.com/rasumeng/BT-Resume/releases)
2. **Run** the installer
3. **Follow the setup wizard** (handles everything)
4. **Launch** from your Desktop

That's it! No command line required.

### For Developers: Manual Setup

Read the [Development Setup](docs/DEVELOPMENT_SETUP.md) guide.

---

## Requirements

- Windows 10 or later (64-bit)
- 8GB+ RAM recommended
- 2GB+ free disk space

---

## Usage

### Application Tabs

| Tab | Description |
|-----|-------------|
| **My Resumes** | View and manage all your resumes |
| **Polish** | Enhance your bullet points with AI |
| **Tailor** | Customize resume for specific job descriptions |
| **Feedback** | Submit feature requests and bug reports |

### First Run Setup

On first launch, the app will:
1. Start the embedded Python backend
2. Download the Ollama AI model (~500MB-1GB)
3. Verify everything is working

This may take a few minutes on first run.

---

## Project Structure

```
BT-Resume/
├── flutter_app/                  # Flutter desktop frontend
│   ├── lib/
│   │   ├── config/               # App configuration (colors, typography, constants)
│   │   ├── core/
│   │   │   └── services/         # API service, app initialization
│   │   ├── features/
│   │   │   ├── resumes/          # My Resumes screen
│   │   │   ├── polish/           # Bullet enhancement screen
│   │   │   ├── tailor/          # Job customization screen
│   │   │   ├── feedback/         # Feedback submission screen
│   │   │   └── setup/            # First-run setup screens
│   │   ├── shared/               # Reusable widgets and mixins
│   │   └── main.dart             # App entry point
│   ├── assets/                   # Icons, images, bundled Python
│   └── pubspec.yaml
│
├── backend/                      # Flask REST API
│   ├── app.py                    # Flask app with CORS
│   ├── routes/                   # API endpoint definitions
│   ├── services/                 # Business logic (LLM, PDF, tailoring)
│   └── config.py                 # Backend configuration
│
├── core/                         # Shared Python modules
│   ├── prompts/                  # LLM prompt templates
│   ├── pdf/                      # PDF generation components
│   ├── resume_model.py           # Data models
│   └── utils.py                  # Utility functions
│
├── installer/                    # NSIS installer scripts
├── scripts/                      # Build and release scripts
├── releases/                     # Built installers
├── docs/                         # Documentation
└── README.md
```

---

## Architecture

### Desktop Application Flow
```
┌─────────────────┐
│  Flutter UI      │  ← Windows Desktop App
│  (User Interface) │
└────────┬────────┘
         │ HTTP/JSON
         ▼
┌─────────────────┐
│  Flask REST API │  ← Embedded Python Backend
│  (localhost)    │     (runs automatically)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Ollama LLM     │  ← Local AI Model
│  (Mistral 7B)   │     Runs entirely offline
└─────────────────┘
```

### API Endpoints
- `GET  /api/health` — Backend health check
- `GET  /api/status` — Detailed service status
- `GET  /api/list-resumes` — List all resumes
- `GET  /api/get-resume` — Load specific resume
- `PUT  /api/update-resume` — Update resume content
- `POST /api/delete-resume` — Delete a resume
- `POST /api/polish-bullets` — Enhance bullet points
- `POST /api/tailor-resume` — Customize for job
- `POST /api/grade-resume` — Score and analyze
- `POST /api/parse-resume` — Parse uploaded resume
- `POST /api/save-resume-pdf` — Generate PDF output

---

## Building from Source

### Prerequisites
- Flutter SDK 3.41.6+
- Python 3.10+
- NSIS 3.x (for installer)
- Git

### Build Commands

```powershell
# Build Flutter app
cd flutter_app
flutter pub get
flutter build windows --release

# Build NSIS installer
cd installer/windows
makensis installer.nsi

# Or use the release script (creates everything)
.\scripts\release.ps1 -Version "1.1.0"
```

### Output
Built installer: `releases/BTFResume-*-Setup.exe`

---

## Releasing Updates

See [RELEASE_PROCESS.md](RELEASE_PROCESS.md) for detailed instructions.

### Quick Release Steps

```powershell
# 1. Tag the release
git tag v1.1.0

# 2. Push to trigger GitHub Actions
git push origin v1.1.0
```

GitHub Actions will:
1. Build the Flutter app
2. Create the NSIS installer
3. Generate the update manifest
4. Create a GitHub Release
5. Update GitHub Pages for auto-updater

---

## Roadmap

- [x] Flutter desktop GUI
- [x] Resume polishing with AI
- [x] Job tailoring
- [x] Resume grading
- [x] PDF generation
- [x] Auto-update system
- [ ] File upload with drag-and-drop
- [ ] Cover letter generator
- [ ] Export to DOCX/HTML
- [ ] macOS support
- [ ] Linux support

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Author

Built by Robert Asumeng
[LinkedIn](https://www.linkedin.com/in/robertasumeng) | [GitHub](https://github.com/rasumeng)