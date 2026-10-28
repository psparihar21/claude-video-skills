# add-zooms

Punch-zooms, listicle ratchet zooms and slow Ken Burns pushes on a flat talking-head or voiceover clip, timed from word timestamps. Idea from Tella's add-zooms (louisedesadeleer/add-zooms); code written fresh.

## Requirements

ffmpeg/ffprobe (NVENC, or `--cpu` for libx264), Python 3.10+.

## Scripts / usage

`python scripts/zoom.py in.mp4 map.json out.mp4` - audio is copied untouched.

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).
