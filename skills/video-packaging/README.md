# video-packaging

A Claude skill that analyzes a real video and produces **only** the packaging requested: a thumbnail / cover, title,
caption or YouTube description. Thumbnails are always built from an extracted frame of the video, never a generated scene.

## What it does

- Samples frames (4 fps, up to 12 fps in a window), ranks them, and **OCRs each one so frames with burned-in titles/logos are skipped**.
- Crops around the subject using a saliency map and tries 4 type layouts to keep the subject clear of the text.
- Picks the highlight colour by measured contrast; refuses text that would mis-shape (Devanagari without raqm).
- Hard gates: cap height >= 7 px at real phone tile width, white type >= 3:1 contrast, platform safe zones.
- Outputs YouTube 1280x720, Shorts/Reel 1080x1920, Instagram feed 1080x1350 as JPG under 2 MB, plus a light/dark phone preview sheet.
- Designs in Canva (Pro) when connected, otherwise with the local ffmpeg + Pillow renderer.

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | Workflow: scope, analyze, copy, thumbnail, hand-off, done checklist |
| `scripts/package.py` | The renderer / analyzer (PEP 723 inline deps; `uv run` needs no install) |
| `scripts/ocr_windows.ps1` | Windows built-in OCR wrapper (tesseract is the fallback) |
| `references/platforms.md`, `copy.md`, `canva.md` | Platform specs, copywriting rules, Canva path |
| `requirements.txt` | `pillow`, `numpy`; needs `ffmpeg`/`ffprobe` on PATH |

## Usage

```powershell
uv run scripts/package.py --help
```

Or just ask Claude: "make a YouTube thumbnail for this video" with the file path.

## Results

See [`../../docs/video-packaging-v2-test-report.md`](../../docs/video-packaging-v2-test-report.md) (4K analyze 28 s -> 8 s; subject
covered by type 52% -> 25%; 5/5 production renders pass) and sample outputs in [`../../examples/video-packaging/`](../../examples/video-packaging/).