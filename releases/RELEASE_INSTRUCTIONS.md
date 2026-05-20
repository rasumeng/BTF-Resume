# BT-Resume v1.0.0 - GitHub Release Guide

## Files to Upload

The following files are ready in `D:\Projects\resume-ai\releases\`:

| File | Size | Description |
|------|------|-------------|
| `BT-Resume-1.0.0.7z` | 99 MB | Compressed app archive (with 7z) |
| `Install-BTResume.ps1` | ~4 KB | PowerShell installer script |

## Steps to Create GitHub Release

### Option 1: Manual Upload via GitHub Website

1. Go to: https://github.com/rasumeng/BT-Resume/releases
2. Click "Draft a new release"
3. Tag: `v1.0.0`
4. Title: `BT-Resume v1.0.0`
5. Description:
   ```
   # BT-Resume v1.0.0

   A free, local AI resume helper that polishes your resume bullets, tailors your resume to job descriptions, and formats new experience — all running privately on your own machine.

   ## Downloads

   - **BT-Resume-1.0.0.exe** (Recommended) - Run `Install-BTResume.ps1` after extracting
   - **BT-Resume-1.0.0.7z** - Use 7-Zip to extract, then run `Install-BTResume.ps1`

   ## Installation Instructions

   1. Download `BT-Resume-1.0.0.7z`
   2. Extract the archive
   3. Run `Install-BTResume.ps1` as Administrator
   4. Follow the on-screen instructions

   Note: On first run, the app will download the AI model (llama3.2) - approximately 500MB-1GB.

   ## What's Included

   - Flutter desktop app
   - Bundled Ollama AI engine
   - Python Flask backend
   - All required dependencies

   ## System Requirements

   - Windows 10 or later (64-bit)
   - 8GB RAM minimum (16GB recommended)
   - 2GB free disk space
   ```

6. Attach files: Drag `BT-Resume-1.0.0.7z` and `Install-BTResume.ps1` to the release
7. Click "Publish release"

### Option 2: Using GitHub CLI

If you have GitHub CLI installed (`gh`):

```bash
cd D:\Projects\resume-ai\releases

# Create release
gh release create v1.0.0 \
  --title "BT-Resume v1.0.0" \
  --notes "See release description above" \
  BT-Resume-1.0.0.7z \
  Install-BTResume.ps1
```

## After Release

Update the website download link in `beyondtheframe-site`:

```tsx
// In app/projects/btr/page.tsx
const handleDownload = () => {
  trackDownload('btr', 'Beyond The Resume');
  setDownloads(prev => prev + 1);
  window.location.href = 'https://github.com/rasumeng/BT-Resume/releases/download/v1.0.0/BT-Resume-1.0.0.7z';
};
```

Or link to the installer script:

```tsx
window.location.href = 'https://github.com/rasumeng/BT-Resume/releases/download/v1.0.0/Install-BTResume.ps1';
```

## Note on File Size

GitHub has a 2GB soft limit per release and 100MB per individual file.
- `BT-Resume-1.0.0.7z` (99 MB) is well under the 100MB limit
- If you want a self-extracting .exe, you'll need to compress to under 100MB or host on another service