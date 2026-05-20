# BT Resume Release Process

## Quick Start

### Creating a New Release

1. **Ensure GitHub Pages is set up** (first time only):
   ```powershell
   .\scripts\setup-gh-pages.ps1
   git push origin gh-pages
   ```
   Then enable GitHub Pages in repo Settings > Pages > Source: gh-pages branch

2. **Create a release**:
   ```powershell
   # Local development (manual)
   .\scripts\release.ps1 -Version "1.1.0" -ReleaseNotes "New features and bug fixes"

   # Via GitHub Actions (recommended)
   git tag v1.1.0
   git push origin v1.1.0
   ```

## Automated Release (GitHub Actions)

The `release.yml` workflow triggers when you push a version tag (`v*`).

### Workflow Steps:
1. Build Flutter Windows app
2. Update NSIS installer version
3. Build NSIS installer
4. Generate `app-archive.json` update manifest
5. Create GitHub Release with installer
6. Update `gh-pages` branch with new manifest

### Manual Trigger (if needed):
```powershell
# Tag and push
git tag v1.1.0
git push origin v1.1.0
```

## Update Manifest Format

The `app-archive.json` manifest for flutter_desktop_updater:

```json
{
  "appName": "BT-Resume",
  "description": "Local AI Resume Helper",
  "items": [
    {
      "version": "1.1.0",
      "shortVersion": 1,
      "changes": [
        { "type": "feat", "message": "New feature" },
        { "type": "fix", "message": "Bug fix" }
      ],
      "date": "2026-05-20",
      "mandatory": false,
      "url": "https://github.com/rasumeng/BT-Resume/releases/download/v1.1.0/",
      "platform": "windows"
    }
  ]
}
```

## Update Flow

```
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│  Flutter App    │      │  GitHub Pages        │      │  GitHub Release │
│  (check update) │ ───> │  app-archive.json    │ <──  │  BTFResume.exe  │
└─────────────────┘      └──────────────────────┘      └─────────────────┘
```

1. App starts → checks `app-archive.json` on GitHub Pages
2. If new version found → downloads installer from GitHub Release
3. User can skip or install the update

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/release.ps1` | Local release build script |
| `scripts/setup-gh-pages.ps1` | Initialize GitHub Pages branch |

## GitHub Release URLs

- Release page: `https://github.com/rasumeng/BT-Resume/releases`
- Manifest: `https://rasumeng.github.io/BT-Resume/releases/app-archive.json`
- Installer: `https://github.com/rasumeng/BT-Resume/releases/download/v{VERSION}/BTFResume-{VERSION}-Setup.exe`

## Requirements

- Flutter SDK
- NSIS (for installer)
- GitHub CLI (optional, for manual releases)
- GitHub token (for CI/CD releases)