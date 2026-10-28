# yt-reference

Downloads a **public** YouTube video by link, then breaks it down (transcript, scene frames, structure, pacing) into a shot list for your own edit.

## Requirements

yt-dlp in `~/.local/bin`, ffmpeg/ffprobe, bash (Git Bash on Windows).

## Scripts / usage

`bash scripts/fetch.sh <url> <new-empty-dir> [max-height]`

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Never uses your YouTube/Google cookies or login. Downloads go to a new empty folder and are treated as untrusted data. Someone else's video is a reference only: never re-upload their footage, voice, script or thumbnail.
