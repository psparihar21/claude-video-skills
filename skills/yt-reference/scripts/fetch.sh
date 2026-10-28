#!/usr/bin/env bash
# usage: fetch.sh <youtube-url> <out-dir> [max-height=1080]
# Video, subs and frames are separate steps so a subtitle 429 never loses the video.
set -u
URL="$1"; OUT="$2"; H="${3:-1080}"
YT="$HOME/.local/bin/yt-dlp"
mkdir -p "$OUT"
"$YT" --no-playlist --write-info-json -f "bv*[height<=$H]+ba/b[height<=$H]" --merge-output-format mp4 \
  -o "$OUT/video.%(ext)s" -- "$URL" || { echo "VIDEO DOWNLOAD FAILED"; exit 1; }
# subs are best-effort: YouTube often 429s them
"$YT" --no-playlist --skip-download --write-auto-subs --write-subs --sub-langs "en.*,hi.*" --sub-format vtt \
  -o "$OUT/video.%(ext)s" -- "$URL" || echo "subs failed (429?) - transcribe with Whisper/Parakeet instead"
# cut-rhythm frames: one per scene change, max 60, small
mkdir -p "$OUT/frames"
ffmpeg -v error -i "$OUT/video.mp4" -vf "select='gt(scene,0.3)',scale=480:-1" -fps_mode vfr -frames:v 60 "$OUT/frames/s%03d.jpg"
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate -of default=nw=1 "$OUT/video.mp4"
