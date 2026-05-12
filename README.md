# Ai Reel Generator

Cloud-first Flask app for creating vertical reels from uploaded clips and narration.

The app uploads media to ImageKit, queues reel jobs in `data/jobs`, and the background worker builds the final MP4 with `ffmpeg` before publishing it back to ImageKit.

## Features

- Upload multiple image clips from the browser
- Generate narration with Google Text-to-Speech
- Build portrait reels with `ffmpeg`
- Store uploads and final reels in ImageKit only
- Auto-hide reels that were deleted from ImageKit
- Modern responsive UI for Home, Create, and Gallery

## Requirements

- Python 3.14+
- `ffmpeg` available on your `PATH`
- An ImageKit account and private API key

## Environment Variables

Set these before running the app:

- `IMAGEKIT_PRIVATE_KEY` - required for uploads and final reel publishing
- `IMAGEKIT_UPLOAD_FOLDER` - optional, defaults to `ai-reels`

Example on Windows PowerShell:

```powershell
$env:IMAGEKIT_PRIVATE_KEY="your_private_key"
$env:IMAGEKIT_UPLOAD_FOLDER="ai-reels"
```

## Install

```powershell
python -m venv .venv
& .venv\Scripts\Activate.ps1
pip install flask gtts requests werkzeug
```

## Run

```powershell
python main.py
```

Open the app in your browser after the server starts.

## How It Works

1. Upload clips on the Create page.
2. Files are sent to ImageKit and a job manifest is saved in `data/jobs`.
3. The background worker downloads the media, generates narration, and assembles the reel.
4. The final MP4 is uploaded back to ImageKit.
5. Home and Gallery list only reels that still exist in ImageKit.

## Project Structure

- `main.py` - Flask routes, upload flow, reel listing, API sync
- `generate_process.py` - background reel builder
- `reel.py` - text-to-speech helper
- `imagekit_storage.py` - ImageKit upload/download helpers
- `templates/` - HTML templates
- `static/` - CSS and static assets

## Notes

- Generated runtime content such as `data/jobs`, `runtime/work`, and `__pycache__` should not be committed.
- If reels are deleted in ImageKit, the app prunes stale entries and hides them from the UI.