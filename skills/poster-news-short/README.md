# poster-news-short

A faceless vertical game-news Short from official posters and your own voice: research, script, recording, take splicing, word-timed posters, music bed, cover and captions.

## Requirements

ffmpeg (NVENC), Python with numpy + Pillow, `faceless-vo-script`, optionally `voice-enhance` and Voice Studio for recording.

## Scripts / usage

`scripts/` holds the two finished builds (`build_final.py` for a poster grid, `build_editions_short.py` for an editions Short) and their helpers. They are **worked examples**: paths point to `~/Videos/pipeline/<project>`; copy a script and change its paths and data for a new Short.

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Use official key art and licensed music only; `references/music-licenses.txt` lists the tracks used.
